#!/usr/bin/env python3
"""Merge chunked q2_residual outputs and apply the frozen stage-2 group tests.

Frozen rules (docs/PREREGISTRATION_DRAFT.md, commit 935c80a, addendum A1):
 * H2: participant shuffle-z of the residual linear statistic (N0) > 0, one-sided Wilcoxon,
   stage-2 alpha 0.04; secondary: the same for R.
 * H1: delta(R) vs delta(L) on the drive, TOST bounds +-0.10 delta (two one-sided tests at
   alpha 0.05 each, i.e. a 90 % CI inside the bounds); report also the one-sided difference.
 * H3 (conditional on H2): delta(R) vs delta(N0), delta(N2a), delta(N2b) on the residual,
   TOST +-0.10; one-sided paired Wilcoxon R > baseline.
Usage: python3 q2_group_merge.py out.json chunk1.json chunk2.json ...
"""
import sys, json
import numpy as np
from scipy.stats import wilcoxon, ttest_1samp

ALPHA2 = 0.04; BOUND = 0.10


def tost(d, bound=BOUND):
    """Two one-sided t tests for equivalence within +-bound; returns (p_lower, p_upper, equivalent_at_0.05)."""
    d = np.asarray(d, float)
    p_lo = ttest_1samp(d, -bound, alternative='greater').pvalue
    p_hi = ttest_1samp(d, bound, alternative='less').pvalue
    return float(p_lo), float(p_hi), bool(max(p_lo, p_hi) < 0.05)


def main():
    out_path, chunks = sys.argv[1], sys.argv[2:]
    subjects = {}
    for c in chunks:
        subjects.update(json.load(open(c))['subjects'])
    subs = sorted(subjects, key=int)
    sc = lambda s, k, f: subjects[s]['scores'][k][f]
    res = {'n': len(subs), 'subjects': subs, 'N_trials': {s: subjects[s]['scores']['N'] for s in subs}, 'group': {}}
    print(f"stage 2: n = {len(subs)} participants; trials per participant min {min(res['N_trials'].values())} max {max(res['N_trials'].values())}")
    for key in ('drive_N0', 'drive_R', 'resid_N0', 'resid_N2a', 'resid_N2b', 'resid_R', 'resid_R_pop', 'resid_Rs'):
        z = np.array([sc(s, key, 'shuffle_z') for s in subs]); dl = np.array([sc(s, key, 'delta') for s in subs])
        p = float(wilcoxon(z, alternative='greater').pvalue)
        res['group'][key] = {'median_z': float(np.median(z)), 'median_delta': float(np.median(dl)), 'frac_positive': float((z > 0).mean()), 'p_wilcoxon': p, 'z': z.tolist(), 'delta': dl.tolist()}
        print(f"  {key:>11}: median z {np.median(z):+.2f}, median delta {np.median(dl):+.3f}, positive {(z>0).mean():.2f}, p = {p:.4f}")
    h2 = res['group']['resid_N0']['p_wilcoxon'] < ALPHA2
    print(f"\nH2 (residual N0 > 0) at stage 2, alpha {ALPHA2}: {'SUPPORTED' if h2 else 'NOT SUPPORTED'} (p = {res['group']['resid_N0']['p_wilcoxon']:.4f}); secondary R: p = {res['group']['resid_R']['p_wilcoxon']:.4f}")
    res['H2'] = {'supported': bool(h2), 'p': res['group']['resid_N0']['p_wilcoxon'], 'alpha': ALPHA2}
    # H1: drive R vs L
    d = np.array([sc(s, 'drive_R', 'delta') - sc(s, 'drive_N0', 'delta') for s in subs]); plo, phi, eq = tost(d)
    p_gt = float(wilcoxon(d, alternative='greater').pvalue); p_lt = float(wilcoxon(d, alternative='less').pvalue)
    res['H1'] = {'paired_delta_R_minus_L': d.tolist(), 'median': float(np.median(d)), 'tost_p': [plo, phi], 'equivalent': eq, 'p_R_gt_L': p_gt, 'p_R_lt_L': p_lt}
    print(f"H1 (drive): median delta R - L {np.median(d):+.3f}; TOST p = {plo:.3f}, {phi:.3f} -> {'EQUIVALENT within +-0.10' if eq else 'not shown equivalent'}; R > L p = {p_gt:.3f}, R < L p = {p_lt:.3f}")
    # H3
    res['H3'] = {}
    for b in ('resid_N0', 'resid_N2a', 'resid_N2b'):
        d = np.array([sc(s, 'resid_R', 'delta') - sc(s, b, 'delta') for s in subs]); plo, phi, eq = tost(d); p_gt = float(wilcoxon(d, alternative='greater').pvalue)
        res['H3'][b] = {'median': float(np.median(d)), 'tost_p': [plo, phi], 'equivalent': eq, 'p_R_gt_baseline': p_gt}
        print(f"H3 (residual) R - {b}: median {np.median(d):+.3f}; TOST -> {'equivalent' if eq else 'not shown equivalent'}; R > baseline p = {p_gt:.3f}" + ("" if h2 else "   [H2 not supported: descriptive only]"))
    json.dump(res, open(out_path, 'w'), indent=1)


if __name__ == '__main__':
    main()
