#!/usr/bin/env python3
"""Q2: beat-locked structure in the residual of a maximal linear encoding model (Weineck 2022).

Per participant, one-to-one trials only.
 1. EEG: 32 ch, average reference, 0.5-30 Hz, 64 Hz for the TRF; features (flux, onsets,
    envelope, derivative) at 64 Hz; windows aligned (first second dropped).
 2. Forward ridge TRF, lags 0-400 ms, lambda chosen by nested leave-one-trial-out within the
    training set (grid 0.1, 1, 10, 100 x trace-normalised), prediction for the held-out trial;
    residual = EEG - prediction, per channel; fronto-central cluster mean -> 256 Hz drive.
 3. Per-trial statistics on the residual drive, each evaluated at every one of the 13 grid
    tempi (own tempo = the beat label):
      N0  tagging of the residual (linear);
      N2a tagging of its 0.5-8 Hz Hilbert envelope;  N2b tagging of its square;
      R   reservoir unit-PC1;  R_pop population rate;  Rs unit-PC1 with shuffled weights.
    Also the same statistics on the EEG drive itself (before subtraction) for reference.
 4. Participant-level z: mean own-tempo statistic against a stimulus-label shuffle (each trial
    re-labelled with another grid tempo > 5 % away; 500 shuffles). Group: one-sided Wilcoxon on
    the participant z's (H2 on N0 and on R); paired contrasts R - N0, R - N2a, R - N2b.
Outputs JSON with per-participant scores; prints the group table.
"""
import argparse, json, os, sys
import numpy as np
from collections import Counter
from scipy.signal import butter, sosfiltfilt, resample_poly, welch, hilbert
from scipy.stats import wilcoxon
from weineck_loader import (load_features, read_block, trials_from_events, participant_blocks,
                            match_trials, FEAT_FS, TRIM_S, TEMPI)
from mtrf import fit_trf, predict, lag_matrix
from tagging import tag_z, GRID, grid_stats, participant_shuffle_z
sys.path.insert(0, '/home/user/dissoAdventureExperiments/chapter5Experiments')
from experiment_zero import LIFReservoir

FC = ['Fz', 'FC1', 'FC2', 'Cz', 'F3', 'F4', 'C3', 'C4']; FS_TRF = 64.0; FS = 256.0
LAMS = (0.1, 1.0, 10.0, 100.0)




def shuffled(seed):
    r = LIFReservoir(seed=seed); rng = np.random.RandomState(seed + 1000)
    W = r.W_rec.copy().ravel(); rng.shuffle(W); W = W.reshape(r.W_rec.shape); r.W_rec = W * (0.9 / np.abs(np.linalg.eigvals(W)).max()); return r


def pc1(M):
    U, s_, Vt = np.linalg.svd(M - M.mean(0), full_matrices=False); return U[:, 0] * s_[0]


def stats_on(drive, f, res, res_s, sos_env):
    x = (drive - drive.mean()) / (drive.std() + 1e-12)
    S = res.forward(x); Ss = res_s.forward(x)
    env = np.abs(hilbert(sosfiltfilt(sos_env, x)))
    g = lambda v: grid_stats(v).tolist()
    return {'N0': g(x), 'N2a': g(env), 'N2b': g(x ** 2), 'R': g(pc1(S)), 'R_pop': g(S.mean(1)), 'Rs': g(pc1(Ss))}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--data', default='/home/user/data_local/weineck2022'); ap.add_argument('--feats', required=True)
    ap.add_argument('--subjects', default='10,11,12,13,14,16,17,18'); ap.add_argument('--out', default='results/q2_residual.json'); ap.add_argument('--min-trials', type=int, default=40)
    a = ap.parse_args()
    feats, table = load_features(a.feats)
    sos = butter(4, [0.5, 30.0], btype='band', fs=1000.0, output='sos'); sos_env = butter(4, [0.5, 8.0], btype='band', fs=FS, output='sos')
    res = LIFReservoir(seed=42); res_s = shuffled(42)
    out = {'subjects': {}, 'min_trials': a.min_trials}
    for subj in a.subjects.split(','):
        trials = []
        for b in participant_blocks(a.data, subj):
            raw, ev = read_block(b); trials += [(raw, s, e) for s, e in trials_from_events(ev)]
        durs = [e - s for (_, s, e) in trials]; j, cost, assign = match_trials(durs, table)
        claims = Counter(x for x in assign if x is not None); dup = {x for x, c in claims.items() if c > 1}
        keepn = [n for n, x in enumerate(assign) if x is not None and x not in dup]
        if len(keepn) < a.min_trials:
            print(f"subj {subj}: {len(keepn)} one-to-one trials < {a.min_trials}, excluded"); continue
        X64, F64, drive256, fbeat = [], [], [], []
        for n in keepn:
            raw, s, e = trials[n]; i, k = assign[n]
            seg = raw.copy().crop(tmin=s + TRIM_S, tmax=e, include_tmax=False).load_data()
            names = seg.ch_names; keep = [c_ for c_, c in enumerate(names) if c != '33']
            X = seg.get_data()[keep]; X = X - X.mean(0, keepdims=True); X = sosfiltfilt(sos, X, axis=1)
            Xd = resample_poly(X, 16, 250, axis=1)                                  # 64 Hz
            F = np.stack([feats[f_][i][j][k] for f_ in ('stim_spec_z', 'stim_beat_z', 'stim_env_z', 'stim_der_z')]); F = resample_poly(F, 1, 2, axis=1)
            T = min(Xd.shape[1], F.shape[1]); Xd = Xd[:, :T]; F = F[:, :T]
            Xd = (Xd - Xd.mean(1, keepdims=True)) / (Xd.std(1, keepdims=True) + 1e-12)
            X64.append(Xd.T); F64.append(F.T); fbeat.append(float(TEMPI[i]))
            idx = [keep.index(names.index(c)) for c in FC if c in names]; drive256.append(resample_poly(X[idx].mean(0), 32, 125))
        fcidx = [keep.index(names.index(c)) for c in FC if c in names]
        rows = []
        for t_ in range(len(keepn)):
            tr = [m for m in range(len(keepn)) if m != t_]
            # nested lambda choice on the training trials (leave-one-out within training)
            best = None
            for lam in LAMS:
                rs = []
                for v in tr[:min(len(tr), 12)]:                                      # inner folds capped at 12 for cost
                    tr2 = [m for m in tr if m != v]
                    W, _ = fit_trf([F64[m] for m in tr2], [X64[m] for m in tr2], FS_TRF, 0.0, 0.4, lam)
                    P = predict(W, F64[v], FS_TRF, 0.0, 0.4); Y = X64[v]
                    Pc = P - P.mean(0); Yc = Y - Y.mean(0); rs.append(((Pc * Yc).sum(0) / (np.sqrt((Pc ** 2).sum(0) * (Yc ** 2).sum(0)) + 1e-12))[fcidx].mean())
                if best is None or np.mean(rs) > best[1]:
                    best = (lam, float(np.mean(rs)))
            W, _ = fit_trf([F64[m] for m in tr], [X64[m] for m in tr], FS_TRF, 0.0, 0.4, best[0])
            P = predict(W, F64[t_], FS_TRF, 0.0, 0.4); Y = X64[t_]
            Pc = P - P.mean(0); Yc = Y - Y.mean(0); r_fc = float(((Pc * Yc).sum(0) / (np.sqrt((Pc ** 2).sum(0) * (Yc ** 2).sum(0)) + 1e-12))[fcidx].mean())
            resid_fc = (Y - P)[:, fcidx].mean(1); resid256 = resample_poly(resid_fc, 4, 1)
            d256 = drive256[t_][:len(resid256)]; resid256 = resid256[:len(d256)]
            rows.append({'f': fbeat[t_], 'lam': best[0], 'pred_r_fc': r_fc, 'drive': stats_on(d256, fbeat[t_], res, res_s, sos_env), 'resid': stats_on(resid256, fbeat[t_], res, res_s, sos_env)})
            if t_ % 20 == 0:
                print(f"  subj {subj} trial {t_+1}/{len(keepn)} lam={best[0]} pred r(FC)={r_fc:+.3f} resid N0={rows[-1]['resid']['N0']:+.2f} R={rows[-1]['resid']['R']:+.2f}", flush=True)
        N = len(rows); summ = {}; rng_s = np.random.RandomState(int(subj))
        own = np.array([int(np.argmin(np.abs(GRID - r['f']))) for r in rows])
        for src in ('drive', 'resid'):
            for st in ('N0', 'N2a', 'N2b', 'R', 'R_pop', 'Rs'):
                Z = np.array([r[src][st] for r in rows])                   # N x 13
                obs, z, mu, sd = participant_shuffle_z(Z, own, rng_s, 500)
                summ[f'{src}_{st}'] = {'obs_mean': obs, 'shuffle_z': z, 'shuffle_mean': mu, 'shuffle_sd': sd}
        summ['pred_r_fc_mean'] = float(np.mean([r['pred_r_fc'] for r in rows])); summ['N'] = N
        out['subjects'][subj] = {'subgroup': int(j), 'trials': rows, 'scores': summ}
        bm = lambda k: summ[k]['shuffle_z']
        print(f"subj {subj}: N={N}, mean held-out TRF r(FC)={summ['pred_r_fc_mean']:+.3f} | shuffle-z: drive N0 {bm('drive_N0'):+.2f} R {bm('drive_R'):+.2f} | resid N0 {bm('resid_N0'):+.2f} N2a {bm('resid_N2a'):+.2f} N2b {bm('resid_N2b'):+.2f} R {bm('resid_R'):+.2f} R_pop {bm('resid_R_pop'):+.2f} Rs {bm('resid_Rs'):+.2f}", flush=True)
        json.dump(out, open(a.out, 'w'), indent=1)
    subs = list(out['subjects'])
    print(f"\ngroup (n={len(subs)}): participant shuffle-z per statistic; one-sided Wilcoxon > 0")
    out['group'] = {}
    for key in ('drive_N0', 'drive_R', 'resid_N0', 'resid_N2a', 'resid_N2b', 'resid_R', 'resid_R_pop', 'resid_Rs'):
        v = np.array([out['subjects'][s]['scores'][key]['shuffle_z'] for s in subs])
        p = float(wilcoxon(v, alternative='greater').pvalue) if len(v) >= 5 and np.any(v != 0) else float('nan')
        out['group'][key] = {'z_values': v.tolist(), 'median_z': float(np.median(v)), 'frac_positive': float((v > 0).mean()), 'p_wilcoxon': p}
        print(f"  {key:>10}: median z {np.median(v):+.2f}, participants positive {(v>0).mean():.2f}, p={p:.3f}")
    for aa, bb in (('resid_R', 'resid_N0'), ('resid_R', 'resid_N2a'), ('resid_R', 'resid_N2b')):
        d = np.array([out['subjects'][s]['scores'][aa]['shuffle_z'] - out['subjects'][s]['scores'][bb]['shuffle_z'] for s in subs])
        print(f"  paired {aa} - {bb}: median {np.median(d):+.2f}, frac>0 {(d>0).mean():.2f}")
    json.dump(out, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
