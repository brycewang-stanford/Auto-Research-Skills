import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import build_maturity_report as bmr


def _depth(path, collection, signals):
    return bmr.SkillDepth(path=path, collection=collection, signals=set(signals))


class SignalDetectionTests(unittest.TestCase):
    def _dir_with(self, *, dirs=(), files=()):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        (root / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        for d in dirs:
            (root / d).mkdir()
        for f in files:
            (root / f).write_text("x", encoding="utf-8")
        return root

    def test_detects_directory_signals(self) -> None:
        d = self._dir_with(dirs=("references", "examples", "tests", "assets", "templates"))
        signals = bmr._dir_signals(d)
        self.assertEqual(
            signals, {"references", "examples", "tests", "assets", "templates"}
        )

    def test_code_signal_from_scripts_dir_or_sibling_file(self) -> None:
        self.assertIn("code", bmr._dir_signals(self._dir_with(dirs=("scripts",))))
        self.assertIn("code", bmr._dir_signals(self._dir_with(files=("run.py",))))
        self.assertIn("code", bmr._dir_signals(self._dir_with(files=("go.sh",))))
        self.assertNotIn("code", bmr._dir_signals(self._dir_with(files=("notes.md",))))

    def test_evals_signal_from_dir_or_json(self) -> None:
        self.assertIn("evals", bmr._dir_signals(self._dir_with(dirs=("evals",))))
        self.assertIn("evals", bmr._dir_signals(self._dir_with(files=("evals.json",))))

    def test_manifest_and_requirements(self) -> None:
        s = bmr._dir_signals(self._dir_with(files=("manifest.yaml", "requirements.txt")))
        self.assertEqual(s, {"manifest", "requirements"})

    def test_bare_skill_has_no_signals(self) -> None:
        self.assertEqual(bmr._dir_signals(self._dir_with()), set())


class DepthModelTests(unittest.TestCase):
    def test_score_rich_and_bare(self) -> None:
        rich = _depth("p", "c", ["references", "code", "tests"])
        self.assertEqual(rich.score, 3)
        self.assertTrue(rich.is_rich)
        self.assertFalse(rich.is_bare)

        bare = _depth("p", "c", [])
        self.assertTrue(bare.is_bare)
        self.assertFalse(bare.is_rich)

        moderate = _depth("p", "c", ["references", "code"])
        self.assertFalse(moderate.is_rich)
        self.assertFalse(moderate.is_bare)


class ScanTests(unittest.TestCase):
    def test_scan_counts_missing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "skills" / "c" / "s").mkdir(parents=True)
            (root / "skills" / "c" / "s" / "SKILL.md").write_text("x", encoding="utf-8")
            (root / "skills" / "c" / "s" / "references").mkdir()
            catalog = {
                "skills": [
                    {"path": "skills/c/s/SKILL.md", "collection": "c"},
                    {"path": "skills/c/gone/SKILL.md", "collection": "c"},
                ]
            }
            with mock.patch.object(bmr, "ROOT", root):
                rows, missing = bmr.scan(catalog)
        self.assertEqual(missing, 1)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].signals, {"references"})


class RenderTests(unittest.TestCase):
    def _rows(self):
        return [
            _depth("skills/deep/a/SKILL.md", "deep", ["references", "code", "tests", "evals"]),
            _depth("skills/deep/b/SKILL.md", "deep", ["references", "code", "examples"]),
            _depth("skills/thin/c/SKILL.md", "thin", []),
            _depth("skills/thin/d/SKILL.md", "thin", ["references"]),
        ]

    def test_render_report_includes_rankings_and_stats(self) -> None:
        report = bmr.render_report(self._rows(), missing=0)
        self.assertIn("Skill maturity & depth", report)
        self.assertIn("**4**", report)  # inspected count
        # "deep" is 100% rich, "thin" 0% -> deep ranks first
        deep_pos = report.find("`deep`")
        thin_pos = report.find("`thin`")
        self.assertLess(deep_pos, thin_pos)

    def test_render_report_notes_missing(self) -> None:
        report = bmr.render_report(self._rows(), missing=2)
        self.assertIn("2 `SKILL.md` path(s)", report)

    def test_render_report_is_deterministic(self) -> None:
        self.assertEqual(
            bmr.render_report(self._rows(), 0), bmr.render_report(self._rows(), 0)
        )


class CheckReportTests(unittest.TestCase):
    def test_check_report_detects_missing_and_outdated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "MATURITY.md"
            with mock.patch.object(bmr, "REPORT_PATH", path):
                self.assertEqual(bmr.check_report("content\n"), 1)  # missing
                path.write_text("stale\n", encoding="utf-8")
                self.assertEqual(bmr.check_report("content\n"), 1)  # outdated
                path.write_text("content\n", encoding="utf-8")
                self.assertEqual(bmr.check_report("content\n"), 0)  # current


if __name__ == "__main__":
    unittest.main()
