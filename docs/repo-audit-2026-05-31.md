# Repo Audit - 2026-05-31

## Scope

This pass focused on the repository as a research-skills hub rather than on the
vendored projects' internals. I avoided editing files already modified by the
parallel agent (`README.md`, `README_CN.md`, `CONTRIBUTING.md`, `setup.sh`,
`CURATION.md`, `.github/workflows/repo-check.yml`, and
`scripts/check-repo.py`).

## Local Baseline

- `git status` showed existing parallel-agent changes before this pass.
- `python3 scripts/check-repo.py` passed with one warning:
  `skills/claude-scholar` contains nested gitlinks without matching nested
  `.gitmodules` entries.
- `./scripts/count-skills.sh` reports 3,250 raw `SKILL.md` files under
  `skills/`.
- The top-level inventory is 76 submodules: 35 skills, 30 systems,
  4 benchmarks, and 7 lists.

## High-Value Improvements

1. Safety review should be a first-class maintenance path. Third-party skills
   are executable instruction bundles, so curation needs static checks for
   remote shell pipes, credential leakage, concealment instructions, and
   destructive commands.
2. The README count should stay explicit about "raw SKILL.md count" versus
   unique capabilities, because aggregator repos re-bundle other collections.
3. Candidate projects should move through a backlog before becoming submodules:
   source signal, license, maintenance, overlap, install evidence, then safety
   scan.
4. Broad ecosystem collections can be useful as lists or discovery sources even
   when they should not be vendored wholesale.
5. The `claude-scholar` nested gitlink warning is worth preserving as a warning
   by default, but should be a release-blocking check under a stricter maintainer
   mode before submodule refreshes.

## Work Completed In This Pass

- Added `scripts/scan-skill-safety.py`, an offline heuristic scanner for
  high-risk patterns in vendored skills and install scripts.
- Ran public registry searches with `npx skills find` across academic research,
  literature review, paper review, reproducibility, Zotero, and bioinformatics.
- Checked live GitHub metadata for the strongest near-term candidates.

## New Safety Scanner

Use the scanner as a manual-review gate:

```bash
python3 scripts/scan-skill-safety.py
```

Useful variants:

```bash
# Include medium-severity prompts and installer concerns.
python3 scripts/scan-skill-safety.py --min-severity medium --fail-on critical

# Scan a candidate checkout before adding it as a submodule.
python3 scripts/scan-skill-safety.py /tmp/candidate-skill-repo --fail-on none

# Machine-readable output for future CI or dashboards.
python3 scripts/scan-skill-safety.py --json
```

The scanner is intentionally conservative. Findings are review prompts, not
automatic verdicts.

Initial run on the current checkout:

```bash
python3 scripts/scan-skill-safety.py --max-findings 20 --fail-on none
```

Result: 444 high/critical findings after truncation controls
(`critical=201`, `high=243`). Most critical findings are documented installer
patterns such as `curl | bash` or PowerShell `iwr | iex`. One apparent
`rm -rf /` finding in `skills/claude-scholar/hooks/security-guard.js` is a
block-list regex inside a safety hook, not an execution path, and should be
allowlisted or downgraded in a future refinement.

## External Skill Discovery

Registry signals from `npx skills find`:

| Query | High-signal results | Current action |
|---|---|---|
| `academic research` | `shubhamsaboo/awesome-llm-apps@academic-researcher` (5.3k installs), `claude-office-skills/skills@academic-search` (3k installs), `tdimino/claude-code-minoan@academic-research` (112 installs) | Audit before listing; first two are broad sources, not obviously research-skill repos. |
| `literature review` | `lingzhi227/agent-research-skills@literature-review` (1.1k installs), `affaan-m/everything-claude-code@literature-review` (1.1k installs), `collaborative-deep-research/agent-papers-cli@literature-review` (556 installs) | Keep in curation backlog; verify license and overlap. |
| `paper review` | `bytedance/deer-flow@academic-paper-review` (830 installs), `evoscientist/evoskills@paper-review` (329 installs) | Deer Flow is already bundled as a system; EvoSkills is a strong skills candidate. |
| `reproducibility research` | `seabbs/skills@analyzing-research-papers` (311 installs), `pedrohcgs/claude-code-my-workflow@audit-reproducibility` (17 installs) | Existing bundled workflow covers part of this; inspect seabbs for a potential gap. |
| `bioinformatics` | `delphine-l/claude_global@bioinformatics-fundamentals` (260 installs), `omer-metin/skills-for-antigravity@bioinformatics-workflows` (99 installs) | Track as domain-science gap candidates. |

Near-term candidates from web/GitHub review:

| Candidate | Signal checked on 2026-05-31 | Suggested action |
|---|---:|---|
| `EvoScientist/EvoSkills` | 381 stars, Apache-2.0, updated 2026-05-28, registry paper-review skill 329 installs | Strongest near-term `skills/` candidate after a safety scan and overlap audit. |
| `Aperivue/medsci-skills` | 123 stars, active on 2026-05-31, medical end-to-end pipeline | Strong domain candidate; clarify license because GitHub API returned `NOASSERTION`. |
| `poemswe/co-researcher` | 101 stars, MIT, multi-platform support including Codex | Strong near-term candidate; audit install/bootstrap scripts carefully. |
| `WenyuChiou/ai-research-skills` | 83 stars, MIT, active on 2026-05-31, structured research manifests | Track despite sub-100 stars because it covers stateful research handoffs. |
| `lingzhi227/agent-research-skills` | 90 stars, 1.1k installs for literature-review, no GitHub license metadata | Track; license must be resolved before vendoring. |
| `huggingface/skills` | 10.6k stars, Apache-2.0, official AI/ML skill examples | Add as a reference/list candidate, not as a research-specific skill bundle. |

## One-Week Execution Plan

Day 1: Freeze the current baseline, keep the parallel-agent diff separate, and
run metadata checks.

Day 2: Expand candidate discovery through `skills.sh`, GitHub topic searches,
and existing bundled awesome lists.

Day 3: Run safety scans on shortlisted candidates, then manually review any
critical/high findings.

Day 4: Update curation notes with scorecards and make README candidate markers
consistent across English and Chinese.

Day 5: Add only the highest-confidence submodule candidates, one project per
commit/PR-sized change.

Day 6: Strengthen CI around metadata drift, nested submodules, and optional
safety scanning.

Day 7: Final validation: repo checks, skill counts, README link sanity, status
review, and handoff for owner acceptance.

## Sources

- https://skills.sh/
- https://github.com/EvoScientist/EvoSkills
- https://github.com/Aperivue/medsci-skills
- https://github.com/poemswe/co-researcher
- https://github.com/WenyuChiou/ai-research-skills
- https://github.com/lingzhi227/agent-research-skills
- https://github.com/huggingface/skills
- https://arxiv.org/abs/2602.08004
- https://arxiv.org/abs/2604.03070
