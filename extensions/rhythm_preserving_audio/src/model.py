"""Loading Stable Audio 3 small-music-base from local files, through the official package.

Weights: stabilityai/stable-audio-3-small-music-base model.safetensors (fp32, sha256
79691fac2a08a99a229b98963f8377ddc78c16f5c63f7e3a022375c311093ab4), stored on disk as bf16 because of the
session's disk allowance and upcast to fp32 in memory on load (copy_state_dict -> load_state_dict casts to
the fp32 parameters). This differs from the official fp32 weights by bf16 rounding; recorded in
MODEL_CARD.md. Everything else (architecture, sampler, LoRA) is the official code at commit 4007b6f.

Text encoder: T5Gemma (google/t5gemma-b-b-ul2, redistributed in the gated stabilityai/stable-audio-3-
small-music repo, subfolder t5gemma-b-b-ul2). Pass its local directory as t5_dir. With t5_dir=None the
prompt conditioner is left out and only the precomputed-tensor path works; that mode exists solely for the
CPU timing smoke test (no text conditioning, no experimental result).
"""
from __future__ import annotations

import copy
import json
import os

import torch

MODEL_DIR = os.environ.get('RPA_MODEL_DIR', '/home/user/models/sa3')
BASE_CKPT = os.path.join(MODEL_DIR, 'base_bf16.safetensors')
BASE_CONFIG = os.path.join(MODEL_DIR, 'base_config.json')
T5_DIR = os.path.join(MODEL_DIR, 't5gemma-b-b-ul2')


def load_config(t5_dir=T5_DIR):
    cfg = json.load(open(BASE_CONFIG)); cfg = copy.deepcopy(cfg); confs = cfg['model']['conditioning']['configs']
    if t5_dir and os.path.isdir(t5_dir):
        for c in confs:
            if c['type'] == 't5gemma':
                c['config'].pop('repo_id', None); c['config'].pop('subfolder', None); c['config']['model_path'] = t5_dir
        return cfg, True
    cfg['model']['conditioning']['configs'] = [c for c in confs if c['type'] != 't5gemma']
    return cfg, False


def load_base(t5_dir=T5_DIR, device='cpu', threads=None):
    """Returns (StableAudioModel, text_enabled)."""
    if threads: torch.set_num_threads(threads)
    from stable_audio_3.loading_utils import load_diffusion_cond
    from stable_audio_3.model import StableAudioModel
    cfg, text = load_config(t5_dir)
    m = load_diffusion_cond(cfg, BASE_CKPT, device=device, model_half=False)
    m.use_lora = False; m.lora_names = []
    return StableAudioModel(m, cfg, device, False), text


def parameter_counts(sam):
    m = sam.model; tot = lambda mod: sum(p.numel() for p in mod.parameters())
    return {'dit': tot(m.model), 'pretransform': tot(m.pretransform), 'conditioner': tot(m.conditioner), 'total': tot(m)}
