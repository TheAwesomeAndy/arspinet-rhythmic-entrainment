#!/usr/bin/env python3
"""Theory 3, group-level leave-one-tempo-out (EXPLORATORY): one encoding model pooled across all
participants (per-tempo normal-equation moments summed over participants), trained on 12 tempi,
predicting every participant's trials at the held-out tempo. Models: d_short, d_long, hopf, lin,
aug, aug_lin with the configuration most often chosen within participants (passed on the CLI);
lambda by inner leave-one-tempo-out on the training tempi. Metric: mean held-out r at
fronto-central channels per participant and tempo. Output: results/oscillator_group_loto.json.
"""
import argparse, json, time
import numpy as np
from scipy.signal import butter
from weineck_loader import load_features
from underfit_check import load_participant_arrays, solve, corr_cols, SUBJECTS_ALL
from tagging import GRID
import oscillator_bank as ob
from oscillator_heldout import Config, LAMS

MODELS = {'d_short': None, 'd_long': None, 'hopf': 'hopf', 'lin': 'lin', 'aug': 'hopf', 'aug_lin': 'lin'}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--feats', required=True); ap.add_argument('--data', default='/home/user/data_local/weineck2022')
    ap.add_argument('--hopf-cfg', type=int, default=1); ap.add_argument('--lin-cfg', type=int, default=0); ap.add_argument('--out', default='results/oscillator_group_loto.json')
    a = ap.parse_args(); feats, table = load_features(a.feats); sos = butter(4, [0.5, 30.0], btype='band', fs=1000.0, output='sos')
    params = {'hopf': ob.HOPF_GRID[a.hopf_cfg], 'lin': ob.LIN_GRID[a.lin_cfg]}
    # pass 1: per-tempo moment TOTALS across participants (13 x p x p per model); per participant keep only
    # the EEG (float32) and the pre-lag model outputs (float32) needed to rebuild held-out lag matrices
    data = {}; A_tot = {}; B_tot = {}; t0 = time.time()
    for s in SUBJECTS_ALL:
        X64, F64, _, fbeat, fcidx, _, _ = load_participant_arrays(a.data, s, feats, table, sos)
        tidx = [int(np.argmin(np.abs(GRID - f))) for f in fbeat]
        d = {'fcidx': fcidx, 'tidx': tidx, 'X64': [x.astype(np.float32) for x in X64], 'cfg': {}}
        for m, base in MODELS.items():
            c = Config(m, F64, params.get(base))
            for part in c.parts:                       # shrink stored outputs
                part[1][:] = [o.astype(np.float32) for o in part[1]]
            d['cfg'][m] = c
            p = c.xl(0).shape[1]
            if m not in A_tot:
                A_tot[m] = np.zeros((13, p, p)); B_tot[m] = np.zeros((13, p, X64[0].shape[1]))
            for i in range(c.n):
                Xl = c.xl(i); A_tot[m][tidx[i]] += Xl.T @ Xl; B_tot[m][tidx[i]] += Xl.T @ X64[i]
        data[s] = d; print(f"  loaded {s} ({time.time()-t0:.0f}s)", flush=True)
    out = {'exploratory': True, 'group_level': True, 'params': {k: v for k, v in params.items()}, 'models': {m: {} for m in MODELS}}
    for m in MODELS:
        A = A_tot[m]; B = B_tot[m]
        for ho in range(13):
            train = [t for t in range(13) if t != ho]; A_tr = A.sum(0) - A[ho]; B_tr = B.sum(0) - B[ho]
            best = None
            for lam in LAMS:
                rs = []
                for v in train:
                    W = solve(A_tr - A[v], B_tr - B[v], lam)
                    for s in data:
                        d = data[s]; rs += [corr_cols(d['cfg'][m].xl(n) @ W, d['X64'][n], d['fcidx']) for n in range(len(d['X64'])) if d['tidx'][n] == v]
                if best is None or np.mean(rs) > best[0]:
                    best = (float(np.mean(rs)), lam)
            W = solve(A_tr, B_tr, best[1]); per_s = {}
            for s in data:
                d = data[s]; idx = [n for n in range(len(d['X64'])) if d['tidx'][n] == ho]
                if idx: per_s[s] = float(np.mean([corr_cols(d['cfg'][m].xl(n) @ W, d['X64'][n], d['fcidx']) for n in idx]))
            out['models'][m][str(float(GRID[ho]))] = {'lam': best[1], 'r_fc_by_participant': per_s, 'median_r': float(np.median(list(per_s.values())))}
            print(f"{m:>8} held-out {GRID[ho]:.2f} Hz: median r_fc {out['models'][m][str(float(GRID[ho]))]['median_r']:+.4f} (lam {best[1]})  ({time.time()-t0:.0f}s)", flush=True)
        json.dump(out, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
