#!/usr/bin/env python3
"""Power check for Q2/H2 (residual beat-locked structure), matched to how it will be run.

Per trial: pink-noise 'residual' (Weineck-like length, drawn from the observed one-to-one
trial durations 8-56 s, median ~25 s) with a planted beat-locked sinusoid at relative
amplitude a (a = 0 is the null). Statistic per trial: Welch tagging z at the beat
frequency and 2f (neighbour-frequency null, 10 s segments), max over k, MINUS the mean of the
same statistic at six pseudo-tempos (0.80-1.20 x f, excluding +-5 %): centred under the null.
Per participant: z_p = mean over N trials of the per-trial z, times sqrt(N) (so that under
the null z_p ~ N(0, 1) approximately). Per participant: z of the mean own-tempo statistic
against a stimulus-label shuffle (each trial re-labelled with another grid tempo). Across
participants: one-sided Wilcoxon on those z's, alpha 0.05. Power over Monte-Carlo replicates for n_participants in {9, 34},
N in {40, 75, 94}, a in {0, 0.02, 0.04, 0.06, 0.1}. Also reports the equivalent bound:
the smallest a with >= 80 % power.
"""
import argparse, json, os, sys, numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'weineck'))
from tagging import tag_z, GRID, grid_stats, participant_shuffle_z
from scipy.stats import wilcoxon

FS = 256.0


def pink(n, rng):
    X = np.fft.rfft(rng.standard_normal(n)); f = np.fft.rfftfreq(n, 1 / FS); f[0] = f[1]
    x = np.fft.irfft(X / np.sqrt(f), n=n); return (x - x.mean()) / x.std()




def trial_z(a, fi, dur, rng):
    f = GRID[fi]; n = int(dur * FS); t = np.arange(n) / FS
    x = pink(n, rng) + a * np.sqrt(2) * np.sin(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    return grid_stats(x)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--reps', type=int, default=300); ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--out', default='results/power_q2.json')
    ap.add_argument('--alphas', default='9:0.01,34:0.04', help='n_p:alpha pairs for the two-stage design')
    ap.add_argument('--amps', default='0.0,0.02,0.04,0.06'); a_ = ap.parse_args()
    alphas = {int(k): float(v) for k, v in (kv.split(':') for kv in a_.alphas.split(','))}
    rng = np.random.RandomState(a_.seed)
    durs = np.concatenate([rng.uniform(8, 56, 1000)])           # Weineck-like trial lengths (uniform 8-56 s; median ~32 s)
    # per-trial z distribution per amplitude (cache: draw a large pool per a)
    pool = {}
    for a in [float(v) for v in a_.amps.split(',')]:
        own = rng.randint(0, len(GRID), 1200)
        pool[a] = (np.array([trial_z(a, own[i], rng.choice(durs), rng) for i in range(1200)]), own)   # (1200 x 13, 1200)
        Z, o = pool[a]; own_z = Z[np.arange(1200), o]; other = np.array([np.delete(Z[i], o[i]).mean() for i in range(1200)])
        delta = (own_z - other).mean() / (own_z - other).std()
        print(f"a={a:.2f}: per-trial z at own tempo mean {own_z.mean():+.3f}; at other grid tempi mean {other.mean():+.3f}; per-trial standardized effect delta = {delta:+.3f}", flush=True)
    out = {'power': {}}
    print(f"{'a':>5} {'n_p':>4} {'N':>4} | power (stimulus-label shuffle z per participant, one-sided Wilcoxon at the stage alpha)")
    for a in pool:
        for n_p in sorted(alphas):
            alpha = alphas[n_p]
            for N in (40, 75, 94):
                rej = 0
                for r in range(a_.reps):
                    Z, o = pool[a]; zp = []
                    for _ in range(n_p):
                        idx = rng.choice(len(Z), N); zp.append(participant_shuffle_z(Z[idx], o[idx], rng, 200)[1])
                    zp = np.array(zp)
                    rej += (wilcoxon(zp, alternative='greater').pvalue < alpha) if np.any(zp != 0) else 0
                pw = rej / a_.reps; out['power'][f"a={a},n_p={n_p},N={N},alpha={alpha}"] = pw
                print(f"{a:5.2f} {n_p:4d} {N:4d} | alpha {alpha:.2f} | {pw:.2f}")
    json.dump(out, open(a_.out, 'w'), indent=1)


if __name__ == '__main__':
    main()
