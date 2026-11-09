#!/usr/bin/env python3
"""Group tables and the committed decision for Theory 3 (docs/OSCILLATOR_DECISION_RULE.md).
Usage: oscillator_merge.py out.json in1.json [in2.json ...]
Primary metric per participant: delta_r = mean over held-out tempi of r_fc(aug) minus the
best evoked baseline (max of d_short, d_long by participant mean). Control: the same with
aug_lin. Rule: supported iff median delta_r > 0, one-sided Wilcoxon p < .01, AND
delta_r(aug) > delta_r(aug_lin) paired one-sided p < .05. Preferred-rate effect: negative
quadratic term of delta_r vs tempo (per-participant quadratic fits, Wilcoxon on the
coefficient < 0), with the fitted peak inside 1-4 Hz."""
import sys, json
import numpy as np
from scipy.stats import wilcoxon

out_path, ins = sys.argv[1], sys.argv[2:]
S = {}
for p in ins:
    S.update(json.load(open(p))['subjects'])
subs = sorted(S, key=int); n = len(subs)
MODELS = ['hopf', 'rf', 'lin', 'd_short', 'd_long', 'aug', 'aug_lin']


def mean_r(s, m):
    return np.mean([v['r_fc'] for v in S[s]['models'][m].values()])


print(f"Theory 3 (exploratory): n = {n} participants; mean held-out-tempo r at fronto-central channels")
print(f"{'model':>8} | {'median r':>9} | {'participants r>0':>16}")
tab = {}
for m in MODELS:
    r = np.array([mean_r(s, m) for s in subs]); tab[m] = r
    print(f"{m:>8} | {np.median(r):+9.4f} | {(r>0).mean():16.2f}")
best_evoked = np.maximum(tab['d_short'], tab['d_long'])
d_aug = tab['aug'] - best_evoked; d_lin = tab['aug_lin'] - best_evoked; d_rf = tab['rf'] - best_evoked; d_hopf = tab['hopf'] - best_evoked
p_aug = float(wilcoxon(d_aug, alternative='greater').pvalue); p_vs_lin = float(wilcoxon(d_aug - d_lin, alternative='greater').pvalue)
print(f"\ndelta_r (aug - best evoked): median {np.median(d_aug):+.4f}, positive {(d_aug>0).mean():.2f}, one-sided p = {p_aug:.4f}")
print(f"delta_r (aug_lin - best evoked): median {np.median(d_lin):+.4f}, positive {(d_lin>0).mean():.2f}")
print(f"aug vs aug_lin (paired, one-sided aug > aug_lin): p = {p_vs_lin:.4f}")
print(f"spiking (rf - best evoked): median {np.median(d_rf):+.4f}; hopf alone - best evoked: median {np.median(d_hopf):+.4f}")
supported = (np.median(d_aug) > 0) and (p_aug < 0.01) and (p_vs_lin < 0.05)
# preferred-rate effect: per-participant quadratic fit of delta_r(tempo)
quad = []; peaks = []
for s in subs:
    temps = sorted(set(S[s]['models']['aug']) & set(S[s]['models']['d_short']) & set(S[s]['models']['d_long']))
    f = np.array([float(t) for t in temps])
    dr = np.array([S[s]['models']['aug'][t]['r_fc'] - max(S[s]['models']['d_short'][t]['r_fc'], S[s]['models']['d_long'][t]['r_fc']) for t in temps])
    if len(f) >= 5:
        c = np.polyfit(f, dr, 2); quad.append(c[0]); peaks.append(-c[1] / (2 * c[0]) if c[0] != 0 else np.nan)
quad = np.array(quad); peaks = np.array(peaks)
p_quad = float(wilcoxon(quad, alternative='less').pvalue) if len(quad) >= 5 else float('nan')
peak_med = float(np.nanmedian(peaks[quad < 0])) if np.any(quad < 0) else float('nan')
pref = (p_quad < 0.05) and (1.0 <= peak_med <= 4.0)
print(f"preferred-rate: quadratic coefficient median {np.median(quad):+.5f}, negative in {(quad<0).mean():.2f}, Wilcoxon (<0) p = {p_quad:.4f}; median peak (negative fits) {peak_med:.2f} Hz")
# delta_r vs tempo curve (group median)
curve = {}
for t in [str(float(x)) for x in np.arange(1.0, 4.01, 0.25)]:
    vals = [S[s]['models']['aug'][t]['r_fc'] - max(S[s]['models']['d_short'][t]['r_fc'], S[s]['models']['d_long'][t]['r_fc']) for s in subs if t in S[s]['models']['aug']]
    if vals: curve[t] = {'median_delta_r': float(np.median(vals)), 'n': len(vals)}
print("delta_r vs tempo (group median): " + ", ".join(f"{float(t):.2f}:{v['median_delta_r']:+.4f}" for t, v in curve.items()))
verdict = ("OSCILLATOR SUPPORTED" if supported else "NOT SUPPORTED") + ("; PREFERRED-RATE EFFECT" if pref else "; no preferred-rate effect")
print(f"\nDECISION (rule applied verbatim): {verdict}")
json.dump({'n': n, 'median_r': {m: float(np.median(tab[m])) for m in MODELS}, 'delta_r_aug': d_aug.tolist(), 'delta_r_aug_lin': d_lin.tolist(), 'p_aug': p_aug, 'p_aug_vs_lin': p_vs_lin,
           'quad_coeffs': quad.tolist(), 'p_quad': p_quad, 'peak_median_hz': peak_med, 'curve': curve, 'supported': bool(supported), 'preferred_rate': bool(pref), 'verdict': verdict}, open(out_path, 'w'), indent=1)
