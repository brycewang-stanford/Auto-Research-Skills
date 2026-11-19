"""Fetch the Card-Krueger New Jersey-Pennsylvania public data set (njmin.zip).

Downloads https://davidcard.berkeley.edu/data_sets/njmin.zip into data/raw/njmin.zip and
extracts its six files into data/raw/njmin/. No hash is published for the archive, so the
script pins the size and SHA-256 observed on the first retrieval (2026-11-19; the server
reports Last-Modified 27 Jul 2007, ETag "46aa0c0d-59e9"). A rerun therefore either gets the
same bytes or fails loudly. Extraction refuses any member name that is not a plain file
name, so a changed archive cannot write outside data/raw/njmin/.

Outputs
- data/raw/njmin.zip                 the archive as downloaded
- data/raw/njmin/{public.dat, codebook, check.sas, read.me, survey1.nj, survey2.nj}
- data/fetch_metrics.json            sizes and SHA-256 of the archive and each member

Run from the workspace root:
    .venv/bin/python -I code/fetch_data.py
"""

import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://davidcard.berkeley.edu/data_sets/njmin.zip"
ZIP_OUT = Path("data/raw/njmin.zip")
DIR_OUT = Path("data/raw/njmin")
METRICS = Path("data/fetch_metrics.json")

# Observed on the first retrieval, 2026-11-19 (no checksum is published by the host).
EXPECTED_SIZE = 23017
EXPECTED_SHA256 = "41a29aec6b489658b20030d044a2b20a5f5a04b871cde41df057afd6013ba587"
EXPECTED_MEMBERS = ["check.sas", "codebook", "public.dat", "read.me", "survey1.nj", "survey2.nj"]


def main() -> int:
    req = urllib.request.Request(URL, headers={"User-Agent": "research-crew-data-fetch"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()

    size = len(data)
    digest = hashlib.sha256(data).hexdigest()
    if size != EXPECTED_SIZE or digest != EXPECTED_SHA256:
        print(f"MISMATCH: size={size} (expected {EXPECTED_SIZE}), "
              f"sha256={digest} (expected {EXPECTED_SHA256})", file=sys.stderr)
        return 1

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = sorted(zf.namelist())
        if names != EXPECTED_MEMBERS:
            print(f"UNEXPECTED MEMBERS: {names}", file=sys.stderr)
            return 1
        members = {}
        for name in names:
            if "/" in name or "\\" in name or name.startswith("."):
                print(f"REFUSED member name {name!r}", file=sys.stderr)
                return 1
            members[name] = zf.read(name)

    ZIP_OUT.parent.mkdir(parents=True, exist_ok=True)
    ZIP_OUT.write_bytes(data)
    DIR_OUT.mkdir(parents=True, exist_ok=True)
    metrics = {"zip_size_bytes": size, "zip_sha256": digest, "zip_sha256_matches_pinned": True,
               "n_members": len(members)}
    for name, content in members.items():
        (DIR_OUT / name).write_bytes(content)
        key = name.replace(".", "_")
        metrics[f"{key}_size_bytes"] = len(content)
        metrics[f"{key}_sha256"] = hashlib.sha256(content).hexdigest()

    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"wrote {ZIP_OUT} ({size} bytes, sha256 {digest}) and {len(members)} files in {DIR_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
