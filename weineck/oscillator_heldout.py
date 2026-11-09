#!/usr/bin/env python3
"""Theory 3 (EXPLORATORY, after the stage-2 merge; rule in docs/OSCILLATOR_DECISION_RULE.md):
held-out-TEMPO comparison of stimulus-driven oscillator encoding models against evoked kernels.

Per participant (one-to-one trials, Q2 preprocessing, 32 channels at 64 Hz):
  models  a  Hopf bank (Re z, |z|)            b  resonate-and-fire bank (rates)
          c  linear damped-oscillator bank    d_short  4-feature TRF 0-400 ms
          d_long  4-feature TRF 0-1000 ms     aug  [Hopf outputs + 4 TRF features]
          aug_lin  [linear-bank outputs + 4 TRF features]  (control for the rule's second clause)
  Oscillator outputs enter the ridge model with lags 0-400 ms (every 2nd sample at 64 Hz);
  TRF features with every lag. Free oscillator parameters (small grid in oscillator_bank.py)
  and lambda are chosen by inner leave-one-tempo-out on the 12 training tempi only.
  Outer CV: leave-one-tempo-out over the 13 tempi (train on 12, predict all trials of the
  held-out tempo). Metric: mean r at fronto-central channels over the held-out tempo's trials.
Also stored per model and held-out tempo: residual grid tagging statistics (shared statistic),
cross-spectral phase at the beat between prediction and EEG (phase-lag signature), and the
Hopf bank's mean |z| per oscillator per stimulation tempo (resonance curve).
--simulate hopf|trf : replace the EEG by data simulated from the fitted model (+ line-free
noise matched to the held-out r) and rerun the identical comparison (validation).
"""
import argparse, json, os, sys, time
import numpy as np
from scipy.signal import butter, resample_poly
from scipy.ndimage import median_filter
from weineck_loader import load_features
from underfit_check import load_participant_arrays, solve, corr_cols
from mtrf import lag_matrix
from tagging import GRID, grid_stats, participant_shuffle_z
import oscillator_bank as ob

FS_TRF = 64.0; FS = 256.0; LAMS = (0.1, 1.0, 10.0, 100.0, 1000.0)
LAG_OSC = (0.0, 0.4, 2)        # tmin, tmax, step in samples
LAG_SHORT = (0.0, 0.4, 1); LAG_LONG = (0.0, 1.0, 1)


def lagmat(X, spec):
    tmin, tmax, step = spec
    Xl, lags = lag_matrix(X, FS_TRF, tmin, tmax)
    if step > 1:
        F = X.shape[1]; keep = np.concatenate([np.arange(k * F, (k + 1) * F) for k in range(0, len(lags), step)])
        Xl = Xl[:, keep]
    return np.hstack([Xl, np.ones((len(Xl), 1))])


def model_outputs(F64, name, params):
    """Per-trial regressor matrices (before lags) for one model/config."""
    outs = []
    for F in F64:
        u = F[:, :2]                                             # spectral flux + beat onsets
        if name == 'hopf':
            outs.append(ob.hopf_bank(u, **params))
        elif name == 'rf':
            outs.append(ob.rf_bank(u, **params))
        elif name == 'lin':
            outs.append(ob.linear_bank(u, **params))
        else:
            raise ValueError(name)
    # standardise each output column across the participant's trials (train/test share the
    # scaling; it is label-free and stimulus-only, so no EEG leaks)
    cat = np.concatenate(outs); mu = cat.mean(0); sd = cat.std(0) + 1e-9
    return [(o - mu) / sd for o in outs]


def build(F64, X64, name, params):
    """Return per-trial lag matrices for a model: list of (T x p)."""
    if name == 'd_short':
        return [lagmat(F, LAG_SHORT) for F in F64]
    if name == 'd_long':
        return [lagmat(F, LAG_LONG) for F in F64]
    if name in ('hopf', 'rf', 'lin'):
        return [lagmat(o, LAG_OSC) for o in model_outputs(F64, name, params)]
    if name in ('aug', 'aug_lin'):
        base = 'hopf' if name == 'aug' else 'lin'
        return [np.hstack([lagmat(o, LAG_OSC)[:, :-1], lagmat(F, LAG_SHORT)]) for o, F in zip(model_outputs(F64, base, params), F64)]
    raise ValueError(name)


def tempo_moments(XL, X64, tidx, n_tempi=13):
    p = XL[0].shape[1]; nch = X64[0].shape[1]
    A = np.zeros((n_tempi, p, p)); B = np.zeros((n_tempi, p, nch))
    for Xl, Y, t in zip(XL, X64, tidx):
        A[t] += Xl.T @ Xl; B[t] += Xl.T @ Y
    return A, B


def loto(XL, X64, tidx, fcidx, configs_XL):
    """Leave-one-tempo-out with inner (config, lambda) selection on the training tempi.
    configs_XL: dict config_key -> list of per-trial lag matrices. Returns per held-out tempo:
    r_fc, chosen key/lambda, predictions and residuals for the held-out trials."""
    tempi_present = sorted(set(tidx)); results = {}
    mom = {k: tempo_moments(xl, X64, tidx) for k, xl in configs_XL.items()}
    for ho in tempi_present:
        train_t = [t for t in tempi_present if t != ho]
        best = None
        for k, (A, B) in mom.items():
            A_tr = A.sum(0) - A[ho]; B_tr = B.sum(0) - B[ho]
            for lam in LAMS:
                rs = []
                for v in train_t:
                    W = solve(A_tr - A[v], B_tr - B[v], lam)
                    rs += [corr_cols(configs_XL[k][n] @ W, X64[n], fcidx) for n in range(len(X64)) if tidx[n] == v]
                if best is None or np.mean(rs) > best[0]:
                    best = (float(np.mean(rs)), k, lam)
        _, k, lam = best; A, B = mom[k]
        W = solve(A.sum(0) - A[ho], B.sum(0) - B[ho], lam)
        idx = [n for n in range(len(X64)) if tidx[n] == ho]
        preds = {n: configs_XL[k][n] @ W for n in idx}
        r = float(np.mean([corr_cols(preds[n], X64[n], fcidx) for n in idx]))
        results[ho] = {'r_fc': r, 'config': k, 'lam': lam, 'inner_r': best[0], 'pred': preds}
    return results


def phase_lag(pred_fc, eeg_fc, f):
    """Cross-spectral phase at f (rad) between prediction and EEG, positive = EEG lags prediction."""
    n = len(pred_fc); t = np.arange(n) / FS_TRF; e = np.exp(-2j * np.pi * f * t)
    a = np.sum((pred_fc - pred_fc.mean()) * e); b = np.sum((eeg_fc - eeg_fc.mean()) * e)
    return float(np.angle(b * np.conj(a)))


def line_free_noise(E, rng):
    n = len(E); Fe = np.fft.rfft(E, axis=0); amp = np.abs(Fe)
    win = max(5, int(round(0.5 / (FS_TRF / n))) | 1); amp_s = median_filter(amp, size=(win, 1), mode='nearest')
    ph = rng.uniform(0, 2 * np.pi, Fe.shape[0]); ph[0] = 0
    if n % 2 == 0: ph[-1] = 0
    Es = np.fft.irfft(amp_s * np.exp(1j * ph)[:, None], n=n, axis=0)
    return Es / (Es.std(0, keepdims=True) + 1e-12) * E.std(0, keepdims=True)


def run_participant(subj, X64, F64, fbeat, fcidx, drive, rng, simulate=None):
    tidx = [int(np.argmin(np.abs(GRID - f))) for f in fbeat]
    cfg = {
        'hopf': {f"hopf|{i}": build(F64, X64, 'hopf', p) for i, p in enumerate(ob.HOPF_GRID)},
        'rf': {f"rf|{i}": build(F64, X64, 'rf', p) for i, p in enumerate(ob.RF_GRID)},
        'lin': {f"lin|{i}": build(F64, X64, 'lin', p) for i, p in enumerate(ob.LIN_GRID)},
        'd_short': {'d_short': build(F64, X64, 'd_short', None)},
        'd_long': {'d_long': build(F64, X64, 'd_long', None)},
        'aug': {f"aug|{i}": build(F64, X64, 'aug', p) for i, p in enumerate(ob.HOPF_GRID)},
        'aug_lin': {f"aug_lin|{i}": build(F64, X64, 'aug_lin', p) for i, p in enumerate(ob.LIN_GRID)},
    }
    Y = X64
    if simulate:                                                 # validation worlds
        src = 'aug' if simulate == 'hopf' else 'd_short'
        key = list(cfg[src])[1] if simulate == 'hopf' else 'd_short'
        XLs = cfg[src][key]; A, B = tempo_moments(XLs, X64, tidx); W = solve(A.sum(0), B.sum(0), 1.0)
        Y = []
        for Xl, Yr in zip(XLs, X64):
            P = Xl @ W; Y.append(P + line_free_noise(Yr - P, rng))
    out = {'N': len(Y), 'tempi': {}, 'models': {}}
    for m, configs in cfg.items():
        t0 = time.time(); res = loto(configs, Y, tidx, fcidx, configs)
        out['models'][m] = {}
        for ho, r in res.items():
            f = float(GRID[ho]); idx = sorted(r['pred'])
            pred_fc = np.concatenate([r['pred'][n][:, fcidx].mean(1) for n in idx]); eeg_fc = np.concatenate([Y[n][:, fcidx].mean(1) for n in idx])
            resid256 = [resample_poly((Y[n] - r['pred'][n])[:, fcidx].mean(1), 4, 1) for n in idx]
            out['models'][m][str(f)] = {'r_fc': r['r_fc'], 'config': r['config'], 'lam': r['lam'], 'n_trials': len(idx),
                                        'phase_lag_rad': phase_lag(pred_fc, eeg_fc, f),
                                        'resid_grid_z': [grid_stats((d - d.mean()) / (d.std() + 1e-12)).tolist() for d in resid256]}
        print(f"    {subj} {m:>8}: mean held-out r_fc {np.mean([v['r_fc'] for v in out['models'][m].values()]):+.4f}  ({time.time()-t0:.0f}s)", flush=True)
    # resonance curve: Hopf |z| per oscillator per stimulation tempo (second grid config, alpha -0.1)
    outs = model_outputs(F64, 'hopf', ob.HOPF_GRID[1]); K = len(ob.FREQS)
    curve = {}
    for t in sorted(set(tidx)):
        curve[str(float(GRID[t]))] = np.mean([outs[n][:, K:].mean(0) for n in range(len(outs)) if tidx[n] == t], axis=0).tolist()
    out['resonance_curve_hopf'] = curve; out['freqs'] = ob.FREQS.tolist()
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--data', default='/home/user/data_local/weineck2022'); ap.add_argument('--feats', required=True)
    ap.add_argument('--subjects', required=True); ap.add_argument('--out', required=True); ap.add_argument('--simulate', default=None, choices=[None, 'hopf', 'trf'])
    ap.add_argument('--seed', type=int, default=0); ap.add_argument('--min-trials', type=int, default=40)
    a = ap.parse_args()
    feats, table = load_features(a.feats); sos = butter(4, [0.5, 30.0], btype='band', fs=1000.0, output='sos'); rng = np.random.RandomState(a.seed)
    out = {'exploratory': True, 'simulate': a.simulate, 'subjects': {}}
    for s in a.subjects.split(','):
        t0 = time.time(); X64, F64, XL, fbeat, fcidx, drive, j = load_participant_arrays(a.data, s, feats, table, sos)
        if len(X64) < a.min_trials:
            print(f"subj {s}: {len(X64)} trials < {a.min_trials}, excluded"); continue
        print(f"subj {s}: {len(X64)} trials, {len(set(np.round(fbeat, 2)))} tempi present", flush=True)
        out['subjects'][s] = run_participant(s, X64, F64, fbeat, fcidx, drive, rng, a.simulate)
        out['subjects'][s]['seconds'] = time.time() - t0
        json.dump(out, open(a.out, 'w'))
        print(f"subj {s} done in {time.time()-t0:.0f}s", flush=True)


if __name__ == '__main__':
    main()
