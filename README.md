# ARSPI-Net rhythmic entrainment

Standalone project, separate from the BIBM/SPL affective line. Nothing here touches the
`BIBM` or `dissoAdventureExperiments` repositories; the analysis imports
`chapter5Experiments/experiment_zero.py` (the canonical LIF reservoir) read-only.

## Status (2026-11-16)

The pre-registered two-stage study is complete (H2 supported at stage 2; H1 and H3 equivalent). The
exploratory follow-ups are complete too: the underfitting check (H2 not explained by underfitting),
Theory 3 (oscillator encoding model not supported, no preferred-rate effect; validated in both
directions), the eleven-row robustness grid (no row flipped; H2 columns reservoir-independent by
construction; IAAFT decomposition: spectral 0.156, phase-dependent 0.045, p = 0.0003), and the
cycle-count control (the rise of the tempo curve toward 4 Hz does not survive a fixed cycle count),
and the identifiability map (the committed Theory 3 rule has zero false positives but 80 % power only
for an oscillator supplying about 89 % of the stimulus-locked amplitude at Weineck's operating point;
the blind spot is independent of SNR, trial count and tempo count, and addendum A3 found it survives
power-matching, nested lambda selection and a TRF-inexpressible oscillator; the cause is the rule's
Hopf-vs-linear-bank criterion, which addendum A4 shows has no lambda-stable answer; the comparison against the TRF
alone bounds structure a Hopf bank can express beyond the TRF at about 59 % of the amplitude, about 67 % of
its variance, a weak exclusion and not guaranteed conservative; see `docs/FRAMING.md` item 11). The TNSRE
figure set (Figs 1-7) is drafted: `weineck/figures/make_figures.py`, outputs in `docs/figures/tnsre/`, captions
in `docs/FIGURES.md`. TNSRE submission pass (2026-11-16): the identifiability procedure is a documented entry
point with a regression test (below); cover letter, citation file and the list of references to verify are in
`docs/manuscript/`. Remaining publication-plan item: the NMED-T generalization (the NMED-T pilot in `pilot/`
predates the pre-registration and is exploratory).

## Using the identifiability procedure

`weineck/identifiability_procedure.py` asks how large an oscillator-bank contribution to the stimulus-locked
EEG would have to be before the committed encoding-model comparison detects it, at a given single-listen SNR.
It wraps `identifiability_sim.py`, the code behind every committed cell, without changing its numerics.

```bash
cd weineck
# 1. fitted kernels, then the sufficient statistics of the stimulus features (needs the Weineck et al. data
#    locally; outputs are not redistributed). Kernels first: the stimuli part reads the pooled residual noise
#    shape from results/identifiability/noise_shape.npz and otherwise falls back to 1/f with a warning.
python3 identifiability_precompute.py --feats <stimulus feature file> --part kernels
python3 identifiability_precompute.py --feats <stimulus feature file> --part stimuli
# 2. the map: per-cell detection and false-positive rates with Clopper-Pearson 95 % intervals, and W80
python3 identifiability_procedure.py --r 0.04 --trials 40 --ntempi 12 \
    --w-grid 0,0.5,0.6,0.7,0.8,0.9,1 --datasets 20 --participants 20 --workers 4 \
    --out-dir results/identifiability/procedure_runs/A_r0.04_n40_t12
```

Inputs: fitted kernels (`--kernels`, JSON), the sufficient-statistics directory (`--stats-dir`), target held-out
r (`--r`; the noise scale is calibrated if not stored), trials per tempo, training tempi, the w grid, datasets
per cell and participants per dataset; `--world A|B|C` and `--nested` select the A3 variants. Output:
`<out-dir>/summary.json` (per cell: full-rule and criterion-1 rates with k/n and intervals; false-positive rate
at w = 0; W80 with its bracket and variance share) and one resumable JSON per cell. Seeds follow the committed
rule (`cksum("<w> <r> <trials> <ntempi>") % 100000`), so committed cells are reproduced exactly.

Regression test (re-runs the committed World A cell w = 0.9, r = 0.04, 40 trials, 12 tempi from its seed and
requires every stored per-dataset value to match exactly; skipped if the sufficient statistics are absent):

```bash
python3 -m unittest discover -s weineck/tests -v                 # first 2 of 20 datasets, ~5 min
IDENT_FULL=1 python3 -m unittest discover -s weineck/tests -v    # the whole cell, ~15 min
```

Citation: `CITATION.cff`; archived release `v1.0-tnsre-submission`, Zenodo DOI to be added.

| Document | What it holds |
|---|---|
| [`docs/FRAMING.md`](docs/FRAMING.md) | the question, results with evidence labels, publication plan (TNSRE, then IEEE TCDS) and must-adds |
| [`docs/PREREGISTRATION_DRAFT.md`](docs/PREREGISTRATION_DRAFT.md) | pre-registration v1.0, frozen at commit `935c80a`; addendum A1 (eight stage-1 participants, power at n = 8) recorded before the stage-1 group test |
| [`docs/STAGE1_RESULTS.md`](docs/STAGE1_RESULTS.md) | stage 1 (8 participants): H2 not supported at alpha 0.01 (p = 0.055), inconclusive below a 4 % component; stage 2 proceeded unconditionally |
| [`docs/UNDERFIT_CHECK.md`](docs/UNDERFIT_CHECK.md) | exploratory: H2 not explained by underfitting (linear-world residual delta 0.039 vs real 0.228; pooled 33-participant TRF leaves it unchanged) |
| [`docs/OSCILLATOR_DECISION_RULE.md`](docs/OSCILLATOR_DECISION_RULE.md), [`docs/THEORY3_RESULTS.md`](docs/THEORY3_RESULTS.md), [`docs/lit_oscillator_models.md`](docs/lit_oscillator_models.md) | exploratory Theory 3: Hopf / resonate-and-fire / linear oscillator banks vs TRF kernels at held-out tempi; rule fixed in advance; NOT SUPPORTED, no preferred-rate effect; recovery and false-positive worlds; literature |
| [`docs/ROBUSTNESS_PLAN.md`](docs/ROBUSTNESS_PLAN.md), [`docs/ROBUSTNESS_RESULTS.md`](docs/ROBUSTNESS_RESULTS.md) | exploratory robustness grid (seeds, rho, beta, TRF variants, IAAFT): no row flipped; audit of which rows can move; IAAFT spectral / phase decomposition |
| [`docs/FIGURES.md`](docs/FIGURES.md) | TNSRE figure set (Figs 1-7, PDF and 300 dpi PNG in `docs/figures/tnsre/`): draft captions generated from the results JSONs, every number with its source key |
| [`docs/CYCLE_COUNT_CONTROL.md`](docs/CYCLE_COUNT_CONTROL.md) | exploratory: tempo curve rescored on a fixed number of beat cycles; the rise toward 4 Hz does not survive |
| [`docs/IDENTIFIABILITY_PLAN.md`](docs/IDENTIFIABILITY_PLAN.md), [`docs/IDENTIFIABILITY_RESULTS.md`](docs/IDENTIFIABILITY_RESULTS.md) | exploratory methods contribution: simulated map of what the Theory 3 rule can detect (94 cells plus addendum A3: power-matched, TRF-inexpressible and nested-lambda worlds); 80 % power only at amplitude share 0.89 at Weineck's operating point, zero false positives; figures in `docs/figures/` |
| [`docs/STAGE2_RESULTS.md`](docs/STAGE2_RESULTS.md) | stage 2 (34 participants): H2 supported (residual beat-locked power beyond the four-feature TRF, median delta 0.228, 31/34 positive, p < 1e-4); H1 and H3 equivalent to the linear statistic; shuffled-weight reservoir matches; 13-tempo curve |
| [`WEEK1_ASSESSMENT.md`](WEEK1_ASSESSMENT.md) | the original literature-backed assessment of the proposal and the redesign |
| `docs/lit_*.md` | three literature reviews (entrainment-vs-evoked debate; open music-EEG datasets; reservoir/EEG novelty) |
| `docs/week1_proposal.txt` | the proposal as retrieved on 2026-11-08 |

## Code and results

| Folder | Contents |
|---|---|
| `weineck/` | Weineck, Wen & Henry (2022) loader and trial-to-stimulus matching (`README.md` there documents the data facts), ridge mTRF, shared tagging statistic and stimulus-label shuffle null (`tagging.py`), Q2 residual pipeline, 13-tempo curve, group merge; `results/` holds aggregate JSON only, with one exception: `results/fig1_traces.npz`, a single 15 s example trial (participant 10) for Fig. 1b; `figures/make_figures.py` builds the TNSRE figure set |
| `calibration/` | synthetic calibration of all detectors (`RESULTS.md`), Q2 power simulations (false-positive and power tables at the stage alphas) |
| `pilot/` | NMED-T feasibility pilot and the ten-song single-listen table (`RESULTS.md`) |

## Data

Never committed. Weineck 2022 raw EEG (OSF y5xhs, CC BY 4.0) in `/home/user/data_local/weineck2022/`
(all 34 participants); NMED-T cleaned files (Stanford Digital Repository, CC BY;
purl.stanford.edu/jn859kj8079) in `/home/user/data_local/nmedt/` (all ten songs). From the
cloud sandbox the Stanford hosts need the public emSign Root CA - G1 appended to the proxy CA
bundle (`WEEK1_ASSESSMENT.md` section 4). NMED-T audio is not distributed.
