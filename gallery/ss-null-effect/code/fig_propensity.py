"""Figure: distribution of the cross-fitted propensity score by arm (overlap).

Reads runs/diag-overlap/propensity_hist.json (bin edges and counts of m_bar by arm) and
runs/diag-overlap/metrics.json (arm sizes, overlap counts) only. Writes
paper/figures/fig_propensity.pdf. Nothing is re-estimated.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import BLUE, INK, MUTED, VERMILLION, load_json, load_metrics, mpl_setup, save_pdf, write_metrics  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_propensity.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

H = load_json("runs/diag-overlap/propensity_hist.json")
D = load_metrics("diag-overlap")
edges, t, c = H["bin_edges"], H["treated"], H["control"]
assert len(edges) == len(t) + 1 == len(c) + 1
assert sum(t) == D["n_treated"] and sum(c) == D["n_control"], "histogram does not cover every unit"
width = edges[1] - edges[0]
lefts = edges[:-1]

plt = mpl_setup()
fig, ax = plt.subplots(figsize=(5.2, 2.9))
ax.bar(lefts, t, width=width, align="edge", color=BLUE, edgecolor="white", lw=0.5,
       label=f"Treated (enrolled), n = {D['n_treated']:,}", zorder=2)
ax.bar(lefts, [-x for x in c], width=width, align="edge", color="white", edgecolor=VERMILLION,
       lw=0.8, hatch="////", label=f"Controls (not enrolled), n = {D['n_control']:,}", zorder=2)
ax.axhline(0, color=INK, lw=0.6, zorder=3)
for x in (0.1, 0.9):
    ax.axvline(x, color=MUTED, lw=0.8, ls=(0, (4, 2)), zorder=1)
ymax = max(max(t), max(c))
top = ymax * 1.18
ax.set_ylim(-top, top)
ax.text(0.1, top * 0.97, " 0.1", ha="left", va="top", fontsize=7, color=MUTED)
ax.text(0.9, top * 0.97, "0.9 ", ha="right", va="top", fontsize=7, color=MUTED)
ax.set_xlim(edges[0], edges[-1])
ax.set_xticks([round(0.1 * k, 1) for k in range(11)])
ticks = [v for v in range(-400, 401, 100) if abs(v) <= top]
ax.set_yticks(ticks)
ax.set_yticklabels([f"{abs(v):,}" for v in ticks])
ax.set_xlabel(r"Cross-fitted propensity score $\bar m(X)$ (mean over 5 repetitions)")
ax.set_ylabel("Number of people\n(treated above, controls below)")
ax.grid(axis="y", color="#e6e6e6", lw=0.5, zorder=0)
ax.legend(loc="upper left", frameon=False, bbox_to_anchor=(0.0, 1.16), ncol=2)
fig.tight_layout()
save_pdf(fig, args.out)

write_metrics(args.metrics, {
    "n_bins": len(t), "bin_width": width,
    "n_treated_plotted": sum(t), "n_control_plotted": sum(c),
    "max_bin_count": ymax,
    "n_treated_above_09": D["n_treated_above_09"], "n_control_below_01": D["n_control_below_01"],
})
