"""Run placebo-re75: the H3 placebo (plan.json design.method.h3_placebo).

The primary estimator (code/aipw_lib.py) with outcome re75 (1982 dollars) and conditioning set
X- = (age, educ, black, hisp, married, nodegree, re74, u74), i.e. X without re75 and u75:
B(X-) 11 terms for the propensity (re-fitted on B(X-)), T(X-) 8 columns for the outcome
model; same folds, repetitions, seeds, upper clip at 0.99 and SE rule; all 16,177 units.
Adopted from gallery/ss-null-effect/code/select_re75.py (716b6c3), now a decision rule.

Data: only data/derived/analysis_noRE78.csv (via diag_overlap.load, which refuses a file with
an re78 column). This script never opens data/raw or data/derived/re78_by_key.csv and never
reads re78; re75 and u75 are the outcome and its zero indicator and enter no basis.

Rule (fixed), in this order: FAIL if the 95% CI excludes 0 (precedence); otherwise PASS if
-900 <= ci_low and ci_high <= 900; otherwise INCONCLUSIVE (aipw_lib.placebo_verdict).
Codes: pass 1, inconclusive 0, fail -1. A pass is worded only as 'the placebo did not reject'.
Outcome validity: the re78 rule applied to re75 (DEV-12); complete cases if any value fails.
Also reported, descriptively (no rule depends on them): clipped-unit count, Kish ESS of the
weighted controls, the largest control weight, ATT-weighted SMDs on B(X-) (weights averaged
over repetitions, as diag-overlap), and the CPS re75 top-code count (3,007 men at the maximum
in the codebook; recomputed here).

Run from the workspace root:  .venv/bin/python -I code/placebo_re75.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402
import diag_overlap  # noqa: E402  (wsmd: the pre-gate weighted-SMD definition)

OUT = Path("runs/placebo-re75/metrics.json")


def main() -> int:
    if {"re75", "u75"} & set(L.X_MINUS):
        sys.exit("ERROR: X- must exclude re75 and u75")
    df = L.load_covariates()
    y_all = df["re75"].to_numpy(float)
    d_all = df["treat"].to_numpy(int)
    counts = L.outcome_counts(y_all, d_all, "re75")
    ok = L.admissible(y_all, "re75")
    sub = df[ok].reset_index(drop=True)
    d = sub["treat"].to_numpy(int)
    y = y_all[ok]
    XB = L.basis(sub, L.X_MINUS)
    if {"re75", "re75_sq", "u75"} & set(XB.columns):
        sys.exit("ERROR: B(X-) contains a re75 term")
    Xb = XB.to_numpy(float)
    Xt = L.tree_features(sub, L.X_MINUS)
    res = L.aipw(d, y, Xb, Xt)

    met = {"outcome": "re75 (placebo; 1982 dollars)", "conditioning_set": ",".join(L.X_MINUS),
           "basis_terms": ",".join(XB.columns), "basis_n_terms": int(Xb.shape[1]),
           "tree_n_columns": int(Xt.shape[1]), "seed_base": L.SEED, "bound": L.PLACEBO_BOUND}
    met.update(L.summarize(res))
    del met["h1_holds"]  # not an H1 quantity
    met.update(L.per_repetition(res))
    verdict, code = L.placebo_verdict(met["ci_low"], met["ci_high"])
    met["verdict"] = verdict
    met["verdict_code"] = code
    met["ci_excludes_zero"] = bool(met["ci_low"] > 0 or met["ci_high"] < 0)
    met["ci_within_bound"] = bool(-L.PLACEBO_BOUND <= met["ci_low"] and met["ci_high"] <= L.PLACEBO_BOUND)
    met["se_needed_for_pass_at_zero"] = L.PLACEBO_BOUND / L.Z95
    met["n_clipped_unit_reps"] = res["n_clipped_unit_reps"]
    met["n_convergence_warnings"] = res["n_convergence_warnings"]
    met["kish_ess_controls"] = res["kish_ess_controls"]
    met["max_control_weight"] = res["max_control_weight"]

    # Descriptive balance on B(X-) with the placebo's own weights.
    w = L.control_weights(res["m_raw"], d)
    smd = {c: diag_overlap.wsmd(XB[c].to_numpy(), d, w) for c in XB.columns}
    for c in XB.columns:
        met[f"smd_w_{c}"] = smd[c]
    worst = max(smd, key=lambda c: abs(smd[c]))
    met["smd_w_max_abs"] = abs(smd[worst])
    met["smd_w_max_abs_term"] = worst

    cps = y_all[d_all == 0]
    met["cps_re75_at_max"] = int(np.sum(cps == cps.max()))
    met.update(counts)
    L.write_metrics(OUT, met)
    print({k: met[k] for k in ("effect", "se", "ci_low", "ci_high", "verdict", "n_clipped_units")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
