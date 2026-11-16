[Date]

The Editor-in-Chief
IEEE Transactions on Neural Systems and Rehabilitation Engineering

Dear Editor,

We submit "What a Linear Encoding Model Leaves at the Beat: A Pre-Registered Test of Residual Beat-Locking, a Spiking-Reservoir Readout, and the Identifiability Limits of Oscillator-versus-Evoked Comparisons in Single-Listen EEG" for consideration as a regular paper.

Rhythm-based rehabilitation often rests on the assumption that the brain entrains to an external beat. Whether scalp EEG can show this, rather than a stimulus-driven linear response, is usually argued from frequency-tagging magnitudes, which cannot separate the two. We present a method that tests whether beat-locked EEG exceeds what a cross-validated linear encoding model (a temporal response function) predicts, with validated nulls and with explicit identifiability bounds on how large an oscillator contribution an encoding-model comparison could detect. We apply it to the open EEG of Weineck, Wen and Henry (eLife 2022; 34 participants, music at 13 tempi).

The test was pre-registered, with the design, hypotheses, statistic, null and equivalence bounds frozen at commit 935c80a of the project repository before any group test. At stage 2, the residual of the linear model kept beat-locked power (median standardized effect 0.228, 31 of 34 participants positive, one-sided Wilcoxon p < 1e-4). Envelope and squared-signal statistics on the residual were null, so what survives is phase-coherent power at the beat and its octave. A fixed spiking reservoir read out linearly was equivalent to the linear statistic (TOST within plus or minus 0.10), and a reservoir with shuffled recurrent weights matched it. We report these as measured limits, and we state that underfitting of a stimulus-locked response at single-listen signal-to-noise ratio is the parsimonious reading. The null models were validated before use, and the nulls we rejected are recorded with their measured false-positive rates.

Every analysis beyond the pre-registration is labelled exploratory or simulated, and each had its plan and decision rule committed before it ran. The simulation map is the methodological contribution. It states, at the operating point of these data, what an oscillator-versus-linear-model comparison can and cannot decide and how strongly its answer depends on the regularization of the comparison models. A pilot on a second, naturalistic dataset (NMED-T) predates the pre-registration and is reported as exploratory only.

The manuscript is original, is not under consideration elsewhere, and uses only openly available, de-identified data collected under the original study's ethics approval. Code, aggregate results, the pre-registration and every analysis plan are in the project repository, and every number in the manuscript is generated from the results files.

Sincerely,

[Corresponding author, affiliation and contact details to be added]
