import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import check_docs


class CheckDocsTests(unittest.TestCase):
    def test_strip_code_fences_removes_links_inside_fences(self) -> None:
        text = "before\n```bash\n[missing](nope.md)\n```\nafter\n"

        cleaned = check_docs.strip_code_fences(text)

        self.assertNotIn("nope.md", cleaned)
        self.assertEqual(cleaned.count("\n"), text.count("\n"))

    def test_links_in_text_ignores_inline_code_links(self) -> None:
        path = Path("README.md")
        links = check_docs.links_in_text(
            path,
            "`[example](missing.md)`\n[real](docs/a.md)\n",
        )

        self.assertEqual([link.target for link in links], ["docs/a.md"])
        self.assertEqual(links[0].line, 2)

    def test_links_in_text_extracts_markdown_images_and_html_attrs(self) -> None:
        path = Path("README.md")
        links = check_docs.links_in_text(
            path,
            '[doc](docs/a.md) ![logo](readme.png) <a href="CONTRIBUTING.md">x</a>',
        )

        self.assertEqual([link.target for link in links], ["docs/a.md", "readme.png", "CONTRIBUTING.md"])

    def test_links_in_text_extracts_angle_bracket_targets(self) -> None:
        path = Path("README.md")
        links = check_docs.links_in_text(
            path,
            '[doc](<docs/a.md>) ![logo](<readme.png>)',
        )

        self.assertEqual([link.target for link in links], ["docs/a.md", "readme.png"])

    def test_links_in_text_extracts_targets_with_single_quoted_titles(self) -> None:
        path = Path("README.md")
        links = check_docs.links_in_text(
            path,
            "[doc](docs/a.md 'Guide') ![logo](readme.png 'Logo')",
        )

        self.assertEqual([link.target for link in links], ["docs/a.md", "readme.png"])

    def test_links_in_text_extracts_reference_style_definitions(self) -> None:
        path = Path("README.md")
        links = check_docs.links_in_text(
            path,
            "[guide]: docs/guide.md 'Guide'\n[logo]: <readme.png>\n[^note]: not-a-link.md\n",
        )

        self.assertEqual([link.target for link in links], ["docs/guide.md", "readme.png"])

    def test_check_link_accepts_existing_local_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "docs" / "README.md"
            target = root / "docs" / "guide.md"
            source.parent.mkdir()
            source.write_text("[guide](guide.md)", encoding="utf-8")
            target.write_text("ok", encoding="utf-8")
            link = check_docs.DocLink(source, "guide.md", 1)

            with mock.patch.object(check_docs, "ROOT", root):
                error = check_docs.check_link(link)

        self.assertIsNone(error)

    def test_check_link_accepts_existing_same_page_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "README.md"
            source.write_text(
                "[section](#-deep-research--literature)\n\n"
                "## 🔎 Deep Research & Literature\n",
                encoding="utf-8",
            )
            link = check_docs.DocLink(source, "#-deep-research--literature", 1)

            with mock.patch.object(check_docs, "ROOT", root):
                error = check_docs.check_link(link)

        self.assertIsNone(error)

    def test_check_link_accepts_existing_cross_file_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "README.md"
            target = root / "docs" / "guide.md"
            target.parent.mkdir()
            source.write_text("[guide](docs/guide.md#setup)", encoding="utf-8")
            target.write_text("# Setup\n", encoding="utf-8")
            link = check_docs.DocLink(source, "docs/guide.md#setup", 1)

            with mock.patch.object(check_docs, "ROOT", root):
                error = check_docs.check_link(link)

        self.assertIsNone(error)

    def test_check_link_reports_missing_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "README.md"
            source.write_text("[missing](#missing)\n\n## Present\n", encoding="utf-8")
            link = check_docs.DocLink(source, "#missing", 1)

            with mock.patch.object(check_docs, "ROOT", root):
                error = check_docs.check_link(link)

        self.assertIn("anchor missing", error or "")

    def test_check_link_reports_missing_local_target(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "README.md"
            source.write_text("[missing](missing.md)", encoding="utf-8")
            link = check_docs.DocLink(source, "missing.md", 1)

            with mock.patch.object(check_docs, "ROOT", root):
                error = check_docs.check_link(link)

        self.assertIn("target missing", error or "")

    def test_check_link_rejects_repo_escape(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "docs" / "README.md"
            source.parent.mkdir()
            source.write_text("[bad](../../outside.md)", encoding="utf-8")
            link = check_docs.DocLink(source, "../../outside.md", 1)

            with mock.patch.object(check_docs, "ROOT", root):
                error = check_docs.check_link(link)

        self.assertIn("escapes repo root", error or "")

    def test_iter_markdown_files_skips_vendored_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "catalog").mkdir()
            (root / "catalog" / "README.md").write_text("ok", encoding="utf-8")
            (root / "skills" / "demo").mkdir(parents=True)
            (root / "skills" / "demo" / "README.md").write_text("skip", encoding="utf-8")

            with mock.patch.object(check_docs, "ROOT", root):
                files = check_docs.iter_markdown_files(["catalog", "skills"])

        self.assertEqual([path.name for path in files], ["README.md"])

    def test_iter_markdown_files_is_case_insensitive(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "docs" / "README.MD").write_text("ok", encoding="utf-8")

            with mock.patch.object(check_docs, "ROOT", root):
                files = check_docs.iter_markdown_files(["docs"])

        self.assertEqual([path.name for path in files], ["README.MD"])

    def test_missing_roots_reports_absent_doc_roots(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            missing = root / "missing-docs"

            with mock.patch.object(check_docs, "ROOT", root):
                result = check_docs.missing_roots([missing])

        self.assertEqual(result, ["missing-docs"])


if __name__ == "__main__":
    unittest.main()
