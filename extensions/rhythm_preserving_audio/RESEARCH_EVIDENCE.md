# Research evidence: rhythm-preserving generative audio editing

Prepared 2026-11-26 from the completed work on branch `extension/rhythm-preserving-audio` of
`TheAwesomeAndy/arspinet-rhythmic-entrainment` (pushed and then merged into `main` at `a78d143`, see section 6). Every number below is read from a committed result file named
next to it. Evidence labels: **measured** (metrics on actual model outputs), **simulated** (synthetic controls),
**proposal** (not run), **interpretation**.

**Authorship.** The research question, the decision to treat timing preservation as a measurement problem, the
request to test whether timing measures alias on periodic grids, the suggestion of nonperiodic and
order-preserving controls, the CPU-only fallback, the narrow scope and the EDGE governance came from the author. The code, experiment execution and first drafts of the analyses were produced by an AI assistant
(Claude) working under that direction in this session. Andrew Lane directed the research question, experimental design, metric calibration,
and evaluation decisions. An AI coding agent implemented, trained, and executed the
experiments under that direction. Contributions are documented in the sections below.

**One-paragraph verdict.** Stable Audio 3 was audited and its flow-matching base checkpoint loaded and timed on
CPU, but no Stable Audio 3 edit or LoRA run could be performed (gated text encoder; the access token supplied to
the session is rejected). As a pre-planned fallback, two small conditional rectified-flow editors (about 2.8 M
parameters each) were implemented from scratch and trained on synthetic paired audio in the latent space of
Stability AI's pretrained SAME-S autoencoder. Under decision rules frozen before any model output was scored, the
source-conditioned editor (V1) preserved event timing better than the label-conditioned SDEdit-style editor (V0)
at matched spectral change: +0.206 floor-normalised onset F1 at the median matched point, 95 % CI
[0.132, 0.283], 8 of 8 held-out compositions (measured; exploratory, synthetic, n = 8). Beat-alignment and tempo
measures were not computed in the held-out evaluation.

---

## 1. Architecture and generative modelling

### 1.1 What was implemented (from scratch) — `src/rf_model.py`

**Objective: rectified flow (a flow-matching objective).** Data at t = 0, Gaussian noise at t = 1, straight path

  x_t = (1 − t) x₀ + t ε,  ε ~ N(0, I),

with constant velocity dx_t/dt = ε − x₀. The network v_θ(x_t, t, c) is trained by regression onto that velocity:

  L(θ) = E_{x₀, ε, t} ‖ v_θ(x_t, t, c) − (ε − x₀) ‖²,  t = sigmoid(n), n ~ N(0, 1) (logit-normal).

This is the same convention as Stable Audio 3's `rectified_flow` objective (verified in its training code). It is
**not** a diffusion objective: there is no noise-prediction or v-prediction target on a variance-preserving
schedule, no stochastic reverse SDE and no score function; sampling integrates a deterministic ODE. (Rectified
flow and diffusion are related, and a diffusion ODE can be written as a flow, but the two terms are not used
interchangeably here.)

**Velocity network (`VelocityNet`).** A fully convolutional 1-D residual network over the latent sequence:

* input: 1×1 convolution from 256 latent channels (+256 source-latent channels in V1) to 192 hidden channels;
* 8 residual blocks, each GroupNorm(8) → FiLM → SiLU → dilated Conv1d(k = 3; dilations 1, 2, 4, 8, 1, 2, 4, 8)
  → GroupNorm → SiLU → Conv1d(k = 3), with a residual connection; receptive field 77 latent frames
  (about 7.0 s at 10.93 frames/s);
* conditioning embedding (256-d) = MLP(sinusoidal features of t) + learned embedding of the target-instrument
  label + linear map of sinusoidal features of the tempo (Hz); injected into every block by FiLM (per-channel
  scale and shift);
* output: 1×1 convolution back to 256 channels, zero-initialised (the network starts by predicting zero velocity).

**Numerical sampling.** Explicit Euler integration of dx/dt = v_θ from t_start to 0 on a uniform grid with
round(32 · t_start) steps (32 steps over the full interval); Heun (second-order) is implemented and unit-tested but
was not used in the evaluation. **Editing** is SDEdit-style (Meng et al. 2021, to be verified): the source latent is
noised to x_{t_start} = (1 − t_start) x_src + t_start ε, then integrated to 0. t_start is the editing strength
(0 = identity, 1 = generation from pure noise), the analogue of Stable Audio 3's `init_noise_level`.

### 1.2 V0 vs V1 (identical except for the source input)

| | V0 "label" | V1 "paired" |
|---|---|---|
| conditioning | target-instrument label, tempo | label, tempo, **source latent concatenated on the channel axis** |
| training data | every latent as its own example (electronic renders labelled 0, acoustic renders labelled 1): 432 examples | pairs: x₀ = acoustic render, condition = electronic render of the same composition: 216 examples |
| how it edits | only through SDEdit noising of the source | SDEdit noising **and** the source latent at every network evaluation |
| parameters (all trainable) | 2,815,936 | 2,865,088 |

Rhythm is not given to either network as a separate input: there is no beat grid, onset track or rhythm loss.
Tempo enters only as a scalar embedding. V1's access to timing comes from the source latent itself.

### 1.3 Pretrained components used (adapted, not trained)

* **SAME-S autoencoder** (Stability AI, from `stabilityai/stable-audio-3-small-music-base`, 108.2 M parameters,
  frozen): 44.1 kHz stereo ↔ 256 × (10.93 Hz) latents. The rectified-flow models operate entirely in this latent
  space. Reconstruction control (measured, `results/reconstruction_control.json`): encode → decode preserves timing
  (nonperiodic probe floor-normalised onset F1 0.939 vs 0.945 for the untouched audio; 0.7 dB LTAS colouration).
* **Stable Audio 3 small-music-base** (459.1 M-parameter DiT, `rectified_flow` objective per its config): audited,
  loaded through the official package and timed on CPU with zero text embeddings (engineering smoke test only,
  `results/smoke_cpu_timing.json`: about 3.3 s per sampler step for an 8.6 s clip, 4 cores, 3.8 GB RAM). **No Stable
  Audio 3 edit was generated with a real prompt, scored or fine-tuned.**

### 1.4 Technologies

Python 3.13; PyTorch 2.7.1 (CPU), torchaudio 2.7.1; NumPy 2.5.5; SciPy 1.18.1 (STFT, filtering, statistics);
matplotlib; mir_eval 0.8.2 (cross-check of onset F-measure); safetensors; Hugging Face Hub; the official
`stable-audio-3` package (commit `4007b6f`) for loading SAME-S and the DiT; transformers 5.24.1 and
pytorch_lightning 2.5.5 installed for the Stable Audio 3 path but not exercised in a training run.

### 1.5 Implemented vs proposed

Implemented and executed: rectified-flow objective, velocity network, label / tempo / source-latent conditioning,
Euler sampling, SDEdit-style editing, training, held-out evaluation, metric suite, controls.
Implemented, not executed in results: Heun sampler (unit-tested only), Stable Audio 3 prompt-based editing path.
Proposed only: Stable Audio 3 LoRA fine-tuning, inpainting-based source-conditioned LoRA, explicit beat-grid
conditioning, rhythm-aware auxiliary loss, training-free latent guidance.

## 2. Training evidence (measured, `results/rf_training.json`)

* **Data** (`experiments/build_latents.py`, `results/latents_manifest.json`): procedurally synthesised music,
  no recorded or licensed audio. 12 rhythmic templates (kick / snare / hat / tonal-note patterns) split **by
  template**: train T01–T06 (melody seeds 0–2), validation V01–V02 (seed 10), test H01–H04 (seed 20). Each
  composition exists in two stimulus families (periodic: one bar repeated; nonperiodic: sparse non-repeating
  sequence) and is rendered twice with identical event times (electronic source, acoustic target). Tempi
  1.0–4.0 Hz; every excerpt holds exactly 16 beats (fixed-cycle-count rule). Train 216 compositions, validation 24,
  test 16 (tempi 2.0 and 3.0 Hz only). A leakage assertion (no template in two splits) passed.
* **Optimisation (both)**: AdamW (lr 2e-4, weight decay 0.01), batch 32 random 32-frame crops (about 2.9 s),
  gradient clipping 1.0, EMA 0.999 (EMA weights used for validation and evaluation), seed 0, **6000 steps
  completed**, CPU (4 threads).

| | V0 | V1 |
|---|---|---|
| training examples | 432 | 216 |
| train MSE, first 50 steps → last 50 steps | 1.832 → 0.809 | 1.718 → 0.585 |
| validation MSE (held-out templates, fixed t and noise), step 500 → 6000 | 1.902 → 1.025 | 1.788 → 0.781 |
| parameter tensors changed by training | 91 / 91 | 91 / 91 |
| wall time | 444 s | 439 s |
| peak RSS | about 0.6 GB | about 0.6 GB |
| checkpoint | `checkpoints/rf_V0.pt` (local, git-ignored, 11 MB) | `checkpoints/rf_V1.pt` (local, git-ignored) |

Validation loss fell monotonically and was still decreasing at 6000 steps for both models (no sign of
over-fitting at the loss level, and no claim of convergence). No instability (NaN, divergence) occurred. The two
validation losses are **not comparable** (V0 also models the electronic renders, V1 predicts only acoustic targets
given the source), and a lower loss is not evidence of better edits; the held-out evaluation below is.

## 3. Held-out results (measured, `results/rf_eval.json`, frozen `DECISION_RULES.md`)

**Protocol.** 16 held-out compositions (H01–H04 × 2 tempi × 2 families), each edited electronic → acoustic by V0
and V1 at strengths 0.1, 0.3, 0.5, 0.7, 0.9, 1.0 with 3 seeds (576 edits), plus 4 reference points per composition
(identity, SAME-S reconstruction, oracle acoustic re-synthesis, DSP low-pass 1500 Hz). Seeds are averaged within a
composition; the composition is the unit. All group results are exploratory (8 compositions per family, built from
4 templates at 2 tempi, so the 8 are not fully independent).

**Measures.** D1 (primary): onsets detected in the edited audio vs ground-truth onsets (±50 ms), as
floor-normalised F1 = (F1 − alias floor)/(1 − alias floor), on the nonperiodic probe family; "timing preserved"
requires D1 ≥ 0.5, lag-0 specificity > 0 and |best global lag| ≤ 50 ms. T1: timing-blind change of spectral
shape (long-term-average log-mel distance from the source, dB). Editing fidelity: LTAS distance to the oracle
acoustic target.

### 3.1 Primary decision: matched transformation, nonperiodic probe (8 compositions)

| matched T1 (dB) | V1 − V0 in D1, mean | 95 % CI (bootstrap) | compositions with V1 > V0 | Wilcoxon p |
|---|---|---|---|---|
| 1.63 (25th pct) | +0.094 | [0.043, 0.156] | 8 / 8 | 0.0078 |
| **2.29 (median)** | **+0.206** | **[0.132, 0.283]** | 8 / 8 | 0.0078 |
| 2.94 (75th pct) | +0.315 | [0.203, 0.428] | 8 / 8 | 0.0078 |

Per-composition differences at the median point ranged from +0.044 to +0.367. All 8 compositions covered every
grid point for both editors (V1's own T1 range includes the comparison points), so the frozen rule's coverage
condition holds and V1 is not winning by editing less. **Decision under the frozen rule: V1 better** (exploratory).
0.0078 is the smallest two-sided Wilcoxon p attainable with 8 units.

### 3.2 Strength sweep (medians over the 8 probe compositions)

| strength | V0 D1 | V0 T1 dB | V0 dist. to target dB | V1 D1 | V1 T1 dB | V1 dist. to target dB |
|---|---|---|---|---|---|---|
| 0.1 | 0.933 | 0.92 | 3.65 | 0.933 | 1.14 | 3.53 |
| 0.3 | 0.846 | 1.61 | 3.16 | 0.904 | 2.19 | 2.85 |
| 0.5 | 0.702 | 2.29 | 2.50 | 0.869 | 2.99 | 2.17 |
| 0.7 | 0.529 | 3.00 | 1.89 | 0.821 | 3.40 | 1.79 |
| 0.9 | −0.060 | 3.46 | 1.97 | 0.780 | 3.49 | 1.62 |
| 1.0 | −0.377 | 6.00 | 5.78 | 0.780 | 3.45 | 1.58 |

References (same compositions): identity D1 0.939 (T1 0); SAME-S reconstruction 0.939 (0.70 dB); oracle acoustic
target 0.939 (3.46 dB from the source, 0 to itself); DSP low-pass 1500 Hz 0.939 (32.6 dB).

* **Monotonicity was tested, not assumed.** D1 fell with strength in 8/8 compositions for V0 (sign test
  p = 0.0078; median Spearman ρ −1.00) and in 7/8 for V1 (p = 0.016; ρ −0.97), while T1 rose with strength
  (median ρ 1.00 and 0.94). The trade-off exists for both editors; for V1 it is much shallower (0.93 → 0.78 vs
  0.93 → −0.38).
* **Fraction of outputs with timing preserved** (D1 rule, 24 outputs per strength): V0 0.88 / 1.00 / 0.83 / 0.46 /
  0.00 / 0.00; V1 0.88 / 0.96 / 1.00 / 1.00 / 0.96 / 0.92 at strengths 0.1 → 1.0.
* **Editing fidelity.** V1 at full strength lands 1.58 dB (LTAS) from the oracle target, closer than V0 at any
  strength (best 1.89 dB at 0.7). V0 at full strength over-transforms (6.0 dB from the source, 5.8 dB from the
  target) and loses timing: generation from noise conditioned only on a label carries no information about the
  source's events.
* **Timing precision** (D2, only for preserved outputs): matched-onset deviation 4.7–5.2 ms for V0 (strengths ≤ 0.7)
  and 4.8–5.2 ms for V1, the same as the untouched audio (5.3 ms; the detector's own offset). Best global lag
  within ±4 ms for V1 at every strength.
* **Gap to the ceiling.** Even V1 does not reach the untouched audio (0.78–0.93 vs 0.94): some onsets are lost.

### 3.3 Secondary: periodic family (8 compositions)

V1 kept D1 = 1.00 at every strength; V0 fell to 0.53 at 0.7 and below zero at 0.9–1.0. Matched comparison at the
median point: +0.280, CI [0.074, 0.522], Wilcoxon p = 0.0625 (ties among compositions). On this family the alias
floor is close to 1 (median 0.906), so floor-normalisation is ill-conditioned: V0 at full strength reads −16.2 and
the DSP low-pass −3.5 because a small raw-F1 drop is divided by a small 1 − floor. These values are reported, not
interpreted as magnitudes, which is why the periodic family was frozen as secondary.

### 3.4 Not measured in the held-out evaluation (stated plainly)

* **Beat alignment (informed beat F1) and tempo error** were pre-specified as secondary measures but the
  evaluation script did not compute them for model outputs. They exist in the metric suite and were validated on
  synthetic controls only. Outputs are deterministic (fixed seeds) and can be re-scored; this was not done, to
  avoid a further analysis cycle.
* **Stable Audio 3** (pretrained edit or LoRA): not run (section 8).
* **No perceptual, emotional, neurological or therapeutic outcome** was measured or is implied.

### 3.5 Interpretation (labelled)

The result says that, for this synthetic paired task, conditioning the velocity field on the source latent lets
the flow model change timbre while carrying the source's event timing through, whereas label-only SDEdit editing
trades timing for transformation as the noise level rises. This is close to the expected behaviour of a paired
(supervised translation) model whose targets share the source's timing exactly: the experiment measures and
bounds that advantage with calibrated, alias-aware metrics, it does not show that it transfers to real music,
to unpaired editing or to large pretrained models.

## 4. Research contribution and connection to the EEG work

**Connection.** The EEG study asked what a measurement chain (scalp EEG → linear encoding model → spiking
reservoir) preserves of a stimulus's rhythm, and calibrated every statistic on synthetic signals with known
structure before reading real data. This extension applies the same discipline to a generative editor.

* **Periodic-grid aliasing.** The EEG pre-registration rejected circular-shift and phase-randomisation nulls
  because they are "invariant for magnitude statistics on a periodic grid". Here the same structure defeats
  event-matching timing measures: on the periodic stimuli a copy displaced by a whole beat scored onset F1 0.885
  and a matched-onset deviation of 0.8 ms, better than the untouched audio's 2.5 ms (simulated,
  `results/aliasing_validation.json`). Order-preserving alignment gave identical values; signed displacement was
  also fooled. The remedy in both projects was a design that breaks periodicity (here, sparse nonperiodic probes
  with a measured alias floor, 0.39 vs 0.91), not a cleverer statistic.
* **Temporal identifiability.** The identifiability work showed that on periodic stimuli evoked and oscillator
  accounts produce near-identical beat-locked output. The audio analogue: on a periodic grid, a timing error of a
  whole grid step is not identifiable from event matches.
* **Fixed cycle count.** Every excerpt holds 16 beats regardless of tempo (from the cycle-count control of the EEG
  study), so tempo comparisons are made on equal numbers of cycles; beat-band statistics use a tempo-scaled baseline.
* **Power vs timing.** The EEG study measured beat-locked power. Here the timing-blind spectral measure (LTAS) reads
  0.001 dB for a time-reversed excerpt: preserving spectral power says nothing about event timing, so every
  spectral measure is paired with an event-timing measure.

**Classification.**

| | items |
|---|---|
| Established methods (literature to verify before citing) | rectified flow / flow matching (Liu et al. 2022; Lipman et al. 2022), SDEdit (Meng et al. 2021), FiLM (Perez et al. 2018), spectral-flux onset detection and ±50 / ±70 ms MIR tolerances, dynamic-programming beat tracking (Ellis 2007), Stable Audio 3 (arXiv:2605.17991) |
| Original experimental contributions of this project | the paired synthetic editing benchmark with exact timing ground truth and template-level splits; the matched-transformation comparison rule (rhythm compared at equal spectral change); the measured V0 vs V1 result under frozen rules |
| Possible methodological contributions, needing a literature check | alias-floor normalisation and lag-0 specificity as a correction for periodic-grid aliasing in onset-based evaluation of generative audio; nonperiodic probe stimuli as an evaluation design; pairing a timing-blind spectral measure with alias-aware timing measures |
| Future work (proposal) | the same protocol on Stable Audio 3 (pretrained and LoRA); real recordings with annotated onsets; explicit beat conditioning or rhythm-aware losses; unpaired editing; perceptual validation (would need a human-subjects protocol) |

## 5. Evidence table

| Capability | What was implemented | What was executed | Supporting evidence | Limitations |
|---|---|---|---|---|
| Flow matching | Rectified-flow objective (straight path, velocity target ε − x₀, logit-normal t) from scratch | Two models trained 6000 steps each | `src/rf_model.py`; `tests/test_rf.py` (target exactness, Euler exact on straight path, two-point mixture); `results/rf_training.json` | Small models, synthetic data, CPU |
| Generative audio modelling | Latent flow model over a pretrained audio autoencoder (SAME-S) | Generated and decoded 576 edits | `results/rf_eval.json`; `figures/fig_example.png` | Narrow synthetic domain; no text or open-ended generation |
| Conditional generation | FiLM conditioning on time, label, tempo; channel-concatenated source latent | V0 and V1 trained and evaluated | `src/rf_model.py`; `experiments/train_rf.py` | No text conditioning in the trained models |
| Audio-to-audio editing | SDEdit-style editing with a strength parameter; paired source-conditioned editing | Strength sweep 0.1–1.0 × 3 seeds × 16 compositions | `experiments/eval_rf.py`; `results/rf_eval.json` | Electronic → acoustic timbre edit only |
| Model training | Training loop with AdamW, EMA, gradient clipping, fixed-noise validation loss | 2 runs, losses logged, 91/91 tensors updated | `results/rf_training.json`; `figures/fig_training.png` | Single seed per model; no hyperparameter search |
| PyTorch and NumPy | Network, loss, sampler (PyTorch); synthesis, DSP and metrics (NumPy / SciPy) | All of the above | `src/*.py`; 23 unit tests pass | CPU only |
| Musical structure preservation | Onset, beat and tempo metrics; alias floor, lag specificity; nonperiodic probes | Metric validation on synthetic controls; held-out evaluation on onsets | `results/metric_validation.json`, `results/aliasing_validation.json`, `results/rf_eval.json` | Beat and tempo metrics not computed on model outputs |
| Generative model evaluation | Pre-registered decision rules, matched-transformation comparison, bootstrap CI, Wilcoxon, sign tests, reference points | Run on 16 held-out compositions | `DECISION_RULES.md` (sha256 f4512b15…, frozen in `17063fb` before any output); `results/rf_eval.json` | n = 8 per family, exploratory |
| Controllable audio transformations | Editing strength as a continuous control; DSP baselines | Trade-off curves measured | `figures/fig_tradeoff.png` | One kind of edit |
| Reproducible ML experimentation | Plan and addenda committed before evaluation; frozen rules with hash; seeds; template-level splits; resumable scripts | All results regenerated by scripts | `EXPERIMENT_PLAN.md`; commit history (public, merged into `main`) | Single training seed per model |
| Pretrained model handling (Stable Audio 3) | Primary-source audit; local loader through the official package; bf16 storage | CPU timing smoke test only (zero text embeddings) | `EXPERIMENT_PLAN.md` §2; `src/model.py`; `results/smoke_cpu_timing.json` | No real-prompt edit, no LoRA |

Not demonstrated by this work: diffusion-model training,
LoRA / parameter-efficient fine-tuning, fine-tuning of any pretrained generative model, post-training,
reward modelling, text-to-audio generation.

## 6. Repository verification

* **Branch**: `extension/rhythm-preserving-audio`, **pushed to GitHub on 2026-11-26 with the author's
  authorization** (https://github.com/TheAwesomeAndy/arspinet-rhythmic-entrainment/tree/extension/rhythm-preserving-audio).
  Merged into `main` with the author's authorization (merge commit `a78d143`); the tag
  `v1.0-tnsre-submission` was not pushed.
* **Commits** (oldest → newest): `6ebbd2d` plan pre-specified; `4dd6d30` metric validation; `e459b29` addendum A1;
  `c6e2a3f` tests, loader, CPU timing; `17063fb` addendum A2, **decision rules frozen**; `376ccfe` rectified-flow
  implementation, dataset, reconstruction control; `d64209f` / `2300e63` training records. Then `89af6d5` (in-progress
  evaluation log), `4067d8b` (held-out evaluation, figures and this report), `9c6e71d` and `9df833d` (updates to this
  report) and the merge `a78d143`.
* **Model implementation**: `extensions/rhythm_preserving_audio/src/rf_model.py`; training
  `experiments/train_rf.py`; evaluation `experiments/eval_rf.py`; metrics `src/rhythmic_metrics.py`,
  `src/acoustic_metrics.py`; stimuli `src/synthetic_audio.py`; DSP `src/baselines.py`; SAME-S wrapper
  `src/latents.py`; Stable Audio 3 loader `src/model.py`.
* **Logs and results**: `results/rf_training.json` (losses, parameters, times), `results/rf_eval.log`,
  `results/rf_eval.json` (all 640 per-output rows, per-composition means, decision quantities),
  `results/metric_validation.json`, `results/aliasing_validation.json`, `results/reconstruction_control.json`,
  `results/smoke_cpu_timing.json`, `results/latents_manifest.json`.
* **Figures**: `figures/fig_tradeoff.{pdf,png}`, `fig_training`, `fig_aliasing`, `fig_example`. **Audio examples**:
  none committed (`.wav` is git-ignored); every clip is synthetic and regenerable from the scripts, so examples could
  be shared without licensing issues if wanted.
* **Reproduction** (from the repository root, CPU):
  ```
  python3 -m venv ~/.venvs/rpa && ~/.venvs/rpa/bin/pip install torch==2.7.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cpu
  ~/.venvs/rpa/bin/pip install einops einops-exts safetensors tqdm huggingface-hub transformers soundfile numpy scipy matplotlib mir_eval
  ~/.venvs/rpa/bin/pip install --no-deps git+https://github.com/Stability-AI/stable-audio-3@4007b6f2987bcb760626c2b4ae3e3541753984e9
  # SAME-S weights: stabilityai/stable-audio-3-small-music-base model.safetensors (ungated) -> /home/user/models/sa3 (see src/model.py)
  cd extensions/rhythm_preserving_audio
  ~/.venvs/rpa/bin/python experiments/validate_metrics.py      # simulated controls
  ~/.venvs/rpa/bin/python experiments/validate_aliasing.py
  ~/.venvs/rpa/bin/python experiments/build_latents.py         # synthetic dataset + SAME-S latents
  ~/.venvs/rpa/bin/python experiments/train_rf.py --steps 6000 # V0, V1
  ~/.venvs/rpa/bin/python experiments/eval_rf.py               # frozen held-out evaluation
  ~/.venvs/rpa/bin/python src/visualize.py                     # figures
  ~/.venvs/rpa/bin/python -m unittest discover -s tests        # 23 tests
  ```
* **Tests**: 23 pass (18 metric and stimulus tests, 5 rectified-flow tests).
* **Neuroscience study unchanged**: `git diff --name-only a78d143^1 a78d143` lists 37 files, all under
  `extensions/` (the earlier check, `git diff main...extension/rhythm-preserving-audio`, is empty now that both refs
  point at the same commit); the pre-registration (`935c80a`), results, manuscript and decision rules of the EEG study are
  untouched. theBIBMsequel and the other attached repositories were not modified.

## 7. EDGE audit

| dimension | score (1–5) | basis |
|---|---|---|
| Exacting standards | 4 | Plan and rules frozen before outputs; metrics calibrated on controls with failures recorded; unit tests on objective and sampler; matched-transformation rule. Lost a point for: beat and tempo metrics omitted from the held-out run, single training seed, n = 8. |
| Differentiated positioning | 4 | Not a generation demo: a measurement study of rhythm preservation, with an aliasing result and alias-aware evaluation tied to the author's EEG work. Lost a point because the main model comparison (paired vs unpaired conditioning) has a predictable direction. |
| Grounded verification | 4 | Every number traces to a committed JSON file; model facts verified in Stable Audio 3 source and config; literature for established methods is cited from memory and still needs checking. |
| Emotional resonance | 4 | The question follows directly from the author's research on how rhythm is carried through measurement and representation; no claim about emotion, perception, therapy or the brain is made from audio analysis. |

Unresolved limitations: synthetic data only; one edit type; no Stable Audio 3 result; no LoRA; beat and tempo
metrics not computed on outputs; small n; literature novelty unchecked.

## 8. Conclusions

### Capabilities demonstrated by this work

* Implementing a rectified-flow (flow-matching) objective, velocity network, conditioning and ODE sampler in
  PyTorch, with unit tests.
* Training small conditional generative audio models in a pretrained autoencoder's latent space (CPU), with
  logged training and validation losses and verified parameter updates.
* Audio-to-audio editing with a controllable strength parameter, and source-conditioned (paired) editing.
* Designing and running a pre-registered, controlled evaluation of rhythm preservation in generative audio,
  including metric calibration, an aliasing analysis and a matched-transformation comparison with uncertainty.
* Auditing a current open generative audio model (Stable Audio 3) from primary sources and loading it through its
  official code.
* Python, PyTorch, NumPy and SciPy for audio signal processing and evaluation.

### Not yet demonstrated by this work

* LoRA or any parameter-efficient fine-tuning; fine-tuning of a pretrained generative model; post-training;
  reward modelling.
* Diffusion-model training (as distinct from flow matching).
* Results with Stable Audio 3 or any large pretrained generator; text-to-audio generation.
* Results on real (non-synthetic) music, perceptual validation, or GPU-scale training.
* Beat-alignment and tempo-preservation results for generated audio.

### Remaining blockers

* **Stable Audio 3 access**: the Hugging Face credential stored for this session is rejected ("Invalid username
  or password"); the gated `stabilityai/stable-audio-3-small-music` repository, which holds the T5Gemma text
  encoder, needs a valid read token from an account that has accepted the licence.
* **Compute**: CPU only (no GPU); Stable Audio 3 LoRA on CPU is estimated at about 10 s per step and was not
  attempted.
* **Publication**: done; the work is public on `main` (merge `a78d143`).
