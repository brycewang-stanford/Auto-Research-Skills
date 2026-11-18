---
name: status
description: Show where a research-crew project stands — gates, tasks, runs, reviews and validation — and resume work on it. Use when the user asks about crew progress or wants to continue a crew workspace.
argument-hint: "[workspace path]"
---

# Crew status

Workspace: $ARGUMENTS (if empty, look for a directory containing `crew.json` under
`./crew-workspace/`; ask if there is more than one).

Run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/crew.py" status <workspace>` and
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/crew.py" validate <workspace>`.

Report in plain words: which gate the project is at, what is done, what is in progress,
the Reviewer's latest verdict and open findings, and any validation error.

If the user wants to continue, read `${CLAUDE_PLUGIN_ROOT}/PI.md` and
`${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md` if you have not this session, then resume as the PI
from the first task that is not done. Never pass a gate that is not approved.
