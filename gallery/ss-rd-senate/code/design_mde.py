"""Design-stage minimum detectable effects for H2(a) and H2(b).

Uses only the running variable `margin` and the four predetermined covariates
(class, termshouse, termssenate, population). It never reads `vote`: the
outcome column is not loaded. No rdrobust or rddensity result on the outcome
is produced.

H2(a): rddensity(margin, c=0, p=2, kernel triangular, vce jackknife, massPoints
  default) under the null. MDE on the density-difference scale
  = (z_0.975 + z_0.80) * SE_jk(diff), reported also relative to the left density.
H2(b): for each covariate, rdrobust(y = covariate, x = margin) with the H1
  options (masspoints='off'). MDE in covariate units
  = (z_0.975 + z_0.80) * robust SE of that test.

Usage (run through crew.py run --kind data-prep):
    .venv/bin/python code/design_mde.py runs/design-mde/metrics.json
"""
import json
import os
import sys

import pandas as pd
from scipy.stats import norm
from rddensity import rddensity
from rdrobust import rdrobust

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")
COVARIATES = ["class", "termshouse", "termssenate", "population"]
Z_MDE = norm.ppf(0.975) + norm.ppf(0.80)  # 80% power, two-sided 5%


def main():
    metrics_path = sys.argv[1]
    # usecols keeps `vote` out of memory entirely.
    df = pd.read_csv(RAW, usecols=["margin"] + COVARIATES)
    for c in ["margin"] + COVARIATES:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    m = {"z_mde": round(float(Z_MDE), 6), "outcome_loaded": 0}

    # H2(a): density test on margin, all rows
    x = df["margin"].to_numpy(dtype=float)
    dens = rddensity(x, c=0, p=2, kernel="triangular", vce="jackknife")
    sd_jk = float(dens.sd_jk["diff"])
    diff = float(dens.hat["diff"])
    f_left = float(dens.hat["left"])
    m["h2a_N"] = int(dens.n["full"])
    m["h2a_n_left"] = int(dens.n["left"])
    m["h2a_n_right"] = int(dens.n["right"])
    m["h2a_diff_hat"] = diff
    m["h2a_se_jk_null"] = sd_jk
    m["h2a_T_Q"] = float(dens.test["t_jk"])
    m["h2a_p_Q"] = float(dens.test["p_jk"])
    m["h2a_mde_density_diff"] = float(Z_MDE * sd_jk)
    m["h2a_f_left_hat"] = f_left
    m["h2a_mde_relative_to_left"] = float(Z_MDE * sd_jk / f_left)

    # H2(b): covariate tests, H1 options except masspoints kept as 'off'
    for cov in COVARIATES:
        sub = df[["margin", cov]].dropna()
        r = rdrobust(y=sub[cov].to_numpy(dtype=float),
                     x=sub["margin"].to_numpy(dtype=float),
                     c=0, p=1, q=2, kernel="tri", bwselect="mserd",
                     vce="nn", nnmatch=3, level=95, masspoints="off")
        se_rb = float(r.se.loc["Robust", "Std. Err."])
        m[f"h2b_{cov}_N"] = int(sum(r.N))
        m[f"h2b_{cov}_se_robust"] = se_rb
        m[f"h2b_{cov}_mde"] = float(Z_MDE * se_rb)

    with open(metrics_path, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
