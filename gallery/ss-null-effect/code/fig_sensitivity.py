"""Figure: Imbens (2003) sensitivity contour with every benchmark covariate group marked.

Reads runs/sens-imbens/metrics.json only (the 8 x 8 grid of bias for both signs of delta,
the diagonal R2* for each target, the three targets, and the nine benchmark points and
their |bias|). Writes paper/figures/fig_sensitivity.pdf.

The shaded surface and the contour lines are the larger |bias| of the two signs at each
of the 64 logged grid points, linearly interpolated between grid points by matplotlib's
contouring; nothing is re-fitted. The |bias| printed next to each benchmark is the value
the EM fit gave at that benchmark point (the value the reading rule uses), not a reading
of the interpolated surface.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import BLUE, INK, MUTED, VERMILLION, load_metrics, money, mpl_setup, save_pdf, write_metrics  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_sensitivity.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

S = load_metrics("sens-imbens")
GRID = [0, 0.01, 0.02, 0.05, 0.1, 0.15, 0.2, 0.3]  # design.method.sensitivity
GROUPS = [("age", "age"), ("educ", "educ"), ("married", "married"), ("urban", "urban"),
          ("region", "region"), ("children", "children"), ("health", "health_limit"),
          ("earn74", "earnings74"), ("earn75", "earnings75")]
TARGETS = [("equiv", r"$t_E$", ":"), ("zero", r"$t_0$", "--"), ("margin", r"$M$", "-")]


def gkey(d: float, y: float, sign: str) -> str:
    return f"grid_d{d:g}_y{y:g}_{sign}_bias"


# Z[i][j]: larger |bias| of the two signs at R2_Y = GRID[i], R2_D = GRID[j].
Z = [[max(abs(S[gkey(d, y, "pos")]), abs(S[gkey(d, y, "neg")])) for d in GRID] for y in GRID]
targets = {k: S[f"target_{k}"] for k, _, _ in TARGETS}
assert targets["margin"] == S["margin_M"]
assert targets["equiv"] < targets["zero"] < targets["margin"], "targets out of the expected order"
zmax = max(max(row) for row in Z)
bench = []
for key, name in GROUPS:
    b = {"key": key, "name": name, "r2d": S[f"bench_{key}_r2d"], "r2y": S[f"bench_{key}_r2y"],
         "bias": S[f"bench_{key}_abs_bias"]}
    assert b["bias"] == max(abs(S[f"bench_{key}_pos_bias"]), abs(S[f"bench_{key}_neg_bias"]))
    assert 0 <= b["r2d"] <= GRID[-1] and 0 <= b["r2y"] <= GRID[-1], f"{key} is outside the grid"
    bench.append(b)

plt = mpl_setup()
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

levels = [0, targets["equiv"], targets["zero"], targets["margin"], zmax * 1.001]
fills = ["#ffffff", "#e3eef7", "#bcd6ea", "#86b3d6"]
fig, axes = plt.subplots(1, 2, figsize=(6.6, 3.35), gridspec_kw={"width_ratios": [1.0, 1.0]})
ZOOM = (0.03, 0.075)  # (R2_D, R2_Y) upper limits of panel (b)
LABEL_POS_FULL = {"earn75": (0.150, 0.275, "left")}
# Panel (b): label positions (x, y, ha) in data units, fanned out so no two collide.
LABEL_POS_ZOOM = {
    "earn74": (0.0125, 0.069, "left"), "age": (0.0135, 0.029, "left"),
    "educ": (0.0215, 0.0145, "left"), "married": (0.0080, 0.0215, "left"),
    "urban": (0.0080, 0.0170, "left"), "children": (0.0080, 0.0125, "left"),
    "health": (0.0080, 0.0080, "left"), "region": (0.0080, 0.0035, "left"),
}

for p, ax in enumerate(axes):
    ax.contourf(GRID, GRID, Z, levels=levels, colors=fills, zorder=0)
    for k, lab, ls in TARGETS:
        ax.contour(GRID, GRID, Z, levels=[targets[k]], colors=[INK], linewidths=0.9,
                   linestyles=[ls], zorder=2)
    gx = [d for d in GRID for _ in GRID]
    gy = [y for _ in GRID for y in GRID]
    ax.plot(gx, gy, ls="", marker=".", ms=1.6, color=MUTED, zorder=1)
    lim = (GRID[-1], GRID[-1]) if p == 0 else ZOOM
    ax.plot([0, lim[0]], [0, lim[0]], color=MUTED, lw=0.6, ls=(0, (1, 2)), zorder=1)
    for k, lab, _ in TARGETS:
        r = S[f"r2star_{k}"]
        if not S[f"r2star_{k}_out_of_grid"] and r <= min(lim):
            ax.plot([r], [r], marker="D", ms=3.2, color=VERMILLION, mec="white", mew=0.4, zorder=4)
    for b in bench:
        if b["r2d"] > lim[0] or b["r2y"] > lim[1]:
            continue  # outside the enlarged panel; shown in (a)
        ax.plot([b["r2d"]], [b["r2y"]], marker="o", ms=4.2, color=INK, mec="white", mew=0.5, zorder=5,
                clip_on=False)
        pos = (LABEL_POS_FULL if p == 0 else LABEL_POS_ZOOM).get(b["key"])
        if pos is None:
            continue
        x, y, ha = pos
        ax.annotate(f"{b['name']}  |bias| {money(b['bias'])}", xy=(b["r2d"], b["r2y"]),
                    xytext=(x, y), ha=ha, va="center", fontsize=6.6, zorder=6,
                    arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.5,
                                "shrinkA": 1, "shrinkB": 2.5})
    ax.set_xlim(0, lim[0])
    ax.set_ylim(0, lim[1])
    ax.set_xlabel(r"$R^2_D$: share of residual enrolment variance explained by $U$")
    ax.grid(False)
axes[0].set_ylabel(r"$R^2_Y$: share of residual re78 variance explained by $U$")
axes[0].set_title("(a) full grid", loc="left")
axes[1].set_title("(b) enlarged: lower-left corner of (a)", loc="left")
axes[0].add_patch(__import__("matplotlib.patches", fromlist=["Rectangle"]).Rectangle(
    (0, 0), ZOOM[0], ZOOM[1], fill=False, ec=INK, lw=0.6, ls="-", zorder=7))
others = ", ".join(b["name"] for b in bench if b["key"] not in LABEL_POS_FULL)
axes[0].annotate(f"other {len(bench) - len(LABEL_POS_FULL)} groups, enlarged in (b):\n"
                 + others.replace("married, ", "married,\n").replace("children, ", "children,\n"),
                 xy=(ZOOM[0], ZOOM[1]), xytext=(0.10, 0.165), fontsize=6.4, ha="left", va="center",
                 zorder=7, arrowprops={"arrowstyle": "-", "color": MUTED, "lw": 0.5, "shrinkB": 0})

handles = [Line2D([], [], color=INK, lw=0.9, ls=ls,
                  label=f"{lab} = {money(targets[k])}") for k, lab, ls in TARGETS]
handles += [Patch(fc=fills[i], ec=MUTED, lw=0.4, label=lab) for i, lab in
            [(1, r"$t_E \leq$ |bias| $< t_0$"), (2, r"$t_0 \leq$ |bias| $< M$"), (3, r"|bias| $\geq M$")]]
handles += [Line2D([], [], ls="", marker="o", color=INK, mec="white", label="benchmark group"),
            Line2D([], [], ls="", marker="D", color=VERMILLION, mec="white", label=r"$R^2_*$ on the diagonal")]
fig.legend(handles=handles, loc="lower center", ncol=4, frameon=False, fontsize=6.8,
           bbox_to_anchor=(0.5, -0.12), columnspacing=1.0, handlelength=1.8)
fig.tight_layout(w_pad=1.5)
save_pdf(fig, args.out)

write_metrics(args.metrics, {
    "n_grid_points": len(GRID) ** 2, "n_benchmarks_plotted": len(bench),
    "target_equiv": targets["equiv"], "target_zero": targets["zero"], "target_margin": targets["margin"],
    "max_abs_bias_grid": zmax,
    "checksum_plotted": sum(sum(r) for r in Z) + sum(b["bias"] + b["r2d"] + b["r2y"] for b in bench),
})
