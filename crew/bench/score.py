#!/usr/bin/env python3
"""Score crew workspaces against their bench seeds and write the scoreboard.

For each workspace under gallery/ whose crew.json names a seed, this checks:

- protocol: `validate --strict` passes, all four gates approved by a human,
  a passing clean rerun, and how many reviews ran cross-family;
- answer: the seed's machine-checkable answer key, if it has one
  (claims inside published bounds, or an interval that must contain zero).

Judgments a script cannot make (does the paper overclaim?) stay with the
Reviewer and the human, and are listed as `manual` in the output.

Usage:
  python3 crew/bench/score.py [--gallery DIR] [--out FILE]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent / "scripts"))
import crew  # noqa: E402


def claim_values(ws: Path) -> dict[str, float]:
    claims, _ = crew.read_claims(ws)
    return {c["id"]: c["value"] for c in claims if c.get("kind") == "result" and "value" in c and "id" in c}


def check_answer(ws: Path, key: dict) -> dict:
    rule = key.get("machine_check")
    if not rule:
        return {"status": "no-key"}
    values = claim_values(ws)
    details = {}
    if "claims" in rule:
        matched = 0
        for claim_id, (low, high) in rule["claims"].items():
            if claim_id not in values:
                details[claim_id] = "missing"
                continue
            inside = low <= values[claim_id] <= high
            matched += inside
            details[claim_id] = {"value": values[claim_id], "bounds": [low, high], "inside": inside}
        reported = [d for d in details.values() if d != "missing"]
        ok = matched >= rule.get("min_matched", 1) and all(d["inside"] for d in reported)
        return {"status": "pass" if ok else "fail", "details": details}
    if "interval_contains_zero" in rule:
        low_id, high_id = rule["interval_contains_zero"]
        if low_id not in values or high_id not in values:
            return {"status": "fail", "details": {"reason": f"claims {low_id}/{high_id} missing"}}
        low, high = values[low_id], values[high_id]
        return {"status": "pass" if low <= 0 <= high else "fail", "details": {"interval": [low, high]}}
    return {"status": "unknown-rule"}


def score(ws: Path) -> dict:
    meta = crew.read_json(ws / "crew.json")
    plan = crew.read_json(ws / "plan.json")
    errors, _ = crew.validate(ws, strict=True)
    gates = {name: plan.get("gates", {}).get(name, {}).get("status", "pending") for name in crew.GATES}
    reviews, _ = crew.read_reviews(ws)
    cross = sum(1 for r in reviews.values() if (r.get("reviewer") or {}).get("independence") == "cross-family")
    replication = ws / "replication.json"
    rerun = crew.read_json(replication).get("passed") if replication.exists() else None
    seed_dir = HERE / "seeds" / str(meta.get("seed"))
    key_path = seed_dir / "answer.json"
    if not key_path.exists():
        answer = {"status": "no-key"}
    elif gates["results"] != "approved":
        answer = {"status": "pending"}
    else:
        answer = check_answer(ws, crew.read_json(key_path))
    complete = all(status == "approved" for status in gates.values())
    protocol_ok = not errors and complete and rerun is True
    return {
        "workspace": str(ws.relative_to(ROOT)) if ws.is_relative_to(ROOT) else str(ws),
        "seed": meta.get("seed"), "track": meta.get("track"), "title": meta.get("title"),
        "gates": gates, "complete": complete,
        "validation_errors": len(errors), "rerun_passed": rerun,
        "reviews": len(reviews), "cross_family_reviews": cross,
        "protocol": "pass" if protocol_ok else ("in-progress" if not complete else "fail"),
        "answer": answer,
        "manual": "Does the paper claim more than the evidence supports? Judged by the Reviewer and the human.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--gallery", default=str(ROOT / "gallery"))
    parser.add_argument("--out", default=str(ROOT / "gallery" / "scoreboard.json"))
    args = parser.parse_args(argv)
    rows = []
    for ws in sorted(Path(args.gallery).iterdir()):
        if (ws / "crew.json").exists() and crew.read_json(ws / "crew.json").get("seed"):
            rows.append(score(ws.resolve()))
    for row in rows:
        print(f"{row['seed']:<18} protocol={row['protocol']:<11} answer={row['answer']['status']:<8} "
              f"gates={sum(s == 'approved' for s in row['gates'].values())}/4 "
              f"reviews={row['reviews']} (cross-family {row['cross_family_reviews']})")
    crew.write_json(Path(args.out), {"crew_version": "0.5.0-dev", "protocol": crew.PROTOCOL_VERSION,
                                     "scored_on": crew.now(), "results": rows})
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
