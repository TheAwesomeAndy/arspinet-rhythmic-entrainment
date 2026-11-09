# Weineck, Wen & Henry (2022) data notes

Source: OSF project y5xhs, "Neural synchronization is strongest to the spectral flux of
slow music and depends on familiarity and beat salience" (eLife 2022). Licence: CC BY 4.0
(stated in `ReadMe.pdf`; the OSF node itself carries no licence field). Contents verified
2026-11-09: 420 files, 14.1 GB; `rawEEGdata_examples/` holds 135 BrainVision blocks
(34 participants x 4 blocks, participant 1 has 3) = 13.9 GB; `SourceData/` 0.2 GB;
`SourceCode/` Matlab figure scripts and the stimulation script.

Raw data are kept in `/home/user/data_local/weineck2022/` and never committed.

## Facts established from the files (not from the paper)

| Item | Value | Source |
|---|---|---|
| EEG | 32 actiCap + 1 aux channel `33`, 1000 Hz, BrainVision | `.vhdr` |
| Markers | S40 start (doubled, 10 ms apart), S80 end of music segment, S120/S180 the 5.5 s repetition for tapping; 80->120 = 0.99 s | `.vmrk`, `SourceCode_stimulation.m` |
| Trials | ~160 per participant, 40 per block, listening 8.3-56.5 s | markers |
| Stimulus features | `Figure1_SourceData1.mat`: `stim_env_z`, `stim_der_z`, `stim_beat_z`, `stim_spec_z`; 13 tempi (1-4 Hz, 0.25 steps) x 4 stimulation subgroups; 642 trial vectors | file |
| Feature sampling rate | **128 Hz** | `Figure1_SourceCode.m` line 18 |
| Feature span | **listening window minus 1.0 s, trimmed from the start** (features begin 1 s after S40) | fitted: 81-83 % of trials within 20 ms once the 1 s offset is applied (21 % without); held-out TRF prediction r 0.04 at FC2/Cz for the start-trim vs 0.015 at scattered channels for the end-trim |
| Presentation order | not released | - |
| Subgroup per participant | recoverable two ways: duration-multiset fit, and the per-tempo non-NaN trial counts in `Figure3_SourceData1.mat` `TRFcorr` (34 columns in sorted subject order; L1 distance <= 7 to the right subgroup, >= 8 to the others) | files |
| Original tempi | 72 segments, 0.93-2.52 Hz original, each presented at a range of stretched tempi | `original_music` |

Participant columns map to subject IDs sorted numerically: `['1','2','3','4','7','8','9','10','11','12','13','14','16','17','18','19','20','21','22','23','24','25','26','27','28','29','30','31','32','33','34','35','36','37']`.
Subgroup assignment by column: `[0,1,2,3,2,3,0,1,2,3,0,1,3,0,1,2,3,0,1,2,3,0,1,2,3,0,1,2,3,0,1,2,3,0]`.

## Trial -> feature mapping (`weineck_loader.py`)

Duration-based: expected feature length = (S80 - S40) - 1.0 s; a trial is assigned the
unique feature vector of its subgroup within +-20 ms. Results for the two participants
downloaded first:

| participant | subgroup | trials | unique match | ambiguous, same tempo | ambiguous, mixed tempo | no candidate within 20 ms |
|---|---|---|---|---|---|---|
| subj10 | 1 | 160 | 81 | 4 | 45 | 30 |
| subj11 | 2 | 159 | 98 | 5 | 29 | 27 |

Each stimulus is presented once per participant, so matching must be one-to-one: 6 (subj10)
and 4 (subj11) "unique" trials in fact shared a stimulus with another trial and are dropped,
leaving **75/160 and 94/159 one-to-one trials** with a known stimulus. Note that the
published `TRFcorr` counts are the authors' analysed trials after exclusions (e.g. 6 at
tempo 1 where 7 were presented); consistency checks must use the presented set (the
subgroup's feature counts).

### Resolving the ambiguous trials: two methods tested, both fail (`resolve_trials.py`, `tempo_tiebreak_selftest.py`)

| method | self-test (leave-one-out on one-to-one trials) | subj10 | subj11 |
|---|---|---|---|
| forward-TRF prediction score, candidates within 50 ms (2.3 on average) | accuracy vs chance | 0.52 vs 0.45 | 0.60 vs 0.45 |
| same, candidates within 300 ms (5.2 on average) | accuracy vs chance | 0.37 vs 0.24 | 0.38 vs 0.23 |
| tempo tagging of the trial's own EEG (3.5 candidate tempi) | accuracy vs chance | 0.43 vs 0.32 | 0.35 vs 0.32 |

No score margin reaches 0.9 precision, so no resolved trial is accepted. Single-trial
stimulus-EEG coupling (r ~ 0.04) and single-trial tagging on 32 channels are too weak to
identify the stimulus or even its tempo. Consequence: Q2 analyses use the one-to-one trials
only (~50-60 % of trials); tempo-level analyses may add the ambiguous trials whose
candidates all share a tempo (4-5 per participant). The Hungarian assignment of the
remainder reproduces the presented set exactly, which is a tautology, not a validation.

## Validation numbers (`align_scan.py`, `trf_align_check.py`)

Spectral flux cross-correlation (0.5-8 Hz EEG, fronto-central mean) under start-trim:
peak z +5.1 at 70 ms, +4.2 at 200 ms; beat onsets -4.1 at 100 ms, +2.0/+2.3 at 150/200 ms
(N1/P2-like). Leave-one-trial-out ridge mTRF (lags 0-400 ms, flux + onsets + envelope):
mean r over channels +0.020 (subj10) / +0.021 (subj11), best channel FC2 r = 0.043 /
0.043 with 70 % of trials positive; end-trim alternative 0.003-0.006 / 0.001.

## Files

`weineck_loader.py` (features, markers, matching, loading at 256 Hz), `mtrf.py` (ridge
TRF, LOO), `align_scan.py`, `trf_align_check.py`, `verify_mapping.py` (superseded by the
two above), `results/` (aggregate JSON only).
