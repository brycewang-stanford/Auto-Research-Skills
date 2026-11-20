"""Figure: histogram and rddensity fit of margin around the cutoff (H2(a)).

rddensity on all 1,390 margins with the same settings as run h2-density
(p = 2, triangular kernel, jackknife variance, bwselect 'comb', massPoints True).
The histogram is drawn here (1-point bins over [-40, 40], scaled to a density over
all 1,390 margins). The estimated density curves and their 95% confidence regions are
the grid values that rddensity's rdplotdensity computes (plotN = 60 per side, evenly
spaced grid). The outcome vote is not loaded.

Output: paper/figures/fig_density.pdf (vector). Metrics: runs/fig-density/metrics.json.
The T_Q and p_Q printed here are recomputed and must equal runs/h2-density.

Usage (crew.py run --kind analysis):
    .venv/bin/python code/fig_density.py runs/fig-density/metrics.json [--data PATH]
"""
import argparse
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from rddensity import rddensity, rdplotdensity  # noqa: E402

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")
H2A = os.path.join(WS, "runs", "h2-density", "metrics.json")
OUT = os.path.join(WS, "paper", "figures", "fig_density.pdf")
OPTS = dict(c=0, p=2, kernel="triangular", vce="jackknife", bwselect="comb")
PLOT_RANGE = [-40, 40]
PLOT_N = [60]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics")
    ap.add_argument("--data", default=RAW)
    args = ap.parse_args()

    df = pd.read_csv(args.data, usecols=["margin"])
    x = pd.to_numeric(df["margin"], errors="coerce").to_numpy(dtype=float)
    n_all = len(x)
    d = rddensity(X=x, massPoints=True, **OPTS)

    with open(H2A) as f:
        h2a = json.load(f)
    t_q = float(d.test["t_jk"])
    p_q = float(d.test["p_jk"])
    if abs(p_q - h2a["p_Q"]) > 1e-9 or abs(t_q - h2a["T_Q"]) > 1e-9:
        raise SystemExit("recomputed rddensity test does not match run h2-density")

    # rdplotdensity supplies the fitted density grid; its layers are left side then right side.
    r = rdplotdensity(d, x, plotRange=PLOT_RANGE, plotN=PLOT_N, plotGrid=["es"],
                      alpha=0.05, CItype="region", hist=False)
    left, right = r.layers[0]._data, r.layers[1]._data
    if not (left["grid"].max() <= 0 + 1e-9 and right["grid"].min() >= 0 - 1e-9):
        raise SystemExit("unexpected rdplotdensity layer order")

    # Histogram: 1-point bins over the plot range, as a density over all margins.
    edges = np.arange(PLOT_RANGE[0], PLOT_RANGE[1] + 1, 1.0)
    counts, _ = np.histogram(x, bins=edges)
    dens = counts / (n_all * 1.0)

    plt.rcParams.update({"font.size": 9, "font.family": "serif"})
    fig, ax = plt.subplots(figsize=(6.2, 3.9))
    ax.bar(edges[:-1], dens, width=1.0, align="edge", color="0.78", edgecolor="white",
           linewidth=0.4, label="Histogram (1-point bins)", zorder=1)
    for part in (left, right):
        ax.fill_between(part["grid"], part["CI_l"], part["CI_r"], color="#9db8d2",
                        alpha=0.55, lw=0, zorder=2)
        ax.plot(part["grid"], part["f_p"], color="#1f4e79", lw=2.0, zorder=3)
    ax.plot([], [], color="#1f4e79", lw=2.0, label="rddensity fit (p = 2)")
    ax.fill_between([], [], [], color="#9db8d2", alpha=0.55, label="95% confidence region")
    ax.axvline(0, color="0.25", lw=0.9)
    ax.set_xlim(PLOT_RANGE)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Democratic margin of victory at t (percentage points; cutoff 0)")
    ax.set_ylabel("Density of margin")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, format="pdf")
    plt.close(fig)

    m = {
        "N_plotted": int(n_all),
        "n_left": int(d.n["left"]),
        "n_right": int(d.n["right"]),
        "plot_range_lo": PLOT_RANGE[0],
        "plot_range_hi": PLOT_RANGE[1],
        "hist_bin_width": 1.0,
        "fit_grid_points_per_side": PLOT_N[0],
        "T_Q": t_q,
        "p_Q": p_q,
        "bw_left": float(d.h["left"]),
        "bw_right": float(d.h["right"]),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.metrics)), exist_ok=True)
    with open(args.metrics, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
