# Curation Notes

This repo is a hub, so quality control matters as much as coverage. Use this
file as the working backlog for candidates that look useful but are not ready
to vendor as submodules yet.

## Current Standard

- Scope: autonomous research systems, research-oriented agent skills, domain
  science agents, benchmarks, and curated lists that help agents do research.
- Default bar for vendoring: canonical GitHub repo, clear license, active
  maintenance, useful docs, and roughly 100+ GitHub stars. Exceptions are fine
  when a project fills a real gap or has strong install/use evidence.
- Skills should include `SKILL.md` files with clear trigger descriptions.
  Prefer concise skills with references/scripts split out when details are long.
- Treat third-party skills as executable supply-chain inputs. Before vendoring,
  scan for dangerous shell commands, secret harvesting, unexpected network
  calls, hidden binaries, and prompt-injection style instructions.
- Prefer adding uncertain projects here first. Vendor them only after a second
  review and a clean `python3 scripts/check-repo.py` run.

## External Sources Checked

- `npx skills find` via the public skills registry surfaced install-count
  signals for research, academic writing, literature review, Zotero, bioinfo,
  reproducibility, and paper-review queries: <https://skills.sh/>
- SkillsMD is another cross-agent registry for browsing agent skills:
  <https://skillsmd.dev/>
- Anthropic's official `anthropics/skills` repo is a useful reference for skill
  layout, templates, and official examples: <https://github.com/anthropics/skills>
- `InternScience/Awesome-Scientific-Skills` is already bundled and remains a
  good upstream source for scientific-skill discovery:
  <https://github.com/InternScience/Awesome-Scientific-Skills>
- Recent ecosystem papers make the case for stricter curation: one large-scale
  analysis reports strong redundancy and safety risks across public skills
  (<https://arxiv.org/abs/2602.08004>), and another studies semantic
  supply-chain attacks through `SKILL.md` metadata/instructions
  (<https://arxiv.org/abs/2605.11418>).

## Recently Promoted

| Project | Promoted to | Review note |
|---|---|---|
| [poemswe/co-researcher](https://github.com/poemswe/co-researcher) | `skills/co-researcher` | Added 2026-06-01 after MIT license check, README/SKILL.md review, and safety scan. The single high scanner hit is in an eval JSON example about rejecting covert scraping, not in executable skill instructions. |

## Candidate Backlog

Checked on 2026-05-31 with GitHub API metadata and `npx skills find` output.
Stars and install counts are approximate and should be refreshed before a PR.

| Candidate | Why it is interesting | Signal | Suggested action |
|---|---|---:|---|
| [anthropics/skills](https://github.com/anthropics/skills) | Official reference implementations, templates, and spec-adjacent examples for Agent Skills. | ~144k stars | Add as a reference/list entry, not a research skill, unless the repo wants an official-pattern bundle. |
| [affaan-m/ECC](https://github.com/affaan-m/ECC) | Broad cross-agent toolkit formerly found via `everything-claude-code`; includes research-first development, memory, security, and workflow patterns. | ~199k stars | Review as ecosystem infrastructure; do not vendor blindly because it is broad. |
| [VoltAgent/awesome-openclaw-skills](https://github.com/VoltAgent/awesome-openclaw-skills) | Large OpenClaw skill index, useful for discovery and gap analysis. | ~49k stars | Add to lists only after security caveats; too broad for direct skills vendoring. |
| [sickn33/antigravity-awesome-skills](https://github.com/sickn33/antigravity-awesome-skills) | Large installable library for Claude Code, Codex CLI, Gemini CLI, Cursor, and Antigravity. | ~39k stars | Review as a list/infrastructure candidate; security review needed. |
| [EvoScientist/EvoSkills](https://github.com/EvoScientist/EvoSkills) | Installable skill and knowledge packs for EvoScientist-style scientific work. | ~381 stars; `paper-review` skill ~327 installs | Good coverage, but hold before vendoring: the `nano-banana` skill currently suggests `echo $GOOGLE_API_KEY`, which would expose secrets in agent-visible output. |
| [zsyggg/paper-craft-skills](https://github.com/zsyggg/paper-craft-skills) | Paper analysis, summaries, and visual explanation skills for Claude Code. | ~385 stars | Promising paper-understanding package; needs explicit license/provenance check before vendoring. |
| [WenyuChiou/ai-research-skills](https://github.com/WenyuChiou/ai-research-skills) | Cross-agent SKILL.md catalog for literature review, research design, project memory, manuscript writing, and delegation. | ~83 stars; MIT | Monitor until it clears the default 100-star bar, or review earlier if cross-agent coverage is prioritized. |
| [ShZhao27208/Aut_Sci_Write](https://github.com/ShZhao27208/Aut_Sci_Write) | Literature search, PDF extraction, figure cropping, Zotero sync, review writing, and PPT generation. | ~88 stars; MIT | Monitor; potentially useful for Zotero/PDF workflow gaps once it matures. |
| [LeonChaoX/qinyan-academic-skills](https://github.com/LeonChaoX/qinyan-academic-skills) | Chinese academic research skill library with many agents across paper search, writing, medicine, bioinfo, and drug discovery. | ~99 stars | Already listed in README; revisit once it clears the 100-star bar or if Chinese coverage is prioritized. |
| [lingzhi227/agent-research-skills](https://github.com/lingzhi227/agent-research-skills) | Systematic academic literature-review skill. | ~89 stars; `literature-review` skill ~1.1k installs | Already listed in README; installs justify a closer manual audit despite sub-100 stars. |
| [collaborative-deep-research/agent-papers-cli](https://github.com/collaborative-deep-research/agent-papers-cli) | Literature-review workflow surfaced by registry search. | ~44 stars; `literature-review` skill ~556 installs | Monitor; needs more repo-level maturity before vendoring. |
| [shoei05/claude-code-zotero-skill](https://github.com/shoei05/claude-code-zotero-skill) | Focused Zotero local API skill for import/search/collection workflows. | ~11 stars; `zotero` skill ~143 installs | Track as a gap-specific Zotero candidate; likely too small to vendor now. |
| [FuZhiyu/ResearchProjectTemplate](https://github.com/FuZhiyu/ResearchProjectTemplate) | AI-friendly Git research-project template with Zotero paper-reader skill. | ~8 stars; `zotero-paper-reader` skill ~425 installs | Monitor; template may be useful even if repo maturity is low. |
| [Delphine-L/claude_global](https://github.com/Delphine-L/claude_global) | Galaxy and bioinformatics-focused global skills. | ~13 stars; `bioinformatics-fundamentals` skill ~260 installs | Track for bioinformatics gap coverage; not ready for top-level vendoring. |

## Practical Review Checklist

1. Verify the candidate is not already bundled under a different name or inside
   an existing aggregate submodule.
2. Read the root README, license, and every top-level `SKILL.md` trigger.
3. Search for high-risk patterns: `curl | sh`, `rm -rf`, credential reads,
   hidden network calls, obfuscated payloads, and instructions that ask the
   agent to hide behavior from the user.
4. Decide whether it belongs in `skills/`, `systems/`, `benchmarks/`, `lists/`,
   or only in this backlog.
5. Add one project per PR, update both README files, and run:

```bash
python3 scripts/check-repo.py
./scripts/count-skills.sh
```
