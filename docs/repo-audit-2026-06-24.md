# Repo Audit — 2026-06-24 (four-week pass)

A month-long improvement pass on the hub, continuing the cadence of
[`repo-audit-2026-06-23.md`](repo-audit-2026-06-23.md). Unlike the prior
single-session audits, this one ran in four themed weeks — **discover & vendor →
build the discovery engine → deepen safety/quality → integrate & publish** — all
on `improve/discovery-suite`, one project/concern per commit.

## Baseline → end state

| Metric | Start (06-23) | End (06-24) | Source |
|---|---:|---:|---|
| Top-level submodules | 79 | **83** (41 skills / 31 systems / 4 bench / 7 lists) | `scripts/check-repo.py` |
| `SKILL.md` files on disk | 3,324 | **3,428** | [`../catalog/skills.json`](../catalog/skills.json) |
| Distinct skills (content hash) | 2,596 | **2,699** | `catalog/skills.json` |
| Safety findings (high+) | 485 | **418** | [`../catalog/SAFETY.md`](../catalog/SAFETY.md) |
| …in `skill`/`script` (must-review) | 263 | **188** | `catalog/SAFETY.md` |
| Repo unit tests | 120 | **155** | `python3 -m unittest discover -s tests` |

The must-review drop (263 → 188, −28%) is from removing scanner false positives,
not from ignoring real findings — every fix shipped with regression tests.

## Week 1 — discover & vendor (4 projects)

Surfaced gaps via a landscape sweep, then vendored four projects one-PR-each with
full catalog/STARS/README/safety regeneration:

- `c6935db` `skills/zotero-mcp` (Zotero/reference-manager gap)
- `67b57c0` `skills/claude-research` (PhD research-infra; sub-bar exception)
- `533f6ad` `skills/claude-skills-journalism` (verification/FOIA crossover)
- `64a2f14` `systems/popper` (hypothesis testing; license-flagged)
- `b7a91b4` `docs/landscape-2026.md` field map + `docs/vendoring-2026-06-23.md`
- `095cdb7` STARS.md leaderboard refresh (all stars re-fetched)

## Week 2 — the discovery engine

Two network-backed maintenance tools (`4651e0e`, `cf501f5`), 24 new tests:

- `scripts/check-submodule-health.py` → [`../catalog/HEALTH.md`](../catalog/HEALTH.md):
  live stars/license/staleness for all 83 repos. **Surfaced 25/83 needing
  attention** — 8 stale, 21 license-unclear, 0 archived — the hub's first
  systematic upstream-hygiene tracking.
- `scripts/discover-skills.py`: curated GitHub searches + a research-relevance
  filter, de-duped against `.gitmodules` + backlog. Refreshed `catalog/DISCOVERY.md`
  with a triaged fresh-finds section (deep-research systems, research lists).

## Week 3 — safety & quality deepening

Two evidence-backed scanner precision fixes plus analysis:

- `2d66db0` `credential-print` no longer fires on the bare word `token`
  (197 → 122; LLM token counts / tokenizer output were the noise).
- `92f382e` `remote-shell-pipe` no longer flags `curl <api> | python3 -c/-m`
  research-API **data** parses (51 → 36 false criticals).
- `3117157` `docs/safety-triage-2026-06-23.md` — the must-review backlog
  classified into benign-installer / false-positive / real, shrinking the human
  review surface to ~13 real `echo-secret-value` items.
- `91090de` QUALITY.md license dimension cross-linked to per-repo HEALTH.md.
- `78e3b46` `docs/reproducibility-2026-06-23.md` — a critique grounded in the
  HEALTH data (a third of `systems/` carries a license gap or staleness flag).

## Week 4 — integrate & publish

- `docs/systems-matrix-2026.md` — all 31 systems compared by tier / domain /
  license / staleness / reproduction-readiness (19 🟢 · 7 🟡 · 5 🔴).
- `site/index.html` — a "Field map" nav link surfacing the analysis docs.
- This audit.

## Open follow-ups

- File upstream license issues on the 5 no-license flagships (`ai-researcher`,
  `auto-deep-research`, `autosurvey`, `popper`, `sibyl-system`).
- Triage the Week-2 fresh-finds (`Alibaba-NLP/DeepResearch`, `HKUDS/DeepCode`,
  the autoresearch lists) through the CURATION second-review before vendoring.
- Optional residual scanner precision: `credential-print` on `…/apikey` help-URLs
  and placeholder creds (recorded in the safety-triage doc).

## Health verification

`make check` exit 0: 155 unit tests, 83 submodules consistent, generated catalog
/ safety / quality / index / site contracts current, 58 markdown files
link-validated, clean working tree, no submodule drift.
