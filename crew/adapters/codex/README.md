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

Status: Codex loads the PI skill, all nine agents and the hooks (checked with
`codex debug prompt-input`, which builds the prompt locally); the guard is tested in
[`tests/test_crew_guard.py`](../../../tests/test_crew_guard.py). The seven gallery
papers were all written in Claude Code; none has yet been run end to end in Codex.
