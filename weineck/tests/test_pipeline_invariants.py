#!/usr/bin/env python3
"""Invariant tests for the building blocks of the confirmatory Q2 pipeline, on synthetic fixtures only.

  python3 -m unittest discover -s weineck/tests -v

Added by the 2026-11-26 engineering audit (docs/FINAL_ENGINEERING_AUDIT.md). No test here reads EEG, audio, the
released stimulus features or the external reservoir; every fixture is generated in the test from a fixed seed.
The tests pin behaviour the committed results depend on. They do not change any method, threshold or seed:

  * loader      trial-to-stimulus matching: 128 Hz features, 1.0 s start trim, +-20 ms tolerance, ambiguous
                trials dropped (weineck_loader.match_trials; skipped when mne is not installed);
  * mTRF        lag layout, recovery of a planted kernel, leave-one-trial-out without leakage, and agreement of
                the three copies of the ridge estimator (mtrf.fit_trf, underfit_check.solve,
                identifiability_sim.ridge);
  * tagging     the shared statistic on a signal with known beat power, and its too-short-signal fallback;
  * shuffle     the stimulus-label shuffle null: own label never drawn, sample size kept, random stream
                consumed as the committed participant scores assume;
  * rule        the committed Theory 3 decision rule as coded in identifiability_sim.decide.
"""
import os, sys, unittest
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')   # before numpy loads BLAS: unittest discovery imports this file before test_identifiability_procedure.py, whose exact-reproduction test needs single-threaded BLAS
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); WEINECK = os.path.dirname(HERE); sys.path.insert(0, WEINECK)
import mtrf
import tagging
import identifiability_sim as sim

try:                                     # weineck_loader imports mne at module level
    import weineck_loader as wl
    import underfit_check as uc
    HAVE_MNE = True
except ImportError:                      # pragma: no cover - depends on the environment
    HAVE_MNE = False


def synthetic_table():
    """Feature table rows (tempo_idx, subgroup, trial_idx, length in samples at 128 Hz). Subgroup 0 holds four
    stimuli: 10.0 s, 20.0 s, and two of 30.0 s and 30.0 s + 1 sample at different tempi (an ambiguous pair).
    Subgroups 1-3 hold lengths that are far from every subgroup-0 duration (the loader scans all four
    stimulation subgroups, as in the released feature file)."""
    fs = 128
    return [(0, 0, 0, 10 * fs), (4, 0, 0, 20 * fs), (8, 0, 0, 30 * fs), (12, 0, 0, 30 * fs + 1),
            (0, 1, 0, 13 * fs), (4, 1, 0, 23 * fs), (8, 1, 0, 37 * fs),
            (0, 2, 0, 44 * fs), (4, 2, 0, 48 * fs), (0, 3, 0, 52 * fs), (4, 3, 0, 55 * fs)]


@unittest.skipUnless(HAVE_MNE, 'mne not installed: weineck_loader cannot be imported')
class LoaderMatching(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(wl.FEAT_FS, 128.0); self.assertEqual(wl.TRIM_S, 1.0)
        self.assertEqual(len(wl.TEMPI), 13); self.assertAlmostEqual(wl.TEMPI[0], 1.0); self.assertAlmostEqual(wl.TEMPI[-1], 4.0)
        self.assertEqual(wl.FEATURES, ('stim_env_z', 'stim_der_z', 'stim_beat_z', 'stim_spec_z'))

    def test_trim_and_tolerance(self):
        table = synthetic_table()
        # listening durations (S40 -> S80) = feature length + 1.0 s; +15 ms is inside the tolerance, +25 ms outside
        durs = [10.0 + 1.0 + 0.015, 20.0 + 1.0 - 0.015, 10.0 + 1.0 + 0.025]
        j, cost, assign = wl.match_trials(durs, table)
        self.assertEqual(j, 0)
        self.assertEqual(assign[0], (0, 0)); self.assertEqual(assign[1], (4, 0)); self.assertIsNone(assign[2])

    def test_without_the_trim_nothing_matches(self):
        table = synthetic_table()
        j, cost, assign = wl.match_trials([10.0, 20.0], table, subgroup=0)       # features are 1.0 s shorter than these
        self.assertEqual(assign, [None, None])
        j, cost, assign = wl.match_trials([10.0, 20.0], table, subgroup=0, trim_s=0.0)
        self.assertEqual(assign, [(0, 0), (4, 0)])

    def test_ambiguous_trial_is_dropped(self):
        table = synthetic_table()
        j, cost, assign = wl.match_trials([30.0 + 1.0 + 0.004], table, subgroup=0)   # two stimuli within 20 ms
        self.assertEqual(assign, [None])

    def test_subgroup_is_the_best_duration_fit(self):
        table = synthetic_table()
        j, cost, assign = wl.match_trials([13.0 + 1.0, 23.0 + 1.0, 37.0 + 1.0], table)
        self.assertEqual(j, 1); self.assertLess(cost, 1e-9); self.assertEqual(assign, [(0, 0), (4, 0), (8, 0)])

    def test_one_to_one_filter_is_the_callers_job(self):
        """match_trials assigns per trial. Two trials can claim the same stimulus; the callers (q2_residual.py,
        underfit_check.load_participant_arrays, tempo_curve.tempo_known_trials) drop such claims. This test pins
        that division of labour so that a new caller does not assume the loader enforces one-to-one matching."""
        j, cost, assign = wl.match_trials([10.0 + 1.0, 10.0 + 1.0 + 0.01], synthetic_table(), subgroup=0)
        self.assertEqual(assign, [(0, 0), (0, 0)])

    def test_trial_pairing_from_markers(self):
        # S40 is doubled 10 ms apart in the recordings; the later one starts the trial; S120/S180 are ignored
        ev = [(5.00, 40), (5.01, 40), (15.01, 80), (16.0, 120), (21.5, 180), (30.0, 40), (30.01, 40), (52.0, 80), (60.0, 80)]
        self.assertEqual(wl.trials_from_events(ev), [(5.01, 15.01), (30.01, 52.0)])


class MTRF(unittest.TestCase):
    def setUp(self):
        self.rng = np.random.RandomState(0); self.fs = 64.0

    def test_lag_layout(self):
        X = self.rng.standard_normal((200, 4)); Xl, lags = mtrf.lag_matrix(X, self.fs, 0.0, 0.4)
        self.assertEqual(len(lags), 27); self.assertEqual(Xl.shape, (200, 4 * 27))          # 0-400 ms at 64 Hz
        self.assertEqual(len(mtrf.lag_matrix(X, self.fs, 0.0, 1.0)[1]), 65)                    # 0-1000 ms
        for k in (0, 1, 13, 26):                                                               # causal: column block k is X delayed by k samples
            np.testing.assert_array_equal(Xl[k:, k * 4:(k + 1) * 4], X[:200 - k]); np.testing.assert_array_equal(Xl[:k, k * 4:(k + 1) * 4], 0.0)

    def test_block_sizes_used_by_the_identifiability_simulator(self):
        """identifiability_sim.NS / NL / NH are typed by hand and must equal the regressor counts that
        identifiability_precompute.py builds from mtrf.lag_matrix (see the comment on that line)."""
        n_short = len(mtrf.lag_matrix(np.zeros((100, 1)), self.fs, 0.0, 0.4)[1]); n_long = len(mtrf.lag_matrix(np.zeros((100, 1)), self.fs, 0.0, 1.0)[1])
        self.assertEqual(sim.NS, 4 * n_short + 1); self.assertEqual(sim.NL, 4 * n_long + 1)
        self.assertEqual(sim.NH, 60 * len(range(0, n_short, 2))); self.assertEqual(sim.NA, sim.NH + sim.NS)

    def _trials(self, n_trials=6, T=1500, noise=0.05):
        W = self.rng.standard_normal((27 * 2, 3)) * np.exp(-np.arange(27 * 2) / 20.0)[:, None]   # planted kernel, 2 features, 3 channels
        Xs, Ys = [], []
        for _ in range(n_trials):
            X = self.rng.standard_normal((T, 2)); Xl, _ = mtrf.lag_matrix(X, self.fs, 0.0, 0.4)
            Xs.append(X); Ys.append(Xl @ W + 0.7 + noise * self.rng.standard_normal((T, 3)))
        return Xs, Ys, W

    def test_recovers_a_planted_kernel(self):
        Xs, Ys, W = self._trials()
        West, lags = mtrf.fit_trf(Xs, Ys, self.fs, 0.0, 0.4, lam=1e-6)
        self.assertEqual(West.shape, (27 * 2 + 1, 3))
        self.assertLess(np.max(np.abs(West[:-1] - W)), 0.01); np.testing.assert_allclose(West[-1], 0.7, atol=0.01)   # last row is the bias
        P = mtrf.predict(West, Xs[0], self.fs, 0.0, 0.4)
        self.assertGreater(np.corrcoef(P[:, 0], Ys[0][:, 0])[0, 1], 0.99)

    def test_leave_one_trial_out_matches_an_explicit_refit(self):
        """No leakage: the held-out trial's prediction must equal the one from a model refitted without it."""
        Xs, Ys, _ = self._trials(n_trials=5, T=600, noise=1.0)
        r, _ = mtrf.loo_prediction_r(Xs, Ys, self.fs, 0.0, 0.4, lam=1.0)
        for i in range(len(Xs)):
            W, _ = mtrf.fit_trf(Xs[:i] + Xs[i + 1:], Ys[:i] + Ys[i + 1:], self.fs, 0.0, 0.4, lam=1.0)
            P = mtrf.predict(W, Xs[i], self.fs, 0.0, 0.4); Pc = P - P.mean(0); Yc = Ys[i] - Ys[i].mean(0)
            np.testing.assert_allclose(r[i], (Pc * Yc).sum(0) / np.sqrt((Pc ** 2).sum(0) * (Yc ** 2).sum(0)), rtol=1e-8, atol=1e-10)

    def test_the_copies_of_the_ridge_estimator_agree(self):
        """q2_residual.py (inline `solve`), underfit_check.solve and identifiability_sim.ridge re-implement
        mtrf.fit_trf's estimator on summed normal-equation moments. They must stay the same estimator, and
        subtracting one trial's moments must equal refitting without that trial."""
        Xs, Ys, _ = self._trials(n_trials=4, T=500, noise=1.0)
        XL = [np.hstack([mtrf.lag_matrix(X, self.fs, 0.0, 0.4)[0], np.ones((len(X), 1))]) for X in Xs]
        A_i = [x.T @ x for x in XL]; B_i = [x.T @ y for x, y in zip(XL, Ys)]; A = sum(A_i); B = sum(B_i)
        for lam in (0.1, 1.0, 10.0, 100.0):
            ref, _ = mtrf.fit_trf(Xs[1:], Ys[1:], self.fs, 0.0, 0.4, lam=lam)                 # refit without trial 0
            np.testing.assert_allclose(sim.ridge(A - A_i[0], B - B_i[0], lam), ref, rtol=1e-7, atol=1e-9)
            if HAVE_MNE:
                np.testing.assert_allclose(uc.solve(A - A_i[0], B - B_i[0], lam), ref, rtol=1e-7, atol=1e-9)


class TaggingStatistic(unittest.TestCase):
    FS = 256.0

    def _signal(self, f, amp, seconds=60, seed=0):
        rng = np.random.RandomState(seed); t = np.arange(int(seconds * self.FS)) / self.FS
        return amp * np.sin(2 * np.pi * f * t + 0.3) + rng.standard_normal(len(t))

    def test_constants(self):
        self.assertEqual(tagging.FS, 256.0); self.assertEqual(len(tagging.GRID), 13)
        np.testing.assert_allclose(tagging.GRID, np.arange(1.0, 4.01, 0.25))

    def test_detects_a_planted_beat_and_not_its_absence(self):
        x = self._signal(2.0, 0.5)
        self.assertGreater(tagging.tag_z(x, 2.0), 8.0)               # beat present at the tested tempo
        self.assertLess(abs(tagging.tag_z(x, 2.75)), 4.0)            # no power planted at this tempo or its 2nd harmonic
        self.assertLess(abs(tagging.tag_z(self._signal(2.0, 0.0), 2.0)), 4.0)

    def test_second_harmonic_counts(self):
        x = self._signal(4.0, 0.5)                                   # power at 4 Hz only
        self.assertGreater(tagging.tag_z(x, 2.0), 8.0)               # seen as k = 2 of a 2 Hz beat (max over k in {1, 2})
        self.assertLess(abs(tagging.tag_z(x, 2.0, ks=(1,))), 4.0)

    def test_grid_statistics_peak_at_the_own_tempo(self):
        z = tagging.grid_stats(self._signal(1.75, 0.6))
        self.assertEqual(z.shape, (13,)); self.assertEqual(int(np.argmax(z)), int(np.argmin(np.abs(tagging.GRID - 1.75))))

    def test_matches_the_pre_registered_definition_on_coloured_noise(self):
        """docs/PREREGISTRATION_DRAFT.md section 3, written out independently: Welch PSD (Hann, 10 s segments, 50 %
        overlap); at k x tempo, k in {1, 2}, the bin is compared with a local quadratic baseline fitted to the bins
        0.15-0.8 Hz away (other harmonics excluded); z = (bin - baseline) / sd of the baseline residuals; max over
        k. On a 1/f spectrum a plain neighbour mean gives a different number, so this pins the baseline."""
        from scipy.signal import welch
        rng = np.random.RandomState(4); n = int(90 * self.FS); X = np.fft.rfft(rng.standard_normal(n)); fr_ = np.fft.rfftfreq(n, 1 / self.FS); fr_[0] = fr_[1]
        x = np.fft.irfft(X / fr_, n=n); x = x / x.std()                                  # steep 1/f^2 power spectrum, no beat
        nper = int(10 * self.FS); fr, p = welch(x - x.mean(), fs=self.FS, nperseg=nper, noverlap=nper // 2, window='hann')
        for f in (1.0, 1.25, 2.0, 3.75):
            zs = []; mean_based = []
            for k in (1, 2):
                i = int(np.argmin(np.abs(fr - k * f))); nb = (np.abs(fr - k * f) > 0.15) & (np.abs(fr - k * f) < 0.8)
                for kk in (1, 2): nb &= np.abs(fr - kk * f) > 0.15
                c = np.polyfit(fr[nb] - k * f, p[nb], 2); resid = p[nb] - np.polyval(c, fr[nb] - k * f)
                zs.append((p[i] - np.polyval(c, 0.0)) / resid.std()); mean_based.append((p[i] - p[nb].mean()) / p[nb].std())
            self.assertAlmostEqual(tagging.tag_z(x, f), max(zs), places=6, msg=f'{f} Hz')
            self.assertGreater(abs(max(zs) - max(mean_based)), 0.05, f'{f} Hz: fixture does not separate the two baselines')

    def test_too_short_signal_returns_zero(self):
        # 1 s of data: 1 Hz resolution, no bins 0.15-0.8 Hz away, so the statistic is defined as 0.0 (not NaN)
        self.assertEqual(tagging.tag_z(self._signal(2.0, 1.0, seconds=1), 2.0), 0.0)

    def test_scale_invariance(self):
        x = self._signal(2.0, 0.5)
        self.assertAlmostEqual(tagging.tag_z(x, 2.0), tagging.tag_z(1e3 * x + 5.0, 2.0), places=6)


class ShuffleNull(unittest.TestCase):
    def test_own_label_is_never_drawn(self):
        N, G = 40, 13; own = np.arange(N) % G; Z = np.zeros((N, G)); Z[np.arange(N), own] = 1000.0
        obs, z, mu, sd = tagging.participant_shuffle_z(Z, own, np.random.RandomState(1), 500)
        self.assertEqual(obs, 1000.0); self.assertEqual(mu, 0.0); self.assertEqual(sd, 0.0)

    def test_null_keeps_the_sample_size(self):
        """Every shuffle averages over all N trials: with one statistic value shared by all other-tempo cells the
        shuffle mean is that value exactly, whatever N is."""
        for N in (40, 75, 110):
            own = np.arange(N) % 13; Z = np.full((N, 13), 2.5); Z[np.arange(N), own] = 7.0
            obs, z, mu, sd = tagging.participant_shuffle_z(Z, own, np.random.RandomState(0), 500)
            self.assertEqual(obs, 7.0); self.assertAlmostEqual(mu, 2.5, places=12); self.assertLess(sd, 1e-12)

    def test_random_stream_is_n_shuffles_by_n_trials(self):
        """The committed participant scores were computed with one RandomState per participant shared across the
        twelve statistics in a fixed order (q2_residual.py). That only reproduces if each call consumes exactly
        n_shuf x N uniform draws."""
        N, n_shuf = 37, 500; rng = np.random.RandomState(123); ref = np.random.RandomState(123)
        Z = np.random.RandomState(5).standard_normal((N, 13)); own = np.arange(N) % 13
        tagging.participant_shuffle_z(Z, own, rng, n_shuf); ref.random_sample((n_shuf, N))
        self.assertEqual(rng.random_sample(), ref.random_sample())

    def test_deterministic_and_centred_under_exchangeability(self):
        Z = np.random.RandomState(7).standard_normal((80, 13)); own = np.random.RandomState(8).randint(0, 13, 80)
        a = tagging.participant_shuffle_z(Z, own, np.random.RandomState(3), 500); b = tagging.participant_shuffle_z(Z, own, np.random.RandomState(3), 500)
        self.assertEqual(a, b)
        zs = [tagging.participant_shuffle_z(np.random.RandomState(100 + k).standard_normal((80, 13)), own, np.random.RandomState(k), 500)[1] for k in range(200)]
        self.assertLess(abs(np.mean(zs)), 0.25); self.assertLess(abs(np.std(zs) - 1.0), 0.25)

    def test_planted_effect_gives_a_large_z(self):
        rng = np.random.RandomState(11); N = 90; own = rng.randint(0, 13, N); Z = rng.standard_normal((N, 13)); Z[np.arange(N), own] += 0.5
        obs, z, mu, sd = tagging.participant_shuffle_z(Z, own, np.random.RandomState(0), 500)
        self.assertGreater(z, 3.0)


class CommittedTheory3Rule(unittest.TestCase):
    """docs/OSCILLATOR_DECISION_RULE.md: supported iff median(aug - best TRF) > 0 with one-sided Wilcoxon p < .01
    AND aug beats the linear-bank-augmented model (paired one-sided Wilcoxon p < .05)."""
    def _part(self, aug_gain, lin_gain, n=20, seed=0):
        rng = np.random.RandomState(seed); s = 0.04 + 0.005 * rng.standard_normal(n); l = s - 0.001
        jit = 0.0005 * rng.standard_normal(n)
        return [{'s': float(s[i]), 'l': float(l[i]), 'a': float(s[i] + aug_gain + jit[i]), 'al': float(s[i] + lin_gain)} for i in range(n)]

    def test_supported_when_both_criteria_hold(self):
        sup, med, p1, r_short = sim.decide(self._part(aug_gain=0.01, lin_gain=0.0))
        self.assertTrue(sup); self.assertGreater(med, 0); self.assertLess(p1, 0.01)

    def test_not_supported_when_the_linear_bank_does_as_well(self):
        part = self._part(aug_gain=0.01, lin_gain=0.01)             # criterion 1 passes, criterion 2 does not
        sup, med, p1, _ = sim.decide(part)
        self.assertFalse(sup); self.assertGreater(med, 0); self.assertLess(p1, 0.01)

    def test_not_supported_when_the_trf_is_better(self):
        sup, med, p1, _ = sim.decide(self._part(aug_gain=-0.01, lin_gain=-0.02))
        self.assertFalse(sup); self.assertLess(med, 0)

    def test_best_evoked_baseline_is_per_participant(self):
        part = self._part(aug_gain=0.01, lin_gain=0.0)
        for p in part[::2]: p['l'] = p['a'] + 0.02                  # the long TRF wins for half of the participants
        sup, med, p1, _ = sim.decide(part)
        self.assertFalse(sup)

    @staticmethod
    def _signed(neg_ranks, n=20):
        """n paired differences with magnitudes 1e-4 ... n e-4 (no ties), negative at the given ranks."""
        d = np.arange(1, n + 1) * 1e-4; d[[r - 1 for r in neg_ranks]] *= -1; return d

    def test_criterion_1_threshold_is_p_below_0_01(self):
        """Exact one-sided Wilcoxon p for 20 participants: 0.0068 with negative ranks {20, 19, 1}, 0.0133 with
        {20, 19, 7}. The median difference is positive and criterion 2 passes in both, so only alpha = 0.01
        separates them."""
        for neg, want in (([20, 19, 1], True), ([20, 19, 7], False)):
            d = self._signed(neg); aug = np.full(20, 0.05)
            part = [{'s': float(aug[i] - d[i]), 'l': float(aug[i] - d[i] - 0.01), 'a': float(aug[i]), 'al': float(aug[i] - 0.001 * (i + 1))} for i in range(20)]
            sup, med, p1, _ = sim.decide(part)
            self.assertGreater(med, 0); self.assertEqual(p1 < 0.01, want); self.assertEqual(sup, want, neg)

    def test_criterion_2_threshold_is_p_below_0_05(self):
        """Criterion 1 passes clearly; aug minus aug_lin has exact p 0.041 (negative ranks {20, 18, 14, 6}) or
        0.057 ({20, 19, 18, 5}), so only alpha = 0.05 separates the two."""
        for neg, want in (([20, 18, 14, 6], True), ([20, 19, 18, 5], False)):
            d2 = self._signed(neg); aug = np.full(20, 0.05)
            part = [{'s': float(aug[i] - 0.001 * (i + 1)), 'l': 0.0, 'a': float(aug[i]), 'al': float(aug[i] - d2[i])} for i in range(20)]
            sup, med, p1, _ = sim.decide(part)
            self.assertGreater(med, 0); self.assertLess(p1, 0.01); self.assertEqual(sup, want, neg)

    def test_six_participants_can_never_pass_criterion_1(self):
        # docs/THEORY3_RESULTS.md section 1: with n = 6 the smallest attainable one-sided p is 1/64 > 0.01
        part = [{'s': 0.04, 'l': 0.03, 'a': 0.04 + 0.001 * (i + 1), 'al': 0.04 - 0.001 * (i + 1)} for i in range(6)]
        sup, med, p1, _ = sim.decide(part)
        self.assertFalse(sup); self.assertAlmostEqual(p1, 1 / 64, places=12)

    def test_training_tempo_sets(self):
        np.testing.assert_allclose(sim.tempo_set(12), np.arange(1.0, 4.01, 0.25))
        np.testing.assert_allclose(sim.tempo_set(4), [1.0, 1.75, 2.5, 3.25, 4.0]); self.assertEqual(len(sim.tempo_set(8)), 9)


if __name__ == '__main__':
    unittest.main(verbosity=2)
