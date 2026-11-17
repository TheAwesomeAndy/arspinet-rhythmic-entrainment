#!/usr/bin/env python3
"""Identifiability procedure for encoding-model tests of entrainment: documented entry point.

Question it answers: if part of the stimulus-locked EEG were produced by an oscillator bank, how large would
that part have to be before the committed Theory 3 comparison (Hopf-augmented TRF vs the best TRF, then vs a
linear-oscillator-bank-augmented TRF; docs/OSCILLATOR_DECISION_RULE.md) detects it, at a given single-listen
signal-to-noise ratio, trial count and number of training tempi?

This module wraps identifiability_sim.py (the code that produced every committed cell in
weineck/results/identifiability/) without changing its numerics. It adds: a cell runner over a w grid,
the committed per-cell seed rule, Clopper-Pearson intervals, false-positive rates and W80.

Inputs
  * fitted kernels: JSON files from `identifiability_precompute.py --part kernels` (per participant: W_trf, the
    short-TRF evoked kernel; W_osc, the Hopf-bank kernel; sd_e, sd_o);
  * stimulus features, as sufficient statistics: the directory written by
    `identifiability_precompute.py --part stimuli` (A_a.npy, A_al.npy, A_l.npy, C_la.npy, C_alh.npy,
    stimuli_meta.npz). These are derived from the stimulus feature vectors and a noise bank; they are not
    redistributed (data policy) and must be rebuilt locally from the Weineck et al. data;
  * target held-out r of the short TRF (the noise scale gamma is calibrated for it if not already stored),
    trials per tempo, number of training tempi, the w grid (oscillator amplitude share), datasets per cell and
    participants per dataset; world A (committed), B (power-matched) or C (oscillator residualised on the TRF).

Outputs (summary JSON)
  * per cell: full-rule detection rate and criterion-1-only rate, each with k/n and a Clopper-Pearson 95 %
    interval; median delta r (augmented minus best TRF); realised held-out r;
  * false-positive rate: the full-rule and criterion-1 rates at w = 0 (evoked-only world), with intervals;
  * W80: the smallest w at which the rate reaches 0.8, by linear interpolation between grid points (full rule
    and criterion 1 alone), with its bracketing grid points, and its variance-share equivalent
    v = W^2 / (W^2 + (1 - W)^2) (uncorrelated components) and, per participant, accounting for the measured
    correlation rho of the evoked and oscillator predictions, v = W^2 / (W^2 + (1 - W)^2 + 2 W (1 - W) rho).

Seeds: by default each cell uses the committed rule seed = cksum("<w> <r> <trials> <ntempi>\\n") % 100000
(POSIX cksum of the string the queue scripts echo), so the committed cells are reproduced exactly.

Usage
  python3 identifiability_procedure.py --r 0.04 --trials 40 --ntempi 12 --w-grid 0,0.5,0.6,0.7,0.8,0.9,1 \\
      --datasets 20 --participants 20 --out-dir results/identifiability/procedure_runs/A_r0.04_n40_t12
Every cell is written to <out-dir>/cells/ as it runs (resumable); the summary goes to <out-dir>/summary.json.
"""
import argparse, json, os, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
from scipy.stats import beta as betad

import identifiability_sim as sim

CRIT1_ALPHA = 0.01   # committed criterion 1: median delta r > 0 and one-sided Wilcoxon p < 0.01


# ---- small statistics, verbatim from identifiability_merge_a3.py (cp, w80) ----
def cp(k, n, a=0.05):
    """Clopper-Pearson (exact binomial) interval for k successes in n."""
    lo = 0.0 if k == 0 else betad.ppf(a / 2, k, n - k + 1); hi = 1.0 if k == n else betad.ppf(1 - a / 2, k + 1, n - k); return [float(lo), float(hi)]


def w80(cells):
    """cells: {w: {'rate': ...}} sorted by w. Linear interpolation at 0.8 over w > 0."""
    ws = [w for w in cells if w > 0]; rs = [cells[w]['rate'] for w in ws]
    for i, (w, r) in enumerate(zip(ws, rs)):
        if r >= 0.8:
            if i == 0: return {'W80': float(w), 'bracket': [0.0, float(w)]}
            w0, r0 = ws[i - 1], rs[i - 1]; return {'W80': float(w0 + (0.8 - r0) * (w - w0) / (r - r0)), 'bracket': [float(w0), float(w)]}
    return {'W80': None, 'bracket': None, 'note': 'not reached'}


def variance_share(W, rho=0.0):
    """Amplitude share W -> variance share of the oscillator component of s = (1 - W) e + W o, e and o unit-sd
    with correlation rho: W^2 / (W^2 + (1 - W)^2 + 2 W (1 - W) rho). rho = 0 is the formula used for the
    committed headline (identifiability_merge.py), which assumes uncorrelated components."""
    return None if W is None else float(W ** 2 / (W ** 2 + (1 - W) ** 2 + 2 * W * (1 - W) * rho))


def correlation_report(st, Ws, world='A', subjects=None):
    """Per participant rho = corr(P_e, P_o) (identifiability_sim.component_correlation) and the variance share at
    each W in Ws; median and range across participants."""
    subs = subjects or st.ksubs; rho = {s: sim.component_correlation(st, s, world) for s in subs}
    stat = lambda v: {'median': float(np.median(v)), 'min': float(np.min(v)), 'max': float(np.max(v))}
    out = {'definition': 'rho = corr(P_e, P_o) over the simulation pool, pooled within trial; share = W^2 / (W^2 + (1 - W)^2 + 2 W (1 - W) rho)',
           'world': world, 'n_participants': len(subs), 'rho': {'per_participant': rho, **stat(list(rho.values())), 'median_abs': float(np.median(np.abs(list(rho.values()))))},
           'share': {}}
    for W in Ws:
        sh = [variance_share(W, r) for r in rho.values()]
        out['share'][f'{W:.6g}'] = {'W': float(W), 'uncorrelated': variance_share(W), **stat(sh)}
    return out


# ---- the committed seed rule ----
_CRC = []
for _i in range(256):
    _c = _i << 24
    for _ in range(8): _c = ((_c << 1) ^ 0x04C11DB7) if _c & 0x80000000 else (_c << 1)
    _CRC.append(_c & 0xFFFFFFFF)


def cksum(data: bytes) -> int:
    """POSIX cksum (CRC-32/CKSUM with the length appended), identical to the coreutils `cksum` CRC."""
    crc = 0
    upd = lambda c, b: ((c << 8) & 0xFFFFFFFF) ^ _CRC[((c >> 24) ^ b) & 0xFF]
    for b in data: crc = upd(crc, b)
    n = len(data)
    while n: crc = upd(crc, n & 0xFF); n >>= 8
    return (~crc) & 0xFFFFFFFF


def fmt(x):
    """Number as the queue scripts wrote it (0.9, 0, 1, 0.25, 0.04)."""
    return f'{x:g}'


def committed_seed(w, r, trials, ntempi):
    return cksum(f'{fmt(w)} {fmt(r)} {trials} {ntempi}\n'.encode()) % 100000


# ---- running ----
def gamma_for(st, r, trials, ntempi, participants, stats_dir, calibration_seed=0):
    """Noise scale for target r: from <stats_dir>/calibration.json if present, else calibrated and stored."""
    f = os.path.join(stats_dir, 'calibration.json'); cal = json.load(open(f)) if os.path.exists(f) else {}
    if str(r) in cal: return cal[str(r)]['gamma']
    g, rec = sim.calibrate_gamma(st, r, trials, sim.tempo_set(ntempi), participants, np.random.RandomState(calibration_seed)); rec.pop('_oracle_gamma')
    cal[str(r)] = rec; json.dump(cal, open(f, 'w'), indent=1); return g


def cell_path(out_dir, w, r, trials, ntempi):
    return os.path.join(out_dir, 'cells', f'w{float(w)}_r{r}_n{trials}_t{ntempi}.json')


def _run_one(job):
    from threadpoolctl import threadpool_limits
    threadpool_limits(1)   # single-threaded BLAS, as for every committed cell: exact reproduction depends on summation order
    (stats_dir, kernel_files, w, r, trials, ntempi, datasets, participants, seed, gamma, world, nested, out) = job
    st = sim.Store(stats_dir, kernel_files)
    return sim.run_cell(st, float(w), r, trials, ntempi, datasets, participants, seed, gamma, world, nested, out=out,
                        log=lambda m: print(m, flush=True))


def summarise_cell(res):
    pd = res['per_dataset']; n = res['datasets_done']; k = int(sum(pd['supported']))
    c1 = [bool(d > 0 and p < CRIT1_ALPHA) for d, p in zip(pd['delta_r'], pd['p1'])] if 'p1' in pd else None
    out = {'w': res['w'], 'seed': res.get('seed'), 'datasets': n, 'full_rule': {'rate': k / n, 'k': k, 'n': n, 'ci95': cp(k, n)},
           'median_delta_r': res['median_delta_r'], 'realised_r_short': res['realised_r_short']}
    if c1 is not None:
        k1 = int(sum(c1)); out['criterion1'] = {'rate': k1 / n, 'k': k1, 'n': n, 'ci95': cp(k1, n)}
    return out


def run_procedure(stats_dir, kernel_files, r, trials, ntempi, w_grid, datasets=20, participants=20, world='A', nested=False,
                  out_dir='identifiability_procedure_out', seeds=None, workers=1):
    """Run (or resume) every cell of the w grid and return the summary dict (also written to out_dir/summary.json)."""
    os.makedirs(os.path.join(out_dir, 'cells'), exist_ok=True)
    st = sim.Store(stats_dir, kernel_files); gamma = gamma_for(st, r, trials, ntempi, participants, stats_dir); del st
    jobs, results = [], {}
    for w in w_grid:
        seed = (seeds or {}).get(w, committed_seed(w, r, trials, ntempi)); p = cell_path(out_dir, w, r, trials, ntempi)
        if os.path.exists(p):
            d = json.load(open(p))
            if d['datasets_done'] >= datasets and d.get('seed') == seed: results[float(w)] = d; continue
        jobs.append((stats_dir, kernel_files, w, r, trials, ntempi, datasets, participants, seed, gamma, world, nested, p))
    if workers > 1 and len(jobs) > 1:
        with ProcessPoolExecutor(workers) as ex:
            for j, res in zip(jobs, ex.map(_run_one, jobs)): results[float(j[2])] = res
    else:
        for j in jobs: results[float(j[2])] = _run_one(j)
    cells = {w: summarise_cell(results[w]) for w in sorted(results)}
    full = {w: {'rate': c['full_rule']['rate']} for w, c in cells.items()}
    W_full = w80(full); W_full['variance_share'] = variance_share(W_full['W80'])
    summary = {'procedure': 'identifiability_procedure.py (wraps identifiability_sim.run_cell)', 'stats_dir': stats_dir,
               'kernel_files': kernel_files, 'world': world, 'nested_lambda': nested, 'r_target': r, 'gamma': gamma, 'trials_per_tempo': trials,
               'training_tempi': ntempi, 'datasets_per_cell': datasets, 'participants_per_dataset': participants,
               'cells': {str(w): c for w, c in cells.items()}, 'W80_full_rule': W_full}
    if all('criterion1' in c for c in cells.values()):
        W1 = w80({w: {'rate': c['criterion1']['rate']} for w, c in cells.items()}); W1['variance_share'] = variance_share(W1['W80']); summary['W80_criterion1'] = W1
    Ws = [x for x in (summary['W80_full_rule']['W80'], summary.get('W80_criterion1', {}).get('W80')) if x is not None]
    if Ws:
        st = sim.Store(stats_dir, kernel_files); summary['variance_share_with_correlation'] = correlation_report(st, Ws, world); del st
    if 0.0 in cells:
        summary['false_positive'] = {'full_rule': cells[0.0]['full_rule'], **({'criterion1': cells[0.0]['criterion1']} if 'criterion1' in cells[0.0] else {})}
    json.dump(summary, open(os.path.join(out_dir, 'summary.json'), 'w'), indent=1)
    return summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n\n')[0], formatter_class=argparse.RawDescriptionHelpFormatter, epilog=__doc__)
    ap.add_argument('--stats-dir', default=sim.OUT, help='sufficient statistics from identifiability_precompute.py --part stimuli')
    ap.add_argument('--kernels', nargs='*', default=None, help='fitted-kernel JSON files (default: <stats-dir>/kernels_*.json)')
    ap.add_argument('--r', type=float, required=True, help='target held-out r of the short TRF (single-listen SNR)')
    ap.add_argument('--trials', type=int, required=True, help='trials per tempo'); ap.add_argument('--ntempi', type=int, default=12, help='training tempi per fold')
    ap.add_argument('--w-grid', default='0,0.1,0.25,0.5,0.6,0.7,0.8,0.9,1', help='comma-separated oscillator amplitude shares')
    ap.add_argument('--datasets', type=int, default=20); ap.add_argument('--participants', type=int, default=20)
    ap.add_argument('--world', default='A', choices=['A', 'B', 'C']); ap.add_argument('--nested', action='store_true', help='nested (inner leave-one-tempo-out) lambda per model')
    ap.add_argument('--out-dir', required=True); ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--rho-report', default=None, metavar='W1,W2', help='only report rho = corr(P_e, P_o) per participant and the variance share at these W (no simulation); writes <out-dir>/component_correlation.json')
    a = ap.parse_args(argv)
    if a.rho_report:
        os.makedirs(a.out_dir, exist_ok=True); rep = correlation_report(sim.Store(a.stats_dir, a.kernels), [float(x) for x in a.rho_report.split(',')], a.world)
        json.dump(rep, open(os.path.join(a.out_dir, 'component_correlation.json'), 'w'), indent=1)
        print('rho', {k: v for k, v in rep['rho'].items() if k != 'per_participant'}); [print(k, v) for k, v in rep['share'].items()]; return
    t0 = time.time(); grid = [float(x) for x in a.w_grid.split(',')]
    s = run_procedure(a.stats_dir, a.kernels, a.r, a.trials, a.ntempi, grid, a.datasets, a.participants, a.world, a.nested, a.out_dir, workers=a.workers)
    for w, c in s['cells'].items():
        fr = c['full_rule']; line = f"w={w}: full rule {fr['k']}/{fr['n']} [{fr['ci95'][0]:.2f}, {fr['ci95'][1]:.2f}]"
        if 'criterion1' in c: c1 = c['criterion1']; line += f"; criterion 1 {c1['k']}/{c1['n']} [{c1['ci95'][0]:.2f}, {c1['ci95'][1]:.2f}]"
        print(line)
    print('W80 full rule:', s['W80_full_rule']); print('W80 criterion 1:', s.get('W80_criterion1')); print(f'({time.time() - t0:.0f}s)')


if __name__ == '__main__':
    main()
