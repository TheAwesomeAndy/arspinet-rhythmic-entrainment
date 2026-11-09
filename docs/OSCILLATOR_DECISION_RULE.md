# Theory 3: stimulus-driven oscillator encoding model vs evoked kernel — decision rule

**Status: EXPLORATORY.** Added 2026-11-09 after the stage-2 merge (`docs/STAGE2_RESULTS.md`),
outside the frozen pre-registration (`935c80a`, addendum A1). Committed before any Theory 3
result existed (this commit is the timestamp). The confirmatory code, the frozen documents and
the running underfitting check are untouched.

## Question

Does an entrained-oscillator model predict beat-locked EEG at held-out tempi better than an
evoked (TRF) kernel, especially near a preferred rate?

## Models (`weineck/oscillator_bank.py`, `weineck/oscillator_heldout.py`)

| label | model | role |
|---|---|---|
| a | bank of ~30 Hopf / Stuart-Landau oscillators (canonical neural-resonance form), natural frequencies log-spaced 0.5-8 Hz, driven by spectral flux and beat onsets; outputs Re(z), \|z\| | PRIMARY nonlinear |
| b | resonate-and-fire units (Izhikevich 2001), same frequency grid, same drive; output smoothed spike rate | PRIMARY spiking |
| c | linear damped-oscillator bank, same frequencies (LTI) | CONTROL 1: does any gain need nonlinearity? |
| d-short | existing 4-feature ridge TRF, lags 0-400 ms | CONTROL 2a (evoked baseline) |
| d-long | 4-feature ridge TRF, lags 0-1000 ms | CONTROL 2b: "oscillator wins" cannot mean "longer kernel" |
| aug | ridge from [a outputs + 4 TRF features] | oscillator-augmented model |

Encoding: ridge regression from model outputs (lags 0-400 ms) to the 32-channel EEG, nested
lambda; same preprocessing, trials and channels as `weineck/q2_residual.py` (one-to-one
matched trials, 40-trial minimum). Free oscillator parameters (bifurcation parameter, input
gain) are chosen only on training tempi by inner cross-validation; the frequency grid is fixed.

Cross-validation: leave-one-tempo-out across the 13 Weineck tempi within participant (train on
12, predict all trials of the held-out tempo); additionally leave-one-tempo-out at the group
level (pooled across participants).

## Primary metric

Held-out-tempo prediction r at fronto-central channels (Fz, FC1, FC2, Cz, F3, F4, C3, C4), per
participant, averaged over held-out tempi: **delta_r = r(augmented model) - r(best evoked
baseline)**, where the best evoked baseline is whichever of d-short and d-long has the higher
held-out r for that participant.

## Decision rule (fixed here, before any result)

* **"Oscillator supported"** = group median delta_r > 0 with one-sided Wilcoxon p < .01 **AND**
  delta_r is larger for the oscillator (Hopf) augmented model than for the linear-oscillator
  control augmented the same way (paired one-sided Wilcoxon p < .05).
* **"Preferred-rate effect"** = significant negative quadratic term in delta_r versus tempo
  (mixed model or per-participant quadratic fits with a Wilcoxon on the quadratic coefficient
  < 0), with the fitted peak inside the 13-tempo range (1-4 Hz).
* **Anything else = not supported**; reported as is, including the direction and size of
  delta_r.

The spiking model (b) is evaluated with the same metric and reported alongside; it does not
enter the primary rule.

## Validation before any real-data table is trusted

* Recovery check: EEG simulated from the fitted Hopf model plus line-free noise matched to the
  observed held-out r (~0.04); the pipeline must show delta_r > 0.
* False-positive check: EEG simulated from the evoked TRF only plus matched noise; the pipeline
  must not show a significant oscillator advantage under the rule above.
Both are reported before the real-data table.

## Descriptive signatures (no decision attached)

Tempo-dependent phase lag of the model-predicted versus actual beat-locked response; the
amplitude-versus-tempo (resonance) curve of the oscillator bank; post-offset persistence only
if the stimuli contain beat omissions or usable endings (stated plainly if not available).

## Reporting

Numbers only, rule applied verbatim. Outputs: `weineck/results/oscillator_heldout*.json`;
group tables and the decision via the merge script. Runs are single-threaded.
