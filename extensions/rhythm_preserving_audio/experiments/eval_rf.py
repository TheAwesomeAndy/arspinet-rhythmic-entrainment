#!/usr/bin/env python3
"""Held-out evaluation of the fallback rectified-flow editors under the frozen DECISION_RULES.md
(sha256 f4512b15...). MEASURED on model outputs; nothing here was looked at before the rules were frozen.

Editors: V0 (label-conditioned, SDEdit from the source) and V1 (source-conditioned, SDEdit from the source),
target label 'acoustic', strengths S, seeds SEEDS, Euler 32 steps over [0, 1]. Reference points per
composition: identity (source), SAME-S reconstruction, oracle target (acoustic re-synthesis, same timing),
DSP low-pass 1500 Hz. Writes results/rf_eval.json (per output, per composition, decision quantities).
"""
import json, os, sys, time
import numpy as np
import torch
from scipy.stats import wilcoxon, spearmanr, binomtest

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, os.path.join(ROOT, 'src')); sys.path.insert(0, HERE)
import synthetic_audio as sa, rhythmic_metrics as rm, acoustic_metrics as am, baselines as bl, latents as la, rf_model as rf
from train_rf import load_split

S = (0.1, 0.3, 0.5, 0.7, 0.9, 1.0); SEEDS = (0, 1, 2); STEPS = 32; CK = os.path.join(ROOT, 'checkpoints')


def comp_of(m):
    return sa.Composition(m['template'], m['melody_seed'], m['tempo_hz'], nonperiodic=m['nonperiodic'])


def score(x, src, tgt, gt):
    tr = rm.timing_report(rm.detect_onsets(x, sa.SR), np.asarray(gt['onsets_s']))
    preserved = bool(tr['f1_norm'] >= 0.5 and tr['lag_specificity'] > 0 and abs(tr['best_lag_ms']) <= 50)
    return {**tr, 'preserved': preserved, 'ltas_db': am.ltas_log_mel_distance(src, x, sa.SR), 'logmel_db': am.log_mel_distance(src, x, sa.SR),
            'ltas_to_target_db': am.ltas_log_mel_distance(tgt, x, sa.SR), 'centroid_shift_hz': am.spectral_centroid(x, sa.SR) - am.spectral_centroid(src, sa.SR)}


def load_editor(v):
    ck = torch.load(os.path.join(CK, f'rf_{v}.pt'), weights_only=False); net = rf.VelocityNet(cond_ch=256 if v == 'V1' else 0); net.load_state_dict(ck['ema']); net.eval()
    return net, ck['mu'], ck['sd']


def interp_at(t1, y, grid):
    """Per composition: y as a piecewise-linear function of T1 (points sorted by T1, ties averaged);
    NaN outside the composition's own T1 range (not covered)."""
    t1 = np.asarray(t1); y = np.asarray(y); o = np.argsort(t1); t1, y = t1[o], y[o]
    u = np.unique(t1); yu = np.array([y[t1 == v].mean() for v in u])
    return np.array([np.interp(g, u, yu) if u[0] <= g <= u[-1] else np.nan for g in grid])


def boot_ci(d, n=10000, seed=0):
    d = np.asarray(d); rng = np.random.RandomState(seed); m = [rng.choice(d, len(d)).mean() for _ in range(n)]; return [float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))]


def main():
    rows = []; t0 = time.time(); te = load_split('test'); editors = {v: load_editor(v) for v in ('V0', 'V1')}
    for m in te:
        c = comp_of(m); src, gt = sa.render(c); tgt, _ = sa.render(c, instrumentation='acoustic'); n = src.shape[1]
        base = {'composition': c.cid, 'family': 'nonperiodic' if m['nonperiodic'] else 'periodic', 'tempo_hz': c.tempo_hz}
        rows.append({**base, 'editor': 'identity', 'strength': 0.0, 'seed': 0, **score(src, src, tgt, gt)})
        rows.append({**base, 'editor': 'reconstruction', 'strength': 0.0, 'seed': 0, **score(la.decode(m['src'], n), src, tgt, gt)})
        rows.append({**base, 'editor': 'oracle_target', 'strength': 1.0, 'seed': 0, **score(tgt, src, tgt, gt)})
        rows.append({**base, 'editor': 'dsp_lowpass_1500', 'strength': 1.0, 'seed': 0, **score(bl.lowpass(src, sa.SR, 1500.0), src, tgt, gt)})
        for v, (net, mu, sd) in editors.items():
            zs = torch.from_numpy(((m['src'] - mu) / sd).astype(np.float32))[None]; cond = zs if v == 'V1' else None
            for s in S:
                for seed in SEEDS:
                    z = rf.sample(net, zs.shape, torch.tensor([1]), torch.tensor([c.tempo_hz], dtype=torch.float32), cond, t_start=s, x_init=zs, steps=STEPS, seed=seed)
                    x = la.decode((z[0].numpy() * sd + mu).astype(np.float32), n)
                    rows.append({**base, 'editor': v, 'strength': s, 'seed': seed, **score(x, src, tgt, gt)})
        print(f'{c.cid} ({time.time() - t0:.0f}s)', flush=True)

    # ---- per-composition means over seeds
    keys = ['f1_norm', 'greedy_f1', 'lag_specificity', 'best_lag_ms', 'greedy_dev_ms', 'signed_dev_ms', 'ltas_db', 'logmel_db', 'ltas_to_target_db', 'centroid_shift_hz', 'preserved']
    comp = {}
    for r in rows:
        k = (r['composition'], r['editor'], r['strength']); comp.setdefault(k, []).append(r)
    cm = [{'composition': k[0], 'editor': k[1], 'strength': k[2], 'family': v[0]['family'],
           **{q: float(np.nanmean([float(x[q]) for x in v])) for q in keys},
           # D2 precision only over outputs whose timing is preserved (DECISION_RULES.md)
           'dev_ms_if_preserved': float(np.nanmean([x['greedy_dev_ms'] for x in v if x['preserved']])) if any(x['preserved'] for x in v) else float('nan')} for k, v in comp.items()]
    res = {'label': 'MEASURED: fallback rectified-flow editors on held-out compositions, frozen DECISION_RULES.md', 'strengths': S, 'seeds': SEEDS, 'euler_steps': STEPS,
           'rows': rows, 'per_composition': cm, 'decision': {}}
    for fam in ('nonperiodic', 'periodic'):
        sel = lambda e, s=None: [r for r in cm if r['family'] == fam and r['editor'] == e and (s is None or r['strength'] == s)]
        comps = sorted(set(r['composition'] for r in sel('V0')))
        ref_t1 = [r['ltas_db'] for r in sel('V0') if 0.3 <= r['strength'] <= 0.7]; grid = [float(np.percentile(ref_t1, q)) for q in (25, 50, 75)]
        diffs = {g: [] for g in grid}; per = []
        for cid in comps:
            a = sorted([r for r in sel('V0') if r['composition'] == cid], key=lambda r: r['strength']); b = sorted([r for r in sel('V1') if r['composition'] == cid], key=lambda r: r['strength'])
            ya = interp_at([r['ltas_db'] for r in a], [r['f1_norm'] for r in a], grid); yb = interp_at([r['ltas_db'] for r in b], [r['f1_norm'] for r in b], grid)
            per.append({'composition': cid, 'V0': ya.tolist(), 'V1': yb.tolist()})
            for g, u, w in zip(grid, ya, yb):
                if not (np.isnan(u) or np.isnan(w)): diffs[g].append(float(w - u))
        mq = {}
        for q, g in zip((25, 50, 75), grid):
            d = diffs[g]; mq[f'p{q}'] = {'ltas_db': g, 'n_compositions_covered': len(d), 'mean_diff_V1_minus_V0': float(np.mean(d)) if d else None,
                                         'ci95': boot_ci(d) if len(d) > 1 else None, 'wilcoxon_p': float(wilcoxon(d).pvalue) if len(d) > 1 and np.any(np.array(d) != 0) else None}
        med = mq['p50']; better = bool(med['ci95'] is not None and med['ci95'][0] > 0); worse = bool(med['ci95'] is not None and med['ci95'][1] < 0)
        sweep = {}
        for e in ('V0', 'V1'):
            rf_, rt = [], []
            for cid in comps:
                pts = sorted([r for r in sel(e) if r['composition'] == cid], key=lambda r: r['strength'])
                rf_.append(spearmanr([p['strength'] for p in pts], [p['f1_norm'] for p in pts]).statistic); rt.append(spearmanr([p['strength'] for p in pts], [p['ltas_db'] for p in pts]).statistic)
            neg = int(np.sum(np.array(rf_) < 0)); sweep[e] = {'rho_strength_f1norm': [float(x) for x in rf_], 'rho_strength_ltas': [float(x) for x in rt],
                                                              'n_negative_f1norm': neg, 'sign_test_p': float(binomtest(neg, int(np.sum(~np.isnan(rf_))), 0.5).pvalue)}
        frac = {e: {str(s): float(np.mean([r['preserved'] for r in sel(e, s)])) for s in S} for e in ('V0', 'V1')}
        refs = {e: {q: float(np.nanmedian([r[q] for r in sel(e)])) for q in ('f1_norm', 'ltas_db', 'ltas_to_target_db', 'greedy_dev_ms')} for e in ('identity', 'reconstruction', 'oracle_target', 'dsp_lowpass_1500')}
        curves = {e: {str(s): {q: float(np.nanmedian([r[q] for r in sel(e, s)])) for q in ('f1_norm', 'ltas_db', 'ltas_to_target_db', 'preserved', 'dev_ms_if_preserved', 'best_lag_ms')} for s in S} for e in ('V0', 'V1')}
        res['decision'][fam] = {'role': 'PRIMARY (D1)' if fam == 'nonperiodic' else 'secondary', 'n_compositions': len(comps), 'grid_ltas_db': grid,
                                'matched_transformation': mq, 'per_composition_interp': per, 'V1_better_at_median': better, 'V1_worse_at_median': worse,
                                'strength_sweep': sweep, 'fraction_preserved': frac, 'reference_points': refs, 'median_curves': curves}
    json.dump(res, open(os.path.join(ROOT, 'results', 'rf_eval.json'), 'w'), indent=1)
    print(json.dumps({f: {k: v for k, v in d.items() if k not in ('per_composition_interp',)} for f, d in res['decision'].items()}, indent=1))


if __name__ == '__main__':
    main()
