"""Figure: distribution of store-level changes in FTE employment on the balanced sample B,
by state, with the pooled 5th/95th-percentile winsorization cutoffs of H2 marked.

Reads (all written by logged runs):
- data/derived/stores.csv        (prepare-data) store-level FTE; the analysis variables are
                                 built with code/ck_analysis.py's build(), the code the
                                 analysis runs used, so nothing is re-specified here
- runs/h2-winsor/metrics.json    cutoffs, sample and capped counts (the lines drawn)
- runs/h2-winsor/capped.csv      the capped stores
- runs/main-t3/metrics.json      row-4 state mean changes and S1 SEs (the interval drawn)

The cutoffs drawn are the logged ones. The script asserts that the stores it plots are the
logged sample (counts, closures), that numpy.percentile on them gives the logged cutoffs,
that the stores beyond the cutoffs are exactly the logged capped list, and that the state
means equal the logged row-4 changes. Nothing new is estimated.

Writes paper/figures/fig_dfte_dist.pdf.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ck_analysis as ck  # noqa: E402
from figlib import (BLUE, INK, LIGHT, VERMILLION, load_metrics, mpl_setup, num,  # noqa: E402
                    save_pdf, write_metrics)

ap = argparse.ArgumentParser()
ap.add_argument("--data", default="data/derived/stores.csv")
ap.add_argument("--out", default="paper/figures/fig_dfte_dist.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

TOL = 1e-9
Z95 = 1.96          # normal 97.5% quantile: the interval drawn is mean +/- 1.96 x S1 SE
BIN = 2.5           # histogram bin width, FTE
OFFSET = -1.125     # bin edges at OFFSET + k*BIN; FTE is a multiple of 0.25, so no store
                    # lies on an edge

w, t3 = load_metrics("h2-winsor"), load_metrics("main-t3")
d = ck.build(ck.load(args.data))
b = d[d["in_bal"]]
q05, q95 = w["q05"], w["q95"]

# ---- the stores plotted are the logged sample
assert len(b) == w["n"] and int((b["NJ"] == 1).sum()) == w["n_nj"] and int((b["NJ"] == 0).sum()) == w["n_pa"]
for s, tag in ((1, "nj"), (0, "pa")):
    assert int(((b["NJ"] == s) & (b["closed_perm"] == 1)).sum()) == w[f"n_closed_{tag}"]
p05, p95 = np.percentile(b["DFTE"].to_numpy(float), [5, 95], method="linear")
assert abs(p05 - q05) < TOL and abs(p95 - q95) < TOL
with open("runs/h2-winsor/capped.csv", newline="", encoding="utf-8") as fh:
    logged = {(int(r["ROW_ID"]), r["tail"]) for r in csv.DictReader(fh)}
mine = {(int(i), "low") for i in b.loc[b["DFTE"] < q05, "ROW_ID"]} | \
       {(int(i), "high") for i in b.loc[b["DFTE"] > q95, "ROW_ID"]}
assert mine == logged, "stores beyond the cutoffs differ from runs/h2-winsor/capped.csv"
for s, tag in ((1, "nj"), (0, "pa")):
    x = b.loc[b["NJ"] == s, "DFTE"]
    assert abs(x.mean() - t3[f"chg_r4_{tag}"]) < TOL
    assert abs(x.std(ddof=1) / np.sqrt(len(x)) - t3[f"chg_r4_{tag}_se"]) < TOL

# ---- figure (bins that straddle a cutoff are drawn whole; the shading marks the capped region)
plt = mpl_setup()
lo = np.floor((b["DFTE"].min() - OFFSET) / BIN) * BIN + OFFSET
hi = np.ceil((b["DFTE"].max() - OFFSET) / BIN) * BIN + OFFSET
edges = np.arange(lo, hi + BIN / 2, BIN)
assert edges[0] <= b["DFTE"].min() and edges[-1] >= b["DFTE"].max()

fig, axes = plt.subplots(2, 1, figsize=(5.6, 3.9), sharex=True,
                         gridspec_kw={"height_ratios": [1.6, 1.0], "hspace": 0.32})
panel = [(1, "nj", "New Jersey"), (0, "pa", "Pennsylvania")]
out_counts: dict = {}
for ax, (s, tag, name) in zip(axes, panel):
    x = b[b["NJ"] == s]
    open_, closed = x.loc[x["closed_perm"] == 0, "DFTE"], x.loc[x["closed_perm"] == 1, "DFTE"]
    h_open, _ = np.histogram(open_, edges)
    h_closed, _ = np.histogram(closed, edges)
    assert h_open.sum() + h_closed.sum() == len(x)
    mids, width = edges[:-1] + BIN / 2, BIN * 0.92
    ymax = int((h_open + h_closed).max())
    top = ymax * 1.42
    # tails beyond the cutoffs (capped by the winsorization)
    ax.axvspan(edges[0] - BIN, q05, color=LIGHT, alpha=0.55, lw=0, zorder=0)
    ax.axvspan(q95, edges[-1] + BIN, color=LIGHT, alpha=0.55, lw=0, zorder=0)
    ax.bar(mids, h_open, width=width, color=BLUE, edgecolor="white", lw=0.3, zorder=2,
           label="Stores open in wave 2")
    k = h_closed > 0      # draw closure segments only where there are closures
    ax.bar(mids[k], h_closed[k], width=width, bottom=h_open[k], color="white",
           edgecolor=VERMILLION, hatch="////", lw=0.6, zorder=2,
           label=r"Permanently closed (wave-2 FTE $=0$)")
    for q in (q05, q95):
        ax.axvline(q, color=INK, ls=(0, (4, 2)), lw=0.8, zorder=3)
    # state mean change (row 4) with mean +/- 1.96 x S1 SE
    mu, se = t3[f"chg_r4_{tag}"], t3[f"chg_r4_{tag}_se"]
    y_mu = ymax * 1.22
    ax.errorbar([mu], [y_mu], xerr=[[Z95 * se], [Z95 * se]], fmt="D", ms=3.2, color=INK,
                mfc="white", mew=0.8, elinewidth=0.9, capsize=2.2, zorder=4)
    ax.annotate(f"mean {num(mu, '.2f').replace('-', '−')}", (mu, y_mu), xytext=(6, 3),
                textcoords="offset points", fontsize=7, va="bottom", ha="left")
    n_low, n_high = w[f"capped_low_{tag}"], w[f"capped_high_{tag}"]
    ax.text(q05 - 0.8, top * 0.97, f"{n_low} capped", ha="right", va="top", fontsize=7)
    ax.text(q95 + 0.8, top * 0.97, f"{n_high} capped", ha="left", va="top", fontsize=7)
    ax.set_ylim(0, top)
    ax.set_ylabel("Stores")
    ax.set_title(f"{name} ({len(x)} stores, {int(len(closed))} permanently closed)", loc="left",
                 fontsize=8, pad=3)
    ax.yaxis.get_major_locator().set_params(integer=True)
    out_counts[f"n_{tag}"] = int(len(x))
    out_counts[f"max_bin_{tag}"] = ymax

for q, side, label in ((q05, 1, "pooled 5th pct."), (q95, -1, "pooled 95th pct.")):
    axes[0].text(q + side * 0.6, axes[0].get_ylim()[1] * 0.62,
                 f"{label} {num(q, '.2f').replace('-', '−')}", rotation=90,
                 ha="left" if side > 0 else "right", va="center", fontsize=7)
axes[-1].set_xlabel("Change in FTE employment per store, wave 2 minus wave 1 (balanced sample)")
axes[-1].set_xlim(edges[0] - 0.5, edges[-1] + 0.5)
handles, labels = axes[0].get_legend_handles_labels()
handles += [Line2D([], [], color=INK, ls=(0, (4, 2)), lw=0.8),
            Patch(facecolor=LIGHT, alpha=0.55, edgecolor="none"),
            Line2D([], [], marker="D", ms=3.2, color=INK, mfc="white", lw=0.9)]
labels += ["Pooled 5th / 95th percentile", "Capped (winsorized) region",
           r"State mean $\pm$ 1.96 SE"]
fig.legend(handles, labels, loc="upper center", bbox_to_anchor=(0.5, 0.0), frameon=False,
           ncol=3, handlelength=1.8, columnspacing=1.2, labelcolor=INK)
for ax in axes:
    ax.tick_params(length=2.5)

save_pdf(fig, args.out)
write_metrics(args.metrics, {**out_counts, "n": int(len(b)), "bin_width": BIN, "n_bins": int(len(edges) - 1),
                             "x_min_edge": float(edges[0]), "x_max_edge": float(edges[-1]),
                             "n_capped_checked": len(logged)})
print(f"wrote {args.out}: {len(b)} stores, {len(edges) - 1} bins, {len(logged)} capped stores checked")
