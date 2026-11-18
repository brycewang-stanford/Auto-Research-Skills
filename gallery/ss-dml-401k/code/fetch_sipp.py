"""Fetch the 1991 SIPP 401(k) extract used by Chernozhukov et al. (2018).

Downloads sipp1991.dta from the authors' replication repository into
data/raw/sipp1991.dta and checks it against what GitHub publishes for the file:
its size (260,726 bytes) and its git blob SHA-1 (735c4ba2...). GitHub publishes no
SHA-256, so the SHA-256 is computed here, written to the metrics file and recorded
in data/manifest.json. The file has not changed since the repository's initial
commit (a8ef8ef, 2017-06-01), so a rerun fetches the same bytes.

Run from the workspace root:
    .venv/bin/python -I code/fetch_sipp.py
"""

import hashlib
import json
import sys
import urllib.request
from pathlib import Path

URL = "https://github.com/VC2015/DMLonGitHub/raw/master/sipp1991.dta"
OUT = Path("data/raw/sipp1991.dta")
METRICS = Path("data/fetch_metrics.json")

# Published by GitHub (contents API, repos/VC2015/DMLonGitHub/contents/sipp1991.dta).
EXPECTED_SIZE = 260726
EXPECTED_GIT_BLOB_SHA1 = "735c4ba26cffbc3e6a7b9ca51874c599efc9f27c"


def git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def main() -> int:
    req = urllib.request.Request(URL, headers={"User-Agent": "research-crew-data-fetch"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()

    size = len(data)
    blob = git_blob_sha1(data)
    sha256 = hashlib.sha256(data).hexdigest()

    if size != EXPECTED_SIZE or blob != EXPECTED_GIT_BLOB_SHA1:
        print(f"MISMATCH: size={size} (expected {EXPECTED_SIZE}), "
              f"git blob sha1={blob} (expected {EXPECTED_GIT_BLOB_SHA1})", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(data)

    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps({
        "size_bytes": size,
        "sha256": sha256,
        "git_blob_sha1": blob,
        "git_blob_sha1_matches_github": True,
        "size_matches_github": True,
    }, indent=2) + "\n")
    print(f"wrote {OUT} ({size} bytes, sha256 {sha256})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
