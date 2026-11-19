# Crew bench

Seed tasks that a crew must be able to finish, each with a way to score the result.

| Seed | Track | Kind | Scored by |
|---|---|---|---|
| [`ss-dml-401k`](seeds/ss-dml-401k/task.json) | Social science | Replication of a published estimate | Distance from the published estimate, plus protocol checks |
| [`ss-null-effect`](seeds/ss-null-effect/task.json) | Social science | Observational evaluation where the true effect is zero | The crew must not find an effect; hidden answer key |
| [`cs-label-noise`](seeds/cs-label-noise/task.json) | CS | Small empirical ML study | Protocol checks and a clean rerun |
| [`cs-calibration`](seeds/cs-calibration/task.json) | CS | Small empirical ML study (probability calibration) | Protocol checks and a clean rerun |
| [`ss-lalonde-observational`](seeds/ss-lalonde-observational/task.json) | Social science | Recover an experimental benchmark from observational data | The 95% interval must contain the experimental benchmark; hidden answer key |
| [`ss-card-krueger`](seeds/ss-card-krueger/task.json) | Social science | Replication of a published difference-in-differences estimate | Distance from the published estimate; hidden answer key |
| [`ss-card-proximity`](seeds/ss-card-proximity/task.json) | Social science | Replication of a published instrumental-variables estimate (return to schooling) | Distance from the published estimate; hidden answer key |
| [`ss-rd-senate`](seeds/ss-rd-senate/task.json) | Social science | Replication of a published regression-discontinuity estimate (US Senate incumbency advantage) | Distance from the published estimate and robust interval; hidden answer key |

Run one with `/crew:start <seed id>`.

## Rules

- A seed is a `task.json` the crew reads, and where there is a right answer an
  `answer.json` (and sometimes an `answer/` directory) it must not read. A replication's
  answer key cites where each number was read.
- Every seed must run on a laptop CPU in under an hour.
- A run counts only if the workspace passes `crew.py validate --strict` and a human
  approved all four gates.
- Results, including failures, are published in the gallery with the full workspace.

## Adding a seed

Copy an existing seed directory, write `task.json`, and for a replication record the
published numbers in `answer.json` with the exact table and the date you read it. Good
seeds have public data, a published or checkable answer, and a small compute budget.
