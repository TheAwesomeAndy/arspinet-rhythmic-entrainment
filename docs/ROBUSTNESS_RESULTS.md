# Robustness grid results (exploratory; run after the stage-2 merge)

Rule (docs/ROBUSTNESS_PLAN.md): 'H2 robust' = residual delta > 0 with one-sided Wilcoxon p < .01 in every row except IAAFT; 'H1/H3 equivalence robust' = TOST (+-0.10 delta) passes in every row. Every row is reported.

| row | tau (ms) | held-out r | median residual delta (H2) | positive / n | Wilcoxon p | H1 TOST (drive R vs L) | H3 TOST (resid R vs N0) | R - Rs (median delta) | H2 p<.01 |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.005) | pass (-0.001) | -0.005 | yes |
| seed7 | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.004) | pass (-0.000) | -0.002 | yes |
| seed99 | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.007) | pass (-0.009) | +0.005 | yes |
| rho0 | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.005) | pass (+0.004) | +0.000 | yes |
| rho0.3 | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.012) | pass (-0.002) | -0.002 | yes |
| rho1.2 | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.010) | pass (-0.003) | -0.003 | yes |
| beta0.01 | 391 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (+0.007) | pass (-0.010) | -0.004 | yes |
| beta0.004 | 977 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.014) | pass (-0.006) | +0.001 | yes |
| trf_flux | 78 | +0.037 | +0.238 | 30 / 34 | 0.0000 | pass (-0.005) | pass (-0.004) | -0.011 | yes |
| trf_long | 78 | +0.034 | +0.228 | 32 / 34 | 0.0000 | pass (-0.005) | pass (-0.005) | -0.007 | yes |
| iaaft (null) | 78 | - | surrogates: +0.156 (real +0.228) | 0.94 | 0.0000 | - | - | - | surrogate deltas > 0: yes |

**H2 robust (rule): YES.**  **H1/H3 equivalence robust (rule): YES.**

No row flipped.


## Reading of the IAAFT row

As recorded in the plan before the row was run, IAAFT surrogates preserve each trial's amplitude
spectrum, so a magnitude statistic was not expected to collapse: the surrogates keep a median delta of
+0.156 against the real +0.228 (about 76 % of it), positive in 94 % of participants.
The part that IAAFT does remove is the within-trial phase coherence of the beat-locked component
across Welch segments: the real delta exceeds the participant's own 200 surrogates at a median
percentile of 0.73, above the 95th percentile in 8 of 34 participants. The row therefore
does not serve as a null for H2 (the stimulus-label shuffle does, with simulated false-positive rate
0.00-0.04), and it is reported as what it is: a measurement of how much of the residual beat-locking is
power at the beat frequency (retained) versus phase coherence over time (removed).

## Summary

All ten non-null rows reproduce the stage-2 conclusions: residual beat-locking delta 0.228-0.238 with
30-32 of 34 participants positive and p < 1e-4; H1 and H3 equivalence within +-0.10 delta in every row;
the reservoir's margin over its weight-shuffled twin within +-0.011 in every row, including rho = 0 (no
recurrence, R - Rs = 0 by construction) and membrane timescales of 78, 391 and 977 ms. The reservoir's
seed, spectral radius and integration time, and the TRF's feature set and kernel length, change nothing
about what is detected. No row flipped.
