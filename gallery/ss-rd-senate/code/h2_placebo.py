"""H2(c): one-sided placebo cutoffs on the outcome. REPORT-ONLY.

c_L = median of margin among margin < 0, c_R = median of margin among margin > 0,
both from the full margin column (outcome-free; design-r3 F11).
Left test:  rdrobust(vote, margin) on margin < 0 only, c = c_L.
Right test: rdrobust(vote, margin) on margin > 0 only, c = c_R.
H1 options, masspoints = 'off'.

Reported, with no equivalence bound, no correction and no non-rejection claim:
estimate, CI, p-value, N, bandwidths, N_h by side, bw_max of the one-sided sample
(max(|c - x_min|, |c - x_max|), the rdbwselect.py cap, lines 651-655),
bw_capped (a final h or b equals bw_max: boundary-limited), and the SD of vote on
the side (descriptive).

Usage (crew.py run --kind analysis):
    .venv/bin/python code/h2_placebo.py runs/h2-placebo/metrics.json [--data PATH]
"""
import argparse
import json
import math
import os

import numpy as np
import pandas as pd
from rdrobust import rdrobust

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")
OPTS = dict(p=1, q=2, kernel="tri", bwselect="mserd", vce="nn", nnmatch=3, level=95)


def capped_flag(r, bwm):
    """1 when a final bandwidth (h or b, either side) equals bw_max, i.e. the cap binds."""
    hb = [float(r.bws.loc[k, s]) for k in ["h", "b"] for s in ["left", "right"]]
    return int(any(math.isclose(v, bwm, rel_tol=0, abs_tol=1e-9) for v in hb))


def one_side(df_side, c, tag):
    y = df_side["vote"].to_numpy(dtype=float)
    x = df_side["margin"].to_numpy(dtype=float)
    r = rdrobust(y=y, x=x, c=c, masspoints="off", **OPTS)
    bwm = max(abs(c - float(x.min())), abs(c - float(x.max())))
    out = {
        f"{tag}_c": float(c),
        f"{tag}_n_side": int(len(x)),
        f"{tag}_coef": float(r.coef.loc["Conventional", "Coeff"]),
        f"{tag}_se_conv": float(r.se.loc["Conventional", "Std. Err."]),
        f"{tag}_se_robust": float(r.se.loc["Robust", "Std. Err."]),
        f"{tag}_ci_low": float(r.ci.loc["Robust", "CI Lower"]),
        f"{tag}_ci_high": float(r.ci.loc["Robust", "CI Upper"]),
        f"{tag}_ci_width": float(r.ci.loc["Robust", "CI Upper"] - r.ci.loc["Robust", "CI Lower"]),
        f"{tag}_p_robust": float(r.pv.loc["Robust", "P>|z|"]),
        f"{tag}_N": int(r.N[0] + r.N[1]),
        f"{tag}_N_left": int(r.N[0]), f"{tag}_N_right": int(r.N[1]),
        f"{tag}_N_h_left": int(r.N_h[0]), f"{tag}_N_h_right": int(r.N_h[1]),
        f"{tag}_h_left": float(r.bws.loc["h", "left"]), f"{tag}_h_right": float(r.bws.loc["h", "right"]),
        f"{tag}_b_left": float(r.bws.loc["b", "left"]), f"{tag}_b_right": float(r.bws.loc["b", "right"]),
        f"{tag}_bw_max": bwm,
        f"{tag}_bw_capped": capped_flag(r, bwm),
        f"{tag}_sd_vote_side": float(np.std(y, ddof=1)),
    }
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics")
    ap.add_argument("--data", default=RAW)
    args = ap.parse_args()

    df = pd.read_csv(args.data)
    for col in ["margin", "vote"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Cutoffs from the running variable only, all rows (outcome-free).
    c_L = float(df.loc[df["margin"] < 0, "margin"].median())
    c_R = float(df.loc[df["margin"] > 0, "margin"].median())

    est = df[df["vote"].notna()]
    left = est[est["margin"] < 0]
    right = est[est["margin"] > 0]

    m = {"c_L": c_L, "c_R": c_R}
    m.update(one_side(left, c_L, "left"))
    m.update(one_side(right, c_R, "right"))

    os.makedirs(os.path.dirname(os.path.abspath(args.metrics)), exist_ok=True)
    with open(args.metrics, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
