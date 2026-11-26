"""SAME-S autoencoder (pretrained, from the small-music-base checkpoint) for encoding / decoding audio.

Used by the fallback rectified-flow model and as the reconstruction control (encode -> decode, no
generative model). Weights: the pretransform.model.* tensors of the base checkpoint (see model.py).
Latent: 256 channels at sr / 4096 frames per second (about 10.8 Hz at 44.1 kHz).
"""
from __future__ import annotations

import numpy as np
import torch

import model as mdl

_AE = None


def autoencoder():
    global _AE
    if _AE is None:
        from stable_audio_3.loading_utils import load_autoencoder
        import json, tempfile, os
        cfg = json.load(open(mdl.BASE_CONFIG)); ae_cfg = {'model': cfg['model']['pretransform']['config'], 'sample_rate': cfg['sample_rate']}
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f: json.dump(ae_cfg, f); path = f.name
        _AE = load_autoencoder(path, mdl.BASE_CKPT, device='cpu').eval().float(); os.unlink(path)
    return _AE


@torch.inference_mode()
def encode(audio: np.ndarray) -> np.ndarray:
    """(2, n) float32 audio at 44.1 kHz -> (256, frames) float32 latent."""
    return autoencoder().encode(torch.from_numpy(np.ascontiguousarray(audio))[None].float())[0].numpy()


@torch.inference_mode()
def decode(z: np.ndarray, n_samples: int | None = None) -> np.ndarray:
    y = autoencoder().decode(torch.from_numpy(np.asarray(z, np.float32))[None])[0].numpy()
    return y[:, :n_samples] if n_samples else y
