"""Fetch the two U.S. Census Bureau Population Estimates Program files into data/raw/census/.

Design (plan.json design.data, source 2; analysis_plan step 0c, task dr-pop):
  2013-2019 July 1 resident population by state: 2010-2020 intercensal file
      https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/intercensal/state/asrh/sc-est2020int-alldata6.csv
      layout: https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2010-2020/intercensal/state/SC-EST2020INT-ALLDATA6.pdf
  2020-2025 July 1 resident population by state: Vintage 2025
      https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/state/totals/NST-EST2025-ALLDATA.csv
      layout: https://www2.census.gov/programs-surveys/popest/technical-documentation/file-layouts/2020-2025/NST-EST2025-ALLDATA.pdf

The Census Bureau publishes no checksum. The sha256 of each file is written to the metrics
(so a clean rerun that fetches different bytes fails the metric comparison) and, if
data/manifest.json already lists the file, compared with the recorded hash.

This script only downloads and checks the file structure (header fields, row counts,
summary-level codes). Summing the intercensal file over RACE and AGE and splicing the two
files is done in code/prepare_state.py. No statistic of any outcome is computed.

Writes: data/raw/census/sc-est2020int-alldata6.csv, data/raw/census/NST-EST2025-ALLDATA.csv,
data/fetch_pop_metrics.json.
"""
import csv
import hashlib
import io
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (compatible; research-data-fetch/1.0)"  # generic, no personal details
RAW = Path("data/raw/census")
FILES = {
    "intercensal": {
        "url": "https://www2.census.gov/programs-surveys/popest/datasets/2010-2020/intercensal/state/asrh/sc-est2020int-alldata6.csv",
        "name": "sc-est2020int-alldata6.csv",
        # documented field order (layout PDF, release September 2025)
        "fields": ["SUMLEV", "REGION", "DIVISION", "STATE", "NAME", "SEX", "ORIGIN", "RACE", "AGE",
                   "ESTIMATESBASE2010"] + [f"POPESTIMATE{y}" for y in range(2010, 2020)] + ["CENSUS2020POP"],
    },
    "v2025": {
        "url": "https://www2.census.gov/programs-surveys/popest/datasets/2020-2025/state/totals/NST-EST2025-ALLDATA.csv",
        "name": "NST-EST2025-ALLDATA.csv",
        # leading documented fields (layout PDF, release January 2026); later fields are components of change
        "fields": ["SUMLEV", "REGION", "DIVISION", "STATE", "NAME", "ESTIMATESBASE2020"]
                  + [f"POPESTIMATE{y}" for y in range(2020, 2026)],
    },
}
STATES_51 = {f"{c:02d}" for c in [1, 2, 4, 5, 6, 8, 9, 10, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21,
                                    22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36, 37,
                                    38, 39, 40, 41, 42, 44, 45, 46, 47, 48, 49, 50, 51, 53, 54, 55, 56]}


def get(url, tries=5):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    err = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                return resp.read(), dict(resp.headers)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404):
                raise SystemExit(f"ERROR: {url} returned HTTP {exc.code}")
            err = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            err = exc
        time.sleep(3 * (attempt + 1))
    raise SystemExit(f"ERROR: failed to fetch {url}: {err}")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    recorded = {}
    mpath = Path("data/manifest.json")
    if mpath.exists():
        for d in json.loads(mpath.read_text()).get("datasets", []):
            recorded[d.get("path")] = d.get("sha256")

    metrics = {}
    for key, spec in FILES.items():
        body, headers = get(spec["url"])
        path = RAW / spec["name"]
        path.write_bytes(body)
        digest = hashlib.sha256(body).hexdigest()
        rel = path.as_posix()
        if rel in recorded and recorded[rel] != digest:
            print(f"WARNING: {rel} differs from the manifest sha256 (a revised file?)")
        text = body.decode("latin-1")
        rows = list(csv.reader(io.StringIO(text)))
        header, data = rows[0], rows[1:]
        n_fields = len(spec["fields"])
        header_ok = header[:n_fields] == spec["fields"]
        if key == "intercensal":
            header_ok = header_ok and len(header) == n_fields
        if not header_ok:
            raise SystemExit(f"ERROR: {rel} header does not match the documented layout: {header[:n_fields + 2]}")
        idx = {name: i for i, name in enumerate(header)}
        sumlev = [r[idx["SUMLEV"]] for r in data]
        states = {r[idx["STATE"]] for r in data if r[idx["SUMLEV"]] == "040"}
        metrics[f"{key}_sha256"] = digest
        metrics[f"{key}_bytes"] = len(body)
        metrics[f"{key}_rows"] = len(data)
        metrics[f"{key}_columns"] = len(header)
        metrics[f"{key}_header_matches_layout"] = int(header_ok)
        metrics[f"{key}_rows_sumlev040"] = sum(1 for s in sumlev if s == "040")
        metrics[f"{key}_states_sumlev040"] = len(states)
        metrics[f"{key}_has_all_51"] = int(STATES_51 <= states)
        metrics[f"{key}_extra_state_codes"] = ",".join(sorted(states - STATES_51)) or "none"
        if key == "intercensal":
            for col in ["SEX", "ORIGIN", "RACE", "AGE"]:
                metrics[f"{key}_distinct_{col}"] = len({r[idx[col]] for r in data})
            metrics[f"{key}_rows_sex0_origin0"] = sum(1 for r in data if r[idx["SEX"]] == "0" and r[idx["ORIGIN"]] == "0")
        print(f"{rel}: {len(body)} bytes, {len(data)} rows, sha256 {digest}, "
              f"Last-Modified {headers.get('Last-Modified') or headers.get('last-modified')}")

    Path("data/fetch_pop_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
