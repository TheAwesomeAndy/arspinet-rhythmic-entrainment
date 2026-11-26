#!/usr/bin/env python3
"""Train the fallback rectified-flow editors on SAME-S latents (CPU).

V0 'label'  : v(x_t, t | target-instrumentation label, tempo). Trained on every latent (electronic sources
              labelled 0, acoustic targets labelled 1). Edits only through SDEdit from the source latent,
              the analogue of Stable Audio 3's text-conditioned editing.
V1 'paired' : v(x_t, t | label, tempo, source latent). Trained on pairs: x_0 = acoustic target, condition =
              electronic source of the same composition.
Identical architecture apart from the input channels, identical optimiser, steps, batch, crops, seed, EMA.
Validation loss: fixed timesteps and noise on full-length validation items, EMA weights.
Writes results/rf_training.json (committed) and checkpoints/rf_{V0,V1}.pt (git-ignored).
"""
import argparse, json, os, resource, sys, time
import numpy as np
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, os.path.join(ROOT, 'src'))
import rf_model as rf

LAT = os.path.join(ROOT, 'results', 'latents'); CK = os.path.join(ROOT, 'checkpoints')


def load_split(split):
    man = json.load(open(os.path.join(ROOT, 'results', 'latents_manifest.json')))['splits'][split]; z = np.load(os.path.join(LAT, f'{split}.npz'))
    return [{**m, 'src': z[f'{i}_src'], 'tgt': z[f'{i}_tgt']} for i, m in enumerate(man)]


def norm_stats(items):
    a = np.concatenate([np.concatenate([it['src'], it['tgt']], 1) for it in items], 1); return a.mean(1, keepdims=True), a.std(1, keepdims=True) + 1e-6


def examples(items, variant):
    """(x0, cond, label, tempo) tuples; latents already normalised."""
    out = []
    for it in items:
        if variant == 'V0':
            out.append((it['src'], None, 0, it['tempo_hz'])); out.append((it['tgt'], None, 1, it['tempo_hz']))
        else:
            out.append((it['tgt'], it['src'], 1, it['tempo_hz']))
    return out


def batch(ex, rng, bs, crop):
    xs, cs, ls, ts = [], [], [], []
    for k in rng.randint(0, len(ex), bs):
        x0, c, l, t = ex[k]; n = x0.shape[1]; s = rng.randint(0, max(1, n - crop + 1)); sl = slice(s, s + crop)
        pad = lambda a: np.pad(a[:, sl], ((0, 0), (0, crop - a[:, sl].shape[1])))
        xs.append(pad(x0)); cs.append(pad(c) if c is not None else None); ls.append(l); ts.append(t)
    cond = torch.from_numpy(np.stack(cs)).float() if cs[0] is not None else None
    return torch.from_numpy(np.stack(xs)).float(), cond, torch.tensor(ls), torch.tensor(ts, dtype=torch.float32)


@torch.no_grad()
def val_loss(net, ex, n_t=8, seed=123):
    g = torch.Generator().manual_seed(seed); tot, cnt = 0.0, 0
    for x0, c, l, tem in ex:
        x0 = torch.from_numpy(x0)[None].float(); cond = torch.from_numpy(c)[None].float() if c is not None else None
        for t in torch.linspace(0.05, 0.95, n_t):
            eps = torch.randn(x0.shape, generator=g); xt = (1 - t) * x0 + t * eps
            v = net(xt, t[None], torch.tensor([l]), torch.tensor([tem], dtype=torch.float32), cond); tot += float(((v - (eps - x0)) ** 2).mean()); cnt += 1
    return tot / cnt


def train(variant, steps, bs, crop, lr, seed, log_every, val_every):
    torch.manual_seed(seed); rng = np.random.RandomState(seed)
    tr, va = load_split('train'), load_split('val'); mu, sd = norm_stats(tr)
    nrm = lambda it: {**it, 'src': ((it['src'] - mu) / sd).astype(np.float32), 'tgt': ((it['tgt'] - mu) / sd).astype(np.float32)}
    tr, va = [nrm(i) for i in tr], [nrm(i) for i in va]; ex_tr, ex_va = examples(tr, variant), examples(va, variant)
    net = rf.VelocityNet(cond_ch=256 if variant == 'V1' else 0); ema = rf.VelocityNet(cond_ch=256 if variant == 'V1' else 0); ema.load_state_dict(net.state_dict())
    for p in ema.parameters(): p.requires_grad_(False)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=0.01); before = {k: v.clone() for k, v in net.state_dict().items()}
    log = {'train': [], 'val': []}; t0 = time.time(); run = []
    for step in range(1, steps + 1):
        x0, c, l, tem = batch(ex_tr, rng, bs, crop); loss, _ = rf.rf_loss(net, x0, l, tem, c)
        opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(net.parameters(), 1.0); opt.step()
        with torch.no_grad():
            for pe, p in zip(ema.parameters(), net.parameters()): pe.mul_(0.999).add_(p, alpha=0.001)
        run.append(float(loss))
        if step % log_every == 0: log['train'].append([step, float(np.mean(run))]); run = []
        if step % val_every == 0 or step == steps:
            log['val'].append([step, val_loss(ema, ex_va)]); print(f'{variant} step {step}: train {log["train"][-1][1]:.4f} val {log["val"][-1][1]:.4f} ({time.time() - t0:.0f}s)', flush=True)
    changed = sum(int(not torch.equal(before[k], v)) for k, v in net.state_dict().items()); os.makedirs(CK, exist_ok=True)
    torch.save({'ema': ema.state_dict(), 'mu': mu, 'sd': sd, 'variant': variant}, os.path.join(CK, f'rf_{variant}.pt'))
    return {'variant': variant, 'params_trainable': rf.n_params(net, True), 'params_total': rf.n_params(net), 'tensors_changed': changed, 'tensors_total': len(before),
            'steps': steps, 'batch': bs, 'crop_frames': crop, 'lr': lr, 'optimizer': 'AdamW(wd 0.01), grad clip 1.0, EMA 0.999', 'seed': seed,
            'objective': 'rectified flow: x_t=(1-t)x0+t*eps, target eps-x0, MSE, t~logit-normal(0,1)', 'train_seconds': time.time() - t0,
            'n_train_examples': len(ex_tr), 'n_val_examples': len(ex_va), 'loss': log, 'peak_rss_gb': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6,
            'torch_threads': torch.get_num_threads(), 'device': 'cpu'}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--steps', type=int, default=3000); ap.add_argument('--bs', type=int, default=32); ap.add_argument('--crop', type=int, default=32)
    ap.add_argument('--lr', type=float, default=2e-4); ap.add_argument('--seed', type=int, default=0); ap.add_argument('--variants', default='V0,V1')
    ap.add_argument('--log_every', type=int, default=50); ap.add_argument('--val_every', type=int, default=500); a = ap.parse_args()
    path = os.path.join(ROOT, 'results', 'rf_training.json'); out = json.load(open(path)) if os.path.exists(path) else {}
    for v in a.variants.split(','):
        out[v] = train(v, a.steps, a.bs, a.crop, a.lr, a.seed, a.log_every, a.val_every); json.dump(out, open(path, 'w'), indent=1)


if __name__ == '__main__':
    main()
