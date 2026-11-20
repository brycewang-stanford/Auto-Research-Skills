"""Tests for crew/adapters/codex/install.py, which installs the crew into Codex."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("codex_install", ROOT / "crew" / "adapters" / "codex" / "install.py")
install = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(install)
ROLES = sorted(p.stem for p in (ROOT / "crew" / "agents").glob("*.md"))


def run(*argv: str) -> int:
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return install.main(list(argv))


class CodexAdapterTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name)

    def test_every_role_becomes_a_valid_custom_agent(self) -> None:
        self.assertEqual(run("--codex-home", str(self.home)), 0)
        for role in ROLES:
            agent = tomllib.loads((self.home / "agents" / f"crew-{role}.toml").read_text())
            self.assertEqual(agent["name"], "crew_" + role.replace("-", "_"))
            self.assertTrue(agent["description"])
            self.assertIn("## Running in Codex", agent["developer_instructions"])
            self.assertNotIn("${CLAUDE_PLUGIN_ROOT}", agent["developer_instructions"].split("## Running in Codex")[0])
        pi = (self.home / "skills" / "crew-pi" / "SKILL.md").read_text()
        self.assertTrue(pi.startswith("---\nname: crew-pi\n"))
        self.assertIn("crew_reviewer", pi)

    def test_hooks_merge_without_duplicates_and_uninstall_cleanly(self) -> None:
        mine = {"hooks": {"Stop": [{"hooks": [{"type": "command", "command": "echo mine"}]}]}}
        (self.home / "hooks.json").write_text(json.dumps(mine))
        self.assertEqual(run("--codex-home", str(self.home)), 0)
        self.assertEqual(run("--codex-home", str(self.home)), 0)  # idempotent
        hooks = json.loads((self.home / "hooks.json").read_text())["hooks"]
        self.assertEqual(len(hooks["PreToolUse"]), 1)
        self.assertEqual(hooks["PreToolUse"][0]["matcher"], "Bash|apply_patch")
        self.assertIn("UserPromptSubmit", hooks)
        self.assertEqual(hooks["Stop"], mine["hooks"]["Stop"])
        self.assertEqual(run("--codex-home", str(self.home), "--uninstall"), 0)
        self.assertEqual(json.loads((self.home / "hooks.json").read_text()), mine)
        self.assertFalse(any((self.home / "agents").glob("crew-*.toml")))
        self.assertFalse((self.home / "skills" / "crew-pi").exists())

    def test_old_role_skills_are_replaced(self) -> None:
        old = self.home / "skills" / "crew-reviewer" / "SKILL.md"
        old.parent.mkdir(parents=True)
        old.write_text("---\nname: crew-reviewer\n---\n## Running in Codex\n")
        unrelated = self.home / "skills" / "crew-writer" / "SKILL.md"
        unrelated.parent.mkdir(parents=True)
        unrelated.write_text("---\nname: crew-writer\n---\nsomeone else's skill\n")
        self.assertEqual(run("--codex-home", str(self.home), "--no-hooks"), 0)
        self.assertFalse(old.exists())
        self.assertTrue(unrelated.exists())
        self.assertFalse((self.home / "hooks.json").exists())


if __name__ == "__main__":
    unittest.main()
