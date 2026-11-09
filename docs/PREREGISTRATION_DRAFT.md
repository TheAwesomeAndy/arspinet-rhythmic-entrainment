# Pre-registration draft (for the author's edit; not yet timestamped)

Title: A fixed spiking reservoir as a beat-locking detector for naturalistic-music EEG:
calibration and detector-power comparison

Status: v1.0, FROZEN 2026-11-09 at commit `935c80a` (the remote refuses tag refs, so the commit hash is the timestamp; a local tag `prereg-v1` points to it). No residual-based statistic had been computed on real data at the time of freezing. All values are now concrete; the document is frozen (timestamped by its commit) before
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

Effect size: because a participant's z grows with sqrt(N_trials), equivalence claims use the
per-trial standardized effect delta = mean over trials of (own-tempo statistic - mean
other-tempo statistic) divided by its sd across trials; delta is independent of trial count.
Calibration mapping (Section 5): a planted beat component of relative amplitude a = 0.02,
0.03, 0.04 gives delta = 0.045, 0.093, 0.208.

H1 (Q1, drive): delta of R equals delta of L. TOST bounds +-0.10 delta (about a 3 %
amplitude component). Outcomes: R > L (reservoir adds detection power), equivalent, R < L
(loses power). All reportable. The calibration (Section 6) sets the prior expectation at
equivalence. With n = 9 the equivalence tests are underpowered, so "not equivalent" is the
likely stage-1 outcome and is NOT read as "different"; equivalence is decided at stage 2.

H2 (Q2, existence): participant z of N0 on the TRF residual > 0 (Wilcoxon). Secondary:
the same for R. If H2 is not supported, Q2's detector comparison is descriptive only.

H3 (Q2, conditional on H2): delta of R versus N0, N2a and N2b on the residual, TOST bounds
+-0.10 delta; a positive one-sided test (R > each baseline, paired Wilcoxon on delta) is the
only outcome that supports the reservoir adding sensitivity to nonlinear residual
structure. Same underpowered-at-stage-1 caveat as H1.

Robustness rows (no hypothesis tests): seeds 7/99; rho sweep; Rs; spectral-flux-only TRF;
TRF lag range 0-600 ms; IAAFT surrogate of the residual.

## 5. Power and the two-stage design (`calibration/power_q2.py`, `calibration/RESULTS.md`)

Simulated with the exact pipeline of Section 3 on pink-noise trials of Weineck-like
length with a planted beat-locked sinusoid of relative amplitude a (a^2 = fraction of
variance); 200 Monte-Carlo replicates per cell; power at the stage alpha.

| a | delta | stage 1: n = 9, alpha 0.01, N = 40 / 75 / 94 | stage 2: n = 34, alpha 0.04, N = 40 / 75 / 94 |
|---|---|---|---|
| 0 (null) | 0.000 | 0.00 / 0.01 / 0.01 | 0.04 / 0.04 / 0.04 |
| 0.02 | 0.045 | 0.01 / 0.04 / 0.07 | 0.41 / 0.61 / 0.77 |
| 0.03 | 0.093 | 0.14 / 0.32 / 0.39 | 0.96 / 1.00 / 1.00 |
| 0.04 | 0.208 | 0.81 / 0.98 / 0.99 | 1.00 / 1.00 / 1.00 |

Pre-specified two-stage rule for H2 (fixed before any residual statistic is computed):
* Stage 1: the nine participants already on disk (subj 10, 11, 12, 13, 14, 16, 17, 18;
  participant 18 has three of four blocks). H2 is supported at stage 1 only if the one-sided
  Wilcoxon p < 0.01.
* Stage 2 is run whatever stage 1 shows, unless stage 1 already supports H2: the remaining
  25 participants are downloaded and H2 is tested on all 34 at alpha 0.04. The two looks
  spend alpha 0.01 + 0.04 = 0.05 in total (Bonferroni bound, conservative under the
  positive dependence of the two samples).
* Interpretation of a null: a non-significant stage 1 is inconclusive for components below
  a = 0.04 (power 0.81 at 40 trials); a non-significant stage 2 is inconclusive below
  a = 0.03 (power 0.96) and says little about a = 0.02 (power 0.41-0.77). Neither is
  evidence that the residual carries no beat-locked structure.
* H1 and H3 (equivalence) are reported descriptively at stage 1 and decided at stage 2.
The decision to download is therefore not conditional on the stage-1 result.

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
a tempo. Participants with fewer than 40 one-to-one trials are excluded (stage 1: none of the nine falls below; checked before freezing: 75, 94, and the rest reported in `weineck/README.md` as the runs complete);
channels flagged bad by amplitude criterion (> 5 SD of the trial's channel-median SD); the Weineck aux channel `33`.

## 8. Disclosure

Exploratory analyses already run are listed in `WEEK1_ASSESSMENT.md` and
`pilot/RESULTS.md`; none used the Q2 residual statistic on real data.
