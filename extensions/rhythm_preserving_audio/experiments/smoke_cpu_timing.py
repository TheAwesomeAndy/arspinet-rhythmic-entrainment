#!/usr/bin/env python3
"""CPU feasibility smoke test (ENGINEERING ONLY, not an experiment): load small-music-base through the
official package, encode / decode one synthetic source with SAME-S, and time audio-to-audio sampling at
one noise level, with ZERO text embeddings (no text encoder available yet). Measures seconds per sampler
step, encode and decode time, peak RSS. Outputs are not scored and not used anywhere.
"""
import json, os, resource, sys, time
import torch

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, os.path.join(ROOT, 'src'))
import synthetic_audio as sa, model as mdl


def main(steps=8, tempo=2.0):
    t0 = time.time(); sam, text = mdl.load_base(t5_dir=None, threads=4); t_load = time.time() - t0
    counts = mdl.parameter_counts(sam)
    comp = sa.Composition('H01', 20, tempo); x, gt = sa.render(comp); audio = torch.from_numpy(x)
    with torch.inference_mode():
        t0 = time.time(); z = sam.same.encode(audio[None].float()); t_enc = time.time() - t0
        t0 = time.time(); y = sam.same.decode(z); t_dec = time.time() - t0
    dur = comp.duration_s
    cond = sam.model.conditioner([{'seconds_total': dur}], 'cpu')
    cond['prompt'] = (torch.zeros(1, 1, 768), torch.ones(1, 1, dtype=torch.bool))
    t0 = time.time()
    out = sam.generate(conditioning_tensors=cond, duration=dur, steps=steps, init_audio=(sa.SR, audio), init_noise_level=0.5, seed=0, duration_padding_sec=0.0)
    t_gen = time.time() - t0
    rec = {'label': 'ENGINEERING smoke test, zero text embeddings; outputs not scored', 'params': counts, 'text_encoder': text,
           'load_s': t_load, 'clip_s': dur, 'latent_shape': list(z.shape), 'encode_s': t_enc, 'decode_s': t_dec,
           'a2a_steps': steps, 'a2a_total_s': t_gen, 'a2a_s_per_step_upper_bound': t_gen / steps, 'out_shape': list(out.shape),
           'peak_rss_gb': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6, 'torch_threads': torch.get_num_threads()}
    os.makedirs(os.path.join(ROOT, 'results'), exist_ok=True)
    json.dump(rec, open(os.path.join(ROOT, 'results', 'smoke_cpu_timing.json'), 'w'), indent=1); print(json.dumps(rec, indent=1))


if __name__ == '__main__':
    main()
