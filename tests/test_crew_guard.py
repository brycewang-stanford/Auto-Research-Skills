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


if __name__ == "__main__":
    unittest.main()
