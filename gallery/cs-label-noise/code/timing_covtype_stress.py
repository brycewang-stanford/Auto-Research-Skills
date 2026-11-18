"""Stress timing for the most expensive cell type, covtype GBDT, on SYNTHETIC data only.

Design-review finding design-r1 F5: the synthetic covtype set used by timing_synthetic.py
may be easier than the real data, so GBDT may stop earlier there than it will on covtype.
This script reruns the covtype-shaped GBDT cells on a harder synthetic set (20 informative
columns, 4 clusters per class, lower class separation), and measures the cost of one
boosting iteration so that a worst case (every fit runs to max_iter=1000) can be bounded.
No study dataset is read.

Writes runs/timing-covtype-stress/timing.json (times; not reproducible, so not metrics) and
runs/timing-covtype-stress/metrics.json (deterministic counts only).
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from sklearn.datasets import make_classification
from sklearn.ensemble import HistGradientBoostingClassifier
from threadpoolctl import threadpool_limits

import timing_synthetic as ts

OUT = Path("runs/timing-covtype-stress")
N_JOBS = ts.N_JOBS
N_CAND = 20
SEEDS = (0, 1, 2, 3)
RHOS = (0.0, 0.4)
COVTYPE_GBDT_CELLS = 50 + 10      # main (5 rates x 10 seeds) + A2 (rho 0.4 x 10 seeds)


def make_hard(name: str, seed: int):
    s = ts.SHAPES["covtype"]
    p = s["num"] + s["onehot"]
    X, y = make_classification(
        n_samples=s["n"], n_features=p, n_informative=20, n_redundant=5, n_classes=7,
        n_clusters_per_class=4, weights=s["weights"], flip_y=0.0, class_sep=0.8,
        random_state=2000 + seed)
    rng = np.random.default_rng(seed)
    for j in range(s["num"], p):
        X[:, j] = (X[:, j] > np.quantile(X[:, j], rng.uniform(0.5, 0.97))).astype(float)
    return X, y, s["num"]


def per_iteration_seconds() -> float:
    X, y, _ = make_hard("covtype", 0)
    X = X[:3000]
    y = y[:3000]
    m = HistGradientBoostingClassifier(max_iter=100, early_stopping=False, max_leaf_nodes=64,
                                       min_samples_leaf=2, learning_rate=0.1, random_state=0)
    t = time.perf_counter()
    m.fit(X, y)
    return (time.perf_counter() - t) / 100


def hard_cell(rho: float, seed: int) -> dict:
    ts.make_shape = make_hard           # patched inside the worker: same cell procedure, harder data
    return ts.cell("covtype", "gbdt", rho, seed, N_CAND)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    rows = Parallel(n_jobs=N_JOBS)(delayed(hard_cell)(r, s) for r in RHOS for s in SEEDS)
    wall = time.perf_counter() - t0
    mean_cell = float(np.mean([r["cell_seconds"] for r in rows]))
    with threadpool_limits(limits=1):   # one thread, as inside a worker
        t_iter = per_iteration_seconds()
    report = {
        "note": "Synthetic data only; times are machine-dependent and are not ledger metrics.",
        "wall_seconds": wall, "cells": rows,
        "mean_cell_seconds_hard": mean_cell,
        "mean_iter_hard": float(np.mean([r["gbdt_mean_iter"] for r in rows])),
        "covtype_gbdt_cpu_minutes_hard": mean_cell * COVTYPE_GBDT_CELLS / 60,
        "seconds_per_boosting_iteration_worst_params": t_iter,
        "covtype_gbdt_cpu_minutes_upper_bound_all_fits_1000_iter":
            t_iter * 1000 * N_CAND * COVTYPE_GBDT_CELLS / 60,
    }
    (OUT / "timing.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT / "metrics.json").write_text(json.dumps({"timed_cells": len(rows), "timed_candidates_per_cell": N_CAND}),
                                      encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k != "cells"}, indent=2))


if __name__ == "__main__":
    main()
