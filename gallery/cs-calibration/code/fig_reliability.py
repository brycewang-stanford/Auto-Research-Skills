"""Figure: reliability diagrams per dataset and model, without recalibration and with isotonic
regression (run `fig-reliability`).

Reads the test-split predictions that run `main` wrote (results/preds/main/<dataset>_s<seed>.npz,
git-ignored, rebuilt by `main`) and runs/describe/metrics.json (seed mean and SD of the plug-in
ECE, and the mean number of non-empty bins, printed in each panel). Bins follow the rule of the
ECE itself (experiment.equal_mass_bins: 15 equal-mass bins on P(y=1), ties never split), applied
to the predictions pooled over the 10 seeds. Each point is one non-empty pooled bin: mean
prediction against observed positive rate. The error bar is plus or minus one SD across seeds of
the positive rate among that seed's rows in the bin. Marker area is proportional to the bin's
share of the pooled rows (equal-mass bins have share 1/15 unless tied predictions merge them).

As a check that the files are the predictions run `main` scored, the per-seed plug-in ECE is
recomputed from them and its seed mean compared with describe's (the largest absolute gap is a
metric of this run).

Writes paper/figures/fig_reliability.pdf.
"""
from __future__ import annotations

import argparse

import numpy as np

from experiment import N_BINS, SEEDS, ece, equal_mass_bins
from figlib import (BLUE, DATASETS, INK, LIGHT, MODEL_TEX, MODELS, MUTED, NAME, VERMILLION,
                    ds_key, load_metrics, mpl_setup, save_pdf, write_metrics)

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_reliability.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

D = load_metrics("describe")
assert D["n_seeds"] == len(SEEDS) == 10
CALS = ("none", "isotonic")
STYLE = {"none": dict(color=VERMILLION, marker="o", mfc=VERMILLION, ls="-", label="no recalibration"),
         "isotonic": dict(color=BLUE, marker="s", mfc="white", ls=(0, (3, 1.6)), label="isotonic")}
SHORT = {"none": "none", "isotonic": "iso"}


def load_preds(d: str):
    ys, ps, seeds = [], {f"{m}_{c}": [] for m in MODELS for c in CALS}, []
    for s in SEEDS:
        z = np.load(f"results/preds/main/{d}_s{s}.npz")
        y = z["y"]
        ys.append(y)
        seeds.append(np.full(len(y), s))
        for key in ps:
            p = z[f"p_{key}"]
            assert p.shape == y.shape
            ps[key].append(p)
    return ys, ps, seeds


def reliability(p: np.ndarray, y: np.ndarray, seed: np.ndarray):
    b = equal_mass_bins(p, N_BINS)
    pts = []
    for k in range(N_BINS):
        sel = b == k
        n = int(sel.sum())
        if n == 0:
            continue
        per_seed = [float(y[sel & (seed == s)].mean()) for s in SEEDS if np.any(sel & (seed == s))]
        sd = float(np.std(per_seed, ddof=1)) if len(per_seed) > 1 else 0.0
        pts.append((float(p[sel].mean()), float(y[sel].mean()), sd, n / len(p), len(per_seed)))
    return pts


plt = mpl_setup()
fig, axes = plt.subplots(len(DATASETS), len(MODELS), figsize=(6.3, 8.6), sharex=True, sharey=True)
out: dict = {"n_panels": len(DATASETS) * len(MODELS), "n_bins_rule": N_BINS}
n_points, checksum, max_gap, min_seeds_in_bin = 0, 0.0, 0.0, len(SEEDS)
for i, d in enumerate(DATASETS):
    ys, ps, seeds = load_preds(d)
    y_all, seed_all = np.concatenate(ys), np.concatenate(seeds)
    for j, model in enumerate(MODELS):
        ax = axes[i, j]
        ax.plot([0, 1], [0, 1], color=MUTED, lw=0.7, ls=(0, (1, 1.5)), zorder=1)
        lines = []
        for cal in CALS:
            key = f"{model}_{cal}"
            # check: these are the predictions run main scored
            per_seed_ece = [ece(p, y)[0] for p, y in zip(ps[key], ys)]
            base = f"{ds_key(d)}_{model}_{cal}"
            max_gap = max(max_gap, abs(float(np.mean(per_seed_ece)) - D[base + "_ece_mean"]))
            pts = reliability(np.concatenate(ps[key]), y_all, seed_all)
            xs, yv, sd, share, ns = (np.array(v) for v in zip(*pts))
            st = STYLE[cal]
            ax.errorbar(xs, yv, yerr=sd, color=st["color"], ls=st["ls"], lw=0.9, elinewidth=0.7,
                        capsize=1.4, zorder=3 if cal == "none" else 4)
            ax.scatter(xs, yv, s=10 * share * N_BINS, marker=st["marker"], facecolor=st["mfc"],
                       edgecolor=st["color"], linewidths=0.8, zorder=5, label=st["label"])
            out[f"{base}_pooled_bins"] = len(pts)
            n_points += len(pts)
            min_seeds_in_bin = min(min_seeds_in_bin, int(ns.min()))
            checksum += float(xs.sum() + yv.sum() + sd.sum() + share.sum())
            e_m, e_s, nb = (D[base + "_ece_mean"], D[base + "_ece_sd"], D[base + "_ece_bins_mean"])
            checksum += e_m + e_s + nb
            lines.append(f"{SHORT[cal]}: ECE {e_m:.4f} ({e_s:.4f}), {nb:.1f} bins")
        ax.text(0.03, 0.97, "\n".join(lines), transform=ax.transAxes, ha="left", va="top",
                fontsize=6, color=INK, linespacing=1.35,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=LIGHT, lw=0.5))
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_aspect("equal")
        ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_yticks([0, 0.25, 0.5, 0.75, 1])
        ax.set_xticklabels(["0", ".25", ".5", ".75", "1"])
        ax.set_yticklabels(["0", ".25", ".5", ".75", "1"])
        ax.grid(color="#efefef", lw=0.5, zorder=0)
        if i == 0:
            ax.set_title(MODEL_TEX[model], fontsize=9)
        if j == 0:
            ax.set_ylabel(f"{NAME[d]}\nobserved positive rate")
        if i == len(DATASETS) - 1:
            ax.set_xlabel("mean predicted P(y=1)")
handles, labels = axes[0, 0].get_legend_handles_labels()
fig.legend(handles, labels, loc="upper center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 1.015),
           markerscale=1.6)
fig.tight_layout(h_pad=0.6, w_pad=0.4)
save_pdf(fig, args.out)

out.update({"n_points": n_points, "checksum_plotted": checksum, "ece_matches_describe_1e12": int(max_gap < 1e-12),
            "min_seeds_in_bin": min_seeds_in_bin})
assert max_gap < 1e-12, max_gap
write_metrics(args.metrics, out)
print(f"points {n_points}, max ECE gap vs describe {max_gap:.2e}, min seeds in a bin {min_seeds_in_bin}")
