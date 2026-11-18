"""Figure: forest plot of the ablation tests Delta = D_main - D_ablation (A1, A2, A3).

Reads runs/abl-noes/metrics.json (A1), runs/abl-cleanval/metrics.json (A2) and
runs/abl-budget/metrics.json (A3). Each row shows Delta with its 95% decision interval
(the dataset's paired t(9) interval); the marker shows the pre-registered status. Datasets
excluded at rho = 0 are drawn in a separate row block on their own x-scale.
Writes paper/figures/fig_ablations.pdf.
"""
from __future__ import annotations

import argparse

from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from figlib import DATASETS, INK, MUTED, SMD, load_metrics, mpl_setup, save_pdf, write_metrics

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_ablations.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

ABL = [("A1", "abl-noes", "A1 no early stopping", ("Delta",)),
       ("A2", "abl-cleanval", "A2 clean-label validation", ("Delta", "Delta1", "Delta2")),
       ("A3", "abl-budget", "A3 half budget", ("Delta", "Delta1", "Delta2"))]
MET = {run: load_metrics(run) for _, run, _, _ in ABL}
H = load_metrics("h-tests")
COLS = [("Delta", r"$\Delta = D_{\mathrm{main}} - D_{\mathrm{abl}}$ (H1 contrast)"),
        ("Delta1", r"$\Delta_1$ ($D_1$, H2 contrast)"),
        ("Delta2", r"$\Delta_2$ ($D_2$, H2 contrast)")]

top = [d for d in DATASETS if H[f"{d}.H1.informative"]]
bottom = [d for d in DATASETS if not H[f"{d}.H1.informative"]]
assert all(H[f"{d}.H1.informative"] == H[f"{d}.H2.informative"] for d in DATASETS)


def marker_for(status: str):
    if status.startswith("excluded"):
        return dict(marker="x", ms=4.5, mec=MUTED, mfc=MUTED, mew=1.0)
    if status == "attributed":
        return dict(marker="o", ms=4.5, mec=INK, mfc=INK, mew=0.9)
    if status == "not attributed":
        return dict(marker="o", ms=4.5, mec=INK, mfc="white", mew=0.9)
    return dict(marker="s", ms=4.0, mec=MUTED, mfc="white", mew=0.9)   # unstable denominator


def rows(ds):
    out = []
    for d in ds:
        for tag, run, label, keys in ABL:
            out.append((d, tag, run, label, keys))
    return out


def limits(ds):
    vals = [-SMD, SMD, 0.0]
    for d, tag, run, _, keys in rows(ds):
        for k in keys:
            vals += [MET[run][f"{d}.{tag}.{k}.lo"], MET[run][f"{d}.{tag}.{k}.hi"]]
    lo, hi = min(vals), max(vals)
    pad = 0.06 * (hi - lo)
    return lo - pad, hi + pad


plt = mpl_setup()
nt, nb = len(rows(top)), len(rows(bottom))
fig = plt.figure(figsize=(6.6, 0.24 * (nt + nb) + 1.6))
gs = fig.add_gridspec(2, 3, height_ratios=[nt, max(nb, 1)], hspace=0.42, wspace=0.12)
n_intervals, n_attributed, checksum = 0, 0, 0.0
bottom_axes = []
for block, ds in enumerate((top, bottom)):
    if not ds:
        continue
    rs = rows(ds)
    xlo, xhi = limits(ds)
    for col, (key, title) in enumerate(COLS):
        ax = fig.add_subplot(gs[block, col])
        ax.axvspan(-SMD, SMD, color="#eeeeee", lw=0, zorder=0)
        ax.axvline(0, color=MUTED, lw=0.7, zorder=1)
        for i, (d, tag, run, label, keys) in enumerate(rs):
            y = len(rs) - 1 - i
            if i and rs[i - 1][0] != d:
                ax.axhline(y + 0.5, color="#dddddd", lw=0.5, zorder=0)
            if key not in keys:
                continue
            b = f"{d}.{tag}.{key}"
            m = MET[run]
            status = m[b + ".status"]
            col_line = MUTED if status.startswith("excluded") else INK
            ax.plot([m[b + ".lo"], m[b + ".hi"]], [y, y], color=col_line, lw=1.4,
                    solid_capstyle="butt", zorder=3)
            ax.plot([m[b + ".value"]], [y], ls="none", zorder=4, **marker_for(status))
            n_intervals += 1
            n_attributed += status == "attributed"
            checksum += m[b + ".value"] + m[b + ".lo"] + m[b + ".hi"]
        ax.set_xlim(xlo, xhi)
        ax.set_ylim(-0.6, len(rs) - 0.4)
        ax.set_yticks(range(len(rs)))
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        if col == 0:
            ax.set_yticklabels([f"{d}: {label}" for d, _, _, label, _ in reversed(rs)])
            if block == 1:
                for lab in ax.get_yticklabels():
                    lab.set_color(MUTED)
        else:
            ax.set_yticklabels([])
        if block == 0:
            ax.set_title(title, fontsize=8)
        else:
            ax.spines["bottom"].set_color(MUTED)
            bottom_axes.append(ax)

if bottom_axes:
    pos = bottom_axes[0].get_position()
    fig.text(0.5 * (pos.x0 + bottom_axes[-1].get_position().x1), pos.y1 + 0.02,
             "Excluded at $\\rho = 0$ (uninformative), drawn on its own x-scale",
             ha="center", va="bottom", fontsize=7.5, color=MUTED)

handles = [
    Line2D([], [], color=INK, lw=1.4, label="95% decision interval"),
    Patch(facecolor="#eeeeee", label=r"$|\Delta| < 0.05$"),
    Line2D([], [], ls="none", label="attributed (interval excludes 0 and $|\\Delta| \\geq 0.05$)",
           **marker_for("attributed")),
    Line2D([], [], ls="none", label="not attributed", **marker_for("not attributed")),
    Line2D([], [], ls="none", label="excluded (uninformative)", **marker_for("excluded")),
]
fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.08),
           handlelength=1.8, columnspacing=1.2)
save_pdf(fig, args.out)

write_metrics(args.metrics, {"n_intervals": n_intervals, "n_attributed": n_attributed,
                             "n_informative_tests": sum(len(k) for *_, k in rows(top)),
                             "checksum_plotted": checksum})
