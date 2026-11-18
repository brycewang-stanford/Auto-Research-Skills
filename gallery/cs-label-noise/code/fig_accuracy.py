"""Figure: clean-test accuracy against the training-label flip rate rho, per dataset.

Reads runs/main-rho0/metrics.json and runs/main-noisy/metrics.json only (seed means and
SDs over the 10 seeds, and the majority-class share m). Writes paper/figures/fig_accuracy.pdf.
"""
from __future__ import annotations

import argparse

from common import RHOS
from figlib import (DATASETS, INK, METHODS, METHOD_STYLE, MUTED, load_metrics, mpl_setup,
                    rho_key, save_pdf, write_metrics)

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_accuracy.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

m0, mn = load_metrics("main-rho0"), load_metrics("main-noisy")
excl = load_metrics("exclusion-check")


def get(key: str):
    return m0[key] if key in m0 else mn[key]


plt = mpl_setup()
fig, axes = plt.subplots(1, 4, figsize=(6.6, 2.35))
dodge = {"lr": -0.007, "rf": 0.0, "gbdt": 0.007}
n_points, checksum = 0, 0.0
for ax, d in zip(axes, DATASETS):
    m = m0[f"{d}.m_mean"]
    lows = [m]
    for meth in METHODS:
        st = METHOD_STYLE[meth]
        xs, ys, es = [], [], []
        for rho in RHOS:
            base = f"{d}.{meth}.{rho_key(rho)}"
            assert get(base + ".n_seeds") == 10
            xs.append(rho + dodge[meth])
            ys.append(get(base + ".acc_mean"))
            es.append(get(base + ".acc_sd"))
        ax.errorbar(xs, ys, yerr=es, color=st["color"], marker=st["marker"], ls=st["ls"],
                    lw=1.1, ms=3.6, capsize=1.8, elinewidth=0.7, mfc=st["color"], mec="white",
                    mew=0.4, label=st["label"], zorder=3)
        lows += [y - e for y, e in zip(ys, es)]
        n_points += len(ys)
        checksum += sum(ys) + sum(es)
    ax.axhline(m, color=MUTED, lw=0.8, ls=(0, (4, 2)), zorder=1)
    ax.text(-0.02, m - 0.006, "majority rate $m$", ha="left", va="top", fontsize=6.5, color=MUTED)
    # Honest axis: from just below the lowest of m and every (mean - SD) up to 1.0.
    ax.set_ylim(min(lows) - 0.045, 1.0)
    ax.set_xlim(-0.03, 0.43)
    ax.set_xticks(RHOS)
    ax.set_xticklabels([f"{r:g}" for r in RHOS])
    ax.set_xlabel(r"flip rate $\rho$")
    excluded = not (excl[f"{d}.informative_h1"] and excl[f"{d}.informative_h2"])
    title = d + (" (excluded)" if excluded else "")
    ax.set_title(title, color=MUTED if excluded else INK, fontsize=8.5)
    if excluded:
        for sp in ax.spines.values():
            sp.set_linestyle((0, (2, 2)))
            sp.set_edgecolor(MUTED)
    ax.grid(axis="y", color="#e6e6e6", lw=0.5, zorder=0)
    checksum += m
axes[0].set_ylabel("clean-test accuracy")
handles, labels = axes[0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.08))
fig.tight_layout(w_pad=0.8)
save_pdf(fig, args.out)

write_metrics(args.metrics, {"n_panels": len(DATASETS), "n_series": len(DATASETS) * len(METHODS),
                             "n_points": n_points, "checksum_plotted": checksum})
