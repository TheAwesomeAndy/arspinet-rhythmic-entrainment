# ARSPI-Net rhythmic entrainment

Standalone project, separate from the BIBM/SPL affective line. Nothing here touches the
`BIBM` or `dissoAdventureExperiments` repositories; the analysis imports
`chapter5Experiments/experiment_zero.py` (the canonical LIF reservoir) read-only.

## Status (2026-11-09)

The pre-registered two-stage study is complete; the underfitting check (exploratory) and
the pre-registered robustness rows are next, per the publication plan.

| Document | What it holds |
|---|---|
| [`docs/FRAMING.md`](docs/FRAMING.md) | the question, results with evidence labels, publication plan (TNSRE, then IEEE TCDS) and must-adds |
| [`docs/PREREGISTRATION_DRAFT.md`](docs/PREREGISTRATION_DRAFT.md) | pre-registration v1.0, frozen at commit `935c80a`; addendum A1 (eight stage-1 participants, power at n = 8) recorded before the stage-1 group test |
| [`docs/STAGE1_RESULTS.md`](docs/STAGE1_RESULTS.md) | stage 1 (8 participants): H2 not supported at alpha 0.01 (p = 0.055), inconclusive below a 4 % component; stage 2 proceeded unconditionally |
| [`docs/STAGE2_RESULTS.md`](docs/STAGE2_RESULTS.md) | stage 2 (34 participants): H2 supported (residual beat-locked power beyond the four-feature TRF, median delta 0.228, 31/34 positive, p < 1e-4); H1 and H3 equivalent to the linear statistic; shuffled-weight reservoir matches; 13-tempo curve |
| [`WEEK1_ASSESSMENT.md`](WEEK1_ASSESSMENT.md) | the original literature-backed assessment of the proposal and the redesign |
| `docs/lit_*.md` | three literature reviews (entrainment-vs-evoked debate; open music-EEG datasets; reservoir/EEG novelty) |
| `docs/week1_proposal.txt` | the proposal as retrieved on 2026-11-08 |

## Code and results

| Folder | Contents |
|---|---|
| `weineck/` | Weineck, Wen & Henry (2022) loader and trial-to-stimulus matching (`README.md` there documents the data facts), ridge mTRF, shared tagging statistic and stimulus-label shuffle null (`tagging.py`), Q2 residual pipeline, 13-tempo curve, group merge; `results/` holds aggregate JSON only |
| `calibration/` | synthetic calibration of all detectors (`RESULTS.md`), Q2 power simulations (false-positive and power tables at the stage alphas) |
| `pilot/` | NMED-T feasibility pilot and the ten-song single-listen table (`RESULTS.md`) |

## Data

Never committed. Weineck 2022 raw EEG (OSF y5xhs, CC BY 4.0) in `/home/user/data_local/weineck2022/`
(all 34 participants); NMED-T cleaned files (Stanford Digital Repository, CC BY;
purl.stanford.edu/jn859kj8079) in `/home/user/data_local/nmedt/` (all ten songs). From the
cloud sandbox the Stanford hosts need the public emSign Root CA - G1 appended to the proxy CA
bundle (`WEEK1_ASSESSMENT.md` section 4). NMED-T audio is not distributed.
