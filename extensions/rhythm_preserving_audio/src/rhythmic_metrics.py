"""Rhythmic-preservation metrics on audio (numpy / scipy only).

Every estimate below is computed from the audio itself (spectral-flux novelty -> onsets, tempo, beats);
the synthesis ground truth is only ever the *reference* the estimates are scored against.

Two independent routes to rhythm are scored, so the conclusion never rests on one beat tracker:
  * onset route  : spectral-flux onset detection, scored against the ground-truth onsets (no tracker);
  * beat route   : autocorrelation tempo + dynamic-programming beat tracker (Ellis 2007 style),
                   scored against the ground-truth beat grid.
Beat-band harmonic power reuses the EEG study's statistic weineck/tagging.tag_z (read-only import),
applied to the novelty envelope with a cycle-scaled baseline window (see beat_band_z).

Pre-specified tolerances (EXPERIMENT_PLAN.md): beats +-70 ms (MIREX convention), onsets +-50 ms.
"""
from __future__ import annotations

import os
import sys

import numpy as np
from scipy.signal import stft, find_peaks, correlate

FRAME_RATE = 100.0          # novelty envelope rate (Hz): hop 10 ms
BEAT_TOL_S = 0.070
ONSET_TOL_S = 0.050

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))


def _tag_z():
    """Read-only import of the EEG study's tagging statistic."""
    p = os.path.join(_REPO, 'weineck')
    if p not in sys.path: sys.path.insert(0, p)
    from tagging import tag_z
    return tag_z


def to_mono(x):
    x = np.asarray(x, np.float64)
    return x.mean(0) if x.ndim == 2 else x


def novelty(x, sr, frame_rate=FRAME_RATE, n_fft=2048, gamma=100.0):
    """Spectral-flux novelty: log-compressed magnitude STFT, half-wave rectified frame difference summed
    over bins, local-mean subtracted, half-wave rectified again. Returns (envelope, frame_rate).
    Frame k is centred at time k / frame_rate."""
    x = to_mono(x); hop = int(round(sr / frame_rate))
    _, _, Z = stft(x, fs=sr, window='hann', nperseg=n_fft, noverlap=n_fft - hop, boundary='zeros', padded=True)
    S = np.log1p(gamma * np.abs(Z))
    d = np.diff(S, axis=1, prepend=S[:, :1]); d[d < 0] = 0
    nov = d.sum(0)
    w = int(0.1 * frame_rate) | 1; loc = np.convolve(nov, np.ones(w) / w, 'same')
    nov = np.maximum(nov - loc, 0)
    return nov / (nov.max() + 1e-12), frame_rate


def detect_onsets(x, sr, delta=0.07, min_gap_s=0.045):
    """Peak picking on the novelty: local maximum, above an adaptive threshold (local median + delta),
    at least min_gap_s apart. Returns onset times (s)."""
    nov, fr = novelty(x, sr)
    w = int(0.25 * fr) | 1; med = np.array([np.median(nov[max(0, i - w // 2): i + w // 2 + 1]) for i in range(len(nov))])
    pk, _ = find_peaks(nov, height=med + delta, distance=max(1, int(min_gap_s * fr)))
    return pk / fr


def estimate_tempo(nov, fr, bpm_range=(40.0, 300.0), prior_bpm=120.0, prior_octaves=1.5):
    """Tempo (Hz) from a comb-filtered autocorrelation of the novelty: lag L scores
    ac(L) + ac(2L)/2 + ac(4L)/4 (rewarding periods whose multiples also recur, the metrical hierarchy of
    a beat), times a broad log-Gaussian prior (prior_octaves wide) centred at prior_bpm. Independent of the
    ground truth; octave errors remain possible and are measured, not hidden (tempo_error)."""
    n = nov - nov.mean(); ac = correlate(n, n, 'full')[len(n) - 1:]; ac /= ac[0] + 1e-12; ac = np.maximum(ac, 0)
    L = np.arange(len(ac)); ok = (L >= fr * 60 / bpm_range[1]) & (L <= fr * 60 / bpm_range[0]) & (4 * L < len(ac))
    comb = ac[L[ok]] + ac[2 * L[ok]] / 2 + ac[4 * L[ok]] / 4
    bpm = 60 * fr / L[ok]; prior = np.exp(-0.5 * (np.log2(bpm / prior_bpm) / prior_octaves) ** 2)
    i = np.argmax(comb * prior)
    # parabolic refinement of the lag
    j = np.where(ok)[0][i]
    if 0 < j < len(ac) - 1:
        y0, y1, y2 = ac[j - 1], ac[j], ac[j + 1]; den = y0 - 2 * y1 + y2
        lag = j + (0.5 * (y0 - y2) / den if den != 0 else 0.0)
    else:
        lag = j
    return float(fr / lag)


def track_beats(x, sr, tempo_hz=None, tightness=100.0):
    """Dynamic-programming beat tracker: maximise sum of novelty at beats minus a log-interval penalty
    around the estimated period. Returns (beat times s, tempo Hz used)."""
    nov, fr = novelty(x, sr); f = tempo_hz or estimate_tempo(nov, fr); period = fr / f
    score = nov.copy(); back = -np.ones(len(nov), int)
    lo, hi = int(round(0.5 * period)), int(round(2.0 * period))
    for t in range(len(nov)):
        if t < lo: continue
        prev = np.arange(max(0, t - hi), t - lo + 1)
        if len(prev) == 0: continue
        pen = -tightness * np.log((t - prev) / period) ** 2
        j = np.argmax(score[prev] + pen); score[t] = nov[t] + score[prev][j] + pen[j]; back[t] = prev[j]
    # start from the best-scoring frame in the last period
    t = len(nov) - 1 - int(np.argmax(score[::-1][:max(1, int(period))])); beats = []
    while t >= 0:
        beats.append(t); t = back[t]
    return np.array(beats[::-1]) / fr, f


def match(est, ref, tol):
    """Greedy one-to-one matching of estimated to reference events within tol (closest pairs first).
    Returns list of (i_est, i_ref, est - ref)."""
    est = np.asarray(est, float); ref = np.asarray(ref, float)
    if len(est) == 0 or len(ref) == 0: return []
    D = np.abs(est[:, None] - ref[None, :]); pairs = []
    cand = np.argwhere(D <= tol); order = np.argsort(D[cand[:, 0], cand[:, 1]]); ue, ur = set(), set()
    for k in order:
        i, j = cand[k]
        if i in ue or j in ur: continue
        ue.add(i); ur.add(j); pairs.append((int(i), int(j), float(est[i] - ref[j])))
    return pairs


def prf(est, ref, tol):
    m = match(est, ref, tol); tp = len(m)
    p = tp / len(est) if len(est) else 0.0; r = tp / len(ref) if len(ref) else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    dev = float(np.mean(np.abs([d for *_, d in m]))) if m else float('nan')
    return {'precision': p, 'recall': r, 'f1': f, 'n_est': int(len(est)), 'n_ref': int(len(ref)), 'mean_abs_dev_s': dev}


def metrical_levels(beats_ref):
    """Reference beat sequences at the annotated level and at half and double rate (both phases of the
    half-rate sequence): the AMLt-style allowance for tracking the right timing at the wrong metrical level."""
    b = np.asarray(beats_ref, float); mid = (b[:-1] + b[1:]) / 2
    return {'x1': b, 'x2': np.sort(np.concatenate([b, mid])), 'x0.5a': b[0::2], 'x0.5b': b[1::2]}


def beat_scores(beats_est, beats_ref, tol=BEAT_TOL_S):
    """Beat F1 at the annotated level, and the best F1 over metrical levels (with that level's timing)."""
    at = prf(beats_est, beats_ref, tol); lv = {k: prf(beats_est, v, tol) for k, v in metrical_levels(beats_ref).items()}
    best = max(lv, key=lambda k: lv[k]['f1'])
    return {'annotated': at, 'any_level': {**lv[best], 'level': best}}


def align_ordered(est, ref, tol):
    """Order-preserving (monotone) alignment of two event sequences by dynamic programming
    (Needleman-Wunsch): matching est[i] to ref[j] costs |est[i] - ref[j]| if within tol (else forbidden),
    skipping an event costs tol. Unlike greedy matching, no two matches may cross. Returns the list of
    (i_est, i_ref, est - ref)."""
    est = np.asarray(est, float); ref = np.asarray(ref, float); n, m = len(est), len(ref)
    if n == 0 or m == 0: return []
    C = np.full((n + 1, m + 1), np.inf); C[0, :] = tol * np.arange(m + 1); C[:, 0] = tol * np.arange(n + 1); B = np.zeros((n + 1, m + 1), int)
    for i in range(1, n + 1):
        d = np.abs(est[i - 1] - ref)
        for j in range(1, m + 1):
            best, arg = C[i - 1, j] + tol, 1
            if C[i, j - 1] + tol < best: best, arg = C[i, j - 1] + tol, 2
            if d[j - 1] <= tol and C[i - 1, j - 1] + d[j - 1] < best: best, arg = C[i - 1, j - 1] + d[j - 1], 0
            C[i, j], B[i, j] = best, arg
    i, j, pairs = n, m, []
    while i > 0 and j > 0:
        if B[i, j] == 0: pairs.append((i - 1, j - 1, float(est[i - 1] - ref[j - 1]))); i -= 1; j -= 1
        elif B[i, j] == 1: i -= 1
        else: j -= 1
    while i > 0 or j > 0:
        if i > 0: i -= 1
        else: j -= 1
    return pairs[::-1]


def prf_pairs(pairs, n_est, n_ref):
    tp = len(pairs); p = tp / n_est if n_est else 0.0; r = tp / n_ref if n_ref else 0.0; f = 2 * p * r / (p + r) if p + r else 0.0
    d = np.array([x for *_, x in pairs]) if pairs else np.array([np.nan])
    return {'precision': p, 'recall': r, 'f1': f, 'mean_abs_dev_s': float(np.nanmean(np.abs(d))), 'mean_signed_dev_s': float(np.nanmean(d))}


def lag_scan(est, ref, tol, max_lag_s=0.6, step_s=0.0025):
    """Greedy F1 of est shifted by -lag against ref, over a range of global lags (s). Returns lags, F1."""
    lags = np.arange(-max_lag_s, max_lag_s + step_s / 2, step_s); est = np.asarray(est, float)
    return lags, np.array([prf(est - l, ref, tol)['f1'] for l in lags])


def _plateau_centre_ms(lags, f):
    """Centre (ms) of the contiguous run of lags at the maximum F1 that contains the first maximum; F1 is
    flat over +-tol around the true lag, so the first maximum would sit at the plateau's edge."""
    i = int(np.argmax(f)); j = i
    while j + 1 < len(f) and f[j + 1] == f[i]: j += 1
    return float(1e3 * (lags[i] + lags[j]) / 2)


def alias_floor(ref, tol, max_lag_s=0.6):
    """Best F1 a copy of the reference itself reaches at a WRONG global lag (|lag| > tol): the coincidental
    re-alignment a displaced output could score on this stimulus. A property of the reference alone."""
    lags, f = lag_scan(ref, ref, tol, max_lag_s); off = np.abs(lags) > tol
    return float(f[off].max()) if off.any() else 0.0


def timing_report(est, ref, tol=ONSET_TOL_S, max_lag_s=0.6):
    """Every candidate timing measure side by side (addendum A2): greedy F1 / deviation, order-preserving
    alignment F1 / deviation / signed displacement, lag scan (best lag, lag-0 specificity), alias floor of
    the reference and the floor-normalised F1 = (F1 - floor) / (1 - floor)."""
    g = prf(est, ref, tol); o = prf_pairs(align_ordered(est, ref, tol), len(est), len(ref))
    lags, f = lag_scan(est, ref, tol, max_lag_s); off = np.abs(lags) > tol; i0 = int(np.argmin(np.abs(lags)))
    floor = alias_floor(ref, tol, max_lag_s)
    return {'greedy_f1': g['f1'], 'greedy_dev_ms': 1e3 * g['mean_abs_dev_s'], 'ordered_f1': o['f1'], 'ordered_dev_ms': 1e3 * o['mean_abs_dev_s'],
            'signed_dev_ms': 1e3 * o['mean_signed_dev_s'], 'best_lag_ms': _plateau_centre_ms(lags, f), 'f1_lag0': float(f[i0]),
            'f1_best_wrong_lag': float(f[off].max()), 'lag_specificity': float(f[i0] - f[off].max()), 'alias_floor': floor,
            'f1_norm': float((g['f1'] - floor) / (1 - floor)) if floor < 1 else float('nan')}


def tempo_error(f_est, f_ref):
    """Relative tempo error, strict and octave-tolerant (factors 1/3, 1/2, 1, 2, 3)."""
    strict = abs(f_est - f_ref) / f_ref
    octave = min(abs(f_est * k - f_ref) / f_ref for k in (1 / 3, 0.5, 1, 2, 3))
    return {'tempo_est_hz': f_est, 'rel_err_strict': strict, 'rel_err_octave': octave}


def ioi_deviation(beats_est, beats_ref):
    """Median absolute deviation of estimated inter-beat intervals from the reference IBI (relative)."""
    if len(beats_est) < 3: return float('nan')
    ibi = np.diff(beats_est); ref = np.median(np.diff(beats_ref)); return float(np.median(np.abs(ibi - ref)) / ref)


def beat_band_z(x, sr, tempo_hz, lo_c=0.15, hi_c=0.8, ks=(1, 2)):
    """Beat-band harmonic power of the novelty envelope: weineck/tagging.tag_z on the envelope at the
    reference tempo, with the baseline window scaled by the tempo (lo = lo_c * f, hi = hi_c * f). The EEG
    study used a window fixed in Hz for long recordings; with excerpts of a fixed number of beat cycles
    (N_BEATS), scaling the window by f gives the same number of neighbouring bins at every tempo, which is
    the cycle-count control of docs/CYCLE_COUNT_CONTROL.md."""
    nov, fr = novelty(x, sr); tag_z = _tag_z()
    return float(tag_z(nov, tempo_hz, ks=ks, seg_s=len(nov) / fr, fs=fr, lo=lo_c * tempo_hz, hi=hi_c * tempo_hz))


def envelope_corr(x_ref, x, sr, max_lag_s=0.0):
    """Pearson r between novelty envelopes (zero lag by default: a timing shift must cost)."""
    a, fr = novelty(x_ref, sr); b, _ = novelty(x, sr); n = min(len(a), len(b)); a, b = a[:n], b[:n]
    if max_lag_s <= 0: return float(np.corrcoef(a, b)[0, 1])
    L = int(max_lag_s * fr); return float(max(np.corrcoef(a[max(0, -l):n - max(0, l)], b[max(0, l):n - max(0, -l)])[0, 1] for l in range(-L, L + 1)))


def envelope_lag_ms(x_ref, x, sr, max_lag_s=0.15):
    """Global latency diagnostic: lag (ms, positive = x late) maximising the novelty-envelope
    cross-correlation within +-max_lag_s. On a periodic grid this can alias to a grid step; diagnostic only."""
    a, fr = novelty(x_ref, sr); b, _ = novelty(x, sr); n = min(len(a), len(b)); a, b = a[:n] - a[:n].mean(), b[:n] - b[:n].mean()
    L = int(max_lag_s * fr); lags = np.arange(-L, L + 1)
    cc = [np.dot(a[max(0, -l):n - max(0, l)], b[max(0, l):n - max(0, -l)]) for l in lags]
    return float(1e3 * lags[int(np.argmax(cc))] / fr)


def rhythm_report(x, sr, gt, x_ref=None):
    """All rhythmic metrics for one output x against the composition's ground truth (and, for envelope
    similarity, against the source audio x_ref). Pre-specified roles (EXPERIMENT_PLAN.md):
      P1 onset F1 (+-50 ms)            : onsets detected in x vs ground-truth onsets (no beat tracker)
      P2 beat F1 informed (+-70 ms)    : beat positions tracked in x with the period of the nominal tempo
      secondary: uninformed beats and tempo (octave-tolerant error), IBI deviation, beat-band z, envelope r."""
    beats_ref = np.asarray(gt['beats_s']); onsets_ref = np.asarray(gt['onsets_s']); f_ref = gt['tempo_hz']
    on = detect_onsets(x, sr)
    b_inf, _ = track_beats(x, sr, tempo_hz=f_ref)
    nov, fr = novelty(x, sr); f_est = estimate_tempo(nov, fr, prior_octaves=3.0); b_un, _ = track_beats(x, sr, tempo_hz=f_est)
    rep = {'onset': prf(on, onsets_ref, ONSET_TOL_S), 'beat_informed': beat_scores(b_inf, beats_ref),
           'beat_uninformed': beat_scores(b_un, beats_ref), 'tempo': tempo_error(f_est, f_ref),
           'ibi_rel_dev': ioi_deviation(b_inf, beats_ref), 'beat_band_z': beat_band_z(x, sr, f_ref)}
    if x_ref is not None: rep['envelope_r'] = envelope_corr(x_ref, x, sr); rep['envelope_lag_ms'] = envelope_lag_ms(x_ref, x, sr)
    return rep


def flat(rep):
    """The scalar summary used in result tables."""
    return {'onset_f1': rep['onset']['f1'], 'onset_dev_ms': 1e3 * rep['onset']['mean_abs_dev_s'],
            'beat_f1': rep['beat_informed']['annotated']['f1'], 'beat_dev_ms': 1e3 * rep['beat_informed']['annotated']['mean_abs_dev_s'],
            'beat_f1_uninformed_any': rep['beat_uninformed']['any_level']['f1'], 'tempo_err_octave': rep['tempo']['rel_err_octave'],
            'tempo_err_strict': rep['tempo']['rel_err_strict'], 'ibi_rel_dev': rep['ibi_rel_dev'], 'beat_band_z': rep['beat_band_z'],
            'envelope_r': rep.get('envelope_r', float('nan')), 'envelope_lag_ms': rep.get('envelope_lag_ms', float('nan'))}
