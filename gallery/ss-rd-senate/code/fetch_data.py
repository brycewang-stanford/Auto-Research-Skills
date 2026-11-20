"""Fetch the Senate RD data file used by Cattaneo, Frandsen and Titiunik (2015)
as distributed with the rdrobust package, verify its sha256 against the seed
task, and record it in data/manifest.json.

Usage (run through crew.py run --kind data-prep):
    .venv/bin/python code/fetch_data.py runs/fetch-data/metrics.json
"""
import datetime
import hashlib
import json
import os
import sys
import urllib.request

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SOURCE_URL = ("https://raw.githubusercontent.com/rdpackages/rdrobust/"
              "2589686d980af0eb2c0edd945d4a43e8bc081872/R/rdrobust_senate.csv")
EXPECTED_SHA256 = "def1fc6b8ae5af273f2140aa449c81b3ecfe1d0f325aa80ceccb0d9638a2ad44"
LICENSE_NOTE = ("No explicit licence stated for the data file. Distributed publicly "
                "in the rdrobust package repository (commit 2589686d) for replication "
                "use; the file is not committed to this repository.")
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")
MANIFEST = os.path.join(WS, "data", "manifest.json")


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    metrics_path = sys.argv[1]
    os.makedirs(os.path.dirname(RAW), exist_ok=True)
    tmp = RAW + ".part"
    with urllib.request.urlopen(SOURCE_URL, timeout=60) as r, open(tmp, "wb") as f:
        f.write(r.read())
    digest = sha256_of(tmp)
    if digest != EXPECTED_SHA256:
        os.remove(tmp)
        raise SystemExit(f"sha256 mismatch: got {digest}, expected {EXPECTED_SHA256}")
    os.replace(tmp, RAW)

    with open(RAW, "rb") as f:
        n_lines = sum(1 for _ in f) - 1  # minus header
    retrieved = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

    manifest = {"datasets": []}
    if os.path.exists(MANIFEST):
        with open(MANIFEST) as f:
            manifest = json.load(f)
    manifest["datasets"] = [d for d in manifest["datasets"] if d.get("id") != "senate-rd"]
    manifest["datasets"].append({
        "id": "senate-rd",
        "origin": SOURCE_URL,
        "license": LICENSE_NOTE,
        "path": "data/raw/rdrobust_senate.csv",
        "sha256": digest,
        "retrieved_on": retrieved,
        "rows_in_file": n_lines,
        "used_in": ["Calonico, Cattaneo, Farrell and Titiunik (2017), Sec. 7.2",
                    "Cattaneo, Frandsen and Titiunik (2015), Sec. 5"],
    })
    with open(MANIFEST, "w") as f:
        json.dump(manifest, f, indent=2)
        f.write("\n")

    with open(metrics_path, "w") as f:
        json.dump({"rows_in_file": n_lines, "sha256_matches_seed": 1,
                   "bytes": os.path.getsize(RAW)}, f, indent=2)
        f.write("\n")
    print(f"fetched {n_lines} rows, sha256 {digest}")


if __name__ == "__main__":
    main()
