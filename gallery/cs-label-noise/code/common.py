"""Shared constants and helpers for experiment.py, exclusion.py and analyze.py.

Everything here is fixed by plan.json design.method (approved at the design gate).
"""
from __future__ import annotations

import json
import math
from fractions import Fraction
from pathlib import Path

import numpy as np

DATASETS = ("breast_cancer", "credit-g", "adult", "covtype")   # index d = 0..3 (design.method step 1)
DATASET_INDEX = {name: i for i, name in enumerate(DATASETS)}
METHODS = ("lr", "rf", "gbdt")                                   # main methods
SEEDS = tuple(range(10))                                         # s = 0..9
RHOS = (0.0, 0.1, 0.2, 0.3, 0.4)
N_CANDIDATES = 20                                                # random-search budget per method per cell
N_HALF = 10                                                      # ablation A3: best of the first 10 candidates
ROOT_SEED = 20261118
CAP = 5000                                                       # stratified row cap
BOOT_SEED = 20261119
N_BOOT = 10_000

# Training / test sizes after the cap and the 60/20/20 split (design.method STATISTICS).
SIZES = {"breast_cancer": (341, 114), "credit-g": (600, 200), "adult": (3000, 1000), "covtype": (3000, 1000)}
# Datasets on which every seed re-splits the same rows: Nadeau-Bengio corrected interval.
NB_CORRECTED = ("breast_cancer", "credit-g")

RESULTS = Path("results")
SCHEMA = Path("data/derived/schema.json")


def rho_key(rho: float) -> str:
    """'0.0' -> 'rho0', '0.4' -> 'rho0.4' style label used in metric names."""
    return f"rho{rho:g}"


def load_schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def write_metrics(path: str | Path, metrics: dict) -> None:
    """Write a FLAT JSON object (no nesting), as crew.py requires."""
    for key, value in list(metrics.items()):
        if isinstance(value, (dict, list)):
            raise TypeError(f"metric {key!r} is not flat")
        if isinstance(value, float) and not math.isfinite(value):
            metrics[key] = None          # strict JSON has no NaN/inf
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def exact_mean(values, n: int) -> Fraction:
    """Exact mean of accuracies that are counts out of n (code-r1 F1).

    Each value must be k/n for an integer k; the mean is returned as a Fraction so that
    pre-registered thresholds (0.05 headroom, 0.01 drop difference, 0.05 in r) are compared
    exactly instead of on rounded floating-point sums.
    """
    arr = np.asarray(values, dtype=float)
    counts = np.rint(arr * n).astype(np.int64)
    if not np.allclose(counts / n, arr, rtol=0, atol=1e-12):
        raise AssertionError("value is not a count out of n")
    return Fraction(int(counts.sum()), n * len(arr))
