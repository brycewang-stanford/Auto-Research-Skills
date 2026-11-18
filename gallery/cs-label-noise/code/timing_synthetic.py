"""Compute-budget timing for the design stage, on SYNTHETIC data only.

No study dataset is read. Each synthetic set has the shape the study data will have after
the stratified 5,000-row cap and one-hot encoding (rows, columns, classes, class shares).
The script runs the planned per-cell procedure (split, exact flips, random search with
N candidates scored on noisy validation labels, GBDT early stopping on the noisy
validation split) on a sample of cells, in parallel as the experiment will, and writes:

- runs/timing-synthetic/timing.json  wall and per-fit times (not reproducible, so not metrics)
- runs/timing-synthetic/metrics.json deterministic counts only, for the ledger

Search spaces here are the ones fixed in plan.json design.method.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from sklearn.datasets import make_classification
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

N_CANDIDATES = 20          # configurations timed per cell; the estimate is scaled to other N
N_JOBS = 8                 # worker processes, as in the experiment
SEEDS = (0, 1)             # timing seeds (synthetic)
RHOS = (0.0, 0.4)          # cheapest and most expensive ends of the noise range
OUT = Path("runs/timing-synthetic")

# rows, numeric columns, one-hot (binary) columns, class shares
SHAPES = {
    "breast_cancer": dict(n=569, num=30, onehot=0, weights=[0.627, 0.373]),
    "credit_g": dict(n=1000, num=7, onehot=54, weights=[0.70, 0.30]),
    "adult": dict(n=5000, num=6, onehot=102, weights=[0.761, 0.239]),
    "covtype": dict(n=5000, num=10, onehot=44,
                    weights=[0.365, 0.488, 0.0615, 0.0047, 0.0163, 0.0299, 0.0353]),
}
METHODS = ("lr", "rf", "gbdt", "gbdt_noes")


def make_shape(name: str, seed: int):
    s = SHAPES[name]
    p = s["num"] + s["onehot"]
    X, y = make_classification(
        n_samples=s["n"], n_features=p, n_informative=min(10, p), n_redundant=min(5, p - 10),
        n_classes=len(s["weights"]), n_clusters_per_class=1, weights=s["weights"],
        flip_y=0.0, class_sep=1.0, random_state=1000 + seed)
    rng = np.random.default_rng(seed)
    if s["onehot"]:  # turn the last columns into 0/1 indicators, as one-hot columns are
        for j in range(s["num"], p):
            X[:, j] = (X[:, j] > np.quantile(X[:, j], rng.uniform(0.5, 0.97))).astype(float)
    return X, y, s["num"]


def flip(y: np.ndarray, rho: float, k: int, rng: np.random.Generator) -> np.ndarray:
    order = rng.permutation(len(y))
    shift = rng.integers(1, k, size=len(y))       # new class uniform over the other k-1
    n_flip = int(np.floor(rho * len(y) + 0.5))
    out = y.copy()
    idx = order[:n_flip]
    out[idx] = (y[idx] + shift[idx]) % k
    return out


def loguni(rng, lo, hi):
    return float(10 ** rng.uniform(np.log10(lo), np.log10(hi)))


def logint(rng, lo, hi):
    return int(np.round(loguni(rng, lo, hi)))


def candidates(method: str, rng: np.random.Generator, n: int):
    out = []
    for _ in range(n):
        if method == "lr":
            out.append(dict(C=loguni(rng, 1e-4, 1e2)))
        elif method == "rf":
            out.append(dict(max_features=float(rng.uniform(0.05, 0.7)),
                            min_samples_leaf=logint(rng, 1, 50),
                            max_samples=float(rng.uniform(0.5, 1.0))))
        else:
            c = dict(learning_rate=loguni(rng, 0.01, 0.3), max_leaf_nodes=logint(rng, 4, 64),
                     min_samples_leaf=logint(rng, 2, 100), l2_regularization=loguni(rng, 1e-4, 10.0))
            if method == "gbdt_noes":
                c["max_iter"] = logint(rng, 10, 500)
            out.append(c)
    return out


def build(method: str, params: dict, rs: int):
    if method == "lr":
        return LogisticRegression(C=params["C"], l1_ratio=0.0, solver="lbfgs", max_iter=2000)
    if method == "rf":
        return RandomForestClassifier(n_estimators=200, bootstrap=True, n_jobs=1, random_state=rs, **params)
    if method == "gbdt":
        return HistGradientBoostingClassifier(loss="log_loss", max_iter=1000, early_stopping=True,
                                              scoring="loss", n_iter_no_change=20, tol=1e-7,
                                              categorical_features=None, random_state=rs, **params)
    return HistGradientBoostingClassifier(loss="log_loss", early_stopping=False,
                                          categorical_features=None, random_state=rs, **params)


def cell(name: str, method: str, rho: float, seed: int, n_cand: int):
    X, y, n_num = make_shape(name, seed)
    k = int(y.max()) + 1
    rng = np.random.default_rng([seed, list(SHAPES).index(name)])
    X_rest, X_te, y_rest, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=seed)
    X_tr, X_va, y_tr, y_va = train_test_split(X_rest, y_rest, test_size=0.25, stratify=y_rest, random_state=seed)
    y_tr_n, y_va_n = flip(y_tr, rho, k, rng), flip(y_va, rho, k, rng)
    if n_num:  # scale numeric columns, fitted on training rows only
        sc = StandardScaler().fit(X_tr[:, :n_num])
        X_tr, X_va, X_te = (np.hstack([sc.transform(a[:, :n_num]), a[:, n_num:]]) for a in (X_tr, X_va, X_te))
    t0 = time.perf_counter()
    best, best_acc, fit_times, iters = None, -1.0, [], []
    for params in candidates(method, rng, n_cand):
        m = build(method, params, rs=seed)
        t = time.perf_counter()
        if method == "gbdt":
            m.fit(X_tr, y_tr_n, X_val=X_va, y_val=y_va_n)
            iters.append(int(m.n_iter_))
        else:
            m.fit(X_tr, y_tr_n)
        fit_times.append(time.perf_counter() - t)
        acc = float(np.mean(m.predict(X_va) == y_va_n))
        if acc > best_acc:
            best, best_acc = m, acc
    best.predict(X_te)
    return dict(dataset=name, method=method, rho=rho, seed=seed, cell_seconds=time.perf_counter() - t0,
                mean_fit_seconds=float(np.mean(fit_times)), max_fit_seconds=float(np.max(fit_times)),
                gbdt_mean_iter=float(np.mean(iters)) if iters else None)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(d, m, r, s) for d in SHAPES for m in METHODS for r in RHOS for s in SEEDS]
    t0 = time.perf_counter()
    rows = Parallel(n_jobs=N_JOBS)(delayed(cell)(d, m, r, s, N_CANDIDATES) for d, m, r, s in jobs)
    wall = time.perf_counter() - t0

    # per-cell cost by (dataset, method), averaged over the timed seeds and both noise rates
    cost = {}
    for d in SHAPES:
        for m in METHODS:
            v = [r["cell_seconds"] for r in rows if r["dataset"] == d and r["method"] == m]
            cost[f"{d}/{m}"] = float(np.mean(v))
    cpu_seconds = sum(r["cell_seconds"] for r in rows)
    efficiency = cpu_seconds / (wall * N_JOBS)   # how well N_JOBS workers were kept busy

    def plan_cpu(n_cand: int) -> float:
        per = {key: c * n_cand / N_CANDIDATES for key, c in cost.items()}
        main = sum(per[f"{d}/{m}"] * 5 * 10 for d in SHAPES for m in ("lr", "rf", "gbdt"))
        a1 = sum(per[f"{d}/gbdt_noes"] * 2 * 10 for d in SHAPES)              # rho 0 and 0.4
        a2 = sum(per[f"{d}/{m}"] * 1 * 10 for d in SHAPES for m in ("lr", "rf", "gbdt"))  # rho 0.4
        return main + a1 + a2

    estimates = {}
    for n_cand in (10, 20, 30, 40):
        c = plan_cpu(n_cand)
        estimates[str(n_cand)] = {"cpu_minutes": c / 60,
                                  "wall_minutes_at_measured_efficiency": c / (N_JOBS * efficiency) / 60}
    report = {
        "note": "Synthetic data only. Times are machine-dependent and are not ledger metrics.",
        "n_jobs": N_JOBS, "timed_candidates_per_cell": N_CANDIDATES,
        "timing_wall_seconds": wall, "timing_cpu_seconds": cpu_seconds,
        "parallel_efficiency": efficiency, "per_cell_seconds_at_timed_N": cost,
        "full_plan_estimates_by_N": estimates, "cells": rows,
        "cpu": os.cpu_count(),
    }
    (OUT / "timing.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    metrics = {"timed_cells": len(rows), "timed_fits": len(rows) * N_CANDIDATES,
               "timed_candidates_per_cell": N_CANDIDATES, "n_jobs": N_JOBS}
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps({k: report[k] for k in ("timing_wall_seconds", "parallel_efficiency",
                                             "per_cell_seconds_at_timed_N", "full_plan_estimates_by_N")}, indent=2))


if __name__ == "__main__":
    main()
