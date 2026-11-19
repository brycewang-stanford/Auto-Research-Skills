"""Main experiment (run `main`): plan.json design.method steps 1-8.

For each of 4 datasets x 10 seeds: stratified 20,000-row subsample (redrawn per seed), 50/25/25
stratified split, one ColumnTransformer fitted on the training split, three scikit-learn default
models (LR max_iter=1000, RF, HGB early_stopping=False) fitted once and frozen, Platt ('sigmoid')
and isotonic fitted on the calibration split through FrozenEstimator on the logit of the clipped
probability, and every (dataset, model, calibrator, seed) scored once on the test split.

This module is also the shared library of the sensitivity scripts (sens_ncal.py,
sens_elec_time.py) and of the unit tests (test_metrics.py). Importing it reads no data.

Outputs of `python code/experiment.py` (run from the workspace root, as crew.py run does):
- results/cells.csv                    360 rows, all metrics of step 8 (deterministic)
- results/main_timing.json             fit and cell seconds (not reproducible, not a metric)
- results/preds/main/<dataset>_s<seed>.npz   test y and p_<model>_<calibrator> (git-ignored)
- runs/main/metrics.json               flat counts and checks for the ledger
"""
from __future__ import annotations

import hashlib
import json
import os
import time
import warnings
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.calibration import CalibratedClassifierCV
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.frozen import FrozenEstimator
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ---------------------------------------------------------------- constants fixed by design.method
SEED_ROOT = 20261119
SEEDS = tuple(range(10))
DATASETS = ("adult", "bank-marketing", "electricity", "phoneme")   # dataset index d = position
MODELS = ("lr", "rf", "hgb")
CALIBRATORS = ("none", "platt", "isotonic")
CAP = 20_000                 # subsample cap (step 3)
EPS = 1e-6                   # clipping epsilon for the logit and for log-loss (steps 7-8)
EPS_MACH = float(np.finfo(np.float64).eps)  # what sklearn.metrics.log_loss clips at in 1.9.1
N_BINS = 15                  # equal-mass bins for ece and ece_db (step 8)
TIE_DECIMALS = 12            # q = round(p, 12) for the tie rule (step 8)
M_DEBIAS = 1000              # normal draws for ece_db (step 8, PI ruling)
N_DEBIAS_CHILDREN = 12       # debias.spawn(12): j = 0..8 main, 9..11 sens-ncal (step 2)
HGB_MAX_ITER = 100
N_TRAIN_MAX = 10_000
N_CAL_MIN = 1_000
VIC_FILL_ROWS = 17_424       # electricity: Victoria columns are fill values in file rows 0..17,423
VIC_COLS = ("vicprice", "vicdemand", "transfer")
N_JOBS = min(8, os.cpu_count() or 1)

RESULTS = Path("results")
MANIFEST = Path("data/manifest.json")


def ds_key(name: str) -> str:
    """Dataset name as used in flat metric keys (no hyphen)."""
    return name.replace("-", "_")


# ---------------------------------------------------------------- step 1: data from the manifest
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_manifest(path: Path = MANIFEST) -> dict[str, dict]:
    entries = {e["id"]: e for e in json.loads(Path(path).read_text())["datasets"]}
    assert tuple(sorted(entries)) == tuple(sorted(DATASETS)), f"manifest datasets {sorted(entries)}"
    return entries


def read_dataset_csv(path: Path, entry: dict) -> tuple[pd.DataFrame, np.ndarray]:
    """Read one data/raw CSV with the column types from the manifest, never from CSV dtypes.

    Categorical columns are strings (object dtype) with empty cells as missing (np.nan);
    numeric columns are float64. Only empty cells count as missing ('NA', 'None' etc. stay text).
    Returns the features in the CSV (OpenML) column order, indexed by file row, and y as int.
    """
    num, cat = list(entry["numeric_features"]), list(entry["categorical_features"])
    header = pd.read_csv(path, nrows=0).columns.tolist()
    assert header[-1] == "target", f"{path}: last column is {header[-1]!r}, not 'target'"
    feats = header[:-1]
    assert len(feats) == len(set(feats)) == len(num) + len(cat) and set(feats) == set(num) | set(cat), \
        f"{path}: CSV header does not equal the manifest's numeric_features + categorical_features"
    dtypes = {c: "float64" for c in num} | {c: str for c in cat} | {"target": "int64"}
    df = pd.read_csv(path, dtype=dtypes, keep_default_na=False, na_values=[""])
    for c in cat:
        col = df[c].astype(object)
        df[c] = col.where(df[c].notna(), np.nan)
    y = df.pop("target").to_numpy()
    assert set(np.unique(y)) <= {0, 1}
    df.index = pd.RangeIndex(len(df))       # index = original file row
    return df[feats], y.astype(np.int64)


@lru_cache(maxsize=None)
def load_study_dataset(name: str) -> tuple[pd.DataFrame, np.ndarray, tuple[str, ...], tuple[str, ...]]:
    """Load a study dataset, checking the manifest sha256, row count and positive count."""
    entry = load_manifest()[name]
    path = Path(entry["path"])
    digest = sha256_file(path)
    assert digest == entry["sha256"], f"{path}: sha256 {digest} != manifest {entry['sha256']}"
    X, y = read_dataset_csv(path, entry)
    assert len(y) == entry["rows"], f"{name}: {len(y)} rows, manifest says {entry['rows']}"
    assert int(y.sum()) == entry["n_positive"], f"{name}: {int(y.sum())} positives, manifest {entry['n_positive']}"
    if name == "electricity":  # the fill-value regime the threats section describes
        for c in VIC_COLS:
            assert X[c].iloc[:VIC_FILL_ROWS].nunique() == 1, f"electricity {c} not constant on the fill rows"
    return X, y, tuple(entry["numeric_features"]), tuple(entry["categorical_features"])


# ---------------------------------------------------------------- step 2: seeds and random streams
def seed_streams(d: int, s: int, variant: int | None = None) -> dict:
    """SeedSequence([20261119, d, s]) (or [..., variant] for sens-elec-time) -> the four streams."""
    entropy = [SEED_ROOT, d, s] + ([variant] if variant is not None else [])
    sub, split, model, debias = np.random.SeedSequence(entropy).spawn(4)
    i_test, i_cal = (int(v) for v in split.generate_state(2))
    return dict(
        sub_int=int(sub.generate_state(1)[0]),
        i_test=i_test,
        i_cal=i_cal,
        rs=int(model.generate_state(1)[0]),
        debias=debias.spawn(N_DEBIAS_CHILDREN),
    )


def debias_index(model: str, calibrator: str) -> int:
    """Child j of debias.spawn(12) for (model, calibrator) in main: (lr, rf, hgb) x (none, platt, isotonic)."""
    return MODELS.index(model) * len(CALIBRATORS) + CALIBRATORS.index(calibrator)


def debias_index_ncal(model: str) -> int:
    """Child j = 9, 10, 11 for (lr, rf, hgb) isotonic on the 1,351-row subset in sens-ncal."""
    return 9 + MODELS.index(model)


# ---------------------------------------------------------------- steps 3-4: subsample and split
def subsample(X: pd.DataFrame, y: np.ndarray, sub_int: int) -> tuple[pd.DataFrame, np.ndarray]:
    if len(y) > CAP:
        X, _, y, _ = train_test_split(X, y, train_size=CAP, stratify=y, random_state=sub_int)
    return X, y


def split_sizes(n: int) -> tuple[int, int, int]:
    n_test = n_cal = int(round(0.25 * n))
    return n - n_test - n_cal, n_cal, n_test


def split_random(X: pd.DataFrame, y: np.ndarray, i_test: int, i_cal: int):
    """Stratified 50/25/25: test first, then calibration from the rest, train = the remainder."""
    _, n_cal, n_test = split_sizes(len(y))
    X_rest, X_te, y_rest, y_te = train_test_split(X, y, test_size=n_test, stratify=y, random_state=i_test)
    X_tr, X_ca, y_tr, y_ca = train_test_split(X_rest, y_rest, test_size=n_cal, stratify=y_rest,
                                              random_state=i_cal)
    return (X_tr, y_tr), (X_ca, y_ca), (X_te, y_te)


def split_chronological(X: pd.DataFrame, y: np.ndarray):
    """sens-elec-time: sort by original file row (time order), earliest half / next quarter / last quarter."""
    order = np.argsort(X.index.to_numpy(), kind="stable")
    X, y = X.iloc[order], y[order]
    n_train, n_cal, _ = split_sizes(len(y))
    a, b = n_train, n_train + n_cal
    return (X.iloc[:a], y[:a]), (X.iloc[a:b], y[a:b]), (X.iloc[b:], y[b:])


def check_split_sizes(n_train: int, n_cal: int) -> None:
    assert n_cal >= N_CAL_MIN, f"n_cal = {n_cal} < {N_CAL_MIN}"
    assert n_train <= N_TRAIN_MAX, f"n_train = {n_train} > {N_TRAIN_MAX}"


# ---------------------------------------------------------------- step 5: preprocessing
def make_preprocessor(num: list[str] | tuple, cat: list[str] | tuple) -> ColumnTransformer:
    steps = []
    if num:
        steps.append(("num", Pipeline([("impute", SimpleImputer(strategy="median")),
                                       ("scale", StandardScaler())]), list(num)))
    if cat:
        steps.append(("cat", Pipeline([("impute", SimpleImputer(strategy="constant", fill_value="missing")),
                                       ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))]),
                      list(cat)))
    return ColumnTransformer(steps, remainder="drop")


def preprocess(num, cat, X_tr, X_ca, X_te):
    """Fit on the training split's features only; apply unchanged to calibration and test."""
    assert set(X_tr.columns) == set(num) | set(cat), "every feature must be numeric or categorical"
    pre = make_preprocessor(num, cat).fit(X_tr)
    out = []
    for X in (X_tr, X_ca, X_te):
        A = pre.transform(X)
        assert isinstance(A, np.ndarray) and A.dtype == np.float64, "preprocessed output must be dense float64"
        out.append(A)
    return pre, out


# ---------------------------------------------------------------- step 6: base models
def fit_models(A_tr: np.ndarray, y_tr: np.ndarray, rs: int) -> tuple[dict, dict, dict]:
    """Fit LR, RF and HGB once on the training split. Returns (models, bookkeeping, fit seconds)."""
    models = {
        "lr": LogisticRegression(max_iter=1000),
        "rf": RandomForestClassifier(random_state=rs, n_jobs=1),
        "hgb": HistGradientBoostingClassifier(early_stopping=False, random_state=rs),
    }
    secs, book = {}, {}
    for name, est in models.items():
        t = time.perf_counter()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            est.fit(A_tr, y_tr)
        secs[name] = time.perf_counter() - t
        if name == "lr":
            n_iter = int(np.max(est.n_iter_))
            warned = any(issubclass(w.category, ConvergenceWarning) for w in caught)
            book["lr_n_iter"] = n_iter
            book["lr_converged"] = int((not warned) and n_iter < est.max_iter)
    hgb = models["hgb"]
    assert hgb.is_categorical_ is None, "HGB must treat every column as numeric"
    assert hgb.n_iter_ == HGB_MAX_ITER, f"HGB n_iter_ = {hgb.n_iter_}, expected {HGB_MAX_ITER}"
    book["hgb_n_iter"] = int(hgb.n_iter_)
    return models, book, secs


# ---------------------------------------------------------------- step 7: calibrators on a frozen model
def logit_clipped(p: np.ndarray) -> np.ndarray:
    pc = np.clip(p, EPS, 1 - EPS)
    return np.log(pc) - np.log1p(-pc)


class LogitScore(ClassifierMixin, BaseEstimator):
    """A fitted classifier whose decision_function is logit(clip(P(y=1), 1e-6, 1-1e-6)).

    predict and predict_proba are delegated to the wrapped (already fitted) model.
    """

    def __init__(self, model=None):
        self.model = model

    def fit(self, X, y):  # never called: FrozenEstimator makes fit a no-op
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
        return logit_clipped(self.model.predict_proba(X)[:, 1])


def fit_calibrator(base, A_ca: np.ndarray, y_ca: np.ndarray, method: str) -> CalibratedClassifierCV:
    """CalibratedClassifierCV(FrozenEstimator(LogitScore(base)), method, ensemble=False) on the calibration rows."""
    return CalibratedClassifierCV(FrozenEstimator(LogitScore(base)), method=method,
                                  ensemble=False).fit(A_ca, y_ca)


def calibrated_predictions(base, A_ca: np.ndarray, y_ca: np.ndarray, A_te: np.ndarray) -> dict[str, np.ndarray]:
    """P(y=1) on the test split for none, platt and isotonic; asserts the base model is untouched."""
    p_none = base.predict_proba(A_te)[:, 1].copy()
    out = {"none": p_none}
    for cal_name, method in (("platt", "sigmoid"), ("isotonic", "isotonic")):
        out[cal_name] = fit_calibrator(base, A_ca, y_ca, method).predict_proba(A_te)[:, 1]
    assert np.array_equal(base.predict_proba(A_te)[:, 1], p_none), "base model changed during calibration"
    return out


# ---------------------------------------------------------------- step 8: metrics
def brier(p: np.ndarray, y: np.ndarray) -> float:
    value = float(np.mean((p - y) ** 2))
    ref = float(brier_score_loss(y, p))
    assert np.isclose(value, ref, rtol=1e-12, atol=1e-15), f"brier {value} != sklearn {ref}"
    return value


def logloss(p: np.ndarray, y: np.ndarray, eps: float = EPS) -> float:
    pc = np.clip(p, eps, 1 - eps)
    return float(-np.mean(np.where(y == 1, np.log(pc), np.log1p(-pc))))


def clip_counts(p: np.ndarray, eps: float = EPS) -> tuple[int, int]:
    return int(np.sum(p < eps)), int(np.sum(p > 1 - eps))


def equal_mass_bins(p: np.ndarray, n_bins: int = N_BINS) -> np.ndarray:
    """Bin index per prediction: floor(B * #{j: q_j < q_i} / n), q = round(p, 12).

    Tied predictions get the same count, so a tie group is never split across bins and sits in
    the bin where its first member would fall. Depends only on the multiset of p.
    """
    q = np.round(np.asarray(p, dtype=np.float64), TIE_DECIMALS)
    n = len(q)
    n_smaller = np.searchsorted(np.sort(q), q, side="left")
    return (n_bins * n_smaller) // n


def bin_stats(p: np.ndarray, y: np.ndarray, n_bins: int = N_BINS):
    """Per non-empty bin, in increasing bin order: weight n_k/n, mean prediction s_k, mean label y_k, n_k."""
    b = equal_mass_bins(p, n_bins)
    cnt = np.bincount(b, minlength=n_bins)
    sp = np.bincount(b, weights=p, minlength=n_bins)
    sy = np.bincount(b, weights=y.astype(np.float64), minlength=n_bins)
    keep = cnt > 0                       # bins left empty are dropped
    nk = cnt[keep].astype(np.float64)
    return nk / len(p), sp[keep] / nk, sy[keep] / nk, nk


def ece(p: np.ndarray, y: np.ndarray, n_bins: int = N_BINS) -> tuple[float, int]:
    """Plug-in 15-bin equal-mass ECE on P(y=1) and the number of non-empty bins."""
    w, s, yb, _ = bin_stats(p, y, n_bins)
    return float(np.sum(w * np.abs(s - yb))), int(len(w))


def ece_debiased(p: np.ndarray, y: np.ndarray, rng: np.random.Generator,
                 n_bins: int = N_BINS, m: int = M_DEBIAS) -> float:
    """Kumar, Liang and Ma (2019), Appendix G, Def. G.3, on the same bins and tie rule as ece.

    R_k^(m) ~ Normal(y_k, y_k(1-y_k)/n_k), drawn as one rng.normal call of shape (M, K) over the K
    non-empty bins in increasing bin order; ece_db = 2*ece - mean_m sum_k p_k |s_k - R_k^(m)|.
    Not floored at 0. A bin with y_k in {0, 1} has zero variance and contributes no correction.
    """
    w, s, yb, nk = bin_stats(p, y, n_bins)
    plug_in = float(np.sum(w * np.abs(s - yb)))
    R = rng.normal(loc=yb, scale=np.sqrt(yb * (1.0 - yb) / nk), size=(m, len(w)))
    resampled = float(np.mean(np.abs(s - R) @ w))
    return 2.0 * plug_in - resampled


def score(p: np.ndarray, y: np.ndarray, rng: np.random.Generator) -> dict:
    """All step-8 metrics for one (dataset, model, calibrator, seed) on its test split."""
    p = np.asarray(p, dtype=np.float64)
    e, nb = ece(p, y)
    lo, hi = clip_counts(p)
    return dict(
        brier=brier(p, y),
        logloss=logloss(p, y, EPS),
        logloss_mach=logloss(p, y, EPS_MACH),
        n_clip_low=lo,
        n_clip_high=hi,
        ece=e,
        ece_bins=nb,
        ece_db=ece_debiased(p, y, rng),
        auc=float(roc_auc_score(y, p)),
    )


# ---------------------------------------------------------------- one (dataset, seed) cell
def vic_fill_counts(*index_sets) -> list[int]:
    return [int(np.sum(np.asarray(ix) < VIC_FILL_ROWS)) for ix in index_sets]


def prepare_cell(d: int, s: int, X: pd.DataFrame, y: np.ndarray, num, cat) -> dict:
    """Steps 2-6 for one (dataset, seed): streams, subsample, split, preprocessing, fitted models."""
    st = seed_streams(d, s)
    Xs, ys = subsample(X, y, st["sub_int"])
    (X_tr, y_tr), (X_ca, y_ca), (X_te, y_te) = split_random(Xs, ys, st["i_test"], st["i_cal"])
    check_split_sizes(len(y_tr), len(y_ca))
    pre, (A_tr, A_ca, A_te) = preprocess(num, cat, X_tr, X_ca, X_te)
    models, book, secs = fit_models(A_tr, y_tr, st["rs"])
    book.update(n_train=len(y_tr), n_cal=len(y_ca), n_test=len(y_te),
                pos_train=int(y_tr.sum()), pos_cal=int(y_ca.sum()), pos_test=int(y_te.sum()),
                width=int(A_tr.shape[1]))
    if DATASETS[d] == "electricity":
        book.update(zip(("n_vicfill_train", "n_vicfill_cal", "n_vicfill_test"),
                        vic_fill_counts(X_tr.index, X_ca.index, X_te.index)))
    return dict(streams=st, A_ca=A_ca, y_ca=y_ca, A_te=A_te, y_te=y_te, models=models, book=book, secs=secs,
                idx_test=X_te.index.to_numpy())


def score_all(models: dict, A_ca, y_ca, A_te, y_te, debias_children) -> tuple[list[dict], dict]:
    """none/platt/isotonic for each model, scored with the (model, calibrator) debias child."""
    rows, preds = [], {}
    for m in MODELS:
        ps = calibrated_predictions(models[m], A_ca, y_ca, A_te)
        for c in CALIBRATORS:
            rng = np.random.default_rng(debias_children[debias_index(m, c)])
            rows.append(dict(model=m, calibrator=c, **score(ps[c], y_te, rng)))
            preds[f"p_{m}_{c}"] = ps[c].astype(np.float64)
    return rows, preds


def run_cell(d: int, s: int, X: pd.DataFrame, y: np.ndarray, num, cat) -> dict:
    t0 = time.perf_counter()
    cell = prepare_cell(d, s, X, y, num, cat)
    rows, preds = score_all(cell["models"], cell["A_ca"], cell["y_ca"], cell["A_te"], cell["y_te"],
                            cell["streams"]["debias"])
    full = [dict(dataset=DATASETS[d], seed=s, **r, **cell["book"]) for r in rows]
    return dict(rows=full, preds=preds, y_test=cell["y_te"].astype(np.float64),
                secs=dict(dataset=DATASETS[d], seed=s, **{f"fit_{k}": v for k, v in cell["secs"].items()},
                          cell_seconds=time.perf_counter() - t0))


def main_cell(d: int, s: int) -> dict:
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        X, y, num, cat = load_study_dataset(DATASETS[d])
        return run_cell(d, s, X, y, num, cat)


# ---------------------------------------------------------------- outputs
CELL_COLUMNS = ["dataset", "seed", "model", "calibrator", "brier", "logloss", "logloss_mach", "n_clip_low",
                "n_clip_high", "ece", "ece_bins", "ece_db", "auc", "n_train", "n_cal", "n_test", "pos_train",
                "pos_cal", "pos_test", "width", "lr_n_iter", "lr_converged", "hgb_n_iter",
                "n_vicfill_train", "n_vicfill_cal", "n_vicfill_test"]


def write_cells(rows: list[dict], path: Path, columns: list[str] = CELL_COLUMNS) -> pd.DataFrame:
    df = pd.DataFrame(rows).reindex(columns=[c for c in columns if any(c in r for r in rows)])
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, float_format="%.17g")   # round-trips float64 exactly
    return df


def save_preds(path: Path, y_test: np.ndarray, preds: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(path, y=y_test.astype(np.float64), **preds)


def summarize_main(df: pd.DataFrame) -> dict:
    """Flat counts and checks for runs/main/metrics.json.

    Split sizes are fixed by construction and asserted constant across seeds. The one-hot width is
    not: the encoder is fitted on each seed's training split, so a rare level (adult native-country
    has a level with about one row) that misses a seed's training split drops a column. The width is
    recorded as its min and max over seeds (design step 5: 'the realised width is recorded').
    """
    n_cells = df.groupby(["dataset", "seed"]).ngroups
    per_cell = df.groupby(["dataset", "seed"]).first()
    metrics = dict(n_rows=len(df), n_dataset_seed_cells=n_cells, n_pred_files=n_cells,
                   n_seeds=int(df["seed"].nunique()),
                   lr_nonconverged_cells=int((per_cell["lr_converged"] == 0).sum()),
                   lr_n_iter_max=int(df["lr_n_iter"].max()),
                   hgb_n_iter_min=int(df["hgb_n_iter"].min()), hgb_n_iter_max=int(df["hgb_n_iter"].max()),
                   n_clip_low_total=int(df["n_clip_low"].sum()), n_clip_high_total=int(df["n_clip_high"].sum()))
    for name in DATASETS:
        sub = df[df["dataset"] == name]
        k = ds_key(name)
        for col in ("n_train", "n_cal", "n_test"):
            vals = sub[col].unique()
            assert len(vals) == 1, f"{name}: {col} varies across seeds"
            metrics[f"{col}_{k}"] = int(vals[0])
        metrics[f"width_min_{k}"] = int(sub["width"].min())
        metrics[f"width_max_{k}"] = int(sub["width"].max())
        metrics[f"n_cal_min_{k}"] = int(sub["n_cal"].min())
        metrics[f"mean_brier_{k}"] = float(sub["brier"].mean())   # grand means: a rerun check, not a result
        metrics[f"mean_ece_{k}"] = float(sub["ece"].mean())
    return metrics


def main() -> None:
    from joblib import Parallel, delayed

    import experiment as module   # workers import main_cell by reference, not as a pickled __main__ object
    load_manifest()  # fail early on a manifest problem
    jobs = [(d, s) for d in range(len(DATASETS)) for s in SEEDS]
    t0 = time.perf_counter()
    out = Parallel(n_jobs=N_JOBS)(delayed(module.main_cell)(d, s) for d, s in jobs)
    wall = time.perf_counter() - t0
    rows = [r for o in out for r in o["rows"]]
    df = write_cells(rows, RESULTS / "cells.csv")
    for (d, s), o in zip(jobs, out):
        save_preds(RESULTS / "preds" / "main" / f"{DATASETS[d]}_s{s}.npz", o["y_test"], o["preds"])
    cpu = sum(o["secs"]["cell_seconds"] for o in out)
    (RESULTS / "main_timing.json").write_text(json.dumps(
        dict(n_jobs=N_JOBS, wall_seconds=wall, cell_cpu_seconds=cpu, cpu_minutes=cpu / 60,
             per_cell=[o["secs"] for o in out]), indent=2) + "\n")

    assert len(df) == len(DATASETS) * len(MODELS) * len(CALIBRATORS) * len(SEEDS) == 360
    metrics = summarize_main(df)
    out_dir = Path("runs/main")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(dict(wall_seconds=round(wall, 1), cpu_minutes=round(cpu / 60, 2), rows=len(df)), indent=2))
    if cpu / 60 > 30:
        print("WARNING: main exceeded 30 CPU-minutes; stop and tell the PI before any further run (design step 14)")


if __name__ == "__main__":
    main()
