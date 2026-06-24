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

Curated lists feeding discovery live in [`lists/`](../lists/).

---

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

## How this map is maintained

New entrants are surfaced by periodic GitHub landscape sweeps, cross-checked
against [`catalog/skills.json`](../catalog/skills.json) and
[`STARS.md`](../STARS.md) to avoid duplicates, recorded in
[`catalog/DISCOVERY.md`](../catalog/DISCOVERY.md), and vetted through the
[`CURATION.md`](../CURATION.md) second-review process before vendoring. The most
recent batch is logged in [`vendoring-2026-06-23.md`](vendoring-2026-06-23.md).
