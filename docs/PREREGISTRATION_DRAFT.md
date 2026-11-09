# Pre-registration draft (for the author's edit; not yet timestamped)

Title: A fixed spiking reservoir as a beat-locking detector for naturalistic-music EEG:
calibration and detector-power comparison

Status: DRAFT v0.2, 2026-11-09, ready to freeze on the author's confirmation. All values are now concrete; the document is frozen (timestamped by its commit) before
any residual-based statistic is computed on real data. The pilot analyses already run
(NMED-T songs 21/28/30 tagging; Weineck alignment checks; synthetic calibration) are
disclosed as exploratory and are excluded from confirmatory claims.

## 1. Questions

Q1 (detector power). On single-listen EEG during naturalistic music, how often does each
detector identify beat-locked activity at a matched false-positive rate, and how does the
fixed LIF reservoir compare with linear tagging and with trivial nonlinear statistics?

Q2 (beyond a maximal linear model). After a cross-validated multi-feature forward TRF is
subtracted, does the residual carry beat-locked structure detectable by any detector, and
is the reservoir's sensitivity to it higher than that of the trivial nonlinear statistics?

Not asked: whether the brain "entrains" (oscillator vs evoked). Q2 can only establish
structure beyond the stated linear model.

## 2. Datasets and units of analysis

* Weineck, Wen & Henry 2022 (OSF y5xhs, CC BY 4.0): 34 participants, 13 tempi (1-4 Hz),
  32 channels; trials with unambiguous stimulus assignment only for Q2; tempo-known trials
  for Q1. Primary dataset for the tempo factor.
* NMED-T (Stanford SDR, CC BY): 20 participants, 10 songs, 125 channels; Q1 at song level;
  Q2 only if the ten tracks are purchased and aligned.
* Damsma et al. 2025 (OSF ghp94): positive control (known evoked structure, 5 tempi).
Unit of inference: participant. Trials are averaged within participant x tempo.

## 3. Pre-specified pipeline

Drive: EEG at 256 Hz, average reference, 0.5-30 Hz, one fronto-central cluster mean
(Weineck: Fz, FC1, FC2, Cz, F3, F4, C3, C4; NMED-T: the group-PC1 spatial filter of
Losorelli 2017) z-scored per trial. One drive only.

Reservoir: `experiment_zero.LIFReservoir`, N = 256, beta = 0.05, theta = 0.5, rho = 0.9,
seed 42 primary; seeds 7 and 99 as replication; weights shuffled (same rho) as instrument
control; rho in {0, 0.3, 1.2} as robustness.

Detectors (identical statistic, windowing and null for all), `weineck/tagging.py`:
* Tagging statistic: Welch PSD (Hann, 10 s segments, 50 % overlap) of the per-trial drive;
  at k x tempo (k in {1, 2}) the bin is compared with a local quadratic baseline fitted to
  the bins 0.15-0.8 Hz away (other harmonics excluded); z = (bin - baseline) / sd of the
  baseline residuals; the trial statistic is the max over k. It is computed at every one
  of the 13 grid tempi for every trial.
* L: statistic of the drive; N0: of the TRF residual (Q2); N2a: of the 0.5-8 Hz Hilbert
  envelope; N2b: of the square; R: of the reservoir unit-PC1; R_pop: of the population
  rate; Rs: of the unit-PC1 with shuffled recurrent weights (same spectral radius).
  Primary reservoir readout: R (unit-PC1). Reservoir: `experiment_zero.LIFReservoir`,
  N = 256, beta 0.05, theta 0.5, rho 0.9, seed 42; seeds 7 and 99 and rho in {0, 0.3,
  1.2} as robustness rows.
* Null (stimulus-label shuffle): per participant, the observed score is the mean over
  trials of the statistic at each trial's own tempo; the null distribution re-labels every
  trial with another grid tempo more than 5 % away (500 shuffles) and the participant's
  z is (observed - null mean) / null sd. Under the null the own-tempo and other-tempo
  statistics are draws from the same distribution. Simulated false-positive rate of the
  group test 0.01-0.04 (`calibration/power_q2.py`).
* Rejected nulls (simulation, kept for the record): testing a neighbour-debiased score
  against zero (false positives 0.08-0.26 from residual spectral bias), a pseudo-tempo
  label permutation (0.10-0.36; adjacent pseudo-tempos are correlated, labels not
  exchangeable), circular shift and phase randomisation (invariant for magnitude
  statistics on a periodic grid; pilot).

Linear model for Q2: ridge forward TRF, lags 0-400 ms, features spectral flux, beat
onsets, envelope, envelope derivative (Weineck features at 128 Hz), lambda by nested CV
within participant, leave-one-trial-out prediction; residual = EEG minus prediction.

## 4. Hypotheses and decision rules

Unit of inference: participant; one participant z per statistic (Section 3). Group tests:
one-sided Wilcoxon signed-rank on participant z's (alpha 0.05) for existence claims; two
one-sided tests (TOST) on paired participant differences for equivalence claims.

H1 (Q1, drive): participant z of R equals that of L. TOST bounds +-0.5 z. Outcomes: R > L
(reservoir adds detection power), equivalent, R < L (loses power). All reportable. The
calibration (Section 6) sets the prior expectation at equivalence.

H2 (Q2, existence): participant z of N0 on the TRF residual > 0 (Wilcoxon). Secondary:
the same for R. If H2 is not supported, Q2's detector comparison is descriptive only.

H3 (Q2, conditional on H2): participant z of R versus N0, N2a and N2b on the residual,
TOST bounds +-0.5 z; a positive one-sided test (R > each baseline) is the only outcome
that supports the reservoir adding sensitivity to nonlinear residual structure.

Robustness rows (no hypothesis tests): seeds 7/99; rho sweep; Rs; spectral-flux-only TRF;
TRF lag range 0-600 ms; IAAFT surrogate of the residual.

## 5. Power (`calibration/power_q2.py`, `calibration/RESULTS.md`)

Simulated with the exact pipeline of Section 3 on pink-noise trials of Weineck-like
length with a planted beat-locked sinusoid of relative amplitude a (a^2 = fraction of
variance):

| a | n = 9, N = 40 | n = 9, N = 94 | n = 34, N = 40 | n = 34, N = 94 |
|---|---|---|---|---|
| 0 (null) | 0.02 | 0.04 | 0.01 | 0.03 |
| 0.02 | 0.10 | 0.28 | 0.41 | 0.82 |
| 0.04 | 0.92 | 1.00 | 1.00 | 1.00 |
| 0.06 | 1.00 | 1.00 | 1.00 | 1.00 |

Decision: the minimum of 40 one-to-one trials per participant is adequate to detect a
residual beat component of a >= 0.04 with the nine participants available; a component of
a = 0.02 requires the full 34-participant cohort with >= 94 trials. The study therefore
runs first on the nine participants; the remaining 25 are downloaded only if H2 is not
supported but the participant z's are predominantly positive (an underpowered signal).

## 6. Calibration (to be completed before unblinding Q2)

Synthetic drives (sinusoid, evoked kernel, forced oscillator; pink noise; SNR 0.05-0.4;
tempi 1-4 Hz, 8 repetitions) through every detector (`calibration/RESULTS.md`): the
reservoir's unit-PC1 detection probability equals the linear detector's in every cell to
within one repetition (max |difference| 0.12); the weight-shuffled reservoir is
indistinguishable from it; gain 1.42-1.44 flat over 1-4 Hz with zero measurable group
delay; population rate and envelope/square statistics far weaker; no detector separates
evoked from oscillator drives at any SNR. Consequence for H1: the prior expectation is
equivalence of R and L; a departure in either direction on real data would be the
finding.

## 7. Exclusions

Weineck trials are used only when the stimulus is identified one-to-one by duration
(TRF-based and tempo-tagging resolution of the rest failed their self-tests; see
`weineck/README.md`); tempo-level analyses may add ambiguous trials whose candidates share
a tempo. Participants with fewer than 40 one-to-one trials are excluded;
channels flagged bad by amplitude criterion (> 5 SD of the trial's channel-median SD); the Weineck aux channel `33`.

## 8. Disclosure

Exploratory analyses already run are listed in `WEEK1_ASSESSMENT.md` and
`pilot/RESULTS.md`; none used the Q2 residual statistic on real data.
