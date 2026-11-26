# AGENTS.md: working rules for this repository

These are operating rules for any agent or person changing this repository. They hold no science. The science,
the status and the document index are in [`README.md`](README.md), which stays the single entry point. The
evidence behind these rules is in [`docs/FINAL_ENGINEERING_AUDIT.md`](docs/FINAL_ENGINEERING_AUDIT.md)
(audit of `main` at `9df833d`, 2026-11-26).

Rules marked **(existing)** describe what the repository already does, as shown by its documents and Git
history. Rules marked **(proposal)** are new. They came out of the audit and wait for the author's decision.

## 1. What this repository is

A standalone follow-on study. It is not the ARSPI-Net dissertation codebase, and it holds no affective decoding,
connectivity-graph or clinical EEG code. Its one link to the dissertation code is the LIF reservoir class
`experiment_zero.LIFReservoir`, imported from a file that is **not in this repository**
(`/home/user/dissoAdventureExperiments/chapter5Experiments/experiment_zero.py`, found through `sys.path`).
No commit or hash of that file is recorded here. Without it, every script that computes a reservoir readout
fails at import. Do not copy that file in, and do not write a stand-in for it in the repository.

## 2. Evidence layers: keep them separate

Every result belongs to exactly one layer. Say which one whenever you write about a result.

| Layer | Where its rules live | Results documents | Code | Committed outputs |
|---|---|---|---|---|
| Confirmatory (pre-registered, stages 1 and 2) | `docs/PREREGISTRATION_DRAFT.md` (frozen at `935c80a`, addendum A1) | `docs/STAGE1_RESULTS.md`, `docs/STAGE2_RESULTS.md` | `weineck/weineck_loader.py`, `mtrf.py`, `tagging.py`, `q2_residual.py`, `q2_group_merge.py`, `tempo_curve.py` | `weineck/results/q2_residual_stage1.json`, `q2_residual_stage2_chunk{1,2,3}.json`, `q2_residual_stage2_merged.json`, `tempo_curve_stage{1,2}.json` |
| Exploratory follow-ups (after the stage-2 merge) | `docs/OSCILLATOR_DECISION_RULE.md`, `docs/ROBUSTNESS_PLAN.md`, `docs/IDENTIFIABILITY_PLAN.md` (addenda A3, A4, A4.1) | `docs/UNDERFIT_CHECK.md`, `docs/THEORY3_RESULTS.md`, `docs/ROBUSTNESS_RESULTS.md`, `docs/CYCLE_COUNT_CONTROL.md`, `docs/IDENTIFIABILITY_RESULTS.md` | `underfit_check.py`, `underfit_merge.py`, `oscillator_bank.py`, `oscillator_heldout.py`, `oscillator_group.py`, `oscillator_merge.py`, `robustness.py`, `merge_robustness.py`, `cycle_count_control.py`, `identifiability_precompute.py`, `identifiability_sim.py`, `identifiability_procedure.py`, `identifiability_merge.py`, `identifiability_merge_a3.py`, `identifiability_merge_a4.py`, `identifiability_crit2_diag.py` (all in `weineck/`) | `weineck/results/underfit_*`, `oscillator_*`, `robustness/`, `robustness_table.json`, `cycle_count_*`, `identifiability/`, `identifiability.json` |
| Pilot (predates the pre-registration, exploratory) | none | `pilot/RESULTS.md`, `WEEK1_ASSESSMENT.md` | `pilot/nmedt_pilot.py` (loader that every other pilot script imports. Its own statistic is superseded), `nmedt_pilot_v2.py` (a recorded negative result, superseded statistic), `nmedt_pilot_v3.py` (tagging statistic, imported by v4 and the ten-song script), `nmedt_pilot_v4_units.py`, `nmedt_tensong.py` | `pilot/results/` |
| Calibration (synthetic) | none | `calibration/RESULTS.md` | `calibration/synthetic_calibration.py`, `calibration/power_q2.py` | `calibration/results/` |
| Manuscript tooling | `docs/manuscript/make_numbers.py` docstring | `docs/FIGURES.md` (generated) | `weineck/figures/make_figures.py`, `docs/manuscript/make_numbers.py` | `docs/figures/tnsre/`, `docs/figures/tnsre/figure_numbers.json`, `docs/manuscript/numbers.tex` |
| Audio extension (separate from the EEG study) | `extensions/rhythm_preserving_audio/EXPERIMENT_PLAN.md`, `DECISION_RULES.md` | `extensions/rhythm_preserving_audio/SPOTIFY_RESEARCH_EVIDENCE.md` | `extensions/rhythm_preserving_audio/src/`, `experiments/` | `extensions/rhythm_preserving_audio/results/`, `figures/` |

One-off checks that back the data notes in `weineck/README.md`: `align_scan.py`, `trf_align_check.py`,
`resolve_trials.py`, `tempo_tiebreak_selftest.py`. `verify_mapping.py` is superseded.

## 3. Files you must not edit

**(existing)** The repository treats these as fixed. Changing them changes the record.

* `docs/PREREGISTRATION_DRAFT.md`. Frozen at `935c80a`. Later changes are dated addenda appended at the end,
  never edits to the frozen text.
* `docs/OSCILLATOR_DECISION_RULE.md`, `docs/ROBUSTNESS_PLAN.md`,
  `extensions/rhythm_preserving_audio/DECISION_RULES.md`. A rule is fixed before the outputs it scores.
  `docs/IDENTIFIABILITY_PLAN.md` and `EXPERIMENT_PLAN.md` grow only by dated addenda.
* Every committed results file: all JSON, `fig1_traces.npz`, and the logs under `weineck/results/`,
  `calibration/results/`, `pilot/results/` and `extensions/rhythm_preserving_audio/results/`.
* The original text of a results document. If a later analysis changes a reading, add a dated
  "Superseded" or "Correction" note in place and leave the original sentence as it was
  (see `docs/STAGE2_RESULTS.md`, notes of 2026-11-10 and 2026-11-17).
* The scripts in section 2 that produced committed results, including their hardcoded paths. A change to
  them changes the provenance of those results. Ask the author first.
* `docs/manuscript/numbers.tex`, `docs/figures/tnsre/figure_numbers.json` and `docs/FIGURES.md` by hand.
  They are generated (section 5).

## 4. Invariants

`python3 -m unittest discover -s weineck/tests -v` checks the starred items. The rest are checked by reading.

* \* Stimulus features are at 128 Hz. A feature vector spans the listening window (marker S40 to S80) minus
  1.0 s trimmed from the start. A trial is matched to the one stimulus of its subgroup within ±20 ms.
  Trials with no candidate or several are dropped (`weineck_loader.match_trials`).
* \* The one-to-one rule (two trials claiming the same stimulus are both dropped) is applied by the callers,
  not by the loader: `q2_residual.py`, `underfit_check.load_participant_arrays`,
  `tempo_curve.tempo_known_trials`. A new caller must apply it too.
* \* TRF: ridge on lags 0 to 400 ms at 64 Hz, penalty scaled by the trace of X'X, bias unpenalised. The
  held-out trial never enters its own fit. `q2_residual.py`, `underfit_check.solve` and
  `identifiability_sim.ridge` are copies of the estimator in `mtrf.fit_trf` and must stay identical to it.
* Lambda is chosen from {0.1, 1, 10, 100} inside the training trials only (inner folds: the first 12 training
  trials). EEG band 0.5 to 30 Hz. Fronto-central set Fz, FC1, FC2, Cz, F3, F4, C3, C4.
* \* The tagging statistic follows `docs/PREREGISTRATION_DRAFT.md` section 3 (Welch, 10 s Hann segments, local
  quadratic baseline 0.15 to 0.8 Hz away, max over harmonics 1 and 2).
* \* Shuffle null: 500 relabellings, each trial relabelled with another grid tempo, all N trials kept. The
  participant scores use one `RandomState(int(subject))` shared across the twelve statistics in a fixed order.
* \* Stage-2 group tests: one-sided Wilcoxon at alpha 0.04 for H2, TOST bounds ±0.10 for H1 and H3
  (`q2_group_merge.py`).
* \* Theory 3 rule: median gain over the best TRF above zero with one-sided p < .01, and the Hopf-augmented model
  above the linear-bank-augmented model with p < .05 (`identifiability_sim.decide`, `oscillator_merge.py`).
* \* Identifiability cells: seed = `cksum("<w> <r> <trials> <ntempi>\n") % 100000`, single-threaded BLAS
  (`OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1`), gamma from
  `weineck/results/identifiability/calibration.json`.
* Reservoir: constructed as `LIFReservoir(seed=42)` and nothing else. Unit count, leak, threshold and
  spectral radius are the external file's defaults. This repository cannot check them.
* Robustness rows change only the parameter they name (\* for the columns that can be checked from the
  committed JSON).

## 5. Generated files and scripts that overwrite

* `python3 weineck/figures/make_figures.py` writes `docs/figures/tnsre/*`, `figure_numbers.json` and
  `docs/FIGURES.md`. Then `python3 docs/manuscript/make_numbers.py` writes `numbers.tex`. Every number in
  `main.tex` is a `\Num...` macro. `make_figures.py` reads the Git log to resolve provenance commits, so it
  needs the full history (a shallow clone fails) and it writes into the repository.
* `weineck/merge_robustness.py` **overwrites `docs/ROBUSTNESS_RESULTS.md`** with a bare table. The committed
  document holds hand-written sections that the script does not produce. Do not run it in place.
* `weineck/identifiability_merge.py` rewrites `weineck/results/identifiability.json` **without the `A3` and
  `A4` keys**. They come back only by running `identifiability_merge_a3.py` (needs the sufficient statistics)
  and then `identifiability_merge_a4.py`. Do not run it in place.
* The queue scripts (`weineck/run_*.sh`) and several Python scripts write to hardcoded paths under
  `/home/user/arspinet-rhythmic-entrainment/`. To re-check a merge, copy the tree outside the repository
  (`git archive HEAD | tar -x -C <scratch>`) and run there.

## 6. Tests

```bash
python3 -m unittest discover -s weineck/tests -v
```

Needs numpy, scipy, threadpoolctl and (for the loader tests) mne. No data is needed.

* `test_pipeline_invariants.py`: synthetic fixtures for the loader matching, the TRF, the tagging statistic,
  the shuffle null and the committed decision rule.
* `test_committed_results.py`: the committed summary files still follow from the files they were built from,
  and `numbers.tex` is what `make_numbers.py` writes. A failure means a committed result or the code between
  two results changed. Do not regenerate the expected file to make it pass.
* `test_identifiability_procedure.py`: seed rule and statistics always run. Three tests re-run a committed
  cell and **skip** when the sufficient statistics (`weineck/results/identifiability/*.npy`,
  `stimuli_meta.npz`) are absent. They are never committed, so on a fresh clone the skip is expected. It
  means "exact reproduction not checked here", not "passed".
* Extension: `extensions/rhythm_preserving_audio/tests/` (own environment, see `EXPERIMENT_PLAN.md` section 1).

## 7. Data, paths and environment

* Never commit raw EEG, audio, stimulus feature files, sufficient statistics, model checkpoints or
  generated audio. Both `.gitignore` files list the patterns. `weineck/results/fig1_traces.npz` is the one
  committed exception.
* Data are expected at `/home/user/data_local/weineck2022/` and `/home/user/data_local/nmedt/`. The stimulus
  feature file is passed with `--feats`. Do not download data or models without the author's approval.
* No dependency manifest exists. The versions known to reproduce the committed merge outputs are listed in the
  audit report, section 6.

## 8. Adding a new experiment

**(existing)** The pattern every follow-up used:

1. Write a dated plan or rule document in `docs/` and commit it **before** any output exists. State the
   layer (exploratory unless the frozen pre-registration already covers it), the decision rule, and what
   stays untouched. The commit is the timestamp.
2. Put new code in new files. Reuse `weineck_loader.py`, `mtrf.py` and `tagging.py` by import. If a
   confirmatory script cannot be reused as is, wrap or copy it in the new file and say so. Do not edit it
   (`robustness.py` does this for `q2_residual.pc1`).
3. Write outputs to new file names or a new sub-folder of `weineck/results/`. Never overwrite an earlier
   output.
4. Write a results document that names its layer in the title, the plan commit, the code and the output
   files. Apply the rule verbatim and report every row.
5. Add one row to the README document table and, if the reading of an earlier result changes, a dated note
   in that earlier document. Later changes to a plan are dated addenda.

**(proposal)** Add the new result to the tables in sections 2 and 3 of this file in the same commit.

## 9. Recording results

* Label every statement with its evidence type, in the scheme of the document you are editing.
  `WEEK1_ASSESSMENT.md` uses `[measured]`, `[lit]` and `[inference]`. `docs/FRAMING.md` uses (measured),
  (simulated) and its section headings. `main.tex` uses `\Conf`, `\Expl` and `\Simul`. The extension report
  uses measured, simulated, proposal and interpretation.
* A number in a document must exist in a committed results file. Quote the file and key.
* A number for the manuscript goes into `make_figures.py` (`figure_numbers.json`) and then into
  `make_numbers.py` as a macro. Do not type numbers into `main.tex`.

## 10. Finding out why something was decided

Read in this order. First the addenda at the end of the plan documents. Then the dated "Superseded" and
"Correction" notes in the results documents. Then `docs/FRAMING.md`. Last the commit messages, which carry the
reasoning (`git log --follow -- <file>`, `git show <commit>`). Commits that matter most: `935c80a` (freeze), `73626a0`
(addendum A1), `b658693` (Q2 refactor during stage 2), `c8b1503` (stage 2), `d54f0ef` (Theory 3 rule),
`70360de` (simulator generalised), `a78d143` (extension merge).

## 11. Long runs and handoff

**(existing)** Long runs were committed while in progress under messages that start with `Interim:` and say
what is finished (for example "3 of 10 datasets"). An interim file is not a result. A result commit says so.

* Identifiability queues (`weineck/run_identifiability*.sh`): a worker pops a line from the queue file under
  `flock` before it runs the cell. An interrupted cell is therefore gone from the queue. The committed queue
  files are empty, and a queue script does nothing while its queue file exists. A cell file with
  `datasets_done` below its target is incomplete. `identifiability_sim.py` restarts a cell from its first
  dataset. `identifiability_procedure.py --out-dir` skips finished cells and reruns the others.
* Robustness queue (`weineck/run_robustness_queue.sh`): one lock directory `results/robustness/.lock_<row>`
  per row, not committed. A row file without an `ended` key is incomplete, and the row restarts from the
  first participant.
* **(proposal)** Before you stop a long run, commit an `Interim:` snapshot whose message lists the cells or
  rows still to do and the exact command that resumes them. The queue files alone do not record this.

## 12. Git discipline

* Run `git status` and `git log -5` before you touch anything. Fetch the full history
  (`git fetch --unshallow`) if the clone is shallow.
* One branch or worktree per task. No unrelated edits. Do not reformat files you are not changing.
* Do not commit or push without the author's approval. Do not rewrite history, force-push or delete
  branches. Do not create tags or releases: the remote has none, and `v1.0-tnsre-submission` is a planned
  name, not an existing tag.
* Do not choose a licence, add authors, or fill in placeholders in `CITATION.cff`. Those are the author's.
* Keep the extension and the EEG study apart: a change under `extensions/` touches nothing outside it, and
  the other way round.
