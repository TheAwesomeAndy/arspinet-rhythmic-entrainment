#!/usr/bin/env python3
"""Robustness grid for the stage-2 results (EXPLORATORY; docs/ROBUSTNESS_PLAN.md).
Reuses the stage-2 path: same trial matching and preprocessing (underfit_check.load_participant_arrays),
same readouts (q2_residual.stats_on: N0, N2a, N2b, R, R_pop, Rs), same tagging statistic and
stimulus-label shuffle (tagging.py), same nested-lambda leave-one-trial-out ridge TRF.
One CLI row per process; output weineck/results/robustness/<row>.json.
"""
import argparse, json, os, sys, time
import numpy as np
from scipy.signal import butter, sosfiltfilt, resample_poly
from weineck_loader import load_features, TEMPI
from underfit_check import load_participant_arrays, solve, corr_cols, SUBJECTS_ALL
from mtrf import lag_matrix
from tagging import GRID, grid_stats, participant_shuffle_z
import q2_residual as q2
sys.path.insert(0, '/home/user/dissoAdventureExperiments/chapter5Experiments')
from experiment_zero import LIFReservoir

FS_TRF = 64.0; FS = 256.0; LAMS = (0.1, 1.0, 10.0, 100.0)
ROWS = {
    'baseline': dict(seed=42, rho=0.9, beta=0.05, feats=(0, 1, 2, 3), tmax=0.4),
    'seed7': dict(seed=7, rho=0.9, beta=0.05, feats=(0, 1, 2, 3), tmax=0.4),
    'seed99': dict(seed=99, rho=0.9, beta=0.05, feats=(0, 1, 2, 3), tmax=0.4),
    'rho0': dict(seed=42, rho=0.0, beta=0.05, feats=(0, 1, 2, 3), tmax=0.4),
    'rho0.3': dict(seed=42, rho=0.3, beta=0.05, feats=(0, 1, 2, 3), tmax=0.4),
    'rho1.2': dict(seed=42, rho=1.2, beta=0.05, feats=(0, 1, 2, 3), tmax=0.4),
    'beta0.01': dict(seed=42, rho=0.9, beta=0.01, feats=(0, 1, 2, 3), tmax=0.4),
    'beta0.004': dict(seed=42, rho=0.9, beta=0.004, feats=(0, 1, 2, 3), tmax=0.4),
    'trf_flux': dict(seed=42, rho=0.9, beta=0.05, feats=(0,), tmax=0.4),
    'trf_long': dict(seed=42, rho=0.9, beta=0.05, feats=(0, 1, 2, 3), tmax=0.6),
    'iaaft': dict(seed=42, rho=0.9, beta=0.05, feats=(0, 1, 2, 3), tmax=0.4, n_surr=200),
}


def make_reservoirs(seed, rho, beta):
    """Canonical reservoir with the row's rho and beta, plus its shuffled-weight twin (same rho)."""
    r = LIFReservoir(seed=seed)                       # weights at rho 0.9
    r.W_rec = r.W_rec * (rho / 0.9); r.beta = beta
    rs = LIFReservoir(seed=seed); rng = np.random.RandomState(seed + 1000)
    W = rs.W_rec.copy().ravel(); rng.shuffle(W); W = W.reshape(rs.W_rec.shape)
    eig = np.abs(np.linalg.eigvals(W)).max(); rs.W_rec = W * (rho / eig if eig > 0 else 0.0); rs.beta = beta
    assert abs(1.0 / (beta * FS) - {0.05: 0.078, 0.01: 0.391, 0.004: 0.977}.get(beta, 1.0 / (beta * FS))) < 2e-3, "tau = 1/(beta*fs) check"
    return r, rs


def build_XL(F64, feats, tmax):
    XL = []
    for F in F64:
        Xl, _ = lag_matrix(F[:, list(feats)], FS_TRF, 0.0, tmax); XL.append(np.hstack([Xl, np.ones((len(Xl), 1))]))
    return XL


def loo_residuals(X64, XL, fcidx):
    A_i = [Xl.T @ Xl for Xl in XL]; B_i = [Xl.T @ Y for Xl, Y in zip(XL, X64)]; A_tot = sum(A_i); B_tot = sum(B_i); N = len(X64)
    res256, rs = [], []
    for t_ in range(N):
        tr = [m for m in range(N) if m != t_]; A_tr = A_tot - A_i[t_]; B_tr = B_tot - B_i[t_]; best = None
        for lam in LAMS:
            sc = [corr_cols(XL[v] @ solve(A_tr - A_i[v], B_tr - B_i[v], lam), X64[v], fcidx) for v in tr[:min(len(tr), 12)]]
            if best is None or np.mean(sc) > best[1]:
                best = (lam, float(np.mean(sc)))
        W = solve(A_tr, B_tr, best[0]); P = XL[t_] @ W; Y = X64[t_]
        rs.append(corr_cols(P, Y, fcidx)); res256.append(resample_poly((Y - P)[:, fcidx].mean(1), 4, 1))
    return res256, rs


def iaaft(x, rng, n_iter=20):
    """Iterative amplitude-adjusted Fourier transform surrogate (Schreiber & Schmitz 1996)."""
    x = np.asarray(x, float); n = len(x); amp = np.abs(np.fft.rfft(x)); sorted_x = np.sort(x)
    s = rng.permutation(x)
    for _ in range(n_iter):
        ph = np.angle(np.fft.rfft(s)); s = np.fft.irfft(amp * np.exp(1j * ph), n=n)
        s = sorted_x[np.argsort(np.argsort(s))]
    return s


def participant_scores(drives, fbeat, rng):
    Z = np.array([grid_stats((d - d.mean()) / (d.std() + 1e-12)) for d in drives]); own = np.array([int(np.argmin(np.abs(GRID - f))) for f in fbeat])
    obs, z, mu, sd = participant_shuffle_z(Z, own, rng, 500)
    other = np.array([np.delete(Z[n], own[n]).mean() for n in range(len(Z))]); dd = Z[np.arange(len(Z)), own] - other
    return {'shuffle_z': z, 'delta': float(dd.mean() / (dd.std() + 1e-12))}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--row', required=True, choices=list(ROWS)); ap.add_argument('--feats', required=True)
    ap.add_argument('--data', default='/home/user/data_local/weineck2022'); ap.add_argument('--subjects', default=','.join(SUBJECTS_ALL)); ap.add_argument('--out', default=None)
    a = ap.parse_args(); cfg = ROWS[a.row]
    out_path = a.out or f'/home/user/arspinet-rhythmic-entrainment/weineck/results/robustness/{a.row}.json'; os.makedirs(os.path.dirname(out_path), exist_ok=True)
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] row {a.row} start: {cfg}", flush=True)
    feats, table = load_features(a.feats); sos = butter(4, [0.5, 30.0], btype='band', fs=1000.0, output='sos'); sos_env = butter(4, [0.5, 8.0], btype='band', fs=FS, output='sos')
    res, res_s = make_reservoirs(cfg['seed'], cfg['rho'], cfg['beta'])
    out = {'row': a.row, 'config': {k: (list(v) if isinstance(v, tuple) else v) for k, v in cfg.items()}, 'tau_ms': 1000.0 / (cfg['beta'] * FS), 'subjects': {}, 'started': time.strftime('%Y-%m-%d %H:%M:%S')}
    for s in a.subjects.split(','):
        t0 = time.time(); X64, F64, XL_default, fbeat, fcidx, drive, j = load_participant_arrays(a.data, s, feats, table, sos)
        if len(X64) < 40:
            print(f"subj {s}: excluded ({len(X64)} trials)"); continue
        XL = build_XL(F64, cfg['feats'], cfg['tmax']); resid, rs = loo_residuals(X64, XL, fcidx)
        rng = np.random.RandomState(int(s))
        resid = [r_[:min(len(d), len(r_))] for d, r_ in zip(drive, resid)]       # common length, as in q2_residual.py
        if a.row == 'iaaft':
            real = participant_scores(resid, fbeat, np.random.RandomState(int(s)))
            surr = []
            for k in range(cfg['n_surr']):
                sur = [iaaft(d, rng) for d in resid]; surr.append(participant_scores(sur, fbeat, np.random.RandomState(int(s)))['delta'])
            surr = np.array(surr)
            out['subjects'][s] = {'N': len(X64), 'heldout_r': float(np.mean(rs)), 'resid_N0_real': real, 'iaaft_delta_mean': float(surr.mean()), 'iaaft_delta_sd': float(surr.std()),
                                  'real_percentile_in_iaaft': float((surr < real['delta']).mean()), 'iaaft_deltas': surr.tolist()}
            print(f"subj {s}: N={len(X64)} real resid delta {real['delta']:+.3f}; IAAFT deltas mean {surr.mean():+.3f} sd {surr.std():.3f}; real at percentile {(surr < real['delta']).mean():.2f}  ({time.time()-t0:.0f}s)", flush=True)
        else:
            rows = []
            for d, r_, f in zip(drive, resid, fbeat):
                n = min(len(d), len(r_)); d = d[:n]; r_ = r_[:n]          # common length, exactly as in q2_residual.py
                rows.append({'f': f, 'drive': q2.stats_on(d, f, res, res_s, sos_env), 'resid': q2.stats_on(r_, f, res, res_s, sos_env)})
            N = len(rows); own = np.array([int(np.argmin(np.abs(GRID - r['f']))) for r in rows]); summ = {'N': N, 'heldout_r': float(np.mean(rs))}
            for src in ('drive', 'resid'):
                for st in ('N0', 'N2a', 'N2b', 'R', 'R_pop', 'Rs'):
                    Z = np.array([r[src][st] for r in rows]); obs, z, mu, sd = participant_shuffle_z(Z, own, np.random.RandomState(int(s)), 500)
                    other = np.array([np.delete(Z[n], own[n]).mean() for n in range(N)]); dd = Z[np.arange(N), own] - other
                    summ[f'{src}_{st}'] = {'shuffle_z': z, 'delta': float(dd.mean() / (dd.std() + 1e-12))}
            out['subjects'][s] = summ
            print(f"subj {s}: N={N} r={np.mean(rs):+.3f} | resid delta N0 {summ['resid_N0']['delta']:+.3f} R {summ['resid_R']['delta']:+.3f} Rs {summ['resid_Rs']['delta']:+.3f} | drive N0 {summ['drive_N0']['delta']:+.3f} R {summ['drive_R']['delta']:+.3f}  ({time.time()-t0:.0f}s)", flush=True)
        json.dump(out, open(out_path, 'w'))
    out['ended'] = time.strftime('%Y-%m-%d %H:%M:%S'); json.dump(out, open(out_path, 'w'))
    print(f"[{out['ended']}] row {a.row} end", flush=True)


if __name__ == '__main__':
    main()
