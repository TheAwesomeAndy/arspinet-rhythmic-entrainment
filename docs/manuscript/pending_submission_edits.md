# Pending manuscript edits for the TNSRE submission pass (2026-11-16)

The 11-page rewrite of `main.tex` is not in this repository yet (origin/main still holds the 6-page skeleton), so
the text edits of the submission pass are staged here, ready to apply. Everything that does not depend on the
rewrite's text is already committed: the macros (`\NumTierBVar`, `\NumTierBVarPct`, `\NumGainLo`, `\NumGainHi`,
`\NumNmedtSongs`, `\NumNmedtDiff`), the Proposition 2 references, FRAMING, the identifiability entry point and its
regression test, CITATION.cff, the cover letter and `new_refs_to_verify.md`. Delete this file once applied.

Every number below is a macro from `numbers.tex`.

## A1. Abstract (replaces the whole abstract)

```latex
Whether beat-locked EEG reflects entrained oscillators or summed evoked responses is often argued from
frequency-tagging magnitudes, which cannot separate the two. We asked whether fronto-central EEG keeps beat-locked
power after a cross-validated linear encoding model, a temporal response function (TRF), is removed.
In a pre-registered two-stage test on \NumNTwo participants listening to music at \NumNTempi tempi (Weineck et
al.\ 2022), the residual kept beat-locked power (\Conf; median standardized effect \NumHTwoDelta,
\NumHTwoPos/\NumNTwo positive). A fixed spiking reservoir (ARSPI-Net, \NumResUnits leaky integrate-and-fire units)
read out linearly was equivalent to the linear statistic (H1, H3; \Conf). A copy with shuffled weights matched it
(\Expl), and it tracked it song by song on a second dataset (NMED-T, \Expl). The residual was not explained by
underfitting (linear-world residual \NumLinWorld; \Expl) and split, under IAAFT surrogates, into a spectral part
(\NumSpectral) and a smaller phase-dependent part (\NumPhase; \Expl). Oscillator-bank encoding models did not beat
the TRF at held-out tempi (\Expl). A simulation map of that comparison (\Simul) showed that the full committed rule,
at its committed regularization pair, has no false positives but reaches \NumPowerPct\% power only when an
oscillator supplies about \NumWA of the stimulus-locked amplitude, about \NumWAVarRhoPct\% of its variance (median
over participants, accounting for the measured correlation). Separately, the comparison against the TRF alone, with
nested regularization, bounds structure a Hopf bank can express beyond the TRF below about \NumTierBPct\% of the
amplitude (about \NumTierBVarRhoPct\% of the variance), a weak exclusion (\Expl). We provide a calibrated identifiability procedure for encoding-model tests of entrainment.
```

The two simulation claims are now separate sentences: 0.89 is the full committed rule with the committed lambda
pair, and 59 % is criterion 1 alone under nested lambda (the largest W80 across worlds). Both variance shares
account for the measured evoked-oscillator correlation (submission pass part 2). 250 words with each macro
counted as one word (limit 250).

## A2. NMED-T (contributions list, Sec. IV-C, Conclusion)

Remove "within ±0.10 on this and a second dataset" wherever it appears. The NMED-T analysis is an exploratory
pilot that predates the pre-registration and has no TOST. Use:

* contributions / Conclusion: `... and it tracked it song by song on a second dataset (NMED-T, \Expl).`
* Sec. IV-C:

```latex
\Expl On a second dataset (NMED-T), in a pilot that predates the pre-registration and has no equivalence test, the
reservoir readout tracked the linear statistic song by song: paired differences in single-listen detection
fraction stayed within $\pm$\NumNmedtDiff over \NumNmedtSongs songs.
```

## B3. Tier (b) bound (Results, Discussion, Fig. 6 caption; FRAMING already done)

Results (replaces the "real data exclude ... oscillatory structure beyond the TRF" sentence):

```latex
\Expl Placement of the real data: criterion~1 itself failed (median $\Delta r$ \NumRealDelta, \NumRealPos/\NumNTwo
positive, $p=\NumRealP$). Taking the largest criterion-1 W80 across worlds under nested regularization as the
bound, the real data exclude, at about \NumPowerPct\% power, structure a Hopf bank can express beyond the TRF
supplying more than about \NumTierBPct\% of the stimulus-locked amplitude, that is about \NumTierBVarRhoPct\% of its
variance (median over participants, range \NumTierBVarRhoLoPct--\NumTierBVarRhoHiPct\%, accounting for the measured
correlation $\rho$ between the evoked and Hopf-bank predictions, median \NumRhoMed, range \NumRhoMin--\NumRhoMax;
\NumTierBVarPct\% if the two were uncorrelated). Criterion~1 compares the Hopf-augmented model with the TRF only, so it cannot separate a Hopf bank from a
linear oscillator bank: this bounds what a Hopf bank can express, not Hopf-specific structure. It is a weak
exclusion.
```

Discussion and Fig. 6 caption: replace "oscillatory structure beyond the TRF" with "structure a Hopf bank can
express beyond the TRF", and add "(about \NumTierBVarRhoPct\% of the variance, median over participants, accounting
for the measured correlation; a weak exclusion)" after the bound. Wherever the 0.89 headline is given a variance
share, use "about \NumWAVarRhoPct\% of its variance (median over participants, accounting for the measured
correlation)" in place of \NumWAVar\%.

Variance share (submission pass part 2): share = $w^2/(w^2+(1-w)^2+2w(1-w)\rho)$ for unit-sd evoked and oscillator
components with correlation $\rho$, measured per participant over the simulation pool
(`identifiability_procedure.py --rho-report`, `results/identifiability/component_correlation.json`). Median
$|\rho|$ = \NumRhoMed > 0.1, so the correlated form is used. The uncorrelated values (\NumWAVar\%,
\NumTierBVarPct\%) overstate the oscillator's own share of the variance.

## B4. Limitations (one sentence)

```latex
The real augmented-minus-TRF $\Delta r$ (\NumRealDelta) is more negative than in the simulated evoked-only world
(\NumEvokedOnly), so the simulation may penalize the augmented model less than real EEG does, the W80 values may be
optimistic, and the bound is not guaranteed to be conservative.
```

## C5. Proposition 1 (replaces "Proposition 1 predicts ...")

```latex
The reservoir's measured beat-band transfer was flat (gain \NumGainLo--\NumGainHi, zero delay), so by
Proposition~1 its linear component leaves $\delta$ unchanged, consistent with the observed equivalence.
```

## C6. Proposition 2 (framing, after its statement)

```latex
Proposition~2 formalizes a known point: a steady-state response to a periodic input can be written as a
superposition of transient responses to the individual events
\cite{galambos1981forty,bohorquez2008generation,capilla2011steady}. The transient $h_T$ in that representation may
depend on the period $T$, so a steady-state magnitude at one tempo cannot separate the two accounts, and prediction
at held-out tempi is the remaining test.
```

All three references were checked against their Crossref records (DOIs 10.1073/pnas.78.4.2643,
10.1016/j.clinph.2008.08.002, 10.1371/journal.pone.0014543) and are in `references.bib`.

## D7. Methods paragraph "Using the identifiability procedure"

```latex
\subsubsection*{Using the identifiability procedure}
The simulation is released as a documented entry point (\texttt{identifiability\_procedure.py}). Its inputs are
the participants' fitted kernels (an evoked TRF kernel and a Hopf-bank kernel), the stimulus features as
sufficient statistics of the model designs, a target held-out $r$, the trials per tempo, the number of training
tempi, a grid of oscillator amplitude shares $w$ and the number of simulated datasets. For each cell it returns the
detection rate of the full rule and of criterion~1 alone with \NumCiPct\% Clopper--Pearson intervals, the
false-positive rate at $w=0$, and W80 with its bracketing grid points and variance share. A regression test
reproduces a committed cell exactly from its stored seed.
```

## E8. Ethics (Data section)

Weineck et al. (2022), Methods, Participants, verbatim: "The study was approved by the Ethics Council of the Max
Planck Society Ethics Council in compliance with the Declaration of Helsinki (Application No: 2019_04)." and "All
participants signed the informed consent before starting the experiment." (PubMed record PMID 36094165, full text
PMC9467512, doi:10.7554/eLife.75515.)

```latex
The original study was approved by the Ethics Council of the Max Planck Society (Application No.\ 2019\_04) in
compliance with the Declaration of Helsinki, and all participants gave written informed consent
\cite{weineck2022neural}.
```

("written" is not in their text; drop it if you want the sentence to stay strictly within what they state.)

## E9. Draft markers

Replace the `\thanks` text with:

```latex
\thanks{Manuscript received XXXX XX, 2026.% TODO: submission date
 This work was supported in part by XXXX.% TODO: funding
}
```

The visible text then follows the IEEE template's "XXXX" placeholder style, and the TODOs sit in LaTeX comments, so
none is visible in the PDF. Remove "(draft)" from `\markboth`. Leave the affiliation, email and acknowledgments
as they are. The full list of removed markers is in the pass summary once applied to the rewrite.

## E10. Code availability

```latex
Code, aggregate results, the pre-registration and every analysis plan:
\url{https://github.com/TheAwesomeAndy/arspinet-rhythmic-entrainment}, release \texttt{v1.0-tnsre-submission},
archived at Zenodo, doi:10.5281/zenodo.XXXXXXX. Every number in this manuscript is generated from the results files
by \texttt{make\_numbers.py}.
```
