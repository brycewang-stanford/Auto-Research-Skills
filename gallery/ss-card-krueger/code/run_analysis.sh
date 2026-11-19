#!/usr/bin/env bash
# Planned analysis runs 1-8 (plan.json analysis_plan), in order, through crew.py run.
#
# Do NOT start this before the Reviewer's code review (analysis_plan 0d): the guard below
# refuses unless the latest reviews/code-r*/review.json has no open critical or major
# finding. The design gate is checked by crew.py itself.
#
# Usage, from anywhere:
#   bash gallery/ss-card-krueger/code/run_analysis.sh            # all eight runs
#   bash gallery/ss-card-krueger/code/run_analysis.sh main-t3    # one run (add --replace
#                                                                #  via REPLACE=1 to redo it)
set -euo pipefail

WS="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CREW="$(cd "$WS/../.." && pwd)/crew/scripts/crew.py"
PY=".venv/bin/python"            # resolved by crew.py relative to the workspace
DATA="data/derived/stores.csv"
EXTRA=()
[[ "${REPLACE:-0}" == "1" ]] && EXTRA+=(--replace)

python3 - "$WS" <<'EOF'
import json, re, sys
from pathlib import Path
ws = Path(sys.argv[1])
rounds = sorted((int(m.group(1)), p) for p in (ws / "reviews").glob("code-r*/review.json")
                if (m := re.search(r"code-r(\d+)", str(p))))
if not rounds:
    sys.exit("REFUSED: no code review (reviews/code-r*/review.json) yet; analysis_plan 0d")
review = json.loads(rounds[-1][1].read_text())
blocking = [f["id"] for f in review.get("findings", [])
            if f.get("status") == "open" and f.get("severity") in ("critical", "major")]
if blocking:
    sys.exit(f"REFUSED: {rounds[-1][1].parent.name} has open critical/major findings {blocking}")
print(f"code review {rounds[-1][1].parent.name}: verdict {review.get('verdict')}, no open critical/major finding")
EOF

run() {  # run <id> [extra crew.py args...] -- <command...>
  local id="$1"; shift
  python3 "$CREW" run "$WS" --id "$id" --role econometrician --kind analysis ${EXTRA[@]+"${EXTRA[@]}"} "$@"
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
