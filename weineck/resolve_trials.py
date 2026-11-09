#!/usr/bin/env python3
"""Resolve ambiguous Weineck trial->stimulus assignments with a forward TRF.

Steps per participant
 1. Markers -> trials (S40..S80); durations; subgroup (duration fit, cross-checked against
    the published per-tempo counts in Figure3_SourceData1 TRFcorr).
 2. Unambiguous trials (one feature vector within +-20 ms of duration-1.0 s) -> training set.
 3. Self-test (leave-one-out on the unambiguous trials): train the TRF on the others, score
    the true feature vector against decoys = every other feature vector of the subgroup
    within +-`wide` s of the trial's duration (same candidate structure as a real ambiguous
    trial), record whether the true one ranks first and the score margin to the runner-up.
    Gives selection accuracy and an acceptance threshold on the margin.
 4. Unresolved trials (several candidates, or none within 20 ms): candidates = unassigned
    feature vectors of the subgroup within +-`wide` s; score each by the TRF prediction
    correlation (mean over channels) using a TRF trained on all unambiguous trials; solve
    the one-to-one assignment (Hungarian) maximising total score; accept assignments whose
    margin exceeds the threshold.
 5. Check assigned per-tempo counts against the published counts.
EEG: 32 channels, average reference, 0.5-8 Hz, 64 Hz, per-trial z-scored; features: flux,
onsets, envelope, derivative at 64 Hz. Each candidate feature is aligned with the 1 s start
trim (features start 1.0 s after S40) and truncated to the common length.
"""
import argparse, json, os, sys
import numpy as np
import scipy.io
from scipy.optimize import linear_sum_assignment
from scipy.signal import resample_poly, butter, sosfiltfilt
from weineck_loader import (load_features, read_block, trials_from_events, participant_blocks,
                            match_trials, FEAT_FS, TRIM_S, TEMPI)
from mtrf import fit_trf, predict, lag_matrix

SUBJECTS = ['1', '2', '3', '4', '7', '8', '9', '10', '11', '12', '13', '14', '16', '17', '18', '19', '20', '21', '22', '23',
            '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37']
FS = 64.0


def published_counts(fig3_path, subj):
    A = np.asarray(scipy.io.loadmat(fig3_path, squeeze_me=True)['TRFcorr'][0], dtype=float)
    cnt = (~np.isnan(A)).any(axis=3).sum(axis=2)              # 13 x 34
    return cnt[:, SUBJECTS.index(subj)]


def prep_eeg(raw, s, e, sos):
    seg = raw.copy().crop(tmin=s + TRIM_S, tmax=e, include_tmax=False).load_data()
    keep = [i for i, c in enumerate(seg.ch_names) if c != '33']
    X = seg.get_data()[keep]; X = X - X.mean(0, keepdims=True)
    X = sosfiltfilt(sos, X, axis=1)
    X = resample_poly(X, 16, 250, axis=1) if raw.info['sfreq'] == 1000 else resample_poly(X, int(FS), int(raw.info['sfreq']), axis=1)
    X = (X - X.mean(1, keepdims=True)) / (X.std(1, keepdims=True) + 1e-12)
    return X.T                                                   # T x n_ch


def feat64(feats, i, j, k):
    F = np.stack([feats[f][i][j][k] for f in ('stim_spec_z', 'stim_beat_z', 'stim_env_z', 'stim_der_z')])
    return resample_poly(F, 1, 2, axis=1).T                      # T x 4


def score(W, F, Y, tmin, tmax):
    n = min(len(F), len(Y)); P = predict(W, F[:n], FS, tmin, tmax); Yc = Y[:n] - Y[:n].mean(0); Pc = P - P.mean(0)
    r = (Pc * Yc).sum(0) / (np.sqrt((Pc ** 2).sum(0) * (Yc ** 2).sum(0)) + 1e-12)
    return float(r.mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='/home/user/data_local/weineck2022'); ap.add_argument('--feats', required=True); ap.add_argument('--fig3', required=True)
    ap.add_argument('--subj', default='10'); ap.add_argument('--wide', type=float, default=0.3); ap.add_argument('--lam', type=float, default=1.0)
    ap.add_argument('--tmin', type=float, default=0.0); ap.add_argument('--tmax', type=float, default=0.4); ap.add_argument('--out', default=None)
    a = ap.parse_args()
    feats, table = load_features(a.feats)
    sos = butter(4, [0.5, 8.0], btype='band', fs=1000.0, output='sos')
    trials = []
    for b in participant_blocks(a.data, a.subj):
        raw, ev = read_block(b)
        for s, e in trials_from_events(ev):
            trials.append((raw, s, e))
    durs = [e - s for (_, s, e) in trials]
    j, cost, assign = match_trials(durs, table)
    pub = published_counts(a.fig3, a.subj)
    pat = np.array([len(feats['stim_env_z'][i][j]) for i in range(13)])
    print(f"subj {a.subj}: {len(trials)} trials, subgroup {j} by duration fit; published per-tempo counts {pub.tolist()} vs subgroup pattern {pat.tolist()} (L1 {int(np.abs(pub-pat).sum())})")
    cands_all = [(i, k, L / FEAT_FS) for (i, jj, k, L) in table if jj == j]
    print("loading EEG ...", flush=True)
    Y = [prep_eeg(raw, s, e, sos) for (raw, s, e) in trials]
    from collections import Counter
    claims = Counter(x for x in assign if x is not None)
    dup = {x for x, c in claims.items() if c > 1}
    unamb = [n for n, x in enumerate(assign) if x is not None and x not in dup]
    for n, x in enumerate(assign):
        if x in dup:
            assign[n] = None
    print(f"duration-unique trials: {len(unamb)} (dropped {sum(claims[x] for x in dup)} trials sharing {len(dup)} stimuli)")
    used = {assign[n] for n in unamb}
    Fun = {n: feat64(feats, assign[n][0], j, assign[n][1]) for n in unamb}

    # ---- 3. self-test on unambiguous trials (leave-one-out)
    print(f"self-test on {len(unamb)} unambiguous trials ...", flush=True)
    windows = (0.02, 0.05, a.wide)
    st = {w: {'hit': [], 'margin': [], 'ncand': []} for w in windows}
    for n in unamb:
        train = [m for m in unamb if m != n]
        W, _ = fit_trf([Fun[m][:min(len(Fun[m]), len(Y[m]))] for m in train], [Y[m][:min(len(Fun[m]), len(Y[m]))] for m in train], FS, a.tmin, a.tmax, a.lam)
        d = durs[n] - TRIM_S
        s_true = score(W, Fun[n], Y[n], a.tmin, a.tmax)
        pool = [((i, k), abs(L - d)) for (i, k, L) in cands_all if abs(L - d) <= a.wide and (i, k) != assign[n]]
        sc = {ik: score(W, feat64(feats, ik[0], j, ik[1]), Y[n], a.tmin, a.tmax) for ik, _ in pool}
        for w in windows:
            dec = [sc[ik] for ik, dd in pool if dd <= w]
            if not dec:
                continue
            allsc = sorted(dec + [s_true], reverse=True)
            st[w]['hit'].append(s_true >= allsc[0]); st[w]['margin'].append(allsc[0] - allsc[1]); st[w]['ncand'].append(len(dec) + 1)
    self_test = {}
    for w in windows:
        h = np.array(st[w]['hit']); mg = np.array(st[w]['margin']); nc = np.array(st[w]['ncand'])
        if len(h) == 0:
            continue
        chance = float(np.mean(1.0 / nc))
        # precision of accepting a pick when its best-minus-second margin >= t
        prec = {}
        for t in (0.0, 0.01, 0.02, 0.03, 0.05):
            sel = mg >= t; prec[t] = (float(h[sel].mean()) if sel.any() else None, int(sel.sum()))
        self_test[w] = {'n': int(len(h)), 'accuracy': float(h.mean()), 'chance': chance, 'mean_candidates': float(nc.mean()), 'precision_by_margin': {str(k): v for k, v in prec.items()}}
        print(f"self-test decoys within ±{w*1000:.0f} ms: n={len(h)}, mean candidates {nc.mean():.1f}, accuracy {h.mean():.2f} (chance {chance:.2f}); precision at margin>=0.01/0.02/0.03/0.05: "
              + ", ".join(f"{prec[t][0]:.2f} (n={prec[t][1]})" if prec[t][0] is not None else "n/a" for t in (0.01, 0.02, 0.03, 0.05)))
    # acceptance threshold from the realistic window (±50 ms): smallest margin with precision >= 0.9 and n >= 10
    thr = None
    if 0.05 in self_test:
        for t in (0.0, 0.01, 0.02, 0.03, 0.05):
            pv, pn = self_test[0.05]['precision_by_margin'][str(t)]
            if pv is not None and pv >= 0.9 and pn >= 10:
                thr = t; break
    print(f"acceptance threshold (precision >= 0.9, ±50 ms decoys): margin >= {thr}")
    acc = self_test.get(0.05, {}).get('accuracy'); chance = self_test.get(0.05, {}).get('chance')

    # ---- 4. resolve the rest with a one-to-one assignment
    W, _ = fit_trf([Fun[m][:min(len(Fun[m]), len(Y[m]))] for m in unamb], [Y[m][:min(len(Fun[m]), len(Y[m]))] for m in unamb], FS, a.tmin, a.tmax, a.lam)
    unres = [n for n, x in enumerate(assign) if x is None]
    free = [(i, k, L) for (i, k, L) in cands_all if (i, k) not in used]
    print(f"resolving {len(unres)} trials among {len(free)} unassigned stimuli ...", flush=True)
    S = np.full((len(unres), len(free)), -np.inf)
    for r_, n in enumerate(unres):
        d = durs[n] - TRIM_S
        for c_, (i, k, L) in enumerate(free):
            if abs(L - d) <= a.wide:
                S[r_, c_] = score(W, feat64(feats, i, j, k), Y[n], a.tmin, a.tmax)
    cost_m = np.where(np.isfinite(S), -S, 1e3)
    rows, cols = linear_sum_assignment(cost_m)
    resolved = {}; accepted = 0
    for r_, c_ in zip(rows, cols):
        if not np.isfinite(S[r_, c_]):
            continue
        n = unres[r_]; i, k, L = free[c_]
        others = S[r_, np.isfinite(S[r_])]; margin = S[r_, c_] - (np.sort(others)[-2] if len(others) > 1 else -1.0)
        ok = thr is not None and margin >= thr
        resolved[n] = {'tempo_idx': int(i), 'trial_idx': int(k), 'score': float(S[r_, c_]), 'margin': float(margin), 'n_candidates': int(np.isfinite(S[r_]).sum()), 'accepted': bool(ok)}
        accepted += ok
    print(f"assigned {len(resolved)} / {len(unres)} unresolved trials; accepted at threshold: {accepted}")
    got_un = np.bincount([assign[n][0] for n in unamb], minlength=13)
    got_acc = got_un + np.bincount([v['tempo_idx'] for v in resolved.values() if v['accepted']], minlength=13)
    got_all = got_un + np.bincount([v['tempo_idx'] for v in resolved.values()], minlength=13)
    print(f"per-tempo counts  unambiguous {got_un.tolist()}\n                  +accepted   {got_acc.tolist()}  within presented set: {bool(np.all(got_acc <= pat))}\n                  +all        {got_all.tolist()}  within presented set: {bool(np.all(got_all <= pat))}\n                  presented   {pat.tolist()}\n                  published (after the authors' exclusions) {pub.tolist()}")
    if a.out:
        json.dump({'subj': a.subj, 'subgroup': int(j), 'n_trials': len(trials), 'n_unambiguous': len(unamb), 'self_test': {str(k): v for k, v in self_test.items()}, 'threshold': thr,
                   'resolved': {int(n): v for n, v in resolved.items()}, 'counts': {'unambiguous': got_un.tolist(), 'plus_accepted': got_acc.tolist(), 'plus_all': got_all.tolist(), 'presented': pat.tolist(), 'published': pub.tolist()}},
                  open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
