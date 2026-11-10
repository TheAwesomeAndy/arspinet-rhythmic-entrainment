#!/usr/bin/env python3
"""Identifiability map, stage 3: merge cells into weineck/results/identifiability.json, draw the heat maps
(detection rate vs (held-out r, trials per tempo) per w, Weineck's operating point marked) and solve the
headline W by linear interpolation of detection rate over w at the operating point (docs/IDENTIFIABILITY_PLAN.md).
"""
import json, glob, os, re
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

D = '/home/user/arspinet-rhythmic-entrainment/weineck/results/identifiability'; FIG = '/home/user/arspinet-rhythmic-entrainment/docs/figures'
WS = [0.0, 0.1, 0.25, 0.5, 1.0]; RS = [0.02, 0.04, 0.08, 0.16]; NS = [20, 40, 80, 160]; TS = [4, 8, 12]; OP = (0.04, 40, 12)


def main():
    cells = {}
    for f in glob.glob(f'{D}/cells/*.json'):
        d = json.load(open(f)); cells[(float(d['w']), float(d['r_target']), int(d['trials']), int(d['ntempi']))] = d
    cal = json.load(open(f'{D}/calibration.json'))
    out = {'plan': 'docs/IDENTIFIABILITY_PLAN.md', 'calibration': cal, 'cells': []}
    for k, d in sorted(cells.items()):
        out['cells'].append({'w': k[0], 'variance_share': k[0] ** 2 / (k[0] ** 2 + (1 - k[0]) ** 2), 'r_target': k[1], 'trials_per_tempo': k[2], 'training_tempi': k[3], 'datasets': d['datasets_done'],
                             'rate': d['detection_rate'], 'kind': 'false_positive' if k[0] == 0 else 'detection', 'median_delta_r': d['median_delta_r'], 'realised_r_short': d['realised_r_short'], 'complete': d['datasets_done'] >= 20})
    # headline at the operating point
    def w80(ws, rs):
        ws, rs = np.array(ws), np.array(rs)
        if rs.max() < 0.8: return None
        i = int(np.argmax(rs >= 0.8)); return float(ws[i]) if i == 0 else float(ws[i - 1] + (0.8 - rs[i - 1]) * (ws[i] - ws[i - 1]) / (rs[i] - rs[i - 1]))
    wop = sorted(k[0] for k in cells if k[1:] == OP)                      # refined w grid at the operating point (plan addendum)
    rates = [cells[(w,) + OP]['detection_rate'] for w in wop]
    head = {'operating_point': {'r_target': OP[0], 'trials_per_tempo': OP[1], 'training_tempi': OP[2]}, 'rate_by_w': dict(zip(map(str, wop), rates)), 'false_positive_rate': cells[(0.0,) + OP]['detection_rate'] if (0.0,) + OP in cells else None,
            'realised_r_short_by_w': {str(w): cells[(w,) + OP]['realised_r_short'] for w in wop}, 'median_delta_r_by_w': {str(w): cells[(w,) + OP]['median_delta_r'] for w in wop}}
    pos = [(w, r) for w, r in zip(wop, rates) if w > 0]
    if pos:
        W = w80(*zip(*pos)); head['W_80_percent_power_amplitude_share'] = W; head['W_80_percent_power_variance_share'] = None if W is None else W ** 2 / (W ** 2 + (1 - W) ** 2)
        coarse = [(w, r) for w, r in pos if w in WS]; head['W_80_coarse_grid'] = w80(*zip(*coarse)) if coarse else None
    # W80 for every (r, n) at 12 tempi on the coarse w grid
    head['W_80_coarse_by_cell'] = {f'r{r}_n{n}': w80(*zip(*[(w, cells[(w, r, n, 12)]['detection_rate']) for w in WS[1:] if (w, r, n, 12) in cells])) for r in RS for n in NS if all((w, r, n, 12) in cells for w in WS[1:])}
    out['headline'] = head
    fp = [c for c in out['cells'] if c['kind'] == 'false_positive' and c['complete']]
    out['false_positive_summary'] = {'cells': len(fp), 'max_rate': max([c['rate'] for c in fp], default=None), 'cells_above_0.05': [(c['r_target'], c['trials_per_tempo'], c['training_tempi'], c['rate']) for c in fp if c['rate'] > 0.05]}
    json.dump(out, open(f'{D}/../identifiability.json', 'w'), indent=1)
    # heat maps
    os.makedirs(FIG, exist_ok=True)
    fig, axes = plt.subplots(1, 5, figsize=(16, 3.6), constrained_layout=True)
    for ax, w in zip(axes, WS):
        M = np.full((len(NS), len(RS)), np.nan)
        for i, n in enumerate(NS):
            for j, r in enumerate(RS):
                c = cells.get((w, r, n, 12)); M[i, j] = c['detection_rate'] if c else np.nan
        im = ax.imshow(M, origin='lower', vmin=0, vmax=1, cmap='Greys', aspect='auto')
        for i in range(len(NS)):
            for j in range(len(RS)):
                if np.isfinite(M[i, j]): ax.text(j, i, f'{M[i, j]:.2f}', ha='center', va='center', fontsize=8, color='white' if M[i, j] > 0.55 else 'black')
        ax.set_xticks(range(len(RS))); ax.set_xticklabels(RS); ax.set_yticks(range(len(NS))); ax.set_yticklabels(NS)
        ax.set_xlabel('held-out r of the evoked model (target)'); ax.set_title(('false-positive rate' if w == 0 else 'detection rate') + f', w = {w}')
        ax.plot(RS.index(OP[0]), NS.index(OP[1]), marker='o', mfc='none', mec='red', mew=2, ms=22, ls='none')
    axes[0].set_ylabel('trials per tempo'); fig.colorbar(im, ax=axes, shrink=0.8, label='rate over 20 simulated datasets')
    fig.suptitle('Identifiability of an oscillator component under the committed Theory 3 rule (12 training tempi; red: Weineck 2022 operating point)')
    fig.savefig(f'{FIG}/identifiability_heatmap.png', dpi=150); plt.close(fig)
    # n-tempi axis and operating-point curve
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4), constrained_layout=True)
    axes[0].plot(wop, rates, 'ko-'); axes[0].axhline(0.8, color='grey', ls='--'); axes[0].set_xlabel('w (amplitude share of the oscillator component)'); axes[0].set_ylabel('rate'); axes[0].set_title('operating point: r 0.04, 40 trials, 12 tempi'); axes[0].set_ylim(-0.02, 1.02)
    for t, mk in zip(TS, ['s', '^', 'o']):
        rr = [cells[(w, 0.04, 40, t)]['detection_rate'] if (w, 0.04, 40, t) in cells else np.nan for w in WS]; axes[1].plot(WS, rr, marker=mk, color='k', ls='-' if t == 12 else ':', label=f'{t} training tempi')
    axes[1].axhline(0.8, color='grey', ls='--'); axes[1].legend(); axes[1].set_xlabel('w'); axes[1].set_title('training-tempi axis (r 0.04, 40 trials)'); axes[1].set_ylim(-0.02, 1.02)
    fig.savefig(f'{FIG}/identifiability_tempi.png', dpi=150); plt.close(fig)
    print(json.dumps(head, indent=1)); print('false positives:', out['false_positive_summary']); print(f"{len(cells)} cells, {sum(c['complete'] for c in out['cells'])} complete")


if __name__ == '__main__':
    main()
