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
| iaaft | - | - | in progress (5/34) | | | | | | |

**H2 robust (rule): YES.**  **H1/H3 equivalence robust (rule): YES.**

No row flipped.

