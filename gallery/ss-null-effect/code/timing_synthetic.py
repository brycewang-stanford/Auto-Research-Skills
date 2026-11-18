"""Runtime check for the ss-null-effect design (plan.json design.runtime), outcome-blind.

Reads data/derived/covariates.csv (id, treat and the eleven covariates; it holds no
outcome) and, if that file is absent, generates synthetic covariates of the same shape.
Every outcome used here is synthetic noise from a fixed seed, independent of treatment
and covariates, so nothing computed here says anything about any real outcome. No
balance or overlap statistic is printed or saved; those belong to the diag-overlap run.

It times each building block of the planned runs, with the learners, folds, repetitions
and bootstrap sizes fixed in plan.json, and projects the total wall time of the
analysis plan. It also records a weighted precision proxy: the ATT standard error the
primary estimator gives for a noise outcome with re75's control-group variance, which
shows the variance cost of ATT weighting (no covariate adjustment gain is possible
with a noise outcome, so it is a conservative proxy).

Timings go to runs/timing-synthetic/timing.json (not reproducible, so not metrics);
the metrics file holds only deterministic design constants.

Run from the workspace root:
    .venv/bin/python -I code/timing_synthetic.py
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import expit
from sklearn.ensemble import (HistGradientBoostingRegressor, RandomForestClassifier,
                              RandomForestRegressor)
from sklearn.linear_model import LinearRegression, LogisticRegression, LogisticRegressionCV
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

COV = Path("data/derived/covariates.csv")
OUT = Path("runs/timing-synthetic/timing.json")
METRICS = Path("runs/timing-synthetic/metrics.json")

SEED = 20261118
K, S = 5, 5
B_MULT = 10_000
B_IPW = 999
ALPHAS = np.arange(0.0, 3.01, 0.5)
DELTAS = np.arange(0.0, 0.61, 0.1)
EM_MAX_ITER = 200
BUDGET_MIN = 30
OUTCOME_NAMES = {"re78", "re79", "employed78", "hours78", "benefits78", "wellbeing78"}
COVS = ["age", "educ", "married", "urban", "region", "children", "health_limit",
        "re74", "re75", "unemp74", "unemp75"]


def load_covariates() -> tuple[pd.DataFrame, str]:
    if COV.exists():
        df = pd.read_csv(COV)
        leaked = OUTCOME_NAMES & set(df.columns) or {c for c in df.columns if c.startswith("survey_")}
        if leaked:
            sys.exit(f"ERROR: {COV} contains outcome columns {sorted(leaked)}; refusing to run")
        return df[["treat"] + COVS], str(COV)
    rng = np.random.default_rng(SEED)
    n = 4000
    df = pd.DataFrame({
        "age": rng.integers(18, 56, n), "educ": rng.integers(6, 18, n),
        "married": rng.integers(0, 2, n), "urban": rng.integers(0, 2, n),
        "region": rng.choice(["northeast", "midwest", "south", "west"], n),
        "children": rng.integers(0, 5, n), "health_limit": rng.integers(0, 2, n),
        "re74": np.where(rng.random(n) < 0.3, 0.0, rng.lognormal(8.5, 1.0, n)),
        "re75": np.where(rng.random(n) < 0.3, 0.0, rng.lognormal(8.5, 1.0, n)),
    })
    df["unemp74"] = (df.re74 == 0).astype(int)
    df["unemp75"] = (df.re75 == 0).astype(int)
    df["treat"] = (rng.random(n) < expit(-0.4 + 0.3 * df.unemp75 - 0.02 * (df.age - 35))).astype(int)
    return df[["treat"] + COVS], "synthetic"


def basis(df: pd.DataFrame) -> np.ndarray:
    """B(X): 17 terms (plan.json design.method.covariate_bases)."""
    cols = [df.age, df.age ** 2, df.educ, df.educ ** 2, df.children, df.married, df.urban,
            df.health_limit, df.re74, df.re74 ** 2, df.re75, df.re75 ** 2, df.unemp74, df.unemp75]
    cols += [(df.region == r).astype(float) for r in ("northeast", "south", "west")]
    return np.column_stack([np.asarray(c, dtype=float) for c in cols])


def tree_features(df: pd.DataFrame) -> np.ndarray:
    """T(X): eleven covariates with region one-hot (14 columns)."""
    num = df[["age", "educ", "married", "urban", "children", "health_limit",
              "re74", "re75", "unemp74", "unemp75"]].to_numpy(float)
    reg = np.column_stack([(df.region == r).to_numpy(float)
                           for r in ("northeast", "midwest", "south", "west")])
    return np.hstack([num, reg])


def propensity_learner(seed: int):
    return make_pipeline(StandardScaler(), LogisticRegressionCV(
        Cs=np.logspace(-4, 4, 10), cv=StratifiedKFold(5, shuffle=True, random_state=seed),
        scoring="neg_log_loss", max_iter=10_000))


def outcome_learner(seed: int):
    return HistGradientBoostingRegressor(
        learning_rate=0.05, max_iter=300, max_leaf_nodes=15, min_samples_leaf=20,
        l2_regularization=1.0, early_stopping=False, random_state=seed)


def folds(d: np.ndarray, s: int):
    return list(StratifiedKFold(K, shuffle=True, random_state=SEED + s).split(np.zeros(len(d)), d))


def crossfit_propensity(Xb, d, make=propensity_learner):
    m = np.zeros((S, len(d)))
    for s in range(S):
        for tr, te in folds(d, s):
            m[s, te] = make(SEED + s).fit(Xb[tr], d[tr]).predict_proba(Xb[te])[:, 1]
    return np.clip(m, 0.01, 0.99)


def crossfit_outcome(Xt, d, y, make=outcome_learner):
    g = np.zeros((S, len(d)))
    for s in range(S):
        for tr, te in folds(d, s):
            c = tr[d[tr] == 0]
            g[s, te] = make(SEED + s).fit(Xt[c], y[c]).predict(Xt[te])
    return g


def att(d, y, m, g):
    """Mean-aggregated cross-fitted AIPW ATT: theta, SE, averaged influence function."""
    n, pi = len(d), d.mean()
    thetas, ses, psis = [], [], []
    for s in range(S):
        w = m[s] / (1 - m[s])
        num = d * (y - g[s]) - (1 - d) * w * (y - g[s])
        theta = num.sum() / d.sum()
        psi = (num - d * theta) / pi
        thetas.append(theta); ses.append(np.sqrt(np.mean(psi ** 2) / n)); psis.append(psi)
    thetas, ses = np.array(thetas), np.array(ses)
    theta = thetas.mean()
    se = np.sqrt(np.mean(ses ** 2 + (thetas - theta) ** 2))
    return theta, se, np.mean(psis, axis=0)


def multiplier_rw(thetas, ses, psis):
    """Gaussian multiplier bootstrap, Romano-Wolf stepdown and max-t critical value."""
    n = psis.shape[1]
    rng = np.random.default_rng(SEED + 1)
    tstar = np.empty((B_MULT, len(thetas)))
    for start in range(0, B_MULT, 1000):  # chunks keep memory small
        xi = rng.standard_normal((min(1000, B_MULT - start), n))
        tstar[start:start + len(xi)] = (xi @ psis.T / n) / ses
    absT = np.abs(tstar)
    t = np.abs(thetas / ses)
    order = np.argsort(-t)
    p_adj = np.empty(len(t))
    prev = 0.0
    for j, k in enumerate(order):
        p = np.mean(absT[:, order[j:]].max(axis=1) >= t[k])
        prev = max(prev, p)
        p_adj[k] = prev
    return p_adj, np.quantile(absT.max(axis=1), 0.95)


def imbens_em(d, y, Z, alpha, delta):
    """One Imbens (2003) grid point by generalized EM; returns tau."""
    W = np.column_stack([d, Z])
    gamma = np.zeros(Z.shape[1]); b = np.linalg.lstsq(W, y, rcond=None)[0]
    sigma2 = np.mean((y - W @ b) ** 2); ll_old = -np.inf
    for _ in range(EM_MAX_ITER):
        p0, p1 = expit(Z @ gamma), expit(Z @ gamma + alpha)
        r = y - W @ b
        l0 = np.where(d == 1, p0, 1 - p0) * np.exp(-r ** 2 / (2 * sigma2))
        l1 = np.where(d == 1, p1, 1 - p1) * np.exp(-(r - delta) ** 2 / (2 * sigma2))
        ll = np.sum(np.log(0.5 * (l0 + l1) + 1e-300))
        q = l1 / (l0 + l1 + 1e-300)
        grad = Z.T @ (d - (1 - q) * p0 - q * p1)
        h = (1 - q) * p0 * (1 - p0) + q * p1 * (1 - p1)
        gamma = gamma + np.linalg.solve((Z * h[:, None]).T @ Z + 1e-8 * np.eye(Z.shape[1]), grad)
        b = np.linalg.lstsq(W, y - delta * q, rcond=None)[0]
        sigma2 = np.mean((y - delta * q - W @ b) ** 2 + delta ** 2 * q * (1 - q))
        if abs(ll - ll_old) < 1e-8 * abs(ll):
            break
        ll_old = ll
    return b[0]


def timed(fn, *args):
    t0 = time.perf_counter()
    out = fn(*args)
    return out, time.perf_counter() - t0


def main() -> int:
    t_start = time.perf_counter()
    df, source = load_covariates()
    d = df["treat"].to_numpy(int)
    Xb, Xt = basis(df), tree_features(df)
    Xminus = df.drop(columns=["re75", "unemp75"]).assign(re75=0.0, unemp75=0)
    Xb_minus = np.delete(basis(Xminus), [10, 11, 13], axis=1)  # drop re75, re75^2, unemp75
    rng = np.random.default_rng(SEED + 99)  # synthetic noise outcomes only
    var_proxy = float(df.loc[df.treat == 0, "re75"].var(ddof=1))
    noise = {"y0_re75var": rng.normal(0, np.sqrt(var_proxy), len(d))}
    for k in range(1, 6):
        noise[f"y{k}"] = rng.normal(0, 1, len(d))

    T = {}
    m, T["A_propensity_crossfit"] = timed(crossfit_propensity, Xb, d)
    _, T["A_minus_propensity_crossfit"] = timed(crossfit_propensity, Xb_minus, d)
    g, T["G_outcome_crossfit"] = timed(crossfit_outcome, Xt, d, noise["y0_re75var"])
    theta0, se0, _ = att(d, noise["y0_re75var"], m, g)

    t0 = time.perf_counter()
    fam = [att(d, noise[f"y{k}"], m, crossfit_outcome(Xt, d, noise[f"y{k}"])) for k in range(1, 6)]
    T["family_5_outcome_crossfits"] = time.perf_counter() - t0
    th = np.array([f[0] for f in fam]); se = np.array([f[1] for f in fam])
    ps = np.vstack([f[2] for f in fam])
    (p_rw, crit), T["multiplier_bootstrap_rw"] = timed(multiplier_rw, th, se, ps)

    rf_c = lambda s: RandomForestClassifier(500, min_samples_leaf=5, max_features="sqrt", random_state=s, n_jobs=-1)
    rf_r = lambda s: RandomForestRegressor(500, min_samples_leaf=5, max_features="sqrt", random_state=s, n_jobs=-1)
    t0 = time.perf_counter()
    crossfit_propensity(Xt, d, rf_c); crossfit_outcome(Xt, d, noise["y1"], rf_r)
    T["rf_learners_crossfit"] = time.perf_counter() - t0
    lin = lambda s: make_pipeline(StandardScaler(), LinearRegression())
    _, T["linear_outcome_crossfit"] = timed(crossfit_outcome, Xb, d, noise["y1"], lin)

    t0 = time.perf_counter()
    c_full = propensity_learner(SEED).fit(Xb, d)[-1].C_[0]
    brng = np.random.default_rng(SEED + 2)
    for _ in range(B_IPW):
        idx = brng.integers(0, len(d), len(d))
        make_pipeline(StandardScaler(), LogisticRegression(C=c_full, max_iter=10_000)).fit(Xb[idx], d[idx])
    T["ipw_bootstrap_999"] = time.perf_counter() - t0

    Z = np.column_stack([np.ones(len(d)), StandardScaler().fit_transform(Xb)])
    y_sd = noise["y1"].std()
    probe = [(a, dl) for a in (0.5, 3.0) for dl in (0.1, 0.6)]
    t0 = time.perf_counter()
    for a, dl in probe:
        imbens_em(d, noise["y1"], Z, a, dl * y_sd)
    per_point = (time.perf_counter() - t0) / len(probe)
    T["imbens_grid_49_projected"] = per_point * len(ALPHAS) * len(DELTAS)

    A, Am, G = T["A_propensity_crossfit"], T["A_minus_propensity_crossfit"], T["G_outcome_crossfit"]
    startup = 3.0  # interpreter and import overhead per run, seconds
    plan = {
        "diag-overlap": A,
        "main-aipw": A + G,
        "secondary-family": A + T["family_5_outcome_crossfits"] + T["multiplier_bootstrap_rw"],
        "placebo-re75": Am + G,
        "rob-trim": A + A + G,
        "rob-covsets": 2 * (A + G),
        "rob-learners": A + T["linear_outcome_crossfit"] + T["rf_learners_crossfit"],
        "rob-diff": Am + G,
        "rob-estimators": A / (S * K) + T["ipw_bootstrap_999"],
        "sens-imbens": T["imbens_grid_49_projected"] + 2 * len(COVS) * per_point,
    }
    plan = {k: v + startup for k, v in plan.items()}
    total = sum(plan.values())
    out = {
        "covariate_source": source,
        "n": int(len(d)), "n_treated": int(d.sum()),
        "outcomes": "synthetic Gaussian noise (seed 20261217), independent of treat and X",
        "cpu_note": "wall-clock seconds on the machine that ran this script",
        "block_seconds": {k: round(v, 2) for k, v in T.items()},
        "projected_run_seconds": {k: round(v, 1) for k, v in plan.items()},
        "projected_total_minutes": round(total / 60, 2),
        "budget_minutes": BUDGET_MIN,
        "within_budget": bool(total / 60 <= BUDGET_MIN),
        "weighted_precision_proxy_se": round(float(se0), 2),
        "weighted_precision_proxy_note": "SE of the primary estimator for a noise outcome with re75's control variance; compare with M",
        "synthetic_family_maxt_crit": round(float(crit), 3),
        "script_seconds": round(time.perf_counter() - t_start, 1),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    METRICS.write_text(json.dumps({
        "n_obs": int(len(d)), "n_folds": K, "n_repetitions": S, "n_multiplier_draws": B_MULT,
        "n_ipw_bootstrap": B_IPW, "sens_grid_points": int(len(ALPHAS) * len(DELTAS)),
        "seed": SEED, "budget_minutes": BUDGET_MIN,
    }, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
