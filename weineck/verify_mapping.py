#!/usr/bin/env python3
"""Verify the duration-based trial->feature mapping of weineck_loader.

For each matched trial: resample the spectral-flux feature (128 Hz) to the EEG
rate, cross-correlate with the mean of fronto-central channels over lags
-0.5..1.0 s, average the normalised cross-correlation across trials, and compare
the peak against a null built from circularly shifting the feature (>= 3 s) within
each trial.  A correct mapping gives a positive peak at ~100-250 ms lag that the
shifted null does not.  Also reports the same for the envelope feature.
"""
import argparse, json, sys, os
import numpy as np
from scipy.signal import resample_poly, correlate
from weineck_loader import load_participant

FC = ['Fz', 'FC1', 'FC2', 'Cz', 'F3', 'F4', 'C3', 'C4']


def xcorr(a, b, fs, lo=-0.5, hi=1.0):
    a = (a - a.mean()) / (a.std() + 1e-12); b = (b - b.mean()) / (b.std() + 1e-12)
    full = correlate(b, a, mode='full') / len(a)          # positive lag = EEG lags stimulus
    lags = np.arange(-len(a) + 1, len(b)) / fs
    m = (lags >= lo) & (lags <= hi)
    return lags[m], full[m]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='/home/user/data_local/weineck2022'); ap.add_argument('--feats', required=True)
    ap.add_argument('--subj', default='10'); ap.add_argument('--trim-side', default='start'); ap.add_argument('--n-null', type=int, default=100); ap.add_argument('--out', default=None)
    a = ap.parse_args()
    trials = load_participant(a.data, a.subj, a.feats, trim_side=a.trim_side, verbose=True)
    rng = np.random.RandomState(0)
    res = {}
    for fi, fname in ((3, 'spectral_flux'), (0, 'envelope')):
        acc = None; nulls = []
        for t in trials:
            idx = [t['ch_names'].index(c) for c in FC if c in t['ch_names']]
            eeg = t['eeg'][idx].mean(0)
            feat = resample_poly(t['feats'][fi], 2, 1)        # 128 -> 256 Hz
            n = min(len(eeg), len(feat)); eeg, feat = eeg[:n], feat[:n]
            lags, c = xcorr(feat, eeg, t['eeg_fs'])
            acc = c if acc is None else acc + c
            ms = int(3 * t['eeg_fs'])
            nulls.append([xcorr(np.roll(feat, rng.randint(ms, n - ms)), eeg, t['eeg_fs'])[1] for _ in range(a.n_null)])
        acc /= len(trials)
        null = np.mean(np.array(nulls), axis=0)                # n_null x lags
        z = (acc - null.mean(0)) / (null.std(0) + 1e-12)
        ip = np.argmax(np.abs(z));
        res[fname] = {'peak_lag_ms': float(lags[ip] * 1000), 'peak_r': float(acc[ip]), 'peak_z': float(z[ip]),
                      'n_trials': len(trials), 'z_at_lags_ms': {int(l * 1000): round(float(zz), 2) for l, zz in zip(lags[::32], z[::32])}}
        print(f"[{fname}] n={len(trials)} trials: peak |z| at lag {lags[ip]*1000:+.0f} ms, r={acc[ip]:+.4f}, z={z[ip]:+.1f}; z at 0/100/150/200/300 ms: "
              + ", ".join(f"{z[np.argmin(np.abs(lags - L))]:+.1f}" for L in (0, 0.1, 0.15, 0.2, 0.3)))
    if a.out:
        json.dump(res, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
