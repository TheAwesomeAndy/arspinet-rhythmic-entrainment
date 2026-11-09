#!/usr/bin/env python3
"""Merge robustness rows into one table and apply the committed rule verbatim (docs/ROBUSTNESS_PLAN.md).
Writes weineck/results/robustness_table.json and docs/ROBUSTNESS_RESULTS.md."""
import glob, json, os, sys
import numpy as np
from scipy.stats import wilcoxon, ttest_1samp

R = '/home/user/arspinet-rhythmic-entrainment/weineck/results/robustness'
ORDER = ['baseline', 'seed7', 'seed99', 'rho0', 'rho0.3', 'rho1.2', 'beta0.01', 'beta0.004', 'trf_flux', 'trf_long', 'iaaft']
BOUND = 0.10


def tost(d):
    d = np.asarray(d, float)
    return bool(max(ttest_1samp(d, -BOUND, alternative='greater').pvalue, ttest_1samp(d, BOUND, alternative='less').pvalue) < 0.05)


rows = {}; md = ["# Robustness grid results (exploratory; run after the stage-2 merge)", "",
                "Rule (docs/ROBUSTNESS_PLAN.md): 'H2 robust' = residual delta > 0 with one-sided Wilcoxon p < .01 in every row except IAAFT; 'H1/H3 equivalence robust' = TOST (+-0.10 delta) passes in every row. Every row is reported.", "",
                "| row | tau (ms) | held-out r | median residual delta (H2) | positive / n | Wilcoxon p | H1 TOST (drive R vs L) | H3 TOST (resid R vs N0) | R - Rs (median delta) | H2 p<.01 |",
                "|---|---|---|---|---|---|---|---|---|---|"]
h2_ok = True; eq_ok = True; flips = []
for row in ORDER:
    p = f'{R}/{row}.json'
    if not os.path.exists(p):
        md.append(f"| {row} | - | - | not run | | | | | | |"); continue
    J = json.load(open(p)); S = J['subjects']; subs = sorted(S, key=int); n = len(subs)
    if row == 'iaaft':
        real = np.array([S[s]['resid_N0_real']['delta'] for s in subs]); sm = np.array([S[s]['iaaft_delta_mean'] for s in subs]); pct = np.array([S[s]['real_percentile_in_iaaft'] for s in subs])
        p_surr = float(wilcoxon(sm, alternative='greater').pvalue) if n >= 5 else float('nan')
        rows[row] = {'n': n, 'median_real_delta': float(np.median(real)), 'median_iaaft_delta': float(np.median(sm)), 'p_iaaft_gt0': p_surr, 'median_percentile_of_real': float(np.median(pct))}
        md.append(f"| iaaft (null) | 78 | - | surrogates: {np.median(sm):+.3f} (real {np.median(real):+.3f}) | {(sm>0).mean():.2f} | {p_surr:.4f} | - | - | - | surrogate deltas > 0: {'yes' if p_surr < 0.01 else 'no'} |")
        continue
    z = np.array([S[s]['resid_N0']['shuffle_z'] for s in subs]); d = np.array([S[s]['resid_N0']['delta'] for s in subs])
    pH2 = float(wilcoxon(z, alternative='greater').pvalue)
    dH1 = np.array([S[s]['drive_R']['delta'] - S[s]['drive_N0']['delta'] for s in subs]); dH3 = np.array([S[s]['resid_R']['delta'] - S[s]['resid_N0']['delta'] for s in subs])
    dRs = np.array([S[s]['resid_R']['delta'] - S[s]['resid_Rs']['delta'] for s in subs])
    t1, t3 = tost(dH1), tost(dH3); ok = (np.median(d) > 0) and (pH2 < 0.01)
    rows[row] = {'n': n, 'tau_ms': J['tau_ms'], 'heldout_r': float(np.median([S[s]['heldout_r'] for s in subs])), 'median_resid_delta': float(np.median(d)), 'frac_positive': float((z > 0).mean()), 'p_H2': pH2,
                 'H1_tost_pass': t1, 'H3_tost_pass': t3, 'median_H1_diff': float(np.median(dH1)), 'median_H3_diff': float(np.median(dH3)), 'R_minus_Rs': float(np.median(dRs)), 'H2_ok': bool(ok)}
    h2_ok &= ok; eq_ok &= (t1 and t3)
    if not ok: flips.append(f"{row}: H2")
    if not t1: flips.append(f"{row}: H1 TOST")
    if not t3: flips.append(f"{row}: H3 TOST")
    md.append(f"| {row} | {J['tau_ms']:.0f} | {rows[row]['heldout_r']:+.3f} | {np.median(d):+.3f} | {int((z>0).sum())} / {n} | {pH2:.4f} | {'pass' if t1 else 'FAIL'} ({np.median(dH1):+.3f}) | {'pass' if t3 else 'FAIL'} ({np.median(dH3):+.3f}) | {np.median(dRs):+.3f} | {'yes' if ok else 'NO'} |")
md += ["", f"**H2 robust (rule): {'YES' if h2_ok else 'NO'}.**  **H1/H3 equivalence robust (rule): {'YES' if eq_ok else 'NO'}.**", "",
       ("Rows that flipped: " + "; ".join(flips)) if flips else "No row flipped.", ""]
open('/home/user/arspinet-rhythmic-entrainment/docs/ROBUSTNESS_RESULTS.md', 'w').write("\n".join(md) + "\n")
json.dump({'rows': rows, 'H2_robust': bool(h2_ok), 'equivalence_robust': bool(eq_ok), 'flips': flips}, open('/home/user/arspinet-rhythmic-entrainment/weineck/results/robustness_table.json', 'w'), indent=1)
print("\n".join(md))
