"""Stimulus-driven oscillator banks for Theory 3 (exploratory; see docs/OSCILLATOR_DECISION_RULE.md).

All banks share a fixed log-spaced natural-frequency grid (default 30 oscillators, 0.5-8 Hz)
and are driven by the same stimulus features (spectral flux and beat onsets, z-scored, at
`fs_in`); integration runs at `fs_int` (default 256 Hz, features upsampled by zero-order
hold) and outputs are returned at `fs_out` (default 64 Hz, the encoding-model rate).

a) hopf_bank: Stuart-Landau / canonical Hopf normal form (neural-resonance form, Large & Snyder 2009):
       dz/dt = (alpha + i*omega) z + beta |z|^2 z + gain * u(t)
   with beta = -1 (supercritical stabilising term). alpha < 0: damped resonator that needs
   input; alpha > 0: self-sustained limit cycle entrained by input. Outputs Re(z) and |z|.
b) rf_bank: resonate-and-fire units (Izhikevich 2001):
       dz/dt = (b + i*omega) z + gain * u(t),  spike when Im(z) >= theta, then z <- z_reset
   (b < 0 damping). Output: spike train smoothed with a 50 ms Gaussian -> rate.
c) linear_bank: damped linear oscillator (LTI), dz/dt = (alpha_lin + i*omega) z + gain*u with
   alpha_lin < 0, same grid; outputs Re(z) and Im(z) (both linear in u). This is the control
   that tells whether a gain over the TRF needs nonlinearity.

Numerical scheme: exponential (exact) integration of the linear part per step, Euler on the
nonlinear and input terms; dt = 1/fs_int.
"""
import numpy as np
from scipy.signal import resample_poly
from scipy.ndimage import gaussian_filter1d

FREQS = np.geomspace(0.5, 8.0, 30)


def _upsample(u, fs_in, fs_int):
    r = int(round(fs_int / fs_in))
    return np.repeat(u, r, axis=0)


def _downsample(y, fs_int, fs_out):
    r = int(round(fs_int / fs_out))
    return resample_poly(y, 1, r, axis=0)


def hopf_bank(u, fs_in=64.0, alpha=-0.5, gain=1.0, beta=-1.0, freqs=FREQS, fs_int=256.0, fs_out=64.0):
    """u: (T, n_feat) drive; returns (T_out, 2*len(freqs)) = [Re z..., |z|...]."""
    U = _upsample(np.asarray(u, float), fs_in, fs_int); drive = U.sum(1) if U.ndim == 2 else U
    dt = 1.0 / fs_int; omega = 2 * np.pi * np.asarray(freqs); n = len(drive); K = len(freqs)
    z = np.zeros(K, complex); out = np.empty((n, 2 * K))
    lin = np.exp((alpha + 1j * omega) * dt)
    for t in range(n):
        z = lin * z + dt * (beta * np.abs(z) ** 2 * z + gain * drive[t])
        out[t, :K] = z.real; out[t, K:] = np.abs(z)
    return _downsample(out, fs_int, fs_out)


def rf_bank(u, fs_in=64.0, b=-1.0, gain=1.0, theta=1.0, z_reset=0.0 + 0.0j, freqs=FREQS, fs_int=256.0, fs_out=64.0, smooth_s=0.05):
    """Resonate-and-fire bank; returns (T_out, len(freqs)) smoothed spike rates (spikes/s)."""
    U = _upsample(np.asarray(u, float), fs_in, fs_int); drive = U.sum(1) if U.ndim == 2 else U
    dt = 1.0 / fs_int; omega = 2 * np.pi * np.asarray(freqs); n = len(drive); K = len(freqs)
    z = np.zeros(K, complex); spikes = np.zeros((n, K)); lin = np.exp((b + 1j * omega) * dt)
    for t in range(n):
        z = lin * z + dt * gain * drive[t]
        s = z.imag >= theta
        if s.any():
            spikes[t, s] = 1.0; z[s] = z_reset
    rate = gaussian_filter1d(spikes, sigma=smooth_s * fs_int, axis=0) * fs_int
    return _downsample(rate, fs_int, fs_out)


def linear_bank(u, fs_in=64.0, alpha_lin=-0.5, gain=1.0, freqs=FREQS, fs_int=256.0, fs_out=64.0):
    """Linear damped oscillator bank (LTI); returns (T_out, 2*len(freqs)) = [Re z..., Im z...]."""
    U = _upsample(np.asarray(u, float), fs_in, fs_int); drive = U.sum(1) if U.ndim == 2 else U
    dt = 1.0 / fs_int; omega = 2 * np.pi * np.asarray(freqs); n = len(drive); K = len(freqs)
    z = np.zeros(K, complex); out = np.empty((n, 2 * K)); lin = np.exp((alpha_lin + 1j * omega) * dt)
    for t in range(n):
        z = lin * z + dt * gain * drive[t]
        out[t, :K] = z.real; out[t, K:] = z.imag
    return _downsample(out, fs_int, fs_out)


# parameter grids searched ONLY on training tempi (inner CV); frequency grid is fixed
HOPF_GRID = [dict(alpha=-0.5, gain=1.0), dict(alpha=-0.1, gain=1.0), dict(alpha=0.2, gain=1.0), dict(alpha=-0.1, gain=3.0)]
RF_GRID = [dict(b=-1.0, gain=1.0, theta=1.0), dict(b=-0.3, gain=1.0, theta=1.0), dict(b=-1.0, gain=3.0, theta=1.0), dict(b=-0.3, gain=3.0, theta=0.5)]
LIN_GRID = [dict(alpha_lin=-0.5, gain=1.0), dict(alpha_lin=-0.1, gain=1.0), dict(alpha_lin=-2.0, gain=1.0)]
