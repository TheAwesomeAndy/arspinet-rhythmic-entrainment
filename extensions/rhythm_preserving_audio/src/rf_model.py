"""A small conditional rectified-flow (flow-matching) model on SAME-S latents, implemented from scratch.

Convention (the same as Stable Audio 3's `rectified_flow` objective): data at t = 0, noise at t = 1,
    x_t = (1 - t) x_0 + t eps,     velocity target  v = d x_t / dt = eps - x_0,
loss = E_{t, eps} || v_theta(x_t, t, c) - (eps - x_0) ||^2 with t ~ logit-normal(0, 1).
Sampling integrates dx/dt = v_theta from t = t_start down to 0 (Euler or Heun). Editing (SDEdit-style,
the analogue of Stable Audio 3's init_noise_level): x_{t_start} = (1 - t_start) x_src + t_start eps, then
integrate to 0. t_start = 1 is generation from pure noise.

Conditioning: target instrumentation label and tempo (both variants), plus, for the paired variant V1, the
source latent concatenated on the channel axis. The network is a 1-D residual convolution stack with
FiLM (scale / shift) conditioning on the time / label / tempo embedding; fully convolutional, so it runs on
any latent length.
"""
from __future__ import annotations

import math

import torch
import torch.nn as nn
import torch.nn.functional as F


def fourier(x, dim, max_period=1000.0):
    half = dim // 2; f = torch.exp(-math.log(max_period) * torch.arange(half, device=x.device) / half)
    a = x[:, None].float() * f[None] * 2 * math.pi; return torch.cat([a.sin(), a.cos()], -1)


class Block(nn.Module):
    def __init__(self, h, emb, dilation):
        super().__init__()
        self.n1 = nn.GroupNorm(8, h); self.c1 = nn.Conv1d(h, h, 3, padding=dilation, dilation=dilation)
        self.n2 = nn.GroupNorm(8, h); self.c2 = nn.Conv1d(h, h, 3, padding=1)
        self.film = nn.Linear(emb, 2 * h)

    def forward(self, x, e):
        s, b = self.film(e)[:, :, None].chunk(2, 1)
        y = self.c1(F.silu(self.n1(x) * (1 + s) + b)); y = self.c2(F.silu(self.n2(y))); return x + y


class VelocityNet(nn.Module):
    def __init__(self, ch=256, cond_ch=0, hidden=192, emb=256, n_labels=3, dilations=(1, 2, 4, 8, 1, 2, 4, 8)):
        super().__init__()
        self.cond_ch = cond_ch
        self.inp = nn.Conv1d(ch + cond_ch, hidden, 1)
        self.t_mlp = nn.Sequential(nn.Linear(emb, emb), nn.SiLU(), nn.Linear(emb, emb))
        self.label = nn.Embedding(n_labels, emb); self.tempo = nn.Linear(64, emb)
        self.blocks = nn.ModuleList([Block(hidden, emb, d) for d in dilations])
        self.out = nn.Conv1d(hidden, ch, 1); nn.init.zeros_(self.out.weight); nn.init.zeros_(self.out.bias)
        self.emb = emb

    def forward(self, x, t, label, tempo_hz, cond=None):
        e = self.t_mlp(fourier(t, self.emb)) + self.label(label) + self.tempo(fourier(tempo_hz, 64, 100.0))
        h = self.inp(torch.cat([x, cond], 1) if self.cond_ch else x)
        for b in self.blocks: h = b(h, e)
        return self.out(h)


def rf_loss(net, x0, label, tempo, cond=None, generator=None):
    """Flow-matching loss for one batch. Returns (loss, t)."""
    B = x0.shape[0]; t = torch.sigmoid(torch.randn(B, generator=generator)); eps = torch.randn(x0.shape, generator=generator)
    xt = (1 - t)[:, None, None] * x0 + t[:, None, None] * eps
    return F.mse_loss(net(xt, t, label, tempo, cond), eps - x0), t


@torch.no_grad()
def sample(net, shape, label, tempo, cond=None, t_start=1.0, x_init=None, steps=32, method='euler', seed=0):
    """Integrate dx/dt = v from t_start to 0. If t_start < 1, x_init (the source latent, normalised) is noised
    to t_start first (SDEdit). The step count scales with t_start (steps over the full [0, 1] interval)."""
    g = torch.Generator().manual_seed(seed); eps = torch.randn(shape, generator=g)
    x = eps if (x_init is None or t_start >= 1.0) else (1 - t_start) * x_init + t_start * eps
    n = max(1, int(round(steps * t_start))); ts = torch.linspace(t_start, 0.0, n + 1)
    for i in range(n):
        t0, t1 = ts[i], ts[i + 1]; tb = torch.full((shape[0],), float(t0))
        v = net(x, tb, label, tempo, cond)
        if method == 'heun' and float(t1) > 0:
            x_e = x + (t1 - t0) * v; v2 = net(x_e, torch.full((shape[0],), float(t1)), label, tempo, cond); x = x + (t1 - t0) * 0.5 * (v + v2)
        else:
            x = x + (t1 - t0) * v
    return x


def n_params(m, trainable_only=False):
    return sum(p.numel() for p in m.parameters() if (p.requires_grad or not trainable_only))
