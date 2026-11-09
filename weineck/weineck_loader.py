#!/usr/bin/env python3
"""Loader for Weineck, Wen & Henry (2022) raw EEG + released stimulus features.

Data: OSF y5xhs (CC BY 4.0). Raw EEG: BrainVision (.vhdr/.vmrk/.eeg), 32 actiCap,
four recording blocks per participant. Markers: 40 = start of music segment,
80 = end, 120/180 = short repetition for tapping. Features (Figure1_SourceData1.mat,
128 Hz, z-scored): stim_env_z, stim_der_z, stim_beat_z, stim_spec_z, each a
13 (tempi 1-4 Hz, 0.25 steps) x 4 (stimulation subgroup) cell of trial vectors.

The per-participant presentation order is not released, so trials are mapped to
feature vectors by duration: (1) the participant's subgroup is the one whose
multiset of feature lengths (at 128 Hz) best matches the multiset of marker
40->80 durations; (2) within that subgroup each trial is assigned the unique
feature vector whose length matches its duration within `tol_s`; trials with
zero or several candidates are dropped and reported.
"""
import glob, os, re
import numpy as np
import scipy.io
import mne

TEMPI = np.arange(1.0, 4.01, 0.25)
FEAT_FS = 128.0
FEATURES = ('stim_env_z', 'stim_der_z', 'stim_beat_z', 'stim_spec_z')


def load_features(path):
    m = scipy.io.loadmat(path, squeeze_me=False)
    feats = {}
    for k in FEATURES:
        cell = m[k]                                      # (13, 4) object array
        feats[k] = [[[np.asarray(t).ravel().astype(float) for t in np.atleast_1d(cell[i, j]).ravel()]
                     for j in range(4)] for i in range(13)]
    # table of (tempo_idx, subgroup, trial_idx, length)
    table = []
    for i in range(13):
        for j in range(4):
            for a, v in enumerate(feats['stim_env_z'][i][j]):
                table.append((i, j, a, len(v)))
    return feats, table


def read_block(vhdr):
    raw = mne.io.read_raw_brainvision(vhdr, preload=False, verbose='ERROR')
    ann = raw.annotations
    ev = []
    for a in ann:
        mm = re.search(r'S\s*(\d+)', a['description'])
        if mm:
            ev.append((float(a['onset']), int(mm.group(1))))
    return raw, ev


def trials_from_events(ev):
    """Pair each 40 with the next 80 -> (t_start, t_end) in seconds."""
    out = []
    start = None
    for t, code in ev:
        if code == 40:
            start = t
        elif code == 80 and start is not None:
            out.append((start, t)); start = None
    return out


def participant_blocks(data_dir, subj):
    return sorted(glob.glob(os.path.join(data_dir, f'Musentrain_subj{subj}_block*.vhdr')),
                  key=lambda p: int(re.search(r'block(\d+)', p).group(1)))


TRIM_S = 1.0   # released feature vectors are the 40->80 listening window minus 1.0 s (fitted: 81-83 % of trials within 20 ms)


def match_trials(durations_s, table, tol_s=0.02, trim_s=TRIM_S, subgroup=None):
    """Return (subgroup, mean_cost, assignments) where assignments[k] = (tempo_idx, trial_idx) or None.
    Expected feature length (s) = duration - trim_s."""
    durations_s = [d - trim_s for d in durations_s]
    best = None
    for j in ([subgroup] if subgroup is not None else range(4)):
        lens = np.array([L for (i, jj, a, L) in table if jj == j]) / FEAT_FS
        cost = 0.0
        for d in durations_s:
            cost += np.min(np.abs(lens - d))
        if best is None or cost < best[1]:
            best = (j, cost)
    j = best[0]
    cands = [(i, a, L / FEAT_FS) for (i, jj, a, L) in table if jj == j]
    assign = []
    for d in durations_s:
        hits = [(i, a) for (i, a, L) in cands if abs(L - d) <= tol_s]
        assign.append(hits[0] if len(hits) == 1 else None)
    return j, best[1] / max(len(durations_s), 1), assign


def load_participant(data_dir, subj, feat_path, eeg_fs_out=256.0, tol_s=0.02, trim_side='start', subgroup=None, verbose=True):
    """Yield dicts per matched trial: eeg (n_ch x T at eeg_fs_out), feats (4 x T), tempo_hz, ch_names."""
    feats, table = load_features(feat_path)
    blocks = participant_blocks(data_dir, subj)
    all_trials = []
    for b in blocks:
        raw, ev = read_block(b)
        tr = trials_from_events(ev)
        all_trials += [(b, raw, s, e) for s, e in tr]
    durs = [e - s for (_, _, s, e) in all_trials]
    j, mean_cost, assign = match_trials(durs, table, tol_s, subgroup=subgroup)
    n_ok = sum(a is not None for a in assign)
    if verbose:
        print(f"subj {subj}: {len(blocks)} blocks, {len(all_trials)} trials, subgroup {j} (mean |dur-len| {mean_cost*1000:.1f} ms), matched {n_ok}/{len(all_trials)} unambiguously")
    out = []
    for (b, raw, s, e), a in zip(all_trials, assign):
        if a is None:
            continue
        i, k = a
        # drop the trimmed second from the chosen side so EEG and feature windows coincide
        if trim_side == 'start':
            s_, e_ = s + TRIM_S, e
        elif trim_side == 'end':
            s_, e_ = s, e - TRIM_S
        else:                      # 'none': keep the whole 40->80 window (1 s longer than the features)
            s_, e_ = s, e
        seg = raw.copy().crop(tmin=s_, tmax=e_, include_tmax=False).load_data()
        seg.resample(eeg_fs_out, verbose='ERROR')
        x = seg.get_data()                                  # n_ch x T (volts)
        F = np.stack([feats[f][i][j][k] for f in FEATURES])  # 4 x L at 128 Hz
        out.append({'block': os.path.basename(b), 't0': s, 'dur': e - s, 'tempo_hz': float(TEMPI[i]),
                    'tempo_idx': i, 'subgroup': j, 'trial_idx': k, 'eeg': x, 'eeg_fs': eeg_fs_out,
                    'feats': F, 'feat_fs': FEAT_FS, 'ch_names': seg.ch_names})
    return out


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--data', default='/home/user/data_local/weineck2022')
    ap.add_argument('--feats', required=True)
    ap.add_argument('--subj', default='10'); ap.add_argument('--trim-side', default='start')
    a = ap.parse_args()
    tr = load_participant(a.data, a.subj, a.feats, trim_side=a.trim_side)
    from collections import Counter
    print('trials per tempo:', sorted(Counter(t['tempo_hz'] for t in tr).items()))
    if tr:
        t = tr[0]; print('example:', t['block'], f"t0={t['t0']:.1f}s dur={t['dur']:.1f}s tempo={t['tempo_hz']} eeg {t['eeg'].shape} feats {t['feats'].shape} ch[:5] {t['ch_names'][:5]}")
