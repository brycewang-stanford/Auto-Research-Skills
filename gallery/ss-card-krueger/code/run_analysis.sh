#!/usr/bin/env bash
# Planned analysis runs 1-8 (plan.json analysis_plan), in order, through crew.py run.
#
# Guard (code-r1 F1). The script refuses to start unless all of these hold:
#   - the latest reviews/code-r*/review.json has no open critical or major finding;
#   - code/ck_analysis.py, code/verdict.py and code/test_ck.py hash to the values below;
#   - runs/check-synthetic/run.json exited 0, recorded those same hashes, and its
#     metrics report tests_failed = 0.
# ck_analysis.py and verdict.py are pinned to the hashes recorded in code-r1. test_ck.py
# is pinned to the version after the code-r1 F3 edit, which added only value tests. Its
# code-r1 hash was 9d06557561f490ec2a723faf661215248f60788ef14ab13566d54d4d5c770166.
# The design gate is checked by crew.py itself.
#
# No replacement (code-r1 F2). Analysis runs are never replaced. This script has no
# --replace path, and crew.py refuses a run id that already exists. Rerunning an analysis
# run needs a deviation the PI has approved and recorded in runs/NOTES.md, and then a
# manual crew.py command (crew.py archives the replaced record under runs/.superseded/).
#
# Usage, from anywhere:
#   bash gallery/ss-card-krueger/code/run_analysis.sh            # all eight runs, in order
#   bash gallery/ss-card-krueger/code/run_analysis.sh main-t3    # named runs only
set -euo pipefail

WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CREW="$(cd "$WS/../.." && pwd)/crew/scripts/crew.py"
PY=".venv/bin/python"            # resolved by crew.py relative to the workspace
DATA="data/derived/stores.csv"

python3 - "$WS" <<'EOF'
import hashlib, json, re, sys
from pathlib import Path
ws = Path(sys.argv[1])
EXPECTED = {
    "code/ck_analysis.py": "632d22031ff807d4cac23bbe985ac5023de6ec872641087391b233b3b8b9ff9a",
    "code/verdict.py": "65599671fb46d8580abfaa4ed43850f4d8a4ec70c188130da05a2d66f89d53bd",
    "code/test_ck.py": "f53561d8e61e7e3edd39b97ae3abbb73ad7379144266976827d4516a5c879729",
}
rounds = sorted((int(m.group(1)), p) for p in (ws / "reviews").glob("code-r*/review.json")
                if (m := re.search(r"code-r(\d+)", str(p))))
if not rounds:
    sys.exit("REFUSED: no code review (reviews/code-r*/review.json) yet; analysis_plan 0d")
review = json.loads(rounds[-1][1].read_text())
blocking = [f["id"] for f in review.get("findings", [])
            if f.get("status") == "open" and f.get("severity") in ("critical", "major")]
if blocking:
    sys.exit(f"REFUSED: {rounds[-1][1].parent.name} has open critical/major findings {blocking}")
for path, want in EXPECTED.items():
    got = hashlib.sha256((ws / path).read_bytes()).hexdigest()
    if got != want:
        sys.exit(f"REFUSED: {path} sha256 {got} is not the reviewed {want}")
rec = json.loads((ws / "runs/check-synthetic/run.json").read_text())
recorded = {c["path"]: c["sha256"] for c in rec.get("code", [])}
if rec.get("exit_code") != 0 or rec.get("metrics", {}).get("tests_failed") != 0:
    sys.exit("REFUSED: check-synthetic did not pass")
if any(recorded.get(p) != h for p, h in EXPECTED.items()):
    sys.exit("REFUSED: check-synthetic was not run on the pinned code; rerun it first")
print(f"guard ok: {rounds[-1][1].parent.name} verdict {review.get('verdict')}, "
      "code hashes pinned, check-synthetic passed on that code")
EOF

run() {  # run <id> [crew.py args...] -- <command...>
  local id="$1"; shift
  python3 "$CREW" run "$WS" --id "$id" --role econometrician --kind analysis "$@"
}

analysis() {  # analysis <id> [--output file]...
  local id="$1"; shift
  run "$id" --code code/ck_analysis.py --input "$DATA" "$@" \
    --metrics "runs/$id/metrics.json" -- "$PY" -I code/ck_analysis.py "$id"
}

step() {
  case "$1" in
    main-t3|main-t4|se-alt|placebo-hiwage|h2-closures-excl|h2-nw-rule) analysis "$1" ;;
    h2-winsor) analysis h2-winsor --output runs/h2-winsor/capped.csv ;;
    verdict)
      run verdict --code code/verdict.py \
        --input runs/main-t3/metrics.json --input runs/main-t4/metrics.json \
        --input runs/h2-winsor/metrics.json \
        --metrics runs/verdict/metrics.json -- "$PY" -I code/verdict.py ;;
    *) echo "unknown run id: $1" >&2; exit 2 ;;
  esac
}

if [[ $# -gt 0 ]]; then
  for id in "$@"; do step "$id"; done
else
  for id in main-t3 main-t4 se-alt placebo-hiwage h2-winsor h2-closures-excl h2-nw-rule verdict; do
    step "$id"
  done
fi
