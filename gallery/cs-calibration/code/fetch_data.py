"""Fetch the four study datasets from OpenML through scikit-learn and record their provenance.

Run from the workspace root, only through the crew tool (a data-prep run):

    python3 crew.py run <ws> --id fetch-data --role data-ra --kind data-prep \
        --code code/fetch_data.py --metrics runs/fetch-data/metrics.json \
        --output data/manifest.json --output data/raw/<name>.csv ... \
        -- .venv/bin/python code/fetch_data.py

Writes
  data/raw/<name>.csv            features in OpenML column order + a final integer `target`
                                 column (0/1), rows in the order of the OpenML ARFF file
  data/raw/sklearn_home/         scikit-learn's download cache (never ~/scikit_learn_data)
  data/manifest.json             origin, licence, path, sha256, retrieval date per dataset
  runs/fetch-data/profile.json   per-column profile (type, missing, distinct, range) used
                                 for data/CODEBOOK.md
  runs/fetch-data/metrics.json   flat metrics (rows, positive share, sha256 per dataset)

Pinning
  adult           OpenML data_id 1590, version 2 (ARFF file_id 1595261)
  bank-marketing  OpenML data_id 1461, version 1 (ARFF file_id 1586218)
  electricity     OpenML data_id 151,  version 1 (ARFF file_id 2419)
  phoneme         OpenML data_id 1489, version 1 (ARFF file_id 1592281)

scikit-learn checks OpenML's published md5 for each ARFF on download; this script also
asserts the data_id, name, version, file_id and md5 it received against the pins below and
re-checks the md5 of the cached ARFF itself, so a silent re-upload fails loudly.

The only label statistic computed is the marginal class count of each dataset (to fix and
check the 0/1 encoding). Nothing here relates any feature to the label.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import sklearn
from sklearn import datasets

RAW = Path("data/raw")
SKL_HOME = RAW / "sklearn_home"
MANIFEST = Path("data/manifest.json")
METRICS = Path("runs/fetch-data/metrics.json")
PROFILE = Path("runs/fetch-data/profile.json")

# The 'pandas' ARFF parser of scikit-learn 1.9.1 fails under pandas 3.1.1 on nominal
# attributes whose values look like integers (bank-marketing and phoneme: Class {1,2};
# electricity: day {1..7}): pandas infers integer categories and sklearn's quote
# stripping then raises TypeError. The pure-Python LIAC-ARFF parser bundled with
# scikit-learn reads every nominal value as a string and is used for all four datasets.
PARSER = "liac-arff"

# Pins taken from the OpenML data descriptions (api/v1/json/data/<id>) read on 2026-11-19.
# `positive` is the raw OpenML label coded 1; the other label is coded 0.
# `expected` are OpenML's published qualities (NumberOfInstances, MinorityClassSize,
# NumberOfMissingValues), checked after loading.
PINS = {
    "adult": {
        "data_id": 1590, "version": 2, "file_id": 1595261,
        "md5": "bb6510925e5d4b23d136715febb2cdf5",
        "target_attr": "class", "positive": ">50K", "negative": "<=50K",
        "positive_meaning": "income > 50K USD per year",
        "source_page": "https://archive.ics.uci.edu/dataset/2/adult",
        "source_licence": "CC BY 4.0, as stated on the UCI ML Repository page for the original data",
        "expected": {"rows": 48842, "minority": 11687, "missing_cells": 6465},
    },
    "bank-marketing": {
        "data_id": 1461, "version": 1, "file_id": 1586218,
        "md5": "b29d2eb78e508569fd41172c97bda00e",
        "target_attr": "Class", "positive": "2", "negative": "1",
        "positive_meaning": "client subscribed a term deposit (UCI y = 'yes')",
        "source_page": "https://archive.ics.uci.edu/dataset/222/bank+marketing",
        "source_licence": "CC BY 4.0, as stated on the UCI ML Repository page for the original data",
        "expected": {"rows": 45211, "minority": 5289, "missing_cells": 0},
    },
    "electricity": {
        "data_id": 151, "version": 1, "file_id": 2419,
        "md5": "8ca97867d960ae029ae3a9ac2c923d34",
        "target_attr": "class", "positive": "UP", "negative": "DOWN",
        "positive_meaning": "NSW price UP relative to the moving average of the last 24 hours",
        "source_page": "http://www.inescporto.pt/~jgama/ales/ales_5.html",
        "source_licence": "no licence stated by the original source (J. Gama, ELEC2); OpenML lists it as 'Public'",
        "expected": {"rows": 45312, "minority": 19237, "missing_cells": 0},
    },
    "phoneme": {
        "data_id": 1489, "version": 1, "file_id": 1592281,
        "md5": "902ff27649dbfb512f3fb01fc05c6b24",
        "target_attr": "Class", "positive": "2", "negative": "1",
        "positive_meaning": "oral vowel (ELENA class 1; OpenML label '2')",
        "source_page": "https://sci2s.ugr.es/keel/dataset.php?cod=105",
        "source_licence": "no licence stated by the original sources (ELENA project, KEEL); OpenML lists it as 'Public'",
        "expected": {"rows": 5404, "minority": 1586, "missing_cells": 0},
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def profile_column(series: pd.Series) -> dict:
    categorical = isinstance(series.dtype, pd.CategoricalDtype) or series.dtype == object
    out = {
        "type": "categorical" if categorical else "numeric",
        "dtype": str(series.dtype),
        "missing": int(series.isna().sum()),
        "distinct": int(series.nunique(dropna=True)),
    }
    if categorical:
        cats = (list(series.cat.categories) if isinstance(series.dtype, pd.CategoricalDtype)
                else sorted(series.dropna().unique()))
        out["levels"] = [str(c) for c in cats]
    else:
        values = series.astype("float64")
        out["min"] = float(values.min())
        out["max"] = float(values.max())
        out["mean"] = float(values.mean())
        out["integer_valued"] = bool(np.all(np.round(values.dropna()) == values.dropna()))
    return out


def electricity_time_checks(frame: pd.DataFrame) -> dict:
    """Feature-only checks of the time ordering of electricity (no use of the label).

    ELEC2 has 48 half-hour periods per day. The checks ask whether the file is a sequence
    of whole days (period 0 -> 1 in 48 steps), whether day of week advances by one from
    block to block, and whether the normalised `date` column is monotone in file order.
    """
    date = frame["date"].astype("float64").to_numpy()
    period = frame["period"].astype("float64").to_numpy()
    day = frame["day"].astype(str).astype(int).to_numpy()
    n = len(frame)
    block = np.arange(n) // 48
    whole_days = n % 48 == 0
    per_block = pd.DataFrame({"block": block, "date": date, "period": period, "day": day}).groupby("block")
    block_date = per_block["date"].first()
    block_day = per_block["day"].first()
    date_drops = np.flatnonzero(np.diff(date) < 0) + 1
    checks = {
        "rows": n,
        "rows_are_whole_days_of_48": bool(whole_days),
        "days_in_file": int(block.max() + 1),
        "each_48_row_block_is_one_day_period_0_to_1": bool(per_block["period"].apply(
            lambda s: s.is_monotonic_increasing and s.iloc[0] == 0.0 and s.iloc[-1] == 1.0
            and s.nunique() == 48).all()),
        "date_constant_within_each_block": bool((per_block["date"].nunique() == 1).all()),
        "day_constant_within_each_block": bool((per_block["day"].nunique() == 1).all()),
        "day_of_week_advances_by_one_each_block": bool(((np.diff(block_day.to_numpy()) % 7) == 1).all()),
        "first_block_day_of_week": int(block_day.iloc[0]),
        "distinct_date_values": int(np.unique(date).size),
        "date_nondecreasing_in_file_order": bool((np.diff(date) >= 0).all()),
        "date_decreases_in_file_order": int(date_drops.size),
        "date_decrease_rows": [int(i) for i in date_drops],
        "date_first_row": float(date[0]),
        "date_last_row": float(date[-1]),
        "date_argmax_row": int(np.argmax(date)),
        "blocks_sharing_a_date_value_with_another_block": int(block_date.duplicated(keep=False).sum()),
    }
    # the Victoria columns are known to be filled with a constant in the early part of ELEC2
    for col in ("vicprice", "vicdemand", "transfer"):
        values = frame[col].astype("float64").to_numpy()
        changed = np.flatnonzero(values != values[0])
        checks[f"{col}_leading_constant_rows"] = int(changed[0]) if changed.size else n
        checks[f"{col}_leading_constant_value"] = float(values[0])
    return checks


def fetch(name: str) -> tuple[dict, dict]:
    pin = PINS[name]
    bunch = datasets.fetch_openml(data_id=pin["data_id"], data_home=str(SKL_HOME),
                                  as_frame=True, parser=PARSER)
    details = bunch.details
    got = {"data_id": int(details["id"]), "name": details["name"], "version": int(details["version"]),
           "file_id": int(details["file_id"]), "md5": details["md5_checksum"]}
    want = {"data_id": pin["data_id"], "name": name, "version": pin["version"],
            "file_id": pin["file_id"], "md5": pin["md5"]}
    if got != want:
        sys.exit(f"ERROR: OpenML metadata {got} does not match the pin {want}")
    if details.get("default_target_attribute") != pin["target_attr"]:
        sys.exit(f"ERROR: {name}: default target {details.get('default_target_attribute')!r} "
                 f"is not {pin['target_attr']!r}")

    cached = sorted((SKL_HOME / "openml" / "openml.org" / "data" / "v1" / "download"
                     / str(pin["file_id"])).glob("*.arff.gz"))
    if len(cached) != 1:
        sys.exit(f"ERROR: expected one cached ARFF for OpenML file_id {pin['file_id']}, found {cached}")
    arff = gzip.decompress(cached[0].read_bytes())
    if hashlib.md5(arff).hexdigest() != pin["md5"]:
        sys.exit(f"ERROR: md5 of the {name} ARFF does not match OpenML's md5_checksum")

    raw_label = bunch.target.astype(str)
    labels = sorted(raw_label.unique())
    if labels != sorted([pin["positive"], pin["negative"]]):
        sys.exit(f"ERROR: {name}: labels {labels} are not {{{pin['positive']}, {pin['negative']}}}")
    counts = raw_label.value_counts()

    frame = bunch.data.copy()
    if "target" in frame.columns:
        sys.exit(f"ERROR: {name} already has a feature named 'target'")
    frame["target"] = (raw_label == pin["positive"]).astype("int64").to_numpy()

    exp = pin["expected"]
    missing_cells = int(bunch.data.isna().sum().sum())
    checks = {
        "rows": (int(frame.shape[0]), exp["rows"]),
        "minority_class_size": (int(counts.min()), exp["minority"]),
        "missing_cells": (missing_cells, exp["missing_cells"]),
    }
    for key, (seen, expected) in checks.items():
        if seen != expected:
            sys.exit(f"ERROR: {name}: {key} = {seen}, OpenML reports {expected}")

    path = RAW / f"{name}.csv"
    frame.to_csv(path, index=False, lineterminator="\n")

    columns = {c: profile_column(bunch.data[c]) for c in bunch.data.columns}
    numeric = [c for c, p in columns.items() if p["type"] == "numeric"]
    categorical = [c for c, p in columns.items() if p["type"] == "categorical"]
    n_pos = int(counts[pin["positive"]])
    n_neg = int(counts[pin["negative"]])
    rows_with_missing = int(bunch.data.isna().any(axis=1).sum())

    entry = {
        "id": name,
        "origin": f"https://www.openml.org/d/{pin['data_id']} (OpenML data_id {pin['data_id']}, version "
                  f"{pin['version']}, ARFF {details['url']}), via sklearn.datasets.fetch_openml",
        "loader": f"sklearn.datasets.fetch_openml(data_id={pin['data_id']}, data_home='{SKL_HOME.as_posix()}', "
                  f"as_frame=True, parser='{PARSER}')",
        "openml": {
            "data_id": pin["data_id"],
            "name": details["name"],
            "version": pin["version"],
            "file_id": pin["file_id"],
            "md5_checksum": pin["md5"],
            "upload_date": details.get("upload_date"),
            "status": details.get("status"),
            "format": details.get("format"),
            "default_target_attribute": details.get("default_target_attribute"),
            "licence": details.get("licence"),
            "original_data_url": details.get("original_data_url"),
        },
        "source_page": pin["source_page"],
        "version": f"OpenML version {pin['version']}",
        "source_file": f"{details['url']} (cached as {cached[0].as_posix()}; md5 checked against OpenML)",
        "source_file_md5": pin["md5"],
        "source_file_sha256": hashlib.sha256(arff).hexdigest(),
        "license": f"OpenML licence field: {details.get('licence')!r}; original source: {pin['source_licence']}",
        "path": path.as_posix(),
        "sha256": sha256_file(path),
        "target": f"target = 1 if OpenML '{pin['target_attr']}' == '{pin['positive']}' "
                  f"({pin['positive_meaning']}), else 0 ('{pin['negative']}')",
        "target_encoding": {"1": pin["positive"], "0": pin["negative"]},
        "rows": int(frame.shape[0]),
        "n_positive": n_pos,
        "n_negative": n_neg,
        "positive_share": n_pos / (n_pos + n_neg),
        "missing_cells": missing_cells,
        "rows_with_missing": rows_with_missing,
        "numeric_features": numeric,
        "categorical_features": categorical,
        "row_order": "as in the OpenML ARFF file",
    }
    profile = {"columns": columns}
    if name == "electricity":
        profile["time_checks"] = electricity_time_checks(bunch.data)
        entry["time_ordering_columns"] = ["date", "period", "day"]
        entry["time_order"] = ("file row order is chronological (944 whole days x 48 half-hours); "
                               "the normalised date column is not monotone in file order, see data/CODEBOOK.md")
    return entry, profile


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    SKL_HOME.mkdir(parents=True, exist_ok=True)
    os.environ["SCIKIT_LEARN_DATA"] = str(SKL_HOME)  # belt and braces: no ~/scikit_learn_data
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()

    entries, profiles = [], {}
    for name in PINS:
        entry, profile = fetch(name)
        entry["retrieved_on"] = today
        entry["sklearn_version"] = sklearn.__version__
        entry["pandas_version"] = pd.__version__
        entries.append(entry)
        profiles[name] = profile

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({"datasets": entries}, indent=2) + "\n", encoding="utf-8")
    PROFILE.parent.mkdir(parents=True, exist_ok=True)
    PROFILE.write_text(json.dumps(profiles, indent=2) + "\n", encoding="utf-8")

    metrics: dict = {}
    for entry in entries:
        key = entry["id"]
        metrics[f"{key}.rows"] = entry["rows"]
        metrics[f"{key}.n_positive"] = entry["n_positive"]
        metrics[f"{key}.positive_share"] = entry["positive_share"]
        metrics[f"{key}.n_numeric"] = len(entry["numeric_features"])
        metrics[f"{key}.n_categorical"] = len(entry["categorical_features"])
        metrics[f"{key}.missing_cells"] = entry["missing_cells"]
        metrics[f"{key}.sha256"] = entry["sha256"]
        metrics[f"{key}.source_md5"] = entry["source_file_md5"]
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    for entry in entries:
        print(f"{entry['id']}: {entry['rows']} rows, positive share {entry['positive_share']:.4f} "
              f"-> {entry['path']} sha256={entry['sha256']}")


if __name__ == "__main__":
    main()
