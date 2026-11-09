#!/usr/bin/env python3
"""Item 1: beat-tagging across the 13 stimulation tempi, drive vs reservoir readouts (Q1).

Per participant: trials with a known tempo (one-to-one duration match, plus ambiguous trials
whose candidates all share a tempo). Drive = fronto-central cluster mean (Fz FC1 FC2 Cz F3 F4
C3 C4), average reference, 0.5-30 Hz, 256 Hz, z-scored per trial, EEG window = features'
window (first second dropped). Trials of one tempo are concatenated (z-scored per trial first).
Detectors with the shared neighbour-frequency null (Welch, 10 s segments; k in {1, 2}):
L (drive), R_pc1 and R_pop (canonical reservoir, seed 42, run per trial then concatenated),
Rs_pc1 (shuffled weights). Output: per participant x tempo z-scores; group table.
"""
import argparse, json, os, sys
import numpy as np
from collections import Counter
from scipy.signal import butter, sosfiltfilt, resample_poly, welch
from weineck_loader import (load_features, read_block, trials_from_events, participant_blocks,
                            match_trials, FEAT_FS, TRIM_S, TEMPI)
sys.path.insert(0, '/home/user/dissoAdventureExperiments/chapter5Experiments')
from experiment_zero import LIFReservoir
from tagging import tag_z, PSEUDO

FC = ['Fz', 'FC1', 'FC2', 'Cz', 'F3', 'F4', 'C3', 'C4']; FS = 256.0




def shuffled(seed):
    r = LIFReservoir(seed=seed); rng = np.random.RandomState(seed + 1000)
    W = r.W_rec.copy().ravel(); rng.shuffle(W); W = W.reshape(r.W_rec.shape); r.W_rec = W * (0.9 / np.abs(np.linalg.eigvals(W)).max()); return r


def tempo_known_trials(data_dir, subj, table):
    trials = []
    for b in participant_blocks(data_dir, subj):
        raw, ev = read_block(b); trials += [(raw, s, e) for s, e in trials_from_events(ev)]
    durs = [e - s for (_, s, e) in trials]; j, cost, assign = match_trials(durs, table)
    claims = Counter(x for x in assign if x is not None); dup = {x for x, c in claims.items() if c > 1}
    cands = [(i, k, L / FEAT_FS) for (i, jj, k, L) in table if jj == j]
    out = []
    for n, (raw, s, e) in enumerate(trials):
        x = assign[n]
        if x is not None and x not in dup:
            out.append((raw, s, e, x[0], 'one-to-one')); continue
        hits = {i for (i, k, L) in cands if abs(L - (durs[n] - TRIM_S)) <= 0.02}
        if len(hits) == 1:
            out.append((raw, s, e, hits.pop(), 'same-tempo'))
    return j, out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--data', default='/home/user/data_local/weineck2022'); ap.add_argument('--feats', required=True)
    ap.add_argument('--subjects', default='10,11,12,13,14,16,17,18'); ap.add_argument('--out', default='results/tempo_curve.json')
    a = ap.parse_args()
    feats, table = load_features(a.feats)
    sos = butter(4, [0.5, 30.0], btype='band', fs=1000.0, output='sos')
    res = LIFReservoir(seed=42); res_s = shuffled(42)
    out = {}
    for subj in a.subjects.split(','):
        j, trials = tempo_known_trials(a.data, subj, table)
        by_tempo = {}
        for raw, s, e, ti, kind in trials:
            seg = raw.copy().crop(tmin=s + TRIM_S, tmax=e, include_tmax=False).load_data()
            names = seg.ch_names; keep = [i for i, c in enumerate(names) if c != '33']
            X = seg.get_data()[keep]; X = X - X.mean(0, keepdims=True); X = sosfiltfilt(sos, X, axis=1)
            idx = [keep.index(names.index(c)) for c in FC if c in names]
            x = resample_poly(X[idx].mean(0), 32, 125); x = (x - x.mean()) / (x.std() + 1e-12)
            S = res.forward(x); Ss = res_s.forward(x)
            by_tempo.setdefault(ti, {'x': [], 'S': [], 'Ss': [], 'n': 0, 'kinds': Counter()})
            d = by_tempo[ti]; d['x'].append(x); d['S'].append(S); d['Ss'].append(Ss); d['n'] += 1; d['kinds'][kind] += 1
        out[subj] = {'subgroup': int(j), 'n_trials': len(trials), 'tempi': {}}
        for ti, d in sorted(by_tempo.items()):
            f = float(TEMPI[ti]); x = np.concatenate(d['x']); S = np.concatenate(d['S']); Ss = np.concatenate(d['Ss'])
            def pc1(M):
                U, s_, Vt = np.linalg.svd(M - M.mean(0), full_matrices=False); return U[:, 0] * s_[0]
            row = {'f': f, 'n_trials': d['n'], 'kinds': dict(d['kinds']), 'seconds': len(x) / FS, 'L': tag_z(x, f), 'R_pc1': tag_z(pc1(S), f), 'R_pop': tag_z(S.mean(1), f),
                   'Rs_pc1': tag_z(pc1(Ss), f), 'R_frac_units': float((np.array([tag_z(S[:, u], f) for u in range(S.shape[1])]) > 1.96).mean()), 'rate': float(S.mean())}
            out[subj]['tempi'][str(f)] = row
            print(f"subj {subj} f={f:.2f} n={d['n']:2d} ({len(x)/FS:4.0f}s): L {row['L']:+5.1f} | R_pc1 {row['R_pc1']:+5.1f} | R_pop {row['R_pop']:+5.1f} | Rs_pc1 {row['Rs_pc1']:+5.1f} | units>1.96 {row['R_frac_units']:.2f}", flush=True)
        json.dump(out, open(a.out, 'w'), indent=1)
    # group table: median over participants of max-k z per tempo
    print("\nmedian over participants of max z at (1x or 2x):")
    print(f"{'f':>5} | {'L':>6} {'R_pc1':>6} {'R_pop':>6} {'Rs_pc1':>6} | frac participants L>1.96 / R_pc1>1.96")
    for f in TEMPI:
        rows = [out[s]['tempi'][str(float(f))] for s in out if str(float(f)) in out[s]['tempi']]
        if not rows:
            continue
        L = np.array([r['L'] for r in rows]); R = np.array([r['R_pc1'] for r in rows]); P = np.array([r['R_pop'] for r in rows]); Rs = np.array([r['Rs_pc1'] for r in rows])
        print(f"{f:5.2f} | {np.median(L):+6.2f} {np.median(R):+6.2f} {np.median(P):+6.2f} {np.median(Rs):+6.2f} | {(L>1.96).mean():.2f} / {(R>1.96).mean():.2f}   (n={len(rows)})")


if __name__ == '__main__':
    main()
