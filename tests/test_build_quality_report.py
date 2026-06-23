import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import build_quality_report as bqr


def _skill(name, collection, content_hash, path, **overrides):
    values = {
        "name": name,
        "collection": collection,
        "content_hash": content_hash,
        "path": path,
        "has_frontmatter": True,
        "is_template": False,
        "license": "",
    }
    values.update(overrides)
    return values


class HelperTests(unittest.TestCase):
    def test_pct_rounds_and_guards_zero(self) -> None:
        self.assertEqual(bqr.pct(1, 4), 25)
        self.assertEqual(bqr.pct(728, 3324), 22)
        self.assertEqual(bqr.pct(5, 0), 0)

    def test_md_escape_protects_tables(self) -> None:
        self.assertEqual(bqr.md_escape("a|b\nc"), "a\\|b c")

    def test_name_collisions_requires_two_bodies_and_two_collections(self) -> None:
        skills = [
            # same name, different bodies, different collections -> collision
            _skill("paper-writing", "aris", "h1", "p1"),
            _skill("paper-writing", "phd", "h2", "p2"),
            # same name, same body across collections -> NOT a collision
            _skill("twin", "a", "same", "p3"),
            _skill("twin", "b", "same", "p4"),
            # same name, different bodies but ONE collection -> NOT cross-collection
            _skill("solo", "a", "x1", "p5"),
            _skill("solo", "a", "x2", "p6"),
        ]
        rows = bqr.name_collisions(skills)
        names = [name for name, _, _ in rows]
        self.assertEqual(names, ["paper-writing"])
        name, distinct, where = rows[0]
        self.assertEqual(distinct, 2)
        self.assertEqual(where, ["aris", "phd"])

    def test_name_collisions_orders_by_distinct_bodies_desc(self) -> None:
        skills = [
            _skill("a", "c1", "a1", "p"),
            _skill("a", "c2", "a2", "p"),
            _skill("b", "c1", "b1", "p"),
            _skill("b", "c2", "b2", "p"),
            _skill("b", "c3", "b3", "p"),
        ]
        rows = bqr.name_collisions(skills)
        # "b" has 3 distinct bodies, "a" has 2 -> b first
        self.assertEqual([name for name, _, _ in rows], ["b", "a"])

    def test_no_frontmatter_counts_by_collection(self) -> None:
        skills = [
            _skill("a", "c1", "h", "p", has_frontmatter=False),
            _skill("b", "c1", "h", "p", has_frontmatter=False),
            _skill("c", "c2", "h", "p", has_frontmatter=False),
            _skill("d", "c2", "h", "p", has_frontmatter=True),
        ]
        counts = bqr.no_frontmatter(skills)
        self.assertEqual(counts["c1"], 2)
        self.assertEqual(counts["c2"], 1)


class WatermarkTests(unittest.TestCase):
    def test_count_watermarks_detects_comment_before_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "wm.md").write_text(
                "<!-- collected by SomeBot -->\n---\nname: x\n---\nbody\n",
                encoding="utf-8",
            )
            (root / "clean.md").write_text("---\nname: y\n---\nbody\n", encoding="utf-8")
            (root / "comment-no-fm.md").write_text("<!-- note -->\n# Title\n", encoding="utf-8")
            skills = [
                _skill("x", "demo", "h1", "wm.md"),
                _skill("y", "demo", "h2", "clean.md"),
                _skill("z", "other", "h3", "comment-no-fm.md"),
                _skill("missing", "demo", "h4", "does-not-exist.md"),
            ]
            with mock.patch.object(bqr, "ROOT", root):
                per_collection, total, missing = bqr.count_watermarks(skills)
        self.assertEqual(total, 1)
        self.assertEqual(per_collection["demo"], 1)
        self.assertEqual(missing, 1)


class RenderTests(unittest.TestCase):
    def _data(self):
        return {
            "skills": [
                _skill("paper-writing", "aris", "h1", "clean.md", license="MIT"),
                _skill("paper-writing", "phd", "h2", "clean.md"),
                _skill("tmpl", "aris", "h3", "clean.md", is_template=True),
                _skill("nofm", "phd", "h4", "clean.md", has_frontmatter=False),
            ],
            "totals": {
                "total_skill_files": 4,
                "unique_skills": 4,
                "rebundled_copies": 0,
                "template_skills": 1,
                "without_frontmatter": 1,
            },
            "collections": [
                {"name": "aris", "skill_files": 3, "unique_skills": 3, "rebundled_copies": 2},
                {"name": "phd", "skill_files": 1, "unique_skills": 1, "rebundled_copies": 0},
            ],
        }

    def test_render_report_includes_key_findings(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.md").write_text("---\nname: y\n---\n", encoding="utf-8")
            with mock.patch.object(bqr, "ROOT", root):
                report = bqr.render_report(self._data(), collision_rows=12, offender_rows=8)
        self.assertIn("**4**", report)  # headline file count
        self.assertNotIn("198", report)  # no stale hardcoded count
        self.assertIn("1 skill names", report)  # exactly one collision (paper-writing)
        self.assertIn("`paper-writing`", report)
        self.assertIn("Only 25% of skills declare a license", report)
        self.assertIn("`aris`", report)  # top re-bundling offender
        self.assertNotIn("test-skill", report)
        self.assertIn("Placeholder / template skills (1)", report)

    def test_render_report_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "clean.md").write_text("---\nname: y\n---\n", encoding="utf-8")
            with mock.patch.object(bqr, "ROOT", root):
                first = bqr.render_report(self._data(), 12, 8)
                second = bqr.render_report(self._data(), 12, 8)
        self.assertEqual(first, second)


class CheckReportTests(unittest.TestCase):
    def test_check_report_detects_missing_and_outdated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "QUALITY.md"
            with mock.patch.object(bqr, "REPORT_PATH", path):
                self.assertEqual(bqr.check_report("content\n"), 1)  # missing
                path.write_text("stale\n", encoding="utf-8")
                self.assertEqual(bqr.check_report("content\n"), 1)  # outdated
                path.write_text("content\n", encoding="utf-8")
                self.assertEqual(bqr.check_report("content\n"), 0)  # current


if __name__ == "__main__":
    unittest.main()
