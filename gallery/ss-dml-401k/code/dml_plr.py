"""DML2 partially linear regression (PLR) of net_tfa on e401 with five nuisance learners.

Implements plan.json design.method and design.learners exactly as fixed at the design gate:

* Robinson partialling-out score, pooled over folds (the authors' lm(ry ~ rz - 1)):
  theta_s = sum(V U) / sum(V^2), sigma_s^2 = sum(V^2 (U - theta_s V)^2) / (sum V^2)^2 (HC0).
* Aggregation over S splits (Definition 3.3): theta_med = median_s theta_s,
  bracketed SE = median_s sigma_s, adjusted SE (eq. 3.14) = sqrt(median_s(sigma_s^2 + (theta_s - theta_med)^2)).
* Partition (s, K): numpy.random.default_rng(SeedSequence([1211, K, s])).permutation(n) cut into
  K consecutive blocks (numpy.array_split). All learners share the partition for the same (s, K).
* Every nuisance fit is seeded with SeedSequence([1211, K, s, fold, learner index, nuisance]).

The learner functions (rlasso_fit_predict, rlassologit_fit_predict, tree_fit_predict,
forest_fit_predict, boost_fit_predict, nnet_fit_predict) are imported unchanged by
code/check_learner_ports.py, which compares them with the authors' R calls on synthetic data.

Usage (analysis runs, only after the design gate):
    python code/dml_plr.py --learner lasso --splits 100 [--lasso-c-y 0.5] [--run-id main-lasso]
writes runs/<run-id>/metrics.json (flat), runs/<run-id>/splits.csv and runs/<run-id>/timing.json.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

COVARIATES = ["age", "inc", "educ", "fsize", "marr", "twoearn", "db", "pira", "hown"]
OUTCOME, TREATMENT = "net_tfa", "e401"
DATA = Path("data/derived/sipp1991.csv")
N_EXPECTED = 9915
LEARNERS = ["lasso", "tree", "forest", "boosting", "nnet"]
LEARNER_INDEX = {"lasso": 1, "tree": 2, "forest": 3, "boosting": 4, "nnet": 5}
SPLITS = {"lasso": 100, "tree": 100, "nnet": 100, "forest": 40, "boosting": 30}  # design.splits
FOLDS = (2, 5)
BASE_SEED = 1211

# design.tolerance_table, copied verbatim (asserted equal to plan.json by assert_plan_constants).
# (learner, K): published, published bracketed SE, published adjusted SE, tolerance, mds80, testable
TOLERANCE_TABLE = {
    ("lasso", 2): dict(published=7717, se_pub=207.5, se_med=1346, se_adj=1749, tolerance=825, mds80=1072, testable=False),
    ("tree", 2): dict(published=8709, se_pub=78.5, se_med=1363, se_adj=1427, tolerance=312, mds80=405, testable=True),
    ("forest", 2): dict(published=9116, se_pub=83.3, se_med=1302, se_adj=1377, tolerance=438, mds80=569, testable=True),
    ("boosting", 2): dict(published=8759, se_pub=63.6, se_med=1339, se_adj=1382, tolerance=372, mds80=483, testable=True),
    ("nnet", 2): dict(published=8950, se_pub=83.1, se_med=1335, se_adj=1408, tolerance=330, mds80=429, testable=True),
    ("lasso", 5): dict(published=8187, se_pub=160.1, se_med=1298, se_adj=1558, tolerance=636, mds80=827, testable=False),
    ("tree", 5): dict(published=8871, se_pub=75.8, se_med=1358, se_adj=1418, tolerance=301, mds80=392, testable=True),
    ("forest", 5): dict(published=9247, se_pub=54.7, se_med=1295, se_adj=1328, tolerance=287, mds80=373, testable=True),
    ("boosting", 5): dict(published=9110, se_pub=35.7, se_med=1314, se_adj=1328, tolerance=209, mds80=272, testable=True),
    ("nnet", 5): dict(published=9038, se_pub=55.2, se_med=1322, se_adj=1355, tolerance=219, mds80=285, testable=True),
}
MAD_TO_SD = 1.4826
ZERO_THRESHOLD = 1e-6  # hdm LassoShooting.fit control$zeroThreshold (all hdm versions)


def assert_plan_constants(plan_path: Path = Path("plan.json")) -> None:
    """Check the constants above against plan.json design (read-only; plan.json is not an
    input of any run because gate decisions rewrite it, which would invalidate the run hash)."""
    design = json.loads(plan_path.read_text(encoding="utf-8"))["design"]
    for row in design["tolerance_table"]:
        mine = TOLERANCE_TABLE[(row["learner"], row["folds"])]
        theirs = dict(published=row["published"], se_pub=row["se_pub"], se_med=row["published_se_median"],
                      se_adj=row["published_se_adjusted"], tolerance=row["tolerance"],
                      mds80=row["mds80"], testable=row["testable"])
        assert mine == theirs, f"tolerance_table mismatch for {row['claim_id']}: {mine} != {theirs}"
        assert row["S_replication"] == SPLITS[row["learner"]], f"S mismatch for {row['claim_id']}"
    for learner, s in SPLITS.items():
        assert design["splits"][learner] == s, f"design.splits[{learner}] != {s}"
    assert len(design["tolerance_table"]) == len(TOLERANCE_TABLE)


# ====================================================================== seeds and partitions
def fit_seed(*entropy: int) -> int:
    """Integer seed for one estimator, derived from a SeedSequence of the given entropy."""
    return int(np.random.SeedSequence(list(entropy)).generate_state(1)[0])


def partition(n: int, k: int, s: int) -> list[np.ndarray]:
    """Random partition of 0..n-1 into k consecutive blocks of a permutation (sizes differ by <= 1)."""
    rng = np.random.default_rng(np.random.SeedSequence([BASE_SEED, k, s]))
    return np.array_split(rng.permutation(n), k)


# ====================================================================== lasso dictionary
def dictionary(X: np.ndarray) -> np.ndarray:
    """401K.R xl: (poly(age,6,raw) + poly(inc,8,raw) + poly(educ,4,raw) + poly(fsize,2,raw)
    + marr + twoearn + db + pira + hown)^2 -> 25 main columns + 250 products of columns from
    different terms = 275 columns, raw powers. X columns in COVARIATES order."""
    col = {name: X[:, j].astype(float) for j, name in enumerate(COVARIATES)}
    terms = [np.column_stack([col[v] ** p for p in range(1, deg + 1)])
             for v, deg in (("age", 6), ("inc", 8), ("educ", 4), ("fsize", 2))]
    terms += [col[v][:, None] for v in ("marr", "twoearn", "db", "pira", "hown")]
    cols = list(terms)
    for a in range(len(terms)):
        for b in range(a + 1, len(terms)):
            cols.append(np.einsum("ni,nj->nij", terms[a], terms[b]).reshape(X.shape[0], -1))
    out = np.column_stack(cols)
    assert out.shape[1] == 275
    return out


# ====================================================================== learners
def rlasso_fit_predict(Xtr, ytr, Xte, c=0.5, num_iter=15, tol=1e-5):
    """Port of hdm::rlasso(post = FALSE, intercept = TRUE), heteroskedastic, X-independent penalty,
    including LassoShooting.fit's 1e-6 zero threshold on unscaled coefficients after every solve.

    Returns (predictions on Xte, info dict with lambda0, n, p, iterations)."""
    from sklearn.linear_model import Lasso, LinearRegression
    n, p = Xtr.shape  # p = 275 in the penalty even if columns are constant in this fold
    sd = Xtr.std(axis=0)
    keep = sd > 0  # constant columns dropped before fitting
    Xs, Xts = Xtr[:, keep] / sd[keep], Xte[:, keep] / sd[keep]  # scale only; loadings absorb it
    sd_keep = sd[keep]
    mx, my = Xs.mean(axis=0), ytr.mean()
    Xc, yc = Xs - mx, ytr - my
    gamma = 0.1 / np.log(n)
    lam0 = 2 * c * np.sqrt(n) * norm.ppf(1 - gamma / (2 * p))
    # starting residuals: OLS of y on the 5 columns most correlated with y (hdm init_values)
    corr = np.abs(Xc.T @ yc) / (np.sqrt((Xc ** 2).sum(axis=0)) * np.sqrt((yc ** 2).sum()))
    top = np.argsort(-corr, kind="stable")[:5]
    e = yc - LinearRegression().fit(Xc[:, top], yc).predict(Xc[:, top])
    psi = np.sqrt((Xc ** 2 * e[:, None] ** 2).mean(axis=0))
    s0 = yc.std(ddof=1)
    coef = np.zeros(Xc.shape[1])
    it = 0
    for it in range(1, num_iter + 1):
        model = Lasso(alpha=lam0 / (2 * n), fit_intercept=False, tol=1e-6, max_iter=100000)
        model.fit(Xc / psi, yc)
        coef = model.coef_ / psi  # coefficients on the SD-scaled centered columns
        # hdm LassoShooting.fit zeroThreshold: w[abs(w) < 1e-6] <- 0 on the centered but
        # otherwise unscaled dictionary columns, no re-optimization (design.learners.lasso.Y_learner)
        coef[np.abs(coef / sd_keep) < ZERO_THRESHOLD] = 0.0
        e = yc - Xc @ coef
        s1 = e.std(ddof=1)
        psi = np.sqrt((Xc ** 2 * e[:, None] ** 2).mean(axis=0))
        if abs(s0 - s1) < tol:
            break
        s0 = s1
    pred = my + (Xts - mx) @ coef
    return pred, {"lambda0": float(lam0), "n": int(n), "p": int(p), "iter": int(it),
                  "nonzero": int((coef != 0).sum())}


def rlassologit_fit_predict(Xtr, dtr, Xte, c=1.1, seed=0):
    """Port of hdm::rlassologit(post = FALSE, intercept = TRUE, c): glmnet binomial at
    lambda = lambda0/(2n), lambda0 = (c/2) sqrt(n) qnorm(1 - gamma/(2p)), standardize = TRUE.
    Returns (predicted probabilities on Xte, info dict)."""
    from sklearn.linear_model import LogisticRegression
    n, p = Xtr.shape
    sd = Xtr.std(axis=0)  # population SD, as glmnet's standardize
    keep = sd > 0
    mu = Xtr[:, keep].mean(axis=0)
    Xs, Xts = (Xtr[:, keep] - mu) / sd[keep], (Xte[:, keep] - mu) / sd[keep]
    gamma = 0.1 / np.log(n)
    lam0 = c / 2 * np.sqrt(n) * norm.ppf(1 - gamma / (2 * p))
    clf = LogisticRegression(l1_ratio=1.0, C=2.0 / lam0, solver="liblinear", intercept_scaling=100.0,
                             tol=1e-6, max_iter=1000, random_state=seed)
    clf.fit(Xs, dtr)
    return clf.predict_proba(Xts)[:, 1], {"lambda0": float(lam0), "n": int(n), "p": int(p),
                                          "nonzero": int((clf.coef_ != 0).sum())}


def tree_fit_predict(Xtr, ytr, Xte, seed, cp=0.01, xval=10):
    """rpart(method = 'anova', cp = 0.01, minsplit = 20, minbucket = 7, maxdepth = 30, xval = 10),
    pruned at the cptable CP with minimum CV error (first minimum, no 1-SE rule)."""
    from sklearn.model_selection import KFold
    from sklearn.tree import DecisionTreeRegressor
    kw = dict(criterion="squared_error", min_samples_split=20, min_samples_leaf=7, max_depth=30,
              random_state=seed)
    var = ytr.var()  # population variance = root impurity; rpart cp = ccp_alpha / var
    full = DecisionTreeRegressor(**kw).fit(Xtr, ytr)
    alphas = full.cost_complexity_pruning_path(Xtr, ytr).ccp_alphas
    cps = np.unique(alphas[alphas >= cp * var] / var)[::-1]  # cptable, largest (root) first
    if cps.size == 0 or cps[-1] > cp:
        cps = np.append(cps, cp)  # the cp = 0.01 row (tree grown to cp)
    geo = np.sqrt(cps * np.append(1.0, cps[:-1]))  # geometric mean with the next larger cp; 1.0 for the root
    err = np.zeros(len(cps))
    for tr, va in KFold(xval, shuffle=True, random_state=seed).split(Xtr):
        v = ytr[tr].var()
        for i, g in enumerate(geo):
            m = DecisionTreeRegressor(ccp_alpha=g * v, **kw).fit(Xtr[tr], ytr[tr])
            err[i] += ((m.predict(Xtr[va]) - ytr[va]) ** 2).sum()
    best = int(np.argmin(err))  # first minimum, as which.min
    return DecisionTreeRegressor(ccp_alpha=geo[best] * var, **kw).fit(Xtr, ytr).predict(Xte)


def forest_fit_predict(Xtr, ytr, Xte, seed, nodesize):
    """randomForest(ntree = 1000, mtry = 3, nodesize, replace = TRUE), regression for Y and D."""
    from sklearn.ensemble import RandomForestRegressor
    m = RandomForestRegressor(n_estimators=1000, max_features=3, bootstrap=True, min_samples_leaf=1,
                              min_samples_split=nodesize + 1, criterion="squared_error", n_jobs=1,
                              random_state=seed)
    return m.fit(Xtr, ytr).predict(Xte)


def boost_fit_predict(Xtr, ytr, Xte, seed, binary):
    """gbm(n.trees = 1000, shrinkage = 0.01, interaction.depth = 2, bag.fraction = 0.5,
    n.minobsinnode = 10, cv.folds = 5); 'gaussian' for Y, 'adaboost' for D; prediction with the
    number of trees minimizing the 5-fold CV loss (gbm.perf(method = 'cv'))."""
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor
    from sklearn.model_selection import KFold
    kw = dict(n_estimators=1000, learning_rate=0.01, subsample=0.5, max_leaf_nodes=3, max_depth=None,
              min_samples_leaf=10, random_state=seed)
    if binary:
        Est, kw["loss"] = GradientBoostingClassifier, "exponential"
    else:
        Est, kw["loss"] = GradientBoostingRegressor, "squared_error"
    cv_loss = np.zeros(1000)
    for tr, va in KFold(5, shuffle=True, random_state=seed).split(Xtr):
        m = Est(**kw).fit(Xtr[tr], ytr[tr])
        staged = m.staged_decision_function(Xtr[va]) if binary else m.staged_predict(Xtr[va])
        for t, f in enumerate(staged):
            f = np.ravel(f)
            cv_loss[t] += (np.exp(-(2 * ytr[va] - 1) * f).sum() if binary else ((ytr[va] - f) ** 2).sum())
    best = int(np.argmin(cv_loss))  # 0-based: best + 1 trees
    m = Est(**kw).fit(Xtr, ytr)
    staged = m.staged_predict_proba(Xte) if binary else m.staged_predict(Xte)
    for t, f in enumerate(staged):
        if t == best:
            return f[:, 1] if binary else f
    raise RuntimeError("unreachable")


def nnet_fit_predict(Xtr, ytr, Xte, seed):
    """nnet(size = 8, decay = 0.01, maxit = 1000, linout = FALSE) as called by nnetF(): inputs and
    target min-max scaled with the training fold's min and max, prediction mapped back.
    Returns (predictions on Xte, number of L-BFGS iterations)."""
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.neural_network import MLPRegressor
    lo, hi = Xtr.min(axis=0), Xtr.max(axis=0)
    span = np.where(hi > lo, hi - lo, 1.0)
    ylo, yhi = ytr.min(), ytr.max()
    m = MLPRegressor(hidden_layer_sizes=(8,), activation="logistic", solver="lbfgs", alpha=0.01,
                     max_iter=1000, tol=1e-8, random_state=seed)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ConvergenceWarning)
        m.fit((Xtr - lo) / span, (ytr - ylo) / (yhi - ylo))
    return m.predict((Xte - lo) / span) * (yhi - ylo) + ylo, int(m.n_iter_)


def fit_nuisance(learner, nuisance, Xtr, ytr, Xte, seed, lasso_c_y=0.5, lasso_c_d=1.1):
    """One nuisance fit. nuisance 0 = Y (l), 1 = D (m). Returns (predictions, info dict)."""
    binary = nuisance == 1
    info: dict = {}
    if learner == "lasso":
        if binary:
            pred, info = rlassologit_fit_predict(Xtr, ytr, Xte, c=lasso_c_d, seed=seed)
        else:
            pred, info = rlasso_fit_predict(Xtr, ytr, Xte, c=lasso_c_y)
    elif learner == "tree":
        pred = tree_fit_predict(Xtr, ytr, Xte, seed)
    elif learner == "forest":
        pred = forest_fit_predict(Xtr, ytr, Xte, seed, nodesize=1 if binary else 5)
    elif learner == "boosting":
        pred = boost_fit_predict(Xtr, ytr, Xte, seed, binary)
    elif learner == "nnet":
        pred, info = nnet_fit_predict(Xtr, ytr, Xte, seed)
        info = {"iter": info}
    else:
        raise ValueError(learner)
    return np.asarray(pred, dtype=float).ravel(), info


# ====================================================================== DML2
def dml2_theta(y, d, l_hat, m_hat):
    """Pooled partialling-out estimate and HC0 SE (lm(ry ~ rz - 1), vcovHC(type = 'HC'))."""
    u, v = y - l_hat, d - m_hat
    vv = (v * v).sum()
    theta = (v * u).sum() / vv
    sigma = np.sqrt((v * v * (u - theta * v) ** 2).sum()) / vv
    return float(theta), float(sigma)


def aggregate(theta_s, sigma_s):
    """Definition 3.3 / eq. 3.14 aggregation over splits (median of an even count = mean of middle two)."""
    theta_s, sigma_s = np.asarray(theta_s), np.asarray(sigma_s)
    med = float(np.median(theta_s))
    return med, float(np.median(sigma_s)), float(np.sqrt(np.median(sigma_s ** 2 + (theta_s - med) ** 2)))


def _job(learner, s, k, fold, nuisance, Xmat, target, train, test, lasso_c_y):
    from threadpoolctl import threadpool_limits
    seed = fit_seed(BASE_SEED, k, s, fold, LEARNER_INDEX[learner], nuisance)
    with threadpool_limits(1):
        pred, info = fit_nuisance(learner, nuisance, Xmat[train], target[train], Xmat[test], seed,
                                  lasso_c_y=lasso_c_y)
    return (s, k, fold, nuisance), pred, info


def run(learner: str, n_splits: int, lasso_c_y: float, run_id: str) -> None:
    from joblib import Parallel, delayed
    t_start = time.perf_counter()
    assert_plan_constants()
    if n_splits != SPLITS[learner] and run_id.startswith("main-"):
        sys.exit(f"ERROR: design.splits fixes S = {SPLITS[learner]} for {learner}")
    df = pd.read_csv(DATA, usecols=[OUTCOME, TREATMENT] + COVARIATES)
    if df.isna().any().any():
        sys.exit("ERROR: missing values in the study variables; stop and tell the PI (design.data)")
    if len(df) != N_EXPECTED:
        sys.exit(f"ERROR: expected {N_EXPECTED} rows (design.sample_rule), found {len(df)}")
    y = df[OUTCOME].to_numpy(float)
    d = df[TREATMENT].to_numpy(float)
    X = df[COVARIATES].to_numpy(float)
    Xmat = dictionary(X) if learner == "lasso" else X
    n = len(y)

    jobs = []
    parts = {(s, k): partition(n, k, s) for k in FOLDS for s in range(1, n_splits + 1)}
    for (s, k), blocks in parts.items():
        for fold, test in enumerate(blocks, start=1):
            train = np.setdiff1d(np.arange(n), test, assume_unique=True)
            for nuisance, target in ((0, y), (1, d)):
                jobs.append(delayed(_job)(learner, s, k, fold, nuisance, Xmat, target, train, test, lasso_c_y))
    results = Parallel(n_jobs=-1, backend="loky")(jobs)
    preds = {key: (pred, info) for key, pred, info in results}

    rows, iters = [], {0: [], 1: []}
    for (s, k), blocks in parts.items():
        l_hat, m_hat = np.empty(n), np.empty(n)
        for fold, test in enumerate(blocks, start=1):
            l_hat[test], info_l = preds[(s, k, fold, 0)]
            m_hat[test], info_m = preds[(s, k, fold, 1)]
            if learner == "nnet":
                iters[0].append(info_l["iter"])
                iters[1].append(info_m["iter"])
        theta, sigma = dml2_theta(y, d, l_hat, m_hat)
        rows.append(dict(s=s, K=k, theta=theta, sigma=sigma,
                         rmse_l=float(np.sqrt(np.mean((y - l_hat) ** 2))),
                         rmse_m=float(np.sqrt(np.mean((d - m_hat) ** 2))),
                         m_out_01=float(np.mean((m_hat < 0.01) | (m_hat > 0.99)))))
    splits = pd.DataFrame(rows)

    metrics: dict = {"learner": learner, "n_splits": n_splits, "n_obs": n, "lasso_c_y": lasso_c_y
                     if learner == "lasso" else None}
    if metrics["lasso_c_y"] is None:
        del metrics["lasso_c_y"]
    for k in FOLDS:
        sub = splits[splits.K == k]
        th, sg = sub.theta.to_numpy(), sub.sigma.to_numpy()
        med, se_med, se_adj = aggregate(th, sg)
        ref = TOLERANCE_TABLE[(learner, k)]
        diff = med - ref["published"]
        mad = float(np.median(np.abs(th - med)))
        metrics.update({
            f"theta_k{k}": med, f"se_med_k{k}": se_med, f"se_adj_k{k}": se_adj,
            f"published_k{k}": ref["published"], f"diff_k{k}": diff,
            f"diff_in_pub_se_k{k}": diff / ref["se_med"], f"tolerance_k{k}": ref["tolerance"],
            f"mds80_k{k}": ref["mds80"], f"testable_k{k}": ref["testable"],
            f"within_tol_k{k}": bool(abs(diff) <= ref["tolerance"]),
            f"split_mad_k{k}": mad, f"split_sd_obs_k{k}": MAD_TO_SD * mad,
            f"implied_mad_obs_k{k}": float(np.sqrt(max(se_adj ** 2 - se_med ** 2, 0.0))),
            f"theta_min_k{k}": float(th.min()), f"theta_max_k{k}": float(th.max()),
            f"rmse_l_k{k}": float(np.median(sub.rmse_l)), f"rmse_m_k{k}": float(np.median(sub.rmse_m)),
            f"m_out_01_k{k}": float(np.median(sub.m_out_01)),
        })
    if learner == "nnet":
        metrics["nnet_iter_med_y"] = float(np.median(iters[0]))
        metrics["nnet_iter_med_d"] = float(np.median(iters[1]))

    out = Path("runs") / run_id
    out.mkdir(parents=True, exist_ok=True)
    splits.to_csv(out / "splits.csv", index=False, float_format="%.10g")
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    wall = time.perf_counter() - t_start
    (out / "timing.json").write_text(json.dumps({"wall_seconds": round(wall, 1), "n_fits": len(jobs)},
                                                indent=2) + "\n")
    print(json.dumps(metrics, indent=2))
    print(f"wall time {wall:.1f} s for {len(jobs)} nuisance fits")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--learner", required=True, choices=LEARNERS)
    ap.add_argument("--splits", required=True, type=int)
    ap.add_argument("--lasso-c-y", type=float, default=0.5,
                    help="penalty constant c of the Y lasso (primary 0.5; 1.1 only for sens-lasso-c11)")
    ap.add_argument("--run-id", default=None, help="output directory under runs/ (default main-<learner>)")
    a = ap.parse_args()
    if a.lasso_c_y != 0.5 and a.learner != "lasso":
        sys.exit("ERROR: --lasso-c-y applies to the lasso only")
    run(a.learner, a.splits, a.lasso_c_y, a.run_id or f"main-{a.learner}")


if __name__ == "__main__":
    main()
