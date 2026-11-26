"""Procedurally generated rhythmic music with exact ground truth (no licensed audio).

A *composition* is fixed by (template, melody_seed, tempo_hz, instrumentation). The rendering is
deterministic given those plus a render seed (small amplitude/timbre randomisation). Every event's
onset time is known exactly; beats are the quarter-note grid.

Fixed-cycle-count rule (docs/CYCLE_COUNT_CONTROL.md): every excerpt holds the same number of beats
(N_BEATS), so its duration is N_BEATS / tempo_hz. Comparisons across tempi are therefore made on
equal numbers of beat cycles, not equal durations.

Splits are by rhythmic template (and melody seed): no template, and therefore no composition or
alternative render of a composition, appears in more than one of train / val / test.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field

import numpy as np

SR = 44100
N_BEATS = 16                 # 4 bars of 4/4; fixed cycle count per excerpt
SUB = 4                      # 16th-note grid: 4 subdivisions per beat
TAIL_S = 0.6                 # release tail after the last beat cycle
TEMPI_HZ = (1.0, 1.5, 2.0, 2.5, 3.0, 4.0)   # 60-240 BPM, the 1-4 Hz range of the EEG study

# One bar = 4 beats x 4 subdivisions = 16 steps. 'x' = hit. Templates are the unit of the split.
TEMPLATES = {
    # train
    'T01': {'kick': 'x...x...x...x...', 'snare': '....x.......x...', 'hat': 'x.x.x.x.x.x.x.x.', 'note': 'x...x...x...x...'},
    'T02': {'kick': 'x.....x.x.......', 'snare': '....x.......x...', 'hat': '..x...x...x...x.', 'note': 'x..x..x...x..x..'},
    'T03': {'kick': 'x...x...x...x...', 'snare': '........x.......', 'hat': 'xxxxxxxxxxxxxxxx', 'note': 'x.x.x.x.x.x.x.x.'},
    'T04': {'kick': 'x.......x.x.....', 'snare': '....x..x....x...', 'hat': 'x...x...x...x...', 'note': 'x.....x.....x...'},
    'T05': {'kick': 'x..x..x.x..x..x.', 'snare': '....x.......x...', 'hat': 'x.x.x.x.x.x.x.x.', 'note': 'x...x..x..x.x...'},
    'T06': {'kick': 'x...x...x...x...', 'snare': '..x...x...x...x.', 'hat': '................', 'note': 'x.x...x.x...x...'},
    # val
    'V01': {'kick': 'x.....x...x.....', 'snare': '....x.......x..x', 'hat': 'x.x.x.x.x.x.x.x.', 'note': 'x...x...x..x....'},
    'V02': {'kick': 'x...x...x...x...', 'snare': '....x.......x...', 'hat': '.x.x.x.x.x.x.x.x', 'note': 'x..x...x..x...x.'},
    # test
    'H01': {'kick': 'x...x...x...x...', 'snare': '....x.......x...', 'hat': 'x.xxx.xxx.xxx.xx', 'note': 'x.....x.x.....x.'},
    'H02': {'kick': 'x..x....x..x....', 'snare': '....x.......x...', 'hat': 'x.x.x.x.x.x.x.x.', 'note': 'x...x.x...x.x...'},
    'H03': {'kick': 'x.......x.......', 'snare': '....x.......x...', 'hat': 'x.x.x.x.x.x.x.x.', 'note': 'x.x.x...x.x.x...'},
    'H04': {'kick': 'x...x...x..xx...', 'snare': '....x.......x...', 'hat': 'x...x...x...x...', 'note': 'x..x..x.x..x..x.'},
}
SPLITS = {'train': ['T01', 'T02', 'T03', 'T04', 'T05', 'T06'], 'val': ['V01', 'V02'], 'test': ['H01', 'H02', 'H03', 'H04']}

SCALES = {'minor_pent': [0, 3, 5, 7, 10], 'major': [0, 2, 4, 5, 7, 9, 11], 'dorian': [0, 2, 3, 5, 7, 9, 10]}
INSTRUMENTATIONS = {
    'electronic': {'tonal': 'saw_pluck', 'bright': 1.0, 'perc': True},
    'acoustic':   {'tonal': 'ks_pluck', 'bright': 0.6, 'perc': True},
    'tonal_only': {'tonal': 'sine_bell', 'bright': 0.4, 'perc': False},
}


@dataclass
class Composition:
    template: str
    melody_seed: int
    tempo_hz: float
    instrumentation: str = 'electronic'
    scale: str = 'minor_pent'
    root_midi: int = 57
    n_beats: int = N_BEATS
    nonperiodic: bool = False      # A2 probe: sparse, non-repeating pattern (see nonperiodic_pattern)

    @property
    def cid(self) -> str:
        return f'{self.template}{"NP" if self.nonperiodic else ""}_m{self.melody_seed}_f{self.tempo_hz:g}_{self.instrumentation}'

    @property
    def duration_s(self) -> float:
        return self.n_beats / self.tempo_hz + TAIL_S


def midi_hz(m):
    return 440.0 * 2 ** ((np.asarray(m, float) - 69) / 12)


# ---------------------------------------------------------------------------------------------
# instruments (mono, float64); each returns a short event waveform
def _env(n, attack_s, decay_s, sr=SR):
    t = np.arange(n) / sr; a = np.clip(t / max(attack_s, 1e-4), 0, 1); return a * np.exp(-t / decay_s)


def kick(rng, sr=SR, bright=1.0):
    n = int(0.35 * sr); t = np.arange(n) / sr
    f = 45 + 110 * np.exp(-t / 0.03); ph = 2 * np.pi * np.cumsum(f) / sr
    return np.sin(ph) * _env(n, 0.001, 0.12) * (0.9 + 0.1 * rng.rand())


def snare(rng, sr=SR, bright=1.0):
    n = int(0.25 * sr); t = np.arange(n) / sr
    noise = rng.randn(n); noise = np.convolve(noise, [1, -0.6 * bright], 'same')
    body = np.sin(2 * np.pi * 190 * t) * np.exp(-t / 0.05)
    return (0.55 * noise * _env(n, 0.001, 0.07) + 0.45 * body) * (0.85 + 0.15 * rng.rand())


def hat(rng, sr=SR, bright=1.0):
    n = int(0.06 * sr); x = rng.randn(n); x = np.diff(np.concatenate([[0], x]))       # crude high-pass
    return 0.35 * bright * x * _env(n, 0.0005, 0.018) * (0.8 + 0.2 * rng.rand())


def tonal(kind, f0, dur_s, rng, sr=SR, bright=1.0):
    n = int(dur_s * sr); t = np.arange(n) / sr
    if kind == 'saw_pluck':
        nh = int(np.clip(6 + 14 * bright, 2, 40)); x = sum(np.sin(2 * np.pi * k * f0 * t) / k * np.exp(-t * k * 3 / max(bright, 0.2)) for k in range(1, nh + 1))
        return 0.5 * x * _env(n, 0.003, 0.35)
    if kind == 'ks_pluck':                      # Karplus-Strong string
        p = max(int(sr / f0), 2); buf = rng.uniform(-1, 1, p); out = np.empty(n); damp = 0.996 - 0.01 * (1 - bright)
        for i in range(n):
            out[i] = buf[i % p]; buf[i % p] = damp * 0.5 * (buf[i % p] + buf[(i + 1) % p])
        return 0.6 * out * _env(n, 0.002, 0.6)
    if kind == 'sine_bell':
        x = np.sin(2 * np.pi * f0 * t) + 0.3 * bright * np.sin(2 * np.pi * 2.76 * f0 * t) * np.exp(-t / 0.15)
        return 0.6 * x * _env(n, 0.004, 0.45)
    raise ValueError(kind)


# ---------------------------------------------------------------------------------------------
NP_DENSITY = 0.22   # fraction of 16th steps carrying an event in the nonperiodic probe (all instruments together)


def nonperiodic_pattern(comp: Composition):
    """A2 probe stimulus: one non-repeating event sequence over the whole excerpt (no bar repeats), sparse
    (about NP_DENSITY of the 16th steps; every bar's first beat kept so the meter stays audible; no two
    adjacent 16ths), events assigned to kick / snare / note by a fixed draw, no hats. Fixed by (template,
    melody_seed). Sparse and aperiodic so that a displaced copy rarely lands on other events."""
    rng = np.random.RandomState(10_000 + 97 * list(TEMPLATES).index(comp.template) + comp.melody_seed); n = comp.n_beats * SUB
    on = rng.rand(n) < NP_DENSITY; on[::SUB * 4] = True
    for i in range(1, n):
        if on[i] and on[i - 1]: on[i] = False
    inst = rng.choice(['kick', 'snare', 'note'], size=n, p=[0.35, 0.25, 0.40]); inst[::SUB * 4] = 'kick'
    pats = {k: ''.join('x' if (on[i] and inst[i] == k) else '.' for i in range(n)) for k in ('kick', 'snare', 'note')}
    pats['hat'] = '.' * n; return pats


def event_times(comp: Composition, jitter_s=0.0, drop_frac=0.0, rng=None):
    """Per instrument, onset times (s) of every hit in the excerpt; optional Gaussian timing jitter
    and random event removal (for metric controls only)."""
    tpl = nonperiodic_pattern(comp) if comp.nonperiodic else TEMPLATES[comp.template]; step = 1.0 / (comp.tempo_hz * SUB); n_steps = comp.n_beats * SUB
    rng = rng or np.random.RandomState(0); out = {}
    for inst, pat in tpl.items():
        idx = [i for i in range(n_steps) if pat[i % len(pat)] == 'x']
        t = np.array(idx, float) * step
        if jitter_s > 0: t = t + rng.randn(len(t)) * jitter_s
        if drop_frac > 0 and len(t): t = t[rng.rand(len(t)) >= drop_frac]
        out[inst] = np.sort(np.clip(t, 0, None))
    return out


def render(comp: Composition, render_seed=0, jitter_s=0.0, drop_frac=0.0, time_scale=1.0, instrumentation=None, shift_s=0.0):
    """Render the composition. Returns (audio float32 (2, n) stereo, ground truth dict).

    jitter_s / drop_frac / time_scale / shift_s / instrumentation are used only to build metric controls:
    the ground truth always describes the UNPERTURBED composition (the reference), while the audio carries
    the perturbation. time_scale > 1 slows the excerpt (tempo / time_scale)."""
    rng = np.random.RandomState(render_seed); mrng = np.random.RandomState(comp.melody_seed)
    inst = INSTRUMENTATIONS[instrumentation or comp.instrumentation]
    ev = event_times(comp, jitter_s, drop_frac, np.random.RandomState(render_seed + 1000))
    dur = comp.duration_s * time_scale + abs(shift_s); n = int(dur * SR); y = np.zeros(n)
    scale = SCALES[comp.scale]; degrees = mrng.randint(0, len(scale), size=4096); octs = mrng.choice([0, 0, 12], size=4096)

    def place(x, t):
        i = int(round((t * time_scale + shift_s) * SR))
        if i < 0 or i >= n: return
        m = min(len(x), n - i); y[i:i + m] += x[:m]

    if inst['perc']:
        for t in ev['kick']: place(kick(rng, bright=inst['bright']), t)
        for t in ev['snare']: place(0.8 * snare(rng, bright=inst['bright']), t)
        for t in ev['hat']: place(hat(rng, bright=inst['bright']), t)
    step = 1.0 / (comp.tempo_hz * SUB)
    for j, t in enumerate(ev['note']):
        f0 = midi_hz(comp.root_midi + scale[degrees[j]] + octs[j])
        place(0.7 * tonal(inst['tonal'], f0, min(0.9, 3.5 * step + 0.15), rng, bright=inst['bright']), t)
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.7
    gt = ground_truth(comp)
    return np.stack([y, y]).astype(np.float32), gt


def ground_truth(comp: Composition):
    """Reference timing of the unperturbed composition: beats (quarter notes), downbeats, and all onsets
    (union over instruments, merged within 20 ms)."""
    beats = np.arange(comp.n_beats) / comp.tempo_hz
    ev = event_times(comp); allo = np.sort(np.concatenate([v for v in ev.values() if len(v)]))
    merged = [allo[0]]
    for t in allo[1:]:
        if t - merged[-1] > 0.02: merged.append(t)
    perc = np.sort(np.concatenate([ev[k] for k in ('kick', 'snare') if len(ev[k])])) if INSTRUMENTATIONS[comp.instrumentation]['perc'] else np.array([])
    return {'beats_s': beats.tolist(), 'downbeats_s': beats[::4].tolist(), 'onsets_s': list(map(float, merged)),
            'tempo_hz': comp.tempo_hz, 'tempo_bpm': 60 * comp.tempo_hz, 'n_beats': comp.n_beats, 'duration_s': comp.duration_s,
            'kick_snare_s': perc.tolist()}


def caption(comp: Composition, style=None):
    """Text description used for conditioning (tempo, instrumentation, pattern)."""
    inst = {'electronic': 'electronic drums and a bright synth pluck', 'acoustic': 'acoustic drum kit and a plucked guitar-like string',
            'tonal_only': 'soft bell-like tones without drums'}[comp.instrumentation]
    return f'{style + ", " if style else ""}steady {round(60 * comp.tempo_hz)} BPM groove in 4/4 with {inst}, tight and on the beat'


def compositions(split: str, tempi=TEMPI_HZ, melody_seeds=(0,), instrumentations=('electronic',), nonperiodic=False):
    return [Composition(t, s, f, i, nonperiodic=nonperiodic) for t in SPLITS[split] for s in melody_seeds for f in tempi for i in instrumentations]


def write_wav(path, audio, sr=SR):
    from scipy.io import wavfile
    wavfile.write(path, sr, np.asarray(audio, np.float32).T)


def read_wav(path):
    from scipy.io import wavfile
    sr, x = wavfile.read(path); x = x.astype(np.float32)
    if x.dtype.kind == 'i' or np.abs(x).max() > 2: x = x / 32768.0
    x = x.T if x.ndim == 2 else x[None]
    return sr, x
