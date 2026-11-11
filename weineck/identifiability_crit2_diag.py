#!/usr/bin/env python3
"""Criterion-2 diagnostic (exploratory, outside the committed rule). Why does the Hopf-augmented model beat
the linear-bank-augmented model at w = 1 in World A but not in World C?

(1) Expressibility, deterministic: pooled over the 388-stimulus pool and per participant kernel, the R^2 of the
oscillator generator (World A: P_o; World C: P_o_perp) on the linear-bank-augmented design Xal = [linear-bank
lags | short TRF]. 1 - R^2 is the Hopf-specific part, the only part aug can fit and aug_lin cannot.
(2) Simulation summary: per-dataset median (aug - aug_lin) delta r and its one-sided Wilcoxon p, at the
committed lambda 10 and at lambda 1, from cells_diag/ (World A and C, w = 1, operating point, 10 datasets).
Writes weineck/results/identifiability/criterion2_diagnostic.json.
"""
import json, os, sys, glob
import numpy as np
sys.argv = sys.argv[:1]
from identifiability_sim import Store, NH, NA, GRID, OUT


def main():
    st = Store(); f = f'{OUT}/pool_sums_al.npz'
    if not os.path.exists(f):
        Sal = np.zeros((NA, NA)); Sch = np.zeros((NH, NH))
        for t in GRID:
            s, e = st.block[t]; Sal += np.asarray(st.A_al[s:e]).sum(0, dtype=float); Sch += np.asarray(st.C_alh[s:e]).sum(0, dtype=float)
        np.savez(f, Sal=Sal, Sch=Sch)
    z = np.load(f); Sal, Sch = z['Sal'], z['Sch']; Sa = st.sums()['Sa']; N = st.T.sum()
    def r2_al(V):
        g = np.concatenate([Sch @ V[:NH] + Sal[:NH, NH:] @ V[NH:], Sa[NH:, :] @ V])     # sum Xal' Xa V
        b = np.linalg.solve(Sal, g); tot = V @ Sa @ V - (Sa[NA - 1] @ V) ** 2 / N; return float(1 - (V @ Sa @ V - b @ g) / tot), float(tot)
    rows = {}
    for s in st.ksubs:
        VA, _ = st.osc_kernel(s, 'A'); VC, d = st.osc_kernel(s, 'C')
        rA, totA = r2_al(VA); rC, totC = r2_al(VC)
        rows[s] = {'R2_lin_aug_design_A': rA, 'R2_lin_aug_design_C': rC, 'hopf_specific_fraction_A': 1 - rA, 'hopf_specific_fraction_C': 1 - rC,
                   'hopf_specific_variance_A': (1 - rA) * totA, 'hopf_specific_variance_C': (1 - rC) * totC, 'var_P_o': totA, 'var_P_o_perp': totC, 'R2_short_trf': d['R2_short_trf']}
    def summ(k): v = np.array([r[k] for r in rows.values()]); return {'median': float(np.median(v)), 'q25': float(np.percentile(v, 25)), 'q75': float(np.percentile(v, 75)), 'min': float(v.min()), 'max': float(v.max())}
    out = {'note': 'exploratory diagnostic, outside the committed rule', 'expressibility': {k: summ(k) for k in ['R2_lin_aug_design_A', 'R2_lin_aug_design_C', 'hopf_specific_fraction_A', 'hopf_specific_fraction_C']},
           'check_hopf_specific_variance_equal_A_C': float(np.max([abs(r['hopf_specific_variance_A'] - r['hopf_specific_variance_C']) / r['hopf_specific_variance_A'] for r in rows.values()])),
           'per_participant': rows, 'simulation': {}}
    for fcell in sorted(glob.glob(f'{OUT}/cells_diag/*.json')):
        d = json.load(open(fcell)); c = d['criterion2_diagnostic']
        def med(k): return float(np.median([x[k] for x in c]))
        out['simulation'][d['world']] = {'w': d['w'], 'datasets': len(c), 'rule_rate': d['detection_rate'],
            'median_over_datasets': {k: med(k) for k in ['median_aug_minus_best', 'median_aug_minus_lin', 'median_aug_lam1_minus_lin', 'median_lin_minus_best']},
            'criterion2_pass_rate_lambda10': float(np.mean([x['p2_aug_vs_lin'] < 0.05 for x in c])), 'criterion2_pass_rate_lambda1': float(np.mean([x['p2_aug_lam1_vs_lin'] < 0.05 for x in c])),
            'median_r': {m: float(np.median([x['median_r'][m] for x in c])) for m in c[0]['median_r']}}
    json.dump(out, open(f'{OUT}/criterion2_diagnostic.json', 'w'), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != 'per_participant'}, indent=1))


if __name__ == '__main__':
    main()
