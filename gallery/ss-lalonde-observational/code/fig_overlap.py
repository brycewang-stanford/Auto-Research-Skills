"""Figure: overlap of the cross-fitted propensity score, NSW-treated men vs CPS-1 men.

Reads runs/diag-overlap/propensity.csv (m_bar for every unit: the mean over the 5
repetitions of the out-of-fold propensity on B(X), unclipped; covariates and treatment only,
computed before the design gate) and runs/diag-overlap/metrics.json (arm sizes, the treated
m_bar range and rob-trim's dropped and kept counts). Writes paper/figures/fig_overlap.pdf.
Nothing is re-estimated.

The horizontal axis is log10(m_bar), because almost every CPS man has m_bar far below
0.01. Bars show the percent of each group per bin (counts would hide the 185 treated men
next to 15,992 CPS men); the treated are drawn above the axis, the CPS men below. The bin
edges are laid out from the lowest treated m_bar, so that no bin straddles rob-trim's
cutoff. The shaded region is the trimming region of rob-trim (method.control_only_trimming):
CPS men whose m_bar lies outside [min, max] of the treated men's m_bar.
"""
from __future__ import annotations

import argparse
import bisect
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import BLUE, INK, LIGHT, MUTED, VERMILLION, load_metrics, mpl_setup, num, save_pdf, write_metrics  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_overlap.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

D = load_metrics("diag-overlap")
treated, control = [], []
with open("runs/diag-overlap/propensity.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        (treated if int(row["treat"]) == 1 else control).append(float(row["m_bar"]))
assert len(treated) == D["n_treated"] and len(control) == D["n_control"], "propensity.csv does not match the arm sizes"
lo, hi = D["m_bar_min_treated"], D["m_bar_max_treated"]
assert math.isclose(min(treated), lo, rel_tol=1e-9) and math.isclose(max(treated), hi, rel_tol=1e-9)
n_drop_below = sum(1 for m in control if m < lo)
n_drop_above = sum(1 for m in control if m > hi)
assert n_drop_below == D["trim_n_control_dropped_below"] and n_drop_above == D["trim_n_control_dropped_above"], \
    "trimming region does not reproduce diag-overlap's rob-trim count"
assert n_drop_below + n_drop_above == D["trim_n_control_dropped"]
n_kept = D["trim_n_control_kept"]
assert n_kept == len(control) - D["trim_n_control_dropped"]

# Bins of width 0.25 in log10(m_bar), with one edge exactly at log10 of the lowest treated m_bar
# as stored in propensity.csv (12 significant digits; it equals diag-overlap's metric to 1e-9).
W = 0.25
cut = math.log10(min(treated))
lt = [math.log10(m) for m in treated]
lc = [math.log10(m) for m in control]
k_lo = math.floor((min(lc + lt) - cut) / W)
k_hi = math.ceil((max(lc + lt) - cut) / W)
edges = [cut + W * k for k in range(k_lo, k_hi + 1)]


def pct(vals: list[float]) -> list[float]:
    counts = [0] * (len(edges) - 1)
    for v in vals:
        i = min(bisect.bisect_right(edges, v) - 1, len(counts) - 1)
        counts[i] += 1
    assert sum(counts) == len(vals)
    return [100.0 * c / len(vals) for c in counts]


pt, pc = pct(lt), pct(lc)

plt = mpl_setup()
fig, ax = plt.subplots(figsize=(6.0, 3.0))
x0, x1 = edges[0], max(edges[-1], 0.0)
ax.axvspan(x0, cut, color=LIGHT, alpha=0.55, lw=0, zorder=0)
if math.log10(hi) < x1:
    ax.axvspan(math.log10(hi), x1, color=LIGHT, alpha=0.55, lw=0, zorder=0)
ax.bar(edges[:-1], pt, width=W, align="edge", color=BLUE, edgecolor="white", lw=0.4, zorder=2,
       label=f"NSW-treated men, n = {len(treated):,} (above the axis)")
ax.bar(edges[:-1], [-v for v in pc], width=W, align="edge", color="white", edgecolor=VERMILLION,
       lw=0.6, hatch="////", zorder=2, label=f"CPS-1 men, n = {len(control):,} (below the axis)")
ax.axhline(0, color=INK, lw=0.6, zorder=3)
for x in (cut, math.log10(hi)):
    ax.axvline(x, color=INK, lw=0.8, ls=(0, (4, 2)), zorder=3)

top = max(pt) * 1.45
bot = max(pc) * 2.3
ax.set_ylim(-bot, top)
ax.set_xlim(x0, x1)
ticks = list(range(math.ceil(x0), 1))
ax.set_xticks(ticks)
ax.set_xticklabels([("1" if t == 0 else f"$10^{{{t}}}$") for t in ticks])
yt = [v for v in range(-40, 41, 5) if -bot <= v <= top]
ax.set_yticks(yt)
ax.set_yticklabels([f"{abs(v)}" for v in yt])
ax.set_xlabel(r"Cross-fitted propensity score $\bar m(X)$ (log scale; mean over 5 repetitions, unclipped)")
ax.set_ylabel("Percent of group per bin\n(treated above, CPS below)")
ax.grid(axis="y", color="#e6e6e6", lw=0.5, zorder=0)

ax.text((x0 + cut) / 2, -bot * 0.93,
        f"trimming region of rob-trim:\n{num(n_drop_below, ',d')} CPS men dropped",
        ha="center", va="bottom", fontsize=7, color=INK)
mant, expo = f"{lo:.2e}".split("e")
ax.annotate(f"lowest treated $\\bar m$\n(${mant} \\times 10^{{{int(expo)}}}$)",
            xy=(cut, top * 0.86), xytext=(cut + 0.15, top * 0.86), ha="left", va="center", fontsize=7)
ax.annotate(f"highest treated $\\bar m$ ({num(hi, '.3f')});\nno CPS man above it",
            xy=(math.log10(hi), top * 0.86), xytext=(math.log10(hi) - 0.15, top * 0.86),
            ha="right", va="center", fontsize=7)
ax.text(cut + 0.15, -bot * 0.93, f"kept: {num(n_kept, ',d')} CPS men, all {len(treated)} treated men",
        ha="left", va="bottom", fontsize=7, color=INK)
ax.legend(loc="upper left", frameon=False, bbox_to_anchor=(0.0, 1.17), ncol=2, fontsize=7.2)
fig.tight_layout()
save_pdf(fig, args.out)

write_metrics(args.metrics, {
    "n_treated_plotted": len(treated), "n_control_plotted": len(control),
    "bin_width_log10": W, "n_bins": len(edges) - 1,
    "log10_cutoff_low": cut, "log10_cutoff_high": math.log10(hi),
    "n_control_in_trimming_region": n_drop_below + n_drop_above,
    "n_control_kept": n_kept,
    "max_pct_treated_bin": max(pt), "max_pct_control_bin": max(pc),
})
