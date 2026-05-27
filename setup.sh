#!/usr/bin/env bash
# Auto-Research-Skills — one-shot setup.
# Fetches every bundled submodule (skills/, systems/, benchmarks/, lists/) shallowly.
set -euo pipefail

cd "$(dirname "$0")"

echo "==> Initializing ${0##*/} submodules (shallow)..."
git submodule update --init --recursive --depth 1

count=$(git submodule status | wc -l | tr -d ' ')
echo "==> Done. $count submodules ready."
echo "    skills/     -> reusable agent skills & plugin collections"
echo "    systems/    -> end-to-end research systems & agents"
echo "    benchmarks/ -> autonomous-research / ML-engineering benchmarks"
echo "    lists/      -> curated awesome-lists & surveys"
echo
echo "Tip: update everything later with:  git submodule update --remote --merge"
