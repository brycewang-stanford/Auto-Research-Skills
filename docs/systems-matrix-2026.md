# Autonomous-Research Systems — Comparison Matrix (2026)

A decision-useful cross-comparison of the **32 systems** vendored under
[`../systems/`](../systems/), grouped by the five-layer field map in
[`landscape-2026.md`](landscape-2026.md). It pairs each system's *capability
shape* (tier, domain, approach) with its *reproduction friction* (license +
staleness), the dimension argued in [`reproducibility-2026-06-23.md`](reproducibility-2026-06-23.md).

Stars / license / last-push are from the
[`../catalog/HEALTH.md`](../catalog/HEALTH.md) snapshot (refresh with
`make health-report`); treat them as a point-in-time reading, not a live feed.

## Reading the "Repro" column

A coarse reproduction-readiness flag, derived purely from measurable upstream
hygiene — *not* a judgment of scientific quality:

- 🟢 — OSI license **and** pushed within ~12 months (legally reusable, plausibly
  still runs against current model APIs).
- 🟡 — `NOASSERTION` license (GitHub can't confirm an OSI license) **or** an
  OSI-licensed repo gone stale (>12 months no push).
- 🔴 — **no license at all** → all-rights-reserved by default; a legal blocker to
  rerun-and-extend regardless of how good the science is.

Tally across the shelf: **20 🟢 · 7 🟡 · 5 🔴**. The 5 🔴 (`ai-researcher`,
`auto-deep-research`, `autosurvey`, `popper`, `sibyl-system`) are the priority
for upstream license issues.

---

## Tier 1 — Full-autonomy "AI scientist" (idea → paper)

| System | ⭐ | License | Last push | Repro | Distinctive approach |
|---|---:|---|---|:--:|---|
| [`systems/ai-scientist`](../systems/ai-scientist) | 14.1k | NOASSERTION | 6mo | 🟡 | The original end-to-end pipeline; template-driven. |
| [`systems/ai-scientist-v2`](../systems/ai-scientist-v2) | 6.7k | NOASSERTION | 6mo | 🟡 | Agentic **tree search**, no templates; first to clear a workshop review. |
| [`systems/ai-researcher`](../systems/ai-researcher) | 5.5k | none | 8mo | 🔴 | Two-level input (idea, or just reference papers); Dockerized. |
| [`systems/autoresearchclaw`](../systems/autoresearchclaw) | 13.6k | MIT | 20d | 🟢 | Claude-native autonomous research loop; very active. |
| [`systems/agent-laboratory`](../systems/agent-laboratory) | 5.7k | MIT | 10mo | 🟢 | Role-specialized "lab" phases (review → experiment → write). |
| [`systems/autonomous-researcher`](../systems/autonomous-researcher) | 803 | MIT | 7mo | 🟢 | Lightweight single-agent researcher. |
| [`systems/sibyl-system`](../systems/sibyl-system) | 257 | none | 3mo | 🔴 | Self-evolving, Claude-Code-native. |
| [`systems/auto-research`](../systems/auto-research) | 1 | MIT | 1mo | 🟢 | Generalist "AI Scientist" with a UI (the UI repo). |

## Tier 2 — Deep-research / literature-synthesis engines

| System | ⭐ | License | Last push | Repro | Distinctive approach |
|---|---:|---|---|:--:|---|
| [`systems/deer-flow`](../systems/deer-flow) | 74.1k | MIT | 0d | 🟢 | ByteDance; the most-starred deep-research framework here. |
| [`systems/storm`](../systems/storm) | 29.3k | MIT | 8mo | 🟢 | Stanford; outline-then-write with simulated expert dialogue. |
| [`systems/gpt-researcher`](../systems/gpt-researcher) | 27.9k | Apache-2.0 | 0d | 🟢 | Planner/executor web research with cited reports. |
| [`systems/deep-research`](../systems/deep-research) | 19.2k | MIT | 2mo | 🟢 | Minimal, hackable deep-research loop. |
| [`systems/open-deep-research`](../systems/open-deep-research) | 11.8k | MIT | 2d | 🟢 | LangChain reference implementation. |
| [`systems/local-deep-research`](../systems/local-deep-research) | 8.6k | MIT | 0d | 🟢 | Self-hostable / local-model friendly. |
| [`systems/open-deep-research-firecrawl`](../systems/open-deep-research-firecrawl) | 6.3k | NOASSERTION | 1y1m | 🟡 | Firecrawl-backed crawl+synthesis; stale + unclear license. |
| [`systems/web-researcher-ollama`](../systems/web-researcher-ollama) | 3.0k | MIT | 1y6m | 🟡 | Local-LLM web researcher; notably stale. |
| [`systems/auto-deep-research`](../systems/auto-deep-research) | 1.6k | none | 8mo | 🔴 | HKUDS open deep-research; no license. |
| [`systems/auto-deep-researcher-24x7`](../systems/auto-deep-researcher-24x7) | 1.2k | Apache-2.0 | 21d | 🟢 | Leader–worker, constant-memory 24/7 runner. |
| [`systems/autosurvey`](../systems/autosurvey) | 470 | none | 1y4m | 🔴 | Multi-stage automated literature survey; no license + stale. |
| [`systems/paper-qa`](../systems/paper-qa) | 8.8k | Apache-2.0 | 12d | 🟢 | FutureHouse; high-accuracy RAG QA over a paper corpus. |

## Tier 3 — Domain-science agents

| System | ⭐ | License | Last push | Repro | Domain / approach |
|---|---:|---|---|:--:|---|
| [`systems/biomni`](../systems/biomni) | 3.2k | Apache-2.0 | 1d | 🟢 | Biomedical; broad tool integration. |
| [`systems/chemcrow`](../systems/chemcrow) | 928 | MIT | 1y6m | 🟡 | Chemistry tool-use; stale (tool integrations likely rotted). |
| [`systems/robin`](../systems/robin) | 578 | Apache-2.0 | 2mo | 🟢 | FutureHouse; validated a dry-AMD drug candidate. |
| [`systems/sciagents`](../systems/sciagents) | 618 | Apache-2.0 | 1y1m | 🟡 | Materials/science multi-agent discovery; stale. |
| [`systems/coscientist`](../systems/coscientist) | 206 | NOASSERTION | 10mo | 🟡 | Autonomous chemistry (Nature 2023). |
| [`systems/virtual-lab`](../systems/virtual-lab) | 694 | MIT | 5mo | 🟢 | LLM "research lab" of specialized agents (biomedical). |
| [`systems/popper`](../systems/popper) | 275 | none | 1y1m | 🔴 | Agentic sequential-falsification hypothesis testing (Stanford SNAP). |

## Tier 4 — Experiment / paper-to-code agents

| System | ⭐ | License | Last push | Repro | Approach |
|---|---:|---|---|:--:|---|
| [`systems/deepcode`](../systems/deepcode) | 15.8k | MIT | 1mo | 🟢 | Open agentic coding: Paper2Code + Text2Web + Text2Backend (vendored 2026-06-24). |
| [`systems/aideml`](../systems/aideml) | 1.3k | MIT | 1mo | 🟢 | ML engineering as code-optimization tree search. |
| [`systems/curie`](../systems/curie) | 361 | Apache-2.0 | 8mo | 🟢 | Rigorous, reproducible ML experimentation harness. |
| [`systems/paper2code`](../systems/paper2code) | 4.7k | Apache-2.0 | 3mo | 🟢 | Turns an ML paper into a runnable code repo. |

## Tier 5 — Research-community simulation

| System | ⭐ | License | Last push | Repro | Approach |
|---|---:|---|---|:--:|---|
| [`systems/research-town`](../systems/research-town) | 208 | Apache-2.0 | 1d | 🟢 | ICML 2025; simulates a *community* of researchers, not one agent. |

---

## What the matrix shows

1. **Deep-research engines (Tier 2) are the healthiest layer** — almost all OSI-
   licensed and actively maintained (deer-flow, gpt-researcher, open-deep-research,
   local-deep-research, paper-qa all pushed within days). This is the layer that
   is genuinely production-usable today.
2. **Full-autonomy "AI scientists" (Tier 1) carry the most reproduction friction
   relative to their fame.** The two most-starred (AI-Scientist 14.1k, v2 6.7k)
   are NOASSERTION; AI-Researcher (5.5k) and Sibyl have no license. The
   capability headlines outrun the hygiene.
3. **Domain-science agents (Tier 3) skew stale.** chemcrow, sciagents, coscientist,
   and popper are all >10 months idle — expected for academic artifacts tied to a
   paper, but a reason to treat them as references rather than live tools.
4. **The 5 🔴 no-license repos are the clearest action item** — a one-line
   upstream license would move each from "study-only" to "reusable".

For the narrative behind these tiers see [`landscape-2026.md`](landscape-2026.md);
for why hygiene is a reproducibility issue see
[`reproducibility-2026-06-23.md`](reproducibility-2026-06-23.md).
