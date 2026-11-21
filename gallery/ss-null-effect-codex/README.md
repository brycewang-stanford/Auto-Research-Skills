# Codex end-to-end test (stopped at the results stage)

This workspace is a test of the crew running in Codex, not a gallery paper. The PI ran in
Codex (codex-cli 0.164.0, model gpt-6.1), delegated to the `crew_*` custom agents, and the
crew guard ran as Codex hooks. The human approved the question and design gates in a
Claude Code chat; each approval was passed verbatim into the Codex session (see
`log.jsonl` and the gate notes in `plan.json`).

It got as far as the results review: two code-review rounds before any analysis run,
nine runs, 288 result claims and a passing results review (round 1). The primary estimate
on the null-effect data is an ATT of −120 (95% CI −448 to 209). A Codex usage limit
paused it before the results gate, and the human chose to stop the test there, because
the remaining stages (paper, clean rerun, submission) use the same machinery. The
results, paper and submission gates were never requested, so nothing here has passed
them.

Findings for the adapter are in
[`crew/adapters/codex/README.md`](../../crew/adapters/codex/README.md#status).
