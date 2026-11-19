"""Figure: replicated minus published estimate per cell, with the H2 tolerance and the
80%-power detectable shift.

Reads runs/verdict/metrics.json (difference, tolerance, testability, H2 status, port-check
result and shift) and runs/main-<learner>/metrics.json (80%-power detectable shift).
Writes paper/figures/fig_h2_diff.pdf. Nothing is estimated here.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import (BLUE, FOLDS, INK, LEARNERS, LIGHT, MUTED, NAME, VERMILLION,  # noqa: E402
                    cell_key, finite, load_metrics, money, mpl_setup, save_pdf, write_metrics)

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_h2_diff.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

v = load_metrics("verdict")
rows = []  # top to bottom
for learner in LEARNERS:
    r = load_metrics(f"main-{learner}")
    for k in FOLDS:
        c = cell_key(learner, k)
        assert v[f"tolerance_{c}"] == r[f"tolerance_k{k}"] and v[f"testable_{c}"] == r[f"testable_k{k}"]
        rows.append(dict(learner=learner, k=k, diff=v[f"diff_{c}"], tol=v[f"tolerance_{c}"],
                         mds=r[f"mds80_k{k}"], testable=v[f"testable_{c}"],
                         inside=v[f"h2_inside_{c}"], port_ok=v[f"port_pass_{learner}"]))
        assert finite(rows[-1]["diff"], rows[-1]["tol"], rows[-1]["mds"])
        assert rows[-1]["inside"] == (abs(rows[-1]["diff"]) <= rows[-1]["tol"])

plt = mpl_setup()
fig, ax = plt.subplots(figsize=(6.3, 3.5))

# y positions: two rows per learner with a gap between learners, first learner on top.
ys, y = [], 0.0
for i, row in enumerate(rows):
    if i and row["k"] == FOLDS[0]:
        y += 0.6
    ys.append(-y)
    y += 1.0

half = 0.32
for row, yy in zip(rows, ys):
    ax.fill_between([-row["tol"], row["tol"]], yy - half, yy + half, color=LIGHT, lw=0, zorder=1)
    ax.plot([-row["tol"], -row["tol"]], [yy - half, yy + half], color=MUTED, lw=0.6, zorder=2)
    ax.plot([row["tol"], row["tol"]], [yy - half, yy + half], color=MUTED, lw=0.6, zorder=2)
    for x in (-row["mds"], row["mds"]):
        ax.plot([x, x], [yy - half * 0.9, yy + half * 0.9], color=INK, lw=0.9, ls=(0, (2, 1.2)), zorder=2)
    if row["testable"]:
        ax.plot(row["diff"], yy, "o", ms=4.6, mfc=BLUE, mec=BLUE, mew=0.8, zorder=4)
    else:
        ax.plot(row["diff"], yy, "o", ms=4.6, mfc="white", mec=INK, mew=0.9, zorder=4)
    note = "inside, not testable" if not row["testable"] else ("inside" if row["inside"] else "outside")
    ax.text(1.015, yy, f"{money(row['diff'])}  /  ±{money(row['tol'])}   {note}",
            transform=ax.get_yaxis_transform(), va="center", ha="left", fontsize=7, clip_on=False)

ax.axvline(0, color=INK, lw=0.6, zorder=3)
lim = 1.12 * max(r["mds"] for r in rows)
ax.set_xlim(-lim, lim)
ax.set_ylim(min(ys) - 0.7, max(ys) + 0.7)
ax.set_yticks(ys)
ax.set_yticklabels([f"{NAME[r['learner']]}, $K$ = {r['k']}" for r in rows])
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
ax.set_xlabel("Replicated $-$ published estimate (1991 US dollars)")
ax.text(1.015, max(ys) + 0.62, "diff.  /  tolerance   H2", transform=ax.get_yaxis_transform(),
        ha="left", va="bottom", fontsize=7, style="italic", clip_on=False)

# Forest: the port check failed before the gate (synthetic outcome; not plotted on this axis).
forest = [yy for row, yy in zip(rows, ys) if row["learner"] == "forest"]
n_port_failed = len({row["learner"] for row in rows if not row["port_ok"]})
assert n_port_failed == 1 and not rows[4]["port_ok"]
for yy in forest:
    ax.plot(-lim, yy, marker=">", ms=4, color=VERMILLION, clip_on=False, zorder=5)
ax.text(-lim * 0.985, min(forest) - 0.52,
        "▶ port check failed before the gate: Python $-$ R shift "
        f"{money(v['port_shift_forest'])} (SE {money(v['port_shift_se_forest'])}) "
        "in synthetic-outcome dollars, 2-fold training size",
        ha="left", va="center", fontsize=6.6, color=VERMILLION, zorder=6,
        bbox=dict(facecolor="white", edgecolor="none", pad=0.6))

from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
handles = [Patch(facecolor=LIGHT, edgecolor=MUTED, lw=0.6, label="H2 tolerance (acceptance interval)"),
           Line2D([], [], color=INK, lw=0.9, ls=(0, (2, 1.2)), label="± 80%-power detectable shift"),
           Line2D([], [], ls="", marker="o", ms=4.6, mfc=BLUE, mec=BLUE, label="testable cell"),
           Line2D([], [], ls="", marker="o", ms=4.6, mfc="white", mec=INK, label="not testable (lasso)")]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=4, frameon=False,
          handlelength=1.6, columnspacing=1.2)
save_pdf(fig, args.out)

write_metrics(args.metrics, {
    "n_cells": len(rows),
    "n_testable": sum(r["testable"] for r in rows),
    "n_inside": sum(r["inside"] for r in rows),
    "n_learners_port_failed": n_port_failed,
    "x_limit": lim,
})
print(f"wrote {args.out}: {len(rows)} cells")
