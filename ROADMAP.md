# Roadmap — from skill hub to research crew

> **Goal.** A crew of research-assistant (RA) agents that work together to produce a
> complete **computer-science** or **social-science** paper — including the real
> experiments or data modeling behind it — with a human PI approving the key decisions.
>
> **目标。** 一支由多个助研智能体组成的团队，协作完成一篇**计算机科学**或**社会科学**论文，
> 包括真实的实验或数据建模，关键决策由人类 PI 把关。

Status: plan adopted 2026-11-18. Nothing under `crew/` exists yet; Phase 1 builds it.

## 1. Where we are

| Asset | Today |
|---|---|
| Vendored projects | 110 repos: 53 skill collections, 38 systems, 8 benchmarks, 11 lists |
| Skills catalogued | 6,089 `SKILL.md` files, with safety, quality, maturity and collision reports |
| Starter kits | 12 research stages × 5 collision-free skills |
| Tooling | Generated catalog, search site, weekly star refresh, `make check` |
| Reach | 261 stars, 20 forks, about 840 views per 14 days |

The hub answers "which skill should I install?". It does not answer "write me a paper".
Every part of a crew is on the shelf, but nothing assembles them, and nothing proves the
result is any good. That gap is the project.

## 2. What we are building

**Free-Research-Crew** = the hub (the supply of skills) + a **crew layer** (roles,
a handoff protocol, two paper tracks) + a **scoreboard** (evidence that it works).

### 2.1 Positioning

Three things distinguish this from the 38 systems already vendored under [`systems/`](systems/):

1. **Two tracks, one crew.** Almost every "AI scientist" targets machine-learning papers.
   We ship a social-science track (identification strategy, econometrics, public data)
   next to the CS track (baselines, ablations, benchmarks), sharing the same roles.
2. **No new runtime.** The crew is plain role files and skills that run inside the agent
   CLI the user already has (Claude Code first, then Codex). No server, no extra API bill.
   That is what "free" means here.
3. **Integrity is a feature, not a disclaimer.** Every number in the paper traces to a
   logged run, every citation is verified against a source, and the crew is tested on
   data where the true effect is zero.

### 2.2 The crew

| Role | Owns | Builds on |
|---|---|---|
| **PI** (orchestrator) | Research plan, task board, gate decisions | new |
| **Scout** | Literature search, novelty check, verified `refs.bib` | [`skills/paper-search-mcp`](skills/paper-search-mcp), [`skills/arxiv-mcp-server`](skills/arxiv-mcp-server), [`skills/zotero-mcp`](skills/zotero-mcp) |
| **Designer** | Question, hypotheses, experimental or identification design, pre-analysis plan | ideation and experiment starter kits |
| **Data RA** | Acquiring and cleaning data, data manifest with provenance | public-data MCP servers (FRED, World Bank, IMF) |
| **Experimenter** (CS) | Code, baselines, ablations, seeds, run ledger | patterns from [`systems/aideml`](systems/aideml), [`systems/paper2code`](systems/paper2code) |
| **Econometrician** (social science) | Estimation, robustness, specification curve | [StatsPAI](https://github.com/brycewang-stanford/StatsPAI), [`skills/stata-code`](skills/stata-code), [`skills/empirical-research-skills`](skills/empirical-research-skills) |
| **Writer** | Sections, LaTeX, venue templates | writing starter kit |
| **Figures RA** | Figures and tables generated from the run ledger | figures starter kit |
| **Referee** | Simulated peer review, claim-to-evidence audit, citation check | review and integrity starter kits |
| **Replicator** | Clean-environment rerun, replication package | new |

### 2.3 The protocol

Agents hand off through files in a project workspace, not through chat history:

- `plan.yaml` — question, design, task board, gate status
- `refs.bib` + `sources/` — only citations the Scout has verified
- `data/manifest.json` — every dataset with origin, hash and license
- `runs/` — one record per experiment or regression: code version, inputs, outputs
- `claims.jsonl` — every claim in the paper linked to the run or source that supports it
- `paper/` — LaTeX source, figures, tables
- `reviews/` — referee reports and responses

Four **human gates** stop the crew until the PI approves: research question, design
(before any outcome data is touched), results, and submission.

### 2.4 Planned layout

```text
crew/
  roles/        one file per role: responsibilities, inputs, outputs, skills
  protocol/     schemas for the workspace files above
  tracks/       cs/ and social-science/ playbooks
  adapters/     claude-code/ (plugin), codex/
  bench/        seed tasks and scoring scripts
gallery/        finished papers with full workspaces, cost and time
```

`skills/`, `systems/`, `benchmarks/` and `lists/` stay vendored and read-only.

## 3. Phases

### Phase 0 — Reposition (by 2026-11-25)

- [x] Rename to Free-Research-Crew (免费助研团)
- [x] Publish this roadmap; lead both READMEs with the crew goal
- [ ] New cover images and social preview that show the crew, not the catalog
- [ ] Open GitHub Discussions; file one tracking issue per phase
- [ ] Update repo topics (`multi-agent`, `social-science`, `ai-co-scientist`)

### Phase 1 — Crew v0.1: one paper per track (by 2026-12-20)

- [ ] Protocol schemas and a validator (`crew/protocol/`), covered by `make check`
- [ ] Six roles: PI, Scout, Designer, Econometrician, Experimenter, Writer
- [ ] Claude Code plugin: `/crew start`, `/crew status`, `/crew gate`
- [ ] Social-science seed: replicate a published difference-in-differences result from public data
- [ ] CS seed: a small empirical ML study that runs on a laptop CPU in under an hour
- [ ] Both seeds end in a compiled PDF and a workspace that passes the validator

**Exit test:** a new user gets from clone to a draft PDF with one command per gate.

### Phase 2 — Crew v0.5: trustworthy (by 2027-02-28)

- [ ] Remaining roles: Data RA, Figures RA, Referee, Replicator
- [ ] Integrity gates: claim-to-evidence coverage, citation verification, clean rerun
- [ ] Null-effect test: on data with no true effect, the crew must report no effect
- [ ] Codex adapter
- [ ] `crew/bench` v0: 10 CS and 10 social-science seed tasks with known answers
- [ ] Role kits: `tools/build_starter_kits.py` picks skills per role, not only per stage
- [ ] Gallery: four papers (two per track) with full workspaces, token cost and wall time

### Phase 3 — v1.0 and launch (by 2027-04-30)

- [ ] Public scoreboard on the site: bench results per model and per crew version
- [ ] Results on vendored benchmarks: [`benchmarks/discoverybench`](benchmarks/discoverybench), [`benchmarks/scienceagentbench`](benchmarks/scienceagentbench), [`benchmarks/mlagentbench`](benchmarks/mlagentbench)
- [ ] Technical report on arXiv describing the protocol and the bench results
- [ ] Launch campaign (section 5)

### Continuous — the hub

- Quarterly vendoring refresh and landscape update, as today
- Rank skills by measured results inside the crew, not only by on-disk depth
- Split the README: crew first, full catalog tables moved to `catalog/`

## 4. How we will know it works

| Measure | v0.1 | v0.5 | v1.0 |
|---|---|---|---|
| Seed tasks ending in a compiled, validated paper | 2 of 2 | 14 of 20 | 18 of 20 |
| Claims linked to a run or verified source | reported | ≥ 95% | 100% |
| Citations that resolve to a real source | reported | ≥ 99% | 100% |
| Replication tasks within tolerance of the published estimate | 1 | 7 of 10 | 9 of 10 |
| False positives on null-effect data | — | 0 | 0 |
| Clean-environment rerun reproduces every table | — | reported | 100% |

Failures are published in the gallery next to successes.

## 5. Promotion

The product is the proof. Each channel gets a finished paper and its workspace, not an
announcement.

| When | Action |
|---|---|
| Phase 0 | New covers, pinned roadmap, Discussions open, bilingual "why a crew" post |
| v0.1 | Three-minute demo video (clone to PDF); posts on Zhihu, Xiaohongshu, WeChat, X; Show HN |
| v0.5 | Gallery launch; "the crew that refuses to p-hack" write-up on the null-effect test; replication threads on r/MachineLearning and r/econometrics |
| v1.0 | arXiv report; scoreboard launch; workshop submission; listing PRs to the lists under [`lists/`](lists/) |
| Always | Credit and link upstream authors of every skill a role uses; `good first issue` labels for new seed tasks and adapters; monthly changelog |

Star targets: 1,000 at v0.1, 3,000 at v0.5, 8,000 at v1.0. Contributor target: 15 people
with a merged seed task, role or adapter by v1.0.

## 6. Responsible use

- **A human is the author.** The crew drafts; the PI decides, verifies and takes
  responsibility. Gates cannot be disabled.
- **Disclosure.** Every paper carries a generated AI-use statement. Many venues restrict
  AI-written submissions, so check the venue's policy before submitting.
- **No fabricated data or citations.** A claim with no run or source behind it fails the
  build.
- **Licenses.** Roles only depend on vendored projects with a license that permits reuse;
  see [`docs/systems-matrix-2026.md`](docs/systems-matrix-2026.md).

## 7. Open decisions

1. **First runtime:** Claude Code plugin first, Codex second (assumed above).
2. **Seed papers:** which published result to replicate for the social-science seed, and
   which small ML question for the CS seed.
3. **Compute for the CS track:** laptop-only seeds (assumed), or a GPU budget for larger ones.
4. **Venue submissions:** whether gallery papers are ever submitted, or stay as demonstrations.

Comments welcome in issues or Discussions.
