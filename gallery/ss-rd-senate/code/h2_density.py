"""H2(a): density test of the running variable at the cutoff.

rddensity on margin, all rows (outcome-free). Primary statistic: robust
bias-corrected T_Q (rddensity `test`, jackknife SE) and its p-value, with the
package defaults (bwselect = 'comb', massPoints = True, p = 2, triangular kernel,
jackknife variance). Single test, no correction (plan: H2(a)).

Also recorded:
  T_conv, p_conv   conventional statistic (rddensity useall = True, `test_p`)
  p_Q_useall       robust p-value from the useall call, must equal p_Q
  p_Q_nomass       robust p-value with massPoints = False (sensitivity, no rule)

The outcome `vote` is not loaded.

Usage (crew.py run --kind analysis):
    .venv/bin/python code/h2_density.py runs/h2-density/metrics.json [--data PATH]
"""
import argparse
import json
import os

import pandas as pd
from rddensity import rddensity

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")
# design-mde (margin-only run, before the gate) gave p_Q = 0.3814253737593818.
DESIGN_MDE_P_Q = 0.3814253737593818
OPTS = dict(c=0, p=2, kernel="triangular", vce="jackknife", bwselect="comb")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics")
    ap.add_argument("--data", default=RAW)
    args = ap.parse_args()

    df = pd.read_csv(args.data, usecols=["margin"])
    x = pd.to_numeric(df["margin"], errors="coerce").to_numpy(dtype=float)

    d = rddensity(X=x, massPoints=True, **OPTS)
    d_all = rddensity(X=x, massPoints=True, useall=True, **OPTS)
    d_nomass = rddensity(X=x, massPoints=False, **OPTS)

    m = {
        "N": int(d.n["full"]),
        "n_left": int(d.n["left"]),
        "n_right": int(d.n["right"]),
        "hat_left": float(d.hat["left"]),
        "hat_right": float(d.hat["right"]),
        "hat_diff": float(d.hat["diff"]),
        "sd_jk_diff": float(d.sd_jk["diff"]),
        "bw_left": float(d.h["left"]),
        "bw_right": float(d.h["right"]),
        "T_Q": float(d.test["t_jk"]),
        "p_Q": float(d.test["p_jk"]),
        "T_Q_asy": float(d.test["t_asy"]),
        "p_Q_asy": float(d.test["p_asy"]),
        "T_conv": float(d_all.test_p["t_jk"]),
        "p_conv": float(d_all.test_p["p_jk"]),
        "p_Q_useall": float(d_all.test["p_jk"]),
        "p_Q_nomass": float(d_nomass.test["p_jk"]),
        "p_Q_minus_design_mde": float(d.test["p_jk"]) - DESIGN_MDE_P_Q,
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.metrics)), exist_ok=True)
    with open(args.metrics, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
