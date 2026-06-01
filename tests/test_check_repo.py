import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def load_check_repo_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "check-repo.py"
    spec = importlib.util.spec_from_file_location("check_repo_module", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/check-repo.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


check_repo = load_check_repo_module()


class CatalogManifestTests(unittest.TestCase):
    def test_catalog_manifest_accepts_current_paths_and_totals(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_files = [
                root / "skills" / "collection-a" / "alpha" / "skill.md",
                root / "skills" / "collection-b" / "beta" / "SKILL.md",
            ]
            for path in skill_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("---\nname: x\n---\n", encoding="utf-8")

            catalog = root / "catalog" / "skills.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(
                json.dumps(
                    {
                        "totals": {
                            "total_skill_files": 2,
                            "unique_skills": 2,
                            "rebundled_copies": 0,
                        },
                        "skills": [
                            {
                                "path": "skills/collection-a/alpha/skill.md",
                                "content_hash": "h1",
                            },
                            {
                                "path": "skills/collection-b/beta/SKILL.md",
                                "content_hash": "h2",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_catalog_manifest(skill_files, reporter)

        self.assertEqual(reporter.errors, [])

    def test_catalog_manifest_reports_missing_and_stale_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "skills" / "collection" / "current" / "SKILL.md"
            current.parent.mkdir(parents=True)
            current.write_text("---\nname: current\n---\n", encoding="utf-8")

            catalog = root / "catalog" / "skills.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(
                json.dumps(
                    {
                        "totals": {
                            "total_skill_files": 1,
                            "unique_skills": 1,
                            "rebundled_copies": 0,
                        },
                        "skills": [
                            {
                                "path": "skills/collection/removed/SKILL.md",
                                "content_hash": "h1",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_catalog_manifest([current], reporter)

        messages = "\n".join(reporter.errors)
        self.assertIn("missing current skill path", messages)
        self.assertIn("includes removed skill path", messages)


class ReadmeCountTests(unittest.TestCase):
    def test_check_readme_counts_validates_chinese_category_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                """
**2 skills** across **4 repos**
2 reusable skill sets
1 end-to-end systems
1 benchmarks
0 curated collections
""",
                encoding="utf-8",
            )
            (root / "README_CN.md").write_text(
                """
**2 个 skills**、分布在 **4 个仓库**
- **`skills/`** —— 2 个可复用技能集与插件合集
- **`systems/`** —— 1 个端到端系统与自主智能体
- **`benchmarks/`** —— 1 个自主研究 / ML 工程评测基准
- **`lists/`** —— 0 个精选清单与综述
""",
                encoding="utf-8",
            )
            skill_files = [
                root / "skills" / "a" / "SKILL.md",
                root / "skills" / "b" / "skill.md",
            ]
            submodules = [
                check_repo.Submodule("skills/a", "https://example.com/a"),
                check_repo.Submodule("skills/b", "https://example.com/b"),
                check_repo.Submodule("systems/s", "https://example.com/s"),
                check_repo.Submodule("benchmarks/b", "https://example.com/bench"),
            ]
            counts = {"skills": 2, "systems": 1, "benchmarks": 1, "lists": 0}

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_readme_counts(submodules, counts, skill_files, reporter)

        self.assertEqual(reporter.errors, [])

    def test_check_readme_counts_reports_chinese_category_drift(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                """
**2 skills** across **4 repos**
2 reusable skill sets
1 end-to-end systems
1 benchmarks
0 curated collections
""",
                encoding="utf-8",
            )
            (root / "README_CN.md").write_text(
                """
**2 个 skills**、分布在 **4 个仓库**
- **`skills/`** —— 99 个可复用技能集与插件合集
- **`systems/`** —— 1 个端到端系统与自主智能体
- **`benchmarks/`** —— 1 个自主研究 / ML 工程评测基准
- **`lists/`** —— 0 个精选清单与综述
""",
                encoding="utf-8",
            )
            skill_files = [
                root / "skills" / "a" / "SKILL.md",
                root / "skills" / "b" / "skill.md",
            ]
            submodules = [
                check_repo.Submodule("skills/a", "https://example.com/a"),
                check_repo.Submodule("skills/b", "https://example.com/b"),
                check_repo.Submodule("systems/s", "https://example.com/s"),
                check_repo.Submodule("benchmarks/b", "https://example.com/bench"),
            ]
            counts = {"skills": 2, "systems": 1, "benchmarks": 1, "lists": 0}

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_readme_counts(submodules, counts, skill_files, reporter)

        self.assertIn("README_CN.md claims 99 skills", "\n".join(reporter.errors))


if __name__ == "__main__":
    unittest.main()
