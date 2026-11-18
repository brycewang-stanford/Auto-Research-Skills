"""Run rob-learners: the primary AIPW ATT score on re78 with alternative nuisance learners.

(a) parametric: propensity LogisticRegressionCV on B(X) (the primary propensity learner) and
    OLS of Y on B(X) among the controls of the training folds (standardized within fold;
    OLS predictions do not depend on the scaling).
(b) random forests on T(X): RandomForestClassifier and RandomForestRegressor, 500 trees,
    min_samples_leaf 5, max_features 'sqrt', random_state = seed of the repetition
    (20261118 + s); propensity clipped to [0.01, 0.99] as in the primary estimator.
Same folds, repetitions and seeds as the primary. Both are in the disagreement rule.

Run from the workspace root:  .venv/bin/python -I code/rob_learners.py
"""

import sys
from pathlib import Path

from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/rob-learners/metrics.json")


def ols(seed: int):
    return make_pipeline(StandardScaler(), LinearRegression())


def rf_c(seed: int):
    return RandomForestClassifier(n_estimators=500, min_samples_leaf=5, max_features="sqrt",
                                  random_state=seed, n_jobs=-1)


def rf_r(seed: int):
    return RandomForestRegressor(n_estimators=500, min_samples_leaf=5, max_features="sqrt",
                                 random_state=seed, n_jobs=-1)


def main() -> int:
    df = L.load_data(["re78"])
    L.check_basis_reuse(df)
    M = float(L.read_json(L.MARGIN_FILE)["margin_M"])
    main_m = L.read_json(L.MAIN_METRICS)
    df = df[L.admissible(df["re78"], "re78")].reset_index(drop=True)
    d = df["treat"].to_numpy(int)
    y = df["re78"].to_numpy(float)
    Xb = L.basis(df, L.COVS).to_numpy(float)
    Xt = L.tree_features(df, L.COVS)
    met = {"margin_M": M, "seed_base": L.SEED}

    lin = L.aipw(d, y, Xb, Xb, out_make=ols)
    met.update(L.summarize(lin, "linear_", M))
    met.update(L.compare_with_main(met, "linear_", main_m))

    rf = L.aipw(d, y, Xt, Xt, prop_make=rf_c, out_make=rf_r)
    met.update(L.summarize(rf, "rf_", M))
    met.update(L.compare_with_main(met, "rf_", main_m))
    met["rf_n_clipped_unit_reps"] = rf["n_clipped_unit_reps"]

    met["linear_triggers_abstract_statement"] = bool(
        met["linear_h1_differs_from_main"] or met["linear_h1b_differs_from_main"])
    met["rf_triggers_abstract_statement"] = bool(
        met["rf_h1_differs_from_main"] or met["rf_h1b_differs_from_main"])
    L.write_metrics(OUT, met)
    print(met)
    return 0


if __name__ == "__main__":
    sys.exit(main())
