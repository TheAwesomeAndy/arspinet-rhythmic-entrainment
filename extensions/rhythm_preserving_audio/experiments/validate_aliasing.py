#!/usr/bin/env python3
"""Addendum A2 (SIMULATED): is each timing measure fooled by coincidental re-alignment on a grid?

Two stimulus families on the 24 test compositions (H01-H04 x 6 tempi, melody seed 20):
  periodic    : the test templates (a 1-bar pattern repeated 4 times, dense 16th-note grid);
  nonperiodic : sparse, non-repeating sequences (synthetic_audio.nonperiodic_pattern).
Controls (reference = the unperturbed composition): identity; global shifts by exact multiples of the
16th-note step (0.25, 0.5, 1, 2, 4 steps; 4 steps = one beat) and a fixed 30 ms shift; Gaussian jitter
(15, 30 ms); tempo x1.05. For LTAS validation also: gain -6 dB, time reversal, low-pass 1500 Hz, acoustic
re-synthesis.

For every candidate measure, separation between 'identity' (genuine preservation) and the exact
1-step and 4-step shifts (coincidental re-alignment candidates) is summarised by the fraction of
compositions in which the measure ranks identity strictly better than the shifted copy (1.0 = always
distinguishes, 0.5 = chance). Writes results/aliasing_validation.json.
"""
import json, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, os.path.join(ROOT, 'src'))
import synthetic_audio as sa, rhythmic_metrics as rm, acoustic_metrics as am, baselines as bl

STEPS = (0.25, 0.5, 1, 2, 4)
# measure -> True if larger is better (preservation), False if smaller is better
MEASURES = {'greedy_f1': True, 'greedy_dev_ms': False, 'ordered_f1': True, 'ordered_dev_ms': False, 'abs_signed_dev_ms': False,
            'lag_specificity': True, 'abs_best_lag_ms': False, 'f1_norm': True}


def controls(c):
    step = 1 / (c.tempo_hz * sa.SUB); src, _ = sa.render(c)
    yield 'identity', src
    for k in STEPS: yield f'shift_{k:g}step', sa.render(c, shift_s=k * step)[0]
    yield 'shift_30ms', sa.render(c, shift_s=0.03)[0]
    for ms in (15, 30): yield f'jitter_{ms}ms', sa.render(c, jitter_s=ms / 1e3)[0]
    yield 'tempo_x1.05', sa.render(c, time_scale=1.05)[0]
    yield 'gain_-6db', (src * 10 ** (-6 / 20)).astype(np.float32)
    yield 'time_reversed', np.ascontiguousarray(src[:, ::-1])
    yield 'lowpass_1500', bl.lowpass(src, sa.SR, 1500.0)
    yield 'timbre_acoustic', bl.oracle_resynthesis(c, 'acoustic')


def main():
    rows = []; t0 = time.time()
    for fam, np_ in (('periodic', False), ('nonperiodic', True)):
        for c in sa.compositions('test', melody_seeds=(20,), nonperiodic=np_):
            src, gt = sa.render(c); ref = np.asarray(gt['onsets_s'])
            for name, x in controls(c):
                tr = rm.timing_report(rm.detect_onsets(x, sa.SR), ref)
                tr['abs_signed_dev_ms'] = abs(tr['signed_dev_ms']); tr['abs_best_lag_ms'] = abs(tr['best_lag_ms'])
                rows.append({'family': fam, 'composition': c.cid, 'tempo_hz': c.tempo_hz, 'step_ms': 1e3 / (c.tempo_hz * sa.SUB), 'control': name, **tr,
                             'ltas_distance_db': am.ltas_log_mel_distance(src, x, sa.SR), 'log_mel_distance_db': am.log_mel_distance(src, x, sa.SR)})
        print(fam, f'done ({time.time() - t0:.0f}s)', flush=True)

    ctrl = list(dict.fromkeys(r['control'] for r in rows)); fams = ('periodic', 'nonperiodic')
    keys = list(MEASURES) + ['signed_dev_ms', 'best_lag_ms', 'alias_floor', 'ltas_distance_db', 'log_mel_distance_db']
    med = {f: {c: {k: float(np.nanmedian([r[k] for r in rows if r['family'] == f and r['control'] == c])) for k in keys} for c in ctrl} for f in fams}
    sep = {}
    for f in fams:
        sep[f] = {}
        for sh in ('shift_1step', 'shift_4step', 'shift_0.5step'):
            sep[f][sh] = {}
            for m, hib in MEASURES.items():
                wins = []
                for cid in dict.fromkeys(r['composition'] for r in rows if r['family'] == f):
                    a = next(r[m] for r in rows if r['composition'] == cid and r['control'] == 'identity' and r['family'] == f)
                    b = next(r[m] for r in rows if r['composition'] == cid and r['control'] == sh and r['family'] == f)
                    if np.isnan(a) or np.isnan(b): wins.append(0.0); continue
                    wins.append(1.0 if (a > b if hib else a < b) else (0.5 if a == b else 0.0))
                sep[f][sh][m] = float(np.mean(wins))
    out = {'label': 'SIMULATED aliasing validation (addendum A2)', 'rows': rows, 'group_medians': med, 'separation_identity_vs_shift': sep}
    json.dump(out, open(os.path.join(ROOT, 'results', 'aliasing_validation.json'), 'w'), indent=1)
    for f in fams:
        print(f'\n== {f} (group medians)')
        cols = ['greedy_f1', 'greedy_dev_ms', 'ordered_f1', 'ordered_dev_ms', 'signed_dev_ms', 'best_lag_ms', 'lag_specificity', 'alias_floor', 'f1_norm', 'ltas_distance_db', 'log_mel_distance_db']
        print(f"{'control':16s}" + ''.join(f'{k[:11]:>12s}' for k in cols))
        for c in ctrl: print(f'{c:16s}' + ''.join(f'{med[f][c][k]:12.3f}' for k in cols))
        print('separation identity vs shift (fraction of compositions identity ranks better; 1 = always):')
        for sh, d in sep[f].items(): print(f'  {sh:14s}', {k: round(v, 2) for k, v in d.items()})


if __name__ == '__main__':
    main()
