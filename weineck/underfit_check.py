#!/usr/bin/env python3
"""EXPLORATORY (not in the frozen pre-registration): the underfitting check for H2.

The confirmatory result (docs/STAGE2_RESULTS.md) stands unchanged; this script only asks
whether that result is explained by the linear model underfitting a stimulus-locked response.

Per participant (one-to-one trials, same preprocessing as q2_residual.py; features flux,
onsets, envelope, derivative at 64 Hz; lags 0-400 ms; the per-trial statistic is the shared
tagging z at all 13 grid tempi on the fronto-central residual at 256 Hz, scored against the
stimulus-label shuffle):
  A. Pooled TRF, leave-one-participant-out: kernel fitted on all other participants' trials
     (moments summed), lambda chosen by inner leave-one-participant-out on the training pool
     from the same grid; residual statistic as in Q2.
  B. Prediction tagging: the within-participant leave-one-trial-out TRF of Q2 (same lambda
     per trial as stored in the stage-2 JSON); the tagging statistic of the PREDICTION itself,
     reported as its own delta and as a ratio to the drive's delta.
  C. Linear-world simulation: Y_sim(trial) = P_full(trial) + noise, with P_full from the
     kernel fitted on all the participant's trials (median of the per-trial lambdas) and noise
     = Gaussian with the residual's amplitude spectrum SMOOTHED over ~0.5 Hz (median filter;
     spectral lines, including any beat-locked line, removed), same variance per channel, one
     random phase vector per trial shared across channels (keeps cross-channel structure). The
     variance split is preserved, so the held-out r is matched to the real ~0.04, while the
     only stimulus-locked content is the linear prediction. Y_sim then goes through the
     IDENTICAL Q2 pipeline (nested lambda, LOO residual, grid statistics, shuffle null).
     (Plain phase randomisation of the residual would be wrong here: it keeps the residual's
     beat-locked spectral line and a magnitude statistic would still see it.)
Outputs per participant: shuffle z and delta for A, B, C and the real residual (recomputed
here, must match stage 2). Group table printed by underfit_merge.py.
"""
import argparse, json, os, sys
import numpy as np
from collections import Counter
from scipy.signal import butter, sosfiltfilt, resample_poly
from scipy.stats import wilcoxon
from weineck_loader import (load_features, read_block, trials_from_events, participant_blocks,
                            match_trials, TRIM_S, TEMPI)
from mtrf import lag_matrix
from tagging import GRID, grid_stats, participant_shuffle_z

FC = ['Fz', 'FC1', 'FC2', 'Cz', 'F3', 'F4', 'C3', 'C4']; FS_TRF = 64.0; FS = 256.0
LAMS = (0.1, 1.0, 10.0, 100.0); TMIN, TMAX = 0.0, 0.4
SUBJECTS_ALL = ['1', '2', '3', '4', '7', '8', '9', '10', '11', '12', '13', '14', '16', '17', '18', '19', '20', '21', '22', '23',
                '24', '25', '26', '27', '28', '29', '30', '31', '32', '33', '34', '35', '36', '37']


def solve(A, B, lam):
    n = A.shape[0]; reg = lam * np.trace(A) / n * np.eye(n); reg[-1, -1] = 0.0
    return np.linalg.solve(A + reg, B)


def corr_cols(P, Y, idx):
    Pc = P - P.mean(0); Yc = Y - Y.mean(0)
    return float(((Pc * Yc).sum(0) / (np.sqrt((Pc ** 2).sum(0) * (Yc ** 2).sum(0)) + 1e-12))[idx].mean())


def load_participant_arrays(data_dir, subj, feats, table, sos):
    """Return X64 (list T x 32), F64 (list T x 4), XL (lag matrices with bias), fbeat, fcidx, drive256."""
    trials = []
    for b in participant_blocks(data_dir, subj):
        raw, ev = read_block(b); trials += [(raw, s, e) for s, e in trials_from_events(ev)]
    durs = [e - s for (_, s, e) in trials]; j, cost, assign = match_trials(durs, table)
    claims = Counter(x for x in assign if x is not None); dup = {x for x, c in claims.items() if c > 1}
    keepn = [n for n, x in enumerate(assign) if x is not None and x not in dup]
    X64, F64, XL, fbeat, drive = [], [], [], [], []
    fcidx = None
    for n in keepn:
        raw, s, e = trials[n]; i, k = assign[n]
        seg = raw.copy().crop(tmin=s + TRIM_S, tmax=e, include_tmax=False).load_data()
        names = seg.ch_names; keep = [c_ for c_, c in enumerate(names) if c != '33']
        X = seg.get_data()[keep]; X = X - X.mean(0, keepdims=True); X = sosfiltfilt(sos, X, axis=1)
        Xd = resample_poly(X, 16, 250, axis=1)
        F = np.stack([feats[f_][i][j][k] for f_ in ('stim_spec_z', 'stim_beat_z', 'stim_env_z', 'stim_der_z')]); F = resample_poly(F, 1, 2, axis=1)
        T = min(Xd.shape[1], F.shape[1]); Xd = Xd[:, :T]; F = F[:, :T]
        Xd = (Xd - Xd.mean(1, keepdims=True)) / (Xd.std(1, keepdims=True) + 1e-12)
        Xl, _ = lag_matrix(F.T, FS_TRF, TMIN, TMAX); Xl = np.hstack([Xl, np.ones((len(Xl), 1))])
        X64.append(Xd.T); F64.append(F.T); XL.append(Xl); fbeat.append(float(TEMPI[i]))
        if fcidx is None:
            fcidx = [keep.index(names.index(c)) for c in FC if c in names]
        drive.append(resample_poly(X[fcidx].mean(0), 32, 125))
    return X64, F64, XL, np.array(fbeat), fcidx, drive, int(j)


def nested_loo_residuals(X64, XL, fcidx):
    """Identical to q2_residual.py: per trial nested-lambda LOO ridge; returns residual FC drives at 256 Hz, predictions, r, lambdas."""
    A_i = [Xl.T @ Xl for Xl in XL]; B_i = [Xl.T @ Y for Xl, Y in zip(XL, X64)]
    A_tot = sum(A_i); B_tot = sum(B_i); N = len(X64)
    res256, preds, rs, lams = [], [], [], []
    for t_ in range(N):
        tr = [m for m in range(N) if m != t_]; A_tr = A_tot - A_i[t_]; B_tr = B_tot - B_i[t_]
        best = None
        for lam in LAMS:
            sc = [corr_cols(XL[v] @ solve(A_tr - A_i[v], B_tr - B_i[v], lam), X64[v], fcidx) for v in tr[:min(len(tr), 12)]]
            if best is None or np.mean(sc) > best[1]:
                best = (lam, float(np.mean(sc)))
        W = solve(A_tr, B_tr, best[0]); P = XL[t_] @ W; Y = X64[t_]
        rs.append(corr_cols(P, Y, fcidx)); lams.append(best[0]); preds.append(P)
        res256.append(resample_poly((Y - P)[:, fcidx].mean(1), 4, 1))
    return res256, preds, rs, lams


def score(drives, fbeat):
    Z = np.array([grid_stats((d - d.mean()) / (d.std() + 1e-12)) for d in drives])
    own = np.array([int(np.argmin(np.abs(GRID - f))) for f in fbeat])
    obs, z, mu, sd = participant_shuffle_z(Z, own, np.random.RandomState(0), 500)
    other = np.array([np.delete(Z[n], own[n]).mean() for n in range(len(Z))]); dd = Z[np.arange(len(Z)), own] - other
    return {'shuffle_z': z, 'delta': float(dd.mean() / (dd.std() + 1e-12)), 'obs': obs}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--data', default='/home/user/data_local/weineck2022'); ap.add_argument('--feats', required=True)
    ap.add_argument('--subjects', default=','.join(SUBJECTS_ALL)); ap.add_argument('--out', required=True); ap.add_argument('--seed', type=int, default=0)
    a = ap.parse_args()
    feats, table = load_features(a.feats); sos = butter(4, [0.5, 30.0], btype='band', fs=1000.0, output='sos')
    rng = np.random.RandomState(a.seed)
    # ---- load everyone once (needed for the pooled TRF, part A)
    print("loading all participants ...", flush=True)
    data = {}; chunk = set(a.subjects.split(','))
    for s in SUBJECTS_ALL:
        X64, F64, XL, fbeat, fcidx, drive, j = load_participant_arrays(a.data, s, feats, table, sos)
        A_s = sum(Xl.T @ Xl for Xl in XL); B_s = sum(Xl.T @ Y for Xl, Y in zip(XL, X64))
        if s in chunk:
            data[s] = dict(X64=X64, XL=XL, fbeat=fbeat, fcidx=fcidx, drive=drive, A=A_s, B=B_s, j=j)
        else:                                            # only what the pooled model needs
            data[s] = dict(X64=X64[:10], XL=XL[:10], fcidx=fcidx, A=A_s, B=B_s, j=j)
        print(f"  {s}: {len(X64)} trials", flush=True)
    A_all = sum(d['A'] for d in data.values()); B_all = sum(d['B'] for d in data.values())
    out = {'exploratory': True, 'subjects': {}}
    for s in a.subjects.split(','):
        d = data[s]; X64, XL, fbeat, fcidx, drive = d['X64'], d['XL'], d['fbeat'], d['fcidx'], d['drive']
        # ---- real residual (recomputed; must match stage 2) and B: prediction tagging
        res_real, preds, rs, lams = nested_loo_residuals(X64, XL, fcidx)
        pred256 = [resample_poly(P[:, fcidx].mean(1), 4, 1) for P in preds]
        sc_drive = score(drive, fbeat); sc_real = score(res_real, fbeat); sc_pred = score(pred256, fbeat)
        # ---- A: pooled LOPO TRF with inner LOPO lambda choice on the training pool
        A_tr = A_all - d['A']; B_tr = B_all - d['B']; best = None
        for lam in LAMS:
            sc = []
            for v in SUBJECTS_ALL:
                if v == s: continue
                W = solve(A_tr - data[v]['A'], B_tr - data[v]['B'], lam)
                sc.append(np.mean([corr_cols(Xl @ W, Y, data[v]['fcidx']) for Xl, Y in zip(data[v]['XL'][:10], data[v]['X64'][:10])]))
            if best is None or np.mean(sc) > best[1]:
                best = (lam, float(np.mean(sc)))
        W = solve(A_tr, B_tr, best[0])
        res_pool = [resample_poly((Y - Xl @ W)[:, fcidx].mean(1), 4, 1) for Xl, Y in zip(XL, X64)]
        r_pool = float(np.mean([corr_cols(Xl @ W, Y, fcidx) for Xl, Y in zip(XL, X64)]))
        sc_pool = score(res_pool, fbeat)
        # ---- C: linear-world simulation through the identical pipeline
        from scipy.ndimage import median_filter
        W_full = solve(d['A'], d['B'], float(np.median(lams)))
        Y_sim = []
        for Xl, Y in zip(XL, X64):
            P = Xl @ W_full; E = Y - P; n = len(E)
            Fe = np.fft.rfft(E, axis=0); amp = np.abs(Fe)
            win = max(5, int(round(0.5 / (FS_TRF / n))) | 1)                 # ~0.5 Hz smoothing window (odd number of bins)
            amp_s = median_filter(amp, size=(win, 1), mode='nearest')
            ph = rng.uniform(0, 2 * np.pi, Fe.shape[0]); ph[0] = 0
            if n % 2 == 0: ph[-1] = 0
            E_s = np.fft.irfft(amp_s * np.exp(1j * ph)[:, None], n=n, axis=0)
            E_s = E_s / (E_s.std(0, keepdims=True) + 1e-12) * E.std(0, keepdims=True)   # exact per-channel variance match
            Y_sim.append(P + E_s)
        res_sim, _, rs_sim, _ = nested_loo_residuals(Y_sim, XL, fcidx)
        sim_drive = [resample_poly(Y[:, fcidx].mean(1), 4, 1) for Y in Y_sim]
        sc_sim_drive = score(sim_drive, fbeat); sc_sim = score(res_sim, fbeat)
        out['subjects'][s] = {'N': len(X64), 'subgroup': d['j'], 'heldout_r_within': float(np.mean(rs)), 'heldout_r_pooled': r_pool, 'heldout_r_sim': float(np.mean(rs_sim)), 'lam_pooled': best[0],
                              'drive': sc_drive, 'resid_real': sc_real, 'pred': sc_pred, 'resid_pooled': sc_pool, 'sim_drive': sc_sim_drive, 'resid_sim': sc_sim}
        print(f"subj {s}: N={len(X64)} r_within={np.mean(rs):+.3f} r_pooled={r_pool:+.3f} r_sim={np.mean(rs_sim):+.3f} | delta: drive {sc_drive['delta']:+.3f} resid(real) {sc_real['delta']:+.3f} pred {sc_pred['delta']:+.3f} resid(pooled) {sc_pool['delta']:+.3f} | linear-world: drive {sc_sim_drive['delta']:+.3f} resid {sc_sim['delta']:+.3f}", flush=True)
        json.dump(out, open(a.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
