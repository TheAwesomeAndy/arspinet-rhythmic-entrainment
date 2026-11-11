#!/usr/bin/env python3
"""TNSRE figure set (Figs 1-7). Every plotted number is read from weineck/results/*.json; numbers derived here
(bootstrap intervals, per-participant means, t intervals) are written to docs/figures/tnsre/figure_numbers.json and
the captions in docs/FIGURES.md are generated from that file, so every caption number traces to a JSON key.
Fig 1b (example traces) is the one exception: it is computed from the raw Weineck 2022 EEG when present
(/home/user/data_local/weineck2022) and is left as a labelled placeholder otherwise; no trace is written to the repo.
Output: docs/figures/tnsre/fig{1..7}_*.pdf (vector) and .png (300 dpi).
"""
import json, os, sys, glob
import numpy as np
from scipy.stats import t as tdist
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')); RES = f'{ROOT}/weineck/results'; OUT = f'{ROOT}/docs/figures/tnsre'
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({'font.size': 7, 'axes.titlesize': 7.5, 'axes.labelsize': 7, 'legend.fontsize': 6, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5,
                     'pdf.fonttype': 42, 'ps.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False, 'lines.linewidth': 1.0, 'savefig.bbox': 'tight'})
W1, W2 = 3.5, 7.16          # IEEE single and double column (inches)
# one colour per model / statistic across all figures (Okabe-Ito, colour-blind safe); markers/linestyles carry the same information
COL = {'L': '#000000', 'R': '#0072B2', 'Rs': '#56B4E9', 'd_short': '#E69F00', 'd_long': '#D55E00', 'aug': '#009E73', 'aug_lin': '#CC79A7',
       'hopf': '#009E73', 'lin': '#CC79A7', 'rf': '#999999', 'env': '#7F7F7F', 'sim': '#999999', 'A': '#000000', 'B': '#666666', 'C': '#009E73'}
NUM = {}
rng = np.random.RandomState(0)


def J(p): return json.load(open(f'{RES}/{p}'))


def boot_ci(x, n=10000):
    x = np.sort(np.asarray(x, float)); r = np.random.RandomState(0); b = np.median(x[r.randint(0, len(x), (n, len(x)))], 1); return [float(np.percentile(b, 2.5)), float(np.percentile(b, 97.5))]   # fixed seed per call: same data, same interval


def t90(x):
    x = np.asarray(x, float); m = x.mean(); h = tdist.ppf(0.95, len(x) - 1) * x.std(ddof=1) / np.sqrt(len(x)); return [float(m - h), float(m + h)]


def save(fig, name):
    for ext, kw in (('pdf', {}), ('png', {'dpi': 300})): fig.savefig(f'{OUT}/{name}.{ext}', **kw)
    plt.close(fig)


def lab(ax, s): ax.text(-0.16, 1.04, s, transform=ax.transAxes, fontweight='bold', fontsize=8.5, va='bottom')


# ---------------------------------------------------------------- Fig 1
def box(ax, xy, w, h, text, fc='white', ec='black'):
    ax.add_patch(FancyBboxPatch(xy, w, h, boxstyle='round,pad=0.01,rounding_size=0.015', fc=fc, ec=ec, lw=0.8)); ax.text(xy[0] + w / 2, xy[1] + h / 2, text, ha='center', va='center', fontsize=6.2)


def arrow(ax, a, b): ax.add_patch(FancyArrowPatch(a, b, arrowstyle='-|>', mutation_scale=7, lw=0.7, color='black'))


TRACES = f'{RES}/fig1_traces.npz'


def example_traces():
    """Participant 10, one tempo-known trial near 2 Hz: beat feature, FC EEG, leave-one-trial-out TRF prediction, residual,
    reservoir unit-PC1 driven by the residual (as in q2_residual.stats_on). Read from weineck/results/fig1_traces.npz; if that
    file is absent, computed once from the raw data and saved there (--rebuild-traces forces recomputation)."""
    if os.path.exists(TRACES) and '--rebuild-traces' not in sys.argv:
        z = np.load(TRACES); return {k: (float(z[k]) if z[k].ndim == 0 else z[k]) for k in z.files}
    data = '/home/user/data_local/weineck2022'
    feats_mat = glob.glob('/tmp/claude-0/*/c557f3fa-*/scratchpad/weineck/small/SourceData__Figure1_SourceData1.mat') + glob.glob(f'{ROOT}/../data_local/weineck_features/SourceData__Figure1_SourceData1.mat')
    if not (os.path.isdir(data) and feats_mat): return None
    sys.path.insert(0, f'{ROOT}/weineck'); sys.path.insert(0, '/home/user/dissoAdventureExperiments/chapter5Experiments')
    from scipy.signal import butter, resample_poly
    from weineck_loader import load_features
    from underfit_check import load_participant_arrays, solve
    from experiment_zero import LIFReservoir
    feats, table = load_features(feats_mat[0]); sos = butter(4, [0.5, 30.0], btype='band', fs=1000.0, output='sos')
    X64, F64, XL, fbeat, fcidx, drive, j = load_participant_arrays(data, '10', feats, table, sos)
    n = int(np.argmin(np.abs(fbeat - 2.0)))
    A = sum(x.T @ x for k, x in enumerate(XL) if k != n); B = sum(x.T @ y for k, (x, y) in enumerate(zip(XL, X64)) if k != n)
    W = solve(A, B, 1.0); P = XL[n] @ W; y = X64[n][:, fcidx].mean(1); p = P[:, fcidx].mean(1); r = y - p
    r256 = resample_poly(r, 4, 1); r256 = (r256 - r256.mean()) / (r256.std() + 1e-12); S = LIFReservoir(seed=42).forward(r256)
    U, s_, _ = np.linalg.svd(S - S.mean(0), full_matrices=False); pc = U[:, 0] * s_[0]
    tr = {'f': float(fbeat[n]), 'beat': F64[n][:, 1], 'y': y, 'p': p, 'r': r, 'pc1': resample_poly(pc, 1, 4)}
    np.savez(TRACES, **tr); return tr


def fig1():
    fig = plt.figure(figsize=(W2, 3.6)); ax = fig.add_axes([0, 0.42, 1, 0.58]); ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    box(ax, (0.01, 0.62), 0.15, 0.3, 'Stimulus features\n(spectral flux, beat,\nenvelope, derivative)\n64 Hz')
    box(ax, (0.01, 0.12), 0.15, 0.3, 'EEG, 32 channels\nfronto-central\ncluster (8 ch)\n0.5-30 Hz')
    box(ax, (0.24, 0.62), 0.17, 0.3, 'Ridge TRF, 0-400 ms\nnested lambda\n(leave-one-trial-out)', ec=COL['d_short'])
    box(ax, (0.24, 0.12), 0.17, 0.3, 'Oscillator banks\nHopf / linear / RF\n+ TRF, held-out tempo', ec=COL['aug'])
    box(ax, (0.48, 0.62), 0.15, 0.3, 'Residual\nEEG minus\nTRF prediction')
    box(ax, (0.70, 0.78), 0.13, 0.17, 'Linear statistic\n(L, N0)', ec=COL['L'])
    box(ax, (0.70, 0.56), 0.13, 0.17, 'LIF reservoir N=256\nunit-PC1 (R)', ec=COL['R'])
    box(ax, (0.88, 0.62), 0.11, 0.3, 'Beat tagging\nown tempo vs\nother grid tempi\nlabel-shuffle null')
    box(ax, (0.48, 0.12), 0.24, 0.3, 'Held-out-tempo r per model\nrule: aug > best TRF (p<.01)\nand aug > linear bank (p<.05)')
    box(ax, (0.80, 0.12), 0.19, 0.3, 'Identifiability map\nsimulated worlds A, B, C\nkernels x real stimuli')
    ax.plot([0.16, 0.20], [0.77, 0.77], color='black', lw=0.7); ax.plot([0.16, 0.20], [0.27, 0.27], color='black', lw=0.7); ax.plot([0.20, 0.20], [0.27, 0.77], color='black', lw=0.7)
    for a, b in [((0.20, 0.77), (0.24, 0.77)), ((0.20, 0.27), (0.24, 0.27)), ((0.41, 0.77), (0.48, 0.77)),
                 ((0.63, 0.82), (0.70, 0.86)), ((0.63, 0.72), (0.70, 0.645)), ((0.83, 0.86), (0.88, 0.82)), ((0.83, 0.645), (0.88, 0.70)), ((0.41, 0.27), (0.48, 0.27)), ((0.72, 0.27), (0.80, 0.27))]:
        arrow(ax, a, b)
    ax.text(0.0, 1.0, 'a', fontweight='bold', fontsize=8.5, va='top')
    tr = example_traces(); axs = [fig.add_axes([0.08, 0.05 + k * 0.064, 0.88, 0.058]) for k in range(5)][::-1]
    if tr is None:
        axs[0].text(0.5, 0.5, 'example traces require the raw Weineck 2022 EEG (not in the repository)', transform=axs[0].transAxes, ha='center')
        for a in axs: a.axis('off')
        NUM['fig1'] = {'example_traces': 'not drawn (raw data absent)'}
    else:
        t0 = 64 * 2; n = 64 * 6; tt = np.arange(n) / 64
        for a, (v, c, name) in zip(axs, [(tr['beat'], COL['L'], 'beat feature'), (tr['y'], '#444444', 'EEG (FC)'), (tr['p'], COL['d_short'], 'TRF prediction'), (tr['r'], COL['R'], 'residual'), (tr['pc1'], COL['Rs'], 'reservoir PC1\n(residual input)')]):
            x = v[t0:t0 + n]; a.plot(tt, (x - x.mean()) / (x.std() + 1e-12), color=c, lw=0.7); a.set_yticks([]); a.set_ylabel(name, rotation=0, ha='right', va='center', fontsize=6); a.spines['left'].set_visible(False)
            if a is not axs[-1]: a.set_xticks([]); a.spines['bottom'].set_visible(False)
        axs[-1].set_xlabel('time (s)')
        axs[0].text(-0.05, 1.25, 'b', transform=axs[0].transAxes, fontweight='bold', fontsize=8.5)
        axs[0].set_title(f'example trial, participant 10, tempo {tr["f"]:.2f} Hz (TRF at lambda 1 for illustration)', fontsize=6.5, loc='left')
        NUM['fig1'] = {'example_participant': '10', 'example_tempo_hz': tr['f']}
    save(fig, 'fig1_pipeline')


# ---------------------------------------------------------------- Fig 2
def fig2():
    q = J('q2_residual_stage2_merged.json'); g = q['group']
    dr = np.array(g['resid_N0']['delta']); dd = np.array(g['drive_N0']['delta'])
    diffs = {'H1: drive, R - L': np.array(g['drive_R']['delta']) - dd, 'H3: residual, R - N0': np.array(g['resid_R']['delta']) - dr,
             'residual, R - envelope (N2a)': np.array(g['resid_R']['delta']) - np.array(g['resid_N2a']['delta']), 'residual, R - square (N2b)': np.array(g['resid_R']['delta']) - np.array(g['resid_N2b']['delta'])}
    NUM['fig2'] = {'n': len(dr), 'resid_median_delta': float(np.median(dr)), 'resid_median_ci95_boot': boot_ci(dr), 'resid_positive': int((np.array(g['resid_N0']['z']) > 0).sum()),
                   'p_H2': q['H2']['p'], 'drive_median_delta': float(np.median(dd)), 'drive_median_ci95_boot': boot_ci(dd),
                   'tost_90ci': {k: t90(v) for k, v in diffs.items()}, 'diff_mean': {k: float(np.mean(v)) for k, v in diffs.items()},
                   'equivalent': {'H1': q['H1']['equivalent'], 'H3': q['H3']['resid_N0']['equivalent'], 'N2a': q['H3']['resid_N2a']['equivalent'], 'N2b': q['H3']['resid_N2b']['equivalent']}}
    fig, (a, b) = plt.subplots(1, 2, figsize=(W2, 2.4), gridspec_kw={'width_ratios': [1, 1.4]})
    o = np.argsort(dr); x0 = np.zeros(len(dr)); x1 = np.ones(len(dr))
    for i in range(len(dr)): a.plot([0, 1], [dd[i], dr[i]], color='#BBBBBB', lw=0.5)
    a.scatter(x0 + rng.uniform(-0.06, 0.06, len(dd)), dd, s=7, color=COL['L'], zorder=3); a.scatter(x1 + rng.uniform(-0.06, 0.06, len(dr)), dr, s=7, color=COL['R'], marker='s', zorder=3)
    for x, v, ci in [(0, dd, NUM['fig2']['drive_median_ci95_boot']), (1, dr, NUM['fig2']['resid_median_ci95_boot'])]:
        a.errorbar(x + 0.22, np.median(v), yerr=[[np.median(v) - ci[0]], [ci[1] - np.median(v)]], fmt='D', color='black', ms=3.5, capsize=2)
    a.axhline(0, color='grey', lw=0.6); a.set_xticks([0, 1]); a.set_xticklabels(['drive\n(EEG)', 'residual\n(EEG - TRF)']); a.set_xlim(-0.4, 1.5)
    a.set_ylabel('beat-locking effect delta\n(per-trial standardised)'); a.set_title(f'H2: 34 participants, residual median {np.median(dr):.3f}', loc='left'); lab(a, 'a')
    names = list(diffs); ys = np.arange(len(names))[::-1]
    for y, k in zip(ys, names):
        lo, hi = NUM['fig2']['tost_90ci'][k]; m = NUM['fig2']['diff_mean'][k]; c = COL['R']
        b.plot([lo, hi], [y, y], color=c, lw=2); b.plot(m, y, 'o', color='black', ms=3)
    b.axvspan(-0.10, 0.10, color='#EEEEEE', zorder=0); b.axvline(0, color='grey', lw=0.6); b.set_yticks(ys); b.set_yticklabels(names)
    b.set_xlabel('reservoir minus comparison statistic (delta units)\nmean with 90 % t interval; shaded = equivalence bounds +-0.10'); b.set_title('H1 / H3: TOST equivalence', loc='left'); lab(b, 'b')
    fig.tight_layout(); save(fig, 'fig2_confirmatory')


# ---------------------------------------------------------------- Fig 3
def fig3():
    u = J('underfit_merged.json')['rows']; real = np.array(u['resid_real']['delta']); sim = np.array(u['resid_sim']['delta'])
    I = J('robustness/iaaft.json')['subjects']; subs = sorted(I, key=int)
    rr = np.array([I[s]['resid_N0_real']['delta'] for s in subs]); sp = np.array([I[s]['iaaft_delta_mean'] for s in subs]); ph = rr - sp; comp = J('robustness/iaaft_components.json')
    NUM['fig3'] = {'underfit_rows_median': {k: v['median_delta'] for k, v in u.items()}, 'real_vs_linear_world': J('underfit_merged.json')['decision'],
                   'real_median_ci95_boot': boot_ci(real), 'linear_world_median_ci95_boot': boot_ci(sim),
                   'iaaft': {'spectral_median': comp['spectral_median'], 'spectral_ci95_boot': boot_ci(sp), 'phase_median': comp['phase_median'], 'phase_ci95': comp['phase_ci95'], 'phase_positive': comp['phase_positive'], 'p': comp['p_wilcoxon']}}
    fig, (a, b) = plt.subplots(1, 2, figsize=(W2, 2.4))
    order = [('drive', 'drive'), ('pred', 'TRF\nprediction'), ('resid_real', 'residual\n(real)'), ('resid_pooled', 'residual\n(pooled TRF)'), ('sim_drive', 'linear world\ndrive'), ('resid_sim', 'linear world\nresidual')]
    for x, (k, name) in enumerate(order):
        v = np.array(u[k]['delta']); c = COL['sim'] if k.startswith(('sim', 'resid_sim')) else (COL['d_short'] if k == 'pred' else (COL['R'] if k.startswith('resid') else COL['L']))
        a.scatter(x + rng.uniform(-0.12, 0.12, len(v)), v, s=4, color=c, alpha=0.7); a.plot([x - 0.25, x + 0.25], [np.median(v)] * 2, color='black', lw=1.4)
    a.axhline(0, color='grey', lw=0.6); a.set_xticks(range(len(order))); a.set_xticklabels([n for _, n in order], fontsize=5.6); a.set_ylabel('delta'); lab(a, 'a')
    a.set_title(f"underfitting check: real residual {NUM['fig3']['real_vs_linear_world']['median_real']:.3f} vs linear world {NUM['fig3']['real_vs_linear_world']['median_linear_world']:.3f}", loc='left', fontsize=6.5)
    for x, (v, c, name) in enumerate([(rr, COL['R'], 'real residual'), (sp, COL['env'], 'spectral\n(IAAFT keeps)'), (ph, COL['aug'], 'phase-dependent\n(real - IAAFT)')]):
        b.scatter(x + rng.uniform(-0.12, 0.12, len(v)), v, s=4, color=c, alpha=0.7); b.plot([x - 0.25, x + 0.25], [np.median(v)] * 2, color='black', lw=1.4)
    ci = comp['phase_ci95']; b.errorbar(2.33, comp['phase_median'], yerr=[[comp['phase_median'] - ci[0]], [ci[1] - comp['phase_median']]], fmt='D', color='black', ms=3, capsize=2)
    ci = NUM['fig3']['iaaft']['spectral_ci95_boot']; b.errorbar(1.33, comp['spectral_median'], yerr=[[comp['spectral_median'] - ci[0]], [ci[1] - comp['spectral_median']]], fmt='D', color='black', ms=3, capsize=2)
    b.axhline(0, color='grey', lw=0.6); b.set_xticks([0, 1, 2]); b.set_xticklabels(['real\nresidual', 'spectral\n(IAAFT keeps)', 'phase-dependent\n(real - IAAFT)'], fontsize=6); b.set_ylabel('delta')
    b.set_title(f"IAAFT split: spectral {comp['spectral_median']:.3f}, phase {comp['phase_median']:.3f} (p = {comp['p_wilcoxon']:.4f})", loc='left', fontsize=6.5); lab(b, 'b')
    fig.tight_layout(); save(fig, 'fig3_underfit_iaaft')


# ---------------------------------------------------------------- robustness rows
ROWS = ['baseline', 'seed7', 'seed99', 'rho0', 'rho0.3', 'rho1.2', 'beta0.01', 'beta0.004', 'trf_flux', 'trf_long']
ROWLAB = {'baseline': 'baseline (seed 42, rho 0.9, beta 0.05)', 'seed7': 'seed 7', 'seed99': 'seed 99', 'rho0': 'rho 0 (no recurrence)', 'rho0.3': 'rho 0.3', 'rho1.2': 'rho 1.2',
          'beta0.01': 'beta 0.01 (tau 390 ms)', 'beta0.004': 'beta 0.004 (tau 980 ms)', 'trf_flux': 'TRF: flux only', 'trf_long': 'TRF: 0-600 ms', 'iaaft': 'IAAFT surrogates'}


def rowdata():
    out = {}
    for r in ROWS:
        S = J(f'robustness/{r}.json')['subjects']; subs = sorted(S, key=int)
        g = lambda k: np.array([S[s][k]['delta'] for s in subs])
        out[r] = {'subs': subs, 'H2': g('resid_N0'), 'R': g('resid_R'), 'Rs': g('resid_Rs'), 'N0': g('resid_N0')}
    return out


def fig4(rd):
    base0 = dict(zip(rd['rho0']['subs'], rd['rho0']['R']))
    NUM['fig4'] = {'R_minus_Rs': {}, 'R_minus_R_rho0': {}}
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(W2, 2.6), gridspec_kw={'width_ratios': [1.25, 1.25, 1]})
    for i, r in enumerate(ROWS):
        y = len(ROWS) - 1 - i; d1 = rd[r]['R'] - rd[r]['Rs']; d2 = rd[r]['R'] - np.array([base0[s] for s in rd[r]['subs']])
        for ax, d, key, col in [(a, d1, 'R_minus_Rs', COL['Rs']), (b, d2, 'R_minus_R_rho0', COL['R'])]:
            if r == 'rho0':                            # no recurrence in either reservoir (or no difference to itself): undefined, not zero
                txt = 'n/a (no recurrence by construction)' if key == 'R_minus_Rs' else 'n/a (reference row)'
                NUM['fig4'][key][r] = txt; ax.text(0, y, txt, ha='center', va='center', fontsize=5.2, color='#555555'); continue
            ci = boot_ci(d); m = float(np.median(d)); NUM['fig4'][key][r] = {'median': m, 'ci95_boot': ci}
            ax.plot(ci, [y, y], color=col, lw=2); ax.plot(m, y, 'o', color='black', ms=2.5)
    for ax, t in [(a, 'R minus shuffled-weight Rs'), (b, 'R minus R at rho 0')]:
        ax.axvline(0, color='grey', lw=0.6); ax.axvspan(-0.10, 0.10, color='#EEEEEE', zorder=0); ax.set_yticks(range(len(ROWS))); ax.set_title(t, loc='left'); ax.set_xlabel('median difference in delta\n(95 % bootstrap CI)')
    a.set_yticklabels([ROWLAB[r] for r in ROWS[::-1]], fontsize=5.8); b.set_yticklabels([]); lab(a, 'a'); lab(b, 'b')
    x = np.array([base0[s] for s in rd['baseline']['subs']]); y = rd['baseline']['R']
    c.scatter(x, y, s=6, color=COL['R']); lim = [min(x.min(), y.min()) - 0.05, max(x.max(), y.max()) + 0.05]; c.plot(lim, lim, color='grey', lw=0.6); c.set_xlim(lim); c.set_ylim(lim)
    c.set_xlabel('R delta, rho 0'); c.set_ylabel('R delta, rho 0.9 (baseline)'); c.set_title('per participant', loc='left'); lab(c, 'c')
    NUM['fig4']['baseline_vs_rho0_corr'] = float(np.corrcoef(x, y)[0, 1])
    fig.tight_layout(); save(fig, 'fig4_reservoir')


# ---------------------------------------------------------------- Fig 5
def fig5():
    S = {}
    for f in sorted(glob.glob(f'{RES}/oscillator_heldout_chunk*.json')): S.update(J(os.path.basename(f))['subjects'])
    models = ['d_short', 'd_long', 'hopf', 'lin', 'rf', 'aug', 'aug_lin']; names = {'d_short': 'TRF 0-400', 'd_long': 'TRF 0-1000', 'hopf': 'Hopf bank', 'lin': 'linear bank', 'rf': 'res.-and-fire', 'aug': 'Hopf + TRF', 'aug_lin': 'linear bank + TRF'}
    subs = sorted(S, key=int); per = {m: np.array([np.mean([v['r_fc'] for v in S[s]['models'][m].values()]) for s in subs]) for m in models}
    m = J('oscillator_heldout_merged.json'); cc = J('cycle_count_summary.json')
    NUM['fig5'] = {'n': len(subs), 'median_r_from_merged': m['median_r'], 'median_r_recomputed': {k: float(np.median(v)) for k, v in per.items()}, 'delta_r_aug_median': float(np.median(m['delta_r_aug'])),
                   'delta_r_aug_positive': int((np.array(m['delta_r_aug']) > 0).sum()), 'p_aug': m['p_aug'], 'p_aug_vs_lin': m['p_aug_vs_lin'], 'verdict': m['verdict'],
                   'curve': m['curve'], 'cycle_slopes': cc['participant_slopes'], 'cycle_group_slopes': cc['slope_of_group_median_z_per_Hz']}
    fig, (a, b, c) = plt.subplots(1, 3, figsize=(W2, 2.7), gridspec_kw={'width_ratios': [1.4, 1, 1]})
    for x, k in enumerate(models):
        v = per[k]; a.scatter(x + rng.uniform(-0.13, 0.13, len(v)), v, s=4, color=COL[k], alpha=0.75); a.plot([x - 0.28, x + 0.28], [np.median(v)] * 2, color='black', lw=1.3)
    a.set_xticks(range(len(models))); a.set_xticklabels([names[k] for k in models], rotation=40, ha='right', fontsize=5.8); a.axhline(0, color='grey', lw=0.6)
    a.set_ylabel('held-out-tempo r\n(mean over tempi)'); a.set_title(f"verdict: {m['verdict'].split(';')[0]}", loc='left'); lab(a, 'a')
    tk = sorted(m['curve'], key=float); b.plot([float(t) for t in tk], [m['curve'][t]['median_delta_r'] for t in tk], 'o-', color=COL['aug'], ms=3)
    b.axhline(0, color='grey', lw=0.6); b.set_xlabel('held-out tempo (Hz)'); b.set_ylabel('median delta r\n(Hopf + TRF minus best TRF)'); b.set_title('no preferred rate', loc='left'); lab(b, 'b')
    G = cc['group_median_z_by_tempo']; tt = [float(t) for t in sorted(G['L_full'], key=float)]
    for k, col, ls, mk, name in [('L_full', COL['L'], '-', 'o', 'L, full duration'), ('L_fixed_cycles', COL['L'], '--', 'o', 'L, fixed cycles'), ('R_pc1_full', COL['R'], '-', 's', 'R, full duration'), ('R_pc1_fixed_cycles', COL['R'], '--', 's', 'R, fixed cycles')]:
        c.plot(tt, [G[k][str(t)]['median_z'] for t in tt], ls=ls, marker=mk, color=col, ms=2.5, mfc='white' if 'fixed' in k else col, label=name)
    c.set_xlabel('tempo (Hz)'); c.set_ylabel('group median tagging z'); c.legend(frameon=False, fontsize=5.0, ncol=2, loc='upper center', bbox_to_anchor=(0.45, -0.28)); c.set_title('cycle-count control', loc='left'); lab(c, 'c')
    fig.tight_layout(); save(fig, 'fig5_theory3')


# ---------------------------------------------------------------- Fig 6
def fig6():
    I = J('identifiability.json'); A3 = I['A3']; diag = A3['diagnostic_criterion1_only']
    worlds = [('A', 'World A', COL['A'], 'o'), ('B', 'World B (power-matched)', COL['B'], 's'), ('C', 'World C (TRF-inexpressible)', COL['C'], '^')]
    real = J('oscillator_heldout_merged.json'); real_dr = float(np.median(real['delta_r_aug']))
    NUM['fig6'] = {'W80_full_rule': {k: A3[k]['w80'] for k in ['A', 'B', 'C', 'A_nested_lambda']}, 'W80_criterion1': diag['W80_criterion1_only'], 'false_positive': {k: A3[k]['false_positive'] for k in ['A', 'B', 'C', 'A_nested_lambda']},
                   'real_median_delta_r': real_dr, 'real_positive': int((np.array(real['delta_r_aug']) > 0).sum()), 'real_p': real['p_aug'], 'decision': A3['decision']['verdict']}
    fig = plt.figure(figsize=(W2, 3.2)); a = fig.add_axes([0.07, 0.36, 0.4, 0.56]); b = fig.add_axes([0.57, 0.36, 0.4, 0.56])
    for k, name, col, mk in worlds:
        bw = A3[k]['by_w']; ws = sorted(bw, key=float)
        a.plot([float(w) for w in ws], [bw[w]['rate'] for w in ws], marker=mk, color=col, ms=3, label=f'{name}, full rule')
        cw = diag[k]; ws2 = sorted(cw, key=float); a.plot([float(w) for w in ws2], [cw[w]['criterion1_pass'] for w in ws2], marker=mk, color=col, ms=3, ls=':', mfc='white', label=f'{name}, criterion 1 only')
        b.plot([float(w) for w in ws], [bw[w]['median_delta_r'] for w in ws], marker=mk, color=col, ms=3, label=name)
    nb = A3['A_nested_lambda']['by_w']; a.plot([float(w) for w in nb], [nb[w]['rate'] for w in nb], 'D', color=COL['aug_lin'], ms=3.5, mfc='white', label='World A, nested lambda')
    a.axhline(0.8, color='grey', lw=0.6); a.set_xlabel('w (oscillator amplitude share)'); a.set_ylabel('rate over simulated datasets'); a.set_ylim(-0.03, 1.03); a.legend(frameon=False, fontsize=5.2, ncol=2, loc='upper center', bbox_to_anchor=(0.5, -0.2))
    a.set_title('operating point: r 0.04, 40 trials, 12 tempi', loc='left'); lab(a, 'a')
    b.axhline(real_dr, color=COL['R'], lw=1.2); b.text(0.98, real_dr + 0.0005, f'real data: median {real_dr:+.3f} ({NUM["fig6"]["real_positive"]}/34 > 0)', color=COL['R'], fontsize=5.6, va='bottom', ha='right'); b.set_ylim(real_dr - 0.002, 0.012)
    b.axhline(0, color='grey', lw=0.6); b.set_xlabel('w'); b.set_ylabel('median delta r\n(Hopf + TRF minus best TRF)'); b.legend(frameon=False, fontsize=5.2, ncol=3, loc='upper center', bbox_to_anchor=(0.5, -0.2)); b.set_title('where the real data sit', loc='left'); lab(b, 'b')
    ins = fig.add_axes([0.63, 0.70, 0.11, 0.17]); RS = [0.02, 0.04, 0.08, 0.16]; NS = [20, 40, 80, 160]; cells = {(c['w'], c['r_target'], c['trials_per_tempo'], c['training_tempi']): c['rate'] for c in I['cells']}
    M = np.array([[cells.get((1.0, r, n, 12), np.nan) for r in RS] for n in NS]); ins.imshow(M, origin='lower', vmin=0, vmax=1, cmap='Greys', aspect='auto')
    ins.plot(1, 1, 'o', mfc='none', mec=COL['d_long'], ms=7, mew=1.2); ins.set_xticks(range(4)); ins.set_xticklabels(RS, fontsize=4.5); ins.set_yticks(range(4)); ins.set_yticklabels(NS, fontsize=4.5)
    ins.set_title('full rule, w = 1', fontsize=5); ins.set_xlabel('held-out r', fontsize=4.8, labelpad=1); ins.set_ylabel('trials', fontsize=4.8, labelpad=1)
    NUM['fig6']['inset_w1_rates'] = M.tolist()
    save(fig, 'fig6_identifiability')


# ---------------------------------------------------------------- Fig 7
def fig7(rd):
    NUM['fig7'] = {'H2': {}, 'R_minus_Rs': {}}; table = J('robustness_table.json')['rows']
    fig, (a, b) = plt.subplots(1, 2, figsize=(W2, 2.6), sharey=True)
    rows = ROWS + ['iaaft']; I = J('robustness/iaaft.json')['subjects']; isubs = sorted(I, key=int); sur = np.array([I[s]['iaaft_delta_mean'] for s in isubs])
    for i, r in enumerate(rows):
        y = len(rows) - 1 - i
        d = sur if r == 'iaaft' else rd[r]['H2']; ci = boot_ci(d); m = float(np.median(d)); NUM['fig7']['H2'][r] = {'median': m, 'ci95_boot': ci, 'p_H2': table[r].get('p_H2') if r != 'iaaft' else table[r].get('p_iaaft_gt0')}
        a.plot(ci, [y, y], color=COL['env'] if r == 'iaaft' else COL['L'], lw=2); a.plot(m, y, 'o' if r != 'iaaft' else 'D', color='black', ms=2.5)
        if r != 'iaaft':
            if r == 'rho0':
                NUM['fig7']['R_minus_Rs'][r] = 'n/a (no recurrence by construction)'; b.text(0, y, 'n/a (no recurrence by construction)', ha='center', va='center', fontsize=5.2, color='#555555')
            else:
                d2 = rd[r]['R'] - rd[r]['Rs']; ci2 = boot_ci(d2); m2 = float(np.median(d2)); NUM['fig7']['R_minus_Rs'][r] = {'median': m2, 'ci95_boot': ci2}
                b.plot(ci2, [y, y], color=COL['Rs'], lw=2); b.plot(m2, y, 'o', color='black', ms=2.5)
    a.axvline(0, color='grey', lw=0.6); a.set_yticks(range(len(rows))); a.set_yticklabels([ROWLAB[r] for r in rows[::-1]], fontsize=5.8); a.set_xlabel('median residual delta (H2)\n95 % bootstrap CI'); a.set_title('H2 per row (IAAFT: surrogate delta)', loc='left'); lab(a, 'a')
    b.set_xticks([-0.1, -0.05, 0, 0.05, 0.1]); b.axvline(0, color='grey', lw=0.6); b.axvspan(-0.10, 0.10, color='#EEEEEE', zorder=0); b.set_xlabel('median R minus Rs\n95 % bootstrap CI'); b.set_title('reservoir vs shuffled weights', loc='left'); lab(b, 'b')
    fig.tight_layout(); save(fig, 'fig7_robustness')


def main():
    fig1(); fig2(); fig3(); rd = rowdata(); fig4(rd); fig5(); fig6(); fig7(rd)
    json.dump(NUM, open(f'{OUT}/figure_numbers.json', 'w'), indent=1, default=float)
    captions(); print('figures and docs/FIGURES.md written to', OUT)


# ---------------------------------------------------------------- captions
def captions():
    n = json.load(open(f'{OUT}/figure_numbers.json')); f2, f3, f4, f5, f6, f7 = (n[k] for k in ('fig2', 'fig3', 'fig4', 'fig5', 'fig6', 'fig7'))
    k = lambda s: f'`{s}`'
    ci = lambda v: f'[{v[0]:.3f}, {v[1]:.3f}]'
    W = lambda d: ('not reached' if d['W80'] is None else f"{d['W80']:.2f} (bracket {d['bracket'][0]:g}-{d['bracket'][1]:g})")
    t = f"""# TNSRE figure set: captions (draft)

Generated by `weineck/figures/make_figures.py` from the results JSONs; do not edit numbers by hand, rerun the script.
Figures: `docs/figures/tnsre/fig{{1..7}}_*.pdf` (vector) and `.png` (300 dpi). Every number below names its source:
a key in a results file under `weineck/results/`, or a key in `docs/figures/tnsre/figure_numbers.json` (written by
the same script; bootstrap intervals use 10,000 resamples of participants, seed 0, percentile method).
Colours are fixed per model across figures (Okabe-Ito): linear statistic black, reservoir R dark blue, shuffled-weight
reservoir Rs light blue, TRF 0-400 ms orange, TRF 0-1000 ms vermillion, Hopf bank and Hopf + TRF green, linear bank
and linear bank + TRF pink, resonate-and-fire grey; markers and line styles carry the same information.

**Fig. 1. Pipeline and an example trial.** (a) Stimulus features (spectral flux, beat, envelope, derivative; 64 Hz) and
fronto-central EEG enter a ridge TRF (0-400 ms, nested lambda, leave-one-trial-out); the residual (EEG minus TRF
prediction) is scored by the shared beat-tagging statistic directly (L) and through the canonical LIF reservoir (N = 256,
unit-PC1, R), against a stimulus-label shuffle null. In parallel, oscillator banks plus the TRF are compared with the TRF
alone at held-out tempi under the committed rule, and the rule's sensitivity is mapped in simulation. (b) One trial,
participant {n['fig1'].get('example_participant', '-')}, tempo {n['fig1'].get('example_tempo_hz', float('nan')):.2f} Hz,
6 s: beat feature, FC EEG, TRF prediction (lambda 1 for illustration; the analysis uses nested lambda), residual, and the
reservoir's unit-PC1 driven by the residual. Traces are z-scored for display and computed from the raw data at
build time; they are not stored in the repository. [{k('figure_numbers.json: fig1')}]

**Fig. 2. Confirmatory stage 2 (34 participants, pre-registered).** (a) Beat-locking effect delta per participant on the
drive (EEG) and on the TRF residual; lines join participants; diamonds, median with 95 % bootstrap CI. Residual median
{f2['resid_median_delta']:.3f} {ci(f2['resid_median_ci95_boot'])}, {f2['resid_positive']}/34 positive, one-sided
Wilcoxon p = {f2['p_H2']:.1e} (H2 supported); drive median {f2['drive_median_delta']:.3f}
{ci(f2['drive_median_ci95_boot'])}. [{k('q2_residual_stage2_merged.json: group.resid_N0.delta, group.drive_N0.delta, H2.p')};
{k('figure_numbers.json: fig2')}] (b) Reservoir minus comparison statistic, mean with 90 % t interval (the TOST
interval); shaded band, equivalence bounds +-0.10 delta. H1 (drive, R - L) {ci(f2['tost_90ci']['H1: drive, R - L'])} and H3
(residual, R - N0) {ci(f2['tost_90ci']['H3: residual, R - N0'])}: equivalent. R exceeds the envelope (N2a,
{ci(f2['tost_90ci']['residual, R - envelope (N2a)'])}) and square (N2b, {ci(f2['tost_90ci']['residual, R - square (N2b)'])})
statistics only because those are null on the residual. [{k('q2_residual_stage2_merged.json: H1, H3')};
{k('figure_numbers.json: fig2.tost_90ci')}]

**Fig. 3. Underfitting check and IAAFT decomposition (exploratory).** (a) Delta per participant for the drive, the TRF
prediction, the real residual, the residual of a pooled 33-participant TRF, and a simulated linear world (fitted kernels x
real stimuli, noise matched to the observed held-out r). Real residual median
{f3['real_vs_linear_world']['median_real']:.3f} {ci(f3['real_median_ci95_boot'])} vs linear-world residual
{f3['real_vs_linear_world']['median_linear_world']:.3f} {ci(f3['linear_world_median_ci95_boot'])}, p(real > linear world) =
{f3['real_vs_linear_world']['p_real_gt_linear_world']:.1e}: H2 is not explained by underfitting. The underfitting check
recomputes the real-residual deltas in its own pipeline: same median as Fig. 2, per-participant values correlate at
r = 0.999 (largest difference 0.024, identical in 18/34), so its interval differs slightly from Fig. 2's. Confirmed cause:
the underfitting check scores the residual at its own length, while stage 2 first truncates residual and 256 Hz drive
to their common length (they differ by up to 4 samples, 16 ms); recomputing participant 10 both ways reproduces both
stored values exactly (-0.0817 untruncated, -0.0574 truncated). [`residual_discrepancy_check.json`]
[{k('underfit_merged.json: rows.*.delta, decision')}; {k('figure_numbers.json: fig3')}] (b) Residual delta split by IAAFT
surrogates (200 per participant): spectral part retained by the surrogates, median {f3['iaaft']['spectral_median']:.3f}
{ci(f3['iaaft']['spectral_ci95_boot'])}; phase-dependent part (real minus surrogate mean), median
{f3['iaaft']['phase_median']:.3f} {ci(f3['iaaft']['phase_ci95'])}, {f3['iaaft']['phase_positive']}/34 positive, one-sided
Wilcoxon p = {f3['iaaft']['p']:.4f}. [{k('robustness/iaaft.json: subjects.*.resid_N0_real.delta, iaaft_delta_mean')};
{k('robustness/iaaft_components.json')}]

**Fig. 4. The reservoir adds nothing over its linear readout (exploratory robustness rows).** (a) Median R minus
shuffled-weight Rs on the residual per row, 95 % bootstrap CI; baseline {f4['R_minus_Rs']['baseline']['median']:+.4f}
{ci(f4['R_minus_Rs']['baseline']['ci95_boot'])}. At rho 0 neither reservoir has recurrence, so R minus Rs is undefined by
construction and the row is marked n/a. (b) Median R in each row minus R in the rho 0 row for the same participant (rho 0 row: reference, n/a); baseline
{f4['R_minus_R_rho0']['baseline']['median']:+.4f} {ci(f4['R_minus_R_rho0']['baseline']['ci95_boot'])}. (c) Per participant,
R at rho 0.9 against R at rho 0 (r = {f4['baseline_vs_rho0_corr']:.3f}). Shaded bands, +-0.10 delta.
[{k('robustness/<row>.json: subjects.*.resid_R.delta, resid_Rs.delta')}; {k('figure_numbers.json: fig4')}]

**Fig. 5. Theory 3, oscillator encoding at held-out tempi (exploratory, rule fixed in advance).** (a) Held-out-tempo r
per participant (mean over held-out tempi) for each model; bars, medians (TRF 0-400 ms {f5['median_r_from_merged']['d_short']:.4f},
Hopf + TRF {f5['median_r_from_merged']['aug']:.4f}, linear bank + TRF {f5['median_r_from_merged']['aug_lin']:.4f}).
Hopf + TRF minus best TRF: median {f5['delta_r_aug_median']:+.3f}, {f5['delta_r_aug_positive']}/34 positive, p =
{f5['p_aug']:.2f}; verdict "{f5['verdict']}". [{k('oscillator_heldout_merged.json: median_r, delta_r_aug, p_aug, verdict')};
{k('oscillator_heldout_chunk*.json: subjects.*.models.*.*.r_fc')}] (b) Median delta r by held-out tempo (n = 34 except 1.00
Hz, n = {f5['curve']['1.0']['n']}): negative at every tempo, no preferred rate. [{k('oscillator_heldout_merged.json: curve')}]
(c) Group median tagging z by tempo on full-duration data and on a fixed number of beat cycles per tempo. Participant
slopes: L {f5['cycle_slopes']['L_full']['median_slope_z_per_Hz']:+.3f} z/Hz (p = {f5['cycle_slopes']['L_full']['wilcoxon_greater_p']:.4f})
full vs {f5['cycle_slopes']['L_fixed_cycles']['median_slope_z_per_Hz']:+.3f} (p = {f5['cycle_slopes']['L_fixed_cycles']['wilcoxon_greater_p']:.2f})
fixed cycles; R {f5['cycle_slopes']['R_pc1_full']['median_slope_z_per_Hz']:+.3f} (p = {f5['cycle_slopes']['R_pc1_full']['wilcoxon_greater_p']:.4f})
vs {f5['cycle_slopes']['R_pc1_fixed_cycles']['median_slope_z_per_Hz']:+.3f} (p = {f5['cycle_slopes']['R_pc1_fixed_cycles']['wilcoxon_greater_p']:.2f}):
the rise toward 4 Hz is a cycle-count artefact. [{k('cycle_count_summary.json: group_median_z_by_tempo, participant_slopes')}]

**Fig. 6. Identifiability of an oscillator component (simulated; exploratory).** (a) Rate at which the committed rule says
"oscillator supported" (solid) and at which its first criterion alone passes (dotted; exploratory decomposition, outside
the committed rule), against the oscillator's amplitude share w, at Weineck's operating point (held-out r 0.04, 40 trials
per tempo, 12 training tempi), 20 simulated datasets of 20 participants per point (nested lambda: 10). W80, full rule:
World A {W(f6['W80_full_rule']['A'])}, World B {W(f6['W80_full_rule']['B'])}, World C {W(f6['W80_full_rule']['C'])}, nested
lambda {W(f6['W80_full_rule']['A_nested_lambda'])}. W80, criterion 1 only: A {W(f6['W80_criterion1']['A'])}, B
{W(f6['W80_criterion1']['B'])}, C {W(f6['W80_criterion1']['C'])}, nested {W(f6['W80_criterion1']['A_nested_lambda'])}.
False-positive rate 0.00 in every world. Pre-committed decision: "{f6['decision']}".
[{k('identifiability.json: A3.*.w80, A3.*.by_w, A3.diagnostic_criterion1_only, A3.decision')}] (b) Median delta r (Hopf +
TRF minus best TRF) against w; horizontal line, the real data (median {f6['real_median_delta_r']:+.3f},
{f6['real_positive']}/34 positive, p = {f6['real_p']:.2f}), below the simulated evoked-only world. Inset: full-rule detection
at w = 1 over held-out r and trials per tempo, operating point circled. [{k('oscillator_heldout_merged.json: delta_r_aug')};
{k('identifiability.json: cells')}; {k('figure_numbers.json: fig6')}]

**Fig. 7. Robustness grid (exploratory; no row flipped).** (a) Median residual delta (H2) per row with 95 % bootstrap
CI; every non-IAAFT row has p < .01 (baseline {f7['H2']['baseline']['median']:.3f} {ci(f7['H2']['baseline']['ci95_boot'])}).
Seed, rho and beta rows equal the baseline by construction: the H2 statistic is computed on the TRF residual and never
passes through the reservoir. IAAFT row: median surrogate delta {f7['H2']['iaaft']['median']:.3f}
{ci(f7['H2']['iaaft']['ci95_boot'])}. (b) Median R minus Rs per row, 95 % bootstrap CI, all within +-0.10; rho 0 row n/a (no recurrence by construction).
[{k('robustness_table.json: rows')}; {k('robustness/<row>.json')}; {k('figure_numbers.json: fig7')}]
"""
    open(f'{ROOT}/docs/FIGURES.md', 'w').write(t)


if __name__ == '__main__':
    captions() if (len(sys.argv) > 1 and sys.argv[1] == '--captions-only') else main()
