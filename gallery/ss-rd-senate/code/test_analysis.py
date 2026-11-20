"""Unit tests for the H1, H2 and H3 analysis scripts, on SYNTHETIC data only.

A synthetic file with the seed file's columns and shape (1,390 rows, 93 missing
outcomes, 282 missing termshouse/termssenate, mass points at +/-100 only) is
written to the scratch directory given as the second argument. Every script is
run with --data pointing at that file. The real raw file is never passed to any
script here, and the outcome is synthetic, so no result of this run is evidence
about the incumbency advantage.

Usage (crew.py run --kind data-prep, id unit-tests):
    .venv/bin/python code/test_analysis.py runs/unit-tests/metrics.json <scratch_dir>
"""
import importlib.util
import json
import math
import os
import subprocess
import sys

import numpy as np
import pandas as pd
from scipy.stats import norm

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CODE = os.path.join(WS, "code")
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")
Z_MDE = norm.ppf(0.975) + norm.ppf(0.80)
H_GIVEN = {"i_2014_bw": (16.79369, 27.43745), "ii_half_bw": (8.854, 13.992),
           "iii_double_bw": (35.416, 55.968)}


def make_synthetic(path):
    rng = np.random.default_rng(20261120)
    n = 1390
    margin = np.round(rng.uniform(-60, 60, n), 4)
    margin[:38] = 100.0          # mass point at +100 (38 obs), as in the seed file
    margin[38:40] = -100.0       # mass point at -100 (2 obs)
    margin[40:] = np.where(margin[40:] == 0, 0.5, margin[40:])
    side = np.where(margin >= 0, 1.0, 0.0)
    vote = 50 + 3 * side + 0.2 * margin + rng.normal(0, 5, n)
    vote[rng.choice(n, 93, replace=False)] = np.nan
    miss = rng.choice(n, 282, replace=False)
    termshouse = rng.integers(0, 10, n).astype(float)
    termssenate = rng.integers(1, 20, n).astype(float)
    termshouse[miss] = np.nan
    termssenate[miss] = np.nan
    df = pd.DataFrame({
        "state": [f"S{i % 50:02d}" for i in range(n)],
        "year": rng.integers(1914, 2011, n),
        "vote": np.round(vote, 4),
        "margin": margin,
        "class": rng.integers(1, 4, n),
        "termshouse": termshouse,
        "termssenate": termssenate,
        "population": rng.integers(78000, 37000000, n),
    })
    df.to_csv(path, index=False)
    return df


def run_script(name, metrics_path, data_path):
    cmd = [sys.executable, os.path.join(CODE, name), metrics_path, "--data", data_path]
    p = subprocess.run(cmd, cwd=WS, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"{name} exited {p.returncode}: {p.stderr[-800:]}")
    with open(metrics_path) as f:
        return json.load(f)


def load_module(name):
    spec = importlib.util.spec_from_file_location(name, os.path.join(CODE, name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def close(a, b, tol=1e-9):
    return abs(a - b) <= tol


def main():
    metrics_out = sys.argv[1]
    scratch = os.path.abspath(sys.argv[2])
    os.makedirs(scratch, exist_ok=True)
    data = os.path.join(scratch, "synthetic_senate.csv")
    assert os.path.abspath(data) != os.path.abspath(RAW), "test must not use the raw file"
    df = make_synthetic(data)
    unit = os.path.join(scratch, "unit")
    os.makedirs(unit, exist_ok=True)
    est = df[df["vote"].notna()]
    e_left = est[est["margin"] < 0]
    e_right = est[est["margin"] >= 0]

    failures, passed = [], []

    def check(label, cond):
        (passed if cond else failures).append(label)

    def scr(name):
        return run_script(name, os.path.join(unit, name.replace(".py", ".json")), data)

    # Holm helper against a hand-computed case.
    h2c = load_module("h2_covariates")
    got = h2c.holm([0.01, 0.04, 0.03, 0.005])
    exp = [0.03, 0.06, 0.06, 0.02]
    check("holm hand case", all(close(a, b) for a, b in zip(got, exp)))
    check("holm bounded and >= raw",
          all(0 <= a <= 1 and a >= p for a, p in zip(h2c.holm([0.2, 0.9, 0.5]), [0.2, 0.9, 0.5])))

    # H1
    m = scr("h1_replication.py")
    n_est = len(est)
    check("h1 N_estimation", m["n_estimation"] == n_est and m["off_N"] == n_est)
    check("h1 side counts",
          m["side_n_left"] == len(e_left) and m["side_n_right"] == len(e_right)
          and m["off_N_left"] == len(e_left) and m["off_N_right"] == len(e_right))
    check("h1 distinct and mass share",
          m["distinct_left"] == e_left["margin"].nunique()
          and close(m["mass_share_left"], 1 - e_left["margin"].nunique() / len(e_left))
          and m["distinct_right"] == e_right["margin"].nunique())
    check("h1 obs at shared values (right has +100 mass)",
          m["obs_at_shared_right"] == int((e_right["margin"].value_counts() >= 2)
                                          .astype(int).mul(e_right["margin"].value_counts()).sum()))
    check("h1 estimate finite and near synthetic effect 3",
          math.isfinite(m["off_conv_coef"]) and abs(m["off_conv_coef"] - 3.0) < 3.0)
    check("h1 CI ordered", m["off_ci_low"] < m["off_ci_high"] and m["off_h_left"] > 0)
    check("h1 adjust reading present", math.isfinite(m["adj_conv_coef"]) and m["adj_N"] == n_est)
    check("h1 tolerance flags are 0/1",
          all(m[k] in (0, 1) for k in ["tol_conv_ok", "tol_ci_low_ok", "tol_ci_high_ok",
                                       "tol_N_ok", "tol_h_ok", "h1_pass_off"]))

    # H2(a)
    m = scr("h2_density.py")
    check("density N and sides", m["N"] == len(df) and m["n_left"] + m["n_right"] == m["N"]
          and m["n_left"] == int((df["margin"] < 0).sum()))
    check("density p-values in [0,1]", all(0 <= m[k] <= 1 for k in
                                          ["p_Q", "p_conv", "p_Q_nomass", "p_Q_useall"]))
    check("density robust p equals useall call", abs(m["p_Q"] - m["p_Q_useall"]) < 1e-10)

    # H2(b)
    m = scr("h2_covariates.py")
    n_cov = {"class": len(df), "population": len(df), "termshouse": int(df["termshouse"].notna().sum()),
             "termssenate": int(df["termssenate"].notna().sum())}
    check("covariate N", all(m[f"{c}_N"] == n_cov[c] for c in n_cov))
    check("covariate MDE = z * robust SE",
          all(close(m[f"{c}_mde"], Z_MDE * m[f"{c}_se_robust"], 1e-9) for c in n_cov))
    sub_tsh = df[["margin", "termshouse"]].dropna()
    bwm = max(abs(sub_tsh["margin"].min()), abs(sub_tsh["margin"].max()))
    check("covariate bw_max from the sample passed", close(m["termshouse_bw_max"], bwm))
    check("covariate Holm family of four (off)",
          all(0 <= m[f"{c}_holm_p"] <= 1 and m[f"{c}_holm_p"] >= m[f"{c}_p_robust"] - 1e-12
              for c in n_cov))
    check("covariate adjust reading and printed comparison present",
          all(f"{c}_adj_p_robust" in m and f"{c}_adj_minus_printed" in m for c in n_cov))

    # H2(c)
    m = scr("h2_placebo.py")
    c_L = float(df.loc[df["margin"] < 0, "margin"].median())
    c_R = float(df.loc[df["margin"] > 0, "margin"].median())
    check("placebo cutoffs from margin only", close(m["c_L"], c_L) and close(m["c_R"], c_R))
    check("placebo left N and side", m["left_n_side"] == len(e_left) and m["left_N"] == len(e_left))
    check("placebo right N and side", m["right_n_side"] == len(e_right) and m["right_N"] == len(e_right))
    xl = e_left["margin"]
    check("placebo left bw_max from one-sided sample",
          close(m["left_bw_max"], max(abs(c_L - xl.min()), abs(c_L - xl.max()))))
    xr = e_right["margin"]
    check("placebo right bw_max from one-sided sample",
          close(m["right_bw_max"], max(abs(c_R - xr.min()), abs(c_R - xr.max()))))
    check("placebo CI width and flags",
          close(m["left_ci_width"], m["left_ci_high"] - m["left_ci_low"])
          and m["left_bw_capped"] in (0, 1) and m["right_bw_capped"] in (0, 1))

    # H2(d)
    m = scr("h2_selection.py")
    check("selection N and outcome is 0/1 missingness",
          m["N"] == len(df) and close(m["n_observed_share"], df["vote"].notna().mean()))
    check("selection MDE = z * robust SE (pp)", close(m["mde_pp"], 100 * Z_MDE * m["se_robust"], 1e-9))

    # H3
    m = scr("h3_sensitivity.py")
    check("h3 fixed bandwidths honoured",
          all(close(m[f"{t}_h_left"], h, 1e-9) and close(m[f"{t}_b_left"], b, 1e-9)
              for t, (h, b) in H_GIVEN.items()))
    check("h3 five specifications", all(f"{t}_conv_coef" in m for t in
                                        ["i_2014_bw", "ii_half_bw", "iii_double_bw", "iv_p2", "v_adjust"]))
    check("h3 adjust N equals full estimation sample", m["v_adjust_N"] == n_est)

    # Static: the density and covariate scripts never name the outcome column.
    for name in ["h2_density.py", "h2_covariates.py"]:
        with open(os.path.join(CODE, name)) as f:
            check(f"{name} has no vote reference", '"vote"' not in f.read())

    total = len(passed) + len(failures)
    result = {"tests_total": total, "tests_passed": len(passed), "tests_failed": len(failures),
              "failures": failures}
    os.makedirs(os.path.dirname(os.path.abspath(metrics_out)), exist_ok=True)
    with open(metrics_out, "w") as f:
        json.dump(result, f, indent=2)
        f.write("\n")
    print(json.dumps(result, indent=2))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
