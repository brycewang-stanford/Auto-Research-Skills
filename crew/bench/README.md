# Crew bench

Seed tasks that a crew must be able to finish, each with a way to score the result.

| Seed | Track | Kind | Scored by |
|---|---|---|---|
| [`ss-dml-401k`](seeds/ss-dml-401k/task.json) | Social science | Replication of a published estimate | Distance from the published estimate, plus protocol checks |
| [`cs-label-noise`](seeds/cs-label-noise/task.json) | CS | Small empirical ML study | Protocol checks and a clean rerun |

Run one with `/crew:start <seed id>`.

## Rules

- A seed is a `task.json` the crew reads, and for replications an `answer.json` it must
  not read. The answer key cites where each number was read.
- Every seed must run on a laptop CPU in under an hour.
- A run counts only if the workspace passes `crew.py validate --strict` and a human
  approved all four gates.
- Results, including failures, are published in the gallery with the full workspace.

## Adding a seed

Copy an existing seed directory, write `task.json`, and for a replication record the
published numbers in `answer.json` with the exact table and the date you read it. Good
seeds have public data, a published or checkable answer, and a small compute budget.
