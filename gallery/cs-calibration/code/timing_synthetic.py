"""Compute-budget timing for the design stage, on SYNTHETIC data only.

No study dataset is read. Each synthetic pool has the shape the study data are expected to
have (pool rows, numeric columns, categorical columns with their level counts, positive
share), taken from OpenML metadata for data_id 1590, 1461, 151 and 1489. The script runs
the per-(dataset, seed) procedure fixed in plan.json design.method on a sample of cells:
stratified 20,000-row subsample, 50/25/25 split, one shared preprocessing fitted on train,
library-default LR (max_iter=1000), RF and HGB (early_stopping=False) each fitted once,
Platt and isotonic fitted on the calibration split through FrozenEstimator on the logit
of the clipped probability, test-set scoring including ECE with its null floor, plus the
two planned sensitivity steps (isotonic on a 1,351-row calibration subset; chronological
split on the electricity shape). It reports times only; no score is written anywhere.

Outputs:
- runs/timing-synthetic/timing.json  wall and per-step times (not reproducible, so not metrics)
- runs/timing-synthetic/metrics.json deterministic counts only, for the ledger
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.calibration import CalibratedClassifierCV
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.compose import ColumnTransformer
from sklearn.datasets import make_classification
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits

N_JOBS = 8                # worker processes, as in the experiment
SEEDS = (0, 1)            # timing seeds (synthetic); the study uses 10
N_SEEDS_STUDY = 10
CAP = 20_000
EPS = 1e-6
N_BINS = 15
B_FLOOR = 200             # null-floor resamples per (model, calibrator) on the test split
OUT = Path("runs/timing-synthetic")

# pool rows, numeric columns, categorical level counts, positive share (OpenML metadata)
SHAPES = {
    "adult": dict(n=48_842, num=6, cats=[9, 16, 7, 15, 6, 5, 2, 42], pos=0.239),
    "bank_marketing": dict(n=45_211, num=7, cats=[12, 3, 4, 2, 2, 2, 3, 12, 4], pos=0.117),
    "electricity": dict(n=45_312, num=7, cats=[7], pos=0.425),
    "phoneme": dict(n=5_404, num=5, cats=[], pos=0.293),
}


def make_pool(name: str, seed: int) -> tuple[pd.DataFrame, np.ndarray, list[str], list[str]]:
    s = SHAPES[name]
    p = s["num"] + len(s["cats"])
    X, y = make_classification(
        n_samples=s["n"], n_features=p, n_informative=max(2, min(8, p - 1)),
        n_redundant=min(2, max(0, p - 9)), weights=[1 - s["pos"]], flip_y=0.02,
        class_sep=1.0, random_state=1000 + seed)
    num_cols = [f"x{j}" for j in range(s["num"])]
    cat_cols = [f"c{j}" for j in range(len(s["cats"]))]
    df = pd.DataFrame(X[:, :s["num"]], columns=num_cols)
    for j, k in enumerate(s["cats"]):  # cut a latent column into k levels of unequal size
        z = X[:, s["num"] + j]
        edges = np.quantile(z, np.sort(np.random.default_rng(j).uniform(0, 1, k - 1)))
        df[cat_cols[j]] = pd.Categorical(np.searchsorted(edges, z).astype(str))
    return df, y.astype(int), num_cols, cat_cols


class LogitScore(ClassifierMixin, BaseEstimator):
    """A fitted classifier whose decision_function is logit(clip(P(y=1), EPS, 1-EPS))."""

    def __init__(self, model=None):
        self.model = model

    def fit(self, X, y):  # never called through FrozenEstimator
        raise RuntimeError("LogitScore wraps an already fitted model")

    def __sklearn_is_fitted__(self):
        return True

    @property
    def classes_(self):
        return self.model.classes_

    def predict_proba(self, X):
        return self.model.predict_proba(X)

    def predict(self, X):
        return self.model.predict(X)

    def decision_function(self, X):
        p = np.clip(self.model.predict_proba(X)[:, 1], EPS, 1 - EPS)
        return np.log(p) - np.log1p(-p)


def ece_equal_mass(p: np.ndarray, y: np.ndarray, n_bins: int = N_BINS) -> float:
    """15 equal-mass bins on P(y=1); ties never split: bin = floor(B * #{p_j < p_i} / n)."""
    q = np.round(p, 12)
    n = len(q)
    smaller = np.searchsorted(np.sort(q), q, side="left")
    b = (n_bins * smaller) // n
    cnt = np.bincount(b, minlength=n_bins)
    sp = np.bincount(b, weights=p, minlength=n_bins)
    sy = np.bincount(b, weights=y, minlength=n_bins)
    keep = cnt > 0
    return float(np.sum(np.abs(sy[keep] - sp[keep])) / n)


def ece_floor(p: np.ndarray, rng: np.random.Generator) -> float:
    """Mean ECE when labels are drawn from the predictions themselves (perfect calibration)."""
    return float(np.mean([ece_equal_mass(p, (rng.random(len(p)) < p).astype(float)) for _ in range(B_FLOOR)]))


def score(p: np.ndarray, y: np.ndarray, rng: np.random.Generator) -> None:
    # computed only to time the work; nothing is returned or written
    pc = np.clip(p, EPS, 1 - EPS)
    _ = (np.mean((p - y) ** 2), -np.mean(y * np.log(pc) + (1 - y) * np.log1p(-pc)),
         ece_equal_mass(p, y), ece_floor(p, rng), int(np.sum((p < EPS) | (p > 1 - EPS))))


def cell(name: str, seed: int) -> dict:
    with threadpool_limits(limits=1):
        t_cell = time.perf_counter()
        df, y, num_cols, cat_cols = make_pool(name, seed)
        sub, split, model_ss = np.random.SeedSequence([20261119, list(SHAPES).index(name), seed]).spawn(3)
        as_int = lambda ss: int(ss.generate_state(1)[0])
        rng = np.random.default_rng(model_ss.spawn(1)[0])
        if len(y) > CAP:
            df, _, y, _ = train_test_split(df, y, train_size=CAP, stratify=y, random_state=as_int(sub))
        n = len(y)
        n_test = n_cal = int(round(0.25 * n))
        rest_X, X_te, rest_y, y_te = train_test_split(df, y, test_size=n_test, stratify=y, random_state=as_int(split))
        X_tr, X_ca, y_tr, y_ca = train_test_split(rest_X, rest_y, test_size=n_cal, stratify=rest_y,
                                                  random_state=as_int(split.spawn(1)[0]))
        assert len(y_ca) >= 1000 and len(y_tr) <= 10_000
        steps = [("num", StandardScaler(), num_cols)]
        if cat_cols:
            steps.append(("cat", make_pipeline(SimpleImputer(strategy="constant", fill_value="missing"),
                                               OneHotEncoder(handle_unknown="ignore", sparse_output=False)), cat_cols))
        pre = ColumnTransformer(steps).fit(X_tr)
        A_tr, A_ca, A_te = (pre.transform(a) for a in (X_tr, X_ca, X_te))
        rs = as_int(model_ss)
        models = {
            "lr": LogisticRegression(max_iter=1000),
            "rf": RandomForestClassifier(random_state=rs, n_jobs=1),
            "hgb": HistGradientBoostingClassifier(early_stopping=False, random_state=rs),
        }
        times = {}
        for m, est in models.items():
            t = time.perf_counter()
            est.fit(A_tr, y_tr)
            times[f"fit_{m}"] = time.perf_counter() - t
            t = time.perf_counter()
            base = LogitScore(est)
            score(est.predict_proba(A_te)[:, 1], y_te, rng)
            for method in ("sigmoid", "isotonic"):
                cal = CalibratedClassifierCV(FrozenEstimator(base), method=method, ensemble=False).fit(A_ca, y_ca)
                score(cal.predict_proba(A_te)[:, 1], y_te, rng)
            # sensitivity: isotonic on a stratified 1,351-row subset of the calibration split
            if len(y_ca) > 1351:
                A_s, _, y_s, _ = train_test_split(A_ca, y_ca, train_size=1351, stratify=y_ca, random_state=rs)
                cal = CalibratedClassifierCV(FrozenEstimator(base), method="isotonic", ensemble=False).fit(A_s, y_s)
                score(cal.predict_proba(A_te)[:, 1], y_te, rng)
            times[f"cal_score_{m}"] = time.perf_counter() - t
        if name == "electricity":  # sensitivity: chronological 50/25/25 split, all three models again
            t = time.perf_counter()
            order = np.argsort(df[num_cols[0]].to_numpy(), kind="stable")
            i_tr, i_ca, i_te = order[: n - 2 * n_test], order[n - 2 * n_test: n - n_test], order[n - n_test:]
            pre_t = ColumnTransformer(steps).fit(df.iloc[i_tr])
            B_tr, B_ca, B_te = (pre_t.transform(df.iloc[i]) for i in (i_tr, i_ca, i_te))
            for est in (LogisticRegression(max_iter=1000), RandomForestClassifier(random_state=rs, n_jobs=1),
                        HistGradientBoostingClassifier(early_stopping=False, random_state=rs)):
                est.fit(B_tr, y[i_tr])
                base = LogitScore(est)
                score(est.predict_proba(B_te)[:, 1], y[i_te], rng)
                for method in ("sigmoid", "isotonic"):
                    cal = CalibratedClassifierCV(FrozenEstimator(base), method=method, ensemble=False).fit(B_ca, y[i_ca])
                    score(cal.predict_proba(B_te)[:, 1], y[i_te], rng)
            times["elec_chrono"] = time.perf_counter() - t
        return dict(dataset=name, seed=seed, n_train=len(y_tr), n_cal=len(y_ca), n_test=len(y_te),
                    n_columns=int(A_tr.shape[1]), lr_n_iter=int(models["lr"].n_iter_[0]),
                    cell_seconds=time.perf_counter() - t_cell, **times)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = [(d, s) for d in SHAPES for s in SEEDS]
    t0 = time.perf_counter()
    rows = Parallel(n_jobs=N_JOBS)(delayed(cell)(d, s) for d, s in jobs)
    wall = time.perf_counter() - t0
    per_ds = {d: float(np.mean([r["cell_seconds"] for r in rows if r["dataset"] == d])) for d in SHAPES}
    cpu_total = N_SEEDS_STUDY * sum(per_ds.values())          # 40 cells in the study
    longest = max(per_ds.values())
    # 40 cells on 8 workers: at least ceil(40/8)=5 waves, and never less than the longest cell
    wall_est = max(cpu_total / N_JOBS, longest)
    timing = dict(
        machine=dict(cpu_count=os.cpu_count(), n_jobs=N_JOBS),
        timed_cells=len(rows), timing_wall_seconds=wall, per_cell=rows,
        mean_cell_seconds_by_dataset=per_ds,
        estimate=dict(study_cells=N_SEEDS_STUDY * len(SHAPES), cpu_seconds=cpu_total,
                      wall_seconds_8_workers=wall_est, wall_minutes_8_workers=wall_est / 60,
                      cpu_minutes=cpu_total / 60,
                      note="includes ECE null floor (B=200), the n_cal=1,351 isotonic sensitivity and the "
                           "electricity chronological split; analysis scripts on 360 rows add seconds"),
    )
    (OUT / "timing.json").write_text(json.dumps(timing, indent=2) + "\n")
    metrics = dict(
        timed_cells=len(rows), n_jobs=N_JOBS, timing_seeds=len(SEEDS),
        **{f"n_train_{r['dataset']}": r["n_train"] for r in rows if r["seed"] == 0},
        **{f"n_cal_{r['dataset']}": r["n_cal"] for r in rows if r["seed"] == 0},
        **{f"n_test_{r['dataset']}": r["n_test"] for r in rows if r["seed"] == 0},
        **{f"n_columns_{r['dataset']}": r["n_columns"] for r in rows if r["seed"] == 0},
    )
    (OUT / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(timing["estimate"], indent=2))
    print(json.dumps(per_ds, indent=2))


if __name__ == "__main__":
    main()
