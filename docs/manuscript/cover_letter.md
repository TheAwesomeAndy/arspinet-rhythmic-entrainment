[Date]

The Editor-in-Chief
IEEE Transactions on Neural Systems and Rehabilitation Engineering

Dear Editor,

We submit "Beat-Locked EEG Measures Stimulus-Locked Processing: Calibrated Bounds on Detecting Neural Entrainment" for consideration as a regular paper.

Rhythm-based rehabilitation often rests on the assumption that the brain entrains to an external beat. Whether scalp EEG can show this, rather than a stimulus-driven linear response, is usually argued from frequency-tagging magnitudes, which cannot separate the two. We present a method that tests whether beat-locked EEG exceeds what a cross-validated linear encoding model (a temporal response function) predicts, with validated nulls and with explicit identifiability bounds on how large an oscillator contribution an encoding-model comparison could detect. We apply it to the open EEG of Weineck, Wen and Henry (eLife 2022; 34 participants, music at 13 tempi).

The test was pre-registered, with the design, hypotheses, statistic, null and equivalence bounds frozen at commit 935c80a of the project repository before any group test. At stage 2, the residual of the linear model kept beat-locked power (median standardized effect 0.228, 31 of 34 participants positive, one-sided Wilcoxon p < 1e-4). Envelope and squared-signal statistics on the residual were null. In an exploratory surrogate analysis (IAAFT), most of the residual effect was spectral, retained by surrogates that keep the amplitude spectrum (0.156), and a smaller part depended on phase (0.045). A fixed spiking reservoir read out linearly was equivalent to the linear statistic (TOST within plus or minus 0.10), and a reservoir with shuffled recurrent weights matched it. The reservoir is the ARSPI-Net leaky integrate-and-fire reservoir from our LISAT 2024 paper (doi:10.1109/LISAT63094.2024.10808138), where it served as a feature extractor for classifying the valence of affective EEG. What is new here is its use as a characterized measurement instrument inside a pre-registered test, against a linear statistic and a weight-shuffled control, rather than as a classifier. The residual was not explained by underfitting of a linear model: in an exploratory linear-world simulation, the residual effect was 0.039, against 0.228 in the real data. The null models were validated before use, and the nulls we rejected are recorded with their measured false-positive rates.

Every analysis beyond the pre-registration is labelled exploratory or simulated, and each had its plan and decision rule committed before it ran. The simulation map is the methodological contribution. It states, at the operating point of these data, what an oscillator-versus-linear-model comparison can and cannot decide and how strongly its answer depends on the regularization of the comparison models. A pilot on a second, naturalistic dataset (NMED-T) predates the pre-registration and is reported as exploratory only.

The manuscript is original, is not under consideration elsewhere, and uses only openly available, de-identified data collected under the original study's ethics approval. Code, aggregate results, the pre-registration and every analysis plan are in the project repository, and every number in the manuscript is generated from the results files.

Sincerely,

[Corresponding author, affiliation and contact details to be added]
