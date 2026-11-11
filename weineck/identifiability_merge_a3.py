#!/usr/bin/env python3
"""Identifiability addendum A3 merge (docs/IDENTIFIABILITY_PLAN.md, A3.5): W80 for World A (operating point
and two refined cells), World B, World C and the nested-lambda check side by side, false-positive rates and
Clopper-Pearson 95 % intervals; R^2 of P_o on the TRF designs over all 34 kernels; the A3 decision rule
applied verbatim. Adds key 'A3' to weineck/results/identifiability.json and draws docs/figures/identifiability_a3.png.
"""
import json, glob, os, sys
import numpy as np
from scipy.stats import beta as betad
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
sys.argv = sys.argv[:1]
from identifiability_sim import Store

D = '/home/user/arspinet-rhythmic-entrainment/weineck/results/identifiability'; FIG = '/home/user/arspinet-rhythmic-entrainment/docs/figures'
OP = (0.04, 40, 12)


def cp(k, n, a=0.05):
    lo = 0.0 if k == 0 else betad.ppf(a / 2, k, n - k + 1); hi = 1.0 if k == n else betad.ppf(1 - a / 2, k + 1, n - k); return [float(lo), float(hi)]


def load(sub, r, n, t):
    out = {}
    for f in glob.glob(f'{D}/{sub}/w*_r{r}_n{n}_t{t}.json'):
        d = json.load(open(f)); k = int(sum(d['per_dataset']['supported'])); m = d['datasets_done']
        out[float(d['w'])] = {'rate': d['detection_rate'], 'k': k, 'n': m, 'ci95': cp(k, m), 'median_delta_r': d['median_delta_r'], 'realised_r_short': d['realised_r_short'], 'complete': m >= d.get('datasets_planned', m), 'raw': d}
    return dict(sorted(out.items()))


def crit1_rates(logdir, prefix, r, n, t):
    """DIAGNOSTIC, not part of the committed rule: fraction of datasets passing criterion 1 alone
    (median delta r > 0 and one-sided Wilcoxon p < 0.01 for aug vs best TRF), parsed from the per-dataset
    log lines; the remaining failures are criterion 2 (aug vs aug_lin, p < 0.05)."""
    import re
    out = {}
    for f in glob.glob(f'{D}/{logdir}/{prefix}w*_r{r}_n{n}_t{t}.log'):
        rows = [re.search(r'w=([\d.]+) .*supported=(\w+) median delta_r ([+-][\d.]+) p=([\d.]+)', l) for l in open(f)]
        rows = [m for m in rows if m]
        if not rows: continue
        w = float(rows[0].group(1)); c1 = [float(m.group(3)) > 0 and float(m.group(4)) < 0.01 for m in rows]; sup = [m.group(2) == 'True' for m in rows]
        out[str(w)] = {'n': len(rows), 'criterion1_pass': float(np.mean(c1)), 'criterion1_ci95': cp(int(sum(c1)), len(rows)), 'full_rule': float(np.mean(sup))}
    return dict(sorted(out.items(), key=lambda kv: float(kv[0])))


def w80(cells):
    ws = [w for w in cells if w > 0]; rs = [cells[w]['rate'] for w in ws]
    for i, (w, r) in enumerate(zip(ws, rs)):
        if r >= 0.8:
            if i == 0: return {'W80': float(w), 'bracket': [0.0, float(w)]}
            w0, r0 = ws[i - 1], rs[i - 1]; return {'W80': float(w0 + (0.8 - r0) * (w - w0) / (r - r0)), 'bracket': [float(w0), float(w)]}
    return {'W80': None, 'bracket': None, 'note': 'not reached'}


def main():
    res = {}
    worlds = {'A': load('cells', *OP), 'B': load('cells_B', *OP), 'C': load('cells_C', *OP), 'A_nested_lambda': load('cells_nested', *OP),
              'A_r0.08_n40': load('cells', 0.08, 40, 12), 'A_r0.04_n160': load('cells', 0.04, 160, 12)}
    for name, cells in worlds.items():
        res[name] = {'w80': w80(cells), 'false_positive': ({k: cells[0.0][k] for k in ('rate', 'k', 'n', 'ci95')} if 0.0 in cells else None),
                     'by_w': {str(w): {k: v for k, v in c.items() if k != 'raw'} for w, c in cells.items()}}
    # nested vs fixed, paired on the same 10 datasets (same seeds)
    pair = {}
    for w, c in worlds['A_nested_lambda'].items():
        fx = worlds['A'].get(w)
        if fx is None: continue
        n = c['n']; fsup = fx['raw']['per_dataset']['supported'][:n]; fdr = fx['raw']['per_dataset']['delta_r'][:n]
        pair[str(w)] = {'nested': {'rate': c['rate'], 'ci95': c['ci95'], 'median_delta_r': c['median_delta_r']},
                        'fixed_same_datasets': {'rate': float(np.mean(fsup)), 'ci95': cp(int(sum(fsup)), n), 'median_delta_r': float(np.median(fdr))},
                        'fixed_all_20': {'rate': fx['rate'], 'median_delta_r': fx['median_delta_r']},
                        'chosen_lambda_counts': c['raw'].get('chosen_lambda_counts')}
    res['nested_vs_fixed'] = pair
    res['diagnostic_criterion1_only'] = {'note': 'not part of the committed rule; criterion 1 = aug beats the best TRF (median > 0, p < 0.01); full rule also needs aug > aug_lin (p < 0.05)',
        'A': crit1_rates('logs', '', *OP), 'B': crit1_rates('logs_a3', 'B_fixed_', *OP), 'C': crit1_rates('logs_a3', 'C_fixed_', *OP), 'A_nested_lambda': crit1_rates('logs_a3', 'A_nested_', *OP)}
    res['diagnostic_criterion1_only']['W80_criterion1_only'] = {k: w80({float(w): {'rate': v['criterion1_pass']} for w, v in d.items()}) for k, d in res['diagnostic_criterion1_only'].items() if isinstance(d, dict) and d}
    # R^2 of P_o on the TRF designs, all 34 kernels
    st = Store(); r2 = {s: st.osc_kernel(s, 'C')[1] for s in st.ksubs}
    a = np.array([v['R2_short_trf'] for v in r2.values()]); b = np.array([v['R2_long_trf'] for v in r2.values()])
    res['R2_P_o_on_TRF'] = {'short_0_400ms': {'median': float(np.median(a)), 'q25': float(np.percentile(a, 25)), 'q75': float(np.percentile(a, 75)), 'min': float(a.min()), 'max': float(a.max())},
                            'long_0_1000ms': {'median': float(np.median(b)), 'q25': float(np.percentile(b, 25)), 'q75': float(np.percentile(b, 75)), 'min': float(b.min()), 'max': float(b.max())},
                            'per_participant': r2, 'n': len(r2)}
    # decision rule (A3, committed before any A3 cell ran)
    def gt08(x): return x['W80'] is None or x['W80'] > 0.8
    WC = res['C']['w80']; nest = worlds['A_nested_lambda']
    nested_gt08 = (0.5 in nest) and nest[0.5]['rate'] < 0.8
    if WC['W80'] is not None and WC['W80'] <= 0.6:
        verdict = f"World C W80 = {WC['W80']:.2f} <= 0.6: headline becomes 'the rule detects TRF-inexpressible oscillator structure above {100 * WC['W80']:.0f} % amplitude'; World A's 0.89 relabelled as a collinearity effect"
    elif gt08(res['B']['w80']) and gt08(WC) and nested_gt08:
        verdict = "W80 > 0.8 in World B, World C and the nested-lambda check: the 0.89 headline stands as a property of the rule"
    else:
        verdict = "outcome not covered by the A3 rule; reported with the numbers, no relabelling made"
    res['decision'] = {'verdict': verdict, 'inputs': {'W80_B': res['B']['w80'], 'W80_C': WC, 'nested_rate_w0.5': nest.get(0.5, {}).get('rate'), 'nested_rate_w0.9': nest.get(0.9, {}).get('rate')}}
    full = json.load(open(f'{D}/../identifiability.json')); full['A3'] = res; json.dump(full, open(f'{D}/../identifiability.json', 'w'), indent=1)
    # figure
    fig, ax = plt.subplots(figsize=(7.5, 4.2), constrained_layout=True)
    for name, mk, ls, lab in [('A', 'o', '-', 'World A (committed)'), ('B', 's', '--', 'World B (power-matched)'), ('C', '^', ':', 'World C (TRF-inexpressible part only)'), ('A_nested_lambda', 'D', '-.', 'World A, nested lambda (10 datasets)')]:
        c = worlds[name]
        if not c: continue
        ws = list(c); rs = [c[w]['rate'] for w in ws]; lo = [c[w]['rate'] - c[w]['ci95'][0] for w in ws]; hi = [c[w]['ci95'][1] - c[w]['rate'] for w in ws]
        ax.errorbar(np.array(ws) + {'A': -0.009, 'B': -0.003, 'C': 0.003, 'A_nested_lambda': 0.009}[name], rs, yerr=[lo, hi], marker=mk, ls=ls, color='k', mfc='white' if name in ('B', 'A_nested_lambda') else 'k', capsize=2, label=lab)
    ax.axhline(0.8, color='grey', lw=0.8); ax.set_xlabel('w (amplitude share of the oscillator component)'); ax.set_ylabel('rate "oscillator supported" (95 % Clopper-Pearson)')
    ax.set_ylim(-0.03, 1.03); ax.legend(fontsize=8, loc='upper left'); ax.set_title('Addendum A3 at the operating point (r 0.04, 40 trials, 12 tempi)', fontsize=10)
    os.makedirs(FIG, exist_ok=True); fig.savefig(f'{FIG}/identifiability_a3.png', dpi=150); plt.close(fig)
    print(json.dumps({k: (v['w80'], v['false_positive']) for k, v in res.items() if isinstance(v, dict) and 'w80' in v}, indent=1, default=str))
    print(json.dumps(pair, indent=1)); print(json.dumps({k: v for k, v in res['R2_P_o_on_TRF'].items() if k != 'per_participant'}, indent=1)); print(json.dumps(res['diagnostic_criterion1_only'], indent=1)); print(res['decision']['verdict'])


if __name__ == '__main__':
    main()
