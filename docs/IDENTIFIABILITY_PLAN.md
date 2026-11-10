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

## Addendum A3 (exploratory; committed 2026-11-10 before any A3 cell or A3 statistic was computed)

World A is the grid as committed above (all 94 cells, unchanged). The committed rule, the four
models, their fixed lambdas, the noise bank and the calibrated gamma are not changed. Every A3 cell is
reported.

**Why.** On the real stimulus pool the evoked and oscillator generating predictions correlate at a
median r of 0.53 across the 34 kernel pairs (`prediction_overlap.json`). Two consequences are
untested: (i) in World A the signal variance at mid w is below its w = 0 value, so mixed worlds run at
lower total SNR; (ii) part of P_o is expressible by the TRF design, so a mixture may be hard to detect
because of collinearity rather than because of the rule. The fixed-lambda shortcut is also untested.

**A3.1 World B (power-matched).** Same generator as World A, s = alpha P_e + beta P_o with
alpha = (1 - w)/sd_e and beta = w/sd_o, but s is rescaled at every w so that its pooled within-trial
variance over the stimulus pool equals that of World A's w = 0 signal (P_e/sd_e) for the same
participant. World B at w = 0 is therefore identical to World A at w = 0, and the calibrated gamma
gives the same total SNR at every w. sd_e and sd_o are the pooled within-trial sds of P_e and P_o
over the simulation pool, so w is the amplitude share on the stimuli actually simulated. Operating
point only (r 0.04, 40 trials per tempo, 12 training tempi); w in {0, 0.1, 0.25, 0.5, 0.6, 0.7, 0.8,
0.9, 1}; 20 datasets x 20 participants per cell.

**A3.2 World C (unique oscillator).** P_o is replaced by P_o_perp, the residual of P_o after ordinary
least-squares projection onto the short TRF design (4 features, 0-400 ms, 109 columns with bias: the
design of the evoked kernel and of the augmented model's TRF block), fitted per participant kernel over
the whole stimulus pool. P_o_perp is a fixed kernel on the augmented design (Hopf block unchanged, TRF
block minus the projection coefficients), so it stays a stationary stimulus-driven generator; it is
orthogonal to the TRF design over the pool, not within every held-out tempo. P_o_perp is normalised to
unit pooled within-trial sd; w is its amplitude share; power-matched as in World B. Same operating point,
w grid and dataset counts. Reported alongside: R^2 of P_o on the short TRF design (the TRF-expressible
fraction), per participant and median; and, descriptively only, R^2 on the long TRF design (0-1000 ms,
whose span contains the short one), because the best-TRF competitor in the rule includes d_long.

**A3.3 Nested-lambda check.** World A generator at the operating point, w in {0, 0.5, 0.9, 1}, 10
datasets x 20 participants. For every model and every outer held-out tempo, lambda is chosen from
{0.1, 1, 10, 100, 1000} by inner leave-one-tempo-out over the 12 training tempi, criterion the mean
held-out per-trial r over all inner held-out trials, then refit on all 12 training tempi; this is the
procedure in `oscillator_heldout.loto`. The oscillator configuration is fixed at the committed modal one
(Hopf alpha -0.5 for aug, linear alpha -2.0 for aug_lin), because the stimulus statistics were stored for
that configuration only; the real pipeline also selects the configuration. Compared against the
fixed-lambda World A cells at the same w: detection rate and median delta r, plus the distribution of
chosen lambdas per model.

**A3.4 World A refinement.** w in {0.6, 0.7, 0.8, 0.9} at (r 0.08, 40 trials, 12 tempi) and (r 0.04, 160
trials, 12 tempi), 20 datasets x 20 participants, so the W80 entries at those cells are interpolated
between neighbouring w at most 0.1 apart.

**A3.5 Merge.** W80 for World A (operating point and the two refined cells), World B, World C and the
nested-lambda check side by side, each with the false-positive rate (w = 0) and Clopper-Pearson 95 %
intervals for every rate. W80 is linear interpolation of detection rate over w between the two grid
points that bracket 0.80; "not reached" if no w reaches 0.80. For the nested-lambda check, with w in
{0, 0.5, 0.9, 1} only, W80 is reported as the bracket. `docs/IDENTIFIABILITY_RESULTS.md` keeps the
original headline as committed and adds the A3 table; FRAMING item 11 and the README status are updated.

**Decision rule (fixed now).**
* If World C's W80 <= 0.6: the headline becomes "the rule detects TRF-inexpressible oscillator
  structure above X % amplitude" (X = World C's W80), and the 0.89 of World A is relabelled as a
  collinearity effect.
* If W80 stays > 0.8 in World B, World C and the nested-lambda check: the 0.89 headline stands as a
  property of the rule. "Not reached" counts as > 0.8. For the nested-lambda check, "> 0.8" means the
  detection rate at w = 0.5 is below 0.80 and the bracket therefore lies above 0.5, with the rate at
  w = 0.9 reported beside it.
* Any other outcome (for example World C's W80 between 0.6 and 0.8, or World B or the nested check at or
  below 0.8 while World C is above 0.6) is not covered by this rule. It will be reported as such, with
  the numbers, and neither relabelling is made.

**Cost.** About 26 fixed-lambda cells at roughly 13 min each and 4 nested cells whose cost is set by the
inner loop (78 distinct training sets x 5 lambdas x 4 models per participant), single-threaded, 4
workers. If the nested cells would exceed about 6 hours, the dataset count stays at 10 and that is
stated; nothing else is cut.
