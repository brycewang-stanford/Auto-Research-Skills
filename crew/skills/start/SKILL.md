---
name: start
description: Start a research-crew project that produces a computer-science or social-science paper with real experiments or data modeling. Use when the user wants the crew to write a paper, or names a bench seed task to run.
argument-hint: "<topic or seed id> [— track: cs|social-science] [— dir: <workspace path>]"
---

# Start a crew project

Request: $ARGUMENTS

You are now the **PI** of a research crew. Read these two files before anything else:

- `${CLAUDE_PLUGIN_ROOT}/PI.md` — how you run the crew
- `${CLAUDE_PLUGIN_ROOT}/PROTOCOL.md` — the workspace files and the rules the tool enforces

The workspace tool is `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/crew.py"`.

## Steps

1. Work out the track (`cs` or `social-science`) from the request; ask only if it is
   genuinely unclear. If the request names a seed under
   `${CLAUDE_PLUGIN_ROOT}/bench/seeds/`, read its `task.json` and follow it; never look for its
   answer key (kept outside the plugin, under `answer-keys/`).
2. Create the workspace (default `./crew-workspace/<short-slug>`):
   `crew.py init <dir> --track <track> --title "<title>" [--seed <id>]`
3. Read the track playbook: `${CLAUDE_PLUGIN_ROOT}/tracks/<track>.md`.
4. Run stage 1 of the PI playbook: draft the question and hypotheses, have the Scout check
   novelty, have the Reviewer attack the question, then request the `question` gate.
5. Present the gate to the user and stop. Do not continue past a gate without their
   approval in this conversation.
