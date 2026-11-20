"""H2(d): selection on the outcome's missingness. RUN ONLY AFTER THE DESIGN GATE.

rdrobust(y = vote_observed, x = margin) on all rows, H1 options, masspoints = 'off'.
vote_observed is 1 where vote is non-missing (a 0/1 indicator of missingness;
no value of vote is used). Primary statistic: robust bias-corrected p-value.
Single test, no correction.

MDE (fixed by formula in plan.json design.method) = (z_0.975 + z_0.80) times the
robust SE, in percentage points of the share of observed outcomes.

Usage (crew.py run --kind analysis, after the design gate):
    .venv/bin/python code/h2_selection.py runs/h2-selection/metrics.json [--data PATH]
"""
import argparse
import json
import os

import pandas as pd
from rdrobust import rdrobust
from scipy.stats import norm

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")
Z_MDE = norm.ppf(0.975) + norm.ppf(0.80)
OPTS = dict(c=0, p=1, q=2, kernel="tri", bwselect="mserd", vce="nn", nnmatch=3, level=95)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics")
    ap.add_argument("--data", default=RAW)
    args = ap.parse_args()

    df = pd.read_csv(args.data, usecols=["margin", "vote"])
    margin = pd.to_numeric(df["margin"], errors="coerce").to_numpy(dtype=float)
    observed = df["vote"].notna().astype(float).to_numpy()

    r = rdrobust(y=observed, x=margin, masspoints="off", **OPTS)
    se = float(r.se.loc["Robust", "Std. Err."])
    m = {
        "n_observed_share": float(observed.mean()),
        "coef": float(r.coef.loc["Conventional", "Coeff"]),
        "se_conv": float(r.se.loc["Conventional", "Std. Err."]),
        "se_robust": se,
        "ci_low": float(r.ci.loc["Robust", "CI Lower"]),
        "ci_high": float(r.ci.loc["Robust", "CI Upper"]),
        "p_robust": float(r.pv.loc["Robust", "P>|z|"]),
        "N": int(r.N[0] + r.N[1]),
        "N_h_left": int(r.N_h[0]), "N_h_right": int(r.N_h[1]),
        "h_left": float(r.bws.loc["h", "left"]), "h_right": float(r.bws.loc["h", "right"]),
        "b_left": float(r.bws.loc["b", "left"]), "b_right": float(r.bws.loc["b", "right"]),
        "mde_pp": float(100 * Z_MDE * se),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.metrics)), exist_ok=True)
    with open(args.metrics, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
