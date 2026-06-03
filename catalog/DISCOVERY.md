# 🔭 Discovery — candidate skills not yet bundled

A working dossier of **new** research-oriented skill/agent repos found online,
de-duplicated against everything already bundled (`.gitmodules`, 76 repos) and
against the existing backlog in [`../CURATION.md`](../CURATION.md). It extends
that backlog with fresh finds and live signals.

**Scope of this file is _discovery only_.** It deliberately does **not** edit
`.gitmodules`, the READMEs, or `STARS.md` — those are being actively changed by
parallel repo-hardening work, and vendoring here would collide. Each candidate
ships a ready-to-run `git submodule add` command so a maintainer can vendor it
in one step **after**:

1. the repo-hardening branch is merged (to avoid `.gitmodules` conflicts), and
2. a full supply-chain scan passes per the
   [CURATION.md checklist](../CURATION.md#practical-review-checklist).

**Method.** Surveyed public skill registries (skills.sh, skillsmd.dev,
agentskills.so, mcpmarket) and GitHub topic searches; pulled live repo metadata
via the GitHub API and did a first-pass README/security read. Stars and dates
are as of **2026-05-31** and drift quickly — re-check before a PR.

---

## Tier 1 — strong candidates (clear license, active, fills a real gap)

| Candidate | ⭐ | License | Gap it fills | Suggested path | Security first-pass |
|---|---:|---|---|---|---|
| [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp) | 3.5k | MIT | **Zotero / reference-manager** — the most-requested gap in CURATION.md. Semantic search, annotation extraction, citation analysis over a local Zotero library. | `skills/zotero-mcp` (MCP server; same shelf as `arxiv-mcp-server`) | Clean. `pip`/`uv` install, no shell pipes. Needs a Zotero API key (expected). |
| [GPTomics/bioSkills](https://github.com/GPTomics/bioSkills) | 819 | MIT | **Bioinformatics breadth** — 528 `SKILL.md` across 63 categories (single-cell, variant calling, ChIP-seq, phylogenetics). | `skills/bioskills` | Low–moderate. Ships `install-*.sh` per agent; relies on external CLIs (samtools, GATK) + NCBI/UniProt. No credential harvesting seen. |
| [ClawBio/ClawBio](https://github.com/ClawBio/ClawBio) | 891 | MIT | **Reproducible genomics** — 77 skills (27 production-ready); each skill is a versioned spec + validated Python + demo data. Architecture constrains the agent to vetted code rather than improvised scripts. | `skills/clawbio` | Low–moderate. Recommends the standard `curl … astral.sh/uv | sh` bootstrap; deps locked via `uv.lock`. Optional Galaxy API key. |
| [jaechang-hits/SciAgent-Skills](https://github.com/jaechang-hits/SciAgent-Skills) | 186 | CC-BY-4.0¹ | **Domain-science depth** — 199 markdown skills (genomics, drug discovery, proteomics); reports BixBench 92%. | `skills/sciagent-skills` | Low runtime risk (markdown only). Setup uses `curl … pixi.sh/install.sh | bash` (toolchain bootstrap). |

¹ The GitHub API reports `NOASSERTION`; the README states **CC-BY-4.0 for original
content**, with individual skills noting their underlying tool licenses. Confirm
the `LICENSE` file before vendoring.

> **Note on the two bioinformatics options.** `bioSkills`, `ClawBio`, and
> `SciAgent-Skills` overlap in domain. If keeping the hub lean, prefer **one**
> primary bioinformatics collection (ClawBio for reproducibility-first, or
> SciAgent-Skills for benchmarked breadth) rather than all three. Note that
> `scientific-agent-skills` (already bundled) and `medical-research-skills`
> (556 skills) already cover parts of biology/medicine — run the catalog
> overlap check before adding a third.

## Tier 2 — promising, but with a caveat

| Candidate | ⭐ | License | Note |
|---|---:|---|---|
| [yilewang/llm-for-zotero](https://github.com/yilewang/llm-for-zotero) | 1.7k | **AGPL-3.0** | A research agent rooted in a Zotero library; very active. AGPL is strong copyleft — fine to vendor as an isolated submodule, but flag the license so downstream users understand the obligations. Overlaps with `zotero-mcp`; pick one Zotero entry. |
| [papersgpt/papersgpt-for-zotero](https://github.com/papersgpt/papersgpt-for-zotero) | 2.4k | **AGPL-3.0** | Popular Zotero AI plugin that also exposes a SKILL. Primarily a GUI plugin rather than an agent-skill collection; AGPL. Lower priority than `zotero-mcp` for an agent-skills hub. |
| [andrehuang/academic-writing-agents](https://github.com/andrehuang/academic-writing-agents) | 81 | MIT | Multi-agent academic-writing orchestrator (10–12 specialists). Just under the 100★ bar. Same author as the already-bundled `research-companion`; check for overlap. |
| [YYH211/Claude-meta-skill](https://github.com/YYH211/Claude-meta-skill) | 268 | MIT | "Skills for building skills." Useful but **meta**, not research — only add if the hub wants a skill-authoring helper. |

## Tier 3 — track only (below the bar today)

| Candidate | ⭐ | License | Why it's parked |
|---|---:|---|---|
| [cookjohn/pm-skills](https://github.com/cookjohn/pm-skills) | 15 | none | Fills a real **PubMed** gap, but **no license** (blocker) and low signal. Watch — ask upstream to add a license. |
| [Black-Lights/prisma-review-tool](https://github.com/Black-Lights/prisma-review-tool) | 3 | MIT | Automated **PRISMA 2020** systematic-review via MCP — exactly the systematic-review gap — but very early. Watch. |
| [X1AOX1A/ZoFiles](https://github.com/X1AOX1A/ZoFiles) | 12 | MIT | Zotero-as-folders + Claude skill; clean license, low signal. |
| [kerim/zotero-mcp-skill](https://github.com/kerim/zotero-mcp-skill) | 9 | MIT | Zotero search skill; stale (last push 2025-10). |
| [wolf5996/agentic-skills](https://github.com/wolf5996/agentic-skills) | 5 | none | R + bioinformatics + sci-docs; no license, low signal. |
| [c0mm4nd/zotero-skills](https://github.com/c0mm4nd/zotero-skills) | 1 | none | Too early. |

## Backlog repos whose signal changed since CURATION.md was written

These are already tracked in [`../CURATION.md`](../CURATION.md); flagging only
the deltas so the maintainer can re-decide:

- **[poemswe/co-researcher](https://github.com/poemswe/co-researcher)** — now **101★** (MIT, active). It has crossed the ~100★ vendoring bar. Strongest backlog promotion candidate.
- **[EvoScientist/EvoSkills](https://github.com/EvoScientist/EvoSkills)** — **381★**, Apache-2.0, active (2026-05-28). Holding steady above bar; revisit for domain overlap.
- **[lingzhi227/agent-research-skills](https://github.com/lingzhi227/agent-research-skills)** — **90★**, still **no license**. Strong installs but license remains the blocker.

## Checked and intentionally **not** recommended

- **ai-boost/awesome-ai-for-science** — already bundled at `lists/awesome-ai-for-science`.
- **travisvn/awesome-claude-skills** (13k★) / **BehiSecc/awesome-claude-skills** / **GetBindu/awesome-claude-code-and-skills** — large *general* Claude-skill indexes (no license on travisvn's). Out of the research scope unless the hub wants a general-index `lists/` entry; the bundled lists are research-specific by design.
- **davila7/claude-code-templates** (27k★) — general Claude Code CLI/templates tool, not research-scoped.
- **anthropics/skills**, **affaan-m/ECC**, **VoltAgent/awesome-openclaw-skills**, **sickn33/antigravity-awesome-skills** — already assessed in CURATION.md (reference/infra, too broad to vendor blindly).

---

## Ready-to-run vendoring (⚠️ do not run until hardening is merged + scan passes)

```bash
# Tier 1. Run ONE AT A TIME, then update both READMEs, regenerate STARS.md,
# rebuild the catalog, and validate — exactly as CURATION.md prescribes.

git submodule add https://github.com/54yyyu/zotero-mcp           skills/zotero-mcp
git submodule add https://github.com/GPTomics/bioSkills          skills/bioskills
git submodule add https://github.com/ClawBio/ClawBio             skills/clawbio
git submodule add https://github.com/jaechang-hits/SciAgent-Skills skills/sciagent-skills

# After each add:
python3 scripts/check-repo.py       # validate counts / gitlinks
./scripts/count-skills.sh           # refresh the headline skill count
python3 scripts/update-stars.py     # refresh STARS.md  (needs $GITHUB_TOKEN)
python3 tools/build_catalog.py      # rebuild this catalog so the new skills are discoverable
```

> **Security gate.** Before running any `git submodule add`, clone the candidate
> to a scratch dir and grep for `curl … | sh`, `rm -rf`, base64-decoded payloads,
> credential reads (`~/.aws`, `~/.ssh`, `.env`, `GITHUB_TOKEN`), unexpected
> outbound calls, and `SKILL.md` instructions that ask the agent to hide
> behavior from the user. The README first-pass above is **not** a substitute
> for reading the code.
