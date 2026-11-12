#!/usr/bin/env python3
"""Generate numbers.tex (LaTeX macros) from docs/figures/tnsre/figure_numbers.json. Every number in main.tex is one of
these macros; nothing is typed by hand. A missing path is an error. Regenerate after weineck/figures/make_figures.py."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); N = json.load(open(os.path.join(HERE, '..', 'figures', 'tnsre', 'figure_numbers.json')))


def get(path):
    x = N
    for k in path.split('/'):
        x = x[int(k)] if isinstance(x, list) else x[k]
    return x


def f(fmt):
    return {'2': lambda v: f'{v:.2f}', '3': lambda v: f'{v:.3f}', '4': lambda v: f'{v:.4f}', 's3': lambda v: f'{v:+.3f}'.replace('-', '$-$'), 's4': lambda v: f'{v:+.4f}'.replace('-', '$-$'),
            'pct': lambda v: f'{100 * v:.0f}', 'int': lambda v: f'{int(round(v))}', 'g': lambda v: f'{v:g}', 'p': lambda v: (f'{v:.2f}' if v >= 0.01 else (f'{v:.4f}' if v >= 1e-4 else '{:.1e}'.format(v).replace('e-0', r'\times10^{-').replace('e-', r'\times10^{-') + '}')),
            'of34': lambda v: f'{int(round(v * 34))}', 'of8': lambda v: f'{int(round(v * 8))}', 'str': lambda v: str(v)}[fmt]


M = [  # (macro, json path, format)
    # provenance
    *[(f'Commit{k[0].upper()}{k[1:]}', f'ms/provenance/{k}', 'str') for k in N['ms']['provenance']],
    # design
    ('AlphaOne', 'ms/design/alpha_stage1', '2'), ('AlphaTwo', 'ms/design/alpha_stage2', '2'), ('TostBound', 'ms/design/tost_bound', '2'), ('NShuffles', 'ms/design/n_shuffles', 'int'),
    ('MinTrials', 'ms/design/min_trials', 'int'), ('TrfLagMax', 'ms/design/trf_lag_ms/1', 'int'), ('FsTrf', 'ms/design/fs_trf_hz', 'int'), ('FsRes', 'ms/design/fs_reservoir_hz', 'int'),
    ('NFc', 'ms/design/n_fc_channels', 'int'), ('BandLo', 'ms/design/eeg_band_hz/0', 'g'), ('BandHi', 'ms/design/eeg_band_hz/1', 'g'), ('ResSeed', 'ms/design/seed', 'int'),
    ('ResRho', 'ms/design/rho', 'g'), ('ResBeta', 'ms/design/beta', 'g'), ('ResUnits', 'ms/design/n_units', 'int'), ('NEeg', 'ms/design/n_eeg_channels', 'int'),
    ('CritOneAlpha', 'ms/design/crit1_alpha', '2'), ('CritTwoAlpha', 'ms/design/crit2_alpha', '2'), ('PowerPct', 'ms/design/power_threshold', 'pct'), ('CiPct', 'ms/design/ci_level', 'pct'),
    ('TostCiPct', 'ms/design/tost_ci_level', 'pct'), ('LamSmall', 'ms/design/lam_small', 'int'), ('LamLarge', 'ms/design/lam_large', 'int'), ('LongTrf', 'ms/design/long_trf_ms', 'int'),
    ('RhoZero', 'ms/design/rho_zero', 'int'), ('TempoRise', 'ms/design/tempo_rise_hz', 'int'),
    ('SnrFactor', 'ms/ident/snr_factor', 'int'), ('TrialsFactor', 'ms/ident/trials_factor', 'int'), ('NestedDatasets', 'ms/ident/nested_datasets', 'int'), ('LampairDatasets', 'ms/ident/lampair_datasets', 'int'),
    # data
    ('NTwo', 'ms/data/n_stage2', 'int'), ('NOne', 'ms/data/n_stage1', 'int'), ('NTrials', 'ms/data/n_trials_stage2', 'int'), ('NTempi', 'ms/data/n_tempi', 'int'),
    ('TempoMin', 'ms/data/tempo_min_hz', 'g'), ('TempoMax', 'ms/data/tempo_max_hz', 'g'),
    # stage 1 and 2
    ('StageOneDelta', 'ms/stage1/median_delta', '3'), ('StageOnePos', 'ms/stage1/frac_positive', 'of8'), ('StageOneP', 'ms/stage1/p', '3'),
    ('HTwoDelta', 'fig2/resid_median_delta', '3'), ('HTwoLo', 'fig2/resid_median_ci95_boot/0', '3'), ('HTwoHi', 'fig2/resid_median_ci95_boot/1', '3'), ('HTwoPos', 'fig2/resid_positive', 'int'), ('HTwoP', 'fig2/p_H2', 'p'),
    ('DriveDelta', 'fig2/drive_median_delta', '3'), ('DriveLo', 'fig2/drive_median_ci95_boot/0', '3'), ('DriveHi', 'fig2/drive_median_ci95_boot/1', '3'),
    ('HOneLo', 'fig2/tost_90ci/H1: drive, R - L/0', 's3'), ('HOneHi', 'fig2/tost_90ci/H1: drive, R - L/1', 's3'),
    ('HThreeLo', 'fig2/tost_90ci/H3: residual, R - N0/0', 's3'), ('HThreeHi', 'fig2/tost_90ci/H3: residual, R - N0/1', 's3'),
    ('EnvLo', 'fig2/tost_90ci/residual, R - envelope (N2a)/0', '3'), ('EnvHi', 'fig2/tost_90ci/residual, R - envelope (N2a)/1', '3'),
    # underfitting and IAAFT
    ('LinWorld', 'fig3/real_vs_linear_world/median_linear_world', '3'), ('LinWorldP', 'fig3/real_vs_linear_world/p_real_gt_linear_world', 'p'),
    ('PooledDelta', 'ms/underfit/resid_pooled/median_delta', '3'), ('PredDelta', 'ms/underfit/pred/median_delta', '3'), ('UDriveDelta', 'ms/underfit/drive/median_delta', '3'),
    ('Spectral', 'fig3/iaaft/spectral_median', '3'), ('SpectralLo', 'fig3/iaaft/spectral_ci95_boot/0', '3'), ('SpectralHi', 'fig3/iaaft/spectral_ci95_boot/1', '3'),
    ('Phase', 'fig3/iaaft/phase_median', '3'), ('PhaseLo', 'fig3/iaaft/phase_ci95/0', '3'), ('PhaseHi', 'fig3/iaaft/phase_ci95/1', '3'), ('PhasePos', 'fig3/iaaft/phase_positive', 'int'), ('PhaseP', 'fig3/iaaft/p', 'p'),
    # reservoir
    ('RRs', 'fig4/R_minus_Rs/baseline/median', 's4'), ('RRsLo', 'fig4/R_minus_Rs/baseline/ci95_boot/0', 's3'), ('RRsHi', 'fig4/R_minus_Rs/baseline/ci95_boot/1', 's3'),
    ('RRhoZero', 'fig4/R_minus_R_rho0/baseline/median', 's4'), ('RRhoZeroLo', 'fig4/R_minus_R_rho0/baseline/ci95_boot/0', 's3'), ('RRhoZeroHi', 'fig4/R_minus_R_rho0/baseline/ci95_boot/1', 's3'),
    ('RhoCorr', 'fig4/baseline_vs_rho0_corr', '3'), ('NRows', 'ms/robustness/n_rows', 'int'), ('NFlips', 'ms/robustness/n_flips', 'int'),
    # theory 3 and tempo curve
    ('TThreeDelta', 'fig5/delta_r_aug_median', 's3'), ('TThreePos', 'fig5/delta_r_aug_positive', 'int'), ('TThreeP', 'fig5/p_aug', '2'),
    ('TThreeLinDelta', 'ms/theory3/delta_r_aug_lin_median', 's3'), ('TThreeAugVsLinP', 'ms/theory3/p_aug_vs_lin', '2'), ('TThreeNegTempi', 'ms/theory3/n_tempi_negative', 'int'),
    ('RShort', 'fig5/median_r_from_merged/d_short', '3'), ('RLong', 'fig5/median_r_from_merged/d_long', '3'), ('RHopf', 'fig5/median_r_from_merged/hopf', '3'), ('RLin', 'fig5/median_r_from_merged/lin', '3'),
    ('RRf', 'fig5/median_r_from_merged/rf', '3'), ('RAug', 'fig5/median_r_from_merged/aug', '3'), ('RAugLin', 'fig5/median_r_from_merged/aug_lin', '3'),
    ('GroupDelta', 'ms/theory3_group/delta_r_median', 's3'), ('GroupPos', 'ms/theory3_group/frac_positive', 'of34'), ('GroupP', 'ms/theory3_group/p', '2'),
    ('SlopeLFull', 'fig5/cycle_slopes/L_full/median_slope_z_per_Hz', 's3'), ('SlopeLFullP', 'fig5/cycle_slopes/L_full/wilcoxon_greater_p', 'p'),
    ('SlopeLFixed', 'fig5/cycle_slopes/L_fixed_cycles/median_slope_z_per_Hz', 's3'), ('SlopeLFixedP', 'fig5/cycle_slopes/L_fixed_cycles/wilcoxon_greater_p', '2'),
    ('SlopeRFull', 'fig5/cycle_slopes/R_pc1_full/median_slope_z_per_Hz', 's3'), ('SlopeRFullP', 'fig5/cycle_slopes/R_pc1_full/wilcoxon_greater_p', 'p'),
    ('SlopeRFixed', 'fig5/cycle_slopes/R_pc1_fixed_cycles/median_slope_z_per_Hz', 's3'), ('SlopeRFixedP', 'fig5/cycle_slopes/R_pc1_fixed_cycles/wilcoxon_greater_p', '2'),
    # identifiability
    ('OpR', 'ms/ident/op_r', 'g'), ('OpTrials', 'ms/ident/op_trials', 'int'), ('OpTempi', 'ms/ident/op_tempi', 'int'), ('CalR', 'ms/ident/calibrated_r', '3'),
    ('NCells', 'ms/ident/n_grid_cells', 'int'), ('NDatasets', 'ms/ident/datasets_per_cell', 'int'), ('NSimPart', 'ms/ident/participants_per_dataset', 'int'), ('NKernels', 'ms/ident/n_kernels', 'int'),
    ('WA', 'ms/ident/W80_A', '2'), ('WAVar', 'ms/ident/W80_A_variance', 'pct'), ('WB', 'ms/ident/W80_B', '2'), ('WNested', 'ms/ident/W80_nested', '2'),
    ('WRefOne', 'ms/ident/W80_refined_r008', '2'), ('WRefTwo', 'ms/ident/W80_refined_n160', '2'), ('CMax', 'ms/ident/C_max_rate', '2'), ('FpMax', 'ms/ident/fp_max', '2'), ('FpHi', 'ms/ident/fp_ci_hi_20', '2'),
    ('Overlap', 'ms/ident/overlap_median', '2'), ('RTwoShort', 'ms/ident/R2_short_median', 'pct'), ('RTwoShortMin', 'ms/ident/R2_short_min', 'pct'), ('RTwoShortMax', 'ms/ident/R2_short_max', 'pct'),
    ('RTwoLong', 'ms/ident/R2_long_median', 'pct'), ('CritOneA', 'ms/ident/crit1_W80_A', '2'), ('CritOneB', 'ms/ident/crit1_W80_B', '2'), ('CritOneC', 'ms/ident/crit1_W80_C', '2'),
    ('CritOneNestedA', 'ms/ident/crit1_nested_A/W80', '2'), ('CritOneNestedALo', 'ms/ident/crit1_nested_A/bracket/0', 'g'), ('CritOneNestedAHi', 'ms/ident/crit1_nested_A/bracket/1', 'g'),
    ('TierB', 'ms/ident/tier_b_bound', '2'), ('TierBPct', 'ms/ident/tier_b_bound', 'pct'), ('EvokedOnly', 'ms/ident/evoked_only_median_delta_r', 's4'),
    ('HopfSpecA', 'ms/ident/hopf_specific_A', 'pct'), ('HopfSpecC', 'ms/ident/hopf_specific_C', 'pct'), ('RealDelta', 'fig6/real_median_delta_r', 's3'), ('RealPos', 'fig6/real_positive', 'int'), ('RealP', 'fig6/real_p', '2'),
    *[(f'CritTwo{wd}{tag}', f"ms/ident/crit2_w1/{wd}/{key}/k", 'int') for wd in ('A', 'C') for tag, key in [('Committed', 'committed pair (Hopf 10, linear 1)'), ('One', 'both lambda 1'), ('Ten', 'both lambda 10'), ('Nested', 'both nested (own inner loop)')]],
    *[(f'CritTwo{wd}{tag}N', f"ms/ident/crit2_w1/{wd}/{key}/n", 'int') for wd in ('A', 'C') for tag, key in [('Committed', 'committed pair (Hopf 10, linear 1)'), ('Nested', 'both nested (own inner loop)')]],
]
# World C nested criterion-1 W80: exact value if bracketed, else the upper bracket
cn = N['ms']['ident']['crit1_nested_C']
lines = ['% generated by make_numbers.py from docs/figures/tnsre/figure_numbers.json; do not edit']
for name, path, fmt in M:
    lines.append(f'\\newcommand{{\\Num{name}}}{{{f(fmt)(get(path))}\\xspace}}')
if cn.get('W80') is not None:
    lines.append(f"\\newcommand{{\\NumCritOneNestedC}}{{{cn['W80']:.2f}\\xspace}}"); lines.append(f"\\newcommand{{\\NumCritOneNestedCText}}{{{cn['W80']:.2f} (bracket {cn['bracket'][0]:g}--{cn['bracket'][1]:g})\\xspace}}")
else:
    lines.append(f"\\newcommand{{\\NumCritOneNestedC}}{{{cn['bracket'][1]:g}\\xspace}}"); lines.append(f"\\newcommand{{\\NumCritOneNestedCText}}{{at or below {cn['bracket'][1]:g}\\xspace}}")
open(os.path.join(HERE, 'numbers.tex'), 'w').write('\n'.join(lines) + '\n'); print(len(lines) - 1, 'macros written')
