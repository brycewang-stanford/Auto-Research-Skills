#!/usr/bin/env bash
# Auto-Research-Skills — one-shot setup.
# Fetches every bundled submodule (skills/, systems/, benchmarks/, lists/) shallowly.
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Initializing top-level submodules (shallow)..."
git submodule update --init --depth 1

if [ "${ARS_SKIP_NESTED_SUBMODULES:-0}" != "1" ]; then
  echo "==> Initializing declared nested submodules (best effort)..."
  git submodule foreach --quiet '
    if [ -f .gitmodules ]; then
      echo "  nested: ${sm_path}"
      git submodule update --init --recursive --depth 1 || {
        echo "  warning: nested submodule update failed in ${sm_path}; continuing" >&2
      }
    fi
  '
else
  echo "==> Skipping nested submodules because ARS_SKIP_NESTED_SUBMODULES=1."
fi

count=$(git submodule status | wc -l | tr -d ' ')
echo "==> Done. $count submodules ready."
echo "    skills/     -> reusable agent skills & plugin collections"
echo "    systems/    -> end-to-end research systems & agents"
echo "    benchmarks/ -> autonomous-research / ML-engineering benchmarks"
echo "    lists/      -> curated awesome-lists & surveys"
echo
if [ -f scripts/check-repo.py ]; then
  python3 scripts/check-repo.py || true
  echo
fi

echo "Tip: update top-level submodules later with:  git submodule update --remote --merge"
