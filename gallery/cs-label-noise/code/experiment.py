"""Label-noise experiment: one row per (dataset, method, variant, rho, seed) cell.

Implements plan.json design.method steps 1-8 exactly (approved at the design gate,
2026-11-18). Run from the workspace root, only through `crew.py run`.

    .venv/bin/python code/experiment.py --rhos 0 --variant main \
        --out results/cells_rho0.csv --metrics runs/main-rho0/metrics.json \
        --timing runs/main-rho0/timing.json

Variants
  main      LR, RF, GBDT; selection and GBDT early stopping on NOISY validation labels.
  gbdt_noes ablation A1: GBDT without early stopping, max_iter in the search space.
  cleanval  ablation A2: LR, RF, GBDT with NOISY training labels, but selection and GBDT
            early stopping on the CLEAN validation labels. Same candidate lists.
  --smoke   pipeline check on a non-study seed (100) with 2 candidates; writes no accuracy.

Randomness (design.method step 1): for dataset index d and seed s,
SeedSequence([20261118, d, s]).spawn(5) -> (sub, split, noise, cand, model), used in that
order; integers passed to scikit-learn are int(child.generate_state(1)[0]) (the second
split integer is generate_state(2)[1]); cand.spawn(4) gives one candidate stream per
method in the order lr, rf, gbdt, gbdt_noes. Every cell draws all its randomness from its
own (dataset, seed) streams, so results do not depend on the number of workers.

Fit times are written to a separate timing file, never to the metrics or the cell table,
because they do not reproduce.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
import warnings
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from threadpoolctl import threadpool_limits

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (CAP, DATASET_INDEX, DATASETS, N_CANDIDATES, N_HALF, ROOT_SEED, SEEDS,  # noqa: E402
                    SIZES, load_schema, rho_key, write_metrics)

N_JOBS = 8
CAND_STREAMS = ("lr", "rf", "gbdt", "gbdt_noes")   # order of cand.spawn(4)
VARIANT_METHODS = {"main": ("lr", "rf", "gbdt"), "gbdt_noes": ("gbdt_noes",), "cleanval": ("lr", "rf", "gbdt")}
# rough relative cost, used only to dispatch expensive cells first (does not affect results)
COST = {"covtype": 4.0, "adult": 3.0, "credit-g": 1.0, "breast_cancer": 0.5}
MCOST = {"gbdt": 3.0, "gbdt_noes": 2.0, "rf": 2.0, "lr": 1.0}


# ------------------------------------------------------------------ data

def load_dataset(name: str, schema: dict) -> tuple[pd.DataFrame, np.ndarray, list[str], list[str], int]:
    """Prepared table -> features (typed), integer target 0..K-1 in the schema's class order."""
    info = schema[name]
    num, cat = list(info["numeric_features"]), list(info["categorical_features"])
    dtypes = {c: "string" for c in cat}
    dtypes[info["target"]] = "string"
    frame = pd.read_csv(info["path"], dtype=dtypes, keep_default_na=True)
    classes = list(info["classes"])
    y_raw = frame[info["target"]].str.strip()
    if not set(y_raw.unique()) <= set(classes):
        raise AssertionError(f"{name}: labels outside the schema's classes")
    y = y_raw.map({c: i for i, c in enumerate(classes)}).to_numpy(dtype=np.int64)
    X = pd.DataFrame(index=frame.index)
    for c in num:
        X[c] = frame[c].astype("float64")
    for c in cat:  # object dtype with np.nan for missing, as SimpleImputer expects
        X[c] = frame[c].astype(object).where(frame[c].notna(), np.nan)
    return X, y, num, cat, len(classes)


def make_preprocessor(num: list[str], cat: list[str]) -> ColumnTransformer:
    parts = [("num", Pipeline([("imp", SimpleImputer(strategy="median")), ("sc", StandardScaler())]), num)]
    if cat:
        parts.append(("cat", Pipeline([
            ("imp", SimpleImputer(strategy="constant", fill_value="missing")),
            ("oh", OneHotEncoder(handle_unknown="ignore", sparse_output=False)),
        ]), cat))
    return ColumnTransformer(parts, sparse_threshold=0.0)


def sk_int(child: np.random.SeedSequence, index: int = 0) -> int:
    return int(child.generate_state(index + 1)[index])


def loguni(rng: np.random.Generator, lo: float, hi: float) -> float:
    return float(10 ** rng.uniform(np.log10(lo), np.log10(hi)))


def logint(rng: np.random.Generator, lo: float, hi: float) -> int:
    return int(np.round(loguni(rng, lo, hi)))


def draw_candidates(stream: str, rng: np.random.Generator, n: int) -> list[dict]:
    """design.method step 5 search spaces."""
    out = []
    for _ in range(n):
        if stream == "lr":
            out.append({"C": loguni(rng, 1e-4, 1e2)})
        elif stream == "rf":
            out.append({"max_features": float(rng.uniform(0.05, 0.7)),
                        "min_samples_leaf": logint(rng, 1, 50),
                        "max_samples": float(rng.uniform(0.5, 1.0))})
        else:
            c = {"learning_rate": loguni(rng, 0.01, 0.3), "max_leaf_nodes": logint(rng, 4, 64),
                 "min_samples_leaf": logint(rng, 2, 100), "l2_regularization": loguni(rng, 1e-4, 10.0)}
            if stream == "gbdt_noes":
                c["max_iter"] = logint(rng, 10, 500)
            out.append(c)
    return out


def prepare(name: str, seed: int, X: pd.DataFrame, y: np.ndarray, num: list[str], cat: list[str],
            k: int, n_cand: int, check_sizes: bool = True) -> dict:
    """Subsample, split, preprocess, draw the noise arrays and the candidate lists for (dataset, seed).

    Everything here is shared by all rho, methods and variants of this (dataset, seed).
    """
    ss = np.random.SeedSequence([ROOT_SEED, DATASET_INDEX[name], seed])
    sub, split, noise, cand, model = ss.spawn(5)
    if len(y) > CAP:
        X, _, y, _ = train_test_split(X, y, train_size=CAP, stratify=y, random_state=sk_int(sub))
    X_rest, X_te, y_rest, y_te = train_test_split(X, y, test_size=0.2, stratify=y, random_state=sk_int(split, 0))
    X_tr, X_va, y_tr, y_va = train_test_split(X_rest, y_rest, test_size=0.25, stratify=y_rest,
                                              random_state=sk_int(split, 1))
    if check_sizes:
        n_tr, n_te = SIZES[name]
        assert (len(y_tr), len(y_va), len(y_te)) == (n_tr, n_te, n_te), (name, len(y_tr), len(y_va), len(y_te))
    for part, lab in (("train", y_tr), ("val", y_va), ("test", y_te)):
        missing = set(range(k)) - set(np.unique(lab).tolist())
        assert not missing, f"{name} seed {seed}: classes {missing} absent from the {part} split"
    pre = make_preprocessor(num, cat).fit(X_tr)          # features of the training split only; no labels
    Xt = [np.ascontiguousarray(pre.transform(a), dtype=np.float64) for a in (X_tr, X_va, X_te)]
    rng = np.random.default_rng(noise)
    perm_tr = rng.permutation(len(y_tr))
    shift_tr = rng.integers(1, k, size=len(y_tr))
    perm_va = rng.permutation(len(y_va))
    shift_va = rng.integers(1, k, size=len(y_va))
    cand_rngs = [np.random.default_rng(c) for c in cand.spawn(4)]
    cands = {s: draw_candidates(s, r, n_cand) for s, r in zip(CAND_STREAMS, cand_rngs)}
    return {"dataset": name, "seed": seed, "K": k, "X_tr": Xt[0], "X_va": Xt[1], "X_te": Xt[2],
            "y_tr": np.asarray(y_tr), "y_va": np.asarray(y_va), "y_te": np.asarray(y_te),
            "perm_tr": perm_tr, "shift_tr": shift_tr, "perm_va": perm_va, "shift_va": shift_va,
            "cands": cands, "model_rs": sk_int(model), "n_features": Xt[0].shape[1]}


# ------------------------------------------------------------------ noise

def n_flip(rho: float, n: int) -> int:
    """floor(rho * n + 0.5), computed exactly from the decimal rate."""
    return math.floor(Fraction(str(rho)) * n + Fraction(1, 2))


def flip(y: np.ndarray, perm: np.ndarray, shift: np.ndarray, rho: float, k: int) -> tuple[np.ndarray, int]:
    n = n_flip(rho, len(y))
    idx = perm[:n]
    out = y.copy()
    out[idx] = (y[idx] + shift[idx]) % k
    assert int(np.sum(out != y)) == n, "flip count differs from n_flip"
    assert not np.any(out[idx] == y[idx]), "a flipped label equals its clean label"
    return out, n


# ------------------------------------------------------------------ models

def build(method: str, params: dict, rs: int):
    if method == "lr":
        # l1_ratio=0 is L2; 'penalty' is deprecated in 1.9 and not passed; lbfgs is multinomial for K > 2
        return LogisticRegression(C=params["C"], l1_ratio=0.0, solver="lbfgs", max_iter=2000, tol=1e-4)
    if method == "rf":
        return RandomForestClassifier(n_estimators=200, criterion="gini", bootstrap=True, max_depth=None,
                                      n_jobs=1, random_state=rs, **params)
    if method == "gbdt":
        return HistGradientBoostingClassifier(loss="log_loss", max_iter=1000, early_stopping=True,
                                              scoring="loss", n_iter_no_change=20, tol=1e-7, max_bins=255,
                                              categorical_features=None, random_state=rs, **params)
    if method == "gbdt_noes":
        return HistGradientBoostingClassifier(loss="log_loss", early_stopping=False, max_bins=255,
                                              categorical_features=None, random_state=rs, **params)
    raise ValueError(method)


def run_cell(prep: dict, method: str, variant: str, rho: float, n_half: int, smoke: bool) -> tuple[dict, dict]:
    with threadpool_limits(limits=1), warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        k = prep["K"]
        y_tr, y_va, y_te = prep["y_tr"], prep["y_va"], prep["y_te"]
        y_tr_n, nf_tr = flip(y_tr, prep["perm_tr"], prep["shift_tr"], rho, k)
        y_va_n, nf_va = flip(y_va, prep["perm_va"], prep["shift_va"], rho, k)
        # nested flips: the flipped set at rho is the first n_flip entries of one fixed permutation
        assert np.array_equal(np.flatnonzero(y_tr_n != y_tr), np.sort(prep["perm_tr"][:nf_tr]))
        y_sel = y_va if variant == "cleanval" else y_va_n    # labels for selection AND GBDT early stopping
        stream = "gbdt" if method == "gbdt" else method
        cands = prep["cands"][stream]
        X_tr, X_va, X_te = prep["X_tr"], prep["X_va"], prep["X_te"]
        best = (-1.0, -1, None)          # (selection accuracy, index, model); ties -> earlier candidate
        best_half = (-1.0, -1, None)
        fit_seconds = []
        for i, params in enumerate(cands):
            m = build(method, params, prep["model_rs"])
            t0 = time.perf_counter()
            if method == "gbdt":
                m.fit(X_tr, y_tr_n, X_val=X_va, y_val=y_sel)
            else:
                m.fit(X_tr, y_tr_n)
            fit_seconds.append(time.perf_counter() - t0)
            acc = accuracy_score(y_sel, m.predict(X_va))
            if acc > best[0]:
                best = (acc, i, m)
            if i < n_half and acc > best_half[0]:
                best_half = (acc, i, m)
        model = best[2]
        pred_te = model.predict(X_te)                        # the one test prediction of this cell
        pred_half = pred_te if best_half[1] == best[1] else best_half[2].predict(X_te)   # A3 configuration
        assert np.array_equal(y_te, prep["y_te"])            # test labels are never changed
        counts = np.bincount(y_te, minlength=k)
        maj = int(np.argmax(counts))
        params = dict(cands[best[1]])
        n_iter = int(model.n_iter_) if method in ("gbdt", "gbdt_noes") else None
        row = {
            "dataset": prep["dataset"], "method": method, "variant": variant, "rho": rho, "seed": prep["seed"],
            "test_acc": float(accuracy_score(y_te, pred_te)),
            "test_acc_half": float(accuracy_score(y_te, pred_half)),
            "majority_rate": float(counts[maj] / len(y_te)),
            "val_acc_noisy": float(accuracy_score(y_va_n, model.predict(X_va))),
            "val_acc_clean": float(accuracy_score(y_va, model.predict(X_va))),
            "train_acc_noisy": float(accuracy_score(y_tr_n, model.predict(X_tr))),
            "pred_majority_share": float(np.mean(pred_te == maj)),
            "n_iter": n_iter, "sel_index": best[1], "half_index": best_half[1],
            "params": json.dumps(params, sort_keys=True),
            "n_train": len(y_tr), "n_val": len(y_va), "n_test": len(y_te), "K": k,
            "n_features": prep["n_features"],
            "n_flipped_train": nf_tr, "n_flipped_val": nf_va,
            "n_flip_expected_train": n_flip(rho, len(y_tr)), "n_flip_expected_val": n_flip(rho, len(y_va)),
            "n_convergence_warnings": sum(issubclass(w.category, ConvergenceWarning) for w in caught),
        }
        timing = {"dataset": prep["dataset"], "method": method, "variant": variant, "rho": rho,
                  "seed": prep["seed"], "fit_seconds_total": float(np.sum(fit_seconds)),
                  "fit_seconds_max": float(np.max(fit_seconds))}
        if smoke:   # structural facts only; no accuracy leaves a smoke run
            for key in ("test_acc", "test_acc_half", "majority_rate", "val_acc_noisy", "val_acc_clean",
                        "train_acc_noisy", "pred_majority_share", "params", "sel_index", "half_index"):
                row.pop(key)
        return row, timing


# ------------------------------------------------------------------ main

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rhos", nargs="+", type=float, required=True)
    ap.add_argument("--variant", choices=tuple(VARIANT_METHODS), required=True)
    ap.add_argument("--out", required=True, help="cell table (CSV)")
    ap.add_argument("--metrics", help="flat JSON ledger metrics")
    ap.add_argument("--timing", help="wall/fit times (not metrics)")
    ap.add_argument("--smoke", action="store_true", help="seed 100, 2 candidates, no accuracies written")
    ap.add_argument("--n-jobs", type=int, default=N_JOBS)
    args = ap.parse_args()
    if args.variant == "main" and not args.smoke and any(r > 0 for r in args.rhos) \
            and not Path("results/exclusion.json").is_file():
        sys.exit("ERROR: noisy main cells need results/exclusion.json (run exclusion-check first)")

    t_start = time.perf_counter()
    schema = load_schema()
    seeds = (100,) if args.smoke else SEEDS
    n_cand = 2 if args.smoke else N_CANDIDATES
    n_half = 1 if args.smoke else N_HALF
    preps = []
    for name in DATASETS:
        X, y, num, cat, k = load_dataset(name, schema)
        for s in seeds:
            preps.append(prepare(name, s, X, y, num, cat, k, n_cand))
    t_prep = time.perf_counter() - t_start

    methods = VARIANT_METHODS[args.variant]
    tasks = [(p, m, r) for p in preps for m in methods for r in args.rhos]
    tasks.sort(key=lambda t: -COST[t[0]["dataset"]] * MCOST[t[1]])   # dispatch order only
    out = Parallel(n_jobs=args.n_jobs, batch_size=1)(
        delayed(run_cell)(p, m, args.variant, r, n_half, args.smoke) for p, m, r in tasks)
    rows = [o[0] for o in out]
    times = [o[1] for o in out]

    order = {"dataset": {d: i for i, d in enumerate(DATASETS)}}
    table = pd.DataFrame(rows)
    table["_d"] = table["dataset"].map(order["dataset"])
    table = table.sort_values(["_d", "method", "rho", "seed"]).drop(columns="_d").reset_index(drop=True)
    assert (table["n_flipped_train"] == table["n_flip_expected_train"]).all()
    assert (table["n_flipped_val"] == table["n_flip_expected_val"]).all()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(args.out, index=False)

    if args.metrics:
        metrics: dict = {"n_cells": int(len(table)), "n_fits": int(len(table) * n_cand),
                         "n_candidates": n_cand, "n_seeds": len(seeds),
                         "n_flip_count_failures": int(((table["n_flipped_train"] != table["n_flip_expected_train"])
                                                       | (table["n_flipped_val"] != table["n_flip_expected_val"])).sum()),
                         "n_convergence_warnings": int(table["n_convergence_warnings"].sum())}
        if args.smoke:
            for name in DATASETS:
                sub = table[table["dataset"] == name].iloc[0]
                for key in ("n_train", "n_val", "n_test", "K", "n_features"):
                    metrics[f"{name}.{key}"] = int(sub[key])
        else:
            for name in DATASETS:
                td = table[table["dataset"] == name]
                maj = td.drop_duplicates("seed").sort_values("seed")["majority_rate"].to_numpy()
                if 0.0 in args.rhos:
                    metrics[f"{name}.m_mean"] = float(np.mean(maj))
                    for s, v in enumerate(maj):
                        metrics[f"{name}.m.s{s}"] = float(v)
                for method in methods:
                    for rho in args.rhos:
                        cell = td[(td["method"] == method) & (td["rho"] == rho)].sort_values("seed")
                        acc = cell["test_acc"].to_numpy()
                        assert len(acc) == len(SEEDS)
                        base = f"{name}.{method}.{rho_key(rho)}"
                        metrics[f"{base}.acc_mean"] = float(np.mean(acc))
                        metrics[f"{base}.acc_sd"] = float(np.std(acc, ddof=1))
                        metrics[f"{base}.n_seeds"] = int(len(acc))
                        for s, v in zip(cell["seed"], acc):
                            metrics[f"{base}.acc.s{int(s)}"] = float(v)
        write_metrics(args.metrics, metrics)

    wall = time.perf_counter() - t_start
    if args.timing:
        Path(args.timing).parent.mkdir(parents=True, exist_ok=True)
        Path(args.timing).write_text(json.dumps({
            "note": "Machine-dependent; not ledger metrics.", "n_jobs": args.n_jobs,
            "wall_seconds": wall, "prepare_seconds": t_prep,
            "cpu_fit_seconds": float(sum(t["fit_seconds_total"] for t in times)),
            "cells": sorted(times, key=lambda t: (t["dataset"], t["method"], t["rho"], t["seed"])),
        }, indent=1), encoding="utf-8")
    print(f"{len(table)} cells in {wall:.1f} s (prepare {t_prep:.1f} s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
