"""Copy the seed extract into data/raw/ and check its SHA-256.

The extract is synthetic and ships with this repository at
crew/bench/seeds/ss-null-effect/data.csv; task.json beside it publishes its SHA-256 and
license (CC0-1.0). This script copies the file byte for byte to
data/raw/null_extract.csv, checks the hash against task.json, and writes a metrics
file. It does not parse the file, so no column (and no outcome) is read here.

The source is found by walking up from the workspace to the repository root, or from
the environment variable CREW_SEED_DIR (a directory holding data.csv and task.json).
In a clean rerun outside the repository with data/raw/ kept (--reuse-data), the
existing copy is re-verified against the recorded hash instead.

Run from the workspace root:
    .venv/bin/python -I code/fetch_data.py
"""

import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

SEED_REL = Path("crew/bench/seeds/ss-null-effect")
OUT = Path("data/raw/null_extract.csv")
METRICS = Path("data/fetch_metrics.json")
# Published in crew/bench/seeds/ss-null-effect/task.json (data.sha256).
EXPECTED_SHA256 = "f09fba8695df8d2cfe44abe770860772f07a562ad88c19789f6feab946048ca9"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def find_seed() -> Path | None:
    env = os.environ.get("CREW_SEED_DIR")
    if env and (Path(env) / "data.csv").is_file():
        return Path(env)
    for parent in [Path.cwd().resolve(), *Path.cwd().resolve().parents]:
        if (parent / SEED_REL / "data.csv").is_file():
            return parent / SEED_REL
    return None


def main() -> int:
    seed = find_seed()
    if seed is not None:
        task = json.loads((seed / "task.json").read_text())
        published = task["data"]["sha256"]
        if published != EXPECTED_SHA256:
            print(f"task.json sha256 {published} differs from the pinned {EXPECTED_SHA256}", file=sys.stderr)
            return 1
        src_hash = sha256(seed / "data.csv")
        if src_hash != EXPECTED_SHA256:
            print(f"MISMATCH: source sha256 {src_hash} != {EXPECTED_SHA256}", file=sys.stderr)
            return 1
        OUT.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(seed / "data.csv", OUT)
        source = "copied-from-seed"
    elif OUT.is_file():
        source = "existing-copy-reverified"
    else:
        print("Seed data not found: run inside the repository or set CREW_SEED_DIR", file=sys.stderr)
        return 1

    out_hash = sha256(OUT)
    if out_hash != EXPECTED_SHA256:
        print(f"MISMATCH: {OUT} sha256 {out_hash} != {EXPECTED_SHA256}", file=sys.stderr)
        return 1

    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps({
        "sha256": out_hash,
        "sha256_matches_task_json": True,
        "size_bytes": OUT.stat().st_size,
    }, indent=2) + "\n")
    print(f"{source}: {OUT} ({OUT.stat().st_size} bytes, sha256 {out_hash})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
