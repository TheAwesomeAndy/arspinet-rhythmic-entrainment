# Exploratory underfitting check for H2 (not in the frozen pre-registration)

Run 2026-11-09 after the stage-2 merge; confirmatory results (`docs/STAGE2_RESULTS.md`)
unchanged. Scripts: `weineck/underfit_check.py`, `weineck/underfit_merge.py`; outputs
`weineck/results/underfit_chunk{1,2,3}.json`, `underfit_merged.json`. All 34 participants,
same one-to-one trials, preprocessing, features (spectral flux, beat onsets, envelope,
derivative), lags (0-400 ms), statistic (shared tagging z at the 13 grid tempi on the
fronto-central residual) and null (stimulus-label shuffle) as the confirmatory Q2 pipeline.

Decision rule, fixed before running: a linear-world residual delta comparable to 0.228 means
H2 is explained by underfitting; a linear-world delta near zero while the real data give 0.228
means the residual is structure the linear model misses.

## Design

* **A. Pooled TRF, leave-one-participant-out**: kernel fitted on the other 33 participants'
  trials (normal-equation moments summed), lambda by inner leave-one-participant-out on the
  training pool; the held-out participant's residual scored as in Q2.
* **B. Prediction tagging**: the within-participant leave-one-trial-out TRF of Q2 (same
  lambda per trial); the tagging statistic of the prediction itself.
* **C. Linear-world simulation**: Y_sim = P_full + noise, with P_full from the kernel fitted
  on all the participant's trials and noise = Gaussian with the residual's amplitude spectrum
  smoothed over ~0.5 Hz (spectral lines removed), exact per-channel variance match, one random
  phase vector per trial shared across channels. The variance split is preserved, so the
  held-out r matches the real data; the only stimulus-locked content is the linear prediction.
  Y_sim goes through the identical pipeline. (Plain phase randomisation of the residual would
  be wrong here: it keeps the residual's beat-locked spectral line, and a magnitude statistic
  would still see it.)

## Results (n = 34; median per-trial standardized effect delta; participants with z > 0; one-sided Wilcoxon)

Held-out fronto-central r: within-participant 0.036, pooled 0.038, linear-world 0.036 (matched).

| quantity | median delta | positive | p |
|---|---|---|---|
| drive (real EEG) | +0.315 | 0.97 | < 1e-4 |
| residual, within-participant TRF (= stage 2) | +0.228 | 0.91 | < 1e-4 |
| B: TRF prediction itself | +0.681 | 1.00 | < 1e-4 |
| A: residual, pooled LOPO TRF | +0.245 | 0.88 | < 1e-4 |
| C: linear-world drive | +0.124 | 0.76 | 1e-4 |
| **C: linear-world residual** | **+0.039** | **0.65** | **0.087** |

Prediction delta / drive delta: median 2.08 (the prediction is nearly pure beat-locked
signal, so its standardized effect exceeds the drive's). Paired real residual > linear-world
residual: p < 1e-4.

## Reading, by the rule

**H2 is not explained by underfitting.** In a world where the only stimulus-locked content is
the fitted linear kernel, the identical pipeline leaves a residual beat-locking of 0.039; the
real data leave 0.228. Giving the linear model 33 participants' worth of data (A) does not
reduce the residual (0.245) or raise the held-out r (0.038 vs 0.036), so ridge shrinkage of a
true linear kernel does not account for the gap either. The linear world reproduces only
0.124 of the real drive's 0.315: a four-feature linear time-invariant model of these
stimulus features misses a large share of the beat-locked power in single-listen EEG, and
that share is what H2 measures.

What the gap is remains open: nonlinear stimulus-locked responses (adaptation,
amplitude-dependent latency), acoustic features outside the four used, non-stationarity
across a trial, or internally generated rhythmic activity. None of this is evidence for an
oscillator; the oscillator question is the subject of the separate, exploratory Theory 3
(`docs/OSCILLATOR_DECISION_RULE.md`).

Limitations: one kernel family (ridge, 0-400 ms, four features); the linear world uses the
within-participant kernel, so model misspecification in the real data has no counterpart in
the simulation by construction; the noise model is Gaussian with a smoothed spectrum.
