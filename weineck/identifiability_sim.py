#!/usr/bin/env python3
"""Identifiability map, stage 2: simulate cells of the grid (docs/IDENTIFIABILITY_PLAN.md, including
addendum A3) from the sufficient statistics produced by identifiability_precompute.py and apply the
committed Theory 3 rule.

A simulated trial is a real stimulus q (pool) with
    y = alpha * P_e + beta * P_o + gamma * n_k,
P_e = Xs W_trf (participant evoked kernel), P_o = Xa V (an oscillator kernel on the augmented design
Xa = [Hopf lags | short TRF with bias]), n_k a stored unit-variance noise realisation, gamma from the
noise calibration for the target held-out r. All model fits and held-out correlations are computed from
X'X, X'y, column sums and sum(y), sum(y^2), without rebuilding any lag matrix.

Worlds:
  A  (committed grid)  V = [W_osc Hopf block; bias]; alpha = (1-w)/sd_e, beta = w/sd_o (participant sds).
  B  (A3.1)  same P_o; sds pooled within-trial over the simulation pool; s rescaled at every w so that its
             pooled within-trial variance equals that of World A's w = 0 signal for the participant.
  C  (A3.2)  P_o replaced by its residual after OLS projection onto the short TRF design over the pool;
             unit pooled within-trial sd; power-matched as in B.
Models: d_short, d_long, aug (Hopf + TRF), aug_lin (linear bank + TRF); fixed lambdas 1, 1, 10, 1, or
(--nested, A3.3) lambda chosen per model and outer fold by inner leave-one-tempo-out over the training
tempi from {0.1, 1, 10, 100, 1000}, as in oscillator_heldout.loto.
"""
import argparse, json, os, sys, time, glob, itertools
import numpy as np
from scipy.stats import wilcoxon

OUT = '/home/user/arspinet-rhythmic-entrainment/weineck/results/identifiability'
NH = 60 * 14; NS = 4 * 27 + 1; NL = 4 * 65 + 1; NA = NH + NS   # 840, 109, 261, 949: block sizes, must match identifiability_precompute.py
LAM = {'s': 1.0, 'l': 1.0, 'a': 10.0, 'al': 1.0}; P = {'s': NS, 'l': NL, 'a': NA, 'al': NA}
LAMS = (0.1, 1.0, 10.0, 100.0, 1000.0)
GRID = np.arange(1.0, 4.01, 0.25)


class Store:
    """Memmapped sufficient statistics. The pool is tempo-sorted, so each tempo is a contiguous block of
    stimuli; every heavy operation is a float32 product over one block (A entries are float32 at source)."""
    def __init__(self):
        self.A_a = np.load(f'{OUT}/A_a.npy', mmap_mode='r'); self.A_al = np.load(f'{OUT}/A_al.npy', mmap_mode='r'); self.A_l = np.load(f'{OUT}/A_l.npy', mmap_mode='r')
        self.C_la = np.load(f'{OUT}/C_la.npy', mmap_mode='r'); self.C_alh = np.load(f'{OUT}/C_alh.npy', mmap_mode='r')
        m = np.load(f'{OUT}/stimuli_meta.npz'); self.Bn = {'a': m['Bn_a'], 'al': m['Bn_al'], 'l': m['Bn_l']}; self.nsum = m['nsum']; self.nsq = m['nsq']; self.T = m['T'].astype(float); self.tempo = m['tempo']
        assert np.all(np.diff(self.tempo) >= 0)
        self.block = {t: (int(np.where(np.isclose(self.tempo, t))[0][0]), int(np.where(np.isclose(self.tempo, t))[0][-1]) + 1) for t in GRID}
        kern = {}
        for f in glob.glob(f'{OUT}/kernels_*.json'): kern.update(json.load(open(f)))
        self.kern = {s: {k: (np.array(v) if isinstance(v, list) else v) for k, v in d.items()} for s, d in kern.items()}; self.ksubs = sorted(self.kern, key=int)
        self._pieces = {}; self._sums = None

    def blocks(self, t):
        s, e = self.block[t]
        return {'a': np.asarray(self.A_a[s:e]), 'al': np.asarray(self.A_al[s:e]), 'l': np.asarray(self.A_l[s:e])}

    def sums(self):
        """Pool sums of A_a, A_l and C_la (participant-independent), cached on disk."""
        if self._sums is None:
            f = f'{OUT}/pool_sums.npz'
            if not os.path.exists(f):
                Sa = np.zeros((NA, NA)); Sl = np.zeros((NL, NL)); Sc = np.zeros((NL, NA))
                for t in GRID:
                    s, e = self.block[t]; Sa += np.asarray(self.A_a[s:e]).sum(0, dtype=float); Sl += np.asarray(self.A_l[s:e]).sum(0, dtype=float); Sc += np.asarray(self.C_la[s:e]).sum(0, dtype=float)
                np.savez(f, Sa=Sa, Sl=Sl, Sc=Sc)
            z = np.load(f); self._sums = {'Sa': z['Sa'], 'Sl': z['Sl'], 'Sc': z['Sc']}
        return self._sums

    def osc_kernel(self, subj, world):
        """Oscillator kernel V on Xa (length NA) and diagnostics. World A/B: Hopf kernel with its bias.
        World C: residual after OLS projection of P_o onto the short TRF design over the pool."""
        k = self.kern[subj]; V = np.zeros(NA); V[:NH] = k['W_osc'][:NH]; V[NA - 1] = k['W_osc'][NH]
        if world != 'C': return V, {}
        S = self.sums(); Sa = S['Sa']; N = self.T.sum()
        b = np.linalg.solve(Sa[NH:, NH:], Sa[NH:, :] @ V)          # projection on Xs (incl. bias)
        Vc = V.copy(); Vc[NH:] -= b
        ss_tot = V @ Sa @ V - (Sa[NA - 1] @ V) ** 2 / N; ss_res = Vc @ Sa @ Vc
        bl = np.linalg.solve(S['Sl'], S['Sc'] @ V); ss_res_l = V @ Sa @ V - bl @ (S['Sc'] @ V)
        return Vc, {'R2_short_trf': float(1 - ss_res / ss_tot), 'R2_long_trf': float(1 - ss_res_l / ss_tot), 'resid_mean_check': float(Sa[NA - 1] @ Vc / N)}

    def pieces(self, subj, world='A'):
        """Per stimulus q (whole pool): b_e[M] = X_M' P_e, b_o[M] = X_M' P_o and the y-statistic pieces
        sPe, sPo, sPe2, sPo2, sPePo, for participant subj in the given world. Cached."""
        key = (subj, 'C' if world == 'C' else 'A')
        if key in self._pieces: return self._pieces[key]
        k = self.kern[subj]; W_e = k['W_trf'].astype(np.float32); V, diag = self.osc_kernel(subj, key[1]); V32 = V.astype(np.float32)
        n = len(self.T); out = {'b_e': {M: np.zeros((n, P[M])) for M in P}, 'b_o': {M: np.zeros((n, P[M])) for M in P}, 'V': V, 'diag': diag}
        sPe = np.zeros(n); sPo = np.zeros(n); sPe2 = np.zeros(n); sPo2 = np.zeros(n); sPePo = np.zeros(n)
        for t in GRID:
            s, e = self.block[t]; Aa = np.asarray(self.A_a[s:e]); Aal = np.asarray(self.A_al[s:e]); Cla = np.asarray(self.C_la[s:e]); Calh = np.asarray(self.C_alh[s:e])
            AaWe = np.einsum('qij,j->qi', Aa[:, :, NH:], W_e); AalWe = np.einsum('qij,j->qi', Aal[:, :, NH:], W_e); ClaWe = np.einsum('qij,j->qi', Cla[:, :, NH:], W_e)
            AaV = np.einsum('qij,j->qi', Aa, V32); ClaV = np.einsum('qij,j->qi', Cla, V32)
            linV = np.einsum('qij,j->qi', Calh, V32[:NH]) + np.einsum('qij,j->qi', Aal[:, :NH, NH:], V32[NH:])
            out['b_e']['a'][s:e] = AaWe; out['b_e']['al'][s:e] = AalWe; out['b_e']['l'][s:e] = ClaWe; out['b_e']['s'][s:e] = AaWe[:, NH:]
            out['b_o']['a'][s:e] = AaV; out['b_o']['al'][s:e] = np.concatenate([linV, AaV[:, NH:]], 1); out['b_o']['l'][s:e] = ClaV; out['b_o']['s'][s:e] = AaV[:, NH:]
            sPe[s:e] = AaWe[:, NA - 1]; sPo[s:e] = AaV[:, NA - 1]
            sPe2[s:e] = AaWe[:, NH:] @ W_e.astype(float); sPo2[s:e] = AaV @ V; sPePo[s:e] = AaV[:, NH:] @ W_e.astype(float)
        T = self.T
        out.update(sPe=sPe, sPo=sPo, sPe2=sPe2, sPo2=sPo2, sPePo=sPePo,
                   Ve=float(np.sum(sPe2 - sPe ** 2 / T)), Vo=float(np.sum(sPo2 - sPo ** 2 / T)), Ceo=float(np.sum(sPePo - sPe * sPo / T)), N=float(T.sum()))
        self._pieces[key] = out; return out


def mix_weights(st, subj, w, world):
    """alpha, beta for the world (see module docstring)."""
    k = st.kern[subj]
    if world == 'A': return (1 - w) / k['sd_e'], w / k['sd_o']
    pc = st.pieces(subj, world); N = pc['N']; sde = np.sqrt(pc['Ve'] / N); sdo = np.sqrt(pc['Vo'] / N)
    a, b = (1 - w) / sde, w / sdo
    V = a ** 2 * pc['Ve'] + b ** 2 * pc['Vo'] + 2 * a * b * pc['Ceo']; V0 = pc['Ve'] / k['sd_e'] ** 2   # World A's w = 0 signal
    c = np.sqrt(V0 / V); return a * c, b * c


def ridge(A, B, lam):
    p = A.shape[0]; reg = lam * np.trace(A) / p * np.eye(p); reg[-1, -1] = 0.0; return np.linalg.solve(A + reg, B)


def heldout_r(blk, s0, Wst, rec_t):
    """Mean per-trial held-out r on one tempo block for a stack of weight vectors Wst (p, K)."""
    qs, B, sy, sy2, T = rec_t
    W32 = Wst.astype(np.float32); AW = np.matmul(blk, W32)                     # (n_q, p, K)
    sp2_all = np.einsum('qik,ik->qk', AW, Wst); sp_all = blk[:, -1, :] @ Wst
    sp = sp_all[qs - s0]; sp2 = sp2_all[qs - s0]; spy = B @ Wst
    cov = spy - sp * sy[:, None] / T[:, None]; vp = sp2 - sp ** 2 / T[:, None]; vy = sy2 - sy ** 2 / T
    return np.mean(cov / np.sqrt(np.maximum(vp, 1e-30) * np.maximum(vy, 1e-30)[:, None]), 0)


def simulate_participant(st, subj, w, gamma, n_trials, tempi, rng, world='A', nested=False, diag=False, lampair=False):
    """One simulated participant: n_trials trials per tempo drawn with replacement from the pool of that tempo,
    y = alpha P_e + beta P_o + gamma n_k; leave-one-tempo-out fits of the four models; returns the mean over
    held-out tempi of the mean per-trial held-out r per model (and, if nested, the chosen lambdas)."""
    pc = st.pieces(subj, world); W_e = st.kern[subj]['W_trf']; V = pc['V']
    alpha, beta = mix_weights(st, subj, w, world); K = st.Bn['a'].shape[1]
    nT = len(tempi); Asum = {M: np.zeros((nT, P[M], P[M])) for M in P}; trials = []
    for ti, t in enumerate(tempi):
        s, e = st.block[t]; qs = rng.randint(s, e, n_trials); kks = rng.randint(0, K, n_trials); counts = np.bincount(qs - s, minlength=e - s).astype(np.float32)
        blk = st.blocks(t)
        for M in ('a', 'al', 'l'): Asum[M][ti] = np.tensordot(counts, blk[M], axes=(0, 0)).astype(float)
        Asum['s'][ti] = Asum['a'][ti][NH:, NH:]
        trials.append((qs, kks))
    rec = []
    for ti, (qs, kks) in enumerate(trials):
        Bna = st.Bn['a'][qs, kks].astype(float)
        B = {M: alpha * pc['b_e'][M][qs] + beta * pc['b_o'][M][qs] + gamma * (Bna[:, NH:] if M == 's' else st.Bn[M][qs, kks].astype(float)) for M in P}
        nsum = st.nsum[qs, kks]; nsq = st.nsq[qs, kks]; sPen = Bna[:, NH:] @ W_e; sPon = Bna @ V
        sy = alpha * pc['sPe'][qs] + beta * pc['sPo'][qs] + gamma * nsum
        sy2 = alpha ** 2 * pc['sPe2'][qs] + beta ** 2 * pc['sPo2'][qs] + gamma ** 2 * nsq + 2 * alpha * beta * pc['sPePo'][qs] + 2 * alpha * gamma * sPen + 2 * beta * gamma * sPon
        rec.append((qs, B, sy, sy2, st.T[qs]))
    Bsum = {M: np.stack([r[1][M].sum(0) for r in rec]) for M in P}
    Atot = {M: Asum[M].sum(0) for M in P}; Btot = {M: Bsum[M].sum(0) for M in P}
    blocks = {}
    def blk_of(ti):
        if ti not in blocks:
            b = st.blocks(tempi[ti]); b['s'] = b['a'][:, NH:, NH:]; blocks[ti] = b
        return blocks[ti]
    def rec_M(ti, M):
        qs, B, sy, sy2, T = rec[ti]; return (qs, B[M], sy, sy2, T)
    r_model = {M: np.zeros(nT) for M in P}; chosen = {M: [] for M in P}
    if not nested:
        if diag: r_model['a1'] = np.zeros(nT)
        if lampair:
            for k in ('a_1', 'a_10', 'al_1', 'al_10'): r_model[k] = np.zeros(nT)
        for ho in range(nT):
            b = blk_of(ho); s0 = st.block[tempi[ho]][0]
            if lampair:                                # A4.2: both augmented models at lambda 1 and at lambda 10
                for M in ('a', 'al'):
                    A_, B_ = Atot[M] - Asum[M][ho], Btot[M] - Bsum[M][ho]
                    rr = heldout_r(b[M], s0, np.stack([ridge(A_, B_, 1.0), ridge(A_, B_, 10.0)], 1), rec_M(ho, M)); r_model[f'{M}_1'][ho], r_model[f'{M}_10'][ho] = rr
            for M in P:
                if M == 'a' and diag:                  # DIAGNOSTIC: aug at lambda 10 (committed) and at lambda 1
                    A_, B_ = Atot[M] - Asum[M][ho], Btot[M] - Bsum[M][ho]
                    Wst = np.stack([ridge(A_, B_, LAM[M]), ridge(A_, B_, 1.0)], 1); rr = heldout_r(b[M], s0, Wst, rec_M(ho, M))
                    r_model['a'][ho], r_model['a1'][ho] = rr; continue
                Wm = ridge(Atot[M] - Asum[M][ho], Btot[M] - Bsum[M][ho], LAM[M])
                r_model[M][ho] = heldout_r(b[M], s0, Wm[:, None], rec_M(ho, M))[0]
        return {M: float(v.mean()) for M, v in r_model.items()}
    # nested: inner LOTO over the training tempi; each unordered pair {i, j} gives one training set
    inner = {M: np.zeros((nT, nT, len(LAMS))) for M in P}     # inner[M][outer, inner_heldout, lam]
    for i, j in itertools.combinations(range(nT), 2):
        for M in P:
            A = Atot[M] - Asum[M][i] - Asum[M][j]; B = Btot[M] - Bsum[M][i] - Bsum[M][j]
            Wst = np.stack([ridge(A, B, lam) for lam in LAMS], 1)
            inner[M][j, i] = heldout_r(blk_of(i)[M], st.block[tempi[i]][0], Wst, rec_M(i, M))
            inner[M][i, j] = heldout_r(blk_of(j)[M], st.block[tempi[j]][0], Wst, rec_M(j, M))
        for ti in (i, j):
            if ti in blocks and len(blocks) > 3: blocks.pop(ti)
    for ho in range(nT):
        tr = [v for v in range(nT) if v != ho]
        for M in P:
            li = int(np.argmax(inner[M][ho, tr].mean(0))); lam = LAMS[li]; chosen[M].append(lam)
            Wm = ridge(Atot[M] - Asum[M][ho], Btot[M] - Bsum[M][ho], lam)
            r_model[M][ho] = heldout_r(blk_of(ho)[M], st.block[tempi[ho]][0], Wm[:, None], rec_M(ho, M))[0]
    res = {M: float(r_model[M].mean()) for M in P}; res['lams'] = chosen; return res


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
    ap.add_argument('--world', default='A', choices=['A', 'B', 'C']); ap.add_argument('--nested', action='store_true')
    ap.add_argument('--diag', action='store_true', help='criterion-2 diagnostic: store per-dataset aug-minus-linear-bank statistics and aug at lambda 1')
    ap.add_argument('--lampair', action='store_true', help='A4.2: criterion 2 with both augmented models at lambda 1 and at lambda 10')
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
    sub = 'cells_lampair' if a.lampair else ('cells_diag' if a.diag else ('cells' if (a.world == 'A' and not a.nested) else (('cells_nested' if a.world == 'A' else f'cells_nested_{a.world}') if a.nested else f'cells_{a.world}')))
    out = a.out or (f'{OUT}/{sub}/{a.world}_w{a.w}_r{a.r}_n{a.trials}_t{a.ntempi}.json' if (a.diag or a.lampair) else None)
    out = out or f'{OUT}/{sub}/w{a.w}_r{a.r}_n{a.trials}_t{a.ntempi}.json'; os.makedirs(os.path.dirname(out), exist_ok=True)
    t0 = time.time(); det = []; dmed = []; rreal = []; lams = []; diag = {}; c2 = []; P1 = []; P2 = []; DL = []; LP = []
    for d in range(a.datasets):
        subs = [st.ksubs[(d * a.participants + k) % len(st.ksubs)] for k in range(a.participants)]
        part = [simulate_participant(st, s, a.w, gamma, a.trials, tempi, rng, a.world, a.nested, a.diag, a.lampair) for s in subs]
        if a.world == 'C':
            for s in subs: diag[s] = st.pieces(s, 'C')['diag']
        sup, dm, p1, rs = decide(part); det.append(sup); dmed.append(dm); rreal.append(rs)
        aug_ = np.array([p['a'] for p in part]); al_ = np.array([p['al'] for p in part]); best_ = np.maximum([p['s'] for p in part], [p['l'] for p in part])
        P1.append(float(p1)); P2.append(float(wilcoxon(aug_ - al_, alternative='greater').pvalue) if np.any(aug_ != al_) else 1.0); DL.append(float(np.median(aug_ - al_)))
        if a.lampair:
            pw = lambda x, y: float(wilcoxon(x - y, alternative='greater').pvalue)
            g = {k: np.array([p[k] for p in part]) for k in ('a_1', 'a_10', 'al_1', 'al_10')}
            LP.append({'committed_10_vs_1': {'p2': pw(g['a_10'], g['al_1']), 'median': float(np.median(g['a_10'] - g['al_1']))},
                       'both_1': {'p2': pw(g['a_1'], g['al_1']), 'median': float(np.median(g['a_1'] - g['al_1']))},
                       'both_10': {'p2': pw(g['a_10'], g['al_10']), 'median': float(np.median(g['a_10'] - g['al_10']))},
                       'criterion1_committed_p': float(p1), 'criterion1_committed_median': float(dm)})
        if a.nested: lams += [p['lams'] for p in part]
        if a.diag:
            aug = np.array([p['a'] for p in part]); al = np.array([p['al'] for p in part]); a1 = np.array([p['a1'] for p in part]); best = np.maximum([p['s'] for p in part], [p['l'] for p in part])
            c2.append({'median_aug_minus_best': float(np.median(aug - best)), 'median_aug_minus_lin': float(np.median(aug - al)), 'p2_aug_vs_lin': float(wilcoxon(aug - al, alternative='greater').pvalue),
                       'median_aug_lam1_minus_lin': float(np.median(a1 - al)), 'p2_aug_lam1_vs_lin': float(wilcoxon(a1 - al, alternative='greater').pvalue), 'median_lin_minus_best': float(np.median(al - best)),
                       'median_r': {'s': float(np.median([p['s'] for p in part])), 'l': float(np.median([p['l'] for p in part])), 'a': float(np.median(aug)), 'a_lam1': float(np.median(a1)), 'al': float(np.median(al))}})
        print(f"  world {a.world}{' nested' if a.nested else ''} w={a.w} r={a.r} n={a.trials} t={a.ntempi} dataset {d+1}/{a.datasets}: supported={sup} median delta_r {dm:+.4f} p={p1:.3f} realised r_short {rs:.4f} ({time.time()-t0:.0f}s)", flush=True)
        res = {'world': a.world, 'nested_lambda': a.nested, 'seed': a.seed, 'w': a.w, 'r_target': a.r, 'trials': a.trials, 'ntempi': a.ntempi, 'gamma': gamma, 'datasets_done': d + 1, 'detection_rate': float(np.mean(det)), 'median_delta_r': float(np.median(dmed)), 'realised_r_short': float(np.median(rreal)), 'per_dataset': {'supported': det, 'delta_r': dmed, 'r_short': rreal, 'p1': P1, 'p2': P2, 'aug_minus_lin': DL}}
        if a.nested: res['chosen_lambda_counts'] = {M: {str(l): int(sum(x[M].count(l) for x in lams)) for l in LAMS} for M in P}
        if diag: res['world_C_diagnostics'] = diag
        if c2: res['criterion2_diagnostic'] = c2
        if LP: res['lambda_pair'] = LP
        json.dump(res, open(out, 'w'), indent=1)
    print(f"cell done: world {a.world}{' nested' if a.nested else ''} w={a.w} r={a.r} n={a.trials} t={a.ntempi}: detection rate {np.mean(det):.2f} ({time.time()-t0:.0f}s)")


if __name__ == '__main__':
    main()
