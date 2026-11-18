"""Designer timing study: how long each planned nuisance learner takes, on a SYNTHETIC outcome.

Reads only the nine covariates of the prepared SIPP extract (never net_tfa or e401) and
replaces the outcome and the treatment by synthetic variables built from fixed, arbitrary
formulas plus random noise. No eligibility coefficient is computed, and nothing here is
fitted to the real outcome or treatment. The only purpose is to fix the number of sample
splits S per learner so that the analysis fits the 60-minute budget (plan.json design).

Writes runs/timing-synthetic/timing.json (a run output, deliberately not a metrics file:
timings never reproduce exactly, and crew.py rerun compares metrics at rtol 1e-6): seconds per nuisance fit for every learner,
nuisance (Y-type continuous, D-type binary) and training size (K = 2 and K = 5 folds), and
the measured parallel throughput of this machine.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.stats import norm
from sklearn.ensemble import (GradientBoostingClassifier, GradientBoostingRegressor,
                              RandomForestRegressor)
from sklearn.linear_model import Lasso, LinearRegression, LogisticRegression
from sklearn.model_selection import KFold
from sklearn.neural_network import MLPRegressor
from sklearn.tree import DecisionTreeRegressor

COVARIATES = ["age", "inc", "educ", "fsize", "marr", "twoearn", "db", "pira", "hown"]
OUT = Path("runs/timing-synthetic/timing.json")
NNET_ITERS: dict = {}


# ---------------------------------------------------------------- synthetic data
def synthetic(X: pd.DataFrame, rng: np.random.Generator):
    """Arbitrary outcome/treatment of the right type and rough scale; NOT the real ones."""
    a, i, e = X["age"].to_numpy(float), X["inc"].to_numpy(float) / 1e4, X["educ"].to_numpy(float)
    y = (1500 * (a - 40) + 900 * np.sign(i) * np.abs(i) ** 1.5 + 3000 * X["pira"] + 2000 * X["hown"]
         + 600 * (e - 12) + 8000 * rng.standard_t(3, len(X)))
    eta = -1.5 + 0.25 * i + 0.4 * X["db"] - 0.01 * (a - 40) ** 2 / 10
    d = (rng.random(len(X)) < 1 / (1 + np.exp(-eta))).astype(float)
    return np.asarray(y, float), np.asarray(d, float)


# ---------------------------------------------------------------- lasso dictionary
def dictionary(X: pd.DataFrame) -> np.ndarray:
    """401K.R xl: (poly(age,6,raw) + poly(inc,8,raw) + poly(educ,4,raw) + poly(fsize,2,raw)
    + marr + twoearn + db + pira + hown)^2  -> 25 main columns + 250 cross-term columns."""
    terms = []
    for var, deg in (("age", 6), ("inc", 8), ("educ", 4), ("fsize", 2)):
        v = X[var].to_numpy(float)
        terms.append(np.column_stack([v ** k for k in range(1, deg + 1)]))
    for var in ("marr", "twoearn", "db", "pira", "hown"):
        terms.append(X[[var]].to_numpy(float))
    cols = list(terms)
    for a in range(len(terms)):
        for b in range(a + 1, len(terms)):
            cols.append(np.einsum("ni,nj->nij", terms[a], terms[b]).reshape(len(X), -1))
    return np.column_stack(cols)


# ---------------------------------------------------------------- learners (prototypes)
def rlasso_fit_predict(Xtr, ytr, Xte, c=0.5, num_iter=15, tol=1e-5):
    """hdm::rlasso, heteroskedastic, X-independent penalty, post=FALSE, intercept."""
    n, p = Xtr.shape
    sd = Xtr.std(axis=0)
    keep = sd > 0
    Xs, Xts = Xtr[:, keep] / sd[keep], Xte[:, keep] / sd[keep]
    mx, my = Xs.mean(0), ytr.mean()
    Xc, yc = Xs - mx, ytr - my
    gamma = 0.1 / np.log(n)
    lam0 = 2 * c * np.sqrt(n) * norm.ppf(1 - gamma / (2 * p))
    # starting residuals: OLS on the 5 columns most correlated with y (hdm init_values)
    corr = np.abs(Xc.T @ yc) / (np.sqrt((Xc ** 2).sum(0)) * np.sqrt((yc ** 2).sum()))
    top = np.argsort(-corr)[:5]
    e = yc - LinearRegression().fit(Xc[:, top], yc).predict(Xc[:, top])
    ups = np.sqrt((Xc ** 2 * e[:, None] ** 2).mean(0))
    s0 = yc.std(ddof=1)
    coef = np.zeros(Xc.shape[1])
    model = Lasso(alpha=lam0 / (2 * n), fit_intercept=False, max_iter=100000, tol=1e-6,
                  warm_start=True, selection="cyclic")
    for _ in range(num_iter):
        model.fit(Xc / ups, yc)
        coef = model.coef_ / ups
        e = yc - Xc @ coef
        s1 = e.std(ddof=1)
        ups = np.sqrt((Xc ** 2 * e[:, None] ** 2).mean(0))
        if abs(s0 - s1) < tol:
            break
        s0 = s1
    return my + (Xts - mx) @ coef


def rlassologit_fit_predict(Xtr, dtr, Xte, c=1.1):
    """hdm::rlassologit, post=FALSE: glmnet binomial, lambda = c/2*sqrt(n)*q/(2n), standardized."""
    n, p = Xtr.shape
    sd = Xtr.std(axis=0)
    keep = sd > 0
    mu = Xtr[:, keep].mean(0)
    Xs, Xts = (Xtr[:, keep] - mu) / sd[keep], (Xte[:, keep] - mu) / sd[keep]
    gamma = 0.1 / np.log(n)
    lam0 = c / 2 * np.sqrt(n) * norm.ppf(1 - gamma / (2 * p))
    # liblinear (coordinate descent, like glmnet); the intercept is a column of value 100 whose
    # weight is penalized, i.e. an intercept penalty 100 times weaker than on any slope.
    clf = LogisticRegression(l1_ratio=1.0, C=2.0 / lam0, solver="liblinear", intercept_scaling=100.0,
                             tol=1e-6, max_iter=1000)
    clf.fit(Xs, dtr)
    return clf.predict_proba(Xts)[:, 1]


def tree_fit_predict(Xtr, ytr, Xte, seed, cp=0.01, xval=10):
    """rpart(method='anova', cp=0.01, minsplit=20, minbucket=7, maxdepth=30, xval=10),
    pruned at the cp with minimum 10-fold CV error."""
    kw = dict(min_samples_split=20, min_samples_leaf=7, max_depth=30, random_state=seed)
    var = ytr.var()
    full = DecisionTreeRegressor(**kw).fit(Xtr, ytr)
    alphas = full.cost_complexity_pruning_path(Xtr, ytr).ccp_alphas
    cps = np.unique(alphas[alphas >= cp * var] / var)[::-1]  # rpart cptable, largest first
    cps = np.append(cps, cp) if cps.size == 0 or cps[-1] > cp else cps
    # rpart xval: each cptable row is evaluated at the geometric mean of its cp and the
    # previous (larger) cp; the first row (no split) at 1.0, which always gives the root.
    geo = np.sqrt(cps * np.append(1.0, cps[:-1]))
    err = np.zeros(len(cps))
    for tr, va in KFold(xval, shuffle=True, random_state=seed).split(Xtr):
        v = ytr[tr].var()
        for i, g in enumerate(geo):
            m = DecisionTreeRegressor(ccp_alpha=g * v, **kw).fit(Xtr[tr], ytr[tr])
            err[i] += ((m.predict(Xtr[va]) - ytr[va]) ** 2).sum()
    best = int(np.argmin(err))  # first minimum = smallest tree among ties, as which.min
    return DecisionTreeRegressor(ccp_alpha=geo[best] * var, **kw).fit(Xtr, ytr).predict(Xte)


def forest_fit_predict(Xtr, ytr, Xte, seed, nodesize, n_jobs=1):
    """randomForest(ntree=1000, mtry=floor(9/3)=3, nodesize, replace=TRUE)."""
    m = RandomForestRegressor(n_estimators=1000, max_features=3, min_samples_split=nodesize + 1,
                              min_samples_leaf=1, bootstrap=True, random_state=seed, n_jobs=n_jobs)
    return m.fit(Xtr, ytr).predict(Xte)


def boost_fit_predict(Xtr, ytr, Xte, seed, binary):
    """gbm(n.trees=1000, shrinkage=.01, interaction.depth=2, bag.fraction=.5, n.minobsinnode=10,
    cv.folds=5), best iteration by gbm.perf(method='cv'); binary target: distribution 'adaboost'."""
    kw = dict(n_estimators=1000, learning_rate=0.01, subsample=0.5, max_leaf_nodes=3,
              max_depth=None, min_samples_leaf=10, random_state=seed)
    Est = GradientBoostingClassifier if binary else GradientBoostingRegressor
    if binary:
        kw["loss"] = "exponential"
    cv_loss = np.zeros(1000)
    for tr, va in KFold(5, shuffle=True, random_state=seed).split(Xtr):
        m = Est(**kw).fit(Xtr[tr], ytr[tr])
        for t, f in enumerate(m.staged_decision_function(Xtr[va]) if binary
                              else m.staged_predict(Xtr[va])):
            f = np.ravel(f)
            cv_loss[t] += (np.exp(-(2 * ytr[va] - 1) * f).sum() if binary
                           else ((ytr[va] - f) ** 2).sum())
    best = int(np.argmin(cv_loss))
    m = Est(**kw).fit(Xtr, ytr)
    for t, f in enumerate(m.staged_predict_proba(Xte) if binary else m.staged_predict(Xte)):
        if t == best:
            return f[:, 1] if binary else f


def nnet_fit_predict(Xtr, ytr, Xte, seed, tag="nnet", restart=False):
    """nnet(size=8, decay=0.01, maxit=1000) on min-max scaled inputs and target.

    sklearn's L-BFGS-B stops when the absolute loss decrease falls below about 2.2e-9 (the
    loss here is far below 1), much earlier than nnet's relative 1e-8. With restart=True the
    optimizer is restarted from the current weights until 1000 iterations in total have run
    or a restart makes fewer than 5 iterations (the variant timed as nnet_cont)."""
    lo, hi = Xtr.min(0), Xtr.max(0)
    span = np.where(hi > lo, hi - lo, 1.0)
    ylo, yhi = ytr.min(), ytr.max()
    m = MLPRegressor(hidden_layer_sizes=(8,), activation="logistic", solver="lbfgs", alpha=0.01,
                     max_iter=1000, tol=1e-8, random_state=seed, warm_start=restart)
    Xs, ys = (Xtr - lo) / span, (ytr - ylo) / (yhi - ylo)
    m.fit(Xs, ys)
    total = m.n_iter_
    while restart and total < 1000 and m.n_iter_ >= 5:
        m.max_iter = 1000 - total
        m.fit(Xs, ys)
        total += m.n_iter_
    NNET_ITERS.setdefault(tag, []).append(total)
    return m.predict((Xte - lo) / span) * (yhi - ylo) + ylo


# ---------------------------------------------------------------- timing
def one_fit(learner, Xraw, Xdict, target, binary, n_train, seed):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(target))
    tr, te = idx[:n_train], idx[n_train:]
    t0 = time.perf_counter()
    if learner == "lasso":
        if binary:
            rlassologit_fit_predict(Xdict[tr], target[tr], Xdict[te])
        else:
            rlasso_fit_predict(Xdict[tr], target[tr], Xdict[te])
    elif learner == "tree":
        tree_fit_predict(Xraw[tr], target[tr], Xraw[te], seed)
    elif learner == "forest":
        forest_fit_predict(Xraw[tr], target[tr], Xraw[te], seed, nodesize=1 if binary else 5)
    elif learner == "boosting":
        boost_fit_predict(Xraw[tr], target[tr], Xraw[te], seed, binary)
    elif learner in ("nnet", "nnet_cont"):
        nnet_fit_predict(Xraw[tr], target[tr], Xraw[te], seed,
                         tag=f"{learner}_{'d' if binary else 'y'}", restart=learner == "nnet_cont")
    return time.perf_counter() - t0


def main() -> None:
    X = pd.read_csv("data/derived/sipp1991.csv", usecols=COVARIATES)[COVARIATES]
    n = len(X)
    rng = np.random.default_rng(20261118)
    y_syn, d_syn = synthetic(X, rng)
    Xraw, Xdict = X.to_numpy(float), dictionary(X)
    sizes = {2: n - n // 2, 5: n - n // 5}  # training-fold sizes
    reps = {"lasso": 2, "tree": 2, "forest": 1, "boosting": 1, "nnet": 3, "nnet_cont": 3}
    metrics: dict = {"n": n, "dictionary_columns": int(Xdict.shape[1]), "cpu_count": os.cpu_count()}
    for learner, r in reps.items():
        for k, ntr in sizes.items():
            for name, target, binary in (("y", y_syn, False), ("d", d_syn, True)):
                ts = [one_fit(learner, Xraw, Xdict, target, binary, ntr, 100 + j) for j in range(r)]
                metrics[f"sec_{learner}_{name}_k{k}"] = round(float(np.mean(ts)), 3)
                print(learner, k, name, metrics[f"sec_{learner}_{name}_k{k}"], flush=True)
        per_split = sum(k * (metrics[f"sec_{learner}_y_k{k}"] + metrics[f"sec_{learner}_d_k{k}"])
                        for k in sizes)
        metrics[f"sec_per_split_serial_{learner}"] = round(per_split, 2)
    for tag, its in sorted(NNET_ITERS.items()):
        metrics[f"iters_mean_{tag}"] = round(float(np.mean(its)), 1)
    # parallel throughput: 16 single-threaded forest fits (K = 5 size), one core vs all cores
    jobs = [("forest", 7000 + j) for j in range(16)]
    t0 = time.perf_counter()
    for l, s in jobs[:4]:
        one_fit(l, Xraw, Xdict, y_syn, False, sizes[5], s)
    t_serial = 4 * (time.perf_counter() - t0)
    t0 = time.perf_counter()
    Parallel(n_jobs=-1)(delayed(one_fit)(l, Xraw, Xdict, y_syn, False, sizes[5], s) for l, s in jobs)
    t_par = time.perf_counter() - t0
    metrics["parallel_speedup_n_jobs_all"] = round(t_serial / t_par, 2)
    metrics["parallel_test_serial_sec"] = round(t_serial, 1)
    metrics["parallel_test_wall_sec"] = round(t_par, 1)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
