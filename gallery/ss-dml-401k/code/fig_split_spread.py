"""Figure: split-to-split spread of the replicated estimates against the spread the published
SEs imply, per learner and K (analysis plan 9(a); task f-splits).

Reads runs/main-<learner>/splits.csv (theta_s of every split), runs/main-<learner>/metrics.json
(replicated median, number of splits) and runs/verdict/metrics.json (published estimate,
difference, tolerance, replicated 1.4826 x MAD and the published-implied 1.4826 x
sqrt(adj^2 - med^2)). Writes paper/figures/fig_split_spread.pdf. Nothing is estimated here:
theta_s minus the published estimate is only a shift of the plotted points.
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import (BLUE, FOLDS, INK, LEARNERS, LIGHT, MUTED, NAME, VERMILLION,  # noqa: E402
                    cell_key, finite, load_metrics, mpl_setup, save_pdf, write_metrics)

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_split_spread.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

v = load_metrics("verdict")
rows = []
n_points = 0
for learner in LEARNERS:
    r = load_metrics(f"main-{learner}")
    with open(f"runs/main-{learner}/splits.csv", newline="", encoding="utf-8") as fh:
        splits = list(csv.DictReader(fh))
    for k in FOLDS:
        c = cell_key(learner, k)
        theta_s = [float(s["theta"]) for s in splits if int(s["K"]) == k]
        assert len(theta_s) == r["n_splits"], (learner, k, len(theta_s))
        # The logged estimate is the median over splits (eq. 3.14); check the file agrees.
        assert abs(statistics.median(theta_s) - r[f"theta_k{k}"]) < 1e-3, (learner, k)
        assert v[f"split_sd_obs_{c}"] == r[f"split_sd_obs_k{k}"]
        pub = v[f"pub_theta_{c}"]
        rows.append(dict(learner=learner, k=k, S=r["n_splits"], pts=[t - pub for t in theta_s],
                         diff=v[f"diff_{c}"], tol=v[f"tolerance_{c}"],
                         sd_obs=v[f"split_sd_obs_{c}"], sd_pub=v[f"split_sd_pub_{c}"]))
        assert finite(rows[-1]["diff"], rows[-1]["tol"], rows[-1]["sd_obs"], rows[-1]["sd_pub"])
        n_points += len(theta_s)

plt = mpl_setup()
fig, (ax, bx) = plt.subplots(1, 2, figsize=(6.5, 3.9), sharey=True,
                             gridspec_kw={"width_ratios": [2.6, 1.0], "wspace": 0.08})

ys, y = [], 0.0
for i, row in enumerate(rows):
    if i and row["k"] == FOLDS[0]:
        y += 0.6
    ys.append(-y)
    y += 1.0

off = 0.2
for row, yy in zip(rows, ys):
    ax.fill_between([-row["tol"], row["tol"]], yy - 0.42, yy + 0.42, color=LIGHT, lw=0, zorder=1)
    ax.plot(row["pts"], [yy + off] * len(row["pts"]), ls="", marker="|", ms=5, mew=0.5,
            color=MUTED, alpha=0.75, zorder=2)
    # replicated: median and +/- 1.4826 x MAD of theta_s (solid)
    ax.plot([row["diff"] - row["sd_obs"], row["diff"] + row["sd_obs"]], [yy + off] * 2,
            color=BLUE, lw=1.6, solid_capstyle="butt", zorder=3)
    ax.plot(row["diff"], yy + off, "D", ms=3.6, mfc=BLUE, mec="white", mew=0.5, zorder=4)
    # published: estimate (zero on this axis) and +/- the spread its SEs imply (dashed)
    ax.plot([-row["sd_pub"], row["sd_pub"]], [yy - off] * 2, color=VERMILLION, lw=1.2,
            ls=(0, (3, 1.5)), zorder=3)
    for x in (-row["sd_pub"], row["sd_pub"]):
        ax.plot([x, x], [yy - off - 0.1, yy - off + 0.1], color=VERMILLION, lw=0.9, zorder=3)
    ax.plot(0, yy - off, "s", ms=3.6, mfc="white", mec=VERMILLION, mew=0.9, zorder=4)

    bx.plot([row["sd_obs"], row["sd_pub"]], [yy, yy], color=MUTED, lw=0.6, zorder=1)
    bx.plot(row["sd_obs"], yy, "o", ms=4.4, mfc=BLUE, mec=BLUE, zorder=3)
    bx.plot(row["sd_pub"], yy, "s", ms=4.2, mfc="white", mec=VERMILLION, mew=0.9, zorder=3)

ax.axvline(0, color=INK, lw=0.5, zorder=0)
lim = 1.06 * max(max(abs(p) for p in row["pts"]) for row in rows)
lim = max(lim, 1.06 * max(row["sd_pub"] for row in rows))
ax.set_xlim(-lim, lim)
ax.set_ylim(min(ys) - 0.7, max(ys) + 0.7)
ax.set_yticks(ys)
ax.set_yticklabels([f"{NAME[r['learner']]}, $K$ = {r['k']} ($S$ = {r['S']})" for r in rows])
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
ax.set_xlabel("Estimate $-$ published estimate (1991 US dollars)")
ax.set_title("(a) Per-split estimates against the published estimate", loc="left")

bx.set_xlim(0, 1.08 * max(max(r["sd_obs"], r["sd_pub"]) for r in rows))
bx.tick_params(axis="y", length=0)
bx.spines["left"].set_visible(False)
bx.set_xlabel("Split-to-split SD (1991 US dollars)")
bx.set_title("(b) Spread: replicated vs published", loc="left")

from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
handles = [
    Line2D([], [], ls="", marker="|", ms=6, mew=0.6, color=MUTED, label="one split ($\\theta_s$)"),
    Line2D([], [], color=BLUE, lw=1.6, marker="D", ms=3.6, mfc=BLUE, mec="white",
           label="replicated median $\\pm$ 1.4826 MAD"),
    Line2D([], [], color=VERMILLION, lw=1.2, ls=(0, (3, 1.5)), marker="s", ms=3.6, mfc="white",
           mec=VERMILLION, label="published estimate $\\pm$ SD implied by its SEs"),
    Patch(facecolor=LIGHT, lw=0, label="H2 tolerance"),
]
fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.06), ncol=4, frameon=False,
           handlelength=1.8, columnspacing=1.1)
save_pdf(fig, args.out)

write_metrics(args.metrics, {
    "n_cells": len(rows),
    "n_split_points": n_points,
    "x_limit_a": lim,
})
print(f"wrote {args.out}: {len(rows)} cells, {n_points} split estimates")
