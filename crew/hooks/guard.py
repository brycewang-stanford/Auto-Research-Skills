#!/usr/bin/env python3
"""PreToolUse guard for the research crew (Claude Code and Codex hook).

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

In Codex the human's latest message comes from a UserPromptSubmit hook that runs this
script too and records the prompt (Codex transcripts are not a stable format), and an
`apply_patch` that marks a gate approved in plan.json is always refused: approvals go
through `crew.py gate`.

Set CREW_GUARD=off in the environment Claude Code or Codex runs in to disable it (for example
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

PATCH_HEADER_RE = re.compile(r"^\*\*\* (Add File|Update File|Delete File|Move to): (.+)$", re.MULTILINE)


def patch_sections(patch: str) -> list[dict]:
    """Split a Codex apply_patch into file sections: action, path, destination, body lines."""
    sections: list[dict] = []
    for line in patch.splitlines():
        header = PATCH_HEADER_RE.match(line)
        if header and header.group(1) == "Move to" and sections:
            sections[-1]["dest"] = header.group(2).strip()
        elif header:
            sections.append({"action": header.group(1), "path": header.group(2).strip(), "dest": None, "lines": []})
        elif sections and not line.startswith("*** "):
            sections[-1]["lines"].append(line)
    return sections


def patch_paths(patch: str) -> list[str]:
    return [p for m in PATCH_HEADER_RE.finditer(patch) for p in [m.group(2).strip()]]


def apply_hunks(current: str, lines: list[str]) -> str | None:
    """Apply an Update section's hunks to the current text; None if a hunk does not fit."""
    text = current
    hunks, hunk = [], []
    for line in lines:
        if line.startswith("@@"):
            if hunk:
                hunks.append(hunk)
            hunk = []
        else:
            hunk.append(line)
    if hunk:
        hunks.append(hunk)
    for hunk in hunks:
        old = "\n".join(l[1:] for l in hunk if l[:1] in (" ", "-"))
        new = "\n".join(l[1:] for l in hunk if l[:1] in (" ", "+"))
        if old and old not in text:
            return None
        text = text.replace(old, new, 1) if old else text + new
    return text


def patch_approves_gate(patch: str, cwd: str) -> bool:
    """True when a Codex apply_patch would turn a gate to approved in a crew workspace's plan.json."""
    base = Path(cwd or ".")
    pending: dict[str, str] = {}  # files added or changed earlier in the same patch

    def read(path: str) -> str:
        if path in pending:
            return pending[path]
        try:
            return (base / path).read_text(encoding="utf-8")
        except OSError:
            return ""

    for section in patch_sections(patch):
        if section["action"] == "Delete File":
            pending[section["path"]] = ""
            continue
        current = read(section["path"])
        if section["action"] == "Add File":
            new = "\n".join(l[1:] for l in section["lines"] if l.startswith("+"))
        else:
            new = apply_hunks(current, section["lines"])
        dest = section["dest"] or section["path"]
        names = {Path(section["path"]).name, Path(dest).name}
        in_crew = any((base / p).parent.joinpath("crew.json").exists() for p in (section["path"], dest))
        if "plan.json" in names and in_crew:
            if new is None:  # cannot tell what the edit does: refuse it if it adds anything "approved"
                if any(l.startswith("+") and "approved" in l for l in section["lines"]):
                    return True
            elif approved_gates(new) - approved_gates(read(dest)):
                return True
        pending[dest] = new if new is not None else current
        if section["dest"]:
            pending[section["path"]] = ""
    return False


def state_dir() -> Path:
    data = os.environ.get("PLUGIN_DATA")
    if data:
        return Path(data)
    home = os.environ.get("CODEX_HOME") or str(Path.home() / ".codex")
    return Path(home) / "crew-guard"


def state_file(session: str) -> Path:
    safe = re.sub(r"[^A-Za-z0-9_.-]", "_", session or "default")
    return state_dir() / f"{safe}.json"


def record_prompt(event: dict) -> None:
    """UserPromptSubmit (Codex): remember the human's latest message for this session."""
    target = state_file(str(event.get("session_id", "")))
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({"prompt": str(event.get("prompt", ""))}), encoding="utf-8")
    except OSError:
        pass


SUBAGENT_TTL = 6 * 3600


def agents_file(session: str) -> Path:
    return state_file(session).with_suffix(".agents.json")


def track_subagent(event: dict, started: bool) -> None:
    """SubagentStart/SubagentStop (Codex): keep the set of subagents running in this session."""
    import time
    target = agents_file(str(event.get("session_id", "")))
    try:
        active = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        active = {}
    agent = str(event.get("agent_id") or event.get("agent_type") or "?")
    if started:
        active[agent] = time.time()
    else:
        active.pop(agent, None)
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(active), encoding="utf-8")
    except OSError:
        pass


def subagents_running(event: dict) -> bool:
    import time
    try:
        active = json.loads(agents_file(str(event.get("session_id", ""))).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return any(time.time() - float(t) < SUBAGENT_TTL for t in active.values())


def recorded_prompt(event: dict):
    try:
        data = json.loads(state_file(str(event.get("session_id", ""))).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    prompt = str(data.get("prompt", "")).strip() if isinstance(data, dict) else ""
    return ("text", prompt) if prompt else None


def is_codex(event: dict) -> bool:
    # Codex adds turn_id to tool hooks; Claude Code does not
    return "turn_id" in event

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
    if is_codex(event):
        if subagents_running(event):
            deny("Refused: a crew subagent is still running in this session, and subagents never "
                 "approve gates. Wait for it to finish, then approve from the PI.")
        evidence = recorded_prompt(event)
    elif transcript and Path(transcript).is_file():
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
    if tool == "apply_patch":  # the patch body is text being written; only its file paths count
        blob = "\n".join(patch_paths(str(tool_input.get("command", ""))))
    else:
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
    if event.get("hook_event_name") == "UserPromptSubmit":
        record_prompt(event)
        sys.exit(0)
    if event.get("hook_event_name") in ("SubagentStart", "SubagentStop"):
        track_subagent(event, started=event["hook_event_name"] == "SubagentStart")
        sys.exit(0)
    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        sys.exit(0)
    if isinstance(tool_input.get("command"), list):  # some Codex shells pass argv
        tool_input = {**tool_input, "command": " ".join(map(str, tool_input["command"]))}
    check_keys(tool, tool_input)
    if tool == "Bash":
        check_gates(event, gates_in_command(str(tool_input.get("command", ""))))
    elif tool == "apply_patch":
        if patch_approves_gate(str(tool_input.get("command", "")), str(event.get("cwd", ""))):
            deny("Refused: never edit plan.json to approve a gate. When the human approves in chat, "
                 "run `crew.py gate <workspace> <gate> approve --by \"<their name>\"`.")
    elif tool in ("Edit", "Write", "MultiEdit"):
        check_gates(event, gates_in_edit(tool, tool_input))
    sys.exit(0)


if __name__ == "__main__":
    main()
