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
| [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp) | `skills/zotero-mcp` | Added 2026-06-23 (MIT, ~4.0k★). Fills the Zotero gap; MCP-server-as-skill shape like `arxiv-mcp-server`. Sole high finding is an `_obfuscate_sensitive()` print (defensive). See [`docs/vendoring-2026-06-23.md`](docs/vendoring-2026-06-23.md). |
| [flonat/claude-research](https://github.com/flonat/claude-research) | `skills/claude-research` | Added 2026-06-23 (MIT, ~96★ — sub-bar exception for a complete PhD research-infra collection). One critical is the official Astral `uv` installer (benign). |
| [jamditis/claude-skills-journalism](https://github.com/jamditis/claude-skills-journalism) | `skills/claude-skills-journalism` | Added 2026-06-23 (MIT, ~295★). Journalism/media/academia skills (fact-check, FOIA, data journalism). One high is a false-positive on a non-credential `token` variable. |
| [snap-stanford/POPPER](https://github.com/snap-stanford/POPPER) | `systems/popper` | Added 2026-06-23 (~275★). Agentic sequential-falsification hypothesis testing (Stanford SNAP). ⚠️ no upstream license — vendored as a flagged exception; treat as all-rights-reserved until clarified. Scan clean. |
| [HKUDS/DeepCode](https://github.com/HKUDS/DeepCode) | `systems/deepcode` | Added 2026-06-24 (MIT, ~15.8k★). Open agentic coding: Paper2Code + Text2Web/Backend; complements `paper2code`. 2 high findings are benign Chinese setup help-text. |
| [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) | `skills/autoresearch` | Added 2026-06-24 (MIT, ~5.2k★). Karpathy-style autonomous-iteration Claude skill. The one critical (`mkfs`) is inside the skill's own command-refusal safety guard — defensive, not a leak. |
| [tmgthb/Autonomous-Agents](https://github.com/tmgthb/Autonomous-Agents) | `lists/autonomous-agents` | Added 2026-06-24 (MIT, ~1.3k★). Daily-updated autonomous-agent research-paper list. |
| [webfuse-com/awesome-autoresearch](https://github.com/webfuse-com/awesome-autoresearch) | `lists/awesome-autoresearch` | Added 2026-06-24 (CC0, ~2.3k★). Curated autoresearch / autonomous-improvement-loop systems. |

## Second-Review Queue

Use this queue for candidates that already passed a first read but should not
be vendored until a second reviewer records fresh evidence. Stars and install
counts drift; refresh them on the day of the PR.

| Priority | Candidate | Current second-review question | Required evidence before vendoring |
|---:|---|---|---|
| ✅ done | [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp) | ~~Does it cleanly fill the Zotero/reference-manager gap without duplicating `arxiv-mcp-server`?~~ | **Vendored 2026-06-23** at `skills/zotero-mcp` (commit `c6935db`); see [`docs/vendoring-2026-06-23.md`](docs/vendoring-2026-06-23.md). |
| 2 | [ClawBio/ClawBio](https://github.com/ClawBio/ClawBio) | If adding one bioinformatics collection, is reproducible-code-first coverage more useful than breadth? | Fresh license check, overlap note against `scientific-agent-skills` and `medical-research-skills`, focused safety scan, and catalog count impact estimate. |
| 3 | [GPTomics/bioSkills](https://github.com/GPTomics/bioSkills) | Does the 500+ skill breadth justify the additional collision/redundancy surface? | Same evidence as ClawBio, plus a name-collision estimate before adding the submodule. |
| 4 | [jaechang-hits/SciAgent-Skills](https://github.com/jaechang-hits/SciAgent-Skills) | Is the license/provenance story clear enough for per-skill reuse? | Confirm the repo license file, check any per-skill license metadata, run focused safety scan, then decide whether to prefer it over ClawBio/bioSkills. |
| hold | [EvoScientist/EvoSkills](https://github.com/EvoScientist/EvoSkills) | Has the `nano-banana` credential-print issue been fixed upstream? | Do not vendor until the second reviewer confirms the unsafe `echo $GOOGLE_API_KEY` guidance is gone or isolated to non-executable docs. |
| hold | [zsyggg/paper-craft-skills](https://github.com/zsyggg/paper-craft-skills) | Is license/provenance explicit enough for a copied-skill workflow? | License/provenance confirmation plus focused safety scan. |

Second-review notes should record reviewer, date, commit/tag inspected, commands
run, and the final decision: `vendor`, `list-only`, `hold`, or `reject`. Add
one project per PR and do not batch submodule additions.

Executed reviews (refreshed metadata, focused safety scans, and per-candidate
verdicts) are logged in
[`docs/second-review-2026-06-23.md`](docs/second-review-2026-06-23.md):
zotero-mcp and one bioinformatics collection (bioSkills or ClawBio) are
vendor-ready; SciAgent-Skills, EvoSkills, and paper-craft-skills are held on
license or secret-exposure grounds.

A follow-up discovery batch — `zotero-mcp` plus three newly surfaced projects
(`claude-research`, `claude-skills-journalism`, `POPPER`) — was vendored on
2026-06-23 and is logged in
[`docs/vendoring-2026-06-23.md`](docs/vendoring-2026-06-23.md).

A second-review of the 2026-06-23 scripted-discovery fresh finds is logged in
[`docs/second-review-2026-06-24.md`](docs/second-review-2026-06-24.md): all
eight code-bearing candidates scanned clean; the recommended next round is
`HKUDS/DeepCode` + `uditgoenka/autoresearch` + 1–2 autoresearch lists, holding
the redundant deep-research agents and broad/off-scope skill dumps. Upstream
license-request drafts for the no-license vendored systems are in
[`docs/upstream-license-requests-2026-06-24.md`](docs/upstream-license-requests-2026-06-24.md).

## Discovery Round — 2026-07-11

New trending research-automation repos surfaced via GitHub search/trending and
verified through the GitHub API (existence, star count, and last-push recency
all confirmed on 2026-07-11). None were already vendored or listed. All were
added to the README curated tables as **list-only candidates** (no `🧩`); they
are *not* vendored as submodules yet, so headline counts are unchanged. Vendor
only after a second review and a focused safety scan, one project per PR.

**Autonomous systems / AI scientists**

| Candidate | ★ | License | Note |
|---|---:|---|---|
| [karpathy/autoresearch](https://github.com/karpathy/autoresearch) | ~90.8k | none | Karpathy's overnight autonomous-research loop on single-GPU nanochat training. Huge reach, but **no LICENSE file** — list-only; do not vendor/reuse code until licensing is clarified. |
| [EvoScientist/EvoScientist](https://github.com/EvoScientist/EvoScientist) | ~4.1k | Apache-2.0 | Self-evolving multi-agent AI scientists. Distinct from the already-listed `EvoScientist/EvoSkills`. Strong vendor candidate pending safety scan. |
| [ResearAI/DeepScientist](https://github.com/ResearAI/DeepScientist) | ~3.2k | none | Local-first autonomous research studio (TS UI + Python). No license — list-only. |
| [OpenNSWM-Lab/FAROS](https://github.com/OpenNSWM-Lab/FAROS) | ~1.8k | none | Blueprint-driven AutoResearch runtime (idea→experiment→paper→review). No license — list-only. |
| [OpenRaiser/NanoResearch](https://github.com/OpenRaiser/NanoResearch) | ~1.5k | MIT | Lightweight autonomous AI research assistant; skills/agent-based. Vendor candidate. |
| [InternScience/InternAgent](https://github.com/InternScience/InternAgent) | ~1.4k | Apache-2.0 | Lab-backed (InternScience) long-horizon scientific-discovery framework. Vendor candidate. |
| [zhu-minjun/Researcher](https://github.com/zhu-minjun/Researcher) | ~398 | custom (CycleResearcher-License) | Research-via-automated-review loop with released models. Custom license — list-only. |
| [tsinghua-fib-lab/OmniScientist](https://github.com/tsinghua-fib-lab/OmniScientist) | ~153 | MIT | AI-scientist ecosystem encoding research infrastructure. Vendor candidate. |

**Data-science / experiment agents**

| Candidate | ★ | License | Note |
|---|---:|---|---|
| [ruc-datalab/DeepAnalyze](https://github.com/ruc-datalab/DeepAnalyze) | ~4.3k | MIT | Autonomous data-science agent; analysis → report. Vendor candidate for `systems/`. |
| [starpig1129/DATAGEN](https://github.com/starpig1129/DATAGEN) | ~1.8k | MIT | LangGraph multi-agent research assistant (hypothesis → analysis → report). |

**Deep research / literature synthesis**

| Candidate | ★ | License | Note |
|---|---:|---|---|
| [AkariAsai/OpenScholar](https://github.com/AkariAsai/OpenScholar) | ~1.6k | Apache-2.0 | AllenAI/UW retrieval-augmented literature synthesis with grounded citations. Strong vendor candidate. |
| [khoj-ai/openpaper](https://github.com/khoj-ai/openpaper) | ~376 | AGPL-3.0 | Paper-library workbench + AI lit review. **AGPL** — flag copyleft before vendoring. |

**Skills & plugin collections**

| Candidate | ★ | License | Note |
|---|---:|---|---|
| [openags/paper-search-mcp](https://github.com/openags/paper-search-mcp) | ~2.1k | MIT | Multi-source (arXiv/PubMed/bioRxiv) paper-search MCP + CLI + skills. **Top vendor pick** — fills the paper-discovery gap next to `arxiv-mcp-server`/`zotero-mcp`. |
| [AIScientists-Dev/academic-humanizer](https://github.com/AIScientists-Dev/academic-humanizer) | ~343 | MIT | Single-purpose "strip AI-writing tells" finishing pass for papers/grants. Easy drop-in. |
| [guhaohao0991/PaperClaw](https://github.com/guhaohao0991/PaperClaw) | ~242 | MIT | Generates topic-specific paper search-review-critique expert agents (OpenClaw). |
| [Stars-OC/thesis-creator](https://github.com/Stars-OC/thesis-creator) | ~191 | MIT | Chinese undergrad-thesis writing skill with AIGC/plagiarism reduction. |
| [ai4s-research/ai4s-skills](https://github.com/ai4s-research/ai4s-skills) | ~141 | MIT | 7-skill AI-for-Science pipeline with integrity audit. Clean modular design — vendor candidate. |
| [LMDHQ-0420/ResearchPilot-Skills](https://github.com/LMDHQ-0420/ResearchPilot-Skills) | ~138 | MIT | 7-phase automated academic workflow. |
| [SNL-UCSB/paper-writing-skill](https://github.com/SNL-UCSB/paper-writing-skill) | ~106 | MIT | Tightly-scoped editorial pipeline (UCSB); good "writing craft" module. |
| [voidful/academic-skills](https://github.com/voidful/academic-skills) | ~103 | MIT | Cross-agent (Claude/Codex/Gemini) suite covering review + ideation phases. |

**Benchmarks**

| Candidate | ★ | License | Note |
|---|---:|---|---|
| [openai/mle-bench](https://github.com/openai/mle-bench) | ~1.6k | MIT | Reference ML-engineering-agent benchmark (75 Kaggle competitions). Strong benchmark vendor pick. |
| [scicode-bench/SciCode](https://github.com/scicode-bench/SciCode) | ~213 | Apache-2.0 | LMs coding solutions to research-grade scientific problems. |
| [HKUST-KnowComp/NewtonBench](https://github.com/HKUST-KnowComp/NewtonBench) | ~152 | MIT | ICLR 2026 — generalizable scientific-law discovery; complements DiscoveryBench/ScienceAgentBench. |
| [Future-House/BixBench](https://github.com/Future-House/BixBench) | ~130 | Apache-2.0 | Computational-biology agent benchmark (FutureHouse; sibling of the bundled `aviary`). |

**Domain science**

| Candidate | ★ | License | Note |
|---|---:|---|---|
| [GENTEL-lab/OriGene](https://github.com/GENTEL-lab/OriGene) | ~218 | CC-BY-NC-SA-4.0 | Self-evolving "virtual disease biologist" for therapeutic-target discovery. **Non-commercial license** — list-only unless a non-commercial exception is acceptable. |

**Suggested next vendoring order** (MIT/Apache, active, gap-filling; one PR each,
each with a focused `make safety-scan` + `python3 scripts/check-repo.py`):
`openags/paper-search-mcp` → `ai4s-research/ai4s-skills` → `openai/mle-bench`
(benchmarks) → `AkariAsai/OpenScholar`. Hold no-license systems
(`karpathy/autoresearch`, `ResearAI/DeepScientist`, `OpenNSWM-Lab/FAROS`),
copyleft (`khoj-ai/openpaper`, AGPL), and non-commercial (`GENTEL-lab/OriGene`)
as list-only until licensing is resolved.

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
make safety-scan SAFETY_ROOTS=/path/to/scratch-clone SAFETY_CONTEXT=skill,script,other
python3 scripts/check-repo.py
./scripts/count-skills.sh
```
