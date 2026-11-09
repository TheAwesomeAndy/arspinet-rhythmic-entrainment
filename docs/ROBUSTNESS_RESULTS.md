# Robustness grid results (exploratory; run after the stage-2 merge)

Rule (docs/ROBUSTNESS_PLAN.md): 'H2 robust' = residual delta > 0 with one-sided Wilcoxon p < .01 in every row except IAAFT; 'H1/H3 equivalence robust' = TOST (+-0.10 delta) passes in every row. Every row is reported.

| row | tau (ms) | held-out r | median residual delta (H2) | positive / n | Wilcoxon p | H1 TOST (drive R vs L) | H3 TOST (resid R vs N0) | R - Rs (median delta) | H2 p<.01 |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.005) | pass (-0.001) | -0.005 | yes |
| seed7 | 78 | +0.036 | +0.228 | 31 / 34 | 0.0000 | pass (-0.004) | pass (-0.000) | -0.002 | yes |
| seed99 | - | - | in progress (2/34) | | | | | | |
| rho0 | - | - | not run | | | | | | |
| rho0.3 | - | - | not run | | | | | | |
| rho1.2 | - | - | not run | | | | | | |
| beta0.01 | - | - | not run | | | | | | |
| beta0.004 | - | - | not run | | | | | | |
| trf_flux | - | - | not run | | | | | | |
| trf_long | - | - | not run | | | | | | |
| iaaft | - | - | not run | | | | | | |

**H2 robust (rule): YES.**  **H1/H3 equivalence robust (rule): YES.**

No row flipped.

