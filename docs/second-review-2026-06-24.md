# Second-Review Log — 2026-06-24 (fresh-finds batch)

Executes a second review of the candidates surfaced by the 2026-06-23 scripted
discovery sweep (the "Fresh finds" section of
[`../catalog/DISCOVERY.md`](../catalog/DISCOVERY.md)). Continues the cadence of
[`second-review-2026-06-23.md`](second-review-2026-06-23.md).

Each candidate was checked live with the GitHub API, shallow-cloned to a scratch
dir, and scanned with the repo's own tool focused on executable contexts:

```bash
python3 scripts/scan-skill-safety.py <clone> --max-findings 0 \
    --fail-on none --context skill,script,other
```

**All eight code-bearing candidates scanned clean (0 high+ findings)** — a
notably clean batch. Verdicts therefore turn on *scope fit*, *license*,
*redundancy with already-vendored projects*, and *collision surface*, not safety.

Reviewer: automated maintenance pass, 2026-06-24. Nothing here is vendored —
these are recommendations for a future approved batch (one project per PR).

## Verdicts at a glance

| Candidate | ⭐ | License | Scan | SKILL.md | Verdict |
|---|---:|---|---|---:|---|
| [HKUDS/DeepCode](https://github.com/HKUDS/DeepCode) | 15.8k | MIT | clean | 7 | **vendor-candidate** (systems) — lead |
| [Alibaba-NLP/DeepResearch](https://github.com/Alibaba-NLP/DeepResearch) | 19.5k | Apache-2.0 | clean | 0 | **vendor-candidate** (systems) |
| [uditgoenka/autoresearch](https://github.com/uditgoenka/autoresearch) | 5.2k | MIT | clean | 5 | **vendor-candidate** (skills) |
| [webfuse-com/awesome-autoresearch](https://github.com/webfuse-com/awesome-autoresearch) | 2.3k | NOASSERTION | n/a (md) | — | **vendor-candidate** (lists) |
| [tmgthb/Autonomous-Agents](https://github.com/tmgthb/Autonomous-Agents) | 1.3k | MIT | n/a (md) | — | **vendor-candidate** (lists) |
| [VoltAgent/awesome-ai-agent-papers](https://github.com/VoltAgent/awesome-ai-agent-papers) | 1.5k | MIT | n/a (md) | — | **vendor-candidate** (lists) |
| [MiroMindAI/MiroThinker](https://github.com/MiroMindAI/MiroThinker) | 8.3k | Apache-2.0 | clean | 0 | **hold** (deep-research redundancy) |
| [SkyworkAI/DeepResearchAgent](https://github.com/SkyworkAI/DeepResearchAgent) | 3.5k | MIT | clean | 1 | **hold** (deep-research redundancy) |
| [OpenRaiser/NanoResearch](https://github.com/OpenRaiser/NanoResearch) | 1.5k | MIT | clean | 16 | **hold** (smaller; redundancy) |
| [Leey21/awesome-ai-research-writing](https://github.com/Leey21/awesome-ai-research-writing) | 29.4k | **none** | n/a (md) | — | **hold** (no license) |
| [trailofbits/skills](https://github.com/trailofbits/skills) | 5.8k | CC-BY-SA-4.0 | clean | 74 | **hold** (scope: security, not science) |
| [alirezarezvani/claude-skills](https://github.com/alirezarezvani/claude-skills) | 18.9k | MIT | clean | 763 | **hold** (broad dump; collision surface) |

## Recommended next batch (if approved)

Add **one project per PR**, in this order; do not batch:

1. **HKUDS/DeepCode** → `systems/deepcode` — MIT, clean, distinct capability
   (Paper2Code + Text2Web/Backend). Complements the bundled `systems/paper2code`
   (note the overlap in the README). Same org as the already-vendored
   `ai-researcher` / `auto-deep-research`.
2. **uditgoenka/autoresearch** → `skills/autoresearch` — MIT, clean, on-theme
   (Karpathy-style autonomous goal-directed iteration as a Claude skill).
3. **webfuse-com/awesome-autoresearch** + **tmgthb/Autonomous-Agents** →
   `lists/` — both directly on-theme; tmgthb is MIT and daily-updated.

That single round adds one system, one skill, and two lists — all scan-clean —
without piling on redundant deep-research agents.

## Per-candidate notes

### Vendor-candidates

- **HKUDS/DeepCode (15.8k, MIT).** Open agentic coding: paper→code, text→web,
  text→backend. 7 SKILL.md. The strongest pick — adds a capability the hub only
  partially covers via `paper2code`. Confirm the README overlap note before
  vendoring.
- **Alibaba-NLP/DeepResearch (19.5k, Apache-2.0).** Tongyi Deep Research; the
  most-starred fresh find. 0 SKILL.md (a system, not a skill pack). **Confirm
  it ships a runnable agent rather than only model weights/eval harness** before
  vendoring — the line between "deep-research *agent*" and "model release" matters
  for this hub. If it is a model release, prefer DeepCode.
- **uditgoenka/autoresearch (5.2k, MIT).** Claude Autoresearch Skill; 5 SKILL.md;
  active (pushed 2026-06-23). Clean fit for `skills/`.
- **Lists** — `webfuse-com/awesome-autoresearch` (NOASSERTION; on-theme),
  `tmgthb/Autonomous-Agents` (MIT; daily-updated paper list),
  `VoltAgent/awesome-ai-agent-papers` (MIT; 2026 agent papers). All low-risk
  markdown indexes. Adding 1–2 is enough; the hub already has 7 lists.

### Holds

- **MiroThinker / DeepResearchAgent / NanoResearch** — all clean and licensed,
  but the hub already vendors a deep dense of deep-research systems (deer-flow,
  gpt-researcher, open-deep-research ×2, local-deep-research, storm, paper-qa,
  auto-deep-research, auto-deep-researcher-24x7). Adding more without a specific
  gap raises redundancy. Hold unless one fills a concrete hole.
- **Leey21/awesome-ai-research-writing (29.4k, no license).** High signal, but
  no license is a hard blocker per the curation bar — confirm/ask upstream first.
- **trailofbits/skills (5.8k, CC-BY-SA-4.0).** High-quality, but **security
  research** (vuln detection, exploitation, audit), not autonomous *science*.
  Out of the hub's stated scope. CC-BY-SA-4.0 is also a content/share-alike
  license. Revisit only if the hub deliberately broadens scope; otherwise note
  in the candidate backlog.
- **alirezarezvani/claude-skills (18.9k, MIT).** 763 SKILL.md — a broad,
  general-purpose dump (30+ agents, 70+ commands, 330+ skills). Per
  `CONTRIBUTING.md` ("avoid broad skill dumps unless a clear reason"), the
  collision/redundancy surface outweighs the research relevance. Hold.

## Cross-link

These verdicts update the "Fresh finds" section of
[`../catalog/DISCOVERY.md`](../catalog/DISCOVERY.md); the candidates remain there
as tracked, none vendored.
