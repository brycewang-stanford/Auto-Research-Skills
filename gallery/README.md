# Gallery

Papers produced by the crew, each with its complete workspace: the plan, the verified
sources, every logged run, every claim, the Reviewer's critiques and the human's gate
decisions. Failures stay here next to successes.

| Paper | Track | Seed | Status |
|---|---|---|---|
| [Does 401(k) eligibility raise household net financial assets?](ss-dml-401k/) | Social science | [`ss-dml-401k`](../crew/bench/seeds/ss-dml-401k/task.json) | In progress: question stage |
| [How much does training-label noise hurt common tabular classifiers?](cs-label-noise/) | CS | [`cs-label-noise`](../crew/bench/seeds/cs-label-noise/task.json) | In progress: question stage |

## Reading a workspace

Start with `plan.json` for the question, the design and the gate decisions, then
`reviews/` for what the Reviewer attacked and how each finding was resolved, then
`paper/main.pdf`. To check a number, find its macro in `claims.jsonl` and follow it to
the run in `runs/`. Run `python3 crew/scripts/crew.py validate gallery/<paper>` to check
the whole workspace, or `crew.py rerun` to reproduce it. The file formats are in
[`crew/PROTOCOL.md`](../crew/PROTOCOL.md).

Raw data files are not committed; each workspace's `data/manifest.json` says where to get
them and their hash.

## Disclosure

These papers are demonstrations of the crew. They are not submitted to journals or
conferences. Each was directed by a human who approved its four gates; the AI-use
statement in each paper says which models did what.
