import unittest
from collections import Counter
from pathlib import Path
import tempfile
from unittest import mock

from tools import build_safety_report


class SafetyReportTests(unittest.TestCase):
    def finding(self, **overrides):
        values = {
            "severity": "critical",
            "rule_id": "remote-shell-pipe",
            "path": "skills/demo/README.md",
            "line": 7,
            "match": "curl https://example.com/install.sh | bash",
            "reason": "Review download-and-execute.",
        }
        values.update(overrides)
        return build_safety_report.scan.Finding(**values)

    def test_collection_from_path_uses_skill_collection(self) -> None:
        self.assertEqual(
            build_safety_report.collection_from_path("skills/demo/SKILL.md"),
            "demo",
        )
        self.assertEqual(
            build_safety_report.collection_from_path("README.md"),
            "(outside skills)",
        )

    def test_render_count_table_limits_and_rolls_up_other(self) -> None:
        table = build_safety_report.render_count_table(
            ("Rule", "Findings"),
            Counter({"a": 3, "b": 2, "c": 1}),
            limit=2,
        )

        self.assertIn("| `a` | 3 |", table)
        self.assertIn("| _Other_ | 1 |", table)

    def test_render_report_includes_summary_and_examples(self) -> None:
        report = build_safety_report.render_report(
            [
                self.finding(),
                self.finding(severity="high", rule_id="credential-print", line=8),
            ],
            roots=["skills"],
            min_severity="high",
            max_examples=1,
        )

        self.assertIn("Findings: **2**", report)
        self.assertIn("Critical: **1**", report)
        self.assertIn("High: **1**", report)
        self.assertIn("remote-shell-pipe", report)
        self.assertIn("Truncated 1 additional findings", report)

    def test_md_escape_protects_tables(self) -> None:
        self.assertEqual(build_safety_report.md_escape("a|b\nc"), "a\\|b c")

    def test_collect_findings_rejects_missing_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            with mock.patch.object(build_safety_report.scan, "ROOT", root):
                with self.assertRaises(FileNotFoundError):
                    build_safety_report.collect_findings(["missing"], "high", 750_000)


if __name__ == "__main__":
    unittest.main()
