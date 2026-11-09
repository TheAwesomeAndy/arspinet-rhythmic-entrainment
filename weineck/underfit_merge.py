#!/usr/bin/env python3
"""Group tables for the exploratory underfitting check (A-C). Usage: underfit_merge.py out.json chunk*.json"""
import sys, json
import numpy as np
from scipy.stats import wilcoxon

out_path, chunks = sys.argv[1], sys.argv[2:]
S = {}
for c in chunks:
    S.update(json.load(open(c))['subjects'])
subs = sorted(S, key=int); n = len(subs)
print(f"exploratory underfitting check: n = {n} participants")
print(f"held-out r (fronto-central): within-participant median {np.median([S[s]['heldout_r_within'] for s in subs]):+.3f}, pooled LOPO {np.median([S[s]['heldout_r_pooled'] for s in subs]):+.3f}, linear-world {np.median([S[s]['heldout_r_sim'] for s in subs]):+.3f}")
res = {'n': n, 'rows': {}}
print(f"{'quantity':>28} | {'median delta':>12} | {'positive':>8} | {'Wilcoxon p (z>0)':>16}")
for key, label in (('drive', 'drive (real EEG)'), ('resid_real', 'residual, within-participant TRF (= stage 2)'), ('pred', 'B: TRF prediction itself'),
                   ('resid_pooled', 'A: residual, pooled LOPO TRF'), ('sim_drive', 'C: linear-world drive'), ('resid_sim', 'C: linear-world residual')):
    z = np.array([S[s][key]['shuffle_z'] for s in subs]); d = np.array([S[s][key]['delta'] for s in subs])
    p = float(wilcoxon(z, alternative='greater').pvalue) if np.any(z != 0) else float('nan')
    res['rows'][key] = {'median_delta': float(np.median(d)), 'frac_positive': float((z > 0).mean()), 'p': p, 'delta': d.tolist(), 'z': z.tolist()}
    print(f"{label:>28} | {np.median(d):+12.3f} | {(z>0).mean():8.2f} | {p:16.4f}")
ratio = np.array([S[s]['pred']['delta'] / S[s]['drive']['delta'] if S[s]['drive']['delta'] > 0 else np.nan for s in subs])
print(f"\nB: prediction delta / drive delta, median over participants with positive drive delta: {np.nanmedian(ratio):.2f}")
d_real = np.array([S[s]['resid_real']['delta'] for s in subs]); d_sim = np.array([S[s]['resid_sim']['delta'] for s in subs])
pd = float(wilcoxon(d_real - d_sim, alternative='greater').pvalue)
print(f"Decision rule: real residual delta {np.median(d_real):+.3f} vs linear-world residual delta {np.median(d_sim):+.3f}; paired real > linear-world p = {pd:.4f}")
res['decision'] = {'median_real': float(np.median(d_real)), 'median_linear_world': float(np.median(d_sim)), 'p_real_gt_linear_world': pd}
json.dump(res, open(out_path, 'w'), indent=1)
