# Robustness grid for the stage-2 results (EXPLORATORY sensitivity analyses)

Added 2026-11-09 after the stage-2 merge (`docs/STAGE2_RESULTS.md`); pre-registration frozen
at `935c80a` and its files untouched. Committed before any robustness row was run.

## Rows (all 34 participants, one-to-one trials, Q2 preprocessing; `weineck/robustness.py`)

| row | change relative to the stage-2 baseline | what it tests |
|---|---|---|
| baseline | seed 42, rho 0.9, beta 0.05 (tau 78 ms), 4-feature TRF 0-400 ms | reference (recomputed by the same script) |
| seed7, seed99 | reservoir weight seed | seed dependence of R |
| rho0, rho0.3, rho1.2 | recurrent spectral radius (rho 0 removes the recurrence) | does recurrence do anything |
| beta0.01, beta0.004 | membrane leak; tau = 1/(beta * fs) at fs = 256 Hz: 78 / 391 / 977 ms | integration time |
| trf_flux | TRF with spectral flux only | feature dependence of the residual |
| trf_long | 4-feature TRF with lags 0-600 ms | kernel-length dependence of the residual |
| iaaft | IAAFT surrogates of the fronto-central residual, 200 per participant (amplitude spectrum and value distribution preserved) | null row |

Rs (reservoir with shuffled recurrent weights, rescaled to the row's rho) is computed inside
every row, so R minus Rs is reported for each.

## Metrics (identical to stage 2)

Per participant and statistic (N0 linear, N2a envelope, N2b square, R unit-PC1, R_pop, Rs):
the shared tagging statistic at the 13 grid tempi, participant z against the stimulus-label
shuffle (500 re-labellings, fixed seed), and the per-trial standardized effect delta; on both
the drive and the TRF residual. Group: H2 = one-sided Wilcoxon on participant z of the residual
N0 (and R); H1 = TOST (+-0.10 delta) on delta(R) - delta(L) for the drive; H3 = TOST on
delta(R) - delta(N0) for the residual; R - Rs = median paired delta difference.

## Reporting rule (fixed here)

Every row is reported in one table regardless of outcome (`docs/ROBUSTNESS_RESULTS.md`,
`weineck/results/robustness_table.json`): rows x [median residual delta (H2), participants
positive / 34, Wilcoxon p, H1 TOST pass, H3 TOST pass, R minus Rs].

* "H2 robust" = the residual delta stays > 0 with one-sided Wilcoxon p < .01 in every row
  except the IAAFT null row.
* "H1/H3 equivalence robust" = TOST (+-0.10 delta) still passes in every row.
* Any row that flips is named in the results, not dropped.

## Expectation recorded for the IAAFT row

IAAFT preserves each trial's amplitude spectrum, including its spectral line at the trial's own
tempo, and the tagging statistic is a magnitude statistic. The surrogates therefore destroy the
phase of the beat-locked component but not its power, and the H2 delta is NOT expected to
collapse toward zero under IAAFT; the pilot showed the same for plain phase randomisation
(`pilot/RESULTS.md` section 4). The null that destroys beat locking for this statistic is the
stimulus-label shuffle used throughout. The IAAFT row is run exactly as specified and reported
as it comes out; if the delta does collapse, that expectation was wrong and will be said so.

## Execution

One process per row, OMP/MKL/OPENBLAS threads = 1, fixed seeds, start and end times logged;
parallel up to the cores not used by the running Theory 3 jobs. Commit messages state that the
rows were run after the stage-2 merge.
