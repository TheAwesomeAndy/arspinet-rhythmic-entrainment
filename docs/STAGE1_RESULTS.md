# Stage 1 results, read against the frozen pre-registration (2026-11-09)

Rules: `docs/PREREGISTRATION_DRAFT.md` frozen at commit `935c80a`, addendum A1 (eight
participants; power at n = 8) recorded before the group test. Runs: `weineck/q2_residual.py`
and `weineck/tempo_curve.py`, outputs in `weineck/results/*_stage1.{json,log}`.

Timing disclosure: the Q2 script computes its group table automatically when the last
participant finishes. That happened while addendum A1-power was being appended (the addendum
stamps "group lines: 1"); A1-power contains only simulation numbers and could not be shaped
by the data. Before reading the full table the analyst saw the three paired-contrast lines
in a process check. The verdicts below apply the frozen rules mechanically.

## Participants and trials

| participant | subgroup | one-to-one trials N | held-out TRF r (fronto-central) |
|---|---|---|---|
| 10 | 1 | 75 | 0.022 |
| 11 | 2 | 94 | 0.031 |
| 12 | 3 | 100 | 0.048 |
| 13 | 0 | 99 | 0.015 |
| 14 | 1 | 78 | 0.032 |
| 16 | 3 | 95 | 0.025 |
| 17 | 0 | 107 | 0.037 |
| 18 | 1 | 71 (three of four blocks) | 0.026 |

All eight exceed the frozen minimum of 40; none excluded.

## Q2: beat-locked structure in the residual of the four-feature TRF

Participant z against the stimulus-label shuffle; delta = per-trial standardized effect.

| statistic | median z | median delta | participants positive | one-sided Wilcoxon p |
|---|---|---|---|---|
| drive, linear (N0) | +2.17 | +0.181 | 7/8 | 0.012 |
| drive, reservoir unit-PC1 (R) | +2.17 | +0.186 | 8/8 | 0.004 |
| **residual, linear (N0), H2** | **+0.90** | **+0.091** | **6/8** | **0.055** |
| residual, envelope (N2a) | -0.23 | -0.022 | 3/8 | 0.578 |
| residual, square (N2b) | -0.40 | -0.029 | 3/8 | 0.844 |
| residual, reservoir unit-PC1 (R) | +1.03 | +0.110 | 5/8 | 0.055 |
| residual, reservoir population rate | +0.48 | +0.037 | 5/8 | 0.578 |
| residual, shuffled-weight reservoir (Rs) | +0.81 | +0.085 | 5/8 | 0.074 |

Paired per-trial standardized differences (TOST bounds +-0.10 delta, decided at stage 2):
R - N0 median +0.009 (5/8 positive); R - N2a +0.163 (6/8); R - N2b +0.166 (6/8).

Per participant, residual linear z: 10 -0.26, 11 +0.61, 12 +5.26, 13 -0.87, 14 +1.18,
16 +0.06, 17 +2.69, 18 +1.79. The reservoir's values track these within about 0.5 z in
every participant (12: +5.93, 17: +2.94, 18: +2.22), as does the shuffled-weight control.

### Verdicts (frozen rules)

* **H2 at stage 1: not supported** (p = 0.055, rule p < 0.01). Per Section 5 and A1 this
  is inconclusive for components below a = 0.04; the observed median delta (0.091) lies
  where stage 1 had power 0.34-0.38. It is not evidence of absence.
* **Stage 2 proceeds, as pre-specified and unconditionally**: the remaining 25 participants
  are downloaded and H2 is tested on all 34 at alpha 0.04.
* **H1 and H3**: descriptive at stage 1 (equivalence underpowered at n = 8, as frozen).
  Descriptively, the reservoir readout equals the linear statistic on both the drive and
  the residual (paired delta +0.009), and the weight-shuffled reservoir equals it too; the
  reservoir's margin over the envelope and square statistics reflects those baselines
  being null while the residual's linear beat-locked power is not.

## Q1: beat tagging across the 13 tempi (tempo-known trials, fronto-central drive)

Median over participants of the tagging z (max over k in {1, 2}) and the fraction of
participants above 1.96:

| tempo (Hz) | L | R_pc1 | R_pop | Rs_pc1 | frac L / R_pc1 > 1.96 | n |
|---|---|---|---|---|---|---|
| 1.00 | +1.18 | +1.03 | +1.56 | +1.15 | 0.33 / 0.33 | 3 |
| 1.25 | +2.11 | +2.17 | +1.19 | +2.13 | 0.50 / 0.50 | 8 |
| 1.50 | +1.07 | +1.03 | +2.05 | +1.05 | 0.25 / 0.25 | 8 |
| 1.75 | +0.79 | +0.82 | +0.92 | +1.13 | 0.38 / 0.38 | 8 |
| 2.00 | +0.97 | +1.14 | +0.99 | +0.85 | 0.12 / 0.25 | 8 |
| 2.25 | +3.07 | +2.78 | +0.48 | +2.92 | 0.62 / 0.62 | 8 |
| 2.50 | +1.75 | +1.40 | +0.82 | +1.42 | 0.38 / 0.38 | 8 |
| 2.75 | +3.35 | +3.49 | +1.57 | +3.09 | 0.75 / 0.88 | 8 |
| 3.00 | +2.84 | +2.86 | +0.92 | +2.65 | 0.62 / 0.62 | 8 |
| 3.25 | +0.59 | +0.97 | +1.41 | +0.80 | 0.25 / 0.38 | 8 |
| 3.50 | +2.55 | +2.45 | +0.10 | +2.26 | 0.50 / 0.75 | 8 |
| 3.75 | +3.66 | +3.52 | +0.67 | +3.29 | 0.62 / 0.62 | 8 |
| 4.00 | +3.86 | +3.55 | +0.18 | +3.74 | 0.88 / 0.88 | 8 |

Readings (descriptive): the reservoir unit-PC1 and the linear statistic agree at every tempo
(largest gap 0.4 z); the population rate does not carry the tagging; with this statistic
(fronto-central power at the tempo and its octave) tagging is strongest from 2.25 to 4 Hz,
whereas Weineck et al. report TRF/SRC synchronization strongest at 1-2 Hz for spectral
flux; the two measures are not the same quantity and the comparison is noted, not resolved.

## What this stage contributes regardless of stage 2

1. A calibrated, pre-registered test with the group result inconclusive in a stated region,
   not a null dressed as absence.
2. Beat-locked power in the TRF residual in two participants (z 5.3, 2.7), seen identically
   by a linear statistic, the reservoir and its weight-shuffled control: whatever this
   structure is (nonlinearity or TRF misfit), it does not need a reservoir to be seen.
3. Replication of participant-level beat tracking in Weineck's data with an independent
   statistic and null, and the first drive-vs-fixed-nonlinear comparison across 13 tempi.
