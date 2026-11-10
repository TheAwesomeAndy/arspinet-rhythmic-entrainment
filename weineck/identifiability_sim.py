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
NH = 60 * 14; NS = 4 * 27 + 1; NL = 4 * 65 + 1; NA = NH + NS   # 840, 109, 261, 949: block sizes, must match identifiability_precompute.py
LAM = {'s': 1.0, 'l': 1.0, 'a': 10.0, 'al': 1.0}; P = {'s': NS, 'l': NL, 'a': NA, 'al': NA}
GRID = np.arange(1.0, 4.01, 0.25)


class Store:
    """Memmapped sufficient statistics. The pool is tempo-sorted, so each tempo is a contiguous block of
    stimuli; every heavy operation is a float32 GEMV over one block (A entries are float32 at source)."""
    def __init__(self):
        self.A_a = np.load(f'{OUT}/A_a.npy', mmap_mode='r'); self.A_al = np.load(f'{OUT}/A_al.npy', mmap_mode='r'); self.A_l = np.load(f'{OUT}/A_l.npy', mmap_mode='r')
        self.C_la = np.load(f'{OUT}/C_la.npy', mmap_mode='r'); self.C_alh = np.load(f'{OUT}/C_alh.npy', mmap_mode='r')
        m = np.load(f'{OUT}/stimuli_meta.npz'); self.Bn = {'a': m['Bn_a'], 'al': m['Bn_al'], 'l': m['Bn_l']}; self.nsum = m['nsum']; self.nsq = m['nsq']; self.T = m['T'].astype(float); self.tempo = m['tempo']
        assert np.all(np.diff(self.tempo) >= 0)
        self.block = {t: (int(np.where(np.isclose(self.tempo, t))[0][0]), int(np.where(np.isclose(self.tempo, t))[0][-1]) + 1) for t in GRID}
        kern = {}
        for f in glob.glob(f'{OUT}/kernels_*.json'): kern.update(json.load(open(f)))
        self.kern = {s: {k: (np.array(v) if isinstance(v, list) else v) for k, v in d.items()} for s, d in kern.items()}; self.ksubs = sorted(self.kern, key=int)
        self._pieces = {}

    def blocks(self, t):
        """float32 blocks (n_q, p, p) for tempo t, read from the page cache."""
        s, e = self.block[t]
        return {'a': np.asarray(self.A_a[s:e]), 'al': np.asarray(self.A_al[s:e]), 'l': np.asarray(self.A_l[s:e])}

    def pieces(self, subj):
        """Per stimulus q (whole pool): b_e[M], b_o[M] (X_M' P_e, X_M' P_o, no noise) and the y-statistic pieces
        sPe, sPo, sPe2, sPo2, sPePo, for the kernels of participant subj. Cached per subject."""
        if subj in self._pieces: return self._pieces[subj]
        k = self.kern[subj]; W_e = k['W_trf'].astype(np.float32); Wo = k['W_osc'][:NH].astype(np.float32); wb = float(k['W_osc'][NH])
        n = len(self.T); out = {'b_e': {M: np.zeros((n, P[M])) for M in P}, 'b_o': {M: np.zeros((n, P[M])) for M in P}}
        sPe = np.zeros(n); sPo = np.zeros(n); sPe2 = np.zeros(n); sPo2 = np.zeros(n); sPePo = np.zeros(n)
        for t in GRID:
            s, e = self.block[t]; Aa = np.asarray(self.A_a[s:e]); Aal = np.asarray(self.A_al[s:e]); Al = np.asarray(self.A_l[s:e]); Cla = np.asarray(self.C_la[s:e]); Calh = np.asarray(self.C_alh[s:e])
            T = self.T[s:e]
            AaWe = np.einsum('qij,j->qi', Aa[:, :, NH:], W_e); AalWe = np.einsum('qij,j->qi', Aal[:, :, NH:], W_e); ClaWe = np.einsum('qij,j->qi', Cla[:, :, NH:], W_e)
            AaWo = np.einsum('qij,j->qi', Aa[:, :, :NH], Wo); CalhWo = np.einsum('qij,j->qi', Calh, Wo); ClaWo = np.einsum('qij,j->qi', Cla[:, :, :NH], Wo)
            out['b_e']['a'][s:e] = AaWe; out['b_e']['al'][s:e] = AalWe; out['b_e']['l'][s:e] = ClaWe; out['b_e']['s'][s:e] = AaWe[:, NH:]
            out['b_o']['a'][s:e] = AaWo + Aa[:, :, NA - 1] * wb; out['b_o']['al'][s:e] = np.concatenate([CalhWo, AaWo[:, NH:]], 1) + Aal[:, :, NA - 1] * wb
            out['b_o']['l'][s:e] = ClaWo + Al[:, :, NL - 1] * wb; out['b_o']['s'][s:e] = AaWo[:, NH:] + Aa[:, NH:, NA - 1] * wb
            sPe[s:e] = AaWe[:, NA - 1]; sPo[s:e] = AaWo[:, NA - 1] + T * wb
            sPe2[s:e] = AaWe[:, NH:] @ W_e.astype(float); sPo2[s:e] = AaWo[:, :NH] @ Wo.astype(float) + 2 * wb * AaWo[:, NA - 1] + T * wb ** 2; sPePo[s:e] = AaWo[:, NH:] @ W_e.astype(float) + wb * AaWe[:, NA - 1]
        out.update(sPe=sPe, sPo=sPo, sPe2=sPe2, sPo2=sPo2, sPePo=sPePo); self._pieces[subj] = out; return out


def ridge(A, B, lam):
    p = A.shape[0]; reg = lam * np.trace(A) / p * np.eye(p); reg[-1, -1] = 0.0; return np.linalg.solve(A + reg, B)


def simulate_participant(st, subj, w, gamma, n_trials, tempi, rng):
    """One simulated participant: n_trials trials per tempo drawn with replacement from the pool of that tempo,
    y = alpha P_e + beta P_o + gamma n_k; leave-one-tempo-out fits of the four models with fixed lambdas; returns
    the mean over held-out tempi of the mean per-trial held-out r per model."""
    kern = st.kern[subj]; pc = st.pieces(subj); W_e = kern['W_trf']; Wo = kern['W_osc'][:NH]; wb = kern['W_osc'][NH]
    alpha = (1 - w) / kern['sd_e']; beta = w / kern['sd_o']; K = st.Bn['a'].shape[1]
    nT = len(tempi); Asum = {M: np.zeros((nT, P[M], P[M])) for M in P}; trials = []
    for ti, t in enumerate(tempi):
        s, e = st.block[t]; qs = rng.randint(s, e, n_trials); kks = rng.randint(0, K, n_trials); counts = np.bincount(qs - s, minlength=e - s).astype(np.float32)
        blk = st.blocks(t)
        for M in ('a', 'al', 'l'): Asum[M][ti] = np.tensordot(counts, blk[M], axes=(0, 0)).astype(float)
        Asum['s'][ti] = Asum['a'][ti][NH:, NH:]
        trials.append((qs, kks))
    # per-trial right-hand sides and y statistics
    rec = []
    for ti, (qs, kks) in enumerate(trials):
        B = {M: alpha * pc['b_e'][M][qs] + beta * pc['b_o'][M][qs] + gamma * (st.Bn['a'][qs, kks][:, NH:] if M == 's' else st.Bn[M][qs, kks]) for M in P}
        nsum = st.nsum[qs, kks]; nsq = st.nsq[qs, kks]; sPen = st.Bn['a'][qs, kks][:, NH:] @ W_e; sPon = st.Bn['a'][qs, kks][:, :NH] @ Wo + wb * nsum
        sy = alpha * pc['sPe'][qs] + beta * pc['sPo'][qs] + gamma * nsum
        sy2 = alpha ** 2 * pc['sPe2'][qs] + beta ** 2 * pc['sPo2'][qs] + gamma ** 2 * nsq + 2 * alpha * beta * pc['sPePo'][qs] + 2 * alpha * gamma * sPen + 2 * beta * gamma * sPon
        rec.append((qs, B, sy, sy2, st.T[qs]))
    Bsum = {M: np.stack([r[1][M].sum(0) for r in rec]) for M in P}
    r_model = {M: np.zeros(nT) for M in P}
    for ho in range(nT):
        W = {M: ridge(Asum[M].sum(0) - Asum[M][ho], Bsum[M].sum(0) - Bsum[M][ho], LAM[M]) for M in P}
        qs, B, sy, sy2, T = rec[ho]; s, e = st.block[tempi[ho]]; blk = st.blocks(tempi[ho]); blk['s'] = blk['a'][:, NH:, NH:]
        for M in P:
            Wm = W[M]; AW = np.einsum('qij,j->qi', blk[M], Wm.astype(np.float32))        # (n_q, p) float32 GEMV per block
            sp_all = blk[M][:, -1, :] @ Wm; sp2_all = AW @ Wm; sp = sp_all[qs - s]; sp2 = sp2_all[qs - s]; spy = B[M] @ Wm
            cov = spy - sp * sy / T; vp = sp2 - sp ** 2 / T; vy = sy2 - sy ** 2 / T
            r_model[M][ho] = np.mean(cov / np.sqrt(np.maximum(vp, 1e-30) * np.maximum(vy, 1e-30)))
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
            res.append(simulate_participant(st, st.ksubs[k % len(st.ksubs)], 0.0, gam, a.trials, tempi, rng)['s'])
        r_real = float(np.median(res)); sig_eff = gam * r_real / np.sqrt(max(1 - r_real ** 2, 1e-9)); gam2 = sig_eff * np.sqrt(1 / a.r ** 2 - 1)
        res2 = [simulate_participant(st, st.ksubs[k % len(st.ksubs)], 0.0, gam2, a.trials, tempi, rng)['s'] for k in range(a.participants)]
        cal = json.load(open(f'{OUT}/calibration.json')) if os.path.exists(f'{OUT}/calibration.json') else {}
        cal[str(a.r)] = {'gamma': float(gam2), 'realised_r_oracle_gamma': r_real, 'realised_r': float(np.median(res2))}; json.dump(cal, open(f'{OUT}/calibration.json', 'w'), indent=1)
        print(f"calibration r*={a.r}: oracle gamma {gam:.3f} -> realised {r_real:.4f}; corrected gamma {gam2:.3f} -> realised {np.median(res2):.4f}"); return
    gamma = a.gamma if a.gamma is not None else json.load(open(f'{OUT}/calibration.json'))[str(a.r)]['gamma']
    out = a.out or f'{OUT}/cells/w{a.w}_r{a.r}_n{a.trials}_t{a.ntempi}.json'; os.makedirs(os.path.dirname(out), exist_ok=True)
    t0 = time.time(); det = []; dmed = []; rreal = []
    for d in range(a.datasets):
        part = [simulate_participant(st, st.ksubs[(d * a.participants + k) % len(st.ksubs)], a.w, gamma, a.trials, tempi, rng) for k in range(a.participants)]
        sup, dm, p1, rs = decide(part); det.append(sup); dmed.append(dm); rreal.append(rs)
        print(f"  w={a.w} r={a.r} n={a.trials} t={a.ntempi} dataset {d+1}/{a.datasets}: supported={sup} median delta_r {dm:+.4f} p={p1:.3f} realised r_short {rs:.4f} ({time.time()-t0:.0f}s)", flush=True)
        json.dump({'w': a.w, 'r_target': a.r, 'trials': a.trials, 'ntempi': a.ntempi, 'gamma': gamma, 'datasets_done': d + 1, 'detection_rate': float(np.mean(det)), 'median_delta_r': float(np.median(dmed)), 'realised_r_short': float(np.median(rreal)), 'per_dataset': {'supported': det, 'delta_r': dmed, 'r_short': rreal}}, open(out, 'w'), indent=1)
    print(f"cell done: w={a.w} r={a.r} n={a.trials} t={a.ntempi}: detection rate {np.mean(det):.2f} ({time.time()-t0:.0f}s)")


if __name__ == '__main__':
    main()
