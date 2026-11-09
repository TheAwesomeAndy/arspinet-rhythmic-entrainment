# Synthetic calibration of beat-locking detectors (2026-11-09)

`synthetic_calibration.py --n-rep 8 --tempi 1.0,1.5,2.0,2.5,3.0,4.0 --snrs 0.05,0.1,0.2,0.4`
(full log: `results/synthetic_calibration_full.log`; data: `results/synthetic_calibration_full.json`).
60 s drives at 256 Hz, pink-noise background, SNR = amplitude ratio signal/noise; three
drive types: beat-locked sinusoid (+0.3 x 2f harmonic), evoked kernel (biphasic, 100 ms
latency) convolved with a beat impulse train, and a forced Stuart-Landau oscillator
(natural frequency 1.08 x beat, coupling 0.8). Detectors share the neighbour-frequency null
(Welch, 20 s Hann segments): L = linear tagging of the drive; N2a = tagging of the Hilbert
envelope of the 0.5-8 Hz drive; N2b = tagging of the squared drive; R_pc1 = unit-PC1 of the
canonical LIF reservoir (experiment_zero, seed 42); R_pop = reservoir population rate;
Rs_pc1 = unit-PC1 of the same reservoir with shuffled recurrent weights (same spectral
radius). Detection = max z over k in {1, 2} > 1.96; probability over 8 repetitions.

## Detection probability, averaged over the six tempi

| drive | SNR | L | N2a | N2b | R_pc1 | R_pop | Rs_pc1 |
|---|---|---|---|---|---|---|---|
| sine | 0.05 | 0.29 | 0.15 | 0.17 | 0.29 | 0.13 | 0.31 |
| sine | 0.10 | 0.79 | 0.08 | 0.25 | 0.83 | 0.27 | 0.81 |
| sine | 0.20 | 1.00 | 0.27 | 0.67 | 1.00 | 0.67 | 1.00 |
| sine | 0.40 | 1.00 | 0.90 | 0.90 | 1.00 | 0.94 | 1.00 |
| evoked | 0.05 | 0.44 | 0.10 | 0.06 | 0.40 | 0.08 | 0.42 |
| evoked | 0.10 | 0.90 | 0.06 | 0.27 | 0.90 | 0.25 | 0.90 |
| evoked | 0.20 | 1.00 | 0.40 | 0.56 | 1.00 | 0.59 | 1.00 |
| evoked | 0.40 | 1.00 | 0.79 | 1.00 | 1.00 | 0.85 | 1.00 |
| osc | 0.05 | 0.52 | 0.15 | 0.15 | 0.54 | 0.12 | 0.50 |
| osc | 0.10 | 0.90 | 0.15 | 0.35 | 0.86 | 0.35 | 0.90 |
| osc | 0.20 | 1.00 | 0.15 | 0.56 | 1.00 | 0.65 | 1.00 |
| osc | 0.40 | 1.00 | 0.23 | 0.98 | 1.00 | 1.00 | 1.00 |

(Per-tempo cells are in the log; the largest per-cell |R_pc1 - L| is 0.12, i.e. one
repetition of eight.)

## Reservoir transfer characteristics ('sine' drive, SNR 3.0)

| beat f (Hz) | gain unit-PC1 / drive | phase difference | firing rate |
|---|---|---|---|
| 1.0 | 1.441 | half a period (-492 ms) | 0.128 |
| 1.5 | 1.440 | half a period (-327 ms) | 0.128 |
| 2.0 | 1.432 | half a period (-244 ms) | 0.128 |
| 2.5 | 1.433 | half a period (-194 ms) | 0.128 |
| 3.0 | 1.426 | half a period (-161 ms) | 0.128 |
| 4.0 | 1.421 | half a period (-120 ms) | 0.128 |

The phase difference is exactly pi at every tempo, which is the arbitrary sign of PC1, so
the measured group delay of the linear reservoir readout is zero to within this test's
resolution and its gain is flat over 1-4 Hz.

## Readings

1. Read out linearly across units (unit-PC1), the canonical reservoir reproduces the
   linear detector's sensitivity on every drive type and SNR; it adds no detection power
   and loses none. The weight-shuffled control is indistinguishable from it, so the
   specific recurrent wiring plays no role in this readout.
2. The population mean rate is a poor readout (units lock at different phases and cancel),
   as on the real NMED-T data.
3. No detector, linear or nonlinear, separates the evoked-kernel drive from the forced
   oscillator at any SNR: beat-locking magnitude statistics are blind to that distinction,
   consistent with Damsma et al. 2025 and Doelling & Assaneo 2021.
4. The trivial nonlinear statistics (envelope, square) are weaker than L on these drives;
   on real residuals they remain the honest baseline the reservoir must beat for Q2.

Not tested here: residual-based statistics (N1), seeds 7/99, rho sweep, IAAFT surrogates.
