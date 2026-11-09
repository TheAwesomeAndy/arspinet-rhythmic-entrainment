# Framing: the question is the contribution

Working title (v1):
**What can scalp EEG tell us about neural entrainment to music? A pre-registered,
instrument-calibrated test of beat-locking beyond a linear encoding model**

Shorter alternative: *The limits of beat-locking: what a calibrated spiking reservoir does
and does not reveal about entrainment in naturalistic-music EEG*

## The core question

When the brain "locks" to a musical beat, the field disagrees about whether that reflects an
internal oscillator being captured or evoked responses stacking up (Nozaradan 2011; Novembre
& Iannetti 2018; Doelling 2019; Doelling & Assaneo 2021; Damsma 2025). We ask a narrower,
answerable question underneath it: **which classes of measurement on single-listen scalp
EEG can, in principle, carry information about that distinction, and does an interpretable
nonlinear instrument add anything to them?** The answer is informative whichever way the
pre-registered test (Q2, H2) comes out.

## What is already established (evidence labels: measured here / literature)

1. **A class-level limit, demonstrated rather than asserted** (measured, synthetic +
   real). Every stimulus-locked *magnitude* statistic we calibrated, linear tagging,
   envelope and squared statistics, and a fixed spiking reservoir read out linearly across
   its units, detects an evoked-kernel drive and a forced oscillator with identical
   sensitivity at every SNR and tempo. On ten real songs and nine participants' trials the
   reservoir reproduces the linear detector song by song. This is a statement about the
   measurement class, not about the brain: these statistics are blind to the oscillator vs
   evoked distinction by construction, and that is exactly why frequency tagging and
   tempo-selective enhancement produced a decade of unresolved debate (consistent with
   Damsma 2025 and Doelling & Assaneo 2021, here shown with a calibrated instrument). The
   positive content is the design implication: only phase-sensitive, model-comparison, or
   perturbation designs (missing pulses, tempo changes, offset persistence with ringing
   controls) can carry the distinction.
2. **A failure of the obvious null models, measured** (measured, real data). Circular shift
   and phase randomisation leave beat-locking magnitudes unchanged on a periodic grid;
   neighbour-debiased scores and pseudo-tempo permutations inflate false positives (0.08-0.36)
   for identifiable reasons (spectral bias; non-exchangeable labels). The stimulus-label
   shuffle holds the nominal rate (0.01-0.04). Writing the rejected nulls down is itself
   useful to a literature that mostly uses the first two.
3. **What single-listen data can see** (measured). Beat tagging is detectable in 20-90 % of
   single listens on NMED-T, song-dependent, mostly at metrical subdivisions; a residual beat
   component of 4 % amplitude (0.16 % of variance) is detectable with nine participants, 2-3 %
   needs the full cohort. Published for the first time for NMED-T.
4. **The instrument, characterised** (measured). Gain 1.42-1.44 flat over 1-4 Hz, zero
   group delay, firing rate 0.126-0.128, weight-shuffled control indistinguishable: the
   canonical reservoir's linear readout is a scaled copy of its drive in the beat band.
   "Fixed weights" becomes a calibration statement rather than a limitation.

## What stage 1 / stage 2 add, either way

* **H2 supported** (residual carries beat-locked structure beyond a four-feature TRF): the
  paper reports a measured nonlinearity (or TRF misfit) in beat-locked EEG, with the
  reservoir's unit-level readout showing *where* in its state space it appears, and the
  trivial-nonlinear baselines (N2a, N2b) saying whether a reservoir was needed to see it.
* **H2 not supported**: the paper reports that, at the power available, a maximal linear
  model accounts for the beat-locked structure a fixed nonlinear instrument can detect,
  with the inconclusive region stated in amplitude units. That bounds what any future
  nonlinear-readout claim on such data must exceed.
Both are refutable, both are pre-registered, neither needs a "winner".

## Interpretability as the lens (planned, not yet run)

Per-unit analyses are cheap and were pre-registered as secondary: which units carry the
beat (input-weight sign and magnitude, recurrent in-degree), at which harmonics, and whether
the carrying set is stable across tempi and seeds. Honest scope: all units share one leak
(beta = 0.05), so "timescales" means effective integration set by recurrent weights, not a
distribution of membrane constants. This is a modest but concrete account of what rhythm
tracking requires of a fixed neural transform.

## The bridge to the larger question (discussion, flagged as perspective)

Entrainment is the field's working model for how music takes hold of a listener. If what
scalp EEG measures at these tempi is dominated by stimulus-driven superposition, then the
mechanism of being moved by rhythm must be sought elsewhere: prediction and timing
expectation, motor simulation, absorption. That reframing is a legitimate discussion point
and a bridge to the author's longer-term interest in rhythmic practice and absorptive
states; it is not a result of this study and is written as such.

## Where this is publishable

* Methods / limits framing: *Journal of Neural Engineering*, *NeuroImage*, *eNeuro*, *PLoS
  Computational Biology* (the calibration + rejected-nulls + pre-registration package fits
  all four; eNeuro and PLoS CB reward negative-but-informative results explicitly).
* Instrument framing: *IEEE Transactions on Neural Systems and Rehabilitation Engineering*,
  *IEEE EMBC* (the reservoir as a characterised measurement operator).
* Perspective companion (short): *Neuroscience of Consciousness*, *Music Perception*, or
  a *Frontiers in Human Neuroscience* opinion piece for the bridge section alone.

## Monday's research step

1. Read stage-1 output against the frozen rules (`docs/PREREGISTRATION_DRAFT.md`, commit
   `935c80a`); stage 2 download proceeds unless H2 is already supported.
2. Run the per-unit interpretability analysis on the tempo-curve output (secondary,
   pre-registered).
3. Draft the paper in Wall order starting from figures: (i) calibration curves and the
   evoked-vs-oscillator indistinguishability panel; (ii) rejected nulls; (iii) NMED-T
   single-listen table; (iv) Weineck tempo curve, drive vs reservoir; (v) Q2 residual
   result with its inconclusive region.
4. Write the limit statement with the design implication as the first sentence of the
   discussion.
