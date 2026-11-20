"""Figure: RD plot of vote on margin (H1 sample, masspoints 'off').

Bins: rdrobust's rdplot (p = 1, binselect 'esmv', evenly spaced bins chosen
separately on each side of the cutoff, masspoints 'off'). Only the bin edges are
taken from rdplot; bin means, standard errors and 95% intervals are recomputed here
from the H1 estimation sample and checked against rdplot's own bin means.

Fits: H1 local-linear fits, p = 1, triangular kernel K(u) = (1 - |u|) on |u| <= 1,
bandwidth h from the 'off' reading of runs/h1-rdrobust (the same weights rdrobust uses
for its conventional estimate). The intercept difference is checked against the
recorded conventional estimate.

Output: paper/figures/fig_rd.pdf (vector). Metrics: runs/fig-rd/metrics.json.

Usage (crew.py run --kind analysis):
    .venv/bin/python code/fig_rd.py runs/fig-rd/metrics.json [--data PATH]
"""
import argparse
import json
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from rdrobust import rdplot  # noqa: E402
from scipy.stats import t as tdist  # noqa: E402

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")
H1 = os.path.join(WS, "runs", "h1-rdrobust", "metrics.json")
OUT = os.path.join(WS, "paper", "figures", "fig_rd.pdf")


def tri_fit(x, y, h):
    """Weighted local-linear fit with triangular weights on [-h, h]; return intercept at 0 and the fit function."""
    w = 1.0 - np.abs(x) / h
    X = np.column_stack([np.ones_like(x), x])
    W = np.sqrt(w)
    beta, *_ = np.linalg.lstsq(X * W[:, None], y * W, rcond=None)
    return beta


def bin_stats(x, y, edges):
    idx = np.digitize(x, edges[1:-1], right=False)
    rows = []
    for b in np.unique(idx):
        m = idx == b
        n = int(m.sum())
        mean = float(y[m].mean())
        sd = float(y[m].std(ddof=1)) if n >= 2 else float("nan")
        xm = float(x[m].mean())
        se = sd / np.sqrt(n) if n >= 2 else float("nan")
        rows.append({"x": xm, "y": mean, "n": n, "se": se})
    return pd.DataFrame(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics")
    ap.add_argument("--data", default=RAW)
    args = ap.parse_args()

    df = pd.read_csv(args.data).dropna(subset=["vote"])
    x = df["margin"].to_numpy(float)
    y = df["vote"].to_numpy(float)
    with open(H1) as f:
        h1 = json.load(f)
    h = float(h1["off_h_left"])
    conv = float(h1["off_conv_coef"])

    # Bin edges from rdplot (masspoints off, p = 1, esmv binning).
    rp = rdplot(y, x, c=0, p=1, kernel="tri", masspoints="off", hide=True)
    vb = rp.vars_bins
    edges = np.unique(np.concatenate([vb["rdplot_min_bin"].to_numpy(float),
                                      vb["rdplot_max_bin"].to_numpy(float)]))
    edges = np.sort(edges)
    bins = bin_stats(x, y, edges)
    # rdplot's own bin means, recomputed over the same bins, as a check on the edges.
    ref = rdplot_bin_means_check(x, y, edges, vb)

    # Local-linear fits within h, triangular weights, each side.
    L = (x < 0) & (x >= -h)
    R = (x >= 0) & (x <= h)
    bl = tri_fit(x[L], y[L], h)
    br = tri_fit(x[R], y[R], h)
    fit_diff = float(br[0] - bl[0])

    # ---- plot ----
    plt.rcParams.update({"font.size": 9, "font.family": "serif"})
    fig, ax = plt.subplots(figsize=(6.2, 3.9))
    ax.axvspan(-100, -h, color="0.94", zorder=0, lw=0)
    ax.axvspan(h, 100, color="0.94", zorder=0, lw=0)
    ok = bins["n"] >= 2
    ax.errorbar(bins.loc[ok, "x"], bins.loc[ok, "y"],
                yerr=1.96 * bins.loc[ok, "se"], fmt="o", ms=3.2, color="black",
                ecolor="0.45", elinewidth=0.8, capsize=1.5, label="Bin mean, 95% CI",
                zorder=3)
    ax.plot(bins.loc[~ok, "x"], bins.loc[~ok, "y"], "o", ms=3.2, mfc="white",
            mec="black", label="Bin with one observation (no CI)", zorder=3)
    xl = np.linspace(-h, 0, 100)
    xr = np.linspace(0, h, 100)
    ax.plot(xl, bl[0] + bl[1] * xl, color="#1f4e79", lw=2.2, zorder=4,
            label="Local-linear fit within h")
    ax.plot(xr, br[0] + br[1] * xr, color="#1f4e79", lw=2.2, zorder=4)
    ax.axvline(0, color="0.25", lw=0.9)
    ax.axvline(-h, color="0.4", lw=0.8, ls="--")
    ax.axvline(h, color="0.4", lw=0.8, ls="--")
    ax.text(h + 1.5, 2, "h", color="0.3", fontsize=8)
    ax.set_xlim(-100, 100)
    ax.set_xlabel("Democratic margin of victory at t (percentage points; cutoff 0)")
    ax.set_ylabel("Democratic vote share at t+2 (%)")
    ax.legend(frameon=False, fontsize=7.5, loc="lower left")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, format="pdf")
    plt.close(fig)

    m = {
        "N_plotted": int(len(x)),
        "h": h,
        "h_source": "runs/h1-rdrobust off_h_left",
        "n_bins_total": int(len(bins)),
        "n_bins_left": int((edges[:-1] < 0).sum()),
        "n_bins_right": int((edges[:-1] >= 0).sum()),
        "n_bins_one_obs": int((~ok).sum()),
        "bin_mean_max_abs_diff_vs_rdplot": ref,
        "n_left_window": int(L.sum()),
        "n_right_window": int(R.sum()),
        "fit_intercept_left": float(bl[0]),
        "fit_intercept_right": float(br[0]),
        "fit_diff": fit_diff,
        "conv_coef_recorded": conv,
        "fit_diff_minus_conv": fit_diff - conv,
    }
    if abs(m["fit_diff_minus_conv"]) > 1e-3:
        raise SystemExit("fit intercept difference does not reproduce the H1 conventional estimate")
    os.makedirs(os.path.dirname(os.path.abspath(args.metrics)), exist_ok=True)
    with open(args.metrics, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    print(json.dumps(m, indent=2))


def rdplot_bin_means_check(x, y, edges, vb):
    """Max absolute difference between rdplot's bin means and the means recomputed here
    over the same bin edges (each rdplot bin is [min_bin, max_bin], last bin closed)."""
    diffs = []
    for lo, hi, mean_rp, n_rp in zip(vb["rdplot_min_bin"].to_numpy(float),
                                     vb["rdplot_max_bin"].to_numpy(float),
                                     vb["rdplot_mean_y"].to_numpy(float),
                                     vb["rdplot_N"].to_numpy(int)):
        m = (x >= lo) & (x < hi) if hi < 100 else (x >= lo) & (x <= hi)
        if int(m.sum()) != n_rp:
            diffs.append(float("inf"))
            continue
        diffs.append(abs(float(y[m].mean()) - mean_rp))
    return float(max(diffs)) if diffs else float("nan")


if __name__ == "__main__":
    main()
