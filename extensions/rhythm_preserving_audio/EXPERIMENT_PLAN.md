# Experiment plan: rhythm-preserving generative audio editing

Written 2026-11-26, **before** any metric-control or model output was evaluated. Changes after this
point are recorded as dated addenda below, never as silent edits. This is a computational audio
extension; nothing here touches the EEG study, its pre-registration (`935c80a`) or its manuscript.

## Question

Can parameter-efficient fine-tuning (LoRA) of a pretrained flow-matching audio model improve rhythmic
preservation during controlled audio-to-audio editing, **at a comparable amount of acoustic change**?

Connection to the EEG work: that study asked what rhythmic information a measurement chain (EEG, a
linear encoding model, a reservoir) preserves, and calibrated every statistic on synthetic signals with
known structure before reading real data. Here the chain is a generative editor; the same discipline
applies: known ground truth, calibrated metrics, controls, fixed-cycle-count comparison across tempi,
pre-specified decision quantities, source-level units.

## 1. Environment audit (measured 2026-11-26)

| item | value |
|---|---|
| CPU | Intel Xeon @ 2.10 GHz, 4 cores (`nproc`) |
| GPU | none (`nvidia-smi` absent; `torch.cuda.is_available()` false) |
| RAM | 15 GB |
| disk | 4.6 GB free before installs, 3.5 GB after the CPU stack (per-session allowance) |
| Python / stack | 3.13; venv `/home/user/.venvs/rpa`: torch 2.7.1+cpu, torchaudio 2.7.1+cpu, transformers 5.24.1, pytorch_lightning 2.5.5, mir_eval 0.8.2, numpy 2.5.5, scipy 1.18.1 |
| paid compute | none used; none to be used without approval |

## 2. Model audit (primary sources, 2026-11-26)

Stable Audio 3 (Stability AI; paper arXiv:2605.17991; code github.com/Stability-AI/stable-audio-3 at
commit `4007b6f2987bcb760626c2b4ae3e3541753984e9`).

* **Objective.** `stable-audio-3-small-music-base/model_config.json`: `"diffusion_objective":
  "rectified_flow"`, i.e. **flow matching**: the network predicts a velocity v = noise - data on the
  straight path x_t = (1 - t) x_0 + t eps (training code `stable_audio_3/training/diffusion.py`: targets
  `noise - diffusion_input`), sampled by integrating an ODE (50-100 steps per the paper), with minibatch
  optimal-transport coupling (`ot_coupling: true`). The same code also implements a **v-objective
  diffusion** (`targets = noise * alpha - x * sigma`), not used by this model. The released
  `small-music` checkpoint is the base model after ODE distillation and adversarial post-training (a
  few-step sampler); it is a *distilled derivative* of the flow-matching model, not itself trained by
  flow matching alone. These are kept distinct throughout.
* **Architecture.** Latent diffusion transformer (DiT, 20 layers, width 1024, 16 heads, adaLN global
  conditioning, 64 memory tokens) on the latents of the SAME-S semantic-acoustic autoencoder (44.1 kHz
  stereo); text conditioning by a T5Gemma encoder (`t5gemma-b-b-ul2`, 768-d) via cross-attention;
  `seconds_total` conditioning; inpainting conditioning (`inpaint_mask`, `inpaint_masked_input`) added
  locally. Small: 433 M parameters (README table).
* **Editing.** Audio-to-audio via `init_audio` + `init_noise_level` (SDEdit-style: the source latent is
  noised to that level and the ODE is integrated from there), and inpainting by mask. `init_noise_level`
  is the editing-strength control.
* **LoRA.** `scripts/train_lora.py`: base weights frozen, adapters (LoRA, DoRA, LoRA-XS) on Linear /
  Conv1d layers of the DiT and conditioner, only adapter params optimised, loss = the model's flow-matching
  MSE on pre-encoded latents with **text** conditioning (audio + caption pairs). It is not a paired
  source-to-target editing objective and has no explicit beat input. Docs list a CUDA GPU (small: ~2-2.5
  GB VRAM); the trainer uses Lightning `accelerator="auto"`, so it can run on CPU. CPU speed is unmeasured.
* **Licence / access.** Stability AI Community License (research and non-commercial use permitted; LoRA
  adapters are Derivative Works; outputs owned by the user). `small-music` is gated (click-through), and
  the T5Gemma text encoder is loaded from that gated repo (`repo_id: stabilityai/stable-audio-3-small-music,
  subfolder: t5gemma-b-b-ul2`), so text conditioning requires accepting the licence even for the ungated
  `small-music-base` and `SAME-S` repos. Weights: base 2.27 GB, T5Gemma 1.18 GB.
* **Choice.** `small-music-base` (the flow-matching model, the one LoRA trains on), CPU, fp32 or bf16.
  The distilled `small-music` is not used: disk does not hold both, and the question is about the
  flow-matching model.

## 3. Approaches considered

| # | approach | scientific value | compute here | relation to repo | decision |
|---|---|---|---|---|---|
| 1 | SA3 small-base, SDEdit-style A2A editing; text-conditioned LoRA on rhythmically controlled clips whose captions state tempo and pattern | tests whether a standard PEFT recipe changes the timing behaviour of a real pretrained flow-matching editor | inference: feasible on CPU (to be measured); LoRA: CPU, small rank, few hundred steps, to be measured | metrics, controls and cycle-count rule reused | **primary** |
| 2 | as 1, but LoRA trained through the model's inpainting conditioning (masked source latent as context), the closest built-in form of source-conditioned training | closer to an editing objective | same as 1 plus mask plumbing | same | optional if 1 runs |
| 3 | auxiliary rhythm loss (differentiable onset envelope of decoded audio added to the flow-matching loss) | directly optimises the target | decoder in the loop at every step: not feasible on 4 CPU cores | metrics would become training targets (circular) | rejected for this pass |
| 4 | small flow-matching model trained from scratch on log-mel frames with an explicit beat-grid input | clean causal test of explicit rhythm conditioning | feasible | none with pretrained generative audio | rejected: violates "no training from scratch" in spirit and says nothing about pretrained editors |
| 5 | training-free latent guidance: re-inject the source latent's low-noise trajectory (RePaint / guided SDEdit) at chosen ODE steps | an inference-time alternative to fine-tuning, a strong comparator | cheap | same metrics | secondary comparator if time allows |
| 6 | other models: Stable Audio Open Small / 1.0 (v-objective diffusion), MusicGen (autoregressive tokens, not diffusion or flow), MelodyFlow (flow matching, ~1 B, editing), AudioLDM 2 (diffusion) | alternatives | larger or not flow matching | - | not chosen: SA3 small-base is the smallest open flow-matching editor with an official LoRA path |

## 4. Stimuli (procedural; `src/synthetic_audio.py`)

* 12 rhythmic templates (16-step bar of kick, snare, hat, tonal-note patterns); split **by template**:
  train T01-T06, val V01-V02, test H01-H04. No template (hence no composition or alternative render of
  one) appears in two splits; melody seeds also differ between splits (train 0-2, val 10, test 20-21).
* Tempi 1.0, 1.5, 2.0, 2.5, 3.0, 4.0 Hz (60-240 BPM), the range of the EEG study.
* **Fixed cycle count:** every excerpt holds 16 beats (duration 16 / f + 0.6 s tail), so tempo
  comparisons are made on equal numbers of beat cycles (docs/CYCLE_COUNT_CONTROL.md).
* Instrumentations: electronic (drum machine + saw pluck), acoustic (noise drums + Karplus-Strong
  string), tonal-only (bell tones, no drums). Exact onset and beat times are kept from synthesis.

## 5. Metrics (pre-specified)

Estimates are always computed from the audio; ground truth is only the reference.

**Rhythm.**
* **P1 (primary): onset F1**, +-50 ms, spectral-flux onsets detected in the output vs the
  composition's ground-truth onsets (greedy one-to-one matching). No beat tracker involved. Plus mean
  absolute onset deviation (ms) of matched onsets.
* **P2: beat F1**, +-70 ms, beat positions tracked in the output by a dynamic-programming tracker whose
  period is the nominal tempo (the tempo the prompt asks for), scored against the ground-truth beat
  grid; plus mean absolute beat deviation. Reason for the informed period (decided on the unedited
  sources, before any edit was scored): the fully uninformed tracker picks the wrong metrical level on
  these 16-beat excerpts (tempo estimate within 4 % strictly on 50 % of sources, octave-tolerant on 79 %).
  P2 is evaluated only on compositions whose **source** P2 is >= 0.9 (an input-only inclusion rule;
  syncopated templates T02, T06, V02 lock to the off-beat and fail it, none of the test templates does).
* Secondary: uninformed tempo (relative error, strict and octave-tolerant), uninformed beat F1 at the best
  metrical level, inter-beat-interval deviation, beat-band harmonic z of the novelty envelope
  (`weineck/tagging.tag_z`, read-only import, baseline window scaled by tempo for the fixed cycle count),
  zero-lag novelty-envelope correlation with the source. Beat-band power is never taken as evidence of
  timing on its own.

**Acoustic change.**
* **T1 (primary): log-mel distance** (dB; 64 bands, per-spectrum max-referenced, floored at -80 dB).
* Direction: spectral-centroid shift (Hz; negative = darker / warmer), RMS and crest-factor change (dB),
  chroma correlation (pitch-class content, to separate tonal from rhythmic preservation).

## 6. Metric validation on controls (before any model output)

On the 24 test compositions (H01-H04 x 6 tempi, melody seed 20), with the unperturbed composition as
reference: identity; global shift 10/30/60/100 ms; Gaussian onset jitter sd 5/15/30/50 ms; tempo change
by time scale 1.02/1.05/1.10; event removal 25/50 %; timbre changes with timing preserved (oracle
re-synthesis with another instrumentation; DSP low-pass, shelf cut, compression). Pass criteria
(decided now):
* identity: P1 and P2 at their source ceiling, log-mel distance 0;
* P1 and P2 decrease monotonically (group median) with shift, jitter and tempo change, and fall below 0.5
  for shifts beyond the tolerance (60 and 100 ms for P1; 100 ms for P2);
* timing-preserving timbre controls: group median P1 >= 0.9 and P2 within 0.05 of the source, while
  log-mel distance is clearly non-zero (> 2 dB).
A metric that fails is reported as failed and not used as primary.

## 7. Experiments

* **A (smoke, then baseline).** 2-3 test sources first; then 8 test sources (H01-H04 x 2 tempi). Three
  prompts: softer instrumentation, warmer texture, different instrumental texture, each stating the
  tempo. Strengths (`init_noise_level`) weak / intermediate / strong = 0.3 / 0.5 / 0.7, fixed seeds.
  Also a reconstruction control: encode-decode through SAME-S only (no diffusion).
* **B (strength sweep).** init_noise_level in {0.1, 0.2, ..., 0.9} on the same sources and one prompt;
  curve of P1 / P2 against log-mel distance, per source. Monotonicity is tested (per-source Spearman
  over levels, group sign test), not assumed.
* **C (LoRA).** Text-conditioned LoRA (adapter type and rank chosen to fit CPU memory, logged) on train
  templates, captions with tempo, meter, instrumentation and pattern; validation loss on val templates;
  identical held-out sources, prompts, strengths and seeds for base and LoRA.

## 8. Decision quantities and comparisons (pre-specified)

Unit: **source composition** (test set). Seeds and strengths of one composition are averaged within the
composition before any group statistic. With few compositions every group result is exploratory.

* **Matched-transformation comparison (C, primary).** For each composition and model, P1 as a function of
  log-mel distance across strengths (piecewise-linear interpolation). Compare LoRA vs base at the
  log-mel distances both reach (pre-specified grid: the 25th, 50th and 75th percentiles of the base
  model's distances over strengths 0.3-0.7, pooled over compositions). The paired difference
  (LoRA - base) at each grid point is the decision quantity; reported with a bootstrap 95 % interval
  over compositions and a two-sided Wilcoxon signed-rank p. LoRA is "better" only if the interval at
  the median grid point excludes zero in its favour **and** its log-mel range covers that point (a model
  that preserves rhythm only by editing less is not better).
* Same analysis for P2 (on compositions passing the source rule).
* Directional check: did the edit move the intended way (centroid down for "warmer", RMS / crest down
  for "softer")? Reported per prompt; an edit that preserves rhythm but does not edit is labelled a
  failed edit, not a success.
* B: per-composition Spearman rho(strength, P1); sign test over compositions.

Evidence labels in the report: **measured** (metrics on actual outputs), **simulated** (synthetic
controls), **proposal** (not run), **interpretation**.

## 9. Addenda

(none yet)
