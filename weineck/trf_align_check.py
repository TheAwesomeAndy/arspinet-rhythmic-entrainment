#!/usr/bin/env python3
"""Held-out forward-TRF prediction as the alignment test: delta=1.0 (drop first second) vs delta=0.0 (drop last).
EEG: 32 channels, average reference, band-pass 0.5-8 Hz, 64 Hz. Features: spec flux, beat onsets, envelope at 64 Hz."""
import sys, json, numpy as np
from scipy.signal import resample_poly, butter, sosfiltfilt
from weineck_loader import load_participant
from mtrf import loo_prediction_r
feats_path, subj = sys.argv[1], sys.argv[2]
trials = load_participant('/home/user/data_local/weineck2022', subj, feats_path, trim_side='none', verbose=True)
fs_eeg = 256.0; fs = 64.0; sos = butter(4, [0.5, 8.0], btype='band', fs=fs_eeg, output='sos')
res = {}
for delta in (1.0, 0.0):
    Xs, Ys = [], []
    for t in trials:
        names = t['ch_names']; keep = [i for i, c in enumerate(names) if c != '33']
        X = t['eeg'][keep]; X = X - X.mean(0, keepdims=True); X = sosfiltfilt(sos, X, axis=1)
        off = int(round(delta * fs_eeg)); n = t['feats'].shape[1] * 2
        X = X[:, off:off + n]; X = resample_poly(X, 1, 4, axis=1)                  # -> 64 Hz
        F = resample_poly(t['feats'][[3, 2, 0]], 1, 2, axis=1)                        # 128 -> 64 Hz
        n = min(X.shape[1], F.shape[1]); X = X[:, :n]; F = F[:, :n]
        X = (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-12)
        Xs.append(F.T); Ys.append(X.T)
    best = None
    for lam in (0.1, 1.0, 10.0):
        r, lags = loo_prediction_r(Xs, Ys, fs, 0.0, 0.4, lam)
        m = r.mean(0)                                 # per channel mean over trials
        row = {'lam': lam, 'mean_r_all_ch': float(m.mean()), 'best_ch_r': float(m.max()), 'best_ch': trials[0]['ch_names'][int(np.argmax(m))],
               'top5': [(trials[0]['ch_names'][i], round(float(m[i]), 4)) for i in np.argsort(m)[-5:][::-1]],
               'frac_trials_r_pos_bestch': float((r[:, np.argmax(m)] > 0).mean())}
        print(f"delta={delta:.1f} lam={lam:5.1f}: mean r (all ch) {m.mean():+.4f} | best ch {row['best_ch']} r={m.max():+.4f} (trials with r>0: {row['frac_trials_r_pos_bestch']:.2f}) | top5 {row['top5']}")
        if best is None or row['mean_r_all_ch'] > best['mean_r_all_ch']: best = row
    res[delta] = best
json.dump(res, open(f'results/trf_align_subj{subj}.json', 'w'), indent=1)
