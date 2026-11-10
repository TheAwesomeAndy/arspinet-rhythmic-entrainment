# Robustness grid results (exploratory; run after the stage-2 merge)

**Audit (A1).** The H2 statistic is the tagging z of the TRF residual itself (`q2_residual.stats_on`, term `N0`); the residual is produced by `loo_residuals(X64, XL, fcidx)` from the EEG and the stimulus features only. No reservoir parameter enters it, so the seed, rho and tau rows are **reservoir-independent by construction** on the H2 columns (hence the identical 0.228 / 31 / 34 in every such row); only the TRF rows (trf_flux, trf_long) can move H2. The reservoir enters R, R_pop and Rs only, so the reservoir-sensitive results are the H1 TOST, H3 TOST and R minus Rs columns.

Rule (docs/ROBUSTNESS_PLAN.md): 'H2 robust' = residual delta > 0 with one-sided Wilcoxon p < .01 in every row except IAAFT; 'H1/H3 equivalence robust' = TOST (+-0.10 delta) passes in every row. Every row is reported.

| row | tau (ms) | held-out r | median residual delta (H2) | positive / n | Wilcoxon p | H1 TOST (drive R vs L) | H3 TOST (resid R vs N0) | R - Rs (median delta) | H2 p<.01 |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.005) | pass (-0.001) | -0.005 | yes |
| seed7 (reservoir-independent on H2) | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.004) | pass (-0.000) | -0.002 | yes |
| seed99 (reservoir-independent on H2) | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.007) | pass (-0.009) | +0.005 | yes |
| rho0 (reservoir-independent on H2) | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.005) | pass (+0.004) | +0.000 | yes |
| rho0.3 (reservoir-independent on H2) | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.012) | pass (-0.002) | -0.002 | yes |
| rho1.2 (reservoir-independent on H2) | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.010) | pass (-0.003) | -0.003 | yes |
| beta0.01 (reservoir-independent on H2) | 391 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (+0.007) | pass (-0.010) | -0.004 | yes |
| beta0.004 (reservoir-independent on H2) | 977 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.014) | pass (-0.006) | +0.001 | yes |
| trf_flux | 78 | +0.037 | +0.238 | 30 / 34 | 0.0000 | pass (-0.005) | pass (-0.004) | -0.011 | yes |
| trf_long | 78 | +0.034 | +0.228 | 32 / 34 | 0.0000 | pass (-0.005) | pass (-0.005) | -0.007 | yes |
| iaaft (null) | 78 | - | surrogates: +0.156 (real +0.228) | 0.94 | 0.0000 | - | - | - | surrogate deltas > 0: yes |

**H2 robust (rule): YES.**  **H1/H3 equivalence robust (rule): YES.**

No row flipped.


## Reading of the IAAFT row (A2)

As recorded in the plan before the row was run, IAAFT surrogates preserve each trial's amplitude
spectrum, so a magnitude statistic was not expected to collapse. Decomposition, per participant
(real residual delta minus the mean of its 200 surrogates), n = 34:

| component | median delta | 95 % bootstrap CI | participants > 0 | one-sided Wilcoxon |
|---|---|---|---|---|
| spectral (retained by IAAFT) | +0.156 | [+0.113, +0.231] | 32/34 | p < 1e-4 |
| phase-dependent (removed by IAAFT) | +0.045 | [+0.022, +0.072] | 26/34 | p = 0.0003 |
| real (sum) | +0.228 | | 31/34 | p < 1e-4 |

The residual beat-locking beyond the linear model is therefore **nonlinear, predominantly
spectral**: about three quarters of it is power at the beat frequency and its octave that any
amplitude-preserving surrogate keeps, and about a quarter (0.045, p = 0.0003) is phase coherence of
that component over time within a trial, which IAAFT destroys. The IAAFT row is not a null for H2
(the stimulus-label shuffle is, simulated false-positive rate 0.00-0.04); it is a measurement of
this split and is reported as such.

## Summary

All ten non-null rows reproduce the stage-2 conclusions: residual beat-locking delta 0.228-0.238 with
30-32 of 34 participants positive and p < 1e-4; H1 and H3 equivalence within +-0.10 delta in every row;
the reservoir's margin over its weight-shuffled twin within +-0.011 in every row, including rho = 0 (no
recurrence, R - Rs = 0 by construction) and membrane timescales of 78, 391 and 977 ms. The reservoir's
seed, spectral radius and integration time, and the TRF's feature set and kernel length, change nothing
about what is detected. No row flipped.
