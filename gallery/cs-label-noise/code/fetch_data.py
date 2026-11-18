"""Fetch the four study datasets through scikit-learn and record their provenance.

Run from the workspace root, only through the crew tool:

    python3 crew.py run <ws> --id fetch-data --role data-ra --kind data-prep \
        --code code/fetch_data.py ... -- .venv/bin/python code/fetch_data.py

Writes
  data/raw/<name>.csv          features + a final `target` column, one row per instance
  data/raw/sklearn_home/       scikit-learn's download cache (never ~/scikit_learn_data)
  data/manifest.json           origin, licence, path, sha256, retrieval date per dataset
  runs/fetch-data/metrics.json flat metrics (rows, columns, sha256 per dataset)

Pinning
  breast_cancer  bundled with scikit-learn 1.9.1 (no download)
  credit-g       OpenML data_id 31,   version 1 (ARFF file_id 31)
  adult          OpenML data_id 1590, version 2 (ARFF file_id 1595261)
  covtype        scikit-learn fetch_covtype archive (figshare file 5976039)

scikit-learn checks the md5 published by OpenML for each ARFF file and the sha256 of the
covtype archive before using them; this script also asserts the OpenML data_id, version
and md5 it received against the pinned values below, so a silent re-upload fails loudly.

Nothing here looks at the relationship between features and labels.
"""

from __future__ import annotations

import datetime as dt
import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd
import sklearn
from sklearn import datasets

RAW = Path("data/raw")
SKL_HOME = RAW / "sklearn_home"
MANIFEST = Path("data/manifest.json")
METRICS = Path("runs/fetch-data/metrics.json")

UCI_LICENCE = "CC BY 4.0 (Creative Commons Attribution 4.0 International), as stated on the UCI ML Repository page"

OPENML = {
    "credit-g": {
        "data_id": 31,
        "version": 1,
        "file_id": 31,
        "md5": "9a475053fed0c26ee95cd4525e50074c",
        "uci_page": "https://archive.ics.uci.edu/dataset/144/statlog+german+credit+data",
    },
    "adult": {
        "data_id": 1590,
        "version": 2,
        "file_id": 1595261,
        "md5": "bb6510925e5d4b23d136715febb2cdf5",
        "uci_page": "https://archive.ics.uci.edu/dataset/2/adult",
    },
}

COVTYPE_ARCHIVE = {
    "url": "https://ndownloader.figshare.com/files/5976039",
    "sha256": "614360d0257557dd1792834a85a1cdebfadc3c4f30b011d56afee7ffb5b15771",
    "uci_page": "https://archive.ics.uci.edu/dataset/31/covertype",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(frame: pd.DataFrame, name: str) -> Path:
    path = RAW / f"{name}.csv"
    frame.to_csv(path, index=False, lineterminator="\n")
    return path


def feature_types(frame: pd.DataFrame) -> tuple[list[str], list[str]]:
    features = [c for c in frame.columns if c != "target"]
    categorical = [c for c in features if isinstance(frame[c].dtype, pd.CategoricalDtype) or frame[c].dtype == object]
    numeric = [c for c in features if c not in categorical]
    return numeric, categorical


def fetch_breast_cancer() -> dict:
    bunch = datasets.load_breast_cancer(as_frame=True)
    frame = bunch.frame.copy()
    assert list(frame.columns)[-1] == "target"
    path = write_csv(frame, "breast_cancer")
    bundled = Path(datasets.__file__).parent / "data" / "breast_cancer.csv"
    numeric, categorical = feature_types(frame)
    return {
        "id": "breast_cancer",
        "origin": f"sklearn.datasets.load_breast_cancer (bundled with scikit-learn {sklearn.__version__}; "
                  "Breast Cancer Wisconsin (Diagnostic), UCI ML Repository id 17)",
        "loader": "sklearn.datasets.load_breast_cancer(as_frame=True)",
        "source_page": "https://archive.ics.uci.edu/dataset/17/breast+cancer+wisconsin+diagnostic",
        "version": f"bundled with scikit-learn {sklearn.__version__}",
        "source_file": f"sklearn/datasets/data/breast_cancer.csv",
        "source_file_sha256": sha256(bundled),
        "license": UCI_LICENCE + "; scikit-learn redistributes it under its BSD-3-Clause package licence",
        "path": str(path),
        "sha256": sha256(path),
        "target": "target (0 = malignant, 1 = benign; scikit-learn coding)",
        "target_names": {"0": str(bunch.target_names[0]), "1": str(bunch.target_names[1])},
        "rows": int(frame.shape[0]),
        "numeric_features": numeric,
        "categorical_features": categorical,
    }


def fetch_openml_dataset(name: str) -> dict:
    pin = OPENML[name]
    bunch = datasets.fetch_openml(data_id=pin["data_id"], data_home=str(SKL_HOME), as_frame=True,
                                  parser="pandas")
    details = bunch.details
    got = {"data_id": int(details["id"]), "version": int(details["version"]),
           "file_id": int(details["file_id"]), "md5": details["md5_checksum"]}
    want = {k: pin[k] for k in got}
    if got != want:
        sys.exit(f"ERROR: OpenML {name} metadata {got} does not match the pin {want}")
    if details["name"] != name:
        sys.exit(f"ERROR: OpenML data_id {pin['data_id']} is named {details['name']!r}, expected {name!r}")
    frame = bunch.data.copy()
    frame["target"] = bunch.target
    path = write_csv(frame, name)
    # the ARFF scikit-learn downloaded: check OpenML's md5 ourselves, and record the sha256
    # of the decompressed ARFF (the gzip wrapper of the cache is not byte-stable)
    cached = sorted((SKL_HOME / "openml" / "openml.org" / "data" / "v1" / "download"
                     / str(pin["file_id"])).glob("*.arff.gz"))
    if len(cached) != 1:
        sys.exit(f"ERROR: expected one cached ARFF for OpenML file_id {pin['file_id']}, found {cached}")
    arff = gzip.decompress(cached[0].read_bytes())
    if hashlib.md5(arff).hexdigest() != pin["md5"]:
        sys.exit(f"ERROR: md5 of the {name} ARFF does not match OpenML's published md5_checksum")
    numeric, categorical = feature_types(frame)
    return {
        "id": name,
        "origin": f"https://www.openml.org/d/{pin['data_id']} (OpenML data_id {pin['data_id']}, "
                  f"version {pin['version']}, ARFF {details['url']}), via sklearn.datasets.fetch_openml",
        "loader": f"sklearn.datasets.fetch_openml(data_id={pin['data_id']}, as_frame=True, parser='pandas')",
        "openml": {
            "data_id": pin["data_id"],
            "version": pin["version"],
            "file_id": pin["file_id"],
            "md5_checksum": pin["md5"],
            "upload_date": details.get("upload_date"),
            "status": details.get("status"),
            "default_target_attribute": details.get("default_target_attribute"),
            "licence": details.get("licence"),
            "original_data_url": details.get("original_data_url"),
        },
        "source_page": pin["uci_page"],
        "version": f"OpenML version {pin['version']}",
        "source_file": f"{details['url']} (cached as {cached[0].as_posix()}; md5 checked against OpenML)",
        "source_file_sha256": hashlib.sha256(arff).hexdigest(),
        "license": f"OpenML licence field: {details.get('licence')!r}; original source: {UCI_LICENCE}",
        "path": str(path),
        "sha256": sha256(path),
        "target": f"target (OpenML default target attribute {details.get('default_target_attribute')!r})",
        "rows": int(frame.shape[0]),
        "numeric_features": numeric,
        "categorical_features": categorical,
    }


def fetch_covtype() -> dict:
    bunch = datasets.fetch_covtype(data_home=str(SKL_HOME), as_frame=True)
    frame = bunch.data.copy()
    # every covtype column is an integer in the source (sklearn returns float64); write integers
    if not (frame.round() == frame).all().all():
        sys.exit("ERROR: covtype has non-integer feature values")
    frame = frame.astype("int64")
    frame["target"] = bunch.target.astype("int64")
    path = write_csv(frame, "covtype")
    numeric, categorical = feature_types(frame)
    return {
        "id": "covtype",
        "origin": f"{COVTYPE_ARCHIVE['url']} (covtype.data.gz, the UCI Covertype data as mirrored by "
                  "scikit-learn), via sklearn.datasets.fetch_covtype",
        "loader": "sklearn.datasets.fetch_covtype(as_frame=True)",
        "source_page": COVTYPE_ARCHIVE["uci_page"],
        "version": f"archive pinned by scikit-learn {sklearn.__version__} (sha256 checked on download)",
        "source_file": "covtype.data.gz (sha256 checked by scikit-learn on download, then deleted after "
                       "conversion to its cache; the published sha256 is recorded here)",
        "source_file_sha256": COVTYPE_ARCHIVE["sha256"],
        "license": UCI_LICENCE,
        "path": str(path),
        "sha256": sha256(path),
        "target": "target (Cover_Type, integer codes 1-7)",
        "rows": int(frame.shape[0]),
        "numeric_features": numeric,
        "categorical_features": categorical,
    }


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    SKL_HOME.mkdir(parents=True, exist_ok=True)
    os.environ["SCIKIT_LEARN_DATA"] = str(SKL_HOME)  # belt and braces: no ~/scikit_learn_data
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()

    entries = [fetch_breast_cancer(), fetch_openml_dataset("credit-g"),
               fetch_openml_dataset("adult"), fetch_covtype()]
    for entry in entries:
        entry["retrieved_on"] = today
        entry["sklearn_version"] = sklearn.__version__
        entry["pandas_version"] = pd.__version__

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps({"datasets": entries}, indent=2) + "\n", encoding="utf-8")

    metrics: dict = {}
    for entry in entries:
        key = entry["id"]
        metrics[f"{key}.rows"] = entry["rows"]
        metrics[f"{key}.n_numeric"] = len(entry["numeric_features"])
        metrics[f"{key}.n_categorical"] = len(entry["categorical_features"])
        metrics[f"{key}.sha256"] = entry["sha256"]
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    for entry in entries:
        print(f"{entry['id']}: {entry['rows']} rows -> {entry['path']} sha256={entry['sha256']}")


if __name__ == "__main__":
    main()
