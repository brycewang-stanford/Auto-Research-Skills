"""Fetch David Card's college-proximity data set (proximity.zip).

Downloads https://davidcard.berkeley.edu/data_sets/proximity.zip into data/raw/proximity.zip
and extracts four of its five members into data/raw/proximity/: nls.dat (the data),
code_bk.txt (codebook), read1.sas (Card's example SAS program) and readme. The fifth
member, read1.lst (the SAS output listing of read1.sas, which contains regression output),
is deliberately left inside the archive and not extracted: data preparation must not see
any estimate that relates the instrument to education or wages.

No checksum is published by the host. The script pins the SHA-256 the Scout observed on
2026-11-20 (sources/notes.md sec. 2) and the member list, so a rerun either gets the same
bytes or fails loudly. Extraction refuses any member name that is not a plain file name.

Outputs
- data/raw/proximity.zip
- data/raw/proximity/{nls.dat, code_bk.txt, read1.sas, readme}
- data/fetch_metrics.json   sizes and SHA-256 of the archive and of each extracted member

Run from the workspace root:  python3 code/fetch_data.py   (standard library only)
"""

import hashlib
import io
import json
import sys
import urllib.request
import zipfile
from pathlib import Path

URL = "https://davidcard.berkeley.edu/data_sets/proximity.zip"
ZIP_OUT = Path("data/raw/proximity.zip")
DIR_OUT = Path("data/raw/proximity")
METRICS = Path("data/fetch_metrics.json")

# Observed by the Scout on 2026-11-20 (no checksum is published by the host).
EXPECTED_SHA256 = "0e9b2ad4182ea631ca3dd8a5fff6c1b0ab86b56c6a3fa868870f716e8d82691f"
EXPECTED_MEMBERS = ["code_bk.txt", "nls.dat", "read1.lst", "read1.sas", "readme"]
EXTRACT = ["code_bk.txt", "nls.dat", "read1.sas", "readme"]  # read1.lst stays in the zip


def main() -> int:
    req = urllib.request.Request(URL, headers={"User-Agent": "research-crew-data-fetch"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = resp.read()

    size = len(data)
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        print(f"MISMATCH: size={size}, sha256={digest} (expected {EXPECTED_SHA256})",
              file=sys.stderr)
        return 1

    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        names = sorted(zf.namelist())
        if names != EXPECTED_MEMBERS:
            print(f"UNEXPECTED MEMBERS: {names}", file=sys.stderr)
            return 1
        members = {}
        for name in EXTRACT:
            if "/" in name or "\\" in name or name.startswith("."):
                print(f"REFUSED member name {name!r}", file=sys.stderr)
                return 1
            members[name] = zf.read(name)
        lst_info = zf.getinfo("read1.lst")

    ZIP_OUT.parent.mkdir(parents=True, exist_ok=True)
    ZIP_OUT.write_bytes(data)
    DIR_OUT.mkdir(parents=True, exist_ok=True)
    metrics = {"zip_size_bytes": size, "zip_sha256": digest, "zip_sha256_matches_pinned": True,
               "n_members_in_zip": len(names), "n_members_extracted": len(members),
               "read1_lst_extracted": False, "read1_lst_size_bytes": lst_info.file_size}
    for name, content in members.items():
        (DIR_OUT / name).write_bytes(content)
        key = name.replace(".", "_")
        metrics[f"{key}_size_bytes"] = len(content)
        metrics[f"{key}_sha256"] = hashlib.sha256(content).hexdigest()
    metrics["nls_dat_lines"] = members["nls.dat"].count(b"\n")

    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"wrote {ZIP_OUT} ({size} bytes, sha256 {digest}) and {len(members)} files in {DIR_OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
