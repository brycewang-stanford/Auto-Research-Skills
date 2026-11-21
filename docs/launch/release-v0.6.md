# Free-Research-Crew v0.6

Protocol 0.2, built from what the Reviewer kept finding in the first seven papers; Codex
support rebuilt on Codex custom agents; and an eighth gallery paper, the first written under
the new rules. It runs on the Claude Code or Codex plan you already have.

## Install

```bash
claude plugin marketplace add brycewang-stanford/Free-Research-Crew
claude plugin install crew@free-research-crew
# Codex: python3 crew/adapters/codex/install.py, then trust the crew guard in /hooks
```

Then run `/crew:start` in an empty folder. How it works:
[`crew/README.md`](https://github.com/brycewang-stanford/Free-Research-Crew/blob/main/crew/README.md).

## Protocol 0.2 (plugin version 0.2.0)

We grouped the Reviewer's findings across the first seven papers by kind and turned the
ones that kept recurring into rules the tool enforces. Workspaces created under 0.1 still
validate; for them the new rules are warnings.

- **Code is reviewed before it runs.** An analysis run needs a passing code review that
  read the exact code it executes. `crew.py review` stamps each review with the hashes of
  the files it read. Running without a review (`--unreviewed`) needs the human's consent
  and is recorded.
- **Process facts are macros.** `crew.py numbers` also writes `paper/process.tex`, which
  holds review rounds, findings, runs and the rerun result, all computed from the ledger.
  A wrong or stale account of the process was the most common finding of all.
- **Typed numbers are flagged.** A number in the paper that matches a claim but is not a
  macro is reported. Published values quoted for comparison are marked `% crew:literal`.
- **Submission checks** require a closed task board, current process macros and a PDF
  newer than its sources.
- **Fresh-environment reruns.** `crew.py rerun --setup` builds a new environment from the
  requirements file. Every attempt is appended to `replication-history.jsonl`.
- Commands pointing at temporary directories are refused, and source verification
  methods are limited to the three the protocol defines.

## Faster and easier to run

- `crew.py next <ws>` gives the next steps and what can run in parallel.
- `crew.py changes <ws> <target>` shows what changed since the Reviewer's last round.
- `crew.py brief` archives a brief and logs it in one step.
- `usage.py` reports busy minutes per role.

## Codex

The adapter (`crew/adapters/codex/install.py`) installs:

- the PI as a skill;
- the nine roles as Codex custom agents, each running in its own context;
- the same guard as hooks. It refuses gate approvals the human did not give, approvals
  while a subagent runs, and `apply_patch` edits that approve a gate.

An end-to-end test in Codex ([`gallery/ss-null-effect-codex`](https://github.com/brycewang-stanford/Free-Research-Crew/tree/main/gallery/ss-null-effect-codex))
ran through the results stage: the PI delegated to the custom agents, the guard ran as
hooks, and the code was reviewed before every run. It was then stopped by choice, so no
paper has yet passed all four gates in Codex.

## Eighth gallery paper

[Card's college-proximity IV return to schooling](https://github.com/brycewang-stanford/Free-Research-Crew/tree/main/gallery/ss-card-proximity)
is the first paper written under protocol 0.2.

- **Reproduced:** Card's 2SLS estimate of 0.132 (0.049) and his OLS estimate.
- **Missed and traced:** all seven unreproduced printed numbers come from a different
  first-stage specification. A post hoc regression, labelled as such, reproduces all
  eight numbers in those columns.
- **Weak-instrument test:** a weak-instrument-robust test does not establish a positive
  return, which the design predicted.
- **Answer key: fail.** The seed did not say which column `first-stage` meant. The result
  stays a fail, and the seed now names its columns.

## Corrections

- **Finding counts.** Earlier counts added up findings round by round, so a finding
  carried into later rounds was counted once per round. Counting each finding once:
  - all eight papers: 5 critical, 120 major and 290 minor findings over 98 review rounds;
  - the six papers in v0.5: 4 critical, 79 major and 189 minor, where v0.5 said 12, 210
    and 373.

  The report, posts and video are corrected.
- **Seed `ss-card-proximity`** cited the wrong NBER working paper (4832 instead of 4483).

## Also

- The technical report (`docs/launch/report/`) now has a Related work section citing 35
  verified sources, a Protocol 0.2 section and the eighth paper's results.
- The launch video is updated for eight papers.

## Known limits

- All eight papers are replications or synthetic tests with a known answer. A paper on an
  open question is in progress (`gallery/ss-ca-fastfood-wage/`).
- The gate guard narrows agents to the honest path, but it is not a sandbox.
- Same-family review shares the authors' blind spots.

The Reviewer's design follows [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep). CC0.
