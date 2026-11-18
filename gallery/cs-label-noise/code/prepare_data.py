"""Prepare the four fetched datasets and count label-only and feature-only facts.

Run from the workspace root, only through the crew tool:

    python3 crew.py run <ws> --id prepare-data --role data-ra --kind data-prep \
        --code code/prepare_data.py --input data/manifest.json ... \
        --metrics runs/prepare-data/metrics.json -- .venv/bin/python code/prepare_data.py

Reads   data/manifest.json and data/raw/<name>.csv (written by code/fetch_data.py)
Writes  data/derived/<name>.csv     every row kept; features then a final `target` column
        data/derived/schema.json    per dataset: numeric / categorical columns, classes
        runs/prepare-data/metrics.json

Preparation is deliberately minimal and design-neutral: no rows are dropped, no row cap
(the 5,000-row stratified cap is drawn per seed by the experiment code), no imputation,
no encoding, no scaling. Categorical values are read as strings with surrounding
whitespace removed; missing values stay missing.

The metrics are label-only (class counts, majority share) or feature-only (types, missing
values, duplicate rows) facts. No model is trained and no relationship between features
and labels is computed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

MANIFEST = Path("data/manifest.json")
DERIVED = Path("data/derived")
METRICS = Path("runs/prepare-data/metrics.json")
ORDER = ["breast_cancer", "credit-g", "adult", "covtype"]

# What each source's own documentation reports, for the comparison in data/CODEBOOK.md.
#   breast_cancer: scikit-learn DESCR (breast_cancer.rst) and UCI dataset 17
#   credit-g:      UCI german.doc (1000 instances; 20 attributes: 7 numerical, 13 categorical);
#                  OpenML data 31 qualities (700 good / 300 bad, 0 missing)
#   adult:         UCI adult.names (48842 instances = 32561 train + 16281 test; P(>50K) 23.93%);
#                  OpenML data 1590 qualities (6 numeric + 8 nominal features, 37155 / 11687,
#                  6465 missing values in 3620 instances)
#   covtype:       UCI covtype.info (581012 instances; 54 columns = 10 quantitative +
#                  4 binary wilderness + 40 binary soil; class distribution in section 10)
SOURCE = {
    "breast_cancer": {"rows": 569, "n_features": 30, "n_numeric": 30, "n_categorical": 0,
                      "class_counts": {"0": 212, "1": 357}, "missing_cells": 0},
    "credit-g": {"rows": 1000, "n_features": 20, "n_numeric": 7, "n_categorical": 13,
                 "class_counts": {"good": 700, "bad": 300}, "missing_cells": 0},
    "adult": {"rows": 48842, "n_features": 14, "n_numeric": 6, "n_categorical": 8,
              "class_counts": {"<=50K": 37155, ">50K": 11687}, "missing_cells": 6465,
              "rows_with_missing": 3620},
    "covtype": {"rows": 581012, "n_features": 54, "n_numeric": 54, "n_categorical": 0,
                "class_counts": {"1": 211840, "2": 283301, "3": 35754, "4": 2747, "5": 9493,
                                 "6": 17367, "7": 20510}, "missing_cells": 0},
}


def load_raw(entry: dict) -> pd.DataFrame:
    categorical = entry["categorical_features"]
    dtypes = {c: "string" for c in categorical}
    dtypes["target"] = "string"
    frame = pd.read_csv(entry["path"], dtype=dtypes, keep_default_na=True)
    expected = entry["numeric_features"] + categorical + ["target"]
    if sorted(frame.columns) != sorted(expected):
        sys.exit(f"ERROR: {entry['id']}: columns in {entry['path']} differ from the manifest")
    for column in categorical + ["target"]:
        frame[column] = frame[column].str.strip()
    for column in entry["numeric_features"]:
        if not pd.api.types.is_numeric_dtype(frame[column]):
            sys.exit(f"ERROR: {entry['id']}: numeric column {column!r} did not parse as numbers")
    return frame


def describe(name: str, frame: pd.DataFrame, entry: dict) -> dict:
    features = [c for c in frame.columns if c != "target"]
    numeric, categorical = entry["numeric_features"], entry["categorical_features"]
    binary = [c for c in numeric if set(frame[c].dropna().unique()) <= {0, 1}]
    counts = frame["target"].value_counts(dropna=False)
    missing = frame[features].isna()
    out = {
        "rows_raw": int(frame.shape[0]),
        "rows": int(frame.shape[0]),
        "rows_dropped": 0,
        "n_features": len(features),
        "n_numeric": len(numeric),
        "n_numeric_binary_0_1": len(binary),
        "n_categorical": len(categorical),
        "n_classes": int(counts.size),
        "majority_class": str(counts.index[0]),
        "majority_share": float(counts.iloc[0] / frame.shape[0]),
        "minority_share": float(counts.iloc[-1] / frame.shape[0]),
        "missing_target": int(frame["target"].isna().sum()),
        "missing_cells": int(missing.to_numpy().sum()),
        "rows_with_missing": int(missing.any(axis=1).sum()),
        "columns_with_missing": int(missing.any(axis=0).sum()),
        "duplicate_rows": int(frame.duplicated().sum()),
    }
    for label, count in counts.items():
        out[f"class_count.{label}"] = int(count)
    for column in features:
        n = int(missing[column].sum())
        if n:
            out[f"missing.{column}"] = n
    for column in categorical:
        out[f"levels.{column}"] = int(frame[column].nunique(dropna=True))

    source = SOURCE[name]
    checks = {
        "rows": out["rows"] == source["rows"],
        "n_features": out["n_features"] == source["n_features"],
        "n_numeric": out["n_numeric"] == source["n_numeric"],
        "n_categorical": out["n_categorical"] == source["n_categorical"],
        "class_counts": {str(k): int(v) for k, v in counts.items()} == source["class_counts"],
        "missing_cells": out["missing_cells"] == source["missing_cells"],
    }
    if "rows_with_missing" in source:
        checks["rows_with_missing"] = out["rows_with_missing"] == source["rows_with_missing"]
    for key, ok in checks.items():
        out[f"matches_source.{key}"] = bool(ok)
    return out


def main() -> None:
    manifest = {d["id"]: d for d in json.loads(MANIFEST.read_text(encoding="utf-8"))["datasets"]}
    if sorted(manifest) != sorted(ORDER):
        sys.exit(f"ERROR: manifest has {sorted(manifest)}, expected {sorted(ORDER)}")
    DERIVED.mkdir(parents=True, exist_ok=True)
    metrics: dict = {}
    schema: dict = {}
    for name in ORDER:
        entry = manifest[name]
        frame = load_raw(entry)
        columns = entry["numeric_features"] + entry["categorical_features"]
        frame = frame[[c for c in frame.columns if c in columns] + ["target"]]
        frame.to_csv(DERIVED / f"{name}.csv", index=False, lineterminator="\n")
        facts = describe(name, frame, entry)
        for key, value in facts.items():
            metrics[f"{name}.{key}"] = value
        schema[name] = {
            "path": f"data/derived/{name}.csv",
            "target": "target",
            "classes": sorted(str(c) for c in frame["target"].dropna().unique()),
            "numeric_features": entry["numeric_features"],
            "categorical_features": entry["categorical_features"],
            "missing_values_in": [c for c in columns if frame[c].isna().any()],
        }
        print(f"{name}: rows={facts['rows']} features={facts['n_features']} "
              f"(num {facts['n_numeric']}, cat {facts['n_categorical']}) classes={facts['n_classes']} "
              f"majority={facts['majority_class']} {facts['majority_share']:.4f} "
              f"missing={facts['missing_cells']}")
    (DERIVED / "schema.json").write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    failed = [k for k, v in metrics.items() if ".matches_source." in k and v is False]
    if failed:
        print("Differences from the source documentation: " + ", ".join(failed))


if __name__ == "__main__":
    main()
