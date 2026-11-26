"""Conventional (non-generative) edits that leave event timing untouched, and the oracle re-synthesis.

These are the timing-preserving reference points of the trade-off plane: they change the sound by a
measured amount (log-mel distance, centroid shift) without moving any event. All are causal-free
(zero-phase) so they introduce no group delay that the timing metrics would mis-read as a timing error.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import butter, sosfiltfilt

import synthetic_audio as sa


def lowpass(x, sr, fc):
    """'Warmer' / darker: 4th-order zero-phase Butterworth low-pass."""
    sos = butter(4, fc, btype='low', fs=sr, output='sos'); return sosfiltfilt(sos, x, axis=-1).astype(np.float32)


def high_shelf_cut(x, sr, fc=3000.0, gain_db=-12.0):
    """Attenuate content above fc by gain_db (zero-phase split-band implementation)."""
    sos = butter(2, fc, btype='high', fs=sr, output='sos'); hi = sosfiltfilt(sos, x, axis=-1)
    return (x + (10 ** (gain_db / 20) - 1) * hi).astype(np.float32)


def compress(x, sr, threshold_db=-20.0, ratio=4.0, smooth_ms=5.0):
    """'Softer' dynamics: feed-forward compressor on a zero-phase smoothed envelope (no look-ahead delay)."""
    m = np.abs(x).max(0); w = max(1, int(smooth_ms * 1e-3 * sr)); env = np.convolve(m, np.ones(w) / w, 'same') + 1e-9
    lvl = 20 * np.log10(env); over = np.maximum(lvl - threshold_db, 0); g = 10 ** (-over * (1 - 1 / ratio) / 20)
    y = x * g[None]; return (y / (np.abs(y).max() + 1e-9) * np.abs(x).max()).astype(np.float32)


def oracle_resynthesis(comp: 'sa.Composition', instrumentation: str, render_seed=0):
    """Same composition (identical event times) rendered with a different instrumentation: the ideal
    rhythm-preserving timbre edit, an upper reference for what an editor could achieve."""
    x, _ = sa.render(comp, render_seed=render_seed, instrumentation=instrumentation); return x


DSP_EDITS = {
    'lowpass_4k': lambda x, sr: lowpass(x, sr, 4000.0),
    'lowpass_1500': lambda x, sr: lowpass(x, sr, 1500.0),
    'lowpass_600': lambda x, sr: lowpass(x, sr, 600.0),
    'shelf_cut_12db': lambda x, sr: high_shelf_cut(x, sr, 3000.0, -12.0),
    'compress_4to1': lambda x, sr: compress(x, sr, -20.0, 4.0),
}
