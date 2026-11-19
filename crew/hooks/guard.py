#!/usr/bin/env python3
"""PreToolUse guard for the research crew (Claude Code hook).

Two rules the protocol used to leave to the agents' goodwill:

1. **Only the human approves a gate.** A tool call that approves a gate, either
   `crew.py gate <ws> <gate> approve` in a shell command or an edit of
   `plan.json` that turns a gate to "approved", is refused unless the human's most
   recent input in the main conversation approves that gate: a typed message that
   names the gate (or "all gates") and says approve, a `/crew:gate ... approve`
   command, or an AskUserQuestion answer that starts with "Approve" to a question
   naming the gate. Subagents can never approve.
2. **Agents never read answer keys.** Any tool call that names `answer-keys/` is refused.

What it cannot stop: a command that hides its intent (for example a script written
to disk and run later) or a human typing an approval without reading. It narrows the
agent's options to the honest path; it is not a sandbox.

Set CREW_GUARD=off in the environment Claude Code runs in to disable it (for example
while maintaining the bench). Standard library only.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

GATES = ("question", "design", "results", "submission")
GATE_WORDS = {
    "question": ("question", "问题"),
    "design": ("design", "设计"),
    "results": ("results", "result", "结果"),
    "submission": ("submission", "submit", "投稿", "提交"),
}
ALL_WORDS = ("all gates", "every gate", "all four", "全部", "所有")
APPROVE_RE = re.compile(r"\b(approve[sd]?|approving|lgtm)\b|批准|同意|通过", re.IGNORECASE)
NEGATION_RE = re.compile(r"\b(do not|don't|not|never|reject\w*)\s+(yet\s+)?approv|不批准|不同意|不通过|驳回|拒绝", re.IGNORECASE)
GATE_CMD_RE = re.compile(
    r"\bgate\b[^\n;&|]*?\b(question|design|results|submission)\b[^\n;&|]*?\bapprove\b",
    re.IGNORECASE,
)
KEYS_RE = re.compile(r"answer-keys")


def deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.exit(0)


# ---------------------------------------------------------------- gate approvals

def gates_in_command(command: str) -> set[str]:
    return {m.group(1).lower() for m in GATE_CMD_RE.finditer(command)}


def approved_gates(plan_text: str) -> set[str]:
    try:
        gates = json.loads(plan_text).get("gates", {})
    except (ValueError, AttributeError):
        return set()
    return {g for g in GATES if isinstance(gates.get(g), dict) and gates[g].get("status") == "approved"}


def gates_in_edit(tool: str, tool_input: dict) -> set[str]:
    path = str(tool_input.get("file_path", ""))
    if Path(path).name != "plan.json":
        return set()
    try:
        current = Path(path).read_text()
    except OSError:
        current = ""
    if tool == "Write":
        new = str(tool_input.get("content", ""))
    else:
        edits = tool_input.get("edits") or [tool_input]
        new = current
        for edit in edits:
            old, repl = str(edit.get("old_string", "")), str(edit.get("new_string", ""))
            new = new.replace(old, repl) if edit.get("replace_all") else new.replace(old, repl, 1)
    return approved_gates(new) - approved_gates(current)


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def is_tool_result(content) -> bool:
    return isinstance(content, list) and any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def last_human_input(transcript: Path):
    """Return ("text", str) or ("answers", dict) for the human's latest input, or None."""
    latest = None
    with transcript.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            if entry.get("type") != "user" or entry.get("isSidechain") or entry.get("isMeta") \
                    or entry.get("isCompactSummary"):
                continue
            content = (entry.get("message") or {}).get("content")
            result = entry.get("toolUseResult")
            if isinstance(result, dict) and isinstance(result.get("answers"), dict):
                latest = ("answers", result["answers"])
                continue
            if is_tool_result(content):
                continue
            text = text_of(content).strip()
            if not text or text.startswith(("<task-notification>", "<local-command", "<system-reminder>",
                                             "<cross-session-message")):
                continue
            if text.startswith("<command-name>") and "crew:gate" not in text:
                continue
            latest = ("text", text)
    return latest


def names_gate(text: str, gate: str) -> bool:
    low = text.lower()
    return any(w in low for w in GATE_WORDS[gate]) or any(w in low for w in ALL_WORDS)


def human_approved(evidence, gate: str) -> bool:
    if evidence is None:
        return False
    kind, value = evidence
    if kind == "text":
        return bool(APPROVE_RE.search(value)) and not NEGATION_RE.search(value) and names_gate(value, gate)
    for question, answer in value.items():
        answer = str(answer).strip().lower()
        if answer.startswith(("approve", "批准", "同意", "通过")) and names_gate(str(question), gate):
            return True
    return False


def check_gates(event: dict, gates: set[str]) -> None:
    if not gates:
        return
    if event.get("agent_id"):
        deny("Gate approvals belong to the human PI; a subagent may never approve a gate. "
             "Return to the PI with a gate request instead.")
    transcript = event.get("transcript_path")
    evidence = None
    if transcript and Path(transcript).is_file():
        evidence = last_human_input(Path(transcript))
    missing = sorted(g for g in gates if not human_approved(evidence, g))
    if missing:
        deny(
            f"Refused: approving the {', '.join(missing)} gate needs the human's own approval, and their "
            "latest message does not give it. Present the gate (verdict, kill argument, open findings), "
            "then ask the human: an AskUserQuestion naming the gate with an 'Approve' option, or let "
            "them type `/crew:gate <workspace> <gate> approve`. Run the approve command only after "
            "they approve. Never edit plan.json to approve a gate."
        )


# ---------------------------------------------------------------- answer keys

KEY_FIELDS = ("command", "file_path", "notebook_path", "path", "glob")


def check_keys(tool: str, tool_input: dict) -> None:
    # Only what the tool will touch: a shell command or a target path. Text being written
    # (a document that mentions the directory) is not access to the keys.
    blob = "\n".join(str(tool_input.get(field, "")) for field in KEY_FIELDS)
    if KEYS_RE.search(blob):
        deny("Refused: answer-keys/ holds the bench's hidden answer keys. Crew agents never read, "
             "search or list them; scoring is done by crew/bench/score.py after the results gate.")


def main() -> None:
    if os.environ.get("CREW_GUARD", "").lower() in ("off", "0", "false"):
        sys.exit(0)
    try:
        event = json.load(sys.stdin)
    except ValueError:
        sys.exit(0)
    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        sys.exit(0)
    check_keys(tool, tool_input)
    if tool == "Bash":
        check_gates(event, gates_in_command(str(tool_input.get("command", ""))))
    elif tool in ("Edit", "Write", "MultiEdit"):
        check_gates(event, gates_in_edit(tool, tool_input))
    sys.exit(0)


if __name__ == "__main__":
    main()
