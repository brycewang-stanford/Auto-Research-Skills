"""H3: descriptive sensitivity of the H1 estimate. No decision rule.

Five specifications on the estimation sample (vote observed), reported next to H1:
  i_2014_bw     printed 2014 bandwidths h = 16.79369, b = 27.43745, p = 1, 'off'
  ii_half_bw    half of the H1 bandwidth: h = 8.854, b = 13.992 (b = half of 27.984)
  iii_double_bw double of the H1 bandwidth: h = 35.416, b = 55.968
  iv_p2         p = 2, q = 3, mserd bandwidth, 'off'
  v_adjust      H1 specification with masspoints = 'adjust'

Usage (crew.py run --kind analysis):
    .venv/bin/python code/h3_sensitivity.py runs/h3-sensitivity/metrics.json [--data PATH]
"""
import argparse
import json
import os

import pandas as pd
from rdrobust import rdrobust

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")
BASE = dict(c=0, p=1, q=2, kernel="tri", bwselect="mserd", vce="nn", nnmatch=3, level=95,
            masspoints="off")
SPECS = [
    ("i_2014_bw", dict(BASE, h=16.79369, b=27.43745)),
    ("ii_half_bw", dict(BASE, h=8.854, b=13.992)),
    ("iii_double_bw", dict(BASE, h=35.416, b=55.968)),
    ("iv_p2", dict(BASE, p=2, q=3)),
    ("v_adjust", dict(BASE, masspoints="adjust")),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics")
    ap.add_argument("--data", default=RAW)
    args = ap.parse_args()

    df = pd.read_csv(args.data, usecols=["margin", "vote"])
    for col in ["margin", "vote"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    est = df[df["vote"].notna()]
    x = est["margin"].to_numpy(dtype=float)
    y = est["vote"].to_numpy(dtype=float)

    m = {}
    for tag, opts in SPECS:
        r = rdrobust(y=y, x=x, **opts)
        m[f"{tag}_conv_coef"] = float(r.coef.loc["Conventional", "Coeff"])
        m[f"{tag}_conv_se"] = float(r.se.loc["Conventional", "Std. Err."])
        m[f"{tag}_ci_low"] = float(r.ci.loc["Robust", "CI Lower"])
        m[f"{tag}_ci_high"] = float(r.ci.loc["Robust", "CI Upper"])
        m[f"{tag}_p_robust"] = float(r.pv.loc["Robust", "P>|z|"])
        m[f"{tag}_h_left"] = float(r.bws.loc["h", "left"])
        m[f"{tag}_h_right"] = float(r.bws.loc["h", "right"])
        m[f"{tag}_b_left"] = float(r.bws.loc["b", "left"])
        m[f"{tag}_b_right"] = float(r.bws.loc["b", "right"])
        m[f"{tag}_N"] = int(r.N[0] + r.N[1])
        m[f"{tag}_N_h_left"] = int(r.N_h[0])
        m[f"{tag}_N_h_right"] = int(r.N_h[1])

    os.makedirs(os.path.dirname(os.path.abspath(args.metrics)), exist_ok=True)
    with open(args.metrics, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
