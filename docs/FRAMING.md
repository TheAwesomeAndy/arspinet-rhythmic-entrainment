# Framing: the question is the contribution

Updated 2026-11-09 after stage 2 (`docs/STAGE2_RESULTS.md`). Evidence labels: **measured**
(real data), **simulated** (synthetic drives or Monte-Carlo), **literature**.

Working title (v2):
**What can scalp EEG tell us about neural entrainment to music? A pre-registered,
instrument-calibrated test of beat-locking beyond a linear encoding model**

Shorter alternative: *Beat-locking beyond a linear encoding model: what a calibrated spiking
reservoir does and does not add in naturalistic-music EEG*

## The core question

When the brain "locks" to a musical beat, the field disagrees about whether that reflects an
internal oscillator being captured or evoked responses stacking up (Nozaradan 2011; Novembre
& Iannetti 2018; Doelling 2019; Doelling & Assaneo 2021; Damsma 2025). We ask a narrower,
answerable question underneath it: **which classes of measurement on single-listen scalp
EEG can carry information about that distinction, does an interpretable fixed nonlinear
instrument add anything to them, and how much beat-locked structure does a maximal linear
encoding model leave unexplained?** The pre-registered test (frozen at commit `935c80a`,
addendum A1) was designed to be informative whichever way it came out; it has now come out.

## Results (stage 2, 34 participants, frozen rules)

1. **H2 supported: beat-locking beyond this linear encoding model** (measured). After a
   cross-validated four-feature ridge TRF (spectral flux, beat onsets, envelope, derivative;
   0-400 ms lags; nested lambda) is subtracted, the residual still carries beat-locked power
   at the trial's own tempo relative to other grid tempi: median per-trial standardized
   effect delta = 0.228, 31 of 34 participants positive, one-sided Wilcoxon p < 1e-4 against
   a stimulus-label shuffle null. By the simulated calibration mapping this corresponds to
   roughly a 4 % amplitude component. **This is a statement about the linear model, not
   about oscillators**: the TRF predicts single trials at r ~ 0.04 and removes about a
   quarter of the drive's beat-locking effect (delta 0.317 -> 0.228), so underfitting of a
   stimulus-locked response at single-listen SNR is the parsimonious account until the
   underfitting check (Publication plan, item 1) says otherwise. Envelope and squared
   statistics on the residual are null: what survives is phase-coherent power at the beat
   and its octave, not amplitude modulation.
2. **H1 and H3: the reservoir is equivalent to the linear statistic** (measured). On the
   drive, delta(reservoir unit-PC1) - delta(linear) = -0.005, TOST within +-0.10 passes; on
   the residual the same, -0.001. The reservoir exceeds the envelope and square statistics
   only because those are null. A reservoir with shuffled recurrent weights (same spectral
   radius) matches the real one (0.219 vs 0.223). Its population mean rate loses the
   information at every tempo.
3. **A class-level limit, in the configurations calibrated** (simulated). Every
   stimulus-locked magnitude statistic we tested, linear tagging, envelope and squared
   statistics, and the reservoir read out linearly across its units, detected an
   evoked-kernel drive and a forced Stuart-Landau oscillator with the same sensitivity at
   every SNR and tempo tested. In these configurations such statistics do not distinguish
   the oscillator from the evoked account; this is consistent with Damsma et al. 2025 and
   Doelling & Assaneo 2021, who reached the same conclusion for frequency tagging and
   tempo-selective enhancement with parametric models. The design implication is positive:
   phase-sensitive, model-comparison or perturbation designs (missing pulses, tempo changes,
   offset persistence with ringing controls) are where the distinction can live.
4. **Null models, measured on real data.** Circular shift and phase randomisation leave
   beat-locking magnitudes unchanged on a periodic grid; a neighbour-debiased score tested
   against zero and a pseudo-tempo label permutation inflated simulated false positives
   (0.08-0.26 and 0.10-0.36) for identifiable reasons; the stimulus-label shuffle held the
   nominal rate (0.00-0.04, simulated). The rejected nulls are recorded in the
   pre-registration.
5. **What single-listen data can see** (measured, NMED-T): beat tagging detectable in 5-90 %
   of single listens depending on the song, mostly at metrical subdivisions. We found no
   published single-listen tagging table for NMED-T; if one exists we will cite it.
6. **The instrument, characterised** (simulated and measured): gain 1.42-1.44 flat over
   1-4 Hz, zero measurable group delay, firing rate 0.126-0.128 on every drive,
   weight-shuffled control indistinguishable. The canonical reservoir's linear readout is a
   scaled copy of its drive in the beat band; "fixed weights" is a calibration statement.

## Follow-up results (exploratory, after the stage-2 merge; pre-registration untouched)

7. **Not underfitting** (simulated and measured, `docs/UNDERFIT_CHECK.md`): a linear world built
   from the fitted kernels and the real stimulus features at the observed SNR leaves a residual
   delta of 0.039 against the real 0.228; a pooled 33-participant TRF leaves the real result
   unchanged (0.245). The residual is structure this linear encoding model misses, not noise from
   a model fitted on too little data.
8. **Theory 3 (oscillator encoding) not supported** (measured, rule fixed in advance,
   `docs/THEORY3_RESULTS.md`): at held-out tempi, Hopf, resonate-and-fire and linear oscillator
   banks added to the TRF do not predict EEG better than the TRF alone (median delta r = -0.010,
   3/34 participants positive; group-level -0.002), and there is no preferred-rate effect. The
   recovery and false-positive worlds behaved as required before the real data were touched.
9. **Robustness grid: no row flipped** (`docs/ROBUSTNESS_RESULTS.md`). Audit: the H2 statistic is
   the tagging of the TRF residual and never touches the reservoir, so the seed, rho and tau rows
   are identical by construction and are labelled so; the reservoir-sensitive quantities are the
   H1/H3 equivalence and R minus Rs, which also held. The IAAFT decomposition splits the residual
   effect into a spectral part the surrogates keep (0.156) and a phase-dependent part they destroy
   (0.045, 95 % CI [0.022, 0.072], 26/34 positive, p = 0.0003): the residual beat-locking is
   nonlinear and predominantly spectral, with a smaller but reliable phase-coherent component.
10. **The rise of the tempo curve toward 4 Hz is a cycle-count artefact**
    (`docs/CYCLE_COUNT_CONTROL.md`). Scored on a fixed number of beat cycles per tempo, the
    participant slopes of the tagging statistic over tempo fall from +0.48 z/Hz (p = 0.0001) to
    +0.015 z/Hz (p = 0.37) for the drive, and the same for the reservoir unit-PC1. Beat-locked
    power is present at all 13 tempi; there is no evidence of a rate preference.
11. **Identifiability map** (simulated, `docs/IDENTIFIABILITY_RESULTS.md`; 94 grid cells plus addendum cells,
    20 participants per simulated dataset; false-positive rate 0.00 in every evoked-only cell). Two tiers:
    (a) *Committed rule.* At Weineck's operating point (held-out r 0.04, 40 trials per tempo, 12 training
    tempi) the rule needs Hopf-specific oscillator structure supplying about 89 % of the stimulus-locked
    amplitude (99 % of its variance) for 80 % detection. This does not move with an eightfold change in SNR
    or trials, with 4 to 12 training tempi, with power matching (0.92), with the real pipeline's nested
    lambda selection (0.9-1.0), or with an oscillator restricted to its TRF-inexpressible part (80 % never
    reached); addendum A3's pre-committed decision is that the 0.89 headline stands as a property of the
    rule. What holds it there is the second criterion, the Hopf bank beating a linear oscillator bank, and
    the criterion-2 passes in World A depend on the committed lambda pair: they occur with lambda 10 for
    Hopf + TRF and lambda 1 for linear bank + TRF, and they vanish when both are fitted at lambda 1 (0/10
    datasets at w = 1). The 0.89 is therefore a property of the rule with its committed lambda pair, not a
    lambda-independent sensitivity to Hopf-specific structure.
    (b) *Exploratory, outside the committed rule.* The comparison against the TRF alone (criterion 1)
    reaches 80 % power at w = 0.58 in Worlds A and B and 0.47 in World C; the conservative bound is the
    largest, 0.58. On the real data criterion 1 itself failed (median delta r -0.010, 3/34 positive,
    p = 1.00). So, at about 80 % power and with fixed lambdas, the real data exclude oscillatory structure
    beyond the TRF supplying more than about 58 % of the stimulus-locked amplitude. Under the real
    pipeline's nested lambda the criterion-1 crossing is so far known only to lie between 0.5 and 0.9
    (World A); addendum A4 pins it.
    The Theory 3 null therefore does not exclude an oscillator at half the amplitude under the committed
    rule, and the exploratory reading bounds oscillatory structure beyond the TRF at roughly 58 % of the
    amplitude, pending A4. This is the methods contribution: a calibrated statement of what an
    encoding-model comparison can and cannot decide at single-listen SNR.

## Interpretability as the lens (planned)

Per-unit analyses (which units carry the beat, at which harmonics, stable across tempi and
seeds) are secondary and pre-registered. Honest scope: all units share one leak (beta =
0.05), so "timescale" means integration set by the recurrent weights; the beta sweep in the
publication plan (item 3) makes integration time an explicit factor.

## The bridge to the larger question (discussion, flagged as perspective)

Entrainment is the field's working model for how music takes hold of a listener. If what
scalp EEG measures at these tempi is dominated by stimulus-locked responses that a linear
model underfits rather than by oscillatory capture, the mechanism of being moved by rhythm
must be sought elsewhere: prediction and timing expectation, motor simulation, absorption.
This is a discussion point and a bridge to the author's longer-term interest in rhythmic
practice and absorptive states; it is not a result of this study and is written as such.

## Publication plan

Target: **IEEE Transactions on Neural Systems and Rehabilitation Engineering (TNSRE)**, as an
instrument-calibration and measurement-validity paper. Second choice: **IEEE Transactions on
Cognitive and Developmental Systems**. Must-adds before submission, in order:

1. **Underfitting check** (DONE, `docs/UNDERFIT_CHECK.md`; exploratory, labelled as such): (A) a group-level pooled TRF,
   leave-one-participant-out, same features and lags, with the Q2 residual statistic rerun;
   (B) the tagging statistic of the TRF prediction itself, to report how much of the drive's
   beat-locked power the linear model reproduces; (C) a linear-world simulation: fitted
   kernels convolved with each trial's real stimulus features plus noise matched to the
   observed held-out r (~0.04), run through the identical pipeline and null. Decision rule:
   a linear-world residual delta comparable to 0.228 means H2 is explained by underfitting;
   a linear-world delta near zero against the real 0.228 means the residual is structure the
   linear model misses.
2. **Held-out-tempo superposition test** (DONE as Theory 3, `docs/THEORY3_RESULTS.md`; identifiability map in progress), plus a cycle-count control on the tempo curve (DONE, `docs/CYCLE_COUNT_CONTROL.md`: the rise does not survive)
   (the number of beat cycles per trial rises with tempo and could drive the rising tagging
   curve on its own).
3. **Pre-registered robustness rows** (DONE, `docs/ROBUSTNESS_RESULTS.md`, no row flipped): seeds 7 and 99; rho in {0, 0.3, 1.2}; spectral-flux-
   only TRF; 0-600 ms lags; IAAFT surrogate of the residual; plus a beta / integration-time
   sweep (about 78, 390 and 980 ms).
4. **A TNSRE-style figure set** built from the existing results JSON: calibration curves
   with the evoked-vs-oscillator indistinguishability panel; rejected nulls; NMED-T
   single-listen table; the 13-tempo curve, drive vs reservoir, with the cycle-count control; the identifiability heat map; the Q2 residual result with
   its inconclusive region and the underfitting check.
5. **NMED-T generalization** of the Q2 pipeline (requires the ten tracks; alignment via the
   60-s click grid).

## What this contributes regardless of item 1's outcome

A pre-registered, calibrated test with its nulls validated and its rejected nulls recorded;
a measured answer to whether a fixed spiking reservoir adds detection power over linear
statistics in this setting (it does not, and a shuffled-weight copy does the same); a
quantified gap between what a maximal linear encoding model predicts and what single-listen
EEG carries at the beat frequency; and a demonstration, in the calibrated configurations,
of which measurement class cannot settle the oscillator question.
