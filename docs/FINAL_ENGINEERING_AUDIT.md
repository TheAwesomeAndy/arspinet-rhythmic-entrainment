# Independent engineering and multi-agent readiness audit

Audited: `main` at commit `9df833d` (2026-11-26), 249 commits, no tags. Audit date: 2026-11-26.
Scope: engineering, provenance, reproducibility and agent readability. This is not a re-analysis. No method,
threshold, seed, statistic or reported number was changed.

Evidence labels used throughout:

| Label | Meaning |
|---|---|
| **[reproduced]** | numerical reproduction of a committed result, by me, in this audit |
| **[synthetic]** | ran on synthetic data. Never a reproduction of a number from real EEG |
| **[read]** | structural or code-reading check, including Git history |
| **[repo record]** | documented by the repository, not re-run by me |
| **[not verified]** | I could not check it, with the reason |

Everything I ran wrote to a scratch directory outside the repository. The raw EEG, the NMED-T files, the
identifiability sufficient statistics, the Stable Audio checkpoints and the external reservoir file were not
available, and I downloaded none of them.

## 1. Executive assessment

The repository is in better condition than its flat layout suggests. It is in worse condition than its own
documents claim on three points, two of which bear on the EEG study.

**What holds up.** The record-keeping is real. The pre-registration body has not changed since the freeze
commit. Each exploratory rule was committed before the first output it governs. The confirmatory result
files were never touched after the commits that reported them. More to the point, the numbers reproduce:
from the committed per-trial statistics I recomputed every participant score for all 34 participants
(3,300 trials) and got the stored values bit for bit, then re-ran the stage-2 group tests and got the
committed merged file with zero differences, including the H2 headline (median delta 0.228, 31 of 34
positive, p = 8.0e-9). The same holds for the Theory 3 merge, the underfitting merge, the eleven-row grid
table, the identifiability base map and addendum A4, the figure numbers (645 values) and `numbers.tex`
(byte-identical). The two pre-registration power tables reproduce exactly from their stated commands.

**What does not hold up.**

1. *The link from raw data to those per-trial statistics is not reproducible from this repository alone,
   and for the reservoir it is not even specified here.* The reservoir class lives in another repository
   at an unrecorded revision. The scripts pass only `seed=42`. The unit count, leak, threshold and spectral
   radius that the pre-registration states (256, 0.05, 0.5, 0.9) are the external file's defaults. Nothing
   in this repository sets or asserts them. H2 does not depend on the reservoir. H1, H3 and every
   reservoir column do.
2. *The identifiability noise bank has no recorded origin.* Both committed kernel-fit logs end in a crash
   inside the noise-shape step. The script would have written a file under a different name from the one
   the next step reads. The next step's committed log shows it found a noise-shape file anyway. Where that
   file came from is not in the code, the documents or the history. All 141 simulated cells rest on it.
3. *The audio extension froze its rules in time and then applied only some of them.* The experiment it
   evaluated is not in its frozen plan, and its headline comparison sits in a region its own frozen rules
   label "no effective edit". This is separate from the EEG study and does not affect it.

Neither of the first two points says a result is wrong. Both say a result cannot currently be regenerated
or checked by someone who has only this repository and the public data.

**Engineering state.** There was no licence, no dependency manifest, no CI, no agent instruction file,
and one test file on the EEG side whose three substantive tests skip on any fresh clone. The confirmatory
pipeline had no tests at all. Hardcoded absolute paths appear in 29 files, two of them pointing into a dead
session scratchpad. Two scripts silently destroy committed content when re-run in place. The README never
mentioned the audio extension. The release named in `README.md` and `CITATION.cff` does not exist.

**What this audit changed.** Six files: two new test files (48 tests, about 1.3 s, no
data needed, 27 seeded regressions all caught), `AGENTS.md`, a two-line `CLAUDE.md`, factual
corrections to `README.md`, and three stale branch-state statements in the extension's evidence report.
A seventh, this report. Nothing else was touched. The changes stayed uncommitted during the audit. On the
author's instruction they were then committed and pushed to branch `ccr-2b3cc9be-qgn4td` (2026-11-26). They
are not on `main`. Section 9 lists what needs your decision.

## 2. Baseline statement

**No earlier modernization pass exists.** At `9df833d` the tree holds 549 files and none of: `AGENTS.md`,
`CLAUDE.md`, `.claude/` or any other agent directory, `.github/` or other CI, `pyproject.toml`, `setup.py`,
a requirements or environment file, `LICENSE`, `conftest.py`, or an earlier engineering audit. The two
commit subjects that contain "audit" (`a40b615`, `f9fc174`) refer to a scientific audit of the eleven-row
grid. **[read]** (`git ls-tree -r 9df833d`, `git log`)

So the requirements audited here are the repository's own stated conventions, R1 to R12.

Other baseline facts, all **[read]**:

* The working clone was shallow (61 commits). After `git fetch --unshallow` it holds 249. 247 commits are
  authored by "Claude" and 2 under the author's GitHub account (`b2a09c2`, `5cd1cc8`). Dates run from
  2026-11-08 to 2026-11-26. 146 of the 249 are `Interim:` snapshots of logs and partial outputs.
* The remote has two heads, `main` and `extension/rhythm-preserving-audio`, both at `9df833d`, and no tags
  (`git ls-remote`).
* Working tree clean at start (`git status`).

Corrections to the brief I was given:

* The brief lists "two test files" and then names three. There were three at baseline: one in
  `weineck/tests/` and two in the extension.
* Hardcoded paths are also in `calibration/synthetic_calibration.py` (default `--out`), not only in
  `weineck/`, `pilot/` and the queue scripts.
* The pilot scripts v1 to v3 are not all superseded. v1 is a live import for every other pilot script and
  v3 for two of them (section 4).
* The robustness queue does not use the committed `queue.lock` files. It uses lock directories
  (`results/robustness/.lock_<row>`) that Git does not track. The three committed lock files and three
  queue files belong to the identifiability queues, and all six are empty.

## 3. Requirements matrix

Status scale: PASS, PARTIAL, FAIL, NOT VERIFIED, NOT APPLICABLE. A status describes the repository at
`9df833d`, before my changes.

| ID | Convention | Status | Evidence I produced | Remaining gaps |
|---|---|---|---|---|
| R1 | Pre-registration frozen at `935c80a`. Later changes are dated addenda, never silent edits | **PASS**, one recorded exception | `git diff 935c80a HEAD -- docs/PREREGISTRATION_DRAFT.md`: 41 insertions, 1 deletion. The insertions are addenda A1 and A1-power, appended. The one changed line is the status line (`a88b923`, three minutes after the freeze: "git tag `prereg-v1`" became "commit `935c80a`"). It changes no rule and its commit message says so, but it is not a dated addendum. At the commits that record A1 and A1-power (`73626a0`, `ba29292`, `43f4984`) the committed stage-1 log holds 7 participant lines and no group table, and the stage-1 JSON has no `group` key. The group table first appears in `4e0d5fc`. **[read]** | Commit order is strong evidence. Commit timestamps are weaker, since the committer sets them. Git cannot show what was seen in a session before it was committed. The "local tag `prereg-v1`" the status line mentions is not on the remote. |
| R2 | Exploratory work never alters confirmatory results. Superseded readings are marked in place | **PASS**, with notes | No commit touches `q2_residual_stage1.json` after `4e0d5fc` or any stage-2 chunk or merged file after `c8b1503`. `docs/STAGE2_RESULTS.md` changed twice since, both times by an added dated note (2026-11-10 correction, 2026-11-17 superseded note) with the original text intact. `tagging.py`, `mtrf.py` and `weineck_loader.py` have not changed since before the freeze. **[read]** | `q2_residual.py` was refactored *during* stage 2 (`b658693`). The reason is recorded and I measured the effect: for the seven stage-1 participants whose data did not change, stage-2 values equal stage-1 values to 1.3e-11 on per-trial statistics and 3.5e-13 on scores, with identical lambda choices **[reproduced]**. `robustness.py` replaces `q2_residual.pc1` at run time (file untouched, fallback only when the SVD fails). `docs/FRAMING.md` plan item 2 still says "identifiability map in progress". |
| R3 | `results/` holds aggregate JSON only, one stated exception | **PARTIAL** | No raw EEG or audio anywhere. But `weineck/results/` (400 files) holds per-trial statistic tables for every participant (the stage-2 chunks, 4.8 to 5.6 MB each), per-participant fitted kernels (`identifiability/kernels_*.json`), 186 logs and 6 queue and lock files. `fig1_traces.npz` holds five 982-sample arrays for one trial of participant 10 (15.3 s at 64 Hz). **[read]** | "Aggregate only" overstates it. The accurate claim is "derived statistics only, no raw signals except one 15 s example". Wording is the author's call. |
| R4 | Raw data, audio and checkpoints never committed | **PASS** | Both `.gitignore` files list the patterns. Every path ever added on any ref (550 paths): 226 json, 193 log, 55 py, 31 md, 14 png, 12 pdf, 4 txt, 4 sh, 3 lock, 3 gitignore, 2 tex, 1 npz, 1 cff, 1 bib. No `.mat`, `.eeg`, `.vhdr`, `.wav`, `.pt`, `.ckpt`, `.safetensors`, `.npy`. Largest blob 5.6 MB (a results JSON). **[read]** | None. |
| R5 | Every number in `main.tex` is a macro from `figure_numbers.json` | **PASS** for the committed skeleton. **NOT VERIFIED** for the manuscript to be submitted | Re-ran `make_figures.py` then `make_numbers.py` in a scratch copy: `figure_numbers.json` identical (645 values, 0 differences), `docs/FIGURES.md` identical, `numbers.tex` byte-identical (175 macros). `main.tex` uses 138 macros, all defined. The 15 body lines with literal digits hold only structure: list and hypothesis numbers, criterion numbers, the DOI, "CC BY 4.0", `(1-w)`, `w = 0`, and the lower lag bound "0" twice. **[reproduced]** | The design constants in `figure_numbers.json` (`ms/design`) are typed by hand in `make_figures.py` (`DESIGN`, and `n_units = 256`). `pending_submission_edits.md` says the 11-page rewrite is not in the repository, so R5 cannot be checked for it. Committed `main.pdf` (6 pages, built 2026-11-12) is older than `numbers.tex` (2026-11-17). 37 macros are defined and unused, among them `\NumNCells` = 102 where the documents say "94 cells plus addenda". |
| R6 | Identifiability cells reproduced exactly from the seed rule, single-threaded BLAS | Seed rule **PASS**. Exact reproduction **NOT VERIFIED** | The Python `cksum` equals coreutils `cksum` on all 102 distinct cell strings. All 47 cells that store a seed match the rule. Queue scripts, the procedure and the test set single-threaded BLAS. **[reproduced]** for the seed rule. | The three tests that re-run a cell skip: the sufficient statistics are not committed and cannot be rebuilt as documented (defect D1). The 94 original grid cells store no seed, so the rule is the only record of theirs. |
| R7 | `identifiability_procedure.py` wraps the simulator without changing numerics | **PASS** by reading. **NOT VERIFIED** numerically | The procedure calls `sim.run_cell` with the same arguments, adds `threadpool_limits(1)`, and only summarises. **[read]** | "The code behind every committed cell" needs a caveat. The simulator changed after the first 94 cells (`70360de`, `9e0f343`). From committed files alone: three cells re-run after the change keep every decision and differ by at most 1.5e-10 (w = 0.8), 1.5e-10 (w = 0.9) and 2.1e-10 (w = 1.0) **[reproduced]**. |
| R8 | Decision rules fixed before outputs are scored | **PASS** on commit order | Position in history: Theory 3 rule #37, code #39, first output #42, rule file unchanged since. Grid plan #44, code #45, first output #47, plan unchanged since. Identifiability plan #129, first cell #133. Addendum A3 #181, first non-empty A3 output later. A4 #206, first A4 output #207. A4.1 #224, its cell #225. Plan grew by 110 insertions and 0 deletions. Extension: A1 #239 and A2 with `DECISION_RULES.md` #241, first scored model output #242. `identifiability_sim.decide` and `oscillator_merge.py` implement the Theory 3 rule as written. **[read]** | The underfitting check's prose rule ("fixed before running") first appears in the commit that reports the results (`932787f`, #38). What was committed before the first output (#34) is the comparison itself, in `underfit_merge.py`. The refinement-cell addendum says in its own words that it was recorded after the coarse result. Extension: the rules were fixed first, but the experiment they scored is not in the plan, and several rules were never applied (section 5.7). |
| R9 | Evidence labels used consistently | **PARTIAL** | Four schemes are in use: `[measured]` / `[lit]` / `[inference]` (`WEEK1_ASSESSMENT.md`), (measured) / (simulated) (`docs/FRAMING.md`), `\Conf` / `\Expl` / `\Simul` (`main.tex`), and the extension's four labels. I found no mislabelled result in what I sampled. Exploratory documents say EXPLORATORY in their titles. **[read]** | The schemes are not unified. `docs/STAGE1_RESULTS.md` and `docs/STAGE2_RESULTS.md` never use the word "confirmatory" (they say "frozen pre-registration"). `calibration/RESULTS.md` never says "simulated". Eight of the eleven grid rows are listed in the frozen pre-registration as robustness rows, yet the grid is labelled exploratory throughout. That is the cautious label, but the two descriptions differ. In the extension's report the delegated check found five label slips, for example "a measured alias floor" inside a simulated bullet (line 221). |
| R10 | The extension touches nothing outside `extensions/` | **PASS** | `git diff --name-only a78d143^1 a78d143`: 37 files, all under `extensions/`. No commit in `a78d143^1..a78d143^2` touches any other path. The commit after the merge touches one extension document. **[read]** | None. |
| R11 | README tables point to files that exist and say what they hold | **PARTIAL**, fixed where low-risk | Every path-like reference in the 32 documents resolves to a tracked file or to named external data. Every number in the README status paragraph matches its results file (section 5). **[reproduced]** | At baseline the README did not mention `extensions/`, `docs/manuscript/` as a folder, or the tests. Added. Its identifiability instructions cannot rebuild the committed statistics (D1). Caution added. The "aggregate JSON only" sentence stands (R3). |
| R12 | Release `v1.0-tnsre-submission` exists | **FAIL** | `git ls-remote --tags origin` returns nothing. `submission_checklist.md` lists "re-point and push the tag" as open. `CITATION.cff` gives `version: "v1.0-tnsre-submission"` and `date-released: "2026-11-16"`. **[read]** | README wording corrected to "planned". `CITATION.cff` left alone (yours to edit). The pre-registration notes that the remote refused tag refs. |

## 4. Architecture assessment

**The flat layout is the right design for this study.** One author, one dataset, a linear sequence of
analyses, about 5,600 lines of Python. A package layer would add ceremony and fix nothing I could
demonstrate. I recommend against one.

### File map

Roles: **A** authoritative (behind a committed result), **M** merge or summary, **O** one-off check,
**S** superseded, **T** test, **Q** queue runner.

| File | Role | Layer | Committed output |
|---|---|---|---|
| `weineck/weineck_loader.py`, `mtrf.py`, `tagging.py` | A (shared) | confirmatory | imported by the scripts below |
| `weineck/q2_residual.py` | A | confirmatory | `q2_residual_stage1.json`, `q2_residual_stage2_chunk{1,2,3}.json`, `q2_check_subj10_fast.json` |
| `weineck/q2_group_merge.py` | M | confirmatory | `q2_residual_stage2_merged.json` |
| `weineck/tempo_curve.py` | A | confirmatory (Q1) | `tempo_curve_stage{1,2}.json` |
| `weineck/underfit_check.py`, `underfit_merge.py` | A, M | exploratory | `underfit_chunk{1,2,3}.json`, `underfit_merged.json` |
| `weineck/oscillator_bank.py`, `oscillator_heldout.py`, `oscillator_merge.py` | A, A, M | exploratory | `oscillator_heldout_chunk{1,2,3}.json`, `oscillator_sim_{hopf,trf}.json`, `*_merged.json` |
| `weineck/oscillator_group.py` | A | exploratory | `oscillator_group_loto.json` |
| `weineck/robustness.py`, `merge_robustness.py` | A, M | exploratory | `robustness/<row>.json`, `robustness_table.json`, and it overwrites `docs/ROBUSTNESS_RESULTS.md` |
| `weineck/cycle_count_control.py` | A | exploratory | `cycle_count_part{1..4}.json` |
| `weineck/identifiability_precompute.py` | A | exploratory (simulated) | `identifiability/kernels_*.json`, uncommitted `.npy` statistics |
| `weineck/identifiability_sim.py` | A | exploratory (simulated) | `identifiability/cells*/`, `calibration.json` |
| `weineck/identifiability_procedure.py` | A (entry point) | exploratory (simulated) | `identifiability/component_correlation.json` |
| `weineck/identifiability_merge.py`, `_merge_a3.py`, `_merge_a4.py` | M | exploratory | `identifiability.json` (base keys, `A3`, `A4`), `a4_summary.json`, three PNGs |
| `weineck/identifiability_crit2_diag.py` | M | exploratory | `identifiability/criterion2_diagnostic.json` |
| `weineck/figures/make_figures.py` | M | manuscript | `docs/figures/tnsre/*`, `figure_numbers.json`, `docs/FIGURES.md`, `fig1_traces.npz` |
| `docs/manuscript/make_numbers.py`, `list_new_refs.py` | M | manuscript | `numbers.tex`, `new_refs_to_verify.md` |
| `weineck/run_identifiability_queue.sh`, `_a3.sh`, `_a4.sh`, `run_robustness_queue.sh` | Q | exploratory | logs and cells |
| `weineck/align_scan.py`, `trf_align_check.py`, `resolve_trials.py`, `tempo_tiebreak_selftest.py` | O | data notes | `align_scan_*`, `trf_align_*`, `resolve_*`, `tempo_tiebreak_*` |
| `weineck/verify_mapping.py` | S | data notes | none |
| `calibration/synthetic_calibration.py`, `power_q2.py` | A | calibration (synthetic) | `calibration/results/*` |
| `pilot/nmedt_pilot.py` | A as loader (imported by all other pilot scripts), S as statistic | pilot | `pilot_song28.json` |
| `pilot/nmedt_pilot_v2.py` | S (a recorded negative result) | pilot | `pilot_v2_song28.json` |
| `pilot/nmedt_pilot_v3.py`, `_v4_units.py` | A | pilot | `pilot_v3_song{21,28,30}.json` (v4 prints only) |
| `pilot/nmedt_tensong.py` | A | pilot | `pilot/results/nmedt_tensong.{json,md,log}` |
| `weineck/tests/test_identifiability_procedure.py` | T | | |
| `extensions/rhythm_preserving_audio/**` | extension | extension | section 5.7 |

Committed outputs with **no committed generating code**: `cycle_count_summary.json`,
`oscillator_group_loto_summary.json`, `robustness/iaaft_components.json`, the assembly of
`robustness/iaaft.json` from its five part files, `residual_discrepancy_check.json`,
`identifiability/prediction_overlap.json`, and the noise-shape file behind the sufficient statistics. The
first three feed manuscript macros. I recomputed them independently from the files they summarise and they
match (section 6). `prediction_overlap.json` needs the uncommitted statistics, so it stays unverified.

### Are the shared building blocks shared?

Partly. **[read]**

* `tagging.py` is shared everywhere it should be. One statistic, one null.
* `weineck_loader.py` shares the feature reader and the matcher. The trial pipeline is not shared: loading,
  referencing, filtering, resampling and the one-to-one filter are written out three times
  (`q2_residual.py` lines 65 to 85, `underfit_check.load_participant_arrays`,
  `tempo_curve.tempo_known_trials`). The loader's own `load_participant()` does not apply the one-to-one
  filter at all. A new caller that trusts it gets trials the study excludes.
* `mtrf.py` is shared for `lag_matrix` only. Since `b658693` the confirmatory script solves the ridge
  system inline, and `underfit_check.solve` and `identifiability_sim.ridge` are two more copies of the same
  two lines.
* `shuffled()` (the shuffled-weight reservoir) exists in four copies: `q2_residual.py`, `tempo_curve.py`,
  `calibration/synthetic_calibration.py`, and a generalised form in `robustness.make_reservoirs`.
* `pc1()` exists in four copies. `cp()` (Clopper-Pearson) exists in three, and `w80()` in four.

**Is the duplication harmful? I measured it instead of guessing.**

* The two inline pipelines agree exactly on real data. The `baseline` row of the eleven-row grid goes
  through `underfit_check.load_participant_arrays` and `robustness.loo_residuals`. Its per-participant
  deltas equal the stage-2 values from `q2_residual.py` for all 34 participants and all 12 statistics with
  a maximum difference of 0.0. **[reproduced]**
* The three ridge copies agree with `mtrf.fit_trf` to 1e-7 relative on synthetic data, and subtracting one
  trial's moments equals refitting without it. A new test pins this. **[synthetic]**
* The four `w80()` versions are **not** equivalent, and that is deliberate. `identifiability_merge_a4.w80`
  returns "no W80, already above 0.8 at the lowest w" where `identifiability_merge_a3.w80` returns that
  lowest w. They encode different reporting rules for different addenda. Do not merge them.
* The three identifiability merge scripts are not versions of one script. They are three stages (base map,
  A3, A4) that write three parts of one JSON. All are authoritative. The risk is their coupling, not their
  duplication (defect D4).
* The pilot versions are four different statistics (magnitude spectrum, harmonic phase locking with a
  circular-shift null, windowed tagging, per-unit tagging), not refactors. They are also not independent.
  `nmedt_pilot.py` is the loader that v2, v3, v4 and the ten-song script import, and v3 supplies the
  tagging functions that v4 and the ten-song script import. Only the *statistics* of v1 and v2 are
  superseded, and `pilot/RESULTS.md` keeps v2 as a recorded negative result. Deleting v1 or v3 as
  "superseded" would break the two scripts behind the reported pilot tables.

**Recommendation.** Leave the duplication. Consolidating would touch scripts behind committed results for
no measured gain. Keep the new tests that pin the copies together.

### Separation of concerns

Science, file I/O, output paths and printing sit in the same `main()` in every authoritative script.
`q2_residual.main` is 96 lines that parse arguments, read BrainVision files, filter, fit, score, write
JSON and print the group table. That is why the confirmatory pipeline had no tests: nothing could be
called without data. Splitting it now would change the provenance of the stage-2 code. I tested the pure
functions that already exist and left the rest alone.

### Configuration

Reservoir parameters do not come from one place. They come from nowhere in this repository. **[read]**

| Parameter | Pre-registration | Where the code sets it | `figure_numbers.json` `ms/design` |
|---|---|---|---|
| seed | 42 | `LIFReservoir(seed=42)` in 5 scripts | 42, copied from `robustness/baseline.json` config |
| rho | 0.9 | never set for the confirmatory runs. `0.9` is hardcoded as an *assumed* default in `shuffled()` (4 copies) and `make_reservoirs` (`r.W_rec * (rho / 0.9)`) | 0.9, from `robustness.ROWS['baseline']`, typed by hand |
| beta | 0.05 | never set for the confirmatory runs. `robustness.py` sets `r.beta` | 0.05, same source |
| units | 256 | never set | 256, typed by hand in `make_figures.py` line 314 |
| theta | 0.5 | never set | not present |
| sampling rate | 256 Hz | `FS = 256.0` repeated in 7 files | 256, typed by hand |

Two indirect checks are possible from committed files. The `baseline` row sets `beta = 0.05` and scales the
weights by 0.9 / 0.9, and reproduces stage 2 exactly. The `beta0.01` and `beta0.004` rows move the reservoir
columns (maximum delta change 0.33). So the `beta` attribute is live and its default is consistent with
0.05. **[reproduced]** Nothing in the repository bears on the default spectral radius, the unit count or
the threshold. **[not verified]**

## 5. Scientific integrity assessment

### 5.1 Verified unchanged, by my own reproduction

| Claim | Check | Result |
|---|---|---|
| Stage-2 participant scores | Recomputed all 12 scores for 34 participants from the committed per-trial grid statistics with `tagging.participant_shuffle_z` and the script's random-stream protocol | 3,300 trials. Maximum difference 0.0 on shuffle z, delta, observed mean, null mean and null sd **[reproduced]** |
| Stage-1 participant scores | Same, 8 participants, 719 trials | Maximum difference 0.0 **[reproduced]** |
| Stage-2 group tests and H2 headline | Re-ran `q2_group_merge.py` on the three committed chunk files | 703 values, 0 differences. Median delta 0.2283, 31 / 34 positive, p = 7.97e-9, H2 supported at alpha 0.04, H1 equivalent, H3 equivalent to N0 and not to N2a or N2b **[reproduced]** |
| Stage-1 result | Read from `q2_residual_stage1.json` | 8 participants, p = 0.0547, median delta 0.091. Matches the documents **[read]** |
| Theory 3 merge and both validation worlds | Re-ran `oscillator_merge.py` | 143, 59 and 59 values, 0 differences **[reproduced]** |
| Underfitting merge | Re-ran `underfit_merge.py` | 430 values, 0 differences. 0.039 against 0.228 **[reproduced]** |
| Eleven-row grid table | Re-ran `merge_robustness.py` in a scratch copy | 127 values, 0 differences **[reproduced]** |
| Each grid row changes only what it names | Compared every row with the baseline row, per participant | Seed, rho and beta rows: every reservoir-free column and the held-out r identical (0.0), reservoir columns move. TRF rows: drive columns identical, residual columns and held-out r move **[reproduced]** |
| IAAFT decomposition | Recomputed from `robustness/iaaft.json` | Spectral 0.1562, phase 0.0451, 26 / 34 positive, p = 0.00025. `iaaft.json` equals the union of its five part files. 200 surrogates per participant **[reproduced]** |
| Identifiability base map | Re-ran `identifiability_merge.py` in a scratch copy | 1,187 values, 0 differences. W80 = 0.893. 18 false-positive cells, maximum rate 0.0 **[reproduced]** |
| Identifiability A4 | Re-ran `identifiability_merge_a4.py` | 2,420 and 383 values, 0 differences **[reproduced]** |
| Rule applied in every cell | For the 15 cells that store both p-values: `supported` equals (delta r > 0, p1 < .01, p2 < .05). For all 141 cells: rate equals the mean of `supported`, gamma equals `calibration.json` | 0 mismatches **[reproduced]** |
| Cycle-count summary | Recomputed participant slopes from the four part files (no committed generator) | Medians and p-values match to the 4 stored decimals **[reproduced]** |
| Group-level Theory 3 summary | Recomputed from `oscillator_group_loto.json` (no committed generator) | Exact **[reproduced]** |
| Subgroup mapping | Compared the list in `weineck/README.md` with the subgroup stored for each participant in the stage-2 chunks | 34 of 34 agree. One-to-one trial counts for participants 10 and 11 are 75 and 94, as documented **[reproduced]** |
| Pre-registration power tables | Re-ran `calibration/power_q2.py` with the stated arguments | `power_q2_twostage.json` (24 cells) and `power_q2_n8.json` (18 cells): 0 differences, log text identical **[reproduced]**, on synthetic data by design |
| Synthetic calibration, linear detectors | Re-ran `synthetic_calibration.py` with a stand-in for the missing reservoir | L, N2a and N2b: 243 and 1,728 values, 0 differences **[reproduced]**. Reservoir columns **[not verified]** |
| Manuscript numbers | Section 3, R5 | Byte-identical **[reproduced]** |

### 5.2 Code matches documents, by reading

* **Loader.** `FEAT_FS = 128.0`. `TRIM_S = 1.0`, applied as `crop(tmin = s + TRIM_S)`. Tolerance
  `tol_s = 0.02`. A trial with zero or several candidates gets `None`. Subgroup by minimum summed duration
  mismatch. The second of the doubled S40 markers starts the trial. **[read]**, now pinned by tests.
* **TRF.** Lags 0 to 0.4 s at 64 Hz (27 lags per feature). Four features in the order flux, onsets,
  envelope, derivative. Ridge penalty `lam * trace(X'X) / p`, bias unpenalised. Lambda from
  {0.1, 1, 10, 100}. The grid and the 12-fold cap on inner validation were already in the script at the
  freeze commit. **[read]**
* **No leakage.** The model for held-out trial t is solved on the summed moments minus trial t. The inner
  selection removes both t and the inner validation trial. EEG is z-scored within trial. The band-pass
  runs on each trial segment separately. The pooled leave-one-participant-out variant removes the held-out
  participant's moments. I found no path by which a held-out trial or participant enters its own fit.
  **[read]**, and the estimator-level property is pinned by a test **[synthetic]**.
* **Channels and band.** Fz, FC1, FC2, Cz, F3, F4, C3, C4. Fourth-order Butterworth 0.5 to 30 Hz,
  zero-phase, at 1000 Hz. **[read]**
* **Shuffle null.** 500 relabellings per participant. Each trial gets another grid tempo more than 5 %
  away. On the 13-tempo grid the smallest ratio is 1.067, so all 12 other tempi are eligible. The null mean
  runs over the same N trials. **[read]**, pinned by tests.
* **Shuffled-weight control.** All recurrent weights permuted with `RandomState(seed + 1000)`, then
  rescaled to spectral radius 0.9. This matches "shuffled (same rho)" only if the canonical reservoir's
  radius is 0.9. **[read]** for the code, **[not verified]** for the assumption.
* **Identifiability.** Worlds A, B and C and the nested option are implemented as the plan describes.
  Each cell folder's `world` and `nested_lambda` fields match its name. A3 and A4 queue scripts derive the
  seed from the World A cell string, so comparisons are paired. **[read]**

### 5.3 Rests only on the repository's own records

* Everything upstream of the per-trial statistics: reading the EEG, matching, filtering, the TRF fits, the
  residuals, the reservoir readouts. **[repo record]**
* All 141 identifiability cells as simulations. I verified their internal consistency and their merges,
  not their generation. **[repo record]**
* The NMED-T pilot, the alignment checks in `weineck/README.md`, the tempo curve. **[repo record]**
* The reservoir columns of the synthetic calibration, and the instrument gain range quoted from it.
  **[repo record]**

### 5.4 Scientific concerns

These are separate from the engineering defects. None is fixed here. Each proposal differs from the
committed method and is labelled as such.

**S1. The reservoir is unspecified inside this repository.** Code: `LIFReservoir(seed=42)` in
`q2_residual.py` line 62, `tempo_curve.py` line 56, `cycle_count_control.py` line 26,
`synthetic_calibration.py` line 107, `robustness.py` line 51. No commit, hash or copy of
`experiment_zero.py` is recorded anywhere (searched every document). Likely effect: none on H2. For H1, H3,
R minus Rs and the tempo curve's reservoir columns, the results cannot be reproduced or audited, and a
later change to that file's defaults would silently change what "the canonical reservoir" means. Also
unknown from here: whether `forward()` resets its state between calls. The scripts call it once per trial
on the same object. *Proposal (not the committed method):* record the commit and SHA-256 of the file used,
and assert the four stated parameters at construction.

**S2. The identifiability noise bank has no recorded origin.** Defect D1 gives the evidence. Likely effect:
unknown. `docs/IDENTIFIABILITY_RESULTS.md` describes the noise as "Gaussian with the pooled residual
spectrum shape", which is plausible for a hand-made file. It cannot be confirmed. *Proposal:* recover the
original `noise_shape.npz` and record how it was made, or regenerate the statistics with a fixed step and
report any change to the map as a dated addendum.

**S3. The lambda choice sits on the edge of its grid.** In the committed stage-2 chunks the smallest value,
0.1, is chosen for 1,974 of 3,300 held-out trials (60 %). The counts are 0.1: 1,974, 1: 932, 10: 234,
100: 160. Stage 1: 437 of 719. **[reproduced]** A selection that mostly returns its boundary may be
censored. A less regularised TRF could remove more linearly predictable signal. Likely effect on H2: I do
not know. The exploratory linear-world simulation ran through the same grid and left a residual delta of
0.039, which argues against the grid edge explaining 0.228. It does not test a wider grid. I did not find
the chosen-lambda distribution reported in any document. *Proposal (exploratory, differs from the frozen
method):* report the distribution, and add a row with the grid extended downward.

**S4. Inner validation uses the first 12 training trials in recording order** (`q2_residual.py` line 109).
The frozen text says "lambda by nested CV within participant". The cap was in the code at the freeze. The
choice of lambda therefore depends on which trials came first. Likely effect: small. *Proposal:* state it
in the methods.

**S5. "Recomputed here, must match stage 2" holds at the group level, not per participant.**
`underfit_check.py` scores the residual at its own length. `q2_residual.py` first truncates residual and
drive to a common length. The group median (0.2283059621647527) and the count of positive participants
(31) are identical. Per participant, the underfitting check's `resid_real` delta equals the stage-2 value
to rounding in 18 of 34, differs by more than 1e-6 in 16, and by more than 0.01 in 3 (largest 0.024,
participant 10). **[reproduced]** The repository recorded this itself in
`residual_discrepancy_check.json`. The table row label "(= stage 2)" in `docs/UNDERFIT_CHECK.md` does not
carry the caveat.

**S6. The shuffle null's 5 % exclusion is only correct on the 13-tempo grid.** For any other grid size
`participant_shuffle_z` (line 75) measures distance on `log(1 .. G)`, a placeholder, not on the real tempi.
No committed result uses another grid. The NMED-T generalization would (scenario D).

**S7. Counting cells.** `\NumNCells` resolves to 102, the length of `identifiability.json` `cells`. That
list includes 8 World A refinement cells added by addendum A3. The documents say "94 grid cells plus
addenda". If the rewrite uses the macro for the grid size, it will say 102.

**S8. Tolerances in two documents are tighter than what I measured.** `docs/STAGE2_RESULTS.md` says the
refactor "reproduces stage-1 output to 1e-14". I measured 1.3e-11 on the stored per-trial statistics and
3.5e-13 on the scores. `docs/IDENTIFIABILITY_RESULTS.md` says "World A reproduces the committed cells to
1e-10" and "World B and World C at w = 0 are bit-identical to World A at w = 0". From committed files: the
re-run cells differ from the first-committed ones by up to 2.1e-10, and B and C at w = 0 are bit-identical
to each other but differ from the committed World A cell by 1.2e-10. The second claim is presumably true
of a World A re-run that was not committed. Decisions are identical in every case. Effect on any result:
none.

**S9. Version sensitivity.** With Python 3.13.18, numpy 2.5.5 and scipy 1.18.1 every p-value in every merge
I re-ran matches to the last bit. `scipy.stats.wilcoxon` has changed its default method across releases, so
an older scipy may give different p-values for n = 34. I did not test other versions. **[not verified]**

### 5.5 Confirmatory results and the freeze

Timeline from Git, all **[read]**:

| Position | Commit | Event |
|---|---|---|
| #16 | `935c80a` | Freeze. Only the pre-registration and a power table change |
| #17 | `a88b923` | Status line records the commit hash. One print statement fixed in `q2_residual.py`, three lines in `tempo_curve.py` (a `max()` over a value that had become a scalar). At the freeze, the tempo-curve script could not have run to completion in that form |
| #22 to #25 | `73626a0` to `43f4984` | Addendum A1 and A1-power. Committed stage-1 log: 7 participant lines, no group table |
| #26 | `4e0d5fc` | Stage-1 results. Group table appears |
| #27 | `9280000` | Stage 2 launched. Fourth recording block of participant 18 fetched |
| #29 | `b658693` | Q2 refactor, stage 2 relaunched single-threaded. `q2_check_subj10_fast.json` committed as the equivalence record |
| #31 | `c8b1503` | Stage-2 chunks and merged file. Never modified since |

Two things to know. Participant 18 has 71 trials in the stage-1 file and 89 in stage 2, because the
missing block was fetched between stages. The addendum and the launch commit both say so. And all stage-2
numbers come from the refactored script, not from the script as it stood at the freeze. I confirmed the
two are numerically equivalent to 1.3e-11 on the seven unchanged stage-1 participants.

### 5.6 Could not verify

* Raw data to per-trial statistics, for anything. No data here.
* Any reservoir readout. No reservoir file here.
* Exact reproduction of an identifiability cell, and `identifiability_merge_a3.py`,
  `identifiability_crit2_diag.py` and `prediction_overlap.json`. No sufficient statistics here.
* That `main.pdf` matches the current `numbers.tex`. No LaTeX here.
* The README's run-time figures for the regression test (about 5 and 15 minutes). The committed logs show
  753 s for the reference cell and 1,165 s for its A4 re-run, which fits.

### 5.7 Extension

The extension was checked by a delegated agent working under this audit, read-only, in its own scratch
environment. Items marked † I re-checked myself against the files.

**Holds up.**

* *Scope.* † The merge changes 37 files, all under `extensions/`. No commit on the extension side touches
  another path. **[read]** The extension does read one file outside its tree: `src/rhythmic_metrics.py`
  imports `weineck/tagging.py`. It writes nothing there.
* *Rules before outputs.* † Addendum A1 is `e459b29` (#239). Addendum A2 and `DECISION_RULES.md` are
  `17063fb` (#241). The first scored model output, `results/reconstruction_control.json`, is `376ccfe`
  (#242). `DECISION_RULES.md` has exactly one commit, and its SHA-256 equals the hash quoted in that
  commit's message. `eval_rf.py` and the metric modules have no commit after `376ccfe`. **[read]**
* *The decision arithmetic.* Recomputed from the 640 committed rows of `rf_eval.json`: the timing flag
  matches in 640 of 640 rows, and the matched comparison comes out identical (+0.2060, bootstrap interval
  [0.1322, 0.2829], Wilcoxon p = 0.0078). **[reproduced]** from committed rows. The rows themselves are
  **[repo record]**.
* *The synthetic validations.* `validate_metrics.py` and `validate_aliasing.py`, run from an unmodified
  scratch export, regenerate `metric_validation.json` and `aliasing_validation.json` byte for byte.
  **[reproduced]**, synthetic by design.
* *Tests.* 23 tests, 23 pass, 0 skip, 11 s. Environment: Python 3.13.18, numpy 2.5.5, scipy 1.18.1,
  mir_eval 0.8.2, torch and torchaudio 2.7.1 in the `+cu126` build, because the CPU wheel index is blocked
  by this sandbox's proxy. The plan records `+cpu`. `stable_audio_3` is not on PyPI and was not installed.
  **[synthetic]**
* *Data and secrets.* 37 paths ever added under `extensions/`: 16 py, 7 json, 4 png, 4 pdf, 3 md, 2 log,
  1 gitignore. No audio, latents or weights. No credential-shaped string in any commit. The rejected access
  token appears only as prose (evidence report lines 15 and 415 to 417). **[read]**

**Does not hold up.** These concern the extension's own record. None touches the EEG study.

1. *The experiment that was evaluated is not in the plan.* † The word "fallback" occurs 0 times in
   `EXPERIMENT_PLAN.md`, and neither editor name (V0, V1) appears in it. Plan section 3, row 4, rejects a
   model trained from scratch. The editors first appear in `376ccfe`, after the freeze, with no addendum,
   although the plan's header says changes are "recorded as dated addenda below, never as silent edits".
   The evidence report calls it "a pre-planned fallback" (line 16) and uses "pre-registered" for rules
   that were committed in the same session. The metric rules do predate the outputs. The choice of what to
   score with them is not in the frozen plan.
2. *Several frozen rules were not applied.* † `DECISION_RULES.md` lines 38 to 40 require a direction check
   and say that an edit whose transformation is below the oracle re-synthesis value of the same composition
   "is labelled 'no effective edit', not a success". `eval_rf.py` computes the oracle only as a reference
   point and applies no such label. Also absent from the code: the sign test on the transformation
   measure, the signed displacement, the secondary acoustic measures (RMS, crest, chroma), and the beat-F1
   secondary measure. The evidence report admits only the last.
3. *The headline comparison sits in the "no effective edit" region.* † The three matched transformation
   levels are 1.63, 2.29 and 2.94 dB. The oracle reference is 3.46 dB (group median, `rf_eval.json`
   `decision.nonperiodic.reference_points.oracle_target`). All three are below it. The delegated
   recomputation counts outputs that are both timing-preserved and at or above the oracle level: 0 of 144
   for V0 and 51 of 144 for V1. The direction of the conclusion survives. The evidence report does not
   mention the label.
4. *A reported test statistic pairs the wrong denominator with its p-value.* † Evidence report line 169:
   "in 7/8 for V1 (p = 0.016)". The stored value (0.015625) is the two-sided sign test for 7 of 7. One
   composition has an undefined correlation and was dropped. A 7-of-8 test gives 0.070.
5. *The timing rule rejects the untouched source* in 1 of 8 probe compositions (lag specificity exactly 0).
   Not disclosed. **[reproduced]** from committed rows by the delegated check.
6. *Numbers in the evidence report that are not in the file cited beside them:* "0.945 for the untouched
   audio" (line 78, from a different set and file), "about 3.3 s per sampler step" (line 81, the JSON gives
   6.05), "about 10 s per step" and "11 MB" (no file), and the alias floors at lines 187, 221 and 320
   (validation set values, not the evaluated set). The report's opening claim that every number is read
   from a committed result file is therefore not true as written.
7. † `results/reconstruction_control.json` has no generating script in the tree.
8. *Test gaps.* Of 18 seeded single-line regressions, the tests caught 12. Not caught: the timing-score
   formula, the onset tolerance (50 to 100 ms), a sign-flipped training target, a missing factor in the
   partial-noise start, the hidden width, and the whole source-conditioning path of V1. `eval_rf.py`,
   `train_rf.py` and `build_latents.py` have no tests.

**Could not verify.** Everything that needs the Stable Audio 3 model, the SAME-S autoencoder, the latents
or the checkpoints: `rf_training.json`, the rows of `rf_eval.json`, the reconstruction control, the CPU
timing. **[not verified]**

**Paths.** `RPA_MODEL_DIR` defaults to `/home/user/models/sa3` (`src/model.py` line 22).
`/home/user/.venvs/rpa` appears in `tests/test_metrics.py` line 4 and the plan. Ten files inject
`sys.path`. The evidence report tells the reader to download `model.safetensors`, while the loader expects
`base_bf16.safetensors` and `base_config.json`. No conversion step is recorded.

**Licence.** The plan states the Stability AI Community License for the model (research and non-commercial
use). The subtree states no licence for its own code.

## 6. Reproducibility assessment

### What a new researcher needs

| Need | State |
|---|---|
| Python | 3.13 (seen in committed tracebacks: `/usr/local/lib/python3.13/`). No version is stated for the EEG code |
| Packages, EEG side | numpy, scipy, mne (loader only), matplotlib (figures and two merges), threadpoolctl (procedure and its test), h5py (pilot v1 and v2 only). No manifest |
| Packages, extension | torch, torchaudio, mir_eval and others, recorded in `EXPERIMENT_PLAN.md` section 1 |
| External code | `dissoAdventureExperiments/chapter5Experiments/experiment_zero.py` at an **unrecorded** commit, expected at `/home/user/dissoAdventureExperiments/` |
| Data | Weineck et al. at `/home/user/data_local/weineck2022/` (14.1 GB), NMED-T at `/home/user/data_local/nmedt/` (39.7 GB), the stimulus feature file passed as `--feats` |
| Run order | Q2 chunks, then merge. Kernels, then stimuli, then cells, then `identifiability_merge.py`, then `_merge_a3.py`, then `_merge_a4.py`. `make_figures.py`, then `make_numbers.py`. Only the identifiability order is written down, and that step is broken (D1) |
| Chunking | Stage 2 ran as participants 1 to 13, 14 to 25, 26 to 37. Recoverable from the chunk files, not from any document |
| Threads | Single-threaded BLAS for exact identifiability reproduction. Stage 2 stalled on thread oversubscription and was relaunched single-threaded (`b658693`) |
| Run times, from committed logs | Grid row: 58 to 72 minutes for 34 participants. Identifiability cell: about 13 minutes for 20 datasets, 91 minutes nested for 10. Theory 3: about 15 minutes per participant. Kernels: about 4 minutes per half. Statistics: 75 s |
| Outputs | `weineck/results/` by default or by hardcoded path |
| Platform | CPU only. The Stanford host needs an extra root CA from the cloud sandbox (`WEEK1_ASSESSMENT.md` section 4) |
| Full Git history | Required by `make_figures.py`, which resolves provenance commits from `git log` and asserts each is unique |

### What I ran

Environment built for the audit: Python 3.13.18, numpy 2.5.5, scipy 1.18.1, mne 1.13.2, h5py 3.16.0,
matplotlib 3.11.2, threadpoolctl 3.8.0, pyflakes 4.1.0. Four cores, 15 GB.

| Run | Outcome | Label |
|---|---|---|
| `python3 -m unittest discover -s weineck/tests -v` at baseline | 11 tests in 0.24 s. 8 pass. 3 skip: `ReproduceCommittedCell` (2) and `ComponentCorrelationOnData` (1), because `A_a.npy`, `A_al.npy`, `A_l.npy`, `C_la.npy`, `C_alh.npy` and `stimuli_meta.npz` are absent | [reproduced] for the seed rule and the W80 headline, [not verified] for the cell |
| Same, after adding tests | 59 tests in 1.4 s. 56 pass, the same 3 skip | [synthetic] and [reproduced] |
| Merge scripts re-run (`q2_group_merge`, `oscillator_merge` three times, `underfit_merge`, `merge_robustness`, `identifiability_merge`, `identifiability_merge_a4`) | Every output identical to the committed file | [reproduced] |
| `identifiability_merge_a3.py` | Stops at `FileNotFoundError: .../A_a.npy` | [not verified] |
| `make_figures.py` then `make_numbers.py`, scratch copy | Identical outputs. 7.4 s | [reproduced] |
| `calibration/power_q2.py`, two committed tables | Identical. 75 s for the n = 8 table. I did not time the other | [reproduced] (a simulation reproduced, not an EEG number) |
| `calibration/synthetic_calibration.py`, both grids, with a stand-in reservoir | Linear detector columns identical. Reservoir columns meaningless by construction and not compared | [reproduced] for L, N2a, N2b. [not verified] for R columns |
| Import check, 38 non-extension Python files | All compile. 6 fail only on `No module named 'experiment_zero'` and import cleanly with a stand-in: `q2_residual`, `tempo_curve`, `robustness`, `cycle_count_control`, `synthetic_calibration`, `nmedt_tensong`. 9 are scripts with top-level code and positional arguments, so they were compiled and (where possible) run, not imported. No other broken import | [read] |
| `pyflakes`, report only | 35 unused imports, 4 unused locals, 1 redundant re-import (`q2_residual.py` line 88). No undefined names | [read] |
| Extension tests and validations | Section 5.7 | |

To run the scripts that hardcode `/home/user/arspinet-rhythmic-entrainment`, I exported the tree with
`git archive` to a scratch directory and replaced that prefix in the copy only (9 files). No logic was
changed. The stand-in reservoir was a scratch file, never placed in the repository.

### Dependency gaps

No manifest exists. If you want one, these are versions I can show reproduce the committed merge outputs
and manuscript numbers bit for bit: Python 3.13.18, numpy 2.5.5, scipy 1.18.1, matplotlib 3.11.2,
threadpoolctl 3.8.0, mne 1.13.2 (import only, no data read). I can't show what the original runs used
beyond "Python 3.13 and numpy 2.x" from tracebacks. Results could depend on versions in three places:
BLAS summation order (identifiability, at the 1e-10 level), `scipy.stats.wilcoxon` method selection
(p-values), and `scipy.signal` filtering and resampling (per-trial statistics, untested).

## 7. Multi-agent readiness

### What a cold-start agent could and could not learn at baseline

| Question | At baseline | After this audit |
|---|---|---|
| 1. What the repository is, and its relation to the dissertation | Yes, README first paragraph | Same, plus `AGENTS.md` section 1 |
| 2. Which results are confirmatory, exploratory, pilot, simulated, extension | Mostly, from the README table. The extension was invisible from the README | `AGENTS.md` section 2 |
| 3. Which scripts are authoritative for each result | Only by reading every results document | `AGENTS.md` section 2, this report section 4 |
| 4. Which files must never be edited | Implied, never listed | `AGENTS.md` section 3 |
| 5. Which invariants must hold | Scattered across docstrings | `AGENTS.md` section 4, tests |
| 6. How to run tests and what a skip means | Command in README. Skip reason in the test | `AGENTS.md` section 6 |
| 7. How to add an experiment | By imitation only | `AGENTS.md` section 8 |
| 8. How to record results | By imitation only | `AGENTS.md` section 9 |
| 9. How to recover a decision | Possible, the commit messages are detailed | `AGENTS.md` section 10 |
| 10. How to hand off a long run | Not documented | `AGENTS.md` section 11, with limits |
| 11. Git discipline | Not documented | `AGENTS.md` section 12 |

### Scenario A. Orientation

*Read:* `README.md`, `docs/FRAMING.md`, `docs/PREREGISTRATION_DRAFT.md`, `docs/STAGE2_RESULTS.md`,
`pilot/RESULTS.md`, `extensions/rhythm_preserving_audio/EXPERIMENT_PLAN.md`.
*Found:* the layering is recoverable and the documents are careful about it. The pre-registered study is
`q2_residual.py` and `q2_group_merge.py`. The follow-ups each have a plan, code and a results document.
The pilot predates the freeze and says so.
*Ambiguities:* the README did not list the extension. The eleven-row grid is "pre-registered robustness
rows" in `STAGE2_RESULTS.md` and `FRAMING.md` and "exploratory" in the README and its own plan. FRAMING
item 2 says the identifiability map is in progress while item 11 reports it complete.
*Reliable?* Yes after the README additions. The two wording conflicts remain.

### Scenario B. Reservoir

*Read:* the 11 files that mention the external path, the pre-registration, `pilot/RESULTS.md`.
*Found:* the file `chapter5Experiments/experiment_zero.py`, class `LIFReservoir`. Constructor called with
`seed` only. Attributes used: `W_rec` (square recurrent matrix, read and overwritten) and `beta`
(overwritten in the grid rows). Method `forward(x)` takes a z-scored one-dimensional drive at 256 Hz and
returns a time-by-units array, read as unit-PC1 (first left singular vector times its singular value) and
as population mean. Dependent scripts: `q2_residual.py`, `tempo_curve.py`, `robustness.py`,
`cycle_count_control.py`, `make_figures.py` (only to rebuild the Fig. 1 traces),
`calibration/synthetic_calibration.py`, and all five pilot scripts.
*Cannot be learned without the other repository:* the commit used, the number of units, the threshold, the
input weights, the reset rule, whether state persists between `forward` calls, whether the weight matrix
is sparse, and whether its spectral radius is 0.9 as four functions assume.
*Reliable?* No. An agent can describe the interface. It cannot run or check any reservoir result.

### Scenario C. Trace a result

*H2, from document to data.* `docs/STAGE2_RESULTS.md` (median delta 0.228, 31 / 34, p < 1e-4) to
`q2_residual_stage2_merged.json` `group.resid_N0` to `q2_group_merge.py` (one-sided Wilcoxon on participant
z, alpha 0.04) to `q2_residual_stage2_chunk{1,2,3}.json` `subjects.<id>.scores.resid_N0` to
`q2_residual.py` lines 122 to 130 (`participant_shuffle_z`, 500 shuffles, `RandomState(int(subject))`) to
`subjects.<id>.trials[*].resid.N0` (13 grid statistics per trial) to `tagging.grid_stats` and `tag_z` to
the residual of the leave-one-trial-out TRF (`mtrf.lag_matrix`, inline ridge) to
`weineck_loader.match_trials` to the BrainVision files and `Figure1_SourceData1.mat`.
I walked the chain and reproduced every step below the per-trial statistics. The chain is unbroken down
to the data and unverifiable above it without the data.
*One macro.* `\NumHTwoDelta` in `numbers.tex` (0.228) comes from `make_numbers.py` entry
`('HTwoDelta', 'fig2/resid_median_delta', '3')`, which reads `figure_numbers.json`
`fig2.resid_median_delta` = 0.2283059621647527, which `make_figures.py` `fig2()` takes as the median of
`q2_residual_stage2_merged.json` `group.resid_N0.delta`. A new test checks this link.
*Ambiguities:* none in the chain. One trap: the confirmatory script imports `fit_trf` and `predict` from
`mtrf.py` and uses neither.
*Reliable?* Yes.

### Scenario D. Safe extension (NMED-T generalization)

*Read:* `docs/FRAMING.md` plan item 5, `pilot/RESULTS.md`, `docs/lit_datasets.md`, `pilot/nmedt_tensong.py`,
`weineck/q2_residual.py`, `weineck/tagging.py`.
*Found:* the item is "NMED-T generalization of the Q2 pipeline (requires the ten tracks, alignment via the
60-s click grid)". The audio is not distributed. The pilot is audio-free, uses the cleaned files and
predates the freeze.
*What blocks an agent:*

1. The audio must be bought. That is the author's decision and purchase.
2. No feature extraction exists here. The Weineck features (flux, onsets, envelope, derivative) came from
   the data release. An NMED-T version needs new code and a choice of feature definitions.
3. The loader and the Q2 script are Weineck-specific: markers, subgroups, the 1.0 s trim.
4. The shuffle null needs each participant to have trials at several tempi, and its 5 % rule is only
   correct on the 13-tempo grid (S6). NMED-T has ten songs with one tempo each.
5. Nothing says whether the generalization is confirmatory or exploratory. The frozen text mentions NMED-T
   under "Q2 only if the ten tracks are purchased and aligned".

*How to do it without touching earlier results:* a dated plan in `docs/` committed first, new scripts under
a new folder (not `pilot/`), new result names, a results document that states its layer, one README row.
`AGENTS.md` section 8 writes this down.
*Reliable?* The procedure, yes. The task, no. It needs three author decisions (audio, features, layer)
before any agent should start.

### Scenario E. Handoff of an interrupted queue

*Read:* the four `run_*.sh` scripts, the queue and lock files, `identifiability_sim.py`,
`identifiability_procedure.py`, `robustness.py`, `merge_robustness.py`, the `Interim:` commits.
*Found:*

* The identifiability workers pop a line from the queue file *before* running the cell. A cell that was
  running when the job died is no longer in the queue. Nothing records which cells were in flight.
* A queue script only builds its queue if the file is missing. The three committed queue files are empty,
  so on this tree all three scripts start, find nothing and print "all cells done". That protects the
  committed cells from an accidental re-run. It also means a second agent must know to rebuild the queue
  by hand.
* An incomplete cell is detectable: `datasets_done` is below its target. `identifiability_sim.py` cannot
  resume inside a cell and restarts it from dataset 1. `identifiability_procedure.py` skips complete cells
  with the right seed and re-runs the rest.
* The robustness queue locks with directories that Git does not track, so a clone has no locks and would
  re-run every row. A row without an `ended` key is incomplete and restarts from the first participant.
  The script's feature-file path points into a session scratchpad that no longer exists.
* The IAAFT row was split by hand into five parts after seven participants (`fcddff1`). The split is
  recorded in `iaaft_split.json`. The script that ran the parts and the step that assembled them are not
  in the repository.

*Reliable?* Partly. Completed work is safe and incomplete work is detectable. Resuming needs manual steps
that were nowhere written down. `AGENTS.md` section 11 now states them and proposes that an `Interim:`
commit name the remaining cells and the resume command.

## 8. Defects and remediation

Severity reflects risk to the scientific record first.

| ID | Severity | Defect and root cause | Files | Action taken | Verification | Remaining risk |
|---|---|---|---|---|---|---|
| D1 | High | Identifiability statistics cannot be rebuilt as documented. `noise_shape()` stacks Welch spectra of unequal length when a trial is shorter than 512 samples, so `np.mean` raises. Both committed kernel logs end in that traceback (0 of 2 reach "kernels part done"), after the kernels were saved. The script would write `noise_shape_<first subject>.npz`. The stimuli part reads `noise_shape.npz` and otherwise falls back to 1/f with a warning. The committed `stimuli.log` has no warning, so the file existed. Its origin is unrecorded | `weineck/identifiability_precompute.py` lines 54 to 59, 79 to 82, 112. `results/identifiability/kernels_part{1,2}.log`, `stimuli.log` | Caution added to `README.md`. Code untouched | Traceback read in both logs. File names read in code. No "WARNING" in `stimuli.log` | High until the original file is recovered or the map is regenerated. A rebuild today gives a different noise bank, and the exact-reproduction test would fail |
| D2 | High | External reservoir at an unrecorded revision, with its stated parameters never set or asserted here (S1) | 11 files with the `sys.path` line | None possible. Documented in `AGENTS.md` | Searched all documents for a commit or hash: none | High for every reservoir result. None for H2 |
| D3 | Medium | `merge_robustness.py` overwrites `docs/ROBUSTNESS_RESULTS.md`. The script writes 22 lines. The committed document has 52, including the hand-written audit paragraph, row annotations and the IAAFT decomposition | `weineck/merge_robustness.py` line 51 | Warning in `AGENTS.md` section 5 | Ran it in a scratch copy and diffed | One command away from losing analysis text. Recoverable from Git |
| D4 | Medium | `identifiability_merge.py` rewrites `identifiability.json` without `A3` and `A4`. Restoring `A3` needs statistics that are not committed | `weineck/identifiability_merge.py` line 41 | Warning in `AGENTS.md`. New test asserts the key set | Ran it in a scratch copy: 5 keys out, 7 in the committed file | Same as D3, and `A3` cannot be regenerated here |
| D5 | Medium | Six committed outputs have no committed generating code (section 4). Three feed manuscript macros | `weineck/results/` | None. Three recomputed independently and matched | Section 5.1 | `prediction_overlap.json` and the noise shape stay unverified |
| D6 | Medium | Hardcoded absolute paths in 29 files. Repository root in 9, data directory in 16, reservoir directory in 11, a dead session scratchpad in 2 (`run_robustness_queue.sh` line 4, `make_figures.py` line 65). Extension: model directory and venv path | see counts | None. Changing them changes provenance | `git grep` counts | Nothing runs outside `/home/user/...` without edits |
| D7 | Medium | No dependency manifest | repository | None. Versions that reproduce are in section 6 | | Version drift, notably scipy |
| D8 | Medium | No LICENSE. `CITATION.cff` has placeholder authors, `license: "TBD"`, and a version and release date for a release that does not exist | `CITATION.cff` | README wording corrected | `git ls-remote --tags` | Reuse terms for the code are undefined |
| D9 | Low | Confirmatory pipeline untested. One test file, whose three substantive tests skip on every fresh clone | `weineck/tests/` | 48 tests added in two files | 59 run, 56 pass, 3 skip. 27 seeded regressions all caught (below) | Raw-data stages still untested |
| D10 | Low | README omitted the extension, the manuscript folder and the tests, and described the release as archived | `README.md` | Fixed | Paths checked against `git ls-files` | None |
| D11 | Low | Statements in results documents and one docstring that I measured as inaccurate (S5, S8), FRAMING item 2 ("in progress"), `make_figures.py` docstring ("no trace is written to the repo", while `fig1_traces.npz` is committed and the same file's `example_traces()` says it is saved there), stale `main.pdf`, `weineck/README.md` file list (5 of 38 scripts) | several | None. Results documents and scripts are yours to change | Section 5.4 | Readers get tighter tolerances than the files support |
| D12 | Low | "Aggregate JSON only" (R3) | `README.md`, `weineck/README.md` | None | Section 3 | Wording |
| D13 | Low | Interim and scratch outputs committed beside results without a marker: `oscillator_interim_partial.json`, `oscillator_sim_hopf_partial.json`, `osc_smoke_subj{10,14}.json`, `robustness/iaaft_part{0..4}.json`, `iaaft_split.json`, six empty queue and lock files, `calibration/results/power_q2.json` (superseded by the two-stage table) | `weineck/results/`, `calibration/results/` | None. `AGENTS.md` section 11 states that an interim file is not a result | | A reader may take a partial file for a result |
| D14 | Low | Latent edge cases, not reached by the data: `mtrf.lag_matrix` raises when the input is shorter than the lag span. `match_trials` raises if the table lacks one of the four subgroups. `q2_residual.py` takes the fronto-central indices from the last trial's channel list | named files | None. Found while writing tests | | Would surface on a new dataset |
| D15 | Info | A shallow clone breaks `make_figures.py` (provenance lookup asserts one commit per message prefix) | `weineck/figures/make_figures.py` lines 305 to 311 | Noted in `AGENTS.md` | This environment's default clone was shallow | |
| D16 | Info | The staged abstract in `pending_submission_edits.md` calls the reservoir "ARSPI-Net, 256 leaky integrate-and-fire units". This repository contains a call to an external LIF reservoir and nothing else of ARSPI-Net | `docs/manuscript/pending_submission_edits.md` | None | | The label cannot be checked from here |

Extension defects (section 5.7 has the evidence):

| ID | Severity | Defect | Action taken | Remaining risk |
|---|---|---|---|---|
| E1 | Medium | The evaluated experiment (two from-scratch editors) is absent from the frozen plan, with no addendum. The evidence report calls it "pre-planned" and "pre-registered" | None | The extension's claim to pre-specification covers the metrics, not the experiment |
| E2 | Medium | Frozen rules not applied by `eval_rf.py`, among them the "no effective edit" label. The headline matched comparison lies wholly below the oracle level that the label uses | None | The headline may be read as a success the frozen text would not call one |
| E3 | Low | "7/8 (p = 0.016)". Five numbers not in their cited files. One undisclosed rule failure on the untouched source | None. A results document | Readers cannot trace those numbers |
| E4 | Low | `reconstruction_control.json` has no generator. The weight-conversion step is undocumented | None | One control cannot be regenerated |
| E5 | Low | Test gaps: 6 of 18 seeded regressions missed, evaluation script untested | None. I did not add tests outside `weineck/tests/` | A change to the timing score or the V1 path would pass the tests |
| E6 | Low | Stale branch state in the evidence report: "local branch" (line 3), a commit list that ends with "hash reported in the conversation", and a verification command that returns nothing since the merge | Fixed (F6) | None |

### Fixes applied, one by one

**F1. New tests for the confirmatory building blocks.** *Problem:* D9. *Root cause:* science and I/O share
one `main()`, so only pure helpers are testable, and none were tested. *Files:*
`weineck/tests/test_pipeline_invariants.py` (new, 32 tests). *Change:* synthetic fixtures for
`match_trials` and `trials_from_events`, `lag_matrix`, kernel recovery, leave-one-trial-out against an
explicit refit, agreement of the three ridge copies, `tag_z` against an independent implementation of the
pre-registered definition on 1/f noise, the shuffle null (own label never drawn, sample size kept, random
stream consumed as the committed scores assume), and `identifiability_sim.decide` with rank patterns whose
exact p-values straddle 0.01 and 0.05. *Verification:* all pass in 0.3 s. I then seeded 27 regressions,
one at a time, in a scratch copy: tolerance 20 to 30 ms, trim 1.0 to 0.9 s, ambiguous trial accepted,
first S40 kept, bias regularised, held-out trial leaked, lag sign flipped, unnormalised penalty, second
harmonic dropped, mean baseline, linear baseline, neighbour band narrowed, 20 s segments, own tempo
drawable, one label per shuffle, z by standard error, criterion alphas changed, baseline restricted to the
short TRF, stage-2 alpha, two-sided test, TOST bound, seed modulus, seed string, tolerant `make_numbers`,
one edited result value, one hand-edited macro. All 27 were caught. *Result:* pass.

**F2. Consistency tests for committed results.** *Problem:* nothing detected an edited or regenerated
results file. *Files:* `weineck/tests/test_committed_results.py` (new, 16 tests). *Change:* re-runs
`q2_group_merge.main()` on the committed chunks into a temporary directory and compares with the committed
merged file. Recomputes every stage-2 participant score from per-trial statistics. Checks the baseline grid
row against stage 2, the reservoir-free columns of the reservoir rows, the IAAFT assembly, all 141
identifiability cells against the rule, seed rule and calibration, and `numbers.tex` against a fresh run of
`make_numbers.py`, including the failure on a missing key. *Verification:* all pass in 1.0 s. No file in
the repository is written. *Result:* pass. These tests read committed files only, so none skips on a fresh
clone.

**F3. Test infrastructure.** *Problem:* unittest discovery now imports the new files before
`test_identifiability_procedure.py`, which sets the BLAS thread variables "before numpy loads". *Change:*
both new files set the same variables before importing numpy. *Verification:* after discovery,
`threadpool_info()` reports 1 thread for OpenBLAS. *Result:* the existing exact-reproduction test runs
under the conditions it documents.

**F4. `AGENTS.md` and `CLAUDE.md`.** *Problem:* no agent instruction file. *Change:* one `AGENTS.md` at the
root with rules only (layers, frozen files, invariants, overwriting scripts, tests, adding an experiment,
recording, handoff, Git). It links to the README for the science. Two items are marked as proposals. A
two-line `CLAUDE.md` points to it. No memory system, task registry or second source of authority.
*Verification:* every path in it resolves (`git ls-files` plus the new files).

**F5. `README.md`.** *Problem:* D10, R12, D1. *Change:* pointer to `AGENTS.md` and this report. A caution
under the identifiability instructions. A sentence on the two new test files. "Archived release" replaced
by "planned and does not exist yet". Three rows added to the code table (`weineck/tests/`,
`docs/manuscript/`, `extensions/rhythm_preserving_audio/`). 22 lines added, 1 replaced. No scientific
statement altered. *Verification:* paths resolve. Claims are the ones evidenced in this report.

**F6. Branch state in the extension's evidence report.** *Problem:* E6. *Root cause:* the report was
written before the push and the merge, and only its section 7 (now section 6) was updated afterwards. *File:*
`extensions/rhythm_preserving_audio/RESEARCH_EVIDENCE.md`. *Change:* line 3 now says the branch was
pushed and merged at `a78d143`. The commit list names `89af6d5`, `4067d8b`, `9c6e71d`, `9df833d` and the
merge. The scope check is now `git diff --name-only a78d143^1 a78d143`, with a note on why the old command
is empty. 8 lines added, 6 removed. No number, result or reading changed. *Verification:* the new command
prints 37 paths, none outside `extensions/`. The old one prints nothing.

### Files changed by this audit

Left uncommitted during the audit, then committed and pushed to branch `ccr-2b3cc9be-qgn4td` on the author's
instruction. Not merged into `main`. No tag, no history rewrite. Status before that commit:

```
 M README.md
 M extensions/rhythm_preserving_audio/RESEARCH_EVIDENCE.md
?? AGENTS.md
?? CLAUDE.md
?? docs/FINAL_ENGINEERING_AUDIT.md
?? weineck/tests/test_committed_results.py
?? weineck/tests/test_pipeline_invariants.py
```

*Note (2026-11-27): the extension's evidence report was later renamed to `extensions/rhythm_preserving_audio/RESEARCH_EVIDENCE.md`; paths in this report use the current name.*

## 9. Changes awaiting approval

Ordered by how much scientific risk each one retires.

| # | Change | Benefit | Risk | Files |
|---|---|---|---|---|
| 1 | Record the reservoir: commit hash and SHA-256 of `experiment_zero.py` as used, in the README and the pre-registration's addenda. Optionally assert the four stated parameters where the reservoir is built | Makes H1, H3 and every reservoir column auditable. Closes D2 | The assertion touches confirmatory scripts. The record alone touches documents only | `README.md`, an addendum, optionally 5 scripts |
| 2 | Recover `noise_shape.npz` and record how it was made. Or fix `noise_shape()` and the file name, regenerate the statistics, and report any change to the map as a dated addendum | Closes D1. Lets the exact-reproduction test run for someone else | Regenerating may move cells at the 1e-10 level or more. That would be a new result, not a repair | `weineck/identifiability_precompute.py`, `docs/IDENTIFIABILITY_PLAN.md` |
| 3 | Make `merge_robustness.py` write its table to a separate generated file, and make `identifiability_merge.py` keep keys it does not own | Removes the two overwrite traps (D3, D4) | Touches two scripts behind committed results. Output values unchanged, which the new tests would confirm | 2 scripts |
| 4 | Replace hardcoded paths with one environment variable each for the repository root, the data directory and the reservoir directory, defaulting to today's values | Lets the code run elsewhere. Closes D6 | Changes provenance of every authoritative script. Defaults keep behaviour identical | 29 files (28 Python, 1 shell script) |
| 5 | Add a `requirements.txt` with the versions in section 6, marked "known to reproduce the merge outputs", and state Python 3.13 | Closes D7 | Claims versions for the merges only, not for the original runs | new file |
| 6 | Choose a licence. Fill in authors. Decide what `CITATION.cff` says about a release that does not exist | Closes D8 and R12 | Yours alone | `LICENSE`, `CITATION.cff` |
| 7 | Correct the measured inaccuracies by dated notes: "1e-14" in `STAGE2_RESULTS.md`, "1e-10" and "bit-identical" in `IDENTIFIABILITY_RESULTS.md`, the "(= stage 2)" row in `UNDERFIT_CHECK.md`, "in progress" in `FRAMING.md`, "aggregate JSON only" in two READMEs, the `make_figures.py` docstring | Documents match the files | Edits results documents | 6 documents, 1 docstring |
| 8 | Report the chosen-lambda distribution, and decide whether to add an extended-grid row as an exploratory addendum (S3) | Answers a question a reviewer may ask | New analysis, needs data | new plan and results |
| 9 | Decide the fate of `\NumNCells` (102 against "94 cells") before the rewrite uses it | Avoids a wrong count in print | Touches `make_figures.py` | 1 script |
| 10 | Commit the generators for the six orphan outputs, or mark those outputs as hand-computed | Closes D5 | Recreated code may not be the code that ran | new scripts or a note |
| 11 | Mark interim and superseded files, in a short index or in the README, without moving them | Closes D13 | None | `README.md` or a new index |
| 12 | Rebuild `main.pdf` from the current `numbers.tex`, or remove the PDF from the tree | Removes a stale artefact | Needs LaTeX | `docs/manuscript/main.pdf` |
| 13 | Add CI that runs the unittest command | Catches D3- and D4-style accidents on push | Needs a manifest first (item 5) | new workflow |
| 14 | Extension: add a dated addendum that records the switch to the two from-scratch editors, and decide whether "pre-planned" and "pre-registered" stay in the evidence report (E1) | The extension's record matches what happened | Edits a plan and a results document | 2 documents |
| 15 | Extension: apply the unapplied frozen rules, above all the "no effective edit" label, or record in a dated addendum why they were not applied (E2) | The headline is read the way the frozen rules require | May change how the headline is worded. Needs the model outputs or the committed rows | `eval_rf.py` or an addendum, the evidence report |
| 16 | Extension: correct "7/8 (p = 0.016)" and the five untraceable numbers, and disclose the rule failure on the untouched source (E3) | Every number traces to a file | Edits a results document | 1 document |
| 17 | Extension: add tests for the timing score, the V1 conditioning path and the evaluation arithmetic (E5) | Closes the gaps the seeded regressions exposed | None | `extensions/.../tests/` |
| 18 | Merge branch `ccr-2b3cc9be-qgn4td`, which holds the changes this audit made, into `main` | Puts the tests and rules on `main` | None beyond review | 7 files |

I did not download data or models, choose a licence, add authors, create a tag, or edit any
pre-registration, results document, results file, `figure_numbers.json`, `numbers.tex` or `main.tex`.

## 10. Remaining technical debt

Ranked by scientific risk, then maintainability, then practical impact.

1. **Reservoir provenance** (D2, S1). Every reservoir claim rests on an unpinned external file.
2. **Identifiability noise bank** (D1, S2). The simulated map cannot be regenerated as documented.
3. **Raw data to per-trial statistics is untested and unreproduced.** The most consequential code in the
   study, about 100 lines in `q2_residual.main`, cannot be exercised without the data. A fixture with a
   synthetic BrainVision file would close this. I did not add one, because it needs a refactor of a
   confirmatory script to be worth it.
4. **Lambda at the grid edge** (S3). A scientific question, not a defect.
5. **Orphan outputs** (D5).
6. **Overwrite traps** (D3, D4). Now documented and partly guarded by a test.
7. **The manuscript that will be submitted is not in the repository.** R5 holds for a skeleton.
8. **Paths and environment** (D6, D7). The largest practical obstacle for anyone else.
9. **Licence and citation metadata** (D8).
10. **Four labelling schemes** (R9). Harmless today, confusing as the document count grows.
11. **Duplication** (section 4). Measured as consistent. Leave it, keep the tests.
12. **Interim files beside results** (D13).
13. **Extension** (E1 to E5). Self-contained. Its record of pre-specification is weaker than its documents
    say, and its tests miss a third of seeded regressions.

## 11. Readiness judgment

**Can independent agents work here reliably? For some work, yes. For the work that matters most, not yet.**

*Ready now, given `AGENTS.md` and the tests:* reading and tracing results, checking a claim against a
results file, regenerating figures and macros in a scratch copy, editing documents under the dated-note
convention, and adding a new exploratory analysis that works from committed outputs. An agent that breaks
a committed result or a pinned invariant will now see a failing test within two seconds.

*Not ready:* anything that must recompute from raw data, anything that involves the reservoir, and
anything that rebuilds the identifiability statistics. Two items are open and I rate both critical for
that class of work: **D1** (noise bank origin) and **D2** (reservoir revision). A third is unverified
rather than broken: the exact-reproduction test has never run outside the original machine.

So I'm not claiming readiness. The honest summary is narrower: the repository's record of what was decided
and when is sound, its summary numbers follow from its stored statistics exactly, and a cold-start agent
can now find the rules, the authoritative code and the frozen material. What it can't yet do is rebuild
those stored statistics, and neither can anyone else without two pieces of information that only the
author holds.
