# Decision rules (frozen 2026-11-26, addendum A2, before any generative model output)

Supersedes EXPERIMENT_PLAN.md section 8 where they differ. Any later change is a dated addendum, never an
edit of this file. The SHA-256 of this file is recorded in the commit that freezes it.

## Units and evaluation set

* Unit: **source composition**. Seeds, prompts and strengths of one composition are averaged within it before
  any group statistic. All group results are exploratory (few units).
* Evaluation compositions: test templates H01-H04, melody seed 20, in both stimulus families (periodic and
  nonperiodic probe), at tempi 2.0 and 3.0 Hz (16 compositions). If CPU time forces a smaller set, the
  reduction is decided before generation, applied to both families alike and recorded.
* Training material (any fine-tuning): train templates only (T01-T06, melody seeds 0-2); validation V01-V02,
  melody seed 10. Nonperiodic versions of test templates are never used in training.

## Timing (rhythmic preservation)

Computed from onsets detected in the output (`rhythmic_metrics.detect_onsets`), against the composition's
ground-truth onsets, tolerance +-50 ms.

* **D1 (primary): floor-normalised onset F1 on the nonperiodic probe family**,
  f1_norm = (F1 - alias_floor) / (1 - alias_floor), where alias_floor is the best F1 a copy of the reference
  reaches at a wrong global lag (|lag| > 50 ms, scan +-0.6 s). An output's timing is called **preserved** only if
  f1_norm >= 0.5 **and** lag_specificity > 0 (F1 at lag 0 exceeds F1 at every wrong lag) **and**
  |best_lag| <= 50 ms. Otherwise it is "not preserved" whatever its raw F1.
* **D2 (precision, conditional):** mean absolute onset deviation and signed displacement (ms) of matched onsets,
  reported only for outputs whose timing is preserved under D1. Never read as evidence of preservation.
* Periodic family: the same quantities are reported as secondary (ecological) results with the alias floor
  shown next to every F1. Informed beat F1 (P2) is secondary and periodic by construction.
* Order-preserving alignment is reported but is not a decision quantity (identical to greedy on all controls).

## Acoustic change

* **T1 (primary): LTAS log-mel distance** (dB), timing-blind. Always reported with D1: LTAS is blind to
  temporal destruction (time reversal reads 0.001 dB), so T1 alone never says an edit succeeded.
* Secondary: frame-wise log-mel distance (also responds to timing), centroid shift, RMS and crest change,
  chroma correlation.
* Direction check per prompt (centroid down for "warmer", crest or RMS down for "softer"). An edit that keeps
  timing but does not move the sound (T1 below the oracle re-synthesis value of the same composition, 3.4 dB
  group median) is labelled "no effective edit", not a success.

## Comparisons

* **Matched transformation (primary comparison between editors, e.g. base vs fine-tuned):** per composition,
  D1's f1_norm as a function of T1 across editing strengths (piecewise-linear interpolation). Evaluated at the
  25th, 50th and 75th percentiles of the reference editor's T1 values over strengths 0.3-0.7, pooled over
  compositions. Decision quantity: paired difference (candidate - reference) at each grid point, bootstrap 95 %
  interval over compositions (10 000 resamples, seed 0) and two-sided Wilcoxon signed-rank p. The candidate
  is "better" only if the interval at the median grid point excludes zero in its favour **and** the candidate's
  own T1 range covers that grid point. Preserving timing by editing less is not "better".
* Fraction of outputs with timing preserved (D1 rule), per editor and strength, as a descriptive companion.
* Strength sweep: per composition Spearman rho(strength, f1_norm) and rho(strength, T1); sign test over
  compositions. Monotonicity is tested, not assumed.
* Reference points on the plane: identity, DSP edits and the oracle re-synthesis of each composition.

## Evidence labels

measured (metrics on actual outputs), simulated (synthetic controls), proposal (not run), interpretation.
