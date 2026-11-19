"""Runtime check for the ss-lalonde-observational design (plan.json design.runtime), outcome-blind.

Reads data/derived/analysis_noRE78.csv (row key, treat and the ten covariates; RE78 is
not in it) and refuses to run if an RE78 column is present. It never opens data/raw/.

Every outcome used here is synthetic Gaussian noise from a fixed seed, independent of
treatment and covariates, so nothing computed here says anything about any real outcome.
RE75 is used only as a covariate (in B(X) and T(X)), never as an outcome.

Placebo conditioning set (plan.json design_constraints): no statistic may be computed
under X- = X without re75 and u75 before the design gate. The placebo's propensity
cross-fit is therefore timed with a SYNTHETIC treatment (a seeded random permutation of
treat, which keeps 185 treated), so no fit of the real treatment on X- is ever made.

No balance or overlap statistic is printed or saved; those belong to run diag-overlap.
The one design constant saved besides timings is a precision multiplier: the standard
error the primary estimator gives for a unit-variance noise outcome with the real
full-set propensity (multiply by an outcome's residual SD to get a rough SE; it includes
the variance cost of ATT weighting and no gain from covariate adjustment).

Timings go to runs/timing-synthetic/timing.json (not reproducible, so not metrics);
runs/timing-synthetic/metrics.json holds only deterministic design constants.

Run from the workspace root:
    .venv/bin/python -I code/timing_synthetic.py
"""

import itertools
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import (HistGradientBoostingRegressor, RandomForestClassifier,
                              RandomForestRegressor)
from sklearn.linear_model import LinearRegression, LogisticRegressionCV
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path("data/derived/analysis_noRE78.csv")
OUT = Path("runs/timing-synthetic/timing.json")
METRICS = Path("runs/timing-synthetic/metrics.json")

SEED = 20261118
K, S = 5, 5
CLIP_HI = 0.99           # upper clip only (plan.json design.method.propensity_clipping)
BUDGET_MIN = 30
STARTUP_S = 3.0          # interpreter and import overhead per run
COVS = ["age", "educ", "black", "hisp", "married", "nodegree", "re74", "re75", "u74", "u75"]
COVS_MINUS = [c for c in COVS if c not in ("re75", "u75")]


def load() -> pd.DataFrame:
    header = set(pd.read_csv(DATA, nrows=0).columns)
    if {"re78", "RE78"} & header:
        sys.exit(f"ERROR: {DATA} contains an RE78 column; refusing to run")
    df = pd.read_csv(DATA, usecols=["treat"] + COVS)
    if df.isna().any().any():
        sys.exit("ERROR: missing values in treatment or covariates")
    return df


def basis(df: pd.DataFrame, covs: list[str]) -> np.ndarray:
    """B(X) on `covs`: continuous (age, educ, re74, re75) linear and squared; binaries linear."""
    cols = []
    for c in covs:
        cols.append(df[c].to_numpy(float))
        if c in ("age", "educ", "re74", "re75"):
            cols.append(df[c].to_numpy(float) ** 2)
    return np.column_stack(cols)


def basis_plus(df: pd.DataFrame, covs: list[str]) -> np.ndarray:
    """B+(X): B(X) and pairwise products, dropping products that are constant or duplicate a column."""
    X = basis(df, covs)
    cols = [X[:, j] for j in range(X.shape[1])]
    for a, b in itertools.combinations(covs, 2):
        p = df[a].to_numpy(float) * df[b].to_numpy(float)
        if np.all(p == p[0]) or any(np.array_equal(p, c) for c in cols):
            continue
        cols.append(p)
    return np.column_stack(cols)


def propensity_learner(seed: int):
    return make_pipeline(StandardScaler(), LogisticRegressionCV(
        Cs=np.logspace(-4, 4, 10), cv=StratifiedKFold(5, shuffle=True, random_state=seed),
        scoring="neg_log_loss", solver="lbfgs", max_iter=10_000))


def outcome_learner(seed: int):
    return HistGradientBoostingRegressor(
        loss="squared_error", learning_rate=0.05, max_iter=300, max_leaf_nodes=15,
        min_samples_leaf=20, l2_regularization=1.0, early_stopping=False, random_state=seed)


def folds(d: np.ndarray, s: int):
    return list(StratifiedKFold(K, shuffle=True, random_state=SEED + s).split(np.zeros(len(d)), d))


def crossfit_propensity(X, d, make=propensity_learner):
    m = np.zeros((S, len(d)))
    for s in range(S):
        for tr, te in folds(d, s):
            m[s, te] = make(SEED + s).fit(X[tr], d[tr]).predict_proba(X[te])[:, 1]
    return m


def crossfit_outcome(X, d, y, make=outcome_learner):
    g = np.zeros((S, len(d)))
    for s in range(S):
        for tr, te in folds(d, s):
            c = tr[d[tr] == 0]
            g[s, te] = make(SEED + s).fit(X[c], y[c]).predict(X[te])
    return g


def att_se(d, y, m_raw, g):
    """Mean-aggregated cross-fitted AIPW ATT SE (upper clip only)."""
    n, pi = len(d), d.mean()
    m = np.minimum(m_raw, CLIP_HI)
    thetas, ses = [], []
    for s in range(S):
        w = m[s] / (1 - m[s])
        num = d * (y - g[s]) - (1 - d) * w * (y - g[s])
        th = num.sum() / d.sum()
        psi = (num - d * th) / pi
        thetas.append(th); ses.append(np.sqrt(np.mean(psi ** 2) / n))
    thetas, ses = np.array(thetas), np.array(ses)
    return float(np.sqrt(np.mean(ses ** 2 + (thetas - thetas.mean()) ** 2)))


def timed(fn, *args):
    t0 = time.perf_counter()
    out = fn(*args)
    return out, time.perf_counter() - t0


def main() -> int:
    t_start = time.perf_counter()
    df = load()
    d = df["treat"].to_numpy(int)
    Xb, Xt = basis(df, COVS), df[COVS].to_numpy(float)
    Xb_minus, Xt_minus = basis(df, COVS_MINUS), df[COVS_MINUS].to_numpy(float)
    Xbp = basis_plus(df, COVS)

    rng = np.random.default_rng(SEED + 99)   # synthetic noise outcomes and treatment only
    y_noise = rng.normal(0.0, 1.0, len(d))
    d_synth = rng.permutation(d)             # synthetic treatment for the placebo-set timing

    T = {}
    m, T["A_propensity_crossfit"] = timed(crossfit_propensity, Xb, d)
    _, T["Aminus_propensity_crossfit_synthetic_treat"] = timed(crossfit_propensity, Xb_minus, d_synth)
    _, T["Aplus_propensity_crossfit"] = timed(crossfit_propensity, Xbp, d)
    g, T["G_outcome_crossfit"] = timed(crossfit_outcome, Xt, d, y_noise)
    _, T["Gminus_outcome_crossfit"] = timed(crossfit_outcome, Xt_minus, d_synth, y_noise)
    se_unit = att_se(d, y_noise, m, g)

    lin = lambda s: make_pipeline(StandardScaler(), LinearRegression())
    _, T["linear_outcome_crossfit"] = timed(crossfit_outcome, Xb, d, y_noise, lin)
    rf_c = lambda s: RandomForestClassifier(500, min_samples_leaf=5, max_features="sqrt",
                                            random_state=s, n_jobs=-1)
    rf_r = lambda s: RandomForestRegressor(500, min_samples_leaf=5, max_features="sqrt",
                                           random_state=s, n_jobs=-1)
    _, T["rf_propensity_crossfit"] = timed(crossfit_propensity, Xt, d, rf_c)
    _, T["rf_outcome_crossfit"] = timed(crossfit_outcome, Xt, d, y_noise, rf_r)

    A, Am, Ap = T["A_propensity_crossfit"], T["Aminus_propensity_crossfit_synthetic_treat"], T["Aplus_propensity_crossfit"]
    G, Gm = T["G_outcome_crossfit"], T["Gminus_outcome_crossfit"]
    # rob-trim is timed at full-sample cost (an upper bound): its trimmed size is an
    # overlap statistic that belongs to diag-overlap, not to this run.
    plan = {
        "diag-overlap": A,
        "main-aipw": A + G,
        "placebo-re75": Am + Gm,
        "rob-trim": A + A + G,
        "rob-learners": A + T["linear_outcome_crossfit"] + T["rf_propensity_crossfit"] + T["rf_outcome_crossfit"],
        "h2-benchmark": 0.0,
    }
    plan = {k: v + STARTUP_S for k, v in plan.items()}
    total = sum(plan.values())
    # Worst case: rule B1 fails, diag-overlap-ext runs, and B+(X) replaces B(X) in every
    # logistic propensity fit (placebo: B+ restricted to X-, timed here at the B+ cost).
    worst = total + (Ap + STARTUP_S) + (Ap - A) * 4 + (Ap - Am)
    out = {
        "covariate_source": str(DATA),
        "n": int(len(d)), "n_treated": int(d.sum()), "n_control": int(len(d) - d.sum()),
        "n_terms_B": int(Xb.shape[1]), "n_terms_B_minus": int(Xb_minus.shape[1]),
        "n_terms_B_plus": int(Xbp.shape[1]),
        "outcomes": "synthetic N(0,1) noise (numpy default_rng(20261217)), independent of treat and X",
        "placebo_set_timing": "propensity on B(X-) timed with a seeded permutation of treat (synthetic)",
        "cpu_note": "wall-clock seconds on the machine that ran this script",
        "block_seconds": {k: round(v, 2) for k, v in T.items()},
        "projected_run_seconds": {k: round(v, 1) for k, v in plan.items()},
        "projected_total_minutes": round(total / 60, 2),
        "projected_total_minutes_if_Bplus": round(worst / 60, 2),
        "budget_minutes": BUDGET_MIN,
        "within_budget": bool(worst / 60 <= BUDGET_MIN),
        "se_per_unit_outcome_sd": round(se_unit, 4),
        "se_per_unit_outcome_sd_note": "SE of the primary estimator for a N(0,1) noise outcome with the real full-set propensity",
        "script_seconds": round(time.perf_counter() - t_start, 1),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    METRICS.write_text(json.dumps({
        "n_obs": int(len(d)), "n_treated": int(d.sum()), "n_folds": K, "n_repetitions": S,
        "seed": SEED, "clip_upper": CLIP_HI, "n_terms_B": int(Xb.shape[1]),
        "n_terms_B_minus": int(Xb_minus.shape[1]), "n_terms_B_plus": int(Xbp.shape[1]),
        "budget_minutes": BUDGET_MIN,
    }, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
