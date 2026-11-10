# Identifiability map for the oscillator-vs-evoked held-out-tempo test (EXPLORATORY; methods contribution)

Committed 2026-11-10 before any cell was run. Pre-registration frozen at `935c80a` untouched; no
committed model is tuned here.

## Question

Given the Theory 3 decision rule (`docs/OSCILLATOR_DECISION_RULE.md`), how large an oscillator
contribution could be detected, at what SNR and with how many trials and tempi? The headline to
compute: *at Weineck's operating point (held-out r ~ 0.04, ~40 trials per tempo, 12 training
tempi), an oscillator contributing at least W % of the stimulus-locked response would be detected
with at least 80 % power.*

## Generative worlds (reuse of the recovery / false-positive code)

Per simulated participant k, a real participant's fitted kernels are used (cycling through the 34):
* evoked kernel: ridge TRF (4 features, 0-400 ms, committed lambda) fitted on all of that
  participant's one-to-one trials;
* oscillator kernel: ridge from the Hopf-bank outputs alone (committed configuration alpha -0.5,
  gain 1, 60 outputs x 13 lags) to the same EEG.
Trials are drawn with replacement, per tempo, from the pool of real stimulus-feature vectors of
the participant's subgroup; the target is the fronto-central channel mean. Signal for a trial:
  s = (1 - w) * P_evoked / sd(P_evoked) + w * P_osc / sd(P_osc),
w in {0, 0.1, 0.25, 0.5, 1} (w = 0 evoked-only, w = 1 oscillator-only; w is the amplitude share,
the variance share is w^2 / (w^2 + (1-w)^2)). Noise: Gaussian with the participant's residual
spectrum smoothed over 0.5 Hz (no spectral lines), scaled so that the held-out r of the evoked model
at w = 0 hits the target; the realized held-out r is recorded at every cell.

## Grid

* held-out r target in {0.02, 0.04 (Weineck), 0.08, 0.16};
* trials per tempo in {20, 40 (Weineck), 80, 160};
* training tempi: 12 (Weineck) for the full w x r x trials grid (80 cells); the n-tempi axis
  {4, 8, 12} is run at Weineck's r and trial count for all w (10 further cells).
* per cell: 20 simulated datasets x 20 participants (the brief asked for 50; see cost note), the
  identical leave-one-tempo-out comparison (d_short, d_long, aug, aug_lin) and the committed rule.
* recorded: detection rate (rule says "oscillator supported" when w > 0), false-positive rate
  (rule fires when w = 0), realized held-out r, median delta_r.

## Cost controls (stated, not hidden)

The brief's grid (240 cells x 50 datasets x 20 participants) with the full nested-lambda pipeline
is about 700 CPU-hours; this box has 4 cores. To make the map computable tonight without changing
what is compared:
1. lambda is fixed per model at the modal value chosen on the real data (no tuning on simulated
   data; the committed models are not retuned);
2. the target is the fronto-central mean (the metric is defined on those channels anyway);
3. every fold is computed from per-trial sufficient statistics (X'X, X'Y, column sums), so no
   lag matrix is rebuilt inside the simulation;
4. 20 datasets per cell and the reduced n-tempi axis as above. If time allows, datasets are
   extended to 50 at Weineck's operating point.

## Reporting rule

Every cell is reported. Detection and false-positive rates per cell in
`weineck/results/identifiability.json`; a heat map of detection rate versus (r, trials) per w with
Weineck's operating point marked (`docs/figures/identifiability_*.png`); the headline W solved by
interpolation of detection rate over w at the operating point, with the false-positive rate at
that point stated beside it. If the false-positive rate exceeds 0.05 anywhere, that is reported as
a property of the rule, not corrected.

## Addendum (2026-11-10, after the five operating-point cells had run)

At the operating point the detection rate was 0.00 at w in {0.1, 0.25, 0.5} and 1.00 at w = 1, so
the 80 % point falls between w = 0.5 and 1 and a linear interpolation over that interval is coarse.
Four refinement cells, w in {0.6, 0.7, 0.8, 0.9} at the operating point only, were added to the
queue. The headline W is solved on the refined w grid; the coarse-grid interpolation (0.90) is
reported beside it. No other cell and no model or rule was changed.
