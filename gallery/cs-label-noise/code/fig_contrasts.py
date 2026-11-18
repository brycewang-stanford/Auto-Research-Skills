"""Figure: forest plot of the pre-registered contrasts D (H1), D1 and D2 (H2) per dataset.

Reads runs/h-tests/metrics.json only. Each row shows the point estimate, the 95% decision
interval (paired t(9); Nadeau-Bengio corrected where c > 0.1) and, as a lighter second mark,
the descriptive seed-bootstrap interval, which never decides an outcome. The marker shows the
per-dataset outcome. Datasets excluded at rho = 0 are drawn in a separate row on their own
x-scale, so their very wide intervals neither vanish nor squeeze the informative rows.
Writes paper/figures/fig_contrasts.pdf.
"""
from __future__ import annotations

import argparse

from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from figlib import DATASETS, INK, LIGHT, MUTED, SMD, load_metrics, mpl_setup, save_pdf, write_metrics

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_contrasts.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

M = load_metrics("h-tests")
COLS = [("H1", "D", r"H1: $D = r_{\mathrm{GBDT}} - r_{\mathrm{RF}}$", "H1 predicts $D > 0$"),
        ("H2", "D1", r"H2: $D_1 = r_{\mathrm{LR}} - r_{\mathrm{GBDT}}$", "H2 predicts $D_1 < 0$"),
        ("H2", "D2", r"H2: $D_2 = r_{\mathrm{LR}} - r_{\mathrm{RF}}$", "H2 predicts $D_2 < 0$")]


def informative(d: str) -> bool:
    h1, h2 = M[f"{d}.H1.informative"], M[f"{d}.H2.informative"]
    assert h1 == h2, "a dataset informative for one hypothesis only needs its own layout"
    return bool(h1)


top = [d for d in DATASETS if informative(d)]
bottom = [d for d in DATASETS if not informative(d)]


def marker_for(outcome: str):
    if outcome.startswith("excluded"):
        return dict(marker="x", ms=4.5, mec=MUTED, mfc=MUTED, mew=1.0)
    if outcome == "supported":
        return dict(marker="o", ms=4.5, mec=INK, mfc=INK, mew=0.9)
    if outcome == "contradicted":
        return dict(marker="D", ms=4.0, mec=INK, mfc=INK, mew=0.9)
    return dict(marker="o", ms=4.5, mec=INK, mfc="white", mew=0.9)   # inconclusive / no meaningful difference


def limits(ds):
    vals = [-SMD, SMD, 0.0]
    for d in ds:
        for hyp, key, *_ in COLS:
            b = f"{d}.{hyp}.{key}"
            vals += [M[b + ".lo"], M[b + ".hi"], M[b + ".boot_lo"], M[b + ".boot_hi"]]
    lo, hi = min(vals), max(vals)
    pad = 0.06 * (hi - lo)
    return lo - pad, hi + pad


plt = mpl_setup()
fig = plt.figure(figsize=(6.6, 2.9))
gs = fig.add_gridspec(2, 3, height_ratios=[len(top), max(len(bottom), 1) * 1.25], hspace=0.9, wspace=0.12)
n_intervals, checksum = 0, 0.0
bottom_axes = []
for row, ds in enumerate((top, bottom)):
    if not ds:
        continue
    xlo, xhi = limits(ds)
    for col, (hyp, key, title, predicts) in enumerate(COLS):
        ax = fig.add_subplot(gs[row, col])
        ax.axvspan(-SMD, SMD, color="#eeeeee", lw=0, zorder=0)
        ax.axvline(0, color=MUTED, lw=0.7, zorder=1)
        for i, d in enumerate(ds):
            y = len(ds) - 1 - i
            b = f"{d}.{hyp}.{key}"
            outcome = M[f"{d}.{hyp}.outcome"]
            excluded = outcome.startswith("excluded")
            main_col = MUTED if excluded else INK
            ax.plot([M[b + ".lo"], M[b + ".hi"]], [y, y], color=main_col, lw=1.4,
                    solid_capstyle="butt", zorder=3)
            ax.plot([M[b + ".boot_lo"], M[b + ".boot_hi"]], [y - 0.25, y - 0.25], color=LIGHT,
                    lw=1.0, zorder=2)
            ax.plot([M[b + ".boot_lo"]] * 2 + [None] + [M[b + ".boot_hi"]] * 2,
                    [y - 0.33, y - 0.17, None, y - 0.33, y - 0.17], color=LIGHT, lw=0.8, zorder=2)
            ax.plot([M[b + ".value"]], [y], ls="none", zorder=4, **marker_for(outcome))
            n_intervals += 2
            checksum += M[b + ".value"] + M[b + ".lo"] + M[b + ".hi"] + M[b + ".boot_lo"] + M[b + ".boot_hi"]
        ax.set_xlim(xlo, xhi)
        ax.set_ylim(-0.6, len(ds) - 0.4)
        ax.set_yticks(range(len(ds)))
        if col == 0:
            names = [d + (r"$^{\dagger}$" if M[f"{d}.c"] > 0.1 else "") for d in ds]
            ax.set_yticklabels(list(reversed(names)))
            for lab in ax.get_yticklabels():
                if not informative(lab.get_text().replace(r"$^{\dagger}$", "")):
                    lab.set_color(MUTED)
        else:
            ax.set_yticklabels([])
        ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False)
        if row == 0:
            ax.set_title(title, fontsize=8.5)
            ax.set_xlabel(predicts, fontsize=7, color=MUTED, labelpad=2)
        else:
            ax.spines["bottom"].set_color(MUTED)
            bottom_axes.append(ax)

if bottom_axes:
    pos = bottom_axes[0].get_position()
    fig.text(0.5 * (pos.x0 + bottom_axes[-1].get_position().x1), pos.y1 + 0.035,
             "Excluded at $\\rho = 0$ (a method's headroom below 0.05; uninformative), drawn on its own x-scale",
             ha="center", va="bottom", fontsize=7.5, color=MUTED)

handles = [
    Line2D([], [], color=INK, lw=1.4, label="95% decision interval"),
    Line2D([], [], color=LIGHT, lw=1.0, label="seed bootstrap 95% (descriptive only)"),
    Patch(facecolor="#eeeeee", label=r"$|{\rm difference}| < 0.05$"),
    Line2D([], [], ls="none", label="supported", **marker_for("supported")),
    Line2D([], [], ls="none", label="no detectable difference (inconclusive)", **marker_for("inconclusive")),
    Line2D([], [], ls="none", label="excluded (uninformative)", **marker_for("excluded")),
]
fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.17),
           handlelength=1.8, columnspacing=1.4)
save_pdf(fig, args.out)

write_metrics(args.metrics, {"n_datasets": len(top) + len(bottom), "n_informative_rows": len(top),
                             "n_intervals": n_intervals, "checksum_plotted": checksum})
