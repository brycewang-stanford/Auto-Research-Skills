import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


def load_update_stars_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "update-stars.py"
    spec = importlib.util.spec_from_file_location("update_stars_module", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/update-stars.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


update_stars = load_update_stars_module()


class GithubSlugTests(unittest.TestCase):
    def test_github_slug_accepts_https_and_ssh_urls(self) -> None:
        self.assertEqual(
            update_stars.github_slug("https://github.com/owner/repo.git"),
            "owner/repo",
        )
        self.assertEqual(
            update_stars.github_slug("git@github.com:owner/repo.git"),
            "owner/repo",
        )
        self.assertEqual(
            update_stars.github_slug("ssh://git@github.com/owner/repo.git"),
            "owner/repo",
        )

    def test_github_slug_rejects_non_github_urls(self) -> None:
        self.assertIsNone(update_stars.github_slug("https://example.com/owner/repo.git"))
        self.assertIsNone(update_stars.github_slug("https://github.com/owner"))
        self.assertIsNone(update_stars.github_slug("https://github.com/owner/repo/tree/main"))


class ParseSubmodulesTests(unittest.TestCase):
    def test_parse_submodules_skips_non_github_remotes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            gitmodules = root / ".gitmodules"
            gitmodules.write_text(
                """
[submodule "skills/good"]
    path = skills/good
    url = https://github.com/owner/good.git
[submodule "skills/mirror"]
    path = skills/mirror
    url = https://example.com/owner/mirror.git
""",
                encoding="utf-8",
            )

            with mock.patch.object(update_stars, "GITMODULES", gitmodules):
                result = update_stars.parse_submodules()

        self.assertEqual(result, [("skills/good", "owner/good")])


class ReadmeTopTests(unittest.TestCase):
    def test_render_top_ranks_and_skips_missing_counts(self) -> None:
        rows = [(2500, "systems/b", "o/b"), (900, "skills/a", "o/a"), (-1, "lists/c", "o/c")]
        block = update_stars.render_top(rows, "en", "2026-01-01")

        self.assertTrue(block.startswith(update_stars.TOP_START))
        self.assertTrue(block.endswith(update_stars.TOP_END))
        self.assertIn("| 🥇 | [o/b](https://github.com/o/b) | 2.5k | System |", block)
        self.assertIn("| 🥈 | [o/a](https://github.com/o/a) | 900 | Skills |", block)
        self.assertNotIn("o/c", block)

    def test_update_readmes_replaces_only_marked_block(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            readme = root / "README_EN.md"
            readme.write_text(
                f"intro\n{update_stars.TOP_START}\nstale\n{update_stars.TOP_END}\noutro\n",
                encoding="utf-8",
            )
            with mock.patch.object(update_stars, "ROOT", root):
                update_stars.update_readmes([(10, "skills/a", "o/a")], "2026-01-01")
            text = readme.read_text(encoding="utf-8")

        self.assertNotIn("stale", text)
        self.assertTrue(text.startswith("intro\n"))
        self.assertTrue(text.endswith("outro\n"))
        self.assertIn("[o/a](https://github.com/o/a)", text)


if __name__ == "__main__":
    unittest.main()
