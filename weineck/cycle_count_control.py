#!/usr/bin/env python3
"""B. Cycle-count control for the 13-tempo curve (EXPLORATORY).
The tagging statistic in tempo_curve.py concatenates all tempo-known trials of a tempo, so faster
tempi carry more beat cycles per second of data. Here, per participant, the concatenated drive of
every tempo is truncated to the SAME number of beat cycles (the minimum available across that
participant's tempi), and the statistic is recomputed for the drive (L) and the reservoir unit-PC1
(R_pc1). Everything else as in tempo_curve.py (canonical reservoir, seed 42; shared tagging z).
"""
import argparse, json, os, sys
import numpy as np
from scipy.signal import butter, sosfiltfilt, resample_poly
from weineck_loader import load_features, TRIM_S, TEMPI
from tempo_curve import tempo_known_trials, FC, FS
from tagging import tag_z
sys.path.insert(0, '/home/user/dissoAdventureExperiments/chapter5Experiments')
from experiment_zero import LIFReservoir


def pc1(M):
    U, s_, Vt = np.linalg.svd(M - M.mean(0), full_matrices=False); return U[:, 0] * s_[0]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--feats', required=True); ap.add_argument('--subjects', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--data', default='/home/user/data_local/weineck2022'); a = ap.parse_args()
    feats, table = load_features(a.feats); sos = butter(4, [0.5, 30.0], btype='band', fs=1000.0, output='sos'); res = LIFReservoir(seed=42)
    out = {}
    for subj in a.subjects.split(','):
        j, trials = tempo_known_trials(a.data, subj, table); by_t = {}
        for raw, s, e, ti, kind in trials:
            seg = raw.copy().crop(tmin=s + TRIM_S, tmax=e, include_tmax=False).load_data(); names = seg.ch_names; keep = [i for i, c in enumerate(names) if c != '33']
            X = seg.get_data()[keep]; X = X - X.mean(0, keepdims=True); X = sosfiltfilt(sos, X, axis=1); idx = [keep.index(names.index(c)) for c in FC if c in names]
            x = resample_poly(X[idx].mean(0), 32, 125); x = (x - x.mean()) / (x.std() + 1e-12)
            by_t.setdefault(ti, []).append(x)
        cat = {ti: np.concatenate(v) for ti, v in by_t.items()}
        cycles = {ti: len(cat[ti]) / FS * float(TEMPI[ti]) for ti in cat}; n_cyc = min(cycles.values())
        out[subj] = {'n_cycles_used': n_cyc, 'cycles_available': {str(float(TEMPI[t])): c for t, c in cycles.items()}, 'tempi': {}}
        for ti, x in cat.items():
            f = float(TEMPI[ti]); n = int(round(n_cyc / f * FS)); xt = x[:n]
            S = res.forward(xt)
            out[subj]['tempi'][str(f)] = {'seconds': n / FS, 'L_fixed_cycles': tag_z(xt, f), 'R_pc1_fixed_cycles': tag_z(pc1(S), f), 'L_full': tag_z(x, f), 'R_pc1_full': tag_z(pc1(res.forward(x)), f), 'seconds_full': len(x) / FS}
        print(f"subj {subj}: {n_cyc:.0f} cycles per tempo ({min(v['seconds'] for v in out[subj]['tempi'].values()):.0f}-{max(v['seconds'] for v in out[subj]['tempi'].values()):.0f} s); L fixed-cycles by tempo: " + " ".join(f"{float(t):.2f}:{v['L_fixed_cycles']:+.1f}" for t, v in sorted(out[subj]['tempi'].items(), key=lambda kv: float(kv[0]))), flush=True)
        json.dump(out, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
