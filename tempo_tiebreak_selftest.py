#!/usr/bin/env python3
"""Self-test of a tempo-tagging tie-break: for each duration-unique trial, the candidate set is
the true stimulus plus every subgroup stimulus within ±300 ms of its duration; pick the tempo
(among the distinct candidate tempi) at which the trial's fronto-central EEG is most strongly
tagged (max over k in {1,2} of Welch z against neighbouring bins). Accuracy vs chance over the
distinct tempi. If accurate, mixed-tempo ambiguous trials can be given a tempo for Q1."""
import sys, json, numpy as np
from collections import Counter
from scipy.signal import butter, sosfiltfilt, resample_poly, welch
from weineck_loader import load_features, read_block, trials_from_events, participant_blocks, match_trials, FEAT_FS, TRIM_S, TEMPI
F, subj = sys.argv[1], sys.argv[2]
feats, table = load_features(F)
FC = ['Fz','FC1','FC2','Cz','F3','F4','C3','C4']; fs = 256.0
sos = butter(4, [0.5, 12.0], btype='band', fs=1000.0, output='sos')
trials = []
for b in participant_blocks('/home/user/data_local/weineck2022', subj):
    raw, ev = read_block(b); trials += [(raw, s, e) for s, e in trials_from_events(ev)]
durs = [e - s for (_, s, e) in trials]; j, cost, assign = match_trials(durs, table)
claims = Counter(x for x in assign if x is not None); dup = {x for x, c in claims.items() if c > 1}
unamb = [n for n, x in enumerate(assign) if x is not None and x not in dup]
cands = [(i, k, L / FEAT_FS) for (i, jj, k, L) in table if jj == j]
def tagz(x, f, seg_s=10):
    nper = int(min(fs * seg_s, len(x))); fr, p = welch(x - x.mean(), fs=fs, nperseg=nper, noverlap=nper // 2, window='hann'); zs = []
    for k in (1, 2):
        f0 = k * f; i = np.argmin(np.abs(fr - f0)); nb = (np.abs(fr - f0) > 0.15) & (np.abs(fr - f0) < 0.8)
        for kk in (1, 2): nb &= np.abs(fr - kk * f) > 0.15
        zs.append((p[i] - p[nb].mean()) / (p[nb].std() + 1e-15))
    return max(zs)
hits, nt = [], []
for n in unamb:
    raw, s, e = trials[n]; seg = raw.copy().crop(tmin=s + TRIM_S, tmax=e, include_tmax=False).load_data()
    names = seg.ch_names; keep = [i for i, c in enumerate(names) if c != '33']; X = seg.get_data()[keep]; X = X - X.mean(0, keepdims=True); X = sosfiltfilt(sos, X, axis=1)
    idx = [keep.index(names.index(c)) for c in FC if c in names]; x = resample_poly(X[idx].mean(0), 32, 125)
    d = durs[n] - TRIM_S; tempi = sorted({TEMPI[i] for (i, k, L) in cands if abs(L - d) <= 0.3} | {TEMPI[assign[n][0]]})
    if len(tempi) < 2: continue
    z = {f: tagz(x, f) for f in tempi}; pick = max(z, key=z.get)
    hits.append(pick == TEMPI[assign[n][0]]); nt.append(len(tempi))
hits = np.array(hits); nt = np.array(nt)
print(f"subj {subj}: tempo tie-break self-test on {len(hits)} trials with {nt.mean():.1f} distinct candidate tempi: accuracy {hits.mean():.2f}, chance {np.mean(1/nt):.2f}")
json.dump({'subj': subj, 'n': int(len(hits)), 'accuracy': float(hits.mean()), 'chance': float(np.mean(1 / nt)), 'mean_tempi': float(nt.mean())}, open(f'results/tempo_tiebreak_subj{subj}.json', 'w'))
