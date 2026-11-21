# Codex adapter

Runs the crew in [Codex](https://github.com/openai/codex) the same way the Claude Code
plugin runs it: the PI in your session, each role as a subagent with its own context, and
the same guard on gate approvals and answer keys.

```bash
python3 crew/adapters/codex/install.py            # into $CODEX_HOME (default ~/.codex)
python3 crew/adapters/codex/install.py --dry-run  # show what would be written
python3 crew/adapters/codex/install.py --uninstall
```

It writes:

| File | What it is |
|---|---|
| `skills/crew-pi/SKILL.md` | The PI: start or resume a crew project |
| `agents/crew-<role>.toml` | One [custom agent](https://developers.openai.com/codex/subagents) per role (`crew_scout`, `crew_designer`, `crew_data_ra`, `crew_econometrician`, `crew_experimenter`, `crew_figures_ra`, `crew_writer`, `crew_replicator`, `crew_reviewer`), generated from [`crew/agents/`](../../agents/) |
| `hooks.json` | The crew guard ([`hooks/guard.py`](../../hooks/guard.py)) on `PreToolUse` (`Bash`, `apply_patch`), `UserPromptSubmit`, `SubagentStart` and `SubagentStop`, merged into any hooks you already have |

Then:

1. Start Codex and open `/hooks` once to trust the crew guard. Codex skips hooks you have
   not trusted.
2. Ask: *"use crew-pi to start seed ss-dml-401k"*, or describe your own topic.
3. Approve gates by typing it, for example *"approve the design gate"*. The guard reads
   your latest message (recorded by the `UserPromptSubmit` hook) and refuses an approval
   you did not give, any approval while a crew subagent is running, and any
   `apply_patch` that marks a gate approved in a workspace's `plan.json`.

Everything points at this checkout's `crew/` by absolute path: keep the clone where it is,
and rerun the installer after you move or update it. The installer also removes the
`crew-<role>` skills an earlier version of it wrote.

Subagents inherit your session's model, sandbox and approval settings. The Reviewer runs
as `crew_reviewer` in a fresh context (`independence: fresh-context`). For a cross-family
review, and only if you agree to send the workspace to Anthropic, the PI can run it on
Claude instead: `python3 crew/scripts/cross_review.py <workspace> <target> <round> --via claude`.

## Status

Codex loads the PI skill, all nine agents and the hooks; the guard is tested in
[`tests/test_crew_guard.py`](../../../tests/test_crew_guard.py).

On 2026-11-21 the first end-to-end test,
[`gallery/ss-null-effect-codex`](../../../gallery/ss-null-effect-codex/), ran in Codex
(codex-cli 0.164.0, model gpt-6.1). It reached the results stage before a Codex usage
limit paused it, and the test was stopped there by choice: the remaining stages use the
same machinery. No paper has yet passed all four gates in Codex.

What worked:

- The PI spawned the `crew_scout`, `crew_designer`, `crew_data_ra`, `crew_econometrician`
  and `crew_reviewer` custom agents, each in its own session.
- The guard ran as Codex hooks, and the human approved each gate.
- The analysis code passed a code review (two rounds) before any of its nine runs.
- The estimate on the null-effect data is −120, 95% CI [−448, 209]: no effect found, as
  the seed requires.

What to watch:

- The Codex Reviewer passed every first round: question, literature, design and results.
  On the same seed, the Claude Reviewer blocked the question in round 1. One run is not
  enough to say whether that is leniency or a better first draft.
- The PI wrote its briefs to `/tmp` before archiving them with `crew.py brief`. The
  archived copy is what counts, but the habit is worth correcting.

Running headless (`codex exec`):

- Hooks run only if they are trusted in `/hooks`, or with `--dangerously-bypass-hook-trust`
  for that invocation.
- `codex exec resume` takes the sandbox as `-c 'sandbox_mode="workspace-write"'`, not
  `-s`.
- The Scout needs `-c sandbox_workspace_write.network_access=true`.

In this test the approvals were typed in a Claude Code chat and passed verbatim into the
Codex session; the workspace log says so.
