# The Autonomous-Research Landscape — 2026 Field Map

A maintainer's map of the autonomous / AI-assisted research ecosystem, written
to explain *why* this hub is organized into `skills/`, `systems/`,
`benchmarks/`, and `lists/`, and where each vendored project sits in the wider
field. Star counts are approximate (see [`STARS.md`](../STARS.md) for the live
leaderboard); treat this as a conceptual map, not a ranking.

The field has stratified into five layers. The first three are heavyweight
*systems*; the fourth is the composable *skills* layer this hub specializes in;
the fifth is the *evaluation* substrate that keeps everyone honest.

---

## 1. Full-autonomy "AI Scientist" systems

End-to-end: read literature → form a hypothesis → write and run code → analyze
→ draft a paper, with minimal human intervention.

> For a side-by-side of all 38 vendored systems (tier, domain, license,
> staleness, reproduction-readiness) see the
> [systems comparison matrix](systems-matrix-2026.md).

| Project | In hub | Note |
|---|---|---|
| SakanaAI/AI-Scientist + v2 | [`systems/ai-scientist`](../systems/ai-scientist), [`systems/ai-scientist-v2`](../systems/ai-scientist-v2) | v2 uses agentic tree search and dropped v1's templates; first machine-authored paper to clear a workshop peer review. |
| HKUDS/AI-Researcher | [`systems/ai-researcher`](../systems/ai-researcher) | NeurIPS 2025 spotlight; two-level input (give an idea, or just reference papers). |
| SamuelSchmidgall/AgentLaboratory | [`systems/agent-laboratory`](../systems/agent-laboratory) | Agent "lab" with role-specialized phases. |
| WecoAI/aideml | [`systems/aideml`](../systems/aideml) | Treats ML engineering as code-optimization search. |
| ulab-uiuc/research-town | [`systems/research-town`](../systems/research-town) | Simulates a *community* of researchers, not a single agent. |

**Maintainer's read:** demos outrun reproducibility. The honest 2026 consensus
(see the arXiv "Why LLMs Aren't Scientists Yet" line of work) is that these
systems are strong scaffolds but weak on genuine novelty judgment and
experimental rigor. Vendored for study and capability reference, not as
turn-key paper generators. See [`reproducibility-2026-06-23.md`](reproducibility-2026-06-23.md)
for an evidence-grounded critique (a third of the `systems/` shelf carries a
license gap or staleness flag before the science is even in question).

## 2. Deep-research / literature-synthesis engines

No wet experiments — focused on retrieval, synthesis, and cited reports. The
most *mature and immediately useful* layer.

| Project | In hub |
|---|---|
| bytedance/deer-flow | [`systems/deer-flow`](../systems/deer-flow) |
| stanford-oval/storm | [`systems/storm`](../systems/storm) |
| assafelovic/gpt-researcher | [`systems/gpt-researcher`](../systems/gpt-researcher) |
| langchain-ai/open_deep_research | [`systems/open-deep-research`](../systems/open-deep-research) |
| LearningCircuit/local-deep-research | [`systems/local-deep-research`](../systems/local-deep-research) |
| Future-House/paper-qa | [`systems/paper-qa`](../systems/paper-qa) |
| AutoSurveys/AutoSurvey | [`systems/autosurvey`](../systems/autosurvey) |

## 3. Domain-science agents

Vertical tool-use + reasoning, often the highest real-world research value.

| Project | In hub | Domain |
|---|---|---|
| (ChemCrow) | [`systems/chemcrow`](../systems/chemcrow) | chemistry tool-use |
| snap-stanford/Biomni | [`systems/biomni`](../systems/biomni) | biomedical |
| Future-House/robin | [`systems/robin`](../systems/robin) | drug discovery (validated a dry-AMD candidate) |
| gomesgroup/coscientist | [`systems/coscientist`](../systems/coscientist) | autonomous chemistry (Nature 2023) |
| Just-Curieous/Curie | [`systems/curie`](../systems/curie) | rigorous, reproducible ML experiments |
| **snap-stanford/POPPER** | [`systems/popper`](../systems/popper) | **automated hypothesis testing via sequential falsification (vendored 2026-06-23)** |

## 4. Composable agent skills ⭐ (this hub's focus)

The fastest-growing, most fragmented layer: portable, plug-in skills for
Claude Code / Codex / any LLM agent. This is where Auto-Research-Skills lives —
see [`README.md`](../README.md) for the full vendored set. Highlights:

- [`skills/academic-research-skills`](../skills/academic-research-skills) — research → write → review → revise → finalize.
- [`skills/scientific-agent-skills`](../skills/scientific-agent-skills) and [`skills/claude-scientific-writer`](../skills/claude-scientific-writer) (K-Dense).
- [`skills/ai-research-skills`](../skills/ai-research-skills) (Orchestra) — open library across 20+ categories.
- [`skills/feynman`](../skills/feynman), [`skills/claude-scholar`](../skills/claude-scholar) — multi-tool research assistants.
- [`skills/zotero-mcp`](../skills/zotero-mcp), [`skills/arxiv-mcp-server`](../skills/arxiv-mcp-server) — MCP-server-as-skill reference/library access (both vendored).
- [`skills/claude-research`](../skills/claude-research) — PhD-grade infra: skills + agents + hooks + rules (vendored 2026-06-23).
- [`skills/claude-skills-journalism`](../skills/claude-skills-journalism) — verification / FOIA / data-journalism crossover (vendored 2026-06-23).

**Tension to watch:** name collisions across collections. Installing every
bundle into one agent profile is unsafe; see
[`catalog/collisions.json`](../catalog/collisions.json).

## 5. Evaluation benchmarks

The substrate that separates a demo from a result. Vendoring these is a
deliberate differentiator — most awesome-lists skip evaluation entirely.

| Benchmark | In hub | Measures |
|---|---|---|
| OSU-NLP-Group/ScienceAgentBench | [`benchmarks/scienceagentbench`](../benchmarks/scienceagentbench) | data-driven scientific tasks |
| snap-stanford/MLAgentBench | [`benchmarks/mlagentbench`](../benchmarks/mlagentbench) | end-to-end ML experimentation |
| allenai/discoverybench | [`benchmarks/discoverybench`](../benchmarks/discoverybench) | data-driven discovery |
| Future-House/aviary | [`benchmarks/aviary`](../benchmarks/aviary) | language-agent gym of scientific tasks |
| Ayanami0730/deep_research_bench | [`benchmarks/deep-research-bench`](../benchmarks/deep-research-bench) | deep-research report quality + citation accuracy *(added 2026-10)* |
| apexin-ai/ASI-Bench | [`benchmarks/asi-bench`](../benchmarks/asi-bench) | project-level research with guidance progressively removed *(added 2026-10)* |
| allenai/asta-bench | [`benchmarks/asta-bench`](../benchmarks/asta-bench) | 2,400+ problems across the discovery process *(added 2026-10)* |
| scicode-bench/SciCode | [`benchmarks/scicode`](../benchmarks/scicode) | research-grade scientific coding *(added 2026-10)* |

Curated lists feeding discovery live in [`lists/`](../lists/).

---

## Q3 2026 update (July → October)

What changed since the June map, and what this hub did about it. Facts below
were checked against the linked primary sources on 2026-10-19/20; items marked
*(unconfirmed)* rest on secondary coverage only.

### What moved in the field

- **Big labs now ship science skill packs.** Anthropic launched the *Claude
  Science* beta on 2026-06-30, a research workbench with 60+ curated skills and
  connectors, a reviewer agent that checks citations and calculations, and
  HPC/Modal job dispatch ([announcement](https://www.anthropic.com/news/claude-science-ai-workbench)).
  Google DeepMind published [`science-skills`](https://github.com/google-deepmind/science-skills)
  (AlphaGenome, AFDB, UniProt and 30+ databases), and NVIDIA published
  [`bionemo-agent-toolkit`](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit)
  (BioNeMo NIM skills). Open-source "Claude Science" clones followed
  ([`aipoch/open-science`](https://github.com/aipoch/open-science),
  [`K-Dense-AI/k-dense-byok`](https://github.com/K-Dense-AI/k-dense-byok)).
- **AI scientists are being rebuilt as orchestration over coding agents.**
  Sakana's [AI-Scientist-v3](https://github.com/SakanaAI/AI-Scientist-v3) ("The
  Agentic Scientist", [arXiv 2610.18933](https://arxiv.org/abs/2610.18933)) is a
  set of skills that drive Claude Code/Codex through a Dockerized six-phase
  pipeline; the paper reports a development version co-produced a paper accepted
  at ALIFE 2026. [alphaXiv/OpenResearch](https://github.com/alphaXiv/OpenResearch),
  [EvoMap/AutoResearch](https://github.com/EvoMap/AutoResearch),
  [RUC-NLPIR/Arbor](https://github.com/RUC-NLPIR/Arbor) and
  [sapientinc/PRAXIST](https://github.com/sapientinc/PRAXIST) follow the same
  shape. The hub's thesis — *skills over monoliths* — is now the mainstream.
- **New benchmarks agree: end-to-end autonomy is still weak.**
  [ResearchClawBench](https://arxiv.org/abs/2606.07591) (7 agents × 17 LLMs; best
  agent ≈21.5/100) and [ASI-Bench](https://arxiv.org/abs/2608.17271) (scores fall
  50.9 → 29.1 → 26.6 as human guidance is removed) both put project-level
  autonomous research far from solved. Microsoft's
  [SciAgentArena](https://www.microsoft.com/en-us/research/publication/benchmarking-ai-agents-for-addressing-scientific-challenges-across-scales/)
  finds agents strong on well-specified analysis and weak on self-directed
  exploration.
- **Venues are hardening AI-use policy.** NeurIPS 2026's Position Paper Track
  ran every submission through an AI-text detector and desk-rejected 178 of 969
  ([NeurIPS blog, 2026-06-02](https://blog.neurips.cc/2026/06/02/ai-generated-papers-in-the-neurips-2026-position-paper-track/)).
  ICLR 2027 requires a mandatory AI-use disclosure section and treats substantial
  LLM-produced falsehoods as a Code-of-Ethics violation
  ([policy](https://iclr.cc/Conferences/2027/AIPolicyForAuthors); deadline
  details *(unconfirmed)*). Integrity skills — citation verification,
  disclosure drafting, anti-fabrication audits — are now table stakes.
- **Skill supply-chain attacks went from theory to incident.** Unit 42 documented
  malicious ClawHub skills that passed marketplace scanning, one padding its
  README to ~22 MB to evade scanners
  ([Unit 42, 2026-06-23](https://unit42.paloaltonetworks.com/openclaw-ai-supply-chain-risk/));
  a CSA research note tallies the "ClawHavoc" campaign and payload-free
  metadata/semantic attacks that scanners miss
  ([CSA, 2026-06-24](https://labs.cloudsecurityalliance.org/research/csa-research-note-ai-skill-supply-chain-attacks-20260624-csa/)).
  We also observed an uncredited re-upload of a vendored pack and star-farmed
  look-alike repos during discovery (see the
  [vendoring log](vendoring-2026-10-20.md#rejected--suspicious)).
- **The Agent Skills format is the de-facto standard.** [agentskills.io](https://agentskills.io)
  lists ~46 compatible clients (Claude Code, ChatGPT/Codex, Gemini CLI, Cursor,
  Copilot, OpenClaw, Hermes, …); the spec itself only received clarifications
  (e.g. `metadata` frontmatter, 2026-08-03) — no breaking release.
- **Per-venue skill packs exploded.** The bundled
  [`franklee-academic-research-skills`](../skills/franklee-academic-research-skills)
  absorbed *Awesome-Journal-Skills* (95 per-journal packs, ~1,600 skills for AER,
  Econometrica, Cell, Nature, AAAI, …), taking the hub from 3,433 to 5,897
  `SKILL.md` files on a routine submodule bump; [CCFA-Skills](https://github.com/mikubaka88/CCFA-Skills)
  does the same for top CS venues. Breadth is no longer scarce — **selection
  is**, which is why this round added [`catalog/STARTER-KITS.md`](../catalog/STARTER-KITS.md).

### What the hub did (2026-10-20 round)

- Bumped all 87 existing submodules to upstream HEAD, then vendored **21 new
  projects** (9 skills, 6 systems, 4 benchmarks, 2 lists) after license, size
  and focused safety review → **108 repos, 6,087 `SKILL.md` files**. Decisions,
  scan triage and list-only/rejected calls are in
  [`vendoring-2026-10-20.md`](vendoring-2026-10-20.md).
- Filled the benchmark gap for **deep research** (`deep-research-bench`),
  **project-level autonomy** (`asi-bench`), **discovery breadth** (`asta-bench`)
  and **scientific coding** (`scicode`).
- Added **research-stage starter kits**: one collision-free, safety-gated kit
  of five skills per stage, installable in one command.

## Cross-cutting trends (2026)

1. **Autonomy is retreating, not advancing.** The narrative moved from
   "fully autonomous AI scientist" to *human-in-the-loop semi-autonomy*
   (e.g. claude-scholar markets itself as "semi-automated"). Full autonomy
   proved unreliable on novelty and rigor, and expensive.
2. **Monolithic systems → composable skills.** Heavy monorepos are giving way
   to lightweight, cross-agent, pluggable skills + MCP. This hub rides that
   main line.
3. **Safety is a real risk surface, not a checkbox.** Install scripts, hooks,
   and credential handling are pervasive across skill repos; see
   [`catalog/SAFETY.md`](../catalog/SAFETY.md) and the scanner in
   [`scripts/scan-skill-safety.py`](../scripts/scan-skill-safety.py).
4. **Aggregation with provenance is the missing layer.** Awesome-lists list
   links; skill packs ship loose skills; almost nobody offers a *reproducible*
   aggregation with dedup, collision detection, safety scanning, and quality
   grading. That is this hub's differentiated position.
5. **Selection beats breadth.** With per-venue packs and lab-published packs,
   the bottleneck moved from "is there a skill for X?" to "which few skills for
   X are deep, safe, and non-colliding?" — see
   [`catalog/STARTER-KITS.md`](../catalog/STARTER-KITS.md) and
   [`catalog/MATURITY.md`](../catalog/MATURITY.md).
6. **Provenance is a security control.** Marketplace scanning demonstrably
   misses payload-free and metadata-only attacks; pinning to reviewed upstream
   commits (as submodules do) plus re-scanning on every bump is the practical
   defense.

## How this map is maintained

New entrants are surfaced by periodic GitHub landscape sweeps, cross-checked
against [`catalog/skills.json`](../catalog/skills.json) and
[`STARS.md`](../STARS.md) to avoid duplicates, recorded in
[`catalog/DISCOVERY.md`](../catalog/DISCOVERY.md), and vetted through the
[`CURATION.md`](../CURATION.md) second-review process before vendoring. The most
recent batch is logged in [`vendoring-2026-10-20.md`](vendoring-2026-10-20.md)
(earlier: [`vendoring-2026-06-23.md`](vendoring-2026-06-23.md)).
