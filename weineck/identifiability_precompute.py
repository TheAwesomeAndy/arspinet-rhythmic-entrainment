#!/usr/bin/env python3
"""Identifiability map, stage 1: sufficient statistics (docs/IDENTIFIABILITY_PLAN.md).

Part A (--part stimuli): for a pool of real stimulus-feature vectors (up to 30 per tempo, all four
subgroups), build the regressor matrices of the four compared models with the committed
configurations and store, per stimulus, in float32 memmaps:
    A_a  = Xa'Xa   (885x885)  Xa  = [Hopf-bank lags (780) | 4-feature TRF 0-400 ms with bias (105)]
    A_al = Xal'Xal (885x885)  Xal = [linear-bank lags (780) | same TRF block (105)]
    A_l  = Xl'Xl   (261x261)  Xl  = 4-feature TRF 0-1000 ms with bias
    C_la = Xl'Xa   (261x885),  C_alh = Xlin'Xh (780x780)
    noise bank: Xm' n_k for K unit-variance noise realisations per stimulus (pooled 1/f-like
    spectrum, no spectral lines), plus sum(n_k), sum(n_k^2), and T.
Bias columns are last, so column sums and T are read off A directly. Hopf/linear outputs are
standardised over the whole pool (a stimulus-only, label-free scaling).

Part B (--part kernels): for each of the 34 real participants, fit on all one-to-one trials, target =
fronto-central channel mean of the z-scored 32-channel EEG at 64 Hz:
    W_trf (105; lambda 1.0)   evoked kernel          W_osc (781; lambda 10.0)  Hopf-only kernel
and record the pooled residual spectrum shape used for the noise bank.
"""
import argparse, json, os, sys, time
import numpy as np
from scipy.signal import butter, resample_poly, welch
from scipy.ndimage import median_filter
from weineck_loader import load_features, TEMPI
from underfit_check import load_participant_arrays, solve, SUBJECTS_ALL
from oscillator_heldout import lagmat, LAG_OSC, LAG_SHORT, LAG_LONG
import oscillator_bank as ob

FS = 64.0; OUT = '/home/user/arspinet-rhythmic-entrainment/weineck/results/identifiability'
HOPF = ob.HOPF_GRID[0]; LIN = ob.LIN_GRID[2]; LAM_TRF = 1.0; LAM_OSC = 10.0; K_NOISE = 6; PER_TEMPO = 30


def feat64(feats, i, j, k):
    F = np.stack([feats[f][i][j][k] for f in ('stim_spec_z', 'stim_beat_z', 'stim_env_z', 'stim_der_z')]); return resample_poly(F, 1, 2, axis=1).T


def pool_list(table):
    by_t = {}
    for (i, j, k, L) in table:
        by_t.setdefault(i, []).append((i, j, k))
    rng = np.random.RandomState(0); pool = []
    for i in sorted(by_t):
        lst = by_t[i]; idx = rng.permutation(len(lst))[:PER_TEMPO]; pool += [lst[q] for q in sorted(idx)]
    return pool


def bank_outputs(F64_list):
    H = [ob.hopf_bank(F[:, :2], **HOPF) for F in F64_list]; L = [ob.linear_bank(F[:, :2], **LIN) for F in F64_list]
    return H, L


def noise_shape(resid_list):
    """pooled smoothed amplitude spectrum shape on a 0-32 Hz grid (relative), from residual trials."""
    fr = None; acc = []
    for r in resid_list:
        f, p = welch(r, fs=FS, nperseg=512, noverlap=256); acc.append(np.log(p + 1e-30)); fr = f
    m = np.exp(np.mean(acc, 0)); m = median_filter(m, size=9, mode='nearest'); return fr, np.sqrt(m / m.mean())


def make_noise(T, fr, shape, rng):
    f = np.fft.rfftfreq(T, 1 / FS); amp = np.interp(f, fr, shape); ph = rng.uniform(0, 2 * np.pi, len(f)); ph[0] = 0
    if T % 2 == 0: ph[-1] = 0
    n = np.fft.irfft(amp * np.exp(1j * ph), n=T); return (n - n.mean()) / (n.std() + 1e-12)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--feats', required=True); ap.add_argument('--part', required=True, choices=['stimuli', 'kernels'])
    ap.add_argument('--subjects', default=','.join(SUBJECTS_ALL)); ap.add_argument('--data', default='/home/user/data_local/weineck2022'); a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True); feats, table = load_features(a.feats); pool = pool_list(table)
    F64 = [feat64(feats, i, j, k) for (i, j, k) in pool]
    t0 = time.time(); H, L = bank_outputs(F64)
    Hc = np.concatenate(H); Lc = np.concatenate(L); hmu, hsd = Hc.mean(0), Hc.std(0) + 1e-9; lmu, lsd = Lc.mean(0), Lc.std(0) + 1e-9
    np.savez(f'{OUT}/standardisation.npz', hmu=hmu, hsd=hsd, lmu=lmu, lsd=lsd)
    print(f"pool: {len(pool)} stimuli over {len(set(p[0] for p in pool))} tempi; bank outputs in {time.time()-t0:.0f}s", flush=True)
    if a.part == 'stimuli':
        # noise spectrum shape: use the pooled residual shape saved by the kernels part if present, else 1/f
        if os.path.exists(f'{OUT}/noise_shape.npz'):
            z = np.load(f'{OUT}/noise_shape.npz'); fr, shape = z['fr'], z['shape']
        else:
            fr = np.linspace(0, 32, 257); shape = 1 / np.sqrt(np.maximum(fr, 0.25)); shape /= shape.mean(); print("WARNING: using 1/f noise shape (kernels part not run yet)")
        n = len(pool); A_a = np.lib.format.open_memmap(f'{OUT}/A_a.npy', 'w+', np.float32, (n, 885, 885)); A_al = np.lib.format.open_memmap(f'{OUT}/A_al.npy', 'w+', np.float32, (n, 885, 885))
        A_l = np.lib.format.open_memmap(f'{OUT}/A_l.npy', 'w+', np.float32, (n, 261, 261)); C_la = np.lib.format.open_memmap(f'{OUT}/C_la.npy', 'w+', np.float32, (n, 261, 885)); C_alh = np.lib.format.open_memmap(f'{OUT}/C_alh.npy', 'w+', np.float32, (n, 780, 780))
        Bn_a = np.zeros((n, K_NOISE, 885), np.float32); Bn_al = np.zeros((n, K_NOISE, 885), np.float32); Bn_l = np.zeros((n, K_NOISE, 261), np.float32); nsum = np.zeros((n, K_NOISE)); nsq = np.zeros((n, K_NOISE)); Tn = np.zeros(n, int); tempo = np.zeros(n)
        rng = np.random.RandomState(123)
        for q, ((i, j, k), F) in enumerate(zip(pool, F64)):
            Xs = lagmat(F, LAG_SHORT); Xl = lagmat(F, LAG_LONG); Xh = lagmat((H[q] - hmu) / hsd, LAG_OSC)[:, :-1]; Xlin = lagmat((L[q] - lmu) / lsd, LAG_OSC)[:, :-1]
            Xa = np.hstack([Xh, Xs]); Xal = np.hstack([Xlin, Xs]); T = len(F)
            A_a[q] = Xa.T @ Xa; A_al[q] = Xal.T @ Xal; A_l[q] = Xl.T @ Xl; C_la[q] = Xl.T @ Xa; C_alh[q] = Xlin.T @ Xh
            for kk in range(K_NOISE):
                nz = make_noise(T, fr, shape, rng); Bn_a[q, kk] = Xa.T @ nz; Bn_al[q, kk] = Xal.T @ nz; Bn_l[q, kk] = Xl.T @ nz; nsum[q, kk] = nz.sum(); nsq[q, kk] = (nz ** 2).sum()
            Tn[q] = T; tempo[q] = TEMPI[i]
            if q % 50 == 0: print(f"  stimulus {q}/{n} ({time.time()-t0:.0f}s)", flush=True)
        for M in (A_a, A_al, A_l, C_la, C_alh): M.flush()
        np.savez(f'{OUT}/stimuli_meta.npz', Bn_a=Bn_a, Bn_al=Bn_al, Bn_l=Bn_l, nsum=nsum, nsq=nsq, T=Tn, tempo=tempo, pool=np.array(pool))
        print(f"stimuli part done in {time.time()-t0:.0f}s", flush=True)
    else:
        sos = butter(4, [0.5, 30.0], btype='band', fs=1000.0, output='sos'); kern = {}; resid_all = []
        for s in a.subjects.split(','):
            X64, F64p, _, fbeat, fcidx, _, j = load_participant_arrays(a.data, s, feats, table, sos)
            Hp, Lp = bank_outputs(F64p)
            Xs = [lagmat(F, LAG_SHORT) for F in F64p]; Xh = [np.hstack([lagmat((h - hmu) / hsd, LAG_OSC)[:, :-1], np.ones((len(h), 1))]) for h in Hp]
            y = [X[:, fcidx].mean(1) for X in X64]
            A = sum(x.T @ x for x in Xs); B = sum(x.T @ yy for x, yy in zip(Xs, y)); W_trf = solve(A, B, LAM_TRF)
            A2 = sum(x.T @ x for x in Xh); B2 = sum(x.T @ yy for x, yy in zip(Xh, y)); W_osc = solve(A2, B2, LAM_OSC)
            Pe = [x @ W_trf for x in Xs]; Po = [x @ W_osc for x in Xh]; res = [yy - pe for yy, pe in zip(y, Pe)]
            kern[s] = {'W_trf': W_trf.tolist(), 'W_osc': W_osc.tolist(), 'sd_e': float(np.concatenate(Pe).std()), 'sd_o': float(np.concatenate(Po).std()), 'sd_y': float(np.concatenate(y).std()), 'sd_res': float(np.concatenate(res).std()), 'N': len(y)}
            resid_all += res[:20]
            print(f"  kernels {s}: sd_e {kern[s]['sd_e']:.3f} sd_o {kern[s]['sd_o']:.3f} sd_res {kern[s]['sd_res']:.3f} ({time.time()-t0:.0f}s)", flush=True)
        json.dump(kern, open(f'{OUT}/kernels_{a.subjects.replace(",", "_")[:40]}.json', 'w'))
        fr, shape = noise_shape(resid_all); np.savez(f'{OUT}/noise_shape_{a.subjects.split(",")[0]}.npz', fr=fr, shape=shape)
        print(f"kernels part done in {time.time()-t0:.0f}s", flush=True)


if __name__ == '__main__':
    main()
