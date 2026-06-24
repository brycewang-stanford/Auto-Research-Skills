# Tooling & checks reference

A living map of how this hub's maintenance tooling fits together. It exists so
that contributors — and the several agents that edit this repo in parallel —
can change one thing without breaking another, and never hand-edit a file that
a generator owns.

Everything here is offline and standard-library Python 3.9+ (plus `node` only
for an optional JS syntax check). See [`../AGENTS.md`](../AGENTS.md) for
multi-agent etiquette and [`../CONTRIBUTING.md`](../CONTRIBUTING.md) for the
submission flow.

## The data pipeline

Vendored submodules are the only source of truth for skill content; every
catalog artifact is derived from them and from `.gitmodules`.

```
.gitmodules + skills/*/**/SKILL.md
        │
        ▼
  build_catalog.py ──► catalog/skills.json   (canonical manifest)
        │              catalog/skills.csv
        │              catalog/CATALOG.md
        │              catalog/collections/*.md
        │
        ├─► build_index.py        ──► catalog/search-index.json   ──► site/ (browser)
        │                             catalog/collisions.json
        │
        ├─► build_quality_report.py ──► catalog/QUALITY.md   (reads skills.json + SKILL.md)
        │
        └─ scan-skill-safety.py ─► build_safety_report.py ──► catalog/SAFETY.md

scripts/update-stars.py          ──► STARS.md              (reads GitHub API; run intentionally)
scripts/check-submodule-health.py ─► catalog/HEALTH.md      (reads GitHub API; run intentionally)
scripts/discover-skills.py        ─► catalog/DISCOVERY.md   (manual triage of GitHub search hits)
```

The bottom three tools need the **network** (GitHub API; `$GITHUB_TOKEN` lifts
the rate limit) and are run on demand, *not* by the offline `make check`.

## Generated vs. hand-written files

**Never hand-edit a generated file** — your change will be reverted the next
time its generator runs, and CI's `--check` mode will fail in the meantime.
Regenerate instead (see the next section).

| File | Generator | Source of truth |
|---|---|---|
| [`../catalog/skills.json`](../catalog/skills.json) | `tools/build_catalog.py` | submodules + `.gitmodules` |
| [`../catalog/skills.csv`](../catalog/skills.csv) | `tools/build_catalog.py` | submodules |
| [`../catalog/CATALOG.md`](../catalog/CATALOG.md) | `tools/build_catalog.py` | submodules |
| `catalog/collections/*.md` | `tools/build_catalog.py` | submodules |
| [`../catalog/search-index.json`](../catalog/search-index.json) | `tools/build_index.py` | `skills.json` |
| [`../catalog/collisions.json`](../catalog/collisions.json) | `tools/build_index.py` | `skills.json` |
| [`../catalog/SAFETY.md`](../catalog/SAFETY.md) | `tools/build_safety_report.py` | `scripts/scan-skill-safety.py` over `skills/` |
| [`../catalog/QUALITY.md`](../catalog/QUALITY.md) | `tools/build_quality_report.py` | `skills.json` + `SKILL.md` files |
| [`../STARS.md`](../STARS.md) | `scripts/update-stars.py` | GitHub API (run intentionally) |
| [`../catalog/HEALTH.md`](../catalog/HEALTH.md) | `scripts/check-submodule-health.py` (`make health-report`) | GitHub API — live stars/license/staleness snapshot |

Hand-written (safe to edit directly): the two READMEs, `AGENTS.md`,
`CONTRIBUTING.md`, `CURATION.md`, [`../catalog/README.md`](../catalog/README.md),
`catalog/DISCOVERY.md`, the `docs/` notes, and everything under `site/`,
`tools/`, `scripts/`, and `tests/`.

## Regenerating after a submodule change

When you add, remove, or bump a submodule:

```bash
make catalog          # rebuilds skills.json/csv, CATALOG.md, collections/, and the index
make safety-report    # rebuilds catalog/SAFETY.md
make quality-report   # rebuilds catalog/QUALITY.md
```

Then update the README headline counts if `scripts/check-repo.py` asks, and run
`make check` to confirm everything is consistent.

## The check matrix

`make check` runs every target below. CI splits them across two jobs in
[`../.github/workflows/repo-check.yml`](../.github/workflows/repo-check.yml):
the **metadata** job runs without submodules, while the **catalog** job
initialises the top-level submodules first (the only checks that need skill
files on disk).

| `make` target | Validates | `--check`? | CI job |
|---|---|:--:|---|
| `py-compile` | maintenance scripts compile | n/a | metadata |
| `shell-check` | `setup.sh`, `count-skills.sh` parse | n/a | metadata |
| `test` | `tests/` (unittest + scoped pytest) | n/a | metadata |
| `repo-check` | `.gitmodules`/README/count consistency | yes | metadata |
| `docs-check` | local Markdown links resolve | yes | metadata |
| `site-check` | site assets + search-index contract | yes | metadata |
| `site-js-check` | `site/*.js` syntax (needs `node`) | n/a | metadata |
| `catalog-check` | `skills.json` & friends are current | yes | catalog |
| `index-check` | `search-index.json`/`collisions.json` current | yes | catalog |
| `safety-report-check` | `catalog/SAFETY.md` current | yes | catalog |
| `quality-report-check` | `catalog/QUALITY.md` current | yes | catalog |
| `count-skills` | bundled `SKILL.md` tally | n/a | catalog |

`pytest` is pinned to `tests/` by [`../pytest.ini`](../pytest.ini); without it a
bare `pytest` would try to collect the vendored submodules' own suites and fail.

## Reviewing a candidate's safety

The scanner is reviewer-assist, not a verdict. Findings are bucketed by where
they live (`skill` / `script` / `docs` / `example` / `other`) because a
`curl … | bash` line in a README is install documentation, while the same line
in a `SKILL.md` body or shipped script is something an agent might run.

```bash
# Scan a candidate checkout before vendoring.
python3 scripts/scan-skill-safety.py /path/to/candidate --fail-on none

# Focus a review on executable instructions, skipping install-doc noise.
make safety-scan SAFETY_ROOTS=skills/<name> SAFETY_CONTEXT=skill,script,other
```

`catalog/SAFETY.md` leads with a "By Context" table and an "in skill/script
files" headline so reviewers can triage the executable findings first.

## Conventions for generators

If you add or change a generator, keep it consistent with the existing ones:

- Provide a `--check` mode that re-renders in memory and compares to the file
  on disk, exiting non-zero (and printing the regenerate command) on drift.
- Emit **no timestamps or other nondeterministic content**, so `--check` can
  compare byte-for-byte across machines and CI.
- Wire `<name>` and `<name>-check` Makefile targets, add the check to the
  `check` aggregate, place the `-check` in the right CI job (metadata if it
  needs no submodules, catalog if it reads skill files), and add tests under
  `tests/`.
