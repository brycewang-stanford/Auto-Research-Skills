# Gallery

Papers produced by the crew, each with its complete workspace: the plan, the verified
sources, every logged run, every claim, the Reviewer's critiques and the human's gate
decisions. Failures stay here next to successes.

| Paper | Track | Seed | Status |
|---|---|---|---|
| [Does 401(k) eligibility raise household net financial assets? A double machine learning replication](ss-dml-401k/) | Social science | [`ss-dml-401k`](../crew/bench/seeds/ss-dml-401k/task.json) | Design approved; main estimates running |
| [How much does training-label noise hurt common tabular classifiers?](cs-label-noise/) | CS | [`cs-label-noise`](../crew/bench/seeds/cs-label-noise/task.json) | Results approved (both hypotheses inconclusive); figures and paper next |
| [Did a job-training program raise participants' earnings? An observational evaluation](ss-null-effect/) | Social science (null-effect test) | [`ss-null-effect`](../crew/bench/seeds/ss-null-effect/task.json) | Results approved; figures and paper next |

## Reading a workspace

Start with `plan.json` for the question, the design and the gate decisions, then
`reviews/` for what the Reviewer attacked and how each finding was resolved, then
`paper/main.pdf`. To check a number, find its macro in `claims.jsonl` and follow it to
the run in `runs/`. Run `python3 crew/scripts/crew.py validate gallery/<paper>` to check
the whole workspace, or `crew.py rerun` to reproduce it. The file formats are in
[`crew/PROTOCOL.md`](../crew/PROTOCOL.md).

Raw data files are not committed; each workspace's `data/manifest.json` says where to get
them and their hash.

## What the Reviewer caught so far

- **cs-label-noise:** a main hypothesis that averaged over datasets not yet named; small-dataset intervals ~40% as wide as honest ones; an ablation mislabelled as a mechanism. It also ran a pilot before the design gate itself, which is disclosed and led to a new rule.
- **ss-dml-401k:** a replication tolerance first too loose, then too strict; a "not testable" rule that discarded failures; a Python lasso missing hdm's zero-threshold step (R–Python gap $87 → $0.36 after the fix).
- **ss-null-effect:** a placebo test that a pre-program earnings dip would make "fail" either way (the design was blocked); a hand-typed log entry stamped in the future; an alternative estimate explained away in the notes.

## Disclosure

These papers are demonstrations of the crew. They are not submitted to journals or
conferences. The `ss-null-effect` seed (its synthetic data and hidden answer key) was
written by the same session that acted as PI; the analysing agents never saw the key. Each was directed by a human who approved its four gates; the AI-use
statement in each paper says which models did what.
