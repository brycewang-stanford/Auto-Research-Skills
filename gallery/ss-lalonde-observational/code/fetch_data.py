"""Fetch the Dehejia-Wahba NSW-treated file and the CPS-1 comparison file.

Downloads, from Rajeev Dehejia's data page (https://users.nber.org/~rdehejia/data/),
exactly two files into data/raw/:

    nswre74_treated.txt   185 NSW-treated men, Dehejia-Wahba (RE74) subsample
    cps_controls.txt      15,992 CPS-SSA-1 comparison men (LaLonde's CPS-1)

The experimental control file (nswre74_control.txt) is deliberately NOT fetched: the
crew may not re-benchmark against the experimental controls.

The page publishes no checksum, so the SHA-256 of each file is computed here, written
to the metrics file and recorded in data/manifest.json. The structural checks below
count lines and whitespace-separated fields only; no field value is parsed except the
first (the treatment indicator), so the 1978 earnings column (field 10) is copied
byte for byte and never read.

Run from the workspace root:
    .venv/bin/python -I code/fetch_data.py
"""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

BASE = "https://users.nber.org/~rdehejia/data/"
RAW_DIR = Path("data/raw")
METRICS = Path("data/fetch_metrics.json")

# Row counts and column count as stated on the data page (.nswdata2.html).
FILES = {
    "nswre74_treated": {"name": "nswre74_treated.txt", "rows": 185, "treat": "1"},
    "cps_controls": {"name": "cps_controls.txt", "rows": 15992, "treat": "0"},
}
EXPECTED_FIELDS = 10  # treat, age, educ, black, hisp, married, nodegree, RE74, RE75, RE78


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "research-crew-data-fetch"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return resp.read()


def structure(data: bytes) -> dict:
    """Count non-blank lines and fields per line; read only field 1 (treat)."""
    lines = [ln for ln in data.decode("ascii").splitlines() if ln.strip()]
    field_counts = {len(ln.split()) for ln in lines}
    treat_values = sorted({ln.split()[0] for ln in lines})
    return {"rows": len(lines), "field_counts": sorted(field_counts), "treat_tokens": treat_values}


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    metrics: dict = {}
    ok = True
    for key, spec in FILES.items():
        url = BASE + spec["name"]
        data = fetch(url)
        info = structure(data)
        rows_ok = info["rows"] == spec["rows"]
        fields_ok = info["field_counts"] == [EXPECTED_FIELDS]
        # the treatment token may be written as e.g. "1" or "1.00"; compare numerically
        treat_ok = all(float(t) == float(spec["treat"]) for t in info["treat_tokens"])
        (RAW_DIR / spec["name"]).write_bytes(data)
        metrics[f"{key}_size_bytes"] = len(data)
        metrics[f"{key}_sha256"] = hashlib.sha256(data).hexdigest()
        metrics[f"{key}_rows"] = info["rows"]
        metrics[f"{key}_rows_expected"] = spec["rows"]
        metrics[f"{key}_rows_match"] = rows_ok
        metrics[f"{key}_fields_per_row"] = ",".join(str(c) for c in info["field_counts"])
        metrics[f"{key}_fields_match"] = fields_ok
        metrics[f"{key}_treat_tokens"] = ",".join(info["treat_tokens"])
        metrics[f"{key}_treat_match"] = treat_ok
        ok = ok and rows_ok and fields_ok and treat_ok
        print(f"wrote {RAW_DIR / spec['name']}: {info['rows']} rows, "
              f"fields {info['field_counts']}, sha256 {metrics[f'{key}_sha256']}")
    metrics["experimental_controls_fetched"] = False
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n")
    if not ok:
        print("MISMATCH against the data page: see data/fetch_metrics.json", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
