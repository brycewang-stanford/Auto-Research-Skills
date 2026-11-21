"""Fetch the California Proposition 99 panel shipped with the synthdid R package.

Design (plan.json design.data, source 3; analysis_plan step 0d, task dr-prop99): used only by
check-methods (code checks against Arkhangelsky et al. 2021, Table 1), never in a study run.

Source: github.com/synth-inference/synthdid, data/california_prop99.csv, pinned to commit
70c1ce3eac58e28c30b67435ca377bb48baa9b8a (repository HEAD on 2026-11-21; the file was last
changed in commit eaf905d96bdcd26d7b7386a8afa5f31488ffbfd0, 2021-03-13). The package's
data/README.md says the data are from Abadie, Diamond and Hainmueller (2010), converted from
their MATLAB file to a ';'-delimited long panel. Package license (DESCRIPTION):
"GPL (>= 2) | BSD_3_clause + file LICENSE".

Published hash: GitHub publishes the git blob SHA-1 of the file at the pinned commit
(contents API: 4ff21c81016d1feaa117d3b863eb8c44cd9b2c07, 32,687 bytes). The script recomputes
the git blob hash of the downloaded bytes and stops if it differs.

Checks are structural only (row and unit counts, the year range, the treatment indicator);
no statistic of PacksPerCapita is computed.

Writes: data/raw/synthdid/california_prop99.csv, data/fetch_prop99_metrics.json.
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
COMMIT = "70c1ce3eac58e28c30b67435ca377bb48baa9b8a"
URL = f"https://raw.githubusercontent.com/synth-inference/synthdid/{COMMIT}/data/california_prop99.csv"
GIT_BLOB_SHA1 = "4ff21c81016d1feaa117d3b863eb8c44cd9b2c07"
OUT = Path("data/raw/synthdid/california_prop99.csv")


def get(url, tries=5):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    err = None
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.read()
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404):
                raise SystemExit(f"ERROR: {url} returned HTTP {exc.code}")
            err = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            err = exc
        time.sleep(2 * (attempt + 1))
    raise SystemExit(f"ERROR: failed to fetch {url}: {err}")


def main():
    body = get(URL)
    blob = hashlib.sha1(b"blob %d\0" % len(body) + body).hexdigest()
    if blob != GIT_BLOB_SHA1:
        raise SystemExit(f"ERROR: git blob sha1 {blob} != published {GIT_BLOB_SHA1}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(body)

    rows = list(csv.reader(io.StringIO(body.decode("utf-8")), delimiter=";"))
    header, data = rows[0], rows[1:]
    if header != ["State", "Year", "PacksPerCapita", "treated"]:
        raise SystemExit(f"ERROR: unexpected header {header}")
    states = {r[0] for r in data}
    years = sorted({int(r[1]) for r in data})
    keys = {(r[0], r[1]) for r in data}
    treated_rows = [(r[0], int(r[1])) for r in data if r[3] == "1"]
    treated_states = {s for s, _ in treated_rows}
    expected_treated = {("California", y) for y in range(1989, 2001)}
    metrics = {
        "sha256": hashlib.sha256(body).hexdigest(),
        "git_blob_sha1_matches": int(blob == GIT_BLOB_SHA1),
        "bytes": len(body),
        "rows": len(data),
        "n_states": len(states),
        "n_years": len(years),
        "first_year": years[0],
        "last_year": years[-1],
        "balanced": int(len(keys) == len(data) == len(states) * len(years)),
        "missing_packs": sum(1 for r in data if r[2].strip() in ("", "NA")),
        "treated_values_0_1_only": int({r[3] for r in data} <= {"0", "1"}),
        "treated_rows": len(treated_rows),
        "treated_states": ",".join(sorted(treated_states)),
        "treated_is_california_1989_2000": int(set(treated_rows) == expected_treated),
    }
    Path("data/fetch_prop99_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
