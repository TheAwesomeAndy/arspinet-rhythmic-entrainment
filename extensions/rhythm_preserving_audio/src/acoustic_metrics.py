"""Acoustic-transformation metrics: did the edit change the sound, and in the intended direction?

A deliberately small set (EXPERIMENT_PLAN.md, addendum A1):
  * ltas_distance     : magnitude of change (primary since A1). Long-term average log-mel spectra
                        compared band by band (dB); blind to event timing.
  * log_mel_distance  : frame-by-frame log-mel difference (dB); secondary, because it also responds to
                        pure timing changes (a 30 ms shift reads as 8.6 dB on the controls).
  * centroid_shift    : direction of brightness change (Hz; negative = darker / "warmer").
  * rms_db_change, crest_db_change : direction of level / percussive-dynamics change ("softer").
  * chroma_corr       : tonal (pitch-class) similarity, to separate harmonic from rhythmic preservation.
Rhythm is not judged here: these say how much and which way the sound changed.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import stft

N_FFT = 2048; HOP = 512; N_MELS = 64


def _mono(x):
    x = np.asarray(x, np.float64); return x.mean(0) if x.ndim == 2 else x


def mel_fb(sr, n_fft=N_FFT, n_mels=N_MELS, fmin=30.0, fmax=None):
    fmax = fmax or sr / 2; hz = lambda m: 700 * (10 ** (m / 2595) - 1); mel = lambda f: 2595 * np.log10(1 + f / 700)
    pts = hz(np.linspace(mel(fmin), mel(fmax), n_mels + 2)); bins = np.fft.rfftfreq(n_fft, 1 / sr); fb = np.zeros((n_mels, len(bins)))
    for i in range(n_mels):
        l, c, r = pts[i:i + 3]; fb[i] = np.clip(np.minimum((bins - l) / (c - l), (r - bins) / (r - c)), 0, None)
    return fb


def power_spec(x, sr):
    _, _, Z = stft(_mono(x), fs=sr, window='hann', nperseg=N_FFT, noverlap=N_FFT - HOP, boundary='zeros', padded=True)
    return np.abs(Z) ** 2


def log_mel(x, sr):
    return 10 * np.log10(mel_fb(sr) @ power_spec(x, sr) + 1e-10)


def log_mel_distance(x_ref, x, sr, floor_db=-80.0):
    """Mean |logmel(ref) - logmel(x)| (dB) over frames of the reference duration; each spectrum is
    referenced to its own maximum and floored, so the distance measures spectral shape, not loudness."""
    A = log_mel(x_ref, sr); B = log_mel(x, sr); n = min(A.shape[1], B.shape[1])
    A = np.maximum(A[:, :n] - A.max(), floor_db); B = np.maximum(B[:, :n] - B.max(), floor_db)
    return float(np.mean(np.abs(A - B)))


def ltas_log_mel_distance(x_ref, x, sr, floor_db=-80.0):
    """Timing-invariant change of spectral shape (primary transformation measure, addendum A1): mean over
    bands of |LTAS(ref) - LTAS(x)| (dB), where LTAS is the long-term average log-mel spectrum (mel power
    averaged over all frames, then dB, referenced to its own maximum and floored). Moving events in time
    leaves it unchanged; changing timbre, brightness or instrumentation moves it."""
    a = mel_fb(sr) @ power_spec(x_ref, sr).mean(1); b = mel_fb(sr) @ power_spec(x, sr).mean(1)
    A = np.maximum(10 * np.log10(a + 1e-12) - 10 * np.log10(a.max() + 1e-12), floor_db); B = np.maximum(10 * np.log10(b + 1e-12) - 10 * np.log10(b.max() + 1e-12), floor_db)
    return float(np.mean(np.abs(A - B)))


def spectral_centroid(x, sr):
    P = power_spec(x, sr); f = np.fft.rfftfreq(N_FFT, 1 / sr); w = P.sum(0)
    c = (f[:, None] * P).sum(0) / (w + 1e-20); return float(np.sum(c * w) / (w.sum() + 1e-20))   # power-weighted mean


def rms_db(x):
    x = _mono(x); return float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12))


def crest_db(x):
    x = _mono(x); return float(20 * np.log10(np.max(np.abs(x)) / (np.sqrt(np.mean(x ** 2)) + 1e-12) + 1e-12))


def chroma(x, sr, fmin=55.0, fmax=2000.0):
    P = power_spec(x, sr); f = np.fft.rfftfreq(N_FFT, 1 / sr); ok = (f >= fmin) & (f <= fmax)
    pc = np.round(12 * np.log2(f[ok] / 440.0)).astype(int) % 12; C = np.zeros((12, P.shape[1]))
    for k in range(12): C[k] = P[ok][pc == k].sum(0)
    return C.sum(1) / (C.sum() + 1e-20)


def chroma_corr(x_ref, x, sr):
    return float(np.corrcoef(chroma(x_ref, sr), chroma(x, sr))[0, 1])


def acoustic_report(x_ref, x, sr):
    return {'ltas_distance_db': ltas_log_mel_distance(x_ref, x, sr), 'log_mel_distance_db': log_mel_distance(x_ref, x, sr), 'centroid_shift_hz': spectral_centroid(x, sr) - spectral_centroid(x_ref, sr),
            'rms_db_change': rms_db(x) - rms_db(x_ref), 'crest_db_change': crest_db(x) - crest_db(x_ref), 'chroma_corr': chroma_corr(x_ref, x, sr)}
