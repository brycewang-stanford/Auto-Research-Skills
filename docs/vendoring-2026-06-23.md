# Vendoring Log — 2026-06-23 (discovery batch)

This session vendored four projects: one previously queued candidate
(`zotero-mcp`) plus three newly discovered via a web/GitHub landscape sweep
(`claude-research`, `claude-skills-journalism`, `POPPER`). Each was added as a
shallow git submodule in its own commit (one project per commit, no batching),
with the catalog, STARS leaderboard, both READMEs, and the safety/quality
reports regenerated and `make check` re-run green before commit.

Reviewer: automated maintenance pass. Metadata refreshed live via the GitHub
API on 2026-06-23. Focused safety scans use the repo's own scanner:

```bash
make safety-scan SAFETY_ROOTS=<path> SAFETY_CONTEXT=skill,script,other
```

## Verdicts at a glance

| Project | Stars | License | Dir | SKILL.md | Safety scan | Verdict |
|---|---:|---|---|---:|---|---|
| [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp) | 3,964 | MIT | `skills/zotero-mcp` | 0 | 1 high (false positive) | **vendored** (`c6935db`) |
| [flonat/claude-research](https://github.com/flonat/claude-research) | 96 | MIT | `skills/claude-research` | 50 | 1 critical (benign installer) | **vendored** (`67b57c0`) |
| [jamditis/claude-skills-journalism](https://github.com/jamditis/claude-skills-journalism) | 295 | MIT | `skills/claude-skills-journalism` | 54 | 1 high (false positive) | **vendored** (`533f6ad`) |
| [snap-stanford/POPPER](https://github.com/snap-stanford/POPPER) | 275 | **none** | `systems/popper` | 0 | clean | **vendored, license-flagged** (`64a2f14`) |

Net catalog impact: repos 79 → 83 (+4), headline SKILL.md 3,324 → 3,428
(+104), `skills/` 38 → 41, `systems/` 30 → 31.

---

## 1. zotero-mcp — vendored

- **Metadata:** 3,964★, MIT, Python, pushed 2026-06-22. Default branch `main`.
- **Why:** fills the Zotero / reference-manager gap. MCP-server-as-skill shape
  (`src/`, `pyproject.toml`, `Dockerfile`), **0 `SKILL.md`** — the same category
  as the already-vendored [`skills/arxiv-mcp-server`](../skills/arxiv-mcp-server),
  so it adds a tool without changing the headline skill count.
- **Safety:** 1 HIGH — `print(f" API Key: {_obfuscate_sensitive(api_key)}")` in
  `src/zotero_mcp/setup_helper.py`. **False positive**: the value is obfuscated
  before printing; this is a defensive pattern, not a leak. (Matches the prior
  verdict in [`second-review-2026-06-23.md`](second-review-2026-06-23.md).)
- **Decision:** vendor.

## 2. flonat/claude-research — vendored (sub-bar exception)

- **Metadata:** 96★, MIT, Python, pushed 2026-06-21. Default branch `main`.
- **Why:** PhD-grade Claude Code *infrastructure* — 50 skills plus agents,
  hooks, and rules for academic workflows (`/bib-validate`,
  `/pre-submission-report`, `/literature`, `/proofread`, …). More than a
  markdown-skill dump; it ships an opinionated end-to-end research harness.
- **Curation bar:** 96★ is just under the ~100 soft bar. Vendored as a
  **sanctioned exception** (the bar explicitly allows exceptions when coverage
  is unusually valuable). README wording relaxed from "every one with 100+★"
  to "most with 100+★".
- **Safety:** 1 CRITICAL — `curl -LsSf https://astral.sh/uv/install.sh | sh` in
  `scripts/setup.sh`. **Benign**: the official Astral `uv` installer, same class
  as the previously cleared Nextflow installers. Ships *defensive* hooks
  (`block-destructive-git.sh`, `protect-source-files.sh`).
- **Decision:** vendor.

## 3. jamditis/claude-skills-journalism — vendored

- **Metadata:** 295★, MIT, pushed 2026-06-23. Default branch `master`.
- **Why:** 54 Claude Code skills across journalism, media, and academia —
  fact-checking, FOIA requests, data journalism, academic writing. Fills a
  previously uncovered verification / investigative-workflow niche.
- **Safety:** 1 HIGH — `print(f"[{token}] ...")` in
  `docs/autonomy/kit/reference/wake.reference.py`. **False positive**: `token`
  is a per-session receipt id used in log filenames (`/tmp/wake-{token}.log`),
  not a credential. Ships a `SECURITY.md` and a `security-toolkit`.
- **Scanner note:** this surfaces a real over-match — the `credential-print`
  rule fires on the bare word `token`. Queued for the Week-3 scanner pass.
- **Decision:** vendor.

## 4. snap-stanford/POPPER — vendored, license-flagged

- **Metadata:** 275★, **no license file** (GitHub reports `license: null`),
  Python, last pushed 2025-05-14. Default branch `main`.
- **Why:** "Automated Hypothesis Testing with Agentic Sequential
  Falsifications" (Stanford SNAP) — a Popperian framework that proposes and
  runs experiments to test a hypothesis with statistical error control. A
  distinctive systems-tier capability not otherwise represented in the hub.
- **License gap:** no license normally means *hold*. Vendored as a flagged
  exception given its research significance. The gap is called out in the
  README systems table (⚠️ no upstream license); users must treat the code as
  all-rights-reserved until upstream clarifies.
- **Follow-up:** file an upstream issue requesting an explicit OSI license. If
  upstream declines, reconsider as a *list-only* entry.
- **Safety:** clean.
- **Decision:** vendor under `systems/`, license-flagged.

---

## Discovery provenance

`claude-research`, `claude-skills-journalism`, and `POPPER` were surfaced by a
2026-06-23 landscape sweep of GitHub for autonomous-research projects, then
cross-checked against `catalog/skills.json` and `STARS.md` to confirm they were
absent before vendoring. The sweep's category map is recorded in
[`landscape-2026.md`](landscape-2026.md).
