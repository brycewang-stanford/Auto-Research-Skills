"""H2(b): balance of the four predetermined covariates at the cutoff.

For each covariate, rdrobust(y = covariate, x = margin) with the H1 options.
Decision reading: masspoints = 'off' (fixed at the design gate). Holm-adjusted
p-values over the four covariates, within this family only, at 5%.

Also recorded: the masspoints = 'adjust' reading (rdrobust 2.1.1 default) with
its own Holm adjustment, and the four p-values printed in CCFT (2017, p. 397)
for default options, compared with the 'adjust' reading (design-r3 F13). The
printed p-values are reference constants; they are not used for any decision.

MDE per test = (z_0.975 + z_0.80) * robust SE, in covariate units.
bw_capped = 1 when a final bandwidth equals bw_max = max(|c - x_min|, |c - x_max|)
over the sample passed to the estimator.

The outcome `vote` is not loaded.

Declared input: runs/design-mde/metrics.json (SE and MDE comparison, F3); tests pass
their own fixture through --design-mde.

Usage (crew.py run --kind analysis):
    .venv/bin/python code/h2_covariates.py runs/h2-covariates/metrics.json [--data PATH]
"""
import argparse
import json
import math
import os

import pandas as pd
from rdrobust import rdrobust
from scipy.stats import norm

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")
# design-mde (margin-only, masspoints 'off', before the gate): SEs and MDEs fixed in the design.
DESIGN_MDE = os.path.join(WS, "runs", "design-mde", "metrics.json")
COVARIATES = ["class", "termshouse", "termssenate", "population"]
PRINTED_P_CCFT2017 = {"class": 0.897, "termshouse": 0.561,
                      "termssenate": 0.901, "population": 0.634}
Z_MDE = norm.ppf(0.975) + norm.ppf(0.80)
OPTS = dict(c=0, p=1, q=2, kernel="tri", bwselect="mserd", vce="nn", nnmatch=3, level=95)


def holm(pvals):
    """Holm step-down adjusted p-values, returned in the input order."""
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    adj = [None] * m
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj


def bw_max_of(x):
    return max(abs(0.0 - float(x.min())), abs(0.0 - float(x.max())))


def run_one(cov, sub, masspoints):
    r = rdrobust(y=sub[cov].to_numpy(dtype=float), x=sub["margin"].to_numpy(dtype=float),
                 masspoints=masspoints, **OPTS)
    bwm = bw_max_of(sub["margin"])
    hb = [float(r.bws.loc[k, s]) for k in ["h", "b"] for s in ["left", "right"]]
    capped = any(math.isclose(v, bwm, rel_tol=0, abs_tol=1e-9) for v in hb)
    se = float(r.se.loc["Robust", "Std. Err."])
    return {
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
        "bw_max": bwm,
        "bw_capped": int(capped),
        "mde": float(Z_MDE * se),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics")
    ap.add_argument("--data", default=RAW)
    ap.add_argument("--design-mde", default=DESIGN_MDE)
    args = ap.parse_args()

    df = pd.read_csv(args.data, usecols=["margin"] + COVARIATES)
    for c in ["margin"] + COVARIATES:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    m = {}
    for setting, tag in [("off", ""), ("adjust", "_adj")]:
        res = {}
        for cov in COVARIATES:
            sub = df[["margin", cov]].dropna().reset_index(drop=True)
            res[cov] = run_one(cov, sub, setting)
        holm_p = holm([res[c]["p_robust"] for c in COVARIATES])
        for cov, hp in zip(COVARIATES, holm_p):
            r = res[cov]
            for k, v in r.items():
                m[f"{cov}{tag}_{k}"] = v
            m[f"{cov}{tag}_holm_p"] = hp
            m[f"{cov}{tag}_holm_reject_5pct"] = int(hp < 0.05)
    # F3: compare the 'off' SEs and MDEs with the values fixed by design-mde.
    with open(args.design_mde) as f:
        dm = json.load(f)
    for cov in COVARIATES:
        d_se, d_mde = dm[f"h2b_{cov}_se_robust"], dm[f"h2b_{cov}_mde"]
        m[f"{cov}_design_se_robust"] = d_se
        m[f"{cov}_design_mde"] = d_mde
        m[f"{cov}_se_minus_design"] = m[f"{cov}_se_robust"] - d_se
        m[f"{cov}_mde_minus_design"] = m[f"{cov}_mde"] - d_mde
        m[f"{cov}_design_match"] = int(math.isclose(m[f"{cov}_se_robust"], d_se, rel_tol=1e-6)
                                       and math.isclose(m[f"{cov}_mde"], d_mde, rel_tol=1e-6))
    for cov in COVARIATES:
        m[f"{cov}_printed_p_ccft2017"] = PRINTED_P_CCFT2017[cov]
        m[f"{cov}_adj_minus_printed"] = m[f"{cov}_adj_p_robust"] - PRINTED_P_CCFT2017[cov]

    os.makedirs(os.path.dirname(os.path.abspath(args.metrics)), exist_ok=True)
    with open(args.metrics, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
