#!/usr/bin/env python3
"""NMED-T, all songs present in the data directory: single-listen beat-tagging table.

Per song: EEG-refined beat frequency; group-PC1 drive tagging z at (1,2,4,8)x tempo;
reservoir (canonical experiment_zero, seed 42) population-rate z, unit-PC1 z, fraction of
units with z>1.96; per participant (single listen, own projection on the group PC1 filter):
drive z and unit-PC1 z, detection fractions. Null: neighbour-frequency baseline (Welch 40 s).
Writes JSON + a markdown table. Aggregate, de-identified output only.
"""
import argparse, glob, json, os, sys, time
import numpy as np
from scipy.signal import resample_poly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from nmedt_pilot import load_song, pc1_component, NOMINAL_BPM
from nmedt_pilot_v3 import refine_beat_freq, tag_z
sys.path.insert(0, '/home/user/dissoAdventureExperiments/chapter5Experiments')
from experiment_zero import LIFReservoir

KS = (1, 2, 4, 8)


def unit_readouts(S, f):
    zu = np.array([tag_z(S[:, j], 256.0, f, KS) for j in range(S.shape[1])])
    U, s, Vt = np.linalg.svd(S - S.mean(0), full_matrices=False)
    return (zu > 1.96).mean(0), tag_z(U[:, 0] * s[0], 256.0, f, KS), tag_z(S.mean(1), 256.0, f, KS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='/home/user/data_local/nmedt'); ap.add_argument('--out', default='results/nmedt_tensong.json')
    ap.add_argument('--participants', type=int, default=20)
    a = ap.parse_args()
    res = LIFReservoir(seed=42)
    rows = []
    for mat in sorted(glob.glob(os.path.join(a.data, 'song*_Imputed.mat'))):
        song = int(os.path.basename(mat).split('_')[0].replace('song', ''))
        t0 = time.time(); data, fs = load_song(mat); pc1, w = pc1_component(data)
        f_nom = NOMINAL_BPM[song] / 60; ref = refine_beat_freq(pc1[int(10 * fs):], fs, f_nom)
        f_beat = ref['f_beat'] if ref['z'] > 4 else f_nom     # fall back to nominal when the EEG peak is weak
        def prep(sig):
            x = resample_poly(sig[int(10 * fs):].astype(float), 256, int(fs)); return (x - x.mean()) / (x.std() + 1e-12)
        x = prep(pc1); S = res.forward(x)
        frac, zpc, zpop = unit_readouts(S, f_beat)
        row = {'song': song, 'bpm': NOMINAL_BPM[song], 'f_beat_used': f_beat, 'refined': ref, 'rate': float(S.mean()),
               'group': {'drive_z': tag_z(x, 256.0, f_beat, KS).tolist(), 'unit_pc1_z': zpc.tolist(), 'pop_z': zpop.tolist(), 'frac_units': frac.tolist()},
               'participants': []}
        for p in range(min(a.participants, data.shape[2])):
            xp = prep(w @ (data[:, :, p] - data[:, :, p].mean(1, keepdims=True))); Sp = res.forward(xp)
            fr, zp, zq = unit_readouts(Sp, f_beat)
            row['participants'].append({'drive_z': tag_z(xp, 256.0, f_beat, KS).tolist(), 'unit_pc1_z': zp.tolist(), 'pop_z': zq.tolist(), 'frac_units': fr.tolist()})
        D = np.array([q['drive_z'] for q in row['participants']]); P = np.array([q['unit_pc1_z'] for q in row['participants']]); Q = np.array([q['pop_z'] for q in row['participants']])
        row['single_listen'] = {'drive_frac_sig': (D > 1.96).mean(0).tolist(), 'unit_pc1_frac_sig': (P > 1.96).mean(0).tolist(), 'pop_frac_sig': (Q > 1.96).mean(0).tolist(),
                                'drive_median_z': np.median(D, 0).tolist(), 'unit_pc1_median_z': np.median(P, 0).tolist()}
        kbest = int(np.argmax(row['group']['drive_z']))
        print(f"song {song} ({NOMINAL_BPM[song]:.0f} BPM, f={f_beat:.4f}): group drive z {np.round(row['group']['drive_z'],1)} | unit-PC1 {np.round(zpc,1)} | pop {np.round(zpop,1)} | best harmonic {KS[kbest]}x: single-listen detect drive {row['single_listen']['drive_frac_sig'][kbest]:.2f} unit-PC1 {row['single_listen']['unit_pc1_frac_sig'][kbest]:.2f} pop {row['single_listen']['pop_frac_sig'][kbest]:.2f}  ({time.time()-t0:.0f}s)", flush=True)
        rows.append(row)
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    json.dump(rows, open(a.out, 'w'), indent=1)
    md = ['| song | BPM | f used (Hz) | group drive z (1,2,4,8)f | group unit-PC1 z | group pop-rate z | best k | single-listen detected: drive / unit-PC1 / pop |', '|---|---|---|---|---|---|---|---|']
    for r in rows:
        kb = int(np.argmax(r['group']['drive_z'])); sl = r['single_listen']
        md.append(f"| {r['song']} | {r['bpm']:.2f} | {r['f_beat_used']:.4f} | {', '.join(f'{v:.1f}' for v in r['group']['drive_z'])} | {', '.join(f'{v:.1f}' for v in r['group']['unit_pc1_z'])} | {', '.join(f'{v:.1f}' for v in r['group']['pop_z'])} | {KS[kb]} | {sl['drive_frac_sig'][kb]:.2f} / {sl['unit_pc1_frac_sig'][kb]:.2f} / {sl['pop_frac_sig'][kb]:.2f} |")
    open(a.out.replace('.json', '.md'), 'w').write('\n'.join(md) + '\n'); print('\n'.join(md))


if __name__ == '__main__':
    main()
