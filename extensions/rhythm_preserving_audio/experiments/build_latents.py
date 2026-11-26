#!/usr/bin/env python3
"""Synthesise the fallback dataset and encode it with SAME-S.

Pairs: electronic render (source) and acoustic re-synthesis (target) of the SAME composition, so the target
has exactly the source's event times. Splits by template (DECISION_RULES.md):
  train : T01-T06, melody seeds 0-2, 6 tempi, periodic and nonperiodic
  val   : V01-V02, melody seed 10, 6 tempi, both families
  test  : H01-H04, melody seed 20, tempi 2.0 and 3.0, both families (the frozen evaluation set)
Latents go to results/latents/<split>.npz (git-ignored); results/latents_manifest.json is committed.
"""
import json, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, os.path.join(ROOT, 'src'))
import synthetic_audio as sa, latents as la

SPEC = {'train': dict(seeds=(0, 1, 2), tempi=sa.TEMPI_HZ), 'val': dict(seeds=(10,), tempi=sa.TEMPI_HZ), 'test': dict(seeds=(20,), tempi=(2.0, 3.0))}
LABELS = {'electronic': 0, 'acoustic': 1, 'tonal_only': 2}


def main():
    out = os.path.join(ROOT, 'results', 'latents'); os.makedirs(out, exist_ok=True); manifest = {}; t0 = time.time()
    for split, sp in SPEC.items():
        items = []
        for np_ in (False, True):
            for c in sa.compositions(split, tempi=sp['tempi'], melody_seeds=sp['seeds'], nonperiodic=np_):
                xs, _ = sa.render(c); xt, _ = sa.render(c, instrumentation='acoustic')
                items.append({'cid': c.cid, 'template': c.template, 'nonperiodic': np_, 'tempo_hz': c.tempo_hz, 'melody_seed': c.melody_seed,
                              'n_samples': xs.shape[1], 'z_src': la.encode(xs), 'z_tgt': la.encode(xt)})
        np.savez(os.path.join(out, f'{split}.npz'), **{f'{i}_src': it['z_src'] for i, it in enumerate(items)}, **{f'{i}_tgt': it['z_tgt'] for i, it in enumerate(items)})
        manifest[split] = [{k: v for k, v in it.items() if not k.startswith('z_')} | {'frames': int(it['z_src'].shape[1])} for it in items]
        print(split, len(items), f'({time.time() - t0:.0f}s)', flush=True)
    tr = set(m['template'] for m in manifest['train']); va = set(m['template'] for m in manifest['val']); te = set(m['template'] for m in manifest['test'])
    assert not (tr & va or tr & te or va & te), 'template leakage across splits'
    json.dump({'labels': LABELS, 'spec': {k: {'seeds': v['seeds'], 'tempi': v['tempi']} for k, v in SPEC.items()}, 'splits': manifest}, open(os.path.join(ROOT, 'results', 'latents_manifest.json'), 'w'), indent=1)


if __name__ == '__main__':
    main()
