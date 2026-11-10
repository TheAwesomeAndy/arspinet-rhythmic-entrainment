# Cycle-count control for the 13-tempo curve (EXPLORATORY)

Run 2026-11-10 after the stage-2 merge; pre-registration frozen at `935c80a` untouched. Code:
`weineck/cycle_count_control.py`; aggregate results `weineck/results/cycle_count_summary.json`
(per-participant files `cycle_count_part{1..4}.json`).

## Why

The 13-tempo curve in `docs/STAGE2_RESULTS.md` concatenates all tempo-known trials of a tempo and
computes the shared tagging statistic on that concatenation. A faster tempo therefore carries more
beat cycles per second of data, so a rise of the statistic toward 4 Hz could be a cycle-count
artefact rather than a property of the response.

## What was done

Per participant, the concatenated fronto-central drive of every tempo was truncated to the same
number of beat cycles (the minimum available across that participant's tempi; median 90 cycles,
range 30 to 206), giving fixed-cycle windows of 7.6 to 165 s depending on tempo and participant.
The tagging statistic (`tagging.tag_z`, same baseline and harmonic rule as everywhere else) was
recomputed on the truncated drive (L) and on the unit-PC1 of the canonical reservoir driven by it
(R_pc1), alongside the full-duration values. The decision quantity is the per-participant slope of
the statistic over tempo (z per Hz), tested one-sided (greater than zero) with a Wilcoxon signed-rank
test over the 34 participants. The rise "survives" if that test is significant at 0.05 for the
fixed-cycle statistic.

## Result: the rise toward 4 Hz does not survive

| statistic | slope of group median z (z/Hz) | participant slopes: median | positive | Wilcoxon p (greater) |
|---|---|---|---|---|
| L, full duration | +0.561 | +0.484 | 26/34 | 0.0001 |
| L, fixed cycles | +0.166 | +0.015 | 18/34 | 0.37 |
| R_pc1, full duration | +0.497 | +0.486 | 26/34 | 0.0006 |
| R_pc1, fixed cycles | +0.013 | +0.016 | 18/34 | 0.45 |

Group median z by tempo (full / fixed cycles), drive L: 1.0 Hz 1.55 / 1.55; 2.0 Hz 1.84 / 2.31;
3.0 Hz 3.14 / 1.59; 4.0 Hz 3.49 / 2.22. The slowest tempo is unchanged by construction (it usually
sets the minimum cycle count). Values at every tempo remain positive (beat-locked power is present
at all 13 tempi), but the monotone increase toward 4 Hz is the duration confound: once every tempo
is scored on the same number of cycles, the participant slopes centre on zero.

## Interpretation and consequences

* The 13-tempo curve in `docs/STAGE2_RESULTS.md` must be read as "beat-locked power present at all
  tempi, no evidence of a rate preference once cycle count is matched". The "rise toward 4 Hz"
  wording is withdrawn (it stays in the stage-2 document as the originally reported, confounded
  curve; this file is the correction).
* This is consistent with Theory 3 (`docs/THEORY3_RESULTS.md`): no preferred-rate effect in the
  held-out-tempo encoding test either.
* Limitation: the fixed-cycle windows are short for some participants (7.6 s minimum at 4 Hz for a
  participant with 30 cycles), so the fixed-cycle statistic is noisier than the full-duration one.
  The null result is therefore "no evidence of a rise", not "evidence of a flat curve"; the group
  medians at fixed cycles are flat within their interquartile range (`cycle_count_summary.json`).
