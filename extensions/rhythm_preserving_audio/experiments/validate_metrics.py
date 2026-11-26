#!/usr/bin/env python3
"""Metric validation on synthetic controls (EXPERIMENT_PLAN.md section 6). SIMULATED.

For every test composition (H01-H04 x 6 tempi, melody seed 20, electronic), renders the unperturbed
source and each control, and scores the control against the composition's ground truth (rhythm) and the
source audio (acoustic change). Writes results/metric_validation.json (per composition and control) and
prints the group medians and the pre-specified pass/fail checks.
"""
import json, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, os.path.join(ROOT, 'src'))
import synthetic_audio as sa, rhythmic_metrics as rm, acoustic_metrics as am, baselines as bl

MELODY_SEED = 20


def controls(comp):
    src, gt = sa.render(comp)
    yield 'identity', src
    for ms in (10, 30, 60, 100): yield f'shift_{ms}ms', sa.render(comp, shift_s=ms / 1e3)[0]
    for ms in (5, 15, 30, 50): yield f'jitter_{ms}ms', sa.render(comp, jitter_s=ms / 1e3)[0]
    for k in (1.02, 1.05, 1.10): yield f'tempo_x{k:g}', sa.render(comp, time_scale=k)[0]
    for d in (0.25, 0.5): yield f'drop_{int(d * 100)}pct', sa.render(comp, drop_frac=d)[0]
    yield 'timbre_acoustic', bl.oracle_resynthesis(comp, 'acoustic')
    for name, fn in bl.DSP_EDITS.items(): yield f'dsp_{name}', fn(src, sa.SR)


def main():
    out = os.path.join(ROOT, 'results', 'metric_validation.json'); rows = []; t0 = time.time()
    comps = sa.compositions('test', melody_seeds=(MELODY_SEED,))
    for c in comps:
        src, gt = sa.render(c)
        for name, x in controls(c):
            r = rm.flat(rm.rhythm_report(x, sa.SR, gt, src)); a = am.acoustic_report(src, x, sa.SR)
            rows.append({'composition': c.cid, 'template': c.template, 'tempo_hz': c.tempo_hz, 'control': name, **r, **a})
        print(f'{c.cid} done ({time.time() - t0:.0f}s)', flush=True)
    json.dump({'label': 'SIMULATED metric validation (synthetic controls)', 'melody_seed': MELODY_SEED, 'rows': rows}, open(out, 'w'), indent=1)

    ctrl = list(dict.fromkeys(r['control'] for r in rows)); keys = ['onset_f1', 'onset_dev_ms', 'beat_f1', 'beat_dev_ms', 'tempo_err_octave', 'envelope_r', 'beat_band_z', 'log_mel_distance_db', 'centroid_shift_hz']
    med = {c: {k: float(np.nanmedian([r[k] for r in rows if r['control'] == c])) for k in keys} for c in ctrl}
    print(f"{'control':22s}" + ''.join(f'{k[:12]:>13s}' for k in keys))
    for c in ctrl: print(f'{c:22s}' + ''.join(f'{med[c][k]:13.3f}' for k in keys))
    # pre-specified checks
    src_beat = {r['composition']: r['beat_f1'] for r in rows if r['control'] == 'identity'}
    ok_beat = [c for c, v in src_beat.items() if v >= 0.9]
    medc = lambda c, k, sel=None: float(np.nanmedian([r[k] for r in rows if r['control'] == c and (sel is None or r['composition'] in sel)]))
    checks = {
        'identity_logmel_zero': med['identity']['log_mel_distance_db'] < 1e-6,
        'P1_monotone_shift': all(medc(f'shift_{a}ms', 'onset_f1') >= medc(f'shift_{b}ms', 'onset_f1') for a, b in ((10, 30), (30, 60), (60, 100))),
        'P1_below_half_shift60_100': medc('shift_60ms', 'onset_f1') < 0.5 and medc('shift_100ms', 'onset_f1') < 0.5,
        'P2_below_half_shift100': medc('shift_100ms', 'beat_f1', ok_beat) < 0.5,
        'P1_monotone_jitter': all(medc(f'jitter_{a}ms', 'onset_f1') >= medc(f'jitter_{b}ms', 'onset_f1') for a, b in ((5, 15), (15, 30), (30, 50))),
        'P2_monotone_jitter': all(medc(f'jitter_{a}ms', 'beat_f1', ok_beat) >= medc(f'jitter_{b}ms', 'beat_f1', ok_beat) for a, b in ((5, 15), (15, 30), (30, 50))),
        'P1_monotone_tempo': medc('tempo_x1.02', 'onset_f1') >= medc('tempo_x1.05', 'onset_f1') >= medc('tempo_x1.1', 'onset_f1'),
        'P2_monotone_tempo': medc('tempo_x1.02', 'beat_f1', ok_beat) >= medc('tempo_x1.05', 'beat_f1', ok_beat) >= medc('tempo_x1.1', 'beat_f1', ok_beat),
        'timbre_controls_preserve_P1': {c: medc(c, 'onset_f1') >= 0.9 for c in ctrl if c.startswith(('timbre_', 'dsp_'))},
        'timbre_controls_preserve_P2': {c: abs(medc(c, 'beat_f1', ok_beat) - medc('identity', 'beat_f1', ok_beat)) <= 0.05 for c in ctrl if c.startswith(('timbre_', 'dsp_'))},
        'timbre_controls_change_sound': {c: medc(c, 'log_mel_distance_db') > 2.0 for c in ctrl if c.startswith(('timbre_', 'dsp_'))},
        'n_compositions': len(comps), 'n_passing_P2_source_rule': len(ok_beat),
    }
    d = json.load(open(out)); d['group_medians'] = med; d['checks'] = checks; json.dump(d, open(out, 'w'), indent=1)
    print(json.dumps(checks, indent=1))


if __name__ == '__main__':
    main()
