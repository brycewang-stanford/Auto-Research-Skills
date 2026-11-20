"""H1: computational reproduction of the CCFT (2017, Sec. 7.2) default output.

Sharp RD, local linear (p = 1, q = 2), triangular kernel, mserd bandwidth,
NN variance (nnmatch = 3), robust bias-corrected 95% CI, on the estimation
sample (rows with a non-missing vote; 1,297 rows in the seed file).

Two readings are computed in the same run:
  off   masspoints = 'off'   primary; the H1 decision is judged on this reading
  adj   masspoints = 'adjust' (rdrobust 2.1.1 default); reported, not decisive

Side counts, distinct margin values and mass-point shares are recorded on the
estimation sample (design-r2 F12).

Usage (crew.py run --kind analysis):
    .venv/bin/python code/h1_replication.py runs/h1-rdrobust/metrics.json [--data PATH]
"""
import argparse
import json
import os

import numpy as np
import pandas as pd
from rdrobust import rdrobust

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")

# Published targets (CCFT 2017 printed default output), fixed at the design gate.
PUB_CONV = 7.416
PUB_CI_LOW = 4.09441
PUB_CI_HIGH = 10.9255
PUB_N = 1297
PUB_H = 17.708
TOL_EST = 0.01   # percentage points
TOL_H = 0.0005   # bandwidth printed to 3 decimals

OPTS = dict(c=0, p=1, q=2, kernel="tri", bwselect="mserd", vce="nn", nnmatch=3, level=95)


def side_stats(x):
    vals, counts = np.unique(x, return_counts=True)
    n = len(x)
    return {
        "n": int(n),
        "distinct": int(len(vals)),
        "mass_share": float(1 - len(vals) / n) if n else float("nan"),
        "obs_at_shared_values": int(counts[counts >= 2].sum()),
    }


def extract(r, prefix, m):
    m[f"{prefix}_conv_coef"] = float(r.coef.loc["Conventional", "Coeff"])
    m[f"{prefix}_conv_se"] = float(r.se.loc["Conventional", "Std. Err."])
    m[f"{prefix}_ci_low"] = float(r.ci.loc["Robust", "CI Lower"])
    m[f"{prefix}_ci_high"] = float(r.ci.loc["Robust", "CI Upper"])
    m[f"{prefix}_robust_se"] = float(r.se.loc["Robust", "Std. Err."])
    m[f"{prefix}_p_robust"] = float(r.pv.loc["Robust", "P>|z|"])
    m[f"{prefix}_h_left"] = float(r.bws.loc["h", "left"])
    m[f"{prefix}_h_right"] = float(r.bws.loc["h", "right"])
    m[f"{prefix}_b_left"] = float(r.bws.loc["b", "left"])
    m[f"{prefix}_b_right"] = float(r.bws.loc["b", "right"])
    m[f"{prefix}_N_left"] = int(r.N[0])
    m[f"{prefix}_N_right"] = int(r.N[1])
    m[f"{prefix}_N"] = int(r.N[0] + r.N[1])
    m[f"{prefix}_N_h_left"] = int(r.N_h[0])
    m[f"{prefix}_N_h_right"] = int(r.N_h[1])
    m[f"{prefix}_M_left"] = int(r.M[0])
    m[f"{prefix}_M_right"] = int(r.M[1])


def tolerance_flags(conv, lo, hi, N, h):
    """H1 decision rule (design.method): 0/1 flags against the printed targets."""
    flags = {
        "tol_conv_ok": int(abs(conv - PUB_CONV) <= TOL_EST),
        "tol_ci_low_ok": int(abs(lo - PUB_CI_LOW) <= TOL_EST),
        "tol_ci_high_ok": int(abs(hi - PUB_CI_HIGH) <= TOL_EST),
        "tol_N_ok": int(N == PUB_N),
        "tol_h_ok": int(abs(h - PUB_H) <= TOL_H),
    }
    flags["h1_pass_off"] = int(all(flags.values()))
    return flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics")
    ap.add_argument("--data", default=RAW)
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    for col in ["margin", "vote"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    est = df[df["vote"].notna()].reset_index(drop=True)
    x = est["margin"].to_numpy(dtype=float)
    y = est["vote"].to_numpy(dtype=float)

    m = {"n_rows_file": int(len(df)), "n_estimation": int(len(est)),
         "n_missing_vote": int(df["vote"].isna().sum())}

    left = x[x < 0]    # rdrobust convention: left x < c, right x >= c
    right = x[x >= 0]
    sl, sr = side_stats(left), side_stats(right)
    m.update({
        "side_n_left": sl["n"], "side_n_right": sr["n"],
        "distinct_left": sl["distinct"], "distinct_right": sr["distinct"],
        "distinct_total": sl["distinct"] + sr["distinct"],
        "mass_share_left": sl["mass_share"], "mass_share_right": sr["mass_share"],
        "obs_at_shared_left": sl["obs_at_shared_values"],
        "obs_at_shared_right": sr["obs_at_shared_values"],
    })

    r_off = rdrobust(y=y, x=x, masspoints="off", **OPTS)
    extract(r_off, "off", m)
    r_adj = rdrobust(y=y, x=x, masspoints="adjust", **OPTS)
    extract(r_adj, "adj", m)

    # Decision reading: masspoints = 'off' against the printed targets.
    conv, lo, hi, N, h = (m["off_conv_coef"], m["off_ci_low"], m["off_ci_high"],
                          m["off_N"], m["off_h_left"])
    m["diff_conv"] = conv - PUB_CONV
    m["diff_ci_low"] = lo - PUB_CI_LOW
    m["diff_ci_high"] = hi - PUB_CI_HIGH
    m["diff_N"] = N - PUB_N
    m["diff_h"] = h - PUB_H
    m.update(tolerance_flags(conv, lo, hi, N, h))

    os.makedirs(os.path.dirname(os.path.abspath(args.metrics)), exist_ok=True)
    with open(args.metrics, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
