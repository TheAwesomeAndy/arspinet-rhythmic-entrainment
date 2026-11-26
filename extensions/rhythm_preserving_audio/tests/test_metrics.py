#!/usr/bin/env python3
"""Unit tests for the stimuli and the scientific metrics (numpy/scipy only; no model needed).

  /home/user/.venvs/rpa/bin/python -m unittest discover -s extensions/rhythm_preserving_audio/tests -v
"""
import os, sys, unittest
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'src'))
import synthetic_audio as sa, rhythmic_metrics as rm, acoustic_metrics as am, baselines as bl


class Stimuli(unittest.TestCase):
    def test_fixed_cycle_count_and_grid(self):
        for f in sa.TEMPI_HZ:
            c = sa.Composition('H01', 20, f); gt = sa.ground_truth(c)
            self.assertEqual(len(gt['beats_s']), sa.N_BEATS)
            self.assertAlmostEqual(gt['duration_s'], sa.N_BEATS / f + sa.TAIL_S)
            step = 1 / (f * sa.SUB)
            self.assertTrue(np.allclose(np.round(np.array(gt['onsets_s']) / step) * step, gt['onsets_s']))

    def test_deterministic_render(self):
        c = sa.Composition('H02', 20, 2.0)
        self.assertTrue(np.array_equal(sa.render(c, 3)[0], sa.render(c, 3)[0]))

    def test_splits_disjoint(self):
        s = {k: set(v) for k, v in sa.SPLITS.items()}
        self.assertFalse(s['train'] & s['val']); self.assertFalse(s['train'] & s['test']); self.assertFalse(s['val'] & s['test'])
        self.assertEqual(set().union(*s.values()), set(sa.TEMPLATES))

    def test_shift_moves_audio_not_reference(self):
        c = sa.Composition('H01', 20, 2.0); x0, g0 = sa.render(c); x1, g1 = sa.render(c, shift_s=0.03)
        self.assertEqual(g0, g1)
        a = np.argmax(np.abs(x0[0]) > 0.05); b = np.argmax(np.abs(x1[0]) > 0.05)
        self.assertAlmostEqual((b - a) / sa.SR, 0.03, delta=0.002)


class Matching(unittest.TestCase):
    def test_prf_exact(self):
        r = rm.prf([0, 1, 2], [0, 1, 2], 0.05); self.assertEqual((r['precision'], r['recall'], r['f1']), (1, 1, 1)); self.assertEqual(r['mean_abs_dev_s'], 0)

    def test_prf_within_and_beyond_tolerance(self):
        ref = np.arange(10.0)
        self.assertAlmostEqual(rm.prf(ref + 0.03, ref, 0.05)['mean_abs_dev_s'], 0.03, places=12)
        self.assertEqual(rm.prf(ref + 0.06, ref, 0.05)['f1'], 0.0)

    def test_one_to_one(self):
        r = rm.prf([1.0, 1.01, 1.02], [1.0], 0.05); self.assertEqual(r['f1'], 0.5)   # P = 1/3, R = 1

    def test_tempo_octave(self):
        e = rm.tempo_error(2.0, 1.0); self.assertEqual(e['rel_err_strict'], 1.0); self.assertEqual(e['rel_err_octave'], 0.0)

    def test_mir_eval_agreement(self):
        import mir_eval
        rng = np.random.RandomState(0); ref = np.sort(rng.uniform(0, 20, 40)); est = np.sort(ref + rng.randn(40) * 0.03)
        self.assertAlmostEqual(rm.prf(est, ref, 0.05)['f1'], mir_eval.onset.f_measure(ref, est, window=0.05)[0], places=12)


class AliasingMeasures(unittest.TestCase):
    def test_ordered_alignment_no_crossing(self):
        pairs = rm.align_ordered([0.0, 0.11, 0.2], [0.0, 0.1, 0.2], 0.05)
        self.assertEqual([(i, j) for i, j, _ in pairs], [(0, 0), (1, 1), (2, 2)])
        self.assertTrue(all(b[0] > a[0] and b[1] > a[1] for a, b in zip(pairs, pairs[1:])))

    def test_grid_shift_fools_deviation_on_periodic_grid(self):
        ref = np.arange(32) * 0.1; est = ref + 0.1                 # displaced by exactly one grid step
        self.assertLess(rm.prf(est, ref, 0.05)['mean_abs_dev_s'], 1e-9)   # deviation looks perfect: aliasing
        tr = rm.timing_report(est, ref, 0.05)
        self.assertAlmostEqual(tr['best_lag_ms'], 100.0, delta=2.6); self.assertLess(tr['lag_specificity'], 0)

    def test_alias_floor(self):
        self.assertGreater(rm.alias_floor(np.arange(32) * 0.1, 0.05), 0.9)        # periodic: high
        rng = np.random.RandomState(0); ref = np.sort(rng.choice(np.arange(200) * 0.05, 20, replace=False))
        self.assertLess(rm.alias_floor(ref, 0.02), 0.5)                              # sparse aperiodic: low

    def test_nonperiodic_probe_has_low_floor(self):
        for f in (2.0, 3.0):
            on = np.asarray(sa.ground_truth(sa.Composition('H02', 20, f, nonperiodic=True))['onsets_s'])
            self.assertLess(rm.alias_floor(on, 0.05), 0.6)

    def test_nonperiodic_split_safe(self):
        a = sa.nonperiodic_pattern(sa.Composition('H01', 20, 2.0)); b = sa.nonperiodic_pattern(sa.Composition('T01', 0, 2.0))
        self.assertNotEqual(a, b)


class OnAudio(unittest.TestCase):
    def test_identity_onsets(self):
        for tpl in ('H01', 'H03'):
            c = sa.Composition(tpl, 20, 2.0); x, gt = sa.render(c); r = rm.rhythm_report(x, sa.SR, gt, x)
            self.assertEqual(r['onset']['f1'], 1.0); self.assertLess(r['onset']['mean_abs_dev_s'], 0.006)
            self.assertGreaterEqual(r['beat_informed']['annotated']['f1'], 0.9); self.assertAlmostEqual(r['envelope_r'], 1.0)

    def test_ltas_timing_blind_and_timbre_sensitive(self):
        c = sa.Composition('H01', 20, 2.0); x, _ = sa.render(c)
        self.assertLess(am.ltas_log_mel_distance(x, sa.render(c, shift_s=0.03)[0], sa.SR), 0.3)
        self.assertGreater(am.ltas_log_mel_distance(x, bl.lowpass(x, sa.SR, 1500.0), sa.SR), 5.0)
        self.assertEqual(am.ltas_log_mel_distance(x, x, sa.SR), 0.0)

    def test_lowpass_darkens(self):
        c = sa.Composition('H01', 20, 2.0); x, _ = sa.render(c)
        self.assertLess(am.acoustic_report(x, bl.lowpass(x, sa.SR, 1500.0), sa.SR)['centroid_shift_hz'], -500)

    def test_shift_detected_by_onset_deviation(self):
        c = sa.Composition('H01', 20, 2.0); x, gt = sa.render(c); r = rm.rhythm_report(sa.render(c, shift_s=0.02)[0], sa.SR, gt, x)
        self.assertAlmostEqual(1e3 * r['onset']['mean_abs_dev_s'], 20.0, delta=4.0); self.assertAlmostEqual(r['envelope_lag_ms'], 20.0, delta=10.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
