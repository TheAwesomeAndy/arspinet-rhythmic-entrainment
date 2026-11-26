#!/usr/bin/env python3
"""Unit tests for the rectified-flow implementation (objective, sampler, editing path)."""
import os, sys, unittest
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(os.path.dirname(HERE), 'src'))
import rf_model as rf


class Oracle(torch.nn.Module):
    """Exact velocity for a point-mass data distribution at mu: v(x, t) = (x - mu) / t (the straight path)."""
    def __init__(self, mu): super().__init__(); self.mu = mu
    def forward(self, x, t, label, tempo, cond=None): return (x - self.mu) / t[:, None, None].clamp_min(1e-6)


class RF(unittest.TestCase):
    def test_target_is_eps_minus_x0(self):
        torch.manual_seed(0); net = rf.VelocityNet(ch=4, hidden=16, emb=32, dilations=(1,))
        x0 = torch.randn(3, 4, 10); lab = torch.zeros(3, dtype=torch.long); tem = torch.full((3,), 2.0)
        g = torch.Generator().manual_seed(1); loss, t = rf.rf_loss(net, x0, lab, tem, generator=g)
        g = torch.Generator().manual_seed(1); t2 = torch.sigmoid(torch.randn(3, generator=g)); eps = torch.randn(x0.shape, generator=g)
        # zero-initialised output layer: prediction 0, so the loss is ||eps - x0||^2 exactly
        self.assertTrue(torch.allclose(t, t2)); self.assertAlmostEqual(float(loss), float(((eps - x0) ** 2).mean()), places=5)

    def test_euler_exact_on_straight_path(self):
        mu = torch.randn(1, 4, 8); x = rf.sample(Oracle(mu), (1, 4, 8), None, None, steps=7)
        self.assertTrue(torch.allclose(x, mu, atol=1e-5))

    def test_sdedit_zero_strength_returns_source(self):
        src = torch.randn(1, 4, 8); net = rf.VelocityNet(ch=4, hidden=16, emb=32, dilations=(1,))
        x = rf.sample(net, (1, 4, 8), torch.zeros(1, dtype=torch.long), torch.ones(1), t_start=1e-9, x_init=src, steps=32)
        self.assertTrue(torch.allclose(x, src, atol=1e-6))

    def test_learns_two_point_mixture(self):
        """Train on a 1-D two-point distribution; samples land near the two points in equal proportion."""
        torch.manual_seed(0); net = rf.VelocityNet(ch=1, hidden=32, emb=32, dilations=(1, 1)); opt = torch.optim.Adam(net.parameters(), 3e-3)
        lab = torch.zeros(256, dtype=torch.long); tem = torch.ones(256)
        for _ in range(800):
            x0 = (torch.randint(0, 2, (256, 1, 1)).float() * 4 - 2); loss, _ = rf.rf_loss(net, x0, lab, tem); opt.zero_grad(); loss.backward(); opt.step()
        x = rf.sample(net, (512, 1, 1), torch.zeros(512, dtype=torch.long), torch.ones(512), steps=50, method='heun', seed=3).flatten()
        self.assertLess(float((x.abs() - 2).abs().median()), 0.3); self.assertAlmostEqual(float((x > 0).float().mean()), 0.5, delta=0.1)

    def test_param_count_reported(self):
        self.assertGreater(rf.n_params(rf.VelocityNet(cond_ch=256)), 1_000_000)


if __name__ == '__main__':
    unittest.main(verbosity=2)
