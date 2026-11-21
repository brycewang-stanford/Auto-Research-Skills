"""Fetch BLS QCEW quarterly industry slices (CSV) into data/raw/qcew/.

Source: BLS QCEW Open Data Access, "Data Slices by Industry"
  https://data.bls.gov/cew/doc/access/csv_data_slices.htm
  URL pattern https://data.bls.gov/cew/data/api/<year>/<qtr>/industry/<code>.csv

Industries: 722513 (limited-service restaurants), 722511 (full-service restaurants),
7225 (restaurants and other eating places), 10 (total, all industries).
Quarters: 2014Q1 through END (2026Q1, the latest quarter published on 2026-11-21).
The quarter after END is probed (HTTP status recorded in data/fetch_index.json) so a
later rerun shows whether a newer quarter has appeared; it is not downloaded.

No checksum is published by BLS. If data/manifest.json already lists a file, the fetched
bytes are compared with the recorded sha256 and mismatches are counted (BLS revises
recent quarters, so a mismatch means a revised vintage, not a broken download).

Writes: data/raw/qcew/<year>q<qtr>_<code>.csv, data/fetch_index.json,
data/fetch_metrics.json.
"""
import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

INDUSTRIES = ["722513", "722511", "7225", "10"]
START = (2014, 1)
END = (2026, 1)
URL = "https://data.bls.gov/cew/data/api/{y}/{q}/industry/{code}.csv"
UA = "Mozilla/5.0 (compatible; research-data-fetch/1.0)"  # generic, no personal details
RAW = Path("data/raw/qcew")
EXPECTED_HEADER_START = '"area_fips","own_code","industry_code","agglvl_code","size_code","year","qtr","disclosure_code"'


def quarters(start, end):
    y, q = start
    while (y, q) <= end:
        yield y, q
        y, q = (y, q + 1) if q < 4 else (y + 1, 1)


def get(url, method="GET", tries=5):
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA})
    for attempt in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                return resp.status, (resp.read() if method == "GET" else b""), dict(resp.headers)
        except urllib.error.HTTPError as exc:
            if exc.code in (403, 404):
                return exc.code, b"", dict(exc.headers or {})
            err = exc
        except (urllib.error.URLError, TimeoutError, ConnectionError) as exc:
            err = exc
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"failed to fetch {url}: {err}")


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    manifest = {}
    mpath = Path("data/manifest.json")
    if mpath.exists():
        for d in json.loads(mpath.read_text()).get("datasets", []):
            manifest[d.get("path")] = d.get("sha256")

    files, total_bytes, pinned, pinned_match = [], 0, 0, 0
    for y, q in quarters(START, END):
        for code in INDUSTRIES:
            url = URL.format(y=y, q=q, code=code)
            status, body, headers = get(url)
            if status != 200:
                raise SystemExit(f"ERROR: {url} returned HTTP {status}")
            text_head = body[:200].decode("utf-8", errors="replace")
            if not text_head.startswith(EXPECTED_HEADER_START):
                raise SystemExit(f"ERROR: {url} does not start with the documented CSV header")
            path = RAW / f"{y}q{q}_{code}.csv"
            path.write_bytes(body)
            digest = hashlib.sha256(body).hexdigest()
            total_bytes += len(body)
            rel = path.as_posix()
            if rel in manifest:
                pinned += 1
                if manifest[rel] == digest:
                    pinned_match += 1
                else:
                    print(f"WARNING: {rel} differs from the manifest sha256 (revised vintage?)")
            files.append({"path": rel, "url": url, "industry": code, "year": y, "qtr": q,
                          "sha256": digest, "size_bytes": len(body),
                          "rows": body.count(b"\n") - 1,
                          "last_modified": headers.get("Last-Modified") or headers.get("last-modified"),
                          "etag": headers.get("ETag") or headers.get("etag")})
            print(f"{rel} {len(body)} bytes")
            time.sleep(0.3)

    ny, nq = (END[0], END[1] + 1) if END[1] < 4 else (END[0] + 1, 1)
    probe = {}
    for code in INDUSTRIES:
        url = URL.format(y=ny, q=nq, code=code)
        status, _, _ = get(url, method="HEAD")
        probe[code] = status
    index = {"retrieved_on": time.strftime("%Y-%m-%d", time.gmtime()),
             "user_agent": UA, "start": f"{START[0]}Q{START[1]}", "end": f"{END[0]}Q{END[1]}",
             "next_quarter_probe": {"quarter": f"{ny}Q{nq}", "http_status": probe},
             "files": files}
    Path("data/fetch_index.json").write_text(json.dumps(index, indent=2) + "\n")
    metrics = {"n_files": len(files), "n_industries": len(INDUSTRIES),
               "n_quarters": len(files) // len(INDUSTRIES),
               "first_quarter": index["start"], "last_quarter": index["end"],
               "total_bytes": total_bytes, "total_rows": sum(f["rows"] for f in files),
               "n_files_pinned_in_manifest": pinned, "n_files_matching_manifest": pinned_match}
    Path("data/fetch_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics))
    print("next quarter probe:", json.dumps(index["next_quarter_probe"]))


if __name__ == "__main__":
    main()
