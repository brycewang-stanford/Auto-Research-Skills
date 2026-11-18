"""Exclusion check (run exclusion-check): reads ONLY the rho=0 cell table.

plan.json design.method 'Exclusion': for H1 a dataset is uninformative if A(0) - m < 0.05
for GBDT or RF; for H2, if it is below 0.05 for any of the three methods. A(0) is the mean
over the 10 seeds of clean-test accuracy at rho=0 and m the mean over seeds of the test
majority rate. A dataset is excluded whole, never a seed. Writes results/exclusion.json,
which code/analyze.py reads and never recomputes.

    .venv/bin/python code/exclusion.py --metrics runs/exclusion-check/metrics.json
"""
from __future__ import annotations

import argparse
import json
import sys
from fractions import Fraction
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATASETS, METHODS, RESULTS, SEEDS, SIZES, exact_mean, write_metrics  # noqa: E402

THRESHOLD = 0.05
THRESHOLD_X = Fraction(5, 100)   # compared exactly on test-set counts (code-r1 F1)
H1_METHODS = ("gbdt", "rf")
H2_METHODS = ("lr", "rf", "gbdt")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cells", default=str(RESULTS / "cells_rho0.csv"))
    ap.add_argument("--out", default=str(RESULTS / "exclusion.json"))
    ap.add_argument("--metrics", required=True)
    args = ap.parse_args()

    cells = pd.read_csv(args.cells)
    assert set(cells["rho"].unique()) == {0.0}, "the exclusion check may read rho=0 cells only"
    assert set(cells["variant"].unique()) == {"main"}

    metrics: dict = {"threshold": THRESHOLD}
    record = {"threshold": THRESHOLD, "rule": "uninformative if A(0) - m < 0.05 for a compared method",
              "source": args.cells, "headroom": {}, "A0": {}, "m": {}, "informative_h1": [], "informative_h2": []}
    for name in DATASETS:
        td = cells[cells["dataset"] == name]
        n_te = SIZES[name][1]
        mx = exact_mean(td.drop_duplicates("seed").sort_values("seed")["majority_rate"].to_numpy(), n_te)
        m = float(mx)
        record["m"][name] = m
        heads = {}
        for method in METHODS:
            acc = td[td["method"] == method].sort_values("seed")["test_acc"].to_numpy()
            assert len(acc) == len(SEEDS)
            a0x = exact_mean(acc, n_te)
            heads[method] = a0x - mx
            record["A0"].setdefault(name, {})[method] = float(a0x)
            metrics[f"{name}.{method}.headroom"] = float(a0x - mx)
        record["headroom"][name] = {k: float(v) for k, v in heads.items()}
        h1 = all(heads[k] >= THRESHOLD_X for k in H1_METHODS)
        h2 = all(heads[k] >= THRESHOLD_X for k in H2_METHODS)
        if h1:
            record["informative_h1"].append(name)
        if h2:
            record["informative_h2"].append(name)
        metrics[f"{name}.m_mean"] = m
        metrics[f"{name}.informative_h1"] = int(h1)
        metrics[f"{name}.informative_h2"] = int(h2)
    metrics["n_informative_h1"] = len(record["informative_h1"])
    metrics["n_informative_h2"] = len(record["informative_h2"])
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(record, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    write_metrics(args.metrics, metrics)
    print(json.dumps({"informative_h1": record["informative_h1"], "informative_h2": record["informative_h2"]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
