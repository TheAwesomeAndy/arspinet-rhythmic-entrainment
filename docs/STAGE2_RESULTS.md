# Stage 2 results, read against the frozen pre-registration (2026-11-09)

Rules: `docs/PREREGISTRATION_DRAFT.md` frozen at `935c80a`, addendum A1. Pipeline:
`weineck/q2_residual.py` (computationally refactored after the first stage-2 launch stalled
on thread oversubscription; the refactor reproduces stage-1 output to 1e-14, see commit
`b658693`), merged by `weineck/q2_group_merge.py`; tempo curve `weineck/tempo_curve.py`.
Outputs: `weineck/results/q2_residual_stage2_{chunk1,chunk2,chunk3,merged}.json`,
`tempo_curve_stage2.{json,log}`.

Data: all 34 participants of Weineck, Wen & Henry (2022); one-to-one trials 75-110 per
participant (subj 18 now 89 with its fourth block, fetched for completeness); no participant
below the 40-trial minimum; no exclusions. Held-out TRF prediction r at fronto-central
channels 0.015-0.079 (median ~0.036).

## Q2 group tests (frozen; participant z against the stimulus-label shuffle; delta = per-trial standardized effect)

| statistic | median z | median delta | participants positive | one-sided Wilcoxon p |
|---|---|---|---|---|
| drive, linear (N0) | +4.45 | +0.317 | 33/34 | < 1e-4 |
| drive, reservoir unit-PC1 (R) | +4.29 | +0.302 | 34/34 | < 1e-4 |
| **residual, linear (N0): H2** | **+3.00** | **+0.228** | **31/34** | **< 1e-4** |
| residual, envelope (N2a) | +0.02 | +0.001 | 17/34 | 0.43 |
| residual, square (N2b) | +0.37 | +0.037 | 21/34 | 0.20 |
| residual, reservoir unit-PC1 (R) | +2.97 | +0.223 | 31/34 | < 1e-4 |
| residual, reservoir population rate | +0.41 | +0.036 | 21/34 | 0.14 |
| residual, shuffled-weight reservoir (Rs) | +2.94 | +0.219 | 31/34 | < 1e-4 |

### Verdicts

* **H2: supported at stage 2 (alpha 0.04).** The residual of the cross-validated four-feature
  ridge TRF (spectral flux, beat onsets, envelope, derivative; lags 0-400 ms; nested lambda)
  carries beat-locked power at the trial's own tempo relative to other grid tempi. By the
  calibration mapping (a = 0.04 -> delta 0.18-0.21) the effect is about a 4 % amplitude
  component.
* **H1: equivalent.** Drive: delta(R) - delta(L) median -0.005; TOST within +-0.10 passes
  (both p < 0.001). The reservoir read out linearly across units neither adds nor loses
  beat-locking detection power relative to the linear statistic.
* **H3: equivalent to the linear residual statistic.** delta(R) - delta(N0) median -0.001,
  TOST passes; R > N0 p = 0.63. R exceeds N2a and N2b (median +0.22, +0.21; p < 1e-4),
  which are themselves null. The shuffled-weight reservoir equals R (0.219 vs 0.223).

### Reading, within the frozen scope

1. There is robust beat-locked structure in single-listen EEG beyond what this linear
   encoding model predicts. It is phase-coherent power at the beat and its octave: the
   envelope and squared-signal statistics, which respond to amplitude modulation, see
   nothing.
2. The linear model explains very little single-trial variance (r ~ 0.04) and removes only
   about a quarter of the drive's beat-locking effect (delta 0.317 -> 0.228). The
   parsimonious account of H2 is therefore **underfitting of a stimulus-locked response at
   single-listen SNR**, not nonlinearity; the frozen text already limits the claim to "beyond
   this linear model", and nothing here distinguishes oscillatory from evoked accounts.
3. **The fixed spiking reservoir is not needed to see any of it.** Its linear readout equals
   the linear statistic on the drive (H1) and on the residual (H3), and a reservoir with
   shuffled recurrent weights does the same; its population rate loses the information.
   This is the class-level result the framing predicted (`docs/FRAMING.md`), now measured on
   34 participants.

## Q1: 13-tempo curve, all 34 participants (median z, max over k in {1, 2})

| tempo (Hz) | L | R_pc1 | R_pop | Rs_pc1 | frac L / R_pc1 > 1.96 | n |
|---|---|---|---|---|---|---|
| 1.00 | +1.55 | +1.63 | +0.69 | +1.62 | 0.43 / 0.43 | 14 |
| 1.25 | +2.14 | +2.20 | +1.38 | +2.16 | 0.59 / 0.56 | 34 |
| 1.50 | +1.32 | +1.35 | +0.94 | +1.31 | 0.44 / 0.41 | 34 |
| 1.75 | +2.17 | +2.01 | +0.54 | +1.93 | 0.56 / 0.50 | 34 |
| 2.00 | +1.84 | +1.90 | +1.03 | +2.08 | 0.47 / 0.50 | 34 |
| 2.25 | +2.04 | +2.20 | +0.81 | +2.27 | 0.56 / 0.53 | 34 |
| 2.50 | +2.91 | +2.87 | +1.04 | +2.39 | 0.59 / 0.56 | 34 |
| 2.75 | +2.91 | +3.13 | +1.02 | +2.72 | 0.71 / 0.76 | 34 |
| 3.00 | +3.14 | +2.78 | +0.60 | +2.74 | 0.62 / 0.65 | 34 |
| 3.25 | +1.42 | +1.31 | +1.06 | +1.40 | 0.41 / 0.47 | 34 |
| 3.50 | +2.53 | +2.14 | +0.41 | +2.64 | 0.56 / 0.59 | 34 |
| 3.75 | +3.71 | +3.72 | +0.81 | +3.45 | 0.76 / 0.74 | 34 |
| 4.00 | +3.49 | +3.32 | +0.42 | +3.49 | 0.79 / 0.82 | 34 |

Readings: L and R_pc1 agree at every tempo (largest gap 0.4 z); population rate weak
throughout; with this statistic (fronto-central power at the tempo and its octave) tagging
rises from 1-2 Hz to 3.75-4 Hz. Weineck et al. report TRF/SRC synchronization strongest at
1-2 Hz for spectral flux; the two measures differ (power at the tempo vs stimulus-response
correlation) and the discrepancy is recorded, not resolved. (Only 14 participants' subgroups
include a tempo-known 1.00 Hz trial after one-to-one matching.)

## Pre-registered robustness rows still to run

Seeds 7 and 99; rho in {0, 0.3, 1.2}; spectral-flux-only TRF; TRF lag range 0-600 ms; IAAFT
surrogate of the residual. Proposed descriptive addition (not pre-registered, labelled as
such): the tagging statistic of the TRF *prediction* itself, to state directly how much of
the drive's beat-locked power the linear model reproduces.

## Disclosure

Stage-1 per-participant lines had been seen before the stage-1 group test (addendum A1).
No stage-2 number was seen before the merge script printed the frozen tests. The first
stage-2 launch was stopped for computational reasons only (no participant had completed);
the refactored pipeline is the same estimator (verified on stage-1 subj 10).
