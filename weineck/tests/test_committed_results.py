#!/usr/bin/env python3
"""Consistency tests for the committed results: each summary file must still follow from the files it was built from.

  python3 -m unittest discover -s weineck/tests -v

Added by the 2026-11-26 engineering audit (docs/FINAL_ENGINEERING_AUDIT.md). These tests read only files that are
committed to this repository (results JSON, figure_numbers.json, numbers.tex). They need no EEG, no stimulus
features, no sufficient statistics and no external reservoir, so none of them skips on a fresh clone. They write
only to a temporary directory.

What they guard:
  * the stage-2 group tests (q2_group_merge.py) re-run on the committed chunk files give the committed merged file,
    including the H2 headline;
  * every participant score in the stage-2 chunks follows from the committed per-trial statistics through
    tagging.participant_shuffle_z with the committed random stream;
  * the robustness baseline row equals stage 2, and the reservoir rows leave the reservoir-free columns untouched;
  * every identifiability cell is internally consistent with the committed rule, seed rule and noise calibration;
  * numbers.tex is exactly what make_numbers.py writes from figure_numbers.json, and a missing JSON path is an error.

A failure here means a committed result, or the code that derives one from another, was changed. It is not a
licence to regenerate the expected file: see AGENTS.md.
"""
import contextlib, glob, io, json, os, re, shutil, subprocess, sys, tempfile, unittest, warnings
for _v in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'): os.environ.setdefault(_v, '1')   # before numpy loads BLAS: unittest discovery imports this file before test_identifiability_procedure.py, whose exact-reproduction test needs single-threaded BLAS
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); WEINECK = os.path.dirname(HERE); ROOT = os.path.dirname(WEINECK); sys.path.insert(0, WEINECK)
import tagging
import q2_group_merge
import identifiability_procedure as proc

RES = os.path.join(WEINECK, 'results'); IDENT = os.path.join(RES, 'identifiability'); MS = os.path.join(ROOT, 'docs', 'manuscript')
CHUNKS = [os.path.join(RES, f'q2_residual_stage2_chunk{c}.json') for c in (1, 2, 3)]
STATS = [f'{src}_{st}' for src in ('drive', 'resid') for st in ('N0', 'N2a', 'N2b', 'R', 'R_pop', 'Rs')]      # order of q2_residual.py
_cache = {}


def load(path):
    if path not in _cache:
        with open(path) as fh: _cache[path] = json.load(fh)
    return _cache[path]


def stage2_subjects():
    out = {}
    for c in CHUNKS: out.update(load(c)['subjects'])
    return out


class Stage2GroupTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='arspinet_audit_'); out = os.path.join(cls.tmp, 'merged.json'); argv = sys.argv
        try:
            sys.argv = ['q2_group_merge.py', out] + CHUNKS
            with contextlib.redirect_stdout(io.StringIO()), warnings.catch_warnings():
                warnings.simplefilter('ignore', ResourceWarning)      # the script leaves its JSON handles to the garbage collector
                q2_group_merge.main()
        finally:
            sys.argv = argv
        with open(out) as fh: cls.got = json.load(fh)
        cls.ref = load(os.path.join(RES, 'q2_residual_stage2_merged.json'))

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_headline_h2(self):
        g = self.ref['group']['resid_N0']
        self.assertEqual(self.ref['n'], 34); self.assertEqual(round(g['median_delta'], 3), 0.228)
        self.assertEqual(int(round(g['frac_positive'] * 34)), 31); self.assertLess(g['p_wilcoxon'], 1e-4)
        self.assertEqual(self.ref['H2'], {'supported': True, 'p': g['p_wilcoxon'], 'alpha': 0.04})
        self.assertEqual(q2_group_merge.ALPHA2, 0.04); self.assertEqual(q2_group_merge.BOUND, 0.10)

    def test_merge_of_committed_chunks_gives_the_committed_file(self):
        got, ref = self.got, self.ref
        self.assertEqual(got['subjects'], ref['subjects']); self.assertEqual(got['N_trials'], ref['N_trials'])
        self.assertEqual(sum(ref['N_trials'].values()), 3300)
        for key, r in ref['group'].items():
            g = got['group'][key]
            self.assertEqual(g['z'], r['z'], key); self.assertEqual(g['delta'], r['delta'], key)
            for k in ('median_z', 'median_delta', 'frac_positive'): self.assertEqual(g[k], r[k], (key, k))
            np.testing.assert_allclose(g['p_wilcoxon'], r['p_wilcoxon'], rtol=1e-9, err_msg=f'{key}: Wilcoxon p moved (scipy version?)')
        self.assertEqual(got['H2']['supported'], ref['H2']['supported'])
        self.assertEqual(got['H1']['equivalent'], ref['H1']['equivalent']); np.testing.assert_allclose(got['H1']['tost_p'], ref['H1']['tost_p'], rtol=1e-9)
        for b in ref['H3']:
            self.assertEqual(got['H3'][b]['equivalent'], ref['H3'][b]['equivalent'], b); self.assertEqual(got['H3'][b]['median'], ref['H3'][b]['median'], b)

    def test_frozen_equivalence_reading(self):
        self.assertTrue(self.ref['H1']['equivalent'])                                   # reservoir vs linear statistic on the drive
        self.assertEqual({k: v['equivalent'] for k, v in self.ref['H3'].items()}, {'resid_N0': True, 'resid_N2a': False, 'resid_N2b': False})


class ParticipantScoresFollowFromTrials(unittest.TestCase):
    def test_all_34_participants(self):
        """q2_residual.py lines 122-130: one RandomState(int(subject)) per participant, used for the twelve
        statistics in the order of STATS, 500 shuffles each."""
        subs = stage2_subjects(); self.assertEqual(len(subs), 34); n_trials = 0
        for s, S in subs.items():
            rows = S['trials']; N = len(rows); n_trials += N; self.assertEqual(N, S['scores']['N']); self.assertGreaterEqual(N, 40)
            own = np.array([int(np.argmin(np.abs(tagging.GRID - r['f']))) for r in rows]); rng = np.random.RandomState(int(s))
            for key in STATS:
                src, st = key.split('_', 1); Z = np.array([r[src][st] for r in rows]); self.assertEqual(Z.shape, (N, 13))
                obs, z, mu, sd = tagging.participant_shuffle_z(Z, own, rng, 500)
                other = np.array([np.delete(Z[n], own[n]).mean() for n in range(N)]); dd = Z[np.arange(N), own] - other
                ref = S['scores'][key]
                self.assertEqual((obs, z, mu, sd), (ref['obs_mean'], ref['shuffle_z'], ref['shuffle_mean'], ref['shuffle_sd']), (s, key))
                self.assertEqual(float(dd.mean() / (dd.std() + 1e-12)), ref['delta'], (s, key))
        self.assertEqual(n_trials, 3300)

    def test_lambda_grid(self):
        lams = {r['lam'] for S in stage2_subjects().values() for r in S['trials']}
        self.assertLessEqual(lams, {0.1, 1.0, 10.0, 100.0})


class RobustnessRows(unittest.TestCase):
    RESERVOIR_ROWS = ('seed7', 'seed99', 'rho0', 'rho0.3', 'rho1.2', 'beta0.01', 'beta0.004')
    LINEAR = [k for k in STATS if k.split('_', 1)[1] in ('N0', 'N2a', 'N2b')]

    def row(self, name):
        return load(os.path.join(RES, 'robustness', f'{name}.json'))

    def test_baseline_row_equals_stage_2(self):
        base = self.row('baseline')['subjects']; subs = stage2_subjects(); self.assertEqual(sorted(base), sorted(subs))
        self.assertEqual(self.row('baseline')['config'], {'seed': 42, 'rho': 0.9, 'beta': 0.05, 'feats': [0, 1, 2, 3], 'tmax': 0.4})
        for s in subs:
            self.assertEqual(base[s]['N'], subs[s]['scores']['N'], s); self.assertEqual(base[s]['heldout_r'], subs[s]['scores']['pred_r_fc_mean'], s)
            for key in STATS: self.assertEqual(base[s][key]['delta'], subs[s]['scores'][key]['delta'], (s, key))

    def test_reservoir_rows_do_not_move_the_reservoir_free_columns(self):
        base = self.row('baseline')['subjects']
        for name in self.RESERVOIR_ROWS:
            row = self.row(name); self.assertIn('ended', row, name); self.assertEqual(len(row['subjects']), 34, name)
            moved = 0.0
            for s, S in row['subjects'].items():
                self.assertEqual(S['heldout_r'], base[s]['heldout_r'], (name, s))
                for key in self.LINEAR: self.assertEqual(S[key]['delta'], base[s][key]['delta'], (name, s, key))
                moved = max(moved, abs(S['resid_R']['delta'] - base[s]['resid_R']['delta']))
            self.assertGreater(moved, 0.0, f'{name}: the reservoir column did not move at all')

    def test_trf_rows_move_only_the_residual(self):
        base = self.row('baseline')['subjects']
        for name in ('trf_flux', 'trf_long'):
            S = self.row(name)['subjects']
            self.assertTrue(all(S[s][k]['delta'] == base[s][k]['delta'] for s in S for k in ('drive_N0', 'drive_N2a', 'drive_N2b', 'drive_R', 'drive_R_pop', 'drive_Rs')), name)
            self.assertTrue(any(S[s]['resid_N0']['delta'] != base[s]['resid_N0']['delta'] for s in S), name)

    def test_iaaft_row(self):
        I = self.row('iaaft')['subjects']; subs = stage2_subjects(); self.assertEqual(len(I), 34)
        for s, v in I.items():
            self.assertEqual(len(v['iaaft_deltas']), 200, s); self.assertEqual(v['resid_N0_real']['delta'], subs[s]['scores']['resid_N0']['delta'], s)
        for p in range(5):                                             # the row was run in five parts; the assembled file must equal them
            for s, v in load(os.path.join(RES, 'robustness', f'iaaft_part{p}.json'))['subjects'].items(): self.assertEqual(v, I[s], (p, s))
        real = np.array([I[s]['resid_N0_real']['delta'] for s in I]); surr = np.array([I[s]['iaaft_delta_mean'] for s in I])
        comp = load(os.path.join(RES, 'robustness', 'iaaft_components.json'))
        self.assertAlmostEqual(float(np.median(surr)), comp['spectral_median'], 12); self.assertAlmostEqual(float(np.median(real - surr)), comp['phase_median'], 12)
        self.assertEqual(int((real - surr > 0).sum()), comp['phase_positive'])


class IdentifiabilityCells(unittest.TestCase):
    DIRS = ('cells', 'cells_B', 'cells_C', 'cells_nested', 'cells_nested_C', 'cells_diag', 'cells_lampair')

    def cells(self):
        for d in self.DIRS:
            for f in sorted(glob.glob(os.path.join(IDENT, d, '*.json'))): yield os.path.relpath(f, IDENT), load(f)

    def test_every_cell_is_internally_consistent(self):
        cal = load(os.path.join(IDENT, 'calibration.json')); n = n_rule = n_seed = 0
        for name, d in self.cells():
            pd = d['per_dataset']; n += 1
            self.assertEqual(len(pd['supported']), d['datasets_done'], name); self.assertEqual(d['detection_rate'], float(np.mean(pd['supported'])), name)
            self.assertEqual(d['gamma'], cal[str(d['r_target'])]['gamma'], name)
            if 'seed' in d:
                n_seed += 1; self.assertEqual(d['seed'], proc.committed_seed(d['w'], d['r_target'], d['trials'], d['ntempi']), name)
            if 'p1' in pd and 'p2' in pd:                               # committed rule: median delta r > 0, p1 < .01, p2 < .05
                n_rule += 1
                self.assertEqual(pd['supported'], [bool(dr > 0 and p1 < 0.01 and p2 < 0.05) for dr, p1, p2 in zip(pd['delta_r'], pd['p1'], pd['p2'])], name)
        self.assertEqual(n, 141); self.assertEqual(n_seed, 47); self.assertEqual(n_rule, 15)

    def test_summary_lists_every_grid_cell_with_no_false_positive(self):
        I = load(os.path.join(RES, 'identifiability.json')); self.assertEqual(len(I['cells']), len(glob.glob(os.path.join(IDENT, 'cells', '*.json'))))
        self.assertEqual(I['false_positive_summary']['max_rate'], 0.0)
        for c in I['cells']:
            d = load(os.path.join(IDENT, 'cells', f"w{c['w']}_r{c['r_target']}_n{c['trials_per_tempo']}_t{c['training_tempi']}.json"))
            self.assertEqual(c['rate'], d['detection_rate']); self.assertTrue(c['complete'])
        self.assertEqual(set(I), {'plan', 'calibration', 'cells', 'headline', 'false_positive_summary', 'A3', 'A4'})   # identifiability_merge.py alone drops A3 and A4

    def test_a4_rerun_agrees_with_the_first_committed_cell(self):
        # same seed, simulator before and after commit 70360de: decisions identical, values within 2e-10 (the test file's own bound)
        a = load(os.path.join(IDENT, 'cells_lampair', 'A_w0.9_r0.04_n40_t12.json'))['per_dataset']; b = load(os.path.join(IDENT, 'cells', 'w0.9_r0.04_n40_t12.json'))['per_dataset']
        self.assertEqual(a['supported'], b['supported'])
        self.assertLess(float(np.max(np.abs(np.array(a['delta_r']) - b['delta_r']))), 2e-10); self.assertLess(float(np.max(np.abs(np.array(a['r_short']) - b['r_short']))), 2e-10)


class ManuscriptNumbers(unittest.TestCase):
    def run_make_numbers(self, mutate=None):
        """Run a copy of make_numbers.py in a temporary tree with the layout it expects; returns (returncode, stderr, numbers.tex or None)."""
        tmp = tempfile.mkdtemp(prefix='arspinet_audit_')
        try:
            os.makedirs(os.path.join(tmp, 'manuscript')); os.makedirs(os.path.join(tmp, 'figures', 'tnsre'))
            shutil.copy(os.path.join(MS, 'make_numbers.py'), os.path.join(tmp, 'manuscript'))
            N = json.loads(json.dumps(load(os.path.join(ROOT, 'docs', 'figures', 'tnsre', 'figure_numbers.json'))))
            if mutate: mutate(N)
            with open(os.path.join(tmp, 'figures', 'tnsre', 'figure_numbers.json'), 'w') as fh: json.dump(N, fh)
            r = subprocess.run([sys.executable, 'make_numbers.py'], cwd=os.path.join(tmp, 'manuscript'), capture_output=True, text=True)
            out = os.path.join(tmp, 'manuscript', 'numbers.tex'); tex = None
            if os.path.exists(out):
                with open(out) as fh: tex = fh.read()
            return r.returncode, r.stderr, tex
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_numbers_tex_is_what_make_numbers_writes(self):
        code, err, tex = self.run_make_numbers()
        self.assertEqual(code, 0, err)
        with open(os.path.join(MS, 'numbers.tex')) as fh: self.assertEqual(tex, fh.read())

    def test_a_missing_json_path_is_an_error(self):
        def drop(N): del N['fig2']['resid_median_delta']
        code, err, tex = self.run_make_numbers(drop)
        self.assertNotEqual(code, 0); self.assertIn('KeyError', err); self.assertIsNone(tex)      # nothing written on failure

    def test_every_macro_in_main_tex_is_defined(self):
        with open(os.path.join(MS, 'main.tex')) as fh: used = set(re.findall(r'\\Num([A-Za-z]+)', fh.read()))
        with open(os.path.join(MS, 'numbers.tex')) as fh: defined = set(re.findall(r'\\newcommand\{\\Num([A-Za-z]+)\}', fh.read()))
        self.assertGreater(len(used), 100); self.assertEqual(used - defined, set())

    def test_headline_macros_match_the_results(self):
        with open(os.path.join(MS, 'numbers.tex')) as fh: tex = fh.read()
        macro = lambda name: re.search(r'\\newcommand\{\\Num' + name + r'\}\{([^\\}]*)', tex).group(1)
        g = load(os.path.join(RES, 'q2_residual_stage2_merged.json'))['group']['resid_N0']; head = load(os.path.join(RES, 'identifiability.json'))['headline']
        self.assertEqual(macro('HTwoDelta'), f"{g['median_delta']:.3f}"); self.assertEqual(macro('HTwoPos'), str(int(round(g['frac_positive'] * 34)))); self.assertEqual(macro('NTwo'), '34')
        self.assertEqual(macro('WA'), f"{head['W_80_percent_power_amplitude_share']:.2f}"); self.assertEqual(macro('WA'), '0.89')


if __name__ == '__main__':
    unittest.main(verbosity=2)
