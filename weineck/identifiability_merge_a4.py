#!/usr/bin/env python3
"""Identifiability addendum A4 merge (exploratory, outside the committed rule; docs/IDENTIFIABILITY_PLAN.md A4).
A4.1: criterion-1 pass rates under nested lambda for Worlds A and C, Clopper-Pearson 95 % intervals, W80 brackets.
A4.2: criterion-2 pass rates for Worlds A and C at w 0.8 / 0.9 / 1.0 with the committed lambda pair (Hopf 10, linear 1),
both at 1, both at 10 (lampair reruns, 20 datasets), and both nested (nested cells, 10 datasets).
Adds key 'A4' to weineck/results/identifiability.json.
"""
import json, glob, re, os
import numpy as np
from scipy.stats import beta as betad

D = '/home/user/arspinet-rhythmic-entrainment/weineck/results/identifiability'


def cp(k, n, a=0.05):
    lo = 0.0 if k == 0 else betad.ppf(a / 2, k, n - k + 1); hi = 1.0 if k == n else betad.ppf(1 - a / 2, k + 1, n - k); return [float(lo), float(hi)]


def rate(flags): k = int(sum(flags)); n = len(flags); return {'rate': k / n if n else None, 'k': k, 'n': n, 'ci95': cp(k, n) if n else None}


def per_dataset(path, logpath):
    """per-dataset (crit1 pass, crit2 pass or None, supported, source) for a cell; crit2 from stored p2 if present,
    else inferred from 'supported' when criterion 1 passed (supported = crit1 and crit2), else None."""
    d = json.load(open(path)); pdz = d['per_dataset']; n = d['datasets_done']
    if 'p1' in pdz:
        c1 = [pdz['delta_r'][i] > 0 and pdz['p1'][i] < 0.01 for i in range(n)]; c2 = [pdz['p2'][i] < 0.05 for i in range(n)]; src = 'stored'
    else:
        rows = [re.search(r'supported=(\w+) median delta_r ([+-][\d.]+) p=([\d.]+)', l) for l in open(logpath)]; rows = [m for m in rows if m][:n]
        c1 = [float(m.group(2)) > 0 and float(m.group(3)) < 0.01 for m in rows]; c2 = [(pdz['supported'][i] if c1[i] else None) for i in range(n)]; src = 'criterion 1 from log; criterion 2 inferred from supported where criterion 1 passed'
    return c1, c2, pdz['supported'][:n], src


def w80(pts):
    pts = sorted((w, r) for w, r in pts if r is not None)
    for i, (w, r) in enumerate(pts):
        if r >= 0.8:
            if i == 0: return {'W80': None, 'bracket': [None, w], 'note': f'already >= 0.8 at the lowest w run ({w})'}
            w0, r0 = pts[i - 1]; return {'W80': w0 + (0.8 - r0) * (w - w0) / (r - r0), 'bracket': [w0, w]}
    return {'W80': None, 'bracket': None, 'note': 'not reached'}


def main():
    out = {'note': 'exploratory, outside the committed rule (docs/IDENTIFIABILITY_PLAN.md, addendum A4)', 'criterion1_nested': {}, 'criterion2_lambda_pair': {}}
    for world, cdir, logdir, logpat in [('A', 'cells_nested', ['logs_a3', 'logs_a4'], ['A_nested_w{w}_r0.04_n40_t12.log', 'A_nested_w{w}.log']), ('C', 'cells_nested_C', ['logs_a4'], ['C_nested_w{w}.log'])]:
        rows = {}
        for f in sorted(glob.glob(f'{D}/{cdir}/w*_r0.04_n40_t12.json')):
            w = float(re.search(r'/w([\d.]+)_r', f).group(1)); ws = f'{w:g}' if w not in (0.0, 1.0) else ('0' if w == 0 else '1')
            logs = [f'{D}/{ld}/{lp.format(w=ws)}' for ld, lp in zip(logdir, logpat)] + [f'{D}/{ld}/{lp.format(w=w)}' for ld, lp in zip(logdir, logpat)]
            lg = next((l for l in logs if os.path.exists(l)), None)
            c1, c2, sup, src = per_dataset(f, lg)
            rows[str(w)] = {'criterion1': rate(c1), 'criterion2': rate([x for x in c2 if x is not None]) | {'n_known': sum(x is not None for x in c2)}, 'full_rule': rate(sup), 'source': src}
        out['criterion1_nested'][world] = {'by_w': dict(sorted(rows.items(), key=lambda kv: float(kv[0]))), 'W80_criterion1': w80([(float(w), v['criterion1']['rate']) for w, v in rows.items()]),
                                           'W80_full_rule': w80([(float(w), v['full_rule']['rate']) for w, v in rows.items() if float(w) > 0])}
    for world in ('A', 'C'):
        byw = {}
        for w in (0.8, 0.9, 1.0):
            e = {}
            f = f'{D}/cells_lampair/{world}_w{w}_r0.04_n40_t12.json'
            if os.path.exists(f):
                L = json.load(open(f))['lambda_pair']
                for k, name in [('committed_10_vs_1', 'committed pair (Hopf 10, linear 1)'), ('both_1', 'both lambda 1'), ('both_10', 'both lambda 10')]:
                    e[name] = rate([x[k]['p2'] < 0.05 for x in L]) | {'median_aug_minus_lin': float(np.median([x[k]['median'] for x in L]))}
            nest = out['criterion1_nested'][world]['by_w'].get(str(w))
            if nest: e['both nested (own inner loop)'] = nest['criterion2'] | {'source': nest['source']}
            byw[str(w)] = e
        out['criterion2_lambda_pair'][world] = byw
    full = json.load(open(f'{D}/../identifiability.json')); full['A4'] = out; json.dump(full, open(f'{D}/../identifiability.json', 'w'), indent=1)
    json.dump(out, open(f'{D}/a4_summary.json', 'w'), indent=1); print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
