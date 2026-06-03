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


if __name__ == "__main__":
    unittest.main()
