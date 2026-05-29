#!/usr/bin/env bash
# Count the skills bundled in this hub.
#
# A "skill" = a directory shipping a SKILL.md file. We count every SKILL.md
# under skills/ (case-insensitive). Note: aggregator collections re-bundle
# other collections inside themselves, so this is a raw file count and includes
# those vendored copies — it is the headline number shown on the README.
#
# Usage: ./scripts/count-skills.sh
set -euo pipefail
cd "$(dirname "$0")/.."

total=$(find skills -iname 'SKILL.md' | wc -l | tr -d ' ')
echo "skills (SKILL.md under skills/): ${total}"

echo
echo "per-collection breakdown:"
for d in skills/*/; do
  n=$(find "$d" -iname 'SKILL.md' 2>/dev/null | wc -l | tr -d ' ')
  printf '  %5s  %s\n' "$n" "$(basename "$d")"
done | sort -rn
