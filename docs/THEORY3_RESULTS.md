# Theory 3 results: stimulus-driven oscillator encoding model vs evoked kernel (EXPLORATORY)

Run 2026-11-09 after the stage-2 merge; rule fixed in advance in `docs/OSCILLATOR_DECISION_RULE.md`
(commit `d54f0ef`). Pre-registration frozen at `935c80a` untouched; confirmatory results
unchanged. Code: `weineck/oscillator_bank.py`, `weineck/oscillator_heldout.py`,
`weineck/oscillator_merge.py`; outputs `weineck/results/oscillator_*.json`. All runs
single-threaded. Literature context: `docs/lit_oscillator_models.md`.

## 1. Validation (reported before the real data, as committed)

Six participants (10, 11, 12, 17, 21, 30), EEG replaced by simulated data through the identical
pipeline (nested lambda and oscillator parameters chosen on training tempi only;
leave-one-tempo-out).

| world | delta_r (aug - best evoked), median | participants positive | one-sided p | Hopf-aug > linear-aug (paired p) |
|---|---|---|---|---|
| recovery: EEG = fitted Hopf-augmented model + line-free noise matched to r ~ 0.04 | **+0.008** | 5 / 6 | 0.078 | **0.016** |
| false positive: EEG = fitted 0-400 ms TRF + matched noise | **-0.018** | 1 / 6 | 0.98 | 0.84 |

The pipeline recovers a planted oscillator in direction (the committed criterion, delta_r > 0;
with n = 6 the smallest attainable Wilcoxon p is 1/64, so the rule's p < .01 is unreachable at
this n by construction) and produces no oscillator advantage in an evoked-only world. In the
evoked world the Hopf-augmented model generalizes *worse* than the TRF alone, which is the
signature to compare the real data against.

## 2. Real data, 34 participants, leave-one-tempo-out within participant

Mean held-out-tempo prediction r at fronto-central channels (median over participants):

| model | median r | participants r > 0 |
|---|---|---|
| d_short: 4-feature TRF, 0-400 ms | **+0.034** | 34/34 |
| d_long: 4-feature TRF, 0-1000 ms | +0.028 | 34/34 |
| c: linear damped-oscillator bank | +0.028 | 34/34 |
| aug_lin: linear bank + TRF features | +0.031 | 34/34 |
| aug: Hopf bank + TRF features | +0.025 | 34/34 |
| a: Hopf bank alone | +0.020 | 33/34 |
| b: resonate-and-fire bank | +0.006 | 30/34 |

Primary metric: delta_r (aug - best evoked baseline) median **-0.010**, positive in **3 of 34**,
one-sided Wilcoxon p = 1.00. Linear-bank control: aug_lin - best evoked median -0.004, positive
8/34. Hopf-aug vs linear-aug: p = 1.00. Spiking bank minus best evoked: -0.026. Hopf alone
minus best evoked: -0.014.

Preferred-rate test: per-participant quadratic coefficient of delta_r vs tempo median +0.0033,
negative in 12/34, Wilcoxon (< 0) p = 0.96. delta_r is negative at every one of the 13 tempi
(group medians -0.007 to -0.024).

**Decision (rule applied verbatim): NOT SUPPORTED; no preferred-rate effect.**

Direction: the evidence runs against the oscillator account. Adding Hopf-bank features to the
TRF lowers held-out-tempo prediction in 31 of 34 participants, the same pattern the pipeline
produces when the world is evoked-only, and the opposite of what it produces when a Hopf
component is present. The inner cross-validation chose the most damped Hopf configuration
(alpha = -0.5) in 323 of 422 participant-tempo fits and the most damped linear configuration
(alpha = -2.0) in 395 of 422: the data prefer oscillators that behave like short filters.

## 3. Descriptive signatures (no decision attached)

* **Phase lag vs tempo.** The circular-median phase of the EEG relative to each model's
  prediction at the beat frequency varies across the 13 held-out tempi without a monotonic
  trend for either the TRF or the Hopf-augmented model (range about -1.1 to +0.9 rad). The
  slope of the unwrapped group phase against 2*pi*f gives an apparent latency of +52 ms (TRF)
  and +49 ms (Hopf-augmented): the two models carry the same lag structure.
* **Resonance curve.** The Hopf bank's mean |z| peaks at the oscillator whose natural frequency
  equals the stimulation tempo (ratio 0.95-1.04 at 9 of 13 tempi) and at a harmonic (2x or 4x)
  at 2.0, 3.25 and 4.0 Hz: the bank behaves as a driven filter bank following the stimulus,
  with no preferred natural frequency independent of the drive.
* **Post-offset persistence.** Not available in this dataset: each trial ends with the end of
  the music segment and the aligned analysis window contains no silent continuation.

## 4. Group-level leave-one-tempo-out (pooled across participants)

One encoding model per family fitted on all participants' trials at 12 tempi (normal-equation
moments summed over participants; lambda by inner leave-one-tempo-out), predicting every
participant's trials at the held-out tempo; configurations fixed to those most often chosen
within participants (Hopf alpha -0.5, gain 1; linear alpha -2.0). `weineck/oscillator_group.py`,
`weineck/results/oscillator_group_loto*.json`.

| model | median held-out r (fronto-central) |
|---|---|
| d_short: TRF 0-400 ms | **+0.038** |
| d_long: TRF 0-1000 ms | +0.038 |
| aug_lin: linear bank + TRF | +0.038 |
| aug: Hopf bank + TRF | +0.037 |
| c: linear bank | +0.031 |
| a: Hopf bank | +0.030 |

delta_r (aug - best evoked) median **-0.002**, positive in 8/34, one-sided p = 1.00; aug vs
aug_lin p = 1.00; delta_r negative at 12 of 13 held-out tempi. Pooling across participants
raises every model's held-out r (the within-participant TRF reached 0.034) and does not change
the verdict: with 34 participants' worth of training data the oscillator features still add
nothing to the evoked kernel at unseen tempi.

## 5. Reading

Within the frozen scope and the committed rule: a bank of stimulus-driven Hopf oscillators,
with free damping and gain chosen on training tempi, does not predict beat-locked EEG at
unseen tempi better than a short TRF kernel, and the resonate-and-fire bank does worse still.
The result replicates, at the level of held-out prediction rather than spectral shape, the
conclusion of Damsma et al. (2025) that an evoked kernel accounts for what these oscillator
models account for, and it adds the direction: nonlinear oscillator features cost
generalization. Stated limits: one noise model in the validation worlds; one Hopf
parameterization family (four configurations); 13 tempi over a factor of 4 while the bank
spans 0.5-8 Hz; held-out r values of 0.02-0.03 leave little headroom for any model.
