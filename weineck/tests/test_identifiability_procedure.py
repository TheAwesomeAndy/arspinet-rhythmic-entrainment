#!/usr/bin/env python3
"""Regression tests for the identifiability procedure (identifiability_procedure.py / identifiability_sim.run_cell).

  python3 -m unittest discover -s weineck/tests -v          # fast: seed rule, statistics, first 2 datasets of the cell
  IDENT_FULL=1 python3 -m unittest discover -s weineck/tests -v   # also the whole committed cell (20 datasets, ~15 min)

The reproduction test needs the sufficient statistics from identifiability_precompute.py (not redistributed) and is
skipped when they are absent. It re-runs the committed World A cell w = 0.9, r = 0.04, 40 trials, 12 tempi from its
stored seed and requires every stored committed-rule per-dataset value to be reproduced exactly (see CELL below).
"""
import json, glob, os, sys, unittest
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); WEINECK = os.path.dirname(HERE); sys.path.insert(0, WEINECK)
os.environ.setdefault('OMP_NUM_THREADS', '1'); os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import identifiability_sim as sim
import identifiability_procedure as proc

D = os.path.join(WEINECK, 'results', 'identifiability')
# Reference cell: World A, w = 0.9, r = 0.04, 40 trials, 12 tempi, seed 39676 (stored in the file), as committed by
# the A4 lambda-pair rerun (cells_lampair/, simulator as of commit 9e0f343). Its committed-rule per-dataset values
# (decision, delta r, realised r, criterion-1 and criterion-2 p) must be reproduced exactly.
CELL = os.path.join(D, 'cells_lampair', 'A_w0.9_r0.04_n40_t12.json')
# The same cell as first committed on 2026-11-10 (cells/, simulator as of commit 7b3f2b8). The simulator was
# generalised afterwards (commit 70360de), which moved its float rounding: decisions and rates are identical, delta r
# and r_short agree to within 2e-10 (measured maximum 1.54e-10 over the 20 datasets).
CELL_ORIG = os.path.join(D, 'cells', 'w0.9_r0.04_n40_t12.json')
HAVE_STATS = all(os.path.exists(os.path.join(D, f)) for f in ('A_a.npy', 'A_al.npy', 'A_l.npy', 'C_la.npy', 'C_alh.npy', 'stimuli_meta.npz'))
KEYS = ('supported', 'delta_r', 'r_short', 'p1', 'p2', 'aug_minus_lin')


def load(f):
    with open(f) as fh: return json.load(fh)


class SeedRule(unittest.TestCase):
    def test_committed_seed_matches_shell_cksum(self):
        # `echo "0.9 0.04 40 12" | cksum` -> 1140139676; % 100000 = 39676 (run_identifiability_queue.sh)
        self.assertEqual(proc.cksum(b'0.9 0.04 40 12\n'), 1140139676)
        self.assertEqual(proc.committed_seed(0.9, 0.04, 40, 12), 39676)

    def test_stored_seeds(self):
        n = 0
        for f in glob.glob(os.path.join(D, 'cells_*', 'w*_r0.04_n40_t12.json')):
            d = load(f)
            if 'seed' in d: self.assertEqual(d['seed'], proc.committed_seed(d['w'], d['r_target'], d['trials'], d['ntempi']), f); n += 1
        self.assertGreater(n, 10)


class Statistics(unittest.TestCase):
    def test_cp(self):
        self.assertEqual(proc.cp(0, 10), [0.0, proc.cp(0, 10)[1]]); self.assertAlmostEqual(proc.cp(0, 10)[1], 0.3084971078187607, 12)
        self.assertAlmostEqual(proc.cp(9, 10)[0], 0.5549838829718047, 12)

    def test_w80_reproduces_committed_headline(self):
        cells = {}
        for f in glob.glob(os.path.join(D, 'cells', 'w*_r0.04_n40_t12.json')):
            d = load(f); cells[float(d['w'])] = {'rate': d['detection_rate']}
        W = proc.w80(dict(sorted(cells.items())))['W80']
        head = load(os.path.join(WEINECK, 'results', 'identifiability.json'))['headline']
        self.assertAlmostEqual(W, head['W_80_percent_power_amplitude_share'], 12)
        self.assertAlmostEqual(proc.variance_share(W), head['W_80_percent_power_variance_share'], 12)


@unittest.skipUnless(HAVE_STATS, 'sufficient statistics not present (rebuild with identifiability_precompute.py)')
class ReproduceCommittedCell(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref = load(CELL); cls.n = 20 if os.environ.get('IDENT_FULL') == '1' else 2; r = cls.ref
        assert r['seed'] == proc.committed_seed(r['w'], r['r_target'], r['trials'], r['ntempi'])
        cls.res = sim.run_cell(sim.Store(), r['w'], r['r_target'], r['trials'], r['ntempi'], cls.n, 20, r['seed'], r['gamma'], 'A', False, log=lambda m: None)

    def test_exact_against_committed_cell(self):
        got, want, n = self.res['per_dataset'], self.ref['per_dataset'], self.n
        for k in KEYS: self.assertEqual(got[k], want[k][:n], k)
        if n == 20:
            self.assertEqual(self.res['detection_rate'], self.ref['detection_rate']); self.assertEqual(self.res['median_delta_r'], self.ref['median_delta_r'])
        print(f'\n  {n}/20 datasets of {os.path.relpath(CELL, D)} (seed {self.ref["seed"]}) reproduced exactly: {", ".join(KEYS)}', file=sys.stderr)

    def test_against_original_cell(self):
        orig = load(CELL_ORIG)['per_dataset']; got, n = self.res['per_dataset'], self.n
        self.assertEqual(got['supported'], orig['supported'][:n])
        dd = float(np.max(np.abs(np.array(got['delta_r']) - orig['delta_r'][:n]))); dr = float(np.max(np.abs(np.array(got['r_short']) - orig['r_short'][:n])))
        self.assertLess(dd, 2e-10); self.assertLess(dr, 2e-10)
        print(f'\n  {os.path.relpath(CELL_ORIG, D)} (first committed): decisions identical; max |delta r diff| {dd:.3g}, max |r_short diff| {dr:.3g}', file=sys.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
