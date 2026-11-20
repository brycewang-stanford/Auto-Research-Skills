"""Tests for crew/hooks/guard.py, the PreToolUse hook that keeps gate approvals human."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "crew" / "hooks" / "guard.py"
APPROVE_CMD = 'python3 crew/scripts/crew.py gate gallery/x design approve --by "Ada" --note "ok"'


def typed(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": text}}


def answered(question: str, answer: str) -> dict:
    return {
        "type": "user",
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t1",
                                                  "content": f'"{question}"="{answer}"'}]},
        "toolUseResult": {"questions": [], "answers": {question: answer}},
    }


def tool_result(text: str) -> dict:
    return {"type": "user", "message": {"role": "user", "content": [
        {"type": "tool_result", "tool_use_id": "t2", "content": text}]}}


class GuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.transcript = self.tmp / "session.jsonl"

    def run_guard(self, tool: str, tool_input: dict, entries: list[dict], **extra) -> str | None:
        self.transcript.write_text("".join(json.dumps(e) + "\n" for e in entries))
        event = {"tool_name": tool, "tool_input": tool_input, "transcript_path": str(self.transcript), **extra}
        env = {k: v for k, v in os.environ.items() if k != "CREW_GUARD"}
        out = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(event),
                             capture_output=True, text=True, env=env, check=True).stdout
        if not out.strip():
            return None
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"]

    def test_approve_without_human_input_is_denied(self) -> None:
        self.assertEqual(self.run_guard("Bash", {"command": APPROVE_CMD}, [typed("ok continue")]), "deny")

    def test_typed_approval_naming_the_gate_is_allowed(self) -> None:
        self.assertIsNone(self.run_guard("Bash", {"command": APPROVE_CMD}, [typed("I approve the design gate")]))
        self.assertIsNone(self.run_guard("Bash", {"command": APPROVE_CMD}, [typed("设计关卡：批准")]))

    def test_approval_of_another_gate_or_a_negation_is_denied(self) -> None:
        self.assertEqual(self.run_guard("Bash", {"command": APPROVE_CMD}, [typed("approve the question gate")]), "deny")
        self.assertEqual(self.run_guard("Bash", {"command": APPROVE_CMD}, [typed("do not approve the design yet")]), "deny")

    def test_ask_user_question_answer_counts(self) -> None:
        q = "Design gate: label-noise study. Approve?"
        self.assertIsNone(self.run_guard("Bash", {"command": APPROVE_CMD}, [answered(q, "Approve")]))
        self.assertEqual(self.run_guard("Bash", {"command": APPROVE_CMD}, [answered(q, "Reject")]), "deny")

    def test_later_tool_results_do_not_hide_the_human_answer(self) -> None:
        entries = [answered("Design gate: approve?", "Approve"), tool_result("approve design gate")]
        self.assertIsNone(self.run_guard("Bash", {"command": APPROVE_CMD}, entries))

    def test_newer_human_message_supersedes_an_old_approval(self) -> None:
        entries = [answered("Design gate: approve?", "Approve"), typed("wait, let me reread it")]
        self.assertEqual(self.run_guard("Bash", {"command": APPROVE_CMD}, entries), "deny")

    def test_slash_command_counts(self) -> None:
        cmd = "<command-name>/crew:gate</command-name>\n<command-args>gallery/x design approve</command-args>"
        self.assertIsNone(self.run_guard("Bash", {"command": APPROVE_CMD}, [typed(cmd)]))

    def test_subagent_can_never_approve(self) -> None:
        entries = [typed("approve the design gate")]
        self.assertEqual(self.run_guard("Bash", {"command": APPROVE_CMD}, entries, agent_id="a1"), "deny")

    def test_gate_request_and_other_commands_pass(self) -> None:
        for command in ("python3 crew/scripts/crew.py gate gallery/x design request --note hi",
                        "python3 crew/scripts/crew.py validate gallery/x", "grep gate-approve log.jsonl"):
            self.assertIsNone(self.run_guard("Bash", {"command": command}, [typed("ok continue")]))

    def test_editing_plan_json_to_approve_is_denied(self) -> None:
        plan = self.tmp / "plan.json"
        plan.write_text(json.dumps({"gates": {"design": {"status": "requested"}}}, indent=2))
        edit = {"file_path": str(plan), "old_string": '"status": "requested"', "new_string": '"status": "approved"'}
        self.assertEqual(self.run_guard("Edit", edit, [typed("ok continue")]), "deny")
        harmless = {"file_path": str(plan), "old_string": '"requested"', "new_string": '"requested" '}
        self.assertIsNone(self.run_guard("Edit", harmless, [typed("ok continue")]))
        write = {"file_path": str(plan), "content": json.dumps({"gates": {"design": {"status": "approved"}}})}
        self.assertEqual(self.run_guard("Write", write, [typed("ok continue")]), "deny")

    def test_answer_keys_are_off_limits(self) -> None:
        self.assertEqual(self.run_guard("Read", {"file_path": "/r/answer-keys/ss-null-effect/answer.json"}, []), "deny")
        self.assertEqual(self.run_guard("Bash", {"command": "cat answer-keys/*/answer.json"}, []), "deny")
        self.assertIsNone(self.run_guard("Read", {"file_path": "/r/crew/bench/seeds/ss-null-effect/task.json"}, []))
        self.assertEqual(self.run_guard("Grep", {"pattern": "truth", "path": "answer-keys"}, []), "deny")
        doc = {"file_path": "/r/README.md", "old_string": "a", "new_string": "keys live in answer-keys/"}
        self.assertIsNone(self.run_guard("Edit", doc, []))

    def test_hook_files_are_wired(self) -> None:
        hooks = json.loads((ROOT / "crew" / "hooks" / "hooks.json").read_text())
        command = hooks["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        self.assertIn("hooks/guard.py", command)


class CodexGuardTest(unittest.TestCase):
    """The same guard under Codex: prompts recorded by UserPromptSubmit, edits via apply_patch."""

    def setUp(self) -> None:
        self.state = Path(tempfile.mkdtemp())

    def send(self, event: dict) -> str | None:
        env = {k: v for k, v in os.environ.items() if k not in ("CREW_GUARD", "PLUGIN_DATA")}
        env["CODEX_HOME"] = str(self.state)
        out = subprocess.run([sys.executable, str(GUARD)], input=json.dumps(event),
                             capture_output=True, text=True, env=env, check=True).stdout
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else None

    def prompt(self, text: str, session: str = "s1") -> None:
        self.assertIsNone(self.send({"hook_event_name": "UserPromptSubmit", "session_id": session,
                                     "turn_id": "t", "prompt": text}))

    def tool(self, name: str, command: str, session: str = "s1") -> str | None:
        return self.send({"hook_event_name": "PreToolUse", "session_id": session, "turn_id": "t",
                          "cwd": str(self.state), "tool_name": name, "tool_input": {"command": command}})

    def workspace(self) -> None:
        ws = self.state / "ws"
        ws.mkdir()
        (ws / "crew.json").write_text("{}")
        (ws / "plan.json").write_text(json.dumps({"gates": {"design": {"status": "requested"}}}, indent=2))

    def test_approval_needs_the_humans_latest_prompt(self) -> None:
        self.assertEqual(self.tool("Bash", APPROVE_CMD), "deny")
        self.prompt("I approve the design gate")
        self.assertIsNone(self.tool("Bash", APPROVE_CMD))
        self.assertEqual(self.tool("Bash", APPROVE_CMD, session="other"), "deny")
        self.prompt("ok continue")
        self.assertEqual(self.tool("Bash", APPROVE_CMD), "deny")

    def test_apply_patch_cannot_approve_a_gate(self) -> None:
        self.workspace()
        self.prompt("approve the design gate")
        patch = ("*** Begin Patch\n*** Update File: ws/plan.json\n@@\n"
                 '-      "status": "requested"\n+      "status": "approved"\n*** End Patch\n')
        self.assertEqual(self.tool("apply_patch", patch), "deny")
        self.assertIsNone(self.tool("apply_patch", patch.replace("plan.json", "notes.json")))
        # the value split over two lines, or a file moved onto plan.json, is still an approval
        split = ("*** Begin Patch\n*** Update File: ws/plan.json\n@@\n"
                 '-      "status": "requested"\n+      "status":\n+        "approved"\n*** End Patch\n')
        self.assertEqual(self.tool("apply_patch", split), "deny")
        moved = ('*** Begin Patch\n*** Add File: ws/x.json\n+{"gates": {"design": {"status": "approved"}}}\n'
                 "*** Update File: ws/x.json\n*** Move to: ws/plan.json\n@@\n*** End Patch\n")
        self.assertEqual(self.tool("apply_patch", moved), "deny")
        # a plan.json outside any crew workspace is not the guard's business
        other = patch.replace("ws/plan.json", "elsewhere/plan.json")
        self.assertIsNone(self.tool("apply_patch", other))

    def test_no_approval_while_a_subagent_runs(self) -> None:
        self.prompt("approve the design gate")
        start = {"hook_event_name": "SubagentStart", "session_id": "s1", "turn_id": "t", "agent_id": "a1"}
        self.assertIsNone(self.send(start))
        self.assertEqual(self.tool("Bash", APPROVE_CMD), "deny")
        self.assertIsNone(self.send({**start, "hook_event_name": "SubagentStop"}))
        self.assertIsNone(self.tool("Bash", APPROVE_CMD))

    def test_answer_keys_are_off_limits(self) -> None:
        keys = "answer" + "-keys"
        self.assertEqual(self.tool("Bash", f"ls {keys}/"), "deny")
        self.assertEqual(self.tool("apply_patch", f"*** Begin Patch\n*** Add File: {keys}/x.json\n+{{}}\n"), "deny")
        # writing text that mentions the directory is not access to it
        doc = f"*** Begin Patch\n*** Update File: README.md\n@@\n-a\n+keys live in {keys}/\n*** End Patch\n"
        self.assertIsNone(self.tool("apply_patch", doc))


if __name__ == "__main__":
    unittest.main()
