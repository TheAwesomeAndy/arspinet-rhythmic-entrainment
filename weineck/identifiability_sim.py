#!/usr/bin/env python3
"""Identifiability map, stage 2: simulate cells of the grid (docs/IDENTIFIABILITY_PLAN.md) from the
sufficient statistics produced by identifiability_precompute.py and apply the committed Theory 3 rule.

A simulated trial is a real stimulus q (pool) with
    y = alpha * P_e + beta * P_o + gamma * n_k,   alpha = (1-w)/sd_e, beta = w/sd_o,
P_e = Xs W_trf (participant kernel), P_o = Xh W_osc, n_k a stored unit-variance noise realisation,
gamma from the noise calibration for the target held-out r. All model fits and held-out correlations
are computed from X'X, X'y, column sums and sum(y), sum(y^2), without rebuilding any lag matrix.
Models: d_short, d_long, aug (Hopf + TRF), aug_lin (linear bank + TRF); fixed lambdas 1, 1, 10, 1.
"""
import argparse, json, os, sys, time, glob
import numpy as np
from scipy.stats import wilcoxon

OUT = '/home/user/arspinet-rhythmic-entrainment/weineck/results/identifiability'
LAM = {'s': 1.0, 'l': 1.0, 'a': 10.0, 'al': 1.0}; P = {'s': 105, 'l': 261, 'a': 885, 'al': 885}
GRID = np.arange(1.0, 4.01, 0.25)


class Store:
    def __init__(self):
        self.A_a = np.load(f'{OUT}/A_a.npy', mmap_mode='r'); self.A_al = np.load(f'{OUT}/A_al.npy', mmap_mode='r'); self.A_l = np.load(f'{OUT}/A_l.npy', mmap_mode='r')
        self.C_la = np.load(f'{OUT}/C_la.npy', mmap_mode='r'); self.C_alh = np.load(f'{OUT}/C_alh.npy', mmap_mode='r')
        m = np.load(f'{OUT}/stimuli_meta.npz'); self.Bn = {'a': m['Bn_a'], 'al': m['Bn_al'], 'l': m['Bn_l']}; self.nsum = m['nsum']; self.nsq = m['nsq']; self.T = m['T']; self.tempo = m['tempo']
        self.by_tempo = {t: np.where(np.isclose(self.tempo, t))[0] for t in GRID}
        kern = {}
        for f in glob.glob(f'{OUT}/kernels_*.json'): kern.update(json.load(open(f)))
        self.kern = {s: {k: (np.array(v) if isinstance(v, list) else v) for k, v in d.items()} for s, d in kern.items()}; self.ksubs = sorted(self.kern, key=int)

    def A(self, M, q):
        if M == 'a': return np.asarray(self.A_a[q], float)
        if M == 'al': return np.asarray(self.A_al[q], float)
        if M == 'l': return np.asarray(self.A_l[q], float)
        return np.asarray(self.A_a[q][780:, 780:], float)

    def pieces(self, q, W_e, W_o):
        """per-model b_e, b_o (without noise) and y-statistics pieces for stimulus q and kernels."""
        Aa = np.asarray(self.A_a[q], float); Aal = np.asarray(self.A_al[q], float); Al = np.asarray(self.A_l[q], float); Cla = np.asarray(self.C_la[q], float); Calh = np.asarray(self.C_alh[q], float)
        Wo, wb = W_o[:780], W_o[780]
        b_e = {'a': Aa[:, 780:] @ W_e, 'al': Aal[:, 780:] @ W_e, 'l': Cla[:, 780:] @ W_e, 's': Aa[780:, 780:] @ W_e}
        b_o = {'a': Aa[:, :780] @ Wo + Aa[:, 884] * wb, 'al': np.concatenate([Calh @ Wo, Aa[780:, :780] @ Wo]) + Aal[:, 884] * wb, 'l': Cla[:, :780] @ Wo + Al[:, 260] * wb, 's': Aa[780:, :780] @ Wo + Aa[780:, 884] * wb}
        T = self.T[q]
        sPe = Aa[884, 780:] @ W_e; sPo = Aa[884, :780] @ Wo + T * wb
        sPe2 = W_e @ Aa[780:, 780:] @ W_e; sPo2 = Wo @ Aa[:780, :780] @ Wo + 2 * wb * (Aa[884, :780] @ Wo) + T * wb ** 2; sPePo = W_e @ (Aa[780:, :780] @ Wo) + wb * (Aa[884, 780:] @ W_e)
        return b_e, b_o, dict(T=T, sPe=sPe, sPo=sPo, sPe2=sPe2, sPo2=sPo2, sPePo=sPePo)

    def noise_pieces(self, q, kk, W_e, W_o):
        Wo, wb = W_o[:780], W_o[780]
        b_n = {'a': self.Bn['a'][q, kk].astype(float), 'al': self.Bn['al'][q, kk].astype(float), 'l': self.Bn['l'][q, kk].astype(float)}; b_n['s'] = b_n['a'][780:]
        sPen = b_n['s'] @ W_e; sPon = b_n['a'][:780] @ Wo + wb * self.nsum[q, kk]
        return b_n, dict(nsum=self.nsum[q, kk], nsq=self.nsq[q, kk], sPen=sPen, sPon=sPon)


def ridge(A, B, lam):
    p = A.shape[0]; reg = lam * np.trace(A) / p * np.eye(p); reg[-1, -1] = 0.0; return np.linalg.solve(A + reg, B)


def simulate_participant(st, kern, w, gamma, n_trials, tempi, rng):
    W_e, W_o = kern['W_trf'], kern['W_osc']; alpha = (1 - w) / kern['sd_e']; beta = w / kern['sd_o']
    trials = []                                                      # (q, kk, tempo_idx)
    for ti, t in enumerate(tempi):
        pool = st.by_tempo[t]; qs = rng.choice(pool, n_trials); kks = rng.randint(0, st.Bn['a'].shape[1], n_trials)
        trials += [(int(q), int(kk), ti) for q, kk in zip(qs, kks)]
    nT = len(tempi); Asum = {M: np.zeros((nT, P[M], P[M])) for M in P}; Bsum = {M: np.zeros((nT, P[M])) for M in P}
    rec = []
    for (q, kk, ti) in trials:
        b_e, b_o, ys = st.pieces(q, W_e, W_o); b_n, ns = st.noise_pieces(q, kk, W_e, W_o)
        B = {M: alpha * b_e[M] + beta * b_o[M] + gamma * b_n[M] for M in P}
        sy = alpha * ys['sPe'] + beta * ys['sPo'] + gamma * ns['nsum']
        sy2 = alpha ** 2 * ys['sPe2'] + beta ** 2 * ys['sPo2'] + gamma ** 2 * ns['nsq'] + 2 * alpha * beta * ys['sPePo'] + 2 * alpha * gamma * ns['sPen'] + 2 * beta * gamma * ns['sPon']
        for M in P:
            Asum[M][ti] += st.A(M, q); Bsum[M][ti] += B[M]
        rec.append((q, ti, B, sy, sy2, ys['T']))
    r_model = {M: np.zeros(nT) for M in P}
    for ho in range(nT):
        W = {M: ridge(Asum[M].sum(0) - Asum[M][ho], Bsum[M].sum(0) - Bsum[M][ho], LAM[M]) for M in P}
        rs = {M: [] for M in P}
        for (q, ti, B, sy, sy2, T) in rec:
            if ti != ho: continue
            for M in P:
                A = st.A(M, q); c = A[-1]; Wm = W[M]
                sp = c @ Wm; sp2 = Wm @ A @ Wm; spy = Wm @ B[M]
                cov = spy - sp * sy / T; vp = sp2 - sp ** 2 / T; vy = sy2 - sy ** 2 / T
                rs[M].append(cov / np.sqrt(max(vp, 1e-30) * max(vy, 1e-30)))
        for M in P: r_model[M][ho] = np.mean(rs[M])
    return {M: float(r_model[M].mean()) for M in P}


def decide(part):
    """part: list of per-participant dicts of mean r per model. Committed rule."""
    aug = np.array([p['a'] for p in part]); best = np.maximum([p['s'] for p in part], [p['l'] for p in part]); al = np.array([p['al'] for p in part])
    d = aug - best; dl = al - best
    p1 = wilcoxon(d, alternative='greater').pvalue if np.any(d != 0) else 1.0; p2 = wilcoxon(d - dl, alternative='greater').pvalue if np.any(d - dl) else 1.0
    return bool(np.median(d) > 0 and p1 < 0.01 and p2 < 0.05), float(np.median(d)), float(p1), float(np.median([p['s'] for p in part]))


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--w', type=float, required=True); ap.add_argument('--r', type=float, required=True); ap.add_argument('--trials', type=int, required=True)
    ap.add_argument('--ntempi', type=int, default=12); ap.add_argument('--datasets', type=int, default=20); ap.add_argument('--participants', type=int, default=20); ap.add_argument('--seed', type=int, default=0)
    ap.add_argument('--gamma', type=float, default=None, help='noise scale; if omitted, read from calibration.json for --r'); ap.add_argument('--calibrate', action='store_true'); ap.add_argument('--out', default=None)
    a = ap.parse_args(); st = Store(); rng = np.random.RandomState(a.seed)
    tempi = GRID[np.round(np.linspace(0, 12, a.ntempi + 1)).astype(int)]
    if a.calibrate:
        # oracle gamma for the target r, then one correction from the realised held-out r at w = 0
        gam = np.sqrt(1 / a.r ** 2 - 1); res = []
        for k in range(a.participants):
            kern = st.kern[st.ksubs[k % len(st.ksubs)]]; res.append(simulate_participant(st, kern, 0.0, gam, a.trials, tempi, rng)['s'])
        r_real = float(np.median(res)); sig_eff = gam * r_real / np.sqrt(max(1 - r_real ** 2, 1e-9)); gam2 = sig_eff * np.sqrt(1 / a.r ** 2 - 1)
        res2 = [simulate_participant(st, st.kern[st.ksubs[k % len(st.ksubs)]], 0.0, gam2, a.trials, tempi, rng)['s'] for k in range(a.participants)]
        cal = json.load(open(f'{OUT}/calibration.json')) if os.path.exists(f'{OUT}/calibration.json') else {}
        cal[str(a.r)] = {'gamma': float(gam2), 'realised_r_oracle_gamma': r_real, 'realised_r': float(np.median(res2))}; json.dump(cal, open(f'{OUT}/calibration.json', 'w'), indent=1)
        print(f"calibration r*={a.r}: oracle gamma {gam:.3f} -> realised {r_real:.4f}; corrected gamma {gam2:.3f} -> realised {np.median(res2):.4f}"); return
    gamma = a.gamma if a.gamma is not None else json.load(open(f'{OUT}/calibration.json'))[str(a.r)]['gamma']
    out = a.out or f'{OUT}/cells/w{a.w}_r{a.r}_n{a.trials}_t{a.ntempi}.json'; os.makedirs(os.path.dirname(out), exist_ok=True)
    t0 = time.time(); det = []; dmed = []; rreal = []
    for d in range(a.datasets):
        part = [simulate_participant(st, st.kern[st.ksubs[(d * a.participants + k) % len(st.ksubs)]], a.w, gamma, a.trials, tempi, rng) for k in range(a.participants)]
        sup, dm, p1, rs = decide(part); det.append(sup); dmed.append(dm); rreal.append(rs)
        print(f"  w={a.w} r={a.r} n={a.trials} t={a.ntempi} dataset {d+1}/{a.datasets}: supported={sup} median delta_r {dm:+.4f} p={p1:.3f} realised r_short {rs:.4f} ({time.time()-t0:.0f}s)", flush=True)
        json.dump({'w': a.w, 'r_target': a.r, 'trials': a.trials, 'ntempi': a.ntempi, 'gamma': gamma, 'datasets_done': d + 1, 'detection_rate': float(np.mean(det)), 'median_delta_r': float(np.median(dmed)), 'realised_r_short': float(np.median(rreal)), 'per_dataset': {'supported': det, 'delta_r': dmed, 'r_short': rreal}}, open(out, 'w'), indent=1)
    print(f"cell done: w={a.w} r={a.r} n={a.trials} t={a.ntempi}: detection rate {np.mean(det):.2f} ({time.time()-t0:.0f}s)")


if __name__ == '__main__':
    main()
