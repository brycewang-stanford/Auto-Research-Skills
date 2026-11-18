# Roadmap — from skill hub to research crew

> **Goal.** A crew of research-assistant (RA) agents that work together to produce a
> complete **computer-science** or **social-science** paper — including the real
> experiments or data modeling behind it — with a human PI approving the key decisions.
>
> **目标。** 一支由多个助研智能体组成的团队，协作完成一篇**计算机科学**或**社会科学**论文，
> 包括真实的实验或数据建模，关键决策由人类 PI 把关。

Status: plan adopted 2026-11-18 and compressed into a one-week sprint the same day
(section 3). The crew is built under [`crew/`](crew/); the first two papers are in progress
in [`gallery/`](gallery/).

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
| **Reviewer** | Attacks every other role's work before each gate; decides what the evidence supports; can run on another provider's model | review design from [`skills/aris`](skills/aris) |
| **Replicator** | Clean-environment rerun, replication package | new |

### 2.3 The protocol

Agents hand off through files in a project workspace, not through chat history:

- `plan.json` — question, design, task board, gate status
- `refs.bib` + `sources/` — only citations the Scout has verified
- `data/manifest.json` — every dataset with origin, hash and license
- `runs/` — one record per experiment or regression: code version, inputs, outputs
- `claims.jsonl` — every claim in the paper linked to the run or source that supports it
- `paper/` — LaTeX source, figures, tables
- `reviews/` — the Reviewer's verdicts, findings and rulings on rebuttals

Four **human gates** stop the crew until the PI approves: research question, design
(before any outcome data is touched), results, and submission.

Three kinds of judgment are kept apart. The tool checks *what happened* (the run finished,
the number matches). The Reviewer, never the role that did the work, judges *whether it is
good*, reading the files and not the author's summary. The human decides *whether to go
on*. A gate cannot be approved while the Reviewer has an open critical finding, unless the
human overrules it on the record. Full specification: [`crew/PROTOCOL.md`](crew/PROTOCOL.md).

### 2.4 Layout

```text
crew/           a Claude Code plugin
  agents/       one file per role
  skills/       /crew:start, /crew:status, /crew:gate
  scripts/      crew.py, the workspace tool that enforces the protocol
  tracks/       cs and social-science playbooks
  templates/    LaTeX paper skeleton
  bench/        seed tasks and answer keys
gallery/        (planned) finished papers with full workspaces, cost and time
```

`skills/`, `systems/`, `benchmarks/` and `lists/` stay vendored and read-only.

## 3. One-week sprint (2026-11-18 → 2026-11-25)

On 2026-11-18 the plan was compressed from five months into one week. Everything that
does not need outside people is scheduled inside the week. Running a paper needs the
human PI at four gates, so the papers move at the speed of those approvals.

| Day | Date | Deliverables | Status |
|---|---|---|---|
| 1 | Wed 11-18 | Rename; roadmap; crew v0.1 plugin and workspace tool; Reviewer modeled on ARIS; Data RA, Figures RA, Replicator; clean rerun (`crew.py rerun`) as a submission requirement; cross-family review through the Codex CLI (`cross_review.py`); both seed papers started in [`gallery/`](gallery/) | done except the seed papers, which are in progress |
| 2 | Thu 11-19 | Question and design gates for both seeds; null-effect seed (true effect zero; the crew must not find one); Codex adapter | done early (11-18): all three question gates and all three design gates approved; null-effect seed and Codex adapter built |
| 3 | Fri 11-20 | Data and analysis runs; results reviews; results gates | in progress (11-18): two of three results gates approved; 401(k) main estimates running |
| 4 | Sat 11-21 | Figures, papers, clean reruns, submission gates → first two gallery papers with token cost and wall time | |
| 5 | Sun 11-22 | Null-effect seed run; three more seeds (six in total) with sourced answer keys; bench scorer; scoreboard page on the site | |
| 6 | Mon 11-23 | Run further seeds as gates allow; role kits (skills picked per role from the hub) | |
| 7 | Tue 11-24 | Launch kit: demo video, bilingual posts (Zhihu, Xiaohongshu, WeChat, X), Show HN draft, technical-report draft, new cover images | |
| 8 | Wed 11-25 | Release v0.5; GitHub Discussions; tracking issues; the human posts the launch | |

### Moved out of the week

These need outside people or more time than a week, so they stay on the list without a date:

- Results on the vendored benchmarks ([`benchmarks/discoverybench`](benchmarks/discoverybench),
  [`benchmarks/scienceagentbench`](benchmarks/scienceagentbench),
  [`benchmarks/mlagentbench`](benchmarks/mlagentbench))
- 20 seed tasks (the week targets six)
- arXiv submission of the technical report (the week produces the draft; submitting is the human's call)
- Workshop submission, listing PRs to other awesome lists, contributor growth

### Continuous — the hub

- Quarterly vendoring refresh and landscape update, as today
- Rank skills by measured results inside the crew, not only by on-disk depth

## 4. How we will know it works

| Measure | End of week (11-25) | Later |
|---|---|---|
| Seed tasks ending in a compiled, validated paper | 2 of 2 started seeds, plus the null-effect seed | 18 of 20 |
| Claims linked to a run or verified source | 100% (enforced by the tool) | 100% |
| Citations with a verification record | 100% (enforced by the tool) | 100% |
| Replication seeds within tolerance of the published estimate | reported, pass or fail | 9 of 10 |
| False positives on null-effect data | 0 | 0 |
| Clean rerun reproduces every run | 100% (required for submission) | 100% |
| Reviews run cross-family | reported | all |

Failures are published in the gallery next to successes.

## 5. Promotion

The product is the proof. Each channel gets a finished paper and its workspace, not an
announcement.

| When | Action |
|---|---|
| Day 4–5 | First gallery papers published with their full workspaces and the Reviewer's critiques |
| Day 7 | Demo video (clone to PDF); bilingual write-up "a research crew with a reviewer that never lets up"; drafts for Zhihu, Xiaohongshu, WeChat, X and Show HN in [`docs/launch/`](docs/launch/) |
| Day 8 | Release v0.5; Discussions open; the human posts the launch |
| After | "The crew that refuses to p-hack" write-up on the null-effect seed; replication threads on r/MachineLearning and r/econometrics; arXiv report; listing PRs to the lists under [`lists/`](lists/) |
| Always | Credit and link upstream authors of every skill a role uses, starting with [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep); `good first issue` labels for new seed tasks and adapters |

Star targets: 1,000 within a month of launch, 3,000 within three months. Contributor
target: 15 people with a merged seed task, role or adapter within three months.

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
2. **Seed papers:** decided 2026-11-18 — both seeds use machine learning (see Phase 1).
3. **Compute for the CS track:** laptop-only seeds (assumed), or a GPU budget for larger ones.
4. **Venue submissions:** decided 2026-11-18 — gallery papers stay as demonstrations and
   are not submitted to venues.

Comments welcome in issues or Discussions.
