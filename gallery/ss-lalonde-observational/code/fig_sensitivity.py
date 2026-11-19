"""Figure: Imbens (2003) sensitivity contour for sens-imbens, with the benchmark groups.

Reads runs/sens-imbens/metrics.json only: the 8 x 8 grid of bias for both signs of delta,
the diagonal points, the target t_0, the diagonal breakdown point R2*_0, the AIPW estimate
the run used, and the eight benchmark points with their |bias|. Writes
paper/figures/fig_sensitivity.pdf. Nothing is re-fitted.

The shading and contour lines are the larger |bias| of the two signs of U's outcome effect
at each of the 64 logged grid points (R2_D, R2_Y in {0, .01, .02, .05, .10, .15, .20, .30};
method.sensitivity), interpolated linearly between grid points by matplotlib's contouring.
The planned target t_0 is the only level the reading rule uses; the second level, the AIPW
point estimate itself, is drawn for orientation (a |bias| that large would move the point
estimate to zero) and is not part of the rule. Both axes use a square-root scale so that the
small R2 values near the origin, where t_0 is reached, are visible; tick labels are R2 values.

Benchmark groups are placed at the strengths (R2_D(G), R2_Y(G)) the run logged; two of them
(age, earnings75) have R2_D above the planned grid's 0.30, so the horizontal axis extends past
the grid, the region outside it is hatched and has no surface, and their |bias| is the EM fit
at the benchmark point (which is what the reading rule uses), as for every group. Groups whose
logged R2_D is exactly 0 (black, married, nodegree) are drawn with a different, open marker:
the design floors R2_D at 0, so their rule verdict ('robust') carries no information about
those confounders.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import INK, MUTED, VERMILLION, load_metrics, mpl_setup, num, save_pdf, write_metrics  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_sensitivity.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

S = load_metrics("sens-imbens")
GRID = [0, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3]  # design.method.sensitivity
DIAG = [0.0025, 0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.1, 0.15, 0.2, 0.3]
GROUPS = [("age", "age"), ("educ", "educ"), ("black", "black"), ("hisp", "hisp"),
          ("married", "married"), ("nodegree", "nodegree"), ("earn74", "earnings74"),
          ("earn75", "earnings75")]


def gkey(d: float, y: float, sign: str) -> str:
    return f"grid_d{d:g}_y{y:g}_{sign}_bias"


Z = [[max(abs(S[gkey(d, y, "pos")]), abs(S[gkey(d, y, "neg")])) for d in GRID] for y in GRID]
for r in DIAG:  # every diagonal point is logged
    assert f"diag_{r:g}_pos_bias" in S and f"diag_{r:g}_neg_bias" in S
t0 = S["target_zero"]
est = S["aipw_effect"]
assert 0 < t0 < est
zmax = max(max(row) for row in Z)
bench = []
for key, name in GROUPS:
    b = {"key": key, "name": name, "r2d": S[f"bench_{key}_r2d"], "r2y": S[f"bench_{key}_r2y"],
         "bias": S[f"bench_{key}_abs_bias"], "robust": S[f"robust_zero_{key}"]}
    assert b["bias"] == max(abs(S[f"bench_{key}_pos_bias"]), abs(S[f"bench_{key}_neg_bias"]))
    assert b["robust"] == (b["bias"] < t0)
    b["floored"] = b["r2d"] == 0.0
    bench.append(b)
floored = [b for b in bench if b["floored"]]
shown = [b for b in bench if not b["floored"]]
assert all(b["robust"] for b in floored), "a floored group is not 'robust'; revisit the marking"
xmax_data = max([GRID[-1]] + [b["r2d"] for b in bench])
ymax_data = max([GRID[-1]] + [b["r2y"] for b in bench])
XMAX = math.ceil(xmax_data * 10 + 0.5) / 10  # next tenth above the largest R2_D, with room
YMAX = ymax_data

plt = mpl_setup()
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402


def fwd(v):
    import numpy as np
    return np.sqrt(np.clip(v, 0, None))


def inv(v):
    return v ** 2


fig, ax = plt.subplots(figsize=(5.6, 4.1))
ax.set_xscale("function", functions=(fwd, inv))
ax.set_yscale("function", functions=(fwd, inv))
fills = ["#ffffff", "#cfe1f0", "#86b3d6"]
ax.contourf(GRID, GRID, Z, levels=[0, t0, est, zmax * 1.001], colors=fills, zorder=0)
ax.contour(GRID, GRID, Z, levels=[t0], colors=[INK], linewidths=0.9, linestyles=["--"], zorder=2)
ax.contour(GRID, GRID, Z, levels=[est], colors=[INK], linewidths=0.9, linestyles=["-"], zorder=2)
ax.add_patch(Rectangle((GRID[-1], 0), XMAX - GRID[-1], YMAX, fill=False, hatch="....", ec=MUTED,
                       lw=0, zorder=0))
ax.axvline(GRID[-1], color=MUTED, lw=0.6, zorder=1)
BOX = {"fc": "white", "ec": "none", "pad": 0.8, "alpha": 0.9}
ax.text(math.sqrt(GRID[-1] * XMAX), YMAX * 0.93, "outside the\nplanned grid\n(no surface)",
        ha="center", va="top", fontsize=6.6, color=INK,
        bbox={"fc": "white", "ec": "none", "pad": 1.0})
gx = [d for d in GRID for _ in GRID]
gy = [y for _ in GRID for y in GRID]
ax.plot(gx, gy, ls="", marker=".", ms=1.8, color=MUTED, zorder=1, clip_on=False)
ax.plot([0, GRID[-1]], [0, GRID[-1]], color=MUTED, lw=0.6, ls=(0, (1, 2)), zorder=1)
r0 = S["r2star_zero"]
assert not S["r2star_zero_out_of_grid"]
ax.plot([r0], [r0], marker="D", ms=4.0, color=VERMILLION, mec="white", mew=0.5, zorder=5)
ax.annotate(f"$R^2_{{*,0}}$ = {S['r2star_zero_text']} on the diagonal", xy=(r0, r0), xytext=(0.012, 0.0035),
            fontsize=6.8, ha="left", va="center", color=INK, bbox=BOX,
            arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.5, "shrinkA": 1, "shrinkB": 3})

# Label offsets in points, chosen so no two labels collide.
OFFS = {"earn75": (-6, 8, "right"), "age": (-6, -9, "right"), "earn74": (6, 6, "left"),
        "educ": (6, -6, "left"), "hisp": (6, -1, "left")}
for b in shown:
    ax.plot([b["r2d"]], [b["r2y"]], marker="o", ms=4.6, color=INK, mec="white", mew=0.5, zorder=6, clip_on=False)
    dx, dy, ha = OFFS[b["key"]]
    ax.annotate(f"{b['name']}  |bias| {num(b['bias'])}", xy=(b["r2d"], b["r2y"]), xytext=(dx, dy),
                textcoords="offset points", ha=ha, va="center", fontsize=6.8, zorder=7, bbox=BOX)
for b in floored:
    ax.plot([b["r2d"]], [b["r2y"]], marker="s", ms=4.2, color=INK, mfc="white", mew=0.9, zorder=6, clip_on=False)
ytop = max(b["r2y"] for b in floored)
ax.annotate(", ".join(b["name"] for b in floored) + ": $R^2_D$ floored at 0,\nso no information (not evidence of robustness)",
            xy=(0, ytop), xytext=(0.0035, 0.045), fontsize=6.8, ha="left", va="center", bbox=BOX,
            arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.5, "shrinkA": 1, "shrinkB": 3})

ticks = [0, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3] + [v / 10 for v in range(4, int(round(XMAX * 10)) + 1)]
ax.set_xticks(ticks)
ax.set_xticklabels([f"{t:g}" for t in ticks])
yt = [0, 0.001, 0.01, 0.02, 0.05, 0.1, 0.2, 0.3]
ax.set_yticks(yt)
ax.set_yticklabels([f"{t:g}" for t in yt])
ax.set_xlim(0, XMAX)
ax.set_ylim(0, YMAX)
ax.set_xlabel(r"$R^2_D$: share of residual latent participation variance explained by $U$ (square-root scale)")
ax.set_ylabel(r"$R^2_Y$: share of residual re78 variance" + "\n" + r"explained by $U$ (square-root scale)")

handles = [Line2D([], [], color=INK, lw=0.9, ls="--", label=f"$t_0$ = {num(t0, ',.1f')} (reading rule)"),
           Line2D([], [], color=INK, lw=0.9, ls="-", label=f"point estimate {num(est)} (orientation only)"),
           Patch(fc=fills[1], ec=MUTED, lw=0.4, label=r"$t_0 \leq$ |bias| < estimate"),
           Patch(fc=fills[2], ec=MUTED, lw=0.4, label=r"|bias| $\geq$ estimate"),
           Line2D([], [], ls="", marker="o", color=INK, mec="white", label="benchmark group"),
           Line2D([], [], ls="", marker="s", color=INK, mfc="white", label=r"benchmark, $R^2_D$ floored at 0"),
           Line2D([], [], ls="", marker="D", color=VERMILLION, mec="white", label=r"$R^2_{*,0}$ (diagonal)"),
           Line2D([], [], ls="", marker=".", color=MUTED, label="grid point (EM fit)")]
fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=6.8,
           bbox_to_anchor=(0.5, -0.17), columnspacing=1.0, handlelength=1.8)
fig.tight_layout()
save_pdf(fig, args.out)

write_metrics(args.metrics, {
    "n_grid_points": len(GRID) ** 2, "n_benchmarks_plotted": len(bench),
    "n_benchmarks_floored": len(floored), "floored_groups": ",".join(b["key"] for b in floored),
    "n_benchmarks_outside_grid": sum(1 for b in bench if b["r2d"] > GRID[-1] or b["r2y"] > GRID[-1]),
    "target_zero": t0, "contour_estimate": est, "r2star_zero": r0,
    "max_abs_bias_grid": zmax, "x_max": XMAX, "y_max": YMAX,
    "checksum_plotted": sum(sum(r) for r in Z) + sum(b["bias"] + b["r2d"] + b["r2y"] for b in bench),
})
