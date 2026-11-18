---
name: gate
description: Record the human's decision on a research-crew gate (question, design, results, submission). Use only when the user explicitly approves or rejects a gate in this conversation.
argument-hint: "<workspace path> <gate> approve|reject [note]"
disable-model-invocation: true
---

# Record a gate decision

Arguments: $ARGUMENTS

This command exists so that a gate is passed only by the human. It is invoked by the
user; never run it, or the underlying command, on your own initiative.

1. Before recording an approval, show the user the Reviewer's latest verdict and every
   open finding for this stage (`crew.py status <workspace>`), unless you just did.
2. Record the decision, with the user's name and their words:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/crew.py" gate <workspace> <gate> approve|reject --by "<user's name>" --note "<their words>"`
   If you do not know the user's name, ask.
3. If the tool refuses because a critical finding is open, tell the user which one. They
   may send it back for another round, or accept it with
   `--accept-findings <ids> --note "<why>"`, which will be disclosed in the paper.
4. After an approval, continue as the PI (`${CLAUDE_PLUGIN_ROOT}/PI.md`) with the next
   stage. After a rejection, ask what should change.
