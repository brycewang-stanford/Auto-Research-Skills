"""verdict (analysis plan 8-9): evaluate H1-H3 from the run metrics, with the fixed decision rules.

Inputs (declared with --input): runs/check-noctrl/metrics.json, runs/main-<learner>/metrics.json
for the five learners, runs/sens-lasso-c11/metrics.json and data/derived/sipp1991.csv (baseline
only). Tolerances, S and testability are the constants in code/dml_plr.py, asserted equal to
plan.json design (plan.json is read for that assertion only).

Decision rules (plan.json design.decision_rules), never changed by what the results show:
  H1  fails if any of the 10 cells has theta_med <= 0 or theta_med - 1.96 x adjusted SE <= 0.
  H2  per cell inside if |theta_rep - theta_pub| <= tolerance. Every cell outside is a failure
      (lasso included); a cell inside counts as a pass only if testable. H2 holds if no cell is
      outside and all 8 testable cells are inside.
  H3  fails if, at K = 2 or K = 5, the lasso theta_med >= the theta_med of any flexible learner
      (main runs only; sens-lasso-c11 evaluated descriptively).
Descriptive only: tol_obs reading of failed cells, side-by-side table, baseline, diagnostics.

Writes runs/verdict/metrics.json (flat).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from dml_plr import (FOLDS, LEARNERS, MAD_TO_SD, SPLITS, TOLERANCE_TABLE,  # noqa: E402
                     assert_plan_constants)

OUT = Path("runs/verdict/metrics.json")
DATA = Path("data/derived/sipp1991.csv")
Z_H1 = 1.96
BONF = 2.81
SE_MEDIAN_FACTOR = 1.2533
FLEXIBLE = ["tree", "forest", "boosting", "nnet"]
READING_INSIDE_OBS = ("outside the planned tolerance but inside the tolerance implied by our own "
                      "split-to-split spread: the failure may reflect a noisier implementation "
                      "(a variance difference), not only a shift of its centre")
READING_OUTSIDE_BOTH = "outside both tolerances: the centre of our estimate differs from the published one"
STATUS_NT_INSIDE = "inside the tolerance, not testable at this resolution"


def load(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    assert_plan_constants()
    noctrl = load("runs/check-noctrl/metrics.json")
    main_runs = {l: load(f"runs/main-{l}/metrics.json") for l in LEARNERS}
    sens = load("runs/sens-lasso-c11/metrics.json")
    for l, m in main_runs.items():
        assert m["learner"] == l and m["n_splits"] == SPLITS[l] and m["n_obs"] == 9915, l
    assert main_runs["lasso"]["lasso_c_y"] == 0.5 and sens["lasso_c_y"] == 1.1
    assert sens["n_splits"] == SPLITS["lasso"] and sens["n_obs"] == 9915

    df = pd.read_csv(DATA, usecols=["net_tfa", "e401"])
    y, d = df.net_tfa.to_numpy(float), df.e401.to_numpy(float)
    base_inelig = float(y[d == 0].mean())
    base_elig = float(y[d == 1].mean())
    sd_y = float(y.std(ddof=1))

    v: dict = {"baseline_mean_net_tfa_ineligible": base_inelig,
               "baseline_mean_net_tfa_eligible": base_elig,
               "baseline_sd_net_tfa": sd_y,
               "noctrl_coef": noctrl["full_coef"], "noctrl_diff": noctrl["full_diff"],
               "noctrl_data_discrepancy": noctrl["data_discrepancy"],
               "noctrl_band_coef": noctrl["band_coef"]}

    h1_ok, n_outside, n_testable_inside, n_testable = True, 0, 0, 0
    for l in LEARNERS:
        m = main_runs[l]
        for k in FOLDS:
            cell = f"{l}_k{k}"
            ref = TOLERANCE_TABLE[(l, k)]
            theta, se_med, se_adj = m[f"theta_k{k}"], m[f"se_med_k{k}"], m[f"se_adj_k{k}"]
            # sanity: run metrics carry the same constants
            assert m[f"published_k{k}"] == ref["published"] and m[f"tolerance_k{k}"] == ref["tolerance"]
            assert m[f"testable_k{k}"] == ref["testable"]
            # se_pub recomputed from the published SEs agrees with the table (rounded to 0.1)
            se_pub = SE_MEDIAN_FACTOR * MAD_TO_SD * math.sqrt(ref["se_adj"] ** 2 - ref["se_med"] ** 2) / 10
            assert abs(se_pub - ref["se_pub"]) < 0.051, (cell, se_pub, ref["se_pub"])
            # H1
            lower = theta - Z_H1 * se_adj
            cell_h1 = theta > 0 and lower > 0
            h1_ok &= cell_h1
            # H2
            diff = theta - ref["published"]
            inside = abs(diff) <= ref["tolerance"]
            if not inside:
                n_outside += 1
                status = "fail"
            elif ref["testable"]:
                status = "pass"
            else:
                status = STATUS_NT_INSIDE
            if ref["testable"]:
                n_testable += 1
                n_testable_inside += int(inside)
            # descriptive tol_obs (decision_rules.H2_reading_of_failures)
            se_rep_obs = SE_MEDIAN_FACTOR * MAD_TO_SD * m[f"split_mad_k{k}"] / math.sqrt(SPLITS[l])
            tol_obs = BONF * math.sqrt(se_rep_obs ** 2 + ref["se_pub"] ** 2)
            reading = ""
            if not inside:
                reading = READING_INSIDE_OBS if abs(diff) <= tol_obs else READING_OUTSIDE_BOTH
            published_mad = math.sqrt(ref["se_adj"] ** 2 - ref["se_med"] ** 2)
            v.update({
                f"rep_theta_{cell}": theta, f"rep_se_med_{cell}": se_med, f"rep_se_adj_{cell}": se_adj,
                f"pub_theta_{cell}": ref["published"], f"pub_se_med_{cell}": ref["se_med"],
                f"pub_se_adj_{cell}": ref["se_adj"],
                f"h1_lower_{cell}": lower, f"h1_ok_{cell}": bool(cell_h1),
                f"diff_{cell}": diff, f"diff_in_pub_se_{cell}": diff / ref["se_med"],
                f"tolerance_{cell}": ref["tolerance"], f"testable_{cell}": ref["testable"],
                f"h2_inside_{cell}": bool(inside), f"h2_status_{cell}": status,
                f"tol_obs_{cell}": tol_obs, f"h2_reading_{cell}": reading,
                f"split_sd_obs_{cell}": m[f"split_sd_obs_k{k}"],
                f"split_sd_pub_{cell}": MAD_TO_SD * published_mad,
                f"implied_mad_obs_{cell}": m[f"implied_mad_obs_k{k}"], f"implied_mad_pub_{cell}": published_mad,
                f"se_med_ratio_{cell}": se_med / ref["se_med"], f"se_adj_ratio_{cell}": se_adj / ref["se_adj"],
                f"rmse_l_{cell}": m[f"rmse_l_k{k}"], f"rmse_m_{cell}": m[f"rmse_m_k{k}"],
                f"m_out_01_{cell}": m[f"m_out_01_k{k}"],
                f"rep_pct_inelig_{cell}": 100 * theta / base_inelig,
                f"pub_pct_inelig_{cell}": 100 * ref["published"] / base_inelig,
                f"rep_sd_units_{cell}": theta / sd_y, f"pub_sd_units_{cell}": ref["published"] / sd_y,
            })
    v["h1_holds"] = bool(h1_ok)
    v["h2_n_outside"] = n_outside
    v["h2_n_testable_inside"] = n_testable_inside
    v["h2_n_testable"] = n_testable
    v["h2_holds"] = bool(n_outside == 0 and n_testable_inside == n_testable == 8)

    # H3: main runs (the test) and sens-lasso-c11 (descriptive)
    h3_ok, h3_ok_c11 = True, True
    for k in FOLDS:
        lasso, lasso_c11 = main_runs["lasso"][f"theta_k{k}"], sens[f"theta_k{k}"]
        flex = {l: main_runs[l][f"theta_k{k}"] for l in FLEXIBLE}
        margin = min(flex.values()) - lasso
        margin_c11 = min(flex.values()) - lasso_c11
        v[f"h3_margin_k{k}"] = margin
        v[f"h3_ok_k{k}"] = bool(margin > 0)
        v[f"h3_margin_c11_k{k}"] = margin_c11
        v[f"h3_ok_c11_k{k}"] = bool(margin_c11 > 0)
        h3_ok &= margin > 0
        h3_ok_c11 &= margin_c11 > 0
        # sens-lasso-c11 next to the main lasso cell (never a claim value)
        ref = TOLERANCE_TABLE[("lasso", k)]
        v[f"sens_c11_theta_k{k}"] = lasso_c11
        v[f"sens_c11_se_adj_k{k}"] = sens[f"se_adj_k{k}"]
        v[f"sens_c11_diff_k{k}"] = lasso_c11 - ref["published"]
        v[f"sens_c11_inside_k{k}"] = bool(abs(lasso_c11 - ref["published"]) <= ref["tolerance"])
        v[f"sens_c11_minus_main_k{k}"] = lasso_c11 - lasso
    v["h3_holds"] = bool(h3_ok)
    v["h3_holds_c11_descriptive"] = bool(h3_ok_c11)
    v["nnet_iter_med_y"] = main_runs["nnet"]["nnet_iter_med_y"]
    v["nnet_iter_med_d"] = main_runs["nnet"]["nnet_iter_med_d"]
    for key, val in v.items():
        if isinstance(val, float) and not np.isfinite(val):
            raise SystemExit(f"ERROR: non-finite metric {key}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(v, indent=2) + "\n")
    print(json.dumps(v, indent=2))


if __name__ == "__main__":
    main()
