#!/usr/bin/env python3
"""Synthetic calibration of beat-locking detectors, including the fixed LIF reservoir.

Drives (all at 256 Hz, z-scored, 60 s unless stated), pink-noise background at a
given SNR (amplitude ratio signal/noise), tempo f in a grid:
  'sine'    : beat-locked sinusoid at f (plus weaker 2f harmonic)
  'evoked'  : evoked kernel (biphasic, ~100 ms latency, ~300 ms duration) convolved
              with a beat impulse train at f  (Damsma-2025-style evoked model)
  'osc'     : Wilson-Cowan-like limit-cycle oscillator phase-locked to the beat
              train with coupling k (constant phase, not constant latency)
Detectors, each returning a z-score at (1,2,4) x f with the neighbour-frequency
null (Welch, 20 s segments, 0.08-0.5 Hz neighbours excluding harmonics):
  L   : linear tagging of the drive
  N2a : tagging of the Hilbert envelope of the band-passed (0.5-8 Hz) drive
  N2b : tagging of the squared drive
  R   : fixed LIF reservoir (experiment_zero), per-unit tagging -> fraction of
        units with z>1.96 and unit-PC1 z; also population-rate z
  Rs  : same reservoir with shuffled recurrent weights (same spectral radius)
Also measured for R: per-tempo gain (unit-PC1 tagging amplitude / drive tagging
amplitude) and group delay (cross-correlation lag between the beat-locked
component of the drive and the unit-PC1 of the reservoir), for the 'sine' drive
at high SNR.
Outputs: JSON with detection probability (z>1.96 at the beat or 2f) over
n_rep repetitions per (drive, tempo, SNR), and the gain/delay table.
"""
import argparse, json, os, sys, time
import numpy as np
from scipy.signal import welch, butter, sosfiltfilt, hilbert, fftconvolve

FS = 256.0
sys.path.insert(0, '/home/user/dissoAdventureExperiments/chapter5Experiments')
from experiment_zero import LIFReservoir  # noqa: E402


def pink(n, rng):
    X = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / FS); f[0] = f[1]
    x = np.fft.irfft(X / np.sqrt(f), n=n); return (x - x.mean()) / x.std()


def beat_train(n, f, rng, jitter_s=0.0):
    t = np.arange(n) / FS; period = 1 / f
    times = np.arange(0.2, n / FS, period) + rng.normal(0, jitter_s, int(np.ceil(n / FS / period)) + 1)[:len(np.arange(0.2, n / FS, period))]
    s = np.zeros(n); idx = np.round(times * FS).astype(int); idx = idx[(idx >= 0) & (idx < n)]; s[idx] = 1.0
    return s


def evoked_kernel(lat=0.10, width=0.08):
    t = np.arange(0, 0.6, 1 / FS)
    k = np.exp(-((t - lat) / width) ** 2) - 0.6 * np.exp(-((t - lat - 0.12) / (1.5 * width)) ** 2)
    return k / np.abs(k).max()


def make_drive(kind, f, snr, n, rng, k_osc=0.8):
    noise = pink(n, rng)
    if kind == 'sine':
        t = np.arange(n) / FS; sig = np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t + 0.7)
    elif kind == 'evoked':
        sig = fftconvolve(beat_train(n, f, rng), evoked_kernel(), mode='full')[:n]
    elif kind == 'osc':
        # Stuart-Landau-type oscillator with natural frequency f0 = f*(1+0.08), forced by the beat train
        dt = 1 / FS; z = 0.1 + 0j; w0 = 2 * np.pi * f * 1.08; drive = beat_train(n, f, rng)
        out = np.empty(n)
        for i in range(n):
            z = z + dt * ((1 - abs(z) ** 2) * z + 1j * w0 * z) + k_osc * drive[i]
            out[i] = z.real
        sig = out
    else:
        raise ValueError(kind)
    sig = (sig - sig.mean()) / (sig.std() + 1e-12)
    x = snr * sig + noise
    return (x - x.mean()) / x.std(), sig


def tag_z(x, f_beat, ks=(1, 2, 4), seg_s=20):
    nper = int(FS * seg_s)
    fr, p = welch(x - x.mean(), fs=FS, nperseg=nper, noverlap=nper // 2, window='hann')
    zs = []
    for k in ks:
        f0 = k * f_beat; i = np.argmin(np.abs(fr - f0))
        nb = (np.abs(fr - f0) > 0.08) & (np.abs(fr - f0) < 0.5)
        for kk in ks:
            nb &= np.abs(fr - kk * f_beat) > 0.08
        zs.append(float((p[i] - p[nb].mean()) / (p[nb].std() + 1e-15)))
    return np.array(zs)


def bandpass(x, lo=0.5, hi=8.0):
    sos = butter(4, [lo, hi], btype='band', fs=FS, output='sos'); return sosfiltfilt(sos, x)


def shuffled_reservoir(seed):
    r = LIFReservoir(seed=seed); rng = np.random.RandomState(seed + 1000)
    W = r.W_rec.copy().ravel(); rng.shuffle(W); W = W.reshape(r.W_rec.shape)
    eig = np.abs(np.linalg.eigvals(W)).max(); r.W_rec = W * (0.9 / eig); return r


def reservoir_readouts(res, x, f):
    S = res.forward(x)
    zu = np.array([tag_z(S[:, j], f) for j in range(S.shape[1])])
    frac = (zu > 1.96).mean(0)
    U, s, Vt = np.linalg.svd(S - S.mean(0), full_matrices=False); pc1 = U[:, 0] * s[0]
    return {'frac_units': frac, 'unit_pc1_z': tag_z(pc1, f), 'pop_z': tag_z(S.mean(1), f), 'rate': float(S.mean())}, pc1


def run(args):
    rng = np.random.RandomState(args.seed)
    res = LIFReservoir(seed=42); res_s = shuffled_reservoir(42)
    n = int(args.seconds * FS)
    tempi = [float(t) for t in args.tempi.split(',')]; snrs = [float(s) for s in args.snrs.split(',')]
    results = []
    t0 = time.time()
    for kind in args.drives.split(','):
        for f in tempi:
            for snr in snrs:
                for rep in range(args.n_rep):
                    x, sig = make_drive(kind, f, snr, n, rng)
                    row = {'drive': kind, 'f': f, 'snr': snr, 'rep': rep}
                    row['L'] = tag_z(x, f).tolist()
                    row['N2a'] = tag_z(np.abs(hilbert(bandpass(x))), f).tolist()
                    row['N2b'] = tag_z(x ** 2, f).tolist()
                    r, pc1 = reservoir_readouts(res, x, f)
                    row['R_frac'] = r['frac_units'].tolist(); row['R_pc1'] = r['unit_pc1_z'].tolist(); row['R_pop'] = r['pop_z'].tolist(); row['R_rate'] = r['rate']
                    rs, _ = reservoir_readouts(res_s, x, f)
                    row['Rs_frac'] = rs['frac_units'].tolist(); row['Rs_pc1'] = rs['unit_pc1_z'].tolist()
                    results.append(row)
                print(f"{kind:>7} f={f:.2f} snr={snr:.2f}: L z1={np.mean([r['L'][0] for r in results[-args.n_rep:]]):6.1f} | N2a {np.mean([r['N2a'][0] for r in results[-args.n_rep:]]):6.1f} | R pc1 {np.mean([r['R_pc1'][0] for r in results[-args.n_rep:]]):6.1f} frac {np.mean([r['R_frac'][0] for r in results[-args.n_rep:]]):.2f} pop {np.mean([r['R_pop'][0] for r in results[-args.n_rep:]]):5.1f} | Rs pc1 {np.mean([r['Rs_pc1'][0] for r in results[-args.n_rep:]]):6.1f}  ({time.time()-t0:.0f}s)", flush=True)

    # gain and group delay of the reservoir at high SNR, 'sine' drive
    gain = []
    for f in tempi:
        x, sig = make_drive('sine', f, 3.0, n, rng)
        r, pc1 = reservoir_readouts(res, x, f)
        # amplitude at f via projection
        t = np.arange(n) / FS; e = np.exp(-2j * np.pi * f * t)
        ax = np.abs(np.mean((x - x.mean()) * e)); ap = np.abs(np.mean((pc1 - pc1.mean()) * e))
        ph = np.angle(np.mean((pc1 - pc1.mean()) * e)) - np.angle(np.mean((x - x.mean()) * e))
        delay_ms = -np.angle(np.exp(1j * ph)) / (2 * np.pi * f) * 1000
        gain.append({'f': f, 'gain_pc1_over_drive': float(ap / ax), 'delay_ms_pc1_vs_drive': float(delay_ms), 'rate': r['rate']})
        print(f"gain/delay f={f:.2f}: gain {ap/ax:.3f}, delay {delay_ms:+.0f} ms (sign ambiguous for PC1), rate {r['rate']:.3f}")
    out = {'fs': FS, 'seconds': args.seconds, 'n_rep': args.n_rep, 'results': results, 'gain_delay': gain}
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    json.dump(out, open(args.out, 'w'))
    # summary: detection probability at z>1.96 on the beat (k=1) or 2f (k=2)
    print("\nDetection probability P(max z over k in {1,2} > 1.96):")
    print(f"{'drive':>7} {'f':>5} {'snr':>5} | {'L':>5} {'N2a':>5} {'N2b':>5} {'R_pc1':>5} {'R_pop':>5} {'Rs_pc1':>6}")
    for kind in args.drives.split(','):
        for f in tempi:
            for snr in snrs:
                rows = [r for r in results if r['drive'] == kind and r['f'] == f and r['snr'] == snr]
                def det(key): return np.mean([max(r[key][0], r[key][1]) > 1.96 for r in rows])
                print(f"{kind:>7} {f:5.2f} {snr:5.2f} | {det('L'):5.2f} {det('N2a'):5.2f} {det('N2b'):5.2f} {det('R_pc1'):5.2f} {det('R_pop'):5.2f} {det('Rs_pc1'):6.2f}")


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--drives', default='sine,evoked,osc'); ap.add_argument('--tempi', default='1.0,1.5,2.0,2.5,3.0,4.0')
    ap.add_argument('--snrs', default='0.05,0.1,0.2,0.4'); ap.add_argument('--n-rep', type=int, default=4)
    ap.add_argument('--seconds', type=float, default=60); ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--out', default='/home/user/arspinet-rhythmic-entrainment/calibration/results/synthetic_calibration.json')
    run(ap.parse_args())
