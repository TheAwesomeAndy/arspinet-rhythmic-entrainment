"""Shared frequency-tagging statistic for the project (used by power_q2, q2_residual, tempo_curve).

tag_z(x, f): Welch PSD (Hann, seg_s segments, 50 % overlap); at each harmonic k*f (k in ks) the
bin value is compared with a LOCAL QUADRATIC baseline fitted to the neighbouring bins
(0.15-0.8 Hz away, other harmonics excluded): z = (p0 - fit(f0)) / sd(residuals). The
quadratic removes both the slope and the curvature of a 1/f-like spectrum, which a plain
neighbour mean does not. Returns max over k.

PSEUDO: log-symmetric pseudo-tempo ratios (mean log-ratio zero) for the within-participant
label-permutation test: the identical statistic at these ratios of the beat tempo is the null
reference for the beat label.
"""
import numpy as np
from scipy.signal import welch

FS = 256.0
PSEUDO = (1 / 1.20, 1 / 1.15, 1 / 1.10, 1.10, 1.15, 1.20)


def tag_z(x, f, ks=(1, 2), seg_s=10, fs=FS, lo=0.15, hi=0.8):
    nper = int(min(fs * seg_s, len(x)))
    fr, p = welch(x - x.mean(), fs=fs, nperseg=nper, noverlap=nper // 2, window='hann')
    zs = []
    for k in ks:
        f0 = k * f
        i = np.argmin(np.abs(fr - f0))
        nb = (np.abs(fr - f0) > lo) & (np.abs(fr - f0) < hi)
        for kk in ks:
            nb &= np.abs(fr - kk * f) > lo
        if nb.sum() < 6:
            zs.append(0.0); continue
        d = fr[nb] - f0
        A = np.vstack([np.ones_like(d), d, d ** 2]).T
        coef, *_ = np.linalg.lstsq(A, p[nb], rcond=None)
        resid = p[nb] - A @ coef
        zs.append(float((p[i] - coef[0]) / (resid.std() + 1e-15)))
    return max(zs)


def seven(x, f, **kw):
    """statistic at the beat tempo and at the six pseudo-tempos (beat first)."""
    return [float(tag_z(x, f, **kw))] + [float(tag_z(x, f * r, **kw)) for r in PSEUDO]


def perm_test(S, rng, n_perm=2000):
    """S: n_p x 7 participant scores (beat first). Statistic: mean over participants of
    beat minus mean(pseudo). Null: within each participant a random one of the 7 labels is
    called beat. Returns (observed, one-sided p)."""
    S = np.asarray(S, dtype=float)

    def stat(lab):
        b = S[np.arange(len(S)), lab]
        return (b - (S.sum(1) - b) / 6.0).mean()
    obs = stat(np.zeros(len(S), int))
    null = np.array([stat(rng.randint(0, 7, len(S))) for _ in range(n_perm)])
    return float(obs), float((np.sum(null >= obs) + 1) / (n_perm + 1))


# ---- stimulus-label shuffle null (replaces the pseudo-tempo label permutation) ----------------
GRID = np.arange(1.0, 4.01, 0.25)            # the 13 stimulation tempi of Weineck 2022


def grid_stats(x, grid=GRID, **kw):
    """tag_z of one trial at every grid tempo -> vector (len(grid),)."""
    return np.array([tag_z(x, float(f), **kw) for f in grid])


def participant_shuffle_z(Z, own, rng, n_shuf=500, min_log_ratio=np.log(1.05)):
    """Z: N x G statistics per trial at every grid tempo; own: N indices of each trial's tempo.
    Observed: mean over trials of Z[n, own[n]]. Null: each trial re-labelled with a random grid
    tempo at least `min_log_ratio` away from its own (same grid distribution, same variance).
    Returns (observed_mean, z against the shuffle distribution, shuffle mean, shuffle sd)."""
    Z = np.asarray(Z, float); own = np.asarray(own, int); N, G = Z.shape
    obs = Z[np.arange(N), own].mean()
    logg = np.log(GRID[:G]) if G == len(GRID) else np.log(np.arange(G) + 1.0)
    allowed = [np.where(np.abs(logg - logg[o]) > min_log_ratio)[0] for o in own]
    null = np.array([Z[np.arange(N), [rng.choice(a) for a in allowed]].mean() for _ in range(n_shuf)])
    return float(obs), float((obs - null.mean()) / (null.std() + 1e-12)), float(null.mean()), float(null.std())
