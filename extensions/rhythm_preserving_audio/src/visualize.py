#!/usr/bin/env python3
"""Figures for the extension (grayscale-legible: line style and marker carry the identity, not colour).

  fig_aliasing.pdf  : timing measures under exact grid shifts, periodic vs nonperiodic stimuli (simulated)
  fig_training.pdf  : rectified-flow training and validation loss, V0 vs V1 (measured)
  fig_tradeoff.pdf  : D1 (floor-normalised onset F1) vs T1 (LTAS distance) across strengths, V0 vs V1, with
                      identity / reconstruction / oracle / DSP reference points, per family (measured)
  fig_example.pdf   : one nonperiodic probe composition: source, V0 and V1 edits at one strength, with
                      ground-truth and detected onsets (measured)
"""
import json, os, sys
import numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); R = os.path.join(ROOT, 'results'); F = os.path.join(ROOT, 'figures')
plt.rcParams.update({'font.size': 8, 'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 300})
STYLE = {'V0': dict(color='0.45', ls='--', marker='o', mfc='white'), 'V1': dict(color='0.0', ls='-', marker='s')}


def fig_aliasing():
    d = json.load(open(os.path.join(R, 'aliasing_validation.json')))['group_medians']; ctrl = ['identity', 'shift_0.25step', 'shift_0.5step', 'shift_1step', 'shift_2step', 'shift_4step']
    lab = ['0', '1/4', '1/2', '1', '2', '4\n(beat)']; fig, ax = plt.subplots(1, 3, figsize=(7.2, 2.3))
    for fam, st in (('periodic', dict(color='0.5', ls='--', marker='o', mfc='white')), ('nonperiodic', dict(color='0', ls='-', marker='s'))):
        for a, k, yl in zip(ax, ('greedy_f1', 'greedy_dev_ms', 'lag_specificity'), ('onset F1 (+-50 ms)', 'matched-onset deviation (ms)', 'lag-0 specificity')):
            a.plot(range(len(ctrl)), [d[fam][c][k] for c in ctrl], label=fam, **st); a.set_xticks(range(len(ctrl))); a.set_xticklabels(lab); a.set_xlabel('global shift (16th steps)'); a.set_ylabel(yl)
    ax[0].axhline(d['periodic']['identity']['alias_floor'], color='0.5', lw=0.6, ls=':'); ax[0].axhline(d['nonperiodic']['identity']['alias_floor'], color='0', lw=0.6, ls=':')
    ax[2].axhline(0, color='0.7', lw=0.6); ax[2].legend(frameon=False, loc='lower right', fontsize=6)
    ax[1].set_title('deviation looks perfect after a whole-step shift', fontsize=7, loc='left'); fig.tight_layout(); fig.savefig(os.path.join(F, 'fig_aliasing.pdf')); fig.savefig(os.path.join(F, 'fig_aliasing.png')); plt.close(fig)


def fig_training():
    d = json.load(open(os.path.join(R, 'rf_training.json'))); fig, ax = plt.subplots(1, 1, figsize=(3.4, 2.3))
    for v in ('V0', 'V1'):
        tr = np.array(d[v]['loss']['train']); va = np.array(d[v]['loss']['val'])
        ax.plot(tr[:, 0], tr[:, 1], color=STYLE[v]['color'], ls=STYLE[v]['ls'], lw=0.8, label=f'{v} train'); ax.plot(va[:, 0], va[:, 1], color=STYLE[v]['color'], ls='', marker=STYLE[v]['marker'], mfc=STYLE[v].get('mfc', STYLE[v]['color']), ms=4, label=f'{v} val')
    ax.set_xlabel('step'); ax.set_ylabel('flow-matching MSE'); ax.set_yscale('log'); ax.legend(frameon=False, fontsize=6); fig.tight_layout()
    fig.savefig(os.path.join(F, 'fig_training.pdf')); fig.savefig(os.path.join(F, 'fig_training.png')); plt.close(fig)


def fig_tradeoff():
    """D1 vs T1. Display only: y clipped to [-1, 1.05] and x to [0, 8] dB; off-scale points drawn at the edge
    with their value written next to them (all values are in results/rf_eval.json)."""
    d = json.load(open(os.path.join(R, 'rf_eval.json'))); fig, ax = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True); YL, XL = (-1.0, 1.05), (0, 8)
    clip = lambda v, lo, hi: min(max(v, lo), hi)
    def put(a, x, y, **kw):
        a.plot(clip(x, *XL), clip(y, *YL), **kw)
        if not (XL[0] <= x <= XL[1] and YL[0] <= y <= YL[1]): a.annotate(f'({x:.1f}, {y:.1f})', (clip(x, *XL), clip(y, *YL)), fontsize=5, xytext=(-30, 4), textcoords='offset points')
    for a, fam in zip(ax, ('nonperiodic', 'periodic')):
        D = d['decision'][fam]
        for v in ('V0', 'V1'):
            c = D['median_curves'][v]; ks = sorted(c, key=float)
            a.plot([clip(c[k]['ltas_db'], *XL) for k in ks], [clip(c[k]['f1_norm'], *YL) for k in ks], label=f'{v} (median of 8 compositions)', **STYLE[v])
            for k in ks:
                put(a, c[k]['ltas_db'], c[k]['f1_norm'], ls='', marker='')
                a.annotate(k, (clip(c[k]['ltas_db'], *XL), clip(c[k]['f1_norm'], *YL)), fontsize=5, xytext=(3, -7 if v == 'V0' else 3), textcoords='offset points', color=STYLE[v]['color'])
        for e, mk in (('identity', '*'), ('reconstruction', 'P'), ('oracle_target', 'D'), ('dsp_lowpass_1500', 'v')):
            p = D['reference_points'][e]; put(a, p['ltas_db'], p['f1_norm'], marker=mk, color='0.3', ms=6, ls='', label=e)
        a.axhline(0.5, color='0.7', lw=0.6, ls=':'); a.axhline(0, color='0.85', lw=0.6)
        for g in D['grid_ltas_db']: a.axvline(g, color='0.85', lw=0.5)
        a.set_xlim(XL[0] - 0.2, XL[1] + 0.2); a.set_ylim(YL[0] - 0.05, YL[1] + 0.05); a.set_xlabel('T1: LTAS distance from source (dB)')
        a.set_title(f"{fam} ({D['role']}); labels = editing strength", fontsize=7, loc='left')
    ax[0].set_ylabel('D1: floor-normalised onset F1'); ax[0].legend(frameon=False, fontsize=5.5, loc='lower left'); fig.tight_layout()
    fig.savefig(os.path.join(F, 'fig_tradeoff.pdf')); fig.savefig(os.path.join(F, 'fig_tradeoff.png')); plt.close(fig)


def fig_example(cid=None, strength=0.7):
    sys.path.insert(0, os.path.join(ROOT, 'src')); sys.path.insert(0, os.path.join(ROOT, 'experiments'))
    import torch, synthetic_audio as sa, rhythmic_metrics as rm, latents as la, rf_model as rf
    from eval_rf import load_editor, comp_of
    from train_rf import load_split
    te = [m for m in load_split('test') if m['nonperiodic']]; m = next(x for x in te if cid is None or x['cid'] == cid); c = comp_of(m); src, gt = sa.render(c); n = src.shape[1]
    outs = {'source (electronic)': src}
    for v in ('V0', 'V1'):
        net, mu, sd = load_editor(v); zs = torch.from_numpy(((m['src'] - mu) / sd).astype(np.float32))[None]
        z = rf.sample(net, zs.shape, torch.tensor([1]), torch.tensor([c.tempo_hz], dtype=torch.float32), zs if v == 'V1' else None, t_start=strength, x_init=zs, steps=32, seed=0)
        outs[f'{v} edit (strength {strength:g})'] = la.decode((z[0].numpy() * sd + mu).astype(np.float32), n)
    fig, ax = plt.subplots(len(outs), 1, figsize=(7.2, 1.2 * len(outs)), sharex=True); t = np.arange(n) / sa.SR
    for a, (k, x) in zip(ax, outs.items()):
        a.plot(t, x.mean(0), color='0.3', lw=0.3); on = rm.detect_onsets(x, sa.SR)
        for g in gt['onsets_s']: a.axvline(g, color='0.75', lw=1.6, zorder=0)
        a.plot(on, np.full(len(on), 0.85 * np.abs(x).max()), 'kv', ms=3); a.set_ylabel(k, fontsize=6, rotation=0, ha='right'); a.set_yticks([])
    ax[-1].set_xlabel('time (s); grey bars = ground-truth onsets, triangles = onsets detected in the audio'); ax[0].set_title(c.cid, fontsize=7, loc='left'); fig.tight_layout()
    fig.savefig(os.path.join(F, 'fig_example.pdf')); fig.savefig(os.path.join(F, 'fig_example.png')); plt.close(fig)


if __name__ == '__main__':
    os.makedirs(F, exist_ok=True)
    for f in sys.argv[1:] or ['aliasing', 'training', 'tradeoff', 'example']: globals()[f'fig_{f}']()
