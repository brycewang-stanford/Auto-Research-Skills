# Repo Audit - 2026-06-23

A maintenance pass focused on the hub's **tooling, reproducibility, and safety
review surface**, not on the vendored projects' internals. Continues the cadence
of [`repo-audit-2026-05-31.md`](repo-audit-2026-05-31.md).

To stay out of other agents' way, this pass avoided the files under active
edit by parallel work (`scripts/check-repo.py`, `tools/check_docs.py`, the two
READMEs, `STARS.md`, `catalog/DISCOVERY.md`, and `site/`). Work concentrated on
the test/CI harness, the generated quality/safety reports, and docs.

## Baseline (reproducible)

All numbers come from the generated catalog and are reproducible with
`make catalog safety-report quality-report`.

| Metric | Value | Source |
|---|---:|---|
| Top-level submodules | 79 (38 skills / 30 systems / 4 benchmarks / 7 lists) | `scripts/check-repo.py` |
| `SKILL.md` files on disk | 3,324 | [`../catalog/skills.json`](../catalog/skills.json) |
| Distinct skills (by content hash) | 2,596 | `catalog/skills.json` |
| Re-bundled copies | 728 (22%) | [`../catalog/QUALITY.md`](../catalog/QUALITY.md) |
| Cross-collection name collisions | 198 | `catalog/QUALITY.md` |
| Skills declaring a license | 28% | `catalog/QUALITY.md` |
| Safety findings (high+) | 485 (231 critical / 254 high) | [`../catalog/SAFETY.md`](../catalog/SAFETY.md) |
| …in `skill`/`script` files (must-review) | 263 (62 critical / 201 high) | `catalog/SAFETY.md` |
| Repo unit tests | 120 | `python3 -m unittest discover -s tests` |

The gap between 485 raw safety findings and 263 must-review ones is the point of
this pass: most criticals are `curl … | bash` install instructions in READMEs,
not executable skill content.

## Work landed this pass

1. **`make check` is green for everyone.** A bare `pytest` from the root was
   collecting ~2,000 vendored-submodule tests and failing with 387 import
   errors. [`../pytest.ini`](../pytest.ini) now pins collection to `tests/`.
2. **`catalog/QUALITY.md` is generated, not hand-written.** It had drifted
   (claimed 3,251 skills vs. the real 3,324). `tools/build_quality_report.py`
   now derives it from the catalog with a `--check` mode enforced in CI.
3. **The safety scanner triages by context.** Every finding is bucketed
   `skill` / `script` / `docs` / `example` / `other`; `catalog/SAFETY.md` leads
   with a "By Context" table and a must-review headline, and a
   `--context skill,script,other` filter focuses a candidate review.
4. **The scanner gained `reverse-shell` and `obfuscated-exec` rules** (high
   signal, near-zero false positives on the current tree) to harden the
   supply-chain gate for future candidates.
5. **`docs/TOOLING.md`** documents the data pipeline, the generated-vs-source
   file map, and the make/CI check matrix — see it before changing any
   generator.

## Open opportunities (prioritised)

1. **Name collisions are the top usability hazard.** 198 names mean different
   things in different collections; agents resolve by name. Consider a README
   note that collections are meant to be installed individually, and/or surface
   the worst collisions to users at install time.
2. **Watermark + template leakage belong in the consistency checker.** 28
   watermark-hidden frontmatters and the lone unedited template skill are
   flagged in `catalog/QUALITY.md`; promoting them to a `check-repo.py` warning
   (owned by another agent this cycle) would catch regressions.
3. **`destructive-root-delete` in `skills/claude-scholar/hooks/security-guard.js`**
   is a block-list regex inside a safety hook, not an execution path. It still
   surfaces in the safety report; a path/Rule allowlist could downgrade known
   false positives without weakening detection.
4. **Per-skill licenses.** Only 28% of `SKILL.md` files declare a license; a
   soft `CONTRIBUTING.md` recommendation would help users who copy a single
   skill out of a collection.
5. **Candidate backlog** in [`../CURATION.md`](../CURATION.md) still has vetted
   projects awaiting a second review before vendoring.

## Open warnings

- `skills/claude-scholar` carries nested gitlinks without matching nested
  `.gitmodules` entries; `scripts/check-repo.py` keeps this as a warning by
  design (CI initialises only top-level submodules).
