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


class SubmoduleIndexTests(unittest.TestCase):
    def test_github_repo_slug_accepts_common_github_remote_urls(self) -> None:
        self.assertEqual(
            check_repo.github_repo_slug("https://github.com/owner/repo.git"),
            "owner/repo",
        )
        self.assertEqual(
            check_repo.github_repo_slug("git@github.com:owner/repo.git"),
            "owner/repo",
        )
        self.assertEqual(
            check_repo.github_repo_slug("ssh://git@github.com/owner/repo.git"),
            "owner/repo",
        )

    def test_github_repo_slug_rejects_non_repo_urls(self) -> None:
        self.assertIsNone(check_repo.github_repo_slug("https://example.com/owner/repo.git"))
        self.assertIsNone(check_repo.github_repo_slug("https://github.com/owner"))
        self.assertIsNone(check_repo.github_repo_slug("https://github.com/owner/repo/tree/main"))

    def test_parse_gitmodules_reports_section_path_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gitmodules = root / ".gitmodules"
            gitmodules.write_text(
                """
[submodule "skills/wrong"]
    path = skills/right
    url = https://example.com/right
""",
                encoding="utf-8",
            )

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.parse_gitmodules(gitmodules, reporter)

        self.assertIn("path mismatch", "\n".join(reporter.errors))

    def test_parse_gitmodules_reports_unsafe_relative_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gitmodules = root / ".gitmodules"
            gitmodules.write_text(
                """
[submodule "skills/bad"]
    path = skills/../bad
    url = https://github.com/owner/bad
""",
                encoding="utf-8",
            )

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.parse_gitmodules(gitmodules, reporter)

        self.assertIn("path is not a safe relative path", "\n".join(reporter.errors))

    def test_parse_gitmodules_reports_non_github_repo_url(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gitmodules = root / ".gitmodules"
            gitmodules.write_text(
                """
[submodule "skills/demo"]
    path = skills/demo
    url = https://example.com/owner/demo.git
""",
                encoding="utf-8",
            )

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.parse_gitmodules(gitmodules, reporter)

        self.assertIn("url is not a GitHub repository URL", "\n".join(reporter.errors))

    def test_check_submodule_index_rejects_unknown_top_level_category(self) -> None:
        reporter = check_repo.Reporter()
        with mock.patch.object(check_repo, "tracked_gitlinks", return_value={"docs/demo"}):
            check_repo.check_submodule_index(
                [check_repo.Submodule("docs/demo", "https://example.com/demo")],
                reporter,
            )

        messages = "\n".join(reporter.errors)
        self.assertIn(".gitmodules path uses unknown top-level category: docs/demo", messages)
        self.assertIn("tracked gitlink uses unknown top-level category: docs/demo", messages)

    def test_check_submodule_index_reports_duplicate_github_repo_slug(self) -> None:
        reporter = check_repo.Reporter()
        submodules = [
            check_repo.Submodule("skills/a", "https://github.com/owner/repo"),
            check_repo.Submodule("skills/b", "https://github.com/owner/repo.git"),
        ]

        with mock.patch.object(check_repo, "tracked_gitlinks", return_value={"skills/a", "skills/b"}):
            check_repo.check_submodule_index(submodules, reporter)

        self.assertIn("duplicate submodule GitHub repo: owner/repo", "\n".join(reporter.errors))

    def test_check_submodule_index_reports_missing_gitmodules_entry(self) -> None:
        reporter = check_repo.Reporter()
        with mock.patch.object(check_repo, "tracked_gitlinks", return_value={"skills/demo"}):
            check_repo.check_submodule_index([], reporter)

        self.assertIn(
            "tracked gitlink is missing from .gitmodules: skills/demo",
            "\n".join(reporter.errors),
        )


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
                            "collections": 2,
                            "template_skills": 0,
                            "without_frontmatter": 0,
                            "rebundled_copies": 0,
                        },
                        "collections": [
                            {
                                "name": "collection-a",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 0,
                            },
                            {
                                "name": "collection-b",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 0,
                            },
                        ],
                        "skills": [
                            {
                                "collection": "collection-a",
                                "path": "skills/collection-a/alpha/skill.md",
                                "content_hash": "1111111111111111",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "",
                            },
                            {
                                "collection": "collection-b",
                                "path": "skills/collection-b/beta/SKILL.md",
                                "content_hash": "2222222222222222",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "",
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
                            "collections": 1,
                            "template_skills": 0,
                            "without_frontmatter": 0,
                            "rebundled_copies": 0,
                        },
                        "collections": [
                            {
                                "name": "collection",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 0,
                            }
                        ],
                        "skills": [
                            {
                                "collection": "collection",
                                "path": "skills/collection/removed/SKILL.md",
                                "content_hash": "1111111111111111",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "",
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

    def test_catalog_manifest_reports_collection_summary_drift(self) -> None:
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
                            "collections": 1,
                            "template_skills": 0,
                            "without_frontmatter": 0,
                            "rebundled_copies": 0,
                        },
                        "collections": [
                            {
                                "name": "collection",
                                "skill_files": 2,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 0,
                            }
                        ],
                        "skills": [
                            {
                                "collection": "collection",
                                "path": "skills/collection/current/SKILL.md",
                                "content_hash": "1111111111111111",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_catalog_manifest([current], reporter)

        self.assertIn(
            "catalog/skills.json collections[0].skill_files is 2, but expected 1",
            "\n".join(reporter.errors),
        )

    def test_catalog_manifest_reports_invalid_content_hash(self) -> None:
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
                            "collections": 1,
                            "template_skills": 0,
                            "without_frontmatter": 0,
                            "rebundled_copies": 0,
                        },
                        "collections": [
                            {
                                "name": "collection",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 0,
                            }
                        ],
                        "skills": [
                            {
                                "collection": "collection",
                                "path": "skills/collection/current/SKILL.md",
                                "content_hash": "not-a-hash",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_catalog_manifest([current], reporter)

        self.assertIn("invalid content_hash", "\n".join(reporter.errors))

    def test_catalog_manifest_reports_invalid_generated_field_types(self) -> None:
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
                            "collections": 1,
                            "template_skills": 0,
                            "without_frontmatter": 0,
                            "rebundled_copies": 0,
                        },
                        "collections": [
                            {
                                "name": "collection",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 0,
                            }
                        ],
                        "skills": [
                            {
                                "collection": "collection",
                                "path": "skills/collection/current/SKILL.md",
                                "content_hash": "1111111111111111",
                                "has_frontmatter": True,
                                "has_name": "yes",
                                "is_template": False,
                                "duplicate_of": "",
                                "nested_depth": 0,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_catalog_manifest([current], reporter)

        self.assertIn("invalid has_name", "\n".join(reporter.errors))

    def test_catalog_manifest_accepts_cross_collection_rebundled_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_files = [
                root / "skills" / "collection-a" / "alpha" / "SKILL.md",
                root / "skills" / "collection-b" / "alpha" / "SKILL.md",
            ]
            for path in skill_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("---\nname: alpha\n---\n", encoding="utf-8")

            catalog = root / "catalog" / "skills.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(
                json.dumps(
                    {
                        "totals": {
                            "total_skill_files": 2,
                            "unique_skills": 1,
                            "collections": 2,
                            "template_skills": 0,
                            "without_frontmatter": 0,
                            "rebundled_copies": 1,
                        },
                        "collections": [
                            {
                                "name": "collection-a",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 1,
                            },
                            {
                                "name": "collection-b",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 1,
                            },
                        ],
                        "skills": [
                            {
                                "collection": "collection-a",
                                "path": "skills/collection-a/alpha/SKILL.md",
                                "content_hash": "aaaaaaaaaaaaaaaa",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "",
                            },
                            {
                                "collection": "collection-b",
                                "path": "skills/collection-b/alpha/SKILL.md",
                                "content_hash": "aaaaaaaaaaaaaaaa",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "skills/collection-a/alpha/SKILL.md",
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

    def test_catalog_manifest_reports_collection_path_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            current = root / "skills" / "actual" / "current" / "SKILL.md"
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
                            "collections": 1,
                            "template_skills": 0,
                            "without_frontmatter": 0,
                            "rebundled_copies": 0,
                        },
                        "collections": [
                            {
                                "name": "wrong",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 0,
                            }
                        ],
                        "skills": [
                            {
                                "collection": "wrong",
                                "path": "skills/actual/current/SKILL.md",
                                "content_hash": "1111111111111111",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_catalog_manifest([current], reporter)

        self.assertIn("path is outside that collection", "\n".join(reporter.errors))

    def test_catalog_manifest_reports_invalid_duplicate_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_files = [
                root / "skills" / "collection-a" / "alpha" / "SKILL.md",
                root / "skills" / "collection-b" / "alpha" / "SKILL.md",
            ]
            for path in skill_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("---\nname: alpha\n---\n", encoding="utf-8")

            catalog = root / "catalog" / "skills.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(
                json.dumps(
                    {
                        "totals": {
                            "total_skill_files": 2,
                            "unique_skills": 1,
                            "collections": 2,
                            "template_skills": 0,
                            "without_frontmatter": 0,
                            "rebundled_copies": 1,
                        },
                        "collections": [
                            {
                                "name": "collection-a",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 1,
                            },
                            {
                                "name": "collection-b",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 1,
                            },
                        ],
                        "skills": [
                            {
                                "collection": "collection-a",
                                "path": "skills/collection-a/alpha/SKILL.md",
                                "content_hash": "aaaaaaaaaaaaaaaa",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "",
                            },
                            {
                                "collection": "collection-b",
                                "path": "skills/collection-b/alpha/SKILL.md",
                                "content_hash": "aaaaaaaaaaaaaaaa",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "skills/missing/alpha/SKILL.md",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_catalog_manifest(skill_files, reporter)

        self.assertIn("duplicate_of target missing", "\n".join(reporter.errors))

    def test_catalog_manifest_reports_duplicate_target_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            skill_files = [
                root / "skills" / "collection-a" / "alpha" / "SKILL.md",
                root / "skills" / "collection-b" / "alpha" / "SKILL.md",
            ]
            for path in skill_files:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("---\nname: alpha\n---\n", encoding="utf-8")

            catalog = root / "catalog" / "skills.json"
            catalog.parent.mkdir(parents=True)
            catalog.write_text(
                json.dumps(
                    {
                        "totals": {
                            "total_skill_files": 2,
                            "unique_skills": 2,
                            "collections": 2,
                            "template_skills": 0,
                            "without_frontmatter": 0,
                            "rebundled_copies": 1,
                        },
                        "collections": [
                            {
                                "name": "collection-a",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 0,
                            },
                            {
                                "name": "collection-b",
                                "skill_files": 1,
                                "unique_skills": 1,
                                "template_skills": 0,
                                "rebundled_copies": 0,
                            },
                        ],
                        "skills": [
                            {
                                "collection": "collection-a",
                                "path": "skills/collection-a/alpha/SKILL.md",
                                "content_hash": "1111111111111111",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "",
                            },
                            {
                                "collection": "collection-b",
                                "path": "skills/collection-b/alpha/SKILL.md",
                                "content_hash": "2222222222222222",
                                "has_frontmatter": True,
                                "is_template": False,
                                "duplicate_of": "skills/collection-a/alpha/SKILL.md",
                            },
                        ],
                    }
                ),
                encoding="utf-8",
            )

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_catalog_manifest(skill_files, reporter)

        self.assertIn("duplicate_of target has different content_hash", "\n".join(reporter.errors))


class ReadmeCountTests(unittest.TestCase):
    def test_check_readme_counts_validates_chinese_category_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README_EN.md").write_text(
                """
**2 skills** across **4 repos**
2 reusable skill sets
1 end-to-end systems
1 benchmarks
0 curated collections
""",
                encoding="utf-8",
            )
            (root / "README.md").write_text(
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
            (root / "README_EN.md").write_text(
                """
**2 skills** across **4 repos**
2 reusable skill sets
1 end-to-end systems
1 benchmarks
0 curated collections
""",
                encoding="utf-8",
            )
            (root / "README.md").write_text(
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

        self.assertIn("README.md claims 99 skills", "\n".join(reporter.errors))

    def test_check_readme_counts_reports_bad_shields_skill_badge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README_EN.md").write_text(
                """
**2 skills** across **4 repos**
<img src="https://img.shields.io/badge/skills_collected-999-ff4e88" alt="2 skills">
2 reusable skill sets
1 end-to-end systems
1 benchmarks
0 curated collections
""",
                encoding="utf-8",
            )
            (root / "README.md").write_text(
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

        self.assertIn("README_EN.md claims 999 skills, but found 2", "\n".join(reporter.errors))

    def test_check_readme_counts_reports_missing_category_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README_EN.md").write_text(
                """
**2 skills** across **4 repos**
2 reusable skill sets
1 end-to-end systems
1 benchmarks
""",
                encoding="utf-8",
            )
            (root / "README.md").write_text(
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

        self.assertIn(
            "README_EN.md is missing a lists category count claim",
            "\n".join(reporter.errors),
        )

    def test_check_readme_counts_reports_missing_headline_claims(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README_EN.md").write_text(
                """
2 reusable skill sets
1 end-to-end systems
1 benchmarks
0 curated collections
""",
                encoding="utf-8",
            )
            (root / "README.md").write_text(
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

        messages = "\n".join(reporter.errors)
        self.assertIn("README_EN.md is missing a bundled repo count claim", messages)
        self.assertIn("README_EN.md is missing a headline skill count claim", messages)


class StarsManifestTests(unittest.TestCase):
    def test_check_stars_total_accepts_matching_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "STARS.md").write_text(
                """
# Star Leaderboard

Total bundled repos: **2**

| # | ⭐ | Repo | Bundled at |
|---|---|---|---|
| 1 | 10 | [owner/a](https://github.com/owner/a) | `skills/a` |
| 2 | 5 | [owner/b](https://github.com/owner/b) | `systems/b` |
""",
                encoding="utf-8",
            )
            submodules = [
                check_repo.Submodule("skills/a", "https://github.com/owner/a"),
                check_repo.Submodule("systems/b", "https://github.com/owner/b"),
            ]

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_stars_total(submodules, reporter)

        self.assertEqual(reporter.errors, [])

    def test_check_stars_total_reports_missing_and_mismatched_rows(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "STARS.md").write_text(
                """
# Star Leaderboard

Total bundled repos: **2**

| # | ⭐ | Repo | Bundled at |
|---|---|---|---|
| 1 | 10 | [owner/wrong](https://github.com/owner/wrong) | `skills/a` |
| 2 | 5 | [owner/old](https://github.com/owner/old) | `skills/old` |
""",
                encoding="utf-8",
            )
            submodules = [
                check_repo.Submodule("skills/a", "https://github.com/owner/a"),
                check_repo.Submodule("systems/b", "https://github.com/owner/b"),
            ]

            reporter = check_repo.Reporter()
            with mock.patch.object(check_repo, "ROOT", root):
                check_repo.check_stars_total(submodules, reporter)

        messages = "\n".join(reporter.errors)
        self.assertIn("STARS.md is missing bundled path(s): systems/b", messages)
        self.assertIn("STARS.md includes unknown bundled path(s): skills/old", messages)
        self.assertIn("STARS.md row for skills/a links owner/wrong", messages)


if __name__ == "__main__":
    unittest.main()
