# Pre-registration draft (for the author's edit; not yet timestamped)

Title: A fixed spiking reservoir as a beat-locking detector for naturalistic-music EEG:
calibration and detector-power comparison

Status: DRAFT v0.1, 2026-11-09. Numbers in brackets are placeholders to be fixed before
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

Detectors (identical null and windowing for all):
* L: Welch tagging z of the drive at k x tempo, k in {1, 2}, 20 s Hann segments (trial
  concatenation within tempo), neighbour bins 0.08-0.5 Hz excluding harmonics.
* N1: phase-locking value of the TRF residual at k x tempo (Q2 only).
* N2: tagging z of the Hilbert envelope (0.5-8 Hz) and of the squared drive/residual.
* R: reservoir per-unit tagging z -> fraction of units with z > 1.96, and unit-PC1 z.
* Rs: R with shuffled weights.
Primary statistic for R: unit-PC1 z (pre-specified; the per-unit fraction is secondary).

Nulls: neighbour-frequency baseline (primary); neighbour-tempo grids for phase-binned
statistics; circular shifts and phase randomisation are NOT used as nulls for magnitude
statistics (shown non-diagnostic for periodic grids in the pilot).

Linear model for Q2: ridge forward TRF, lags 0-400 ms, features spectral flux, beat
onsets, envelope, envelope derivative (Weineck features at 128 Hz), lambda by nested CV
within participant, leave-one-trial-out prediction; residual = EEG minus prediction.

## 4. Hypotheses and decision rules

H1 (Q1): detection probability at z > 1.96 differs between R and L. Two one-sided
equivalence tests on the participant-level paired difference in detection probability,
bounds +-[0.10]. Outcomes: R > L (reservoir adds power), equivalent, R < L (reservoir
loses power). All three are reportable.

H2 (Q2): residual beat-locked structure exists: participant-level z of N1 at the beat or
2f exceeds 0 (one-sided Wilcoxon, alpha 0.05, 13 tempi pooled). If H2 is not supported,
Q2's detector comparison is reported descriptively only.

H3 (Q2, conditional on H2): R's residual sensitivity vs N1/N2, same equivalence frame,
bounds +-[0.2] in participant-level z.

Robustness rows (not hypothesis tests): seeds 7/99; rho sweep; Rs; shifted-residual
surrogate; IAAFT surrogate of the residual; spectral-flux-only TRF.

## 5. Power

n = 34 (Weineck): paired test has 80 % power for d_z ~ 0.5; n = 20 (NMED-T): d_z ~ 0.66.
Equivalence bounds above are the smallest effects the design can exclude.

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
a tempo. Participants with < [40] usable trials are excluded;
channels flagged bad by amplitude criterion [> 5 SD]; the Weineck aux channel `33`.

## 8. Disclosure

Exploratory analyses already run are listed in `WEEK1_ASSESSMENT.md` and
`pilot/RESULTS.md`; none used the Q2 residual statistic on real data.
