"""Run rob-covsets: primary estimator on re78 with two pre-fixed alternative conditioning sets (DEV-13).

Adopted from gallery/ss-null-effect/code/rob_covsets.py (716b6c3); the adopted rule applied to
these covariates:
(a) earnings-history core: age, educ, married, re74, re75, u74, u75 (B: 11 terms; T: 7 columns).
    Drops black, hisp and nodegree, so it also tests reliance on conditioning for race and
    ethnicity (design-r2 F6). In the disagreement rule: if its H1 decision differs from
    main-aipw's, the abstract says 'not robust to dropping race, ethnicity and degree status'.
(b) single lag: every covariate except re74 and u74 (B: 11 terms; T: 8 columns). Also removes
    the covariate whose measurement period differs between groups (F2). Changes the
    assumption; reported, never triggers.
Propensity (LogisticRegressionCV, primary settings) and outcome (HistGradientBoosting) models
re-fitted for each set; same folds, repetitions, seeds and upper clip.

Run from the workspace root:  .venv/bin/python -I code/rob_covsets.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/rob-covsets/metrics.json")
SETS = {"covset_a": L.COVSET_A, "covset_b": L.COVSET_B}


def main() -> int:
    df = L.load_covariates()
    main_m = L.read_json(L.MAIN_METRICS)
    y = L.load_re78(df)
    ok = L.admissible(y)
    df, y = df[ok].reset_index(drop=True), y[ok]
    d = df["treat"].to_numpy(int)
    met = {"seed_base": L.SEED}
    for name, covs in SETS.items():
        XB = L.basis(df, covs)
        Xb = XB.to_numpy(float)
        Xt = L.tree_features(df, covs)
        res = L.aipw(d, y, Xb, Xt)
        p = f"{name}_"
        met[f"{p}covariates"] = ",".join(c for c in L.COVS if c in covs)
        met[f"{p}dropped_covariates"] = ",".join(c for c in L.COVS if c not in covs)
        met[f"{p}basis_n_terms"] = int(Xb.shape[1])
        met[f"{p}tree_n_columns"] = int(Xt.shape[1])
        met.update(L.summarize(res, p))
        met.update(L.compare_with_main(met, p, main_m))
        met[f"{p}kish_ess_controls"] = res["kish_ess_controls"]
        met[f"{p}max_control_weight"] = res["max_control_weight"]
    met["covset_a_triggers_abstract_statement"] = bool(met["covset_a_h1_differs_from_main"])
    L.write_metrics(OUT, met)
    print({k: v for k, v in met.items() if k.endswith(("effect", "ci_low", "ci_high", "statement"))})
    return 0


if __name__ == "__main__":
    sys.exit(main())
