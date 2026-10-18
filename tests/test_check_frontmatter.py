import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import build_catalog as bc
from tools import check_frontmatter as cf


def _row(path, collection, **overrides):
    values = {
        "path": path,
        "collection": collection,
        "has_frontmatter": True,
        "has_name": True,
        "has_description": True,
        "has_license": False,
        "has_version": False,
    }
    values.update(overrides)
    return cf.SkillFM(**values)


class HelperTests(unittest.TestCase):
    def test_pct_rounds_and_guards_zero(self) -> None:
        self.assertEqual(cf.pct(1, 4), 25)
        self.assertEqual(cf.pct(5, 0), 0)

    def test_md_escape_protects_tables(self) -> None:
        self.assertEqual(cf.md_escape("a|b\nc"), "a\\|b c")


class ConformsTests(unittest.TestCase):
    def test_conforms_requires_frontmatter_name_and_description(self) -> None:
        self.assertTrue(_row("p", "c").conforms)
        self.assertFalse(_row("p", "c", has_frontmatter=False).conforms)
        self.assertFalse(_row("p", "c", has_name=False).conforms)
        self.assertFalse(_row("p", "c", has_description=False).conforms)


class ScanTests(unittest.TestCase):
    def test_scan_reads_fields_from_disk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skills = root / "skills"
            (skills / "good" / "a").mkdir(parents=True)
            (skills / "good" / "a" / "SKILL.md").write_text(
                "---\nname: a\ndescription: does a thing\nlicense: MIT\nversion: 1.0.0\n---\nbody\n",
                encoding="utf-8",
            )
            (skills / "bad" / "b").mkdir(parents=True)
            (skills / "bad" / "b" / "SKILL.md").write_text(
                "# no frontmatter here\n", encoding="utf-8"
            )
            with mock.patch.object(bc, "SKILLS_DIR", skills), mock.patch.object(
                cf, "ROOT", root
            ):
                rows = cf.scan()
        by_path = {Path(r.path).parts[-2]: r for r in rows}
        self.assertTrue(by_path["a"].conforms)
        self.assertTrue(by_path["a"].has_license)
        self.assertTrue(by_path["a"].has_version)
        self.assertFalse(by_path["b"].has_frontmatter)
        self.assertFalse(by_path["b"].conforms)


class RenderTests(unittest.TestCase):
    def _rows(self):
        return [
            _row("skills/aris/x/SKILL.md", "aris", has_license=True, has_version=True),
            _row("skills/aris/y/SKILL.md", "aris"),
            _row("skills/phd/z/SKILL.md", "phd", has_frontmatter=False,
                 has_name=False, has_description=False),
        ]

    def test_render_report_includes_key_findings(self) -> None:
        report = cf.render_report(self._rows())
        self.assertIn("Frontmatter conformance", report)
        self.assertIn("**3**", report)  # scanned count
        self.assertIn("(67%)", report)  # 2/3 conform
        self.assertIn("`phd`", report)  # the non-conforming collection
        self.assertNotIn("`aris`", report.split("non-conforming")[-1])

    def test_render_report_all_good(self) -> None:
        report = cf.render_report([_row("skills/a/x/SKILL.md", "a")])
        self.assertIn("✅", report)

    def test_render_report_is_deterministic(self) -> None:
        self.assertEqual(cf.render_report(self._rows()), cf.render_report(self._rows()))


class CheckReportTests(unittest.TestCase):
    def test_check_report_detects_missing_and_outdated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "FRONTMATTER.md"
            with mock.patch.object(cf, "REPORT_PATH", path):
                self.assertEqual(cf.check_report("content\n"), 1)  # missing
                path.write_text("stale\n", encoding="utf-8")
                self.assertEqual(cf.check_report("content\n"), 1)  # outdated
                path.write_text("content\n", encoding="utf-8")
                self.assertEqual(cf.check_report("content\n"), 0)  # current


if __name__ == "__main__":
    unittest.main()
