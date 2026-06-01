import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import check_site


class LinkedAssetsTests(unittest.TestCase):
    def test_linked_assets_extracts_local_references(self) -> None:
        html = """
<link rel="stylesheet" href="styles.css">
<script src="app.js"></script>
<img src="../readme.png" alt="">
"""

        self.assertEqual(
            check_site.linked_assets(html),
            {"styles.css", "app.js", "../readme.png"},
        )


class HtmlContractTests(unittest.TestCase):
    def valid_html(self) -> str:
        controls = "\n".join(f'<div id="{value}"></div>' for value in check_site.REQUIRED_INDEX_IDS)
        return f"<html><body>{controls}<noscript>Fallback</noscript></body></html>"

    def test_check_html_contract_accepts_required_ids_and_noscript(self) -> None:
        self.assertEqual(
            check_site.check_html_contract(
                self.valid_html(),
                check_site.REQUIRED_INDEX_IDS,
                "site/index.html",
                require_noscript=True,
            ),
            [],
        )

    def test_check_html_contract_reports_missing_id(self) -> None:
        html = self.valid_html().replace('id="query"', 'id="other"', 1)

        errors = check_site.check_html_contract(html, check_site.REQUIRED_INDEX_IDS, "site/index.html")

        self.assertIn("missing required ids: query", "\n".join(errors))

    def test_check_html_contract_reports_duplicate_ids(self) -> None:
        html = self.valid_html().replace("</body>", '<div id="query"></div></body>', 1)

        errors = check_site.check_html_contract(html, check_site.REQUIRED_INDEX_IDS, "site/index.html")

        self.assertIn("duplicate ids: query", "\n".join(errors))

    def test_check_html_contract_requires_noscript(self) -> None:
        html = self.valid_html().replace("<noscript>Fallback</noscript>", "")

        errors = check_site.check_html_contract(
            html,
            check_site.REQUIRED_INDEX_IDS,
            "site/index.html",
            require_noscript=True,
        )

        self.assertIn("noscript fallback", "\n".join(errors))


class SearchIndexContractTests(unittest.TestCase):
    def valid_payload(self) -> dict:
        return {
            "totals": {
                "skill_files": 1,
                "unique_skills": 1,
                "collections": 1,
                "name_collisions": 0,
            },
            "tags": ["writing"],
            "collections": [{"name": "demo", "skill_files": 1, "unique_skills": 1}],
            "skills": [
                {
                    "name": "paper-writing",
                    "collection": "demo",
                    "trigger": "Write a paper.",
                    "path": "skills/demo/paper-writing/SKILL.md",
                }
            ],
        }

    def test_check_index_payload_accepts_valid_index(self) -> None:
        self.assertEqual(check_site.check_index_payload(self.valid_payload()), [])

    def test_check_index_payload_reports_missing_totals(self) -> None:
        payload = self.valid_payload()
        del payload["totals"]["skill_files"]

        errors = check_site.check_index_payload(payload)

        self.assertIn("totals.skill_files", "\n".join(errors))

    def test_check_index_payload_reports_missing_skill_keys(self) -> None:
        payload = self.valid_payload()
        del payload["skills"][0]["trigger"]

        errors = check_site.check_index_payload(payload)

        self.assertIn("skills[0] missing keys: trigger", "\n".join(errors))


class CollisionsContractTests(unittest.TestCase):
    def valid_payload(self) -> dict:
        return {
            "count": 1,
            "collisions": [
                {
                    "name": "analysis",
                    "collections": 2,
                    "distinct_bodies": 2,
                    "variants": [
                        {
                            "collection": "a",
                            "trigger": "Analyze data.",
                            "path": "skills/a/analysis/SKILL.md",
                        }
                    ],
                }
            ],
        }

    def test_check_collisions_payload_accepts_valid_payload(self) -> None:
        self.assertEqual(check_site.check_collisions_payload(self.valid_payload()), [])

    def test_check_collisions_payload_reports_missing_variant_keys(self) -> None:
        payload = self.valid_payload()
        del payload["collisions"][0]["variants"][0]["path"]

        errors = check_site.check_collisions_payload(payload)

        self.assertIn("missing keys: path", "\n".join(errors))


class SiteMainTests(unittest.TestCase):
    def write_site_fixture(self, root: Path) -> None:
        site = root / "site"
        catalog = root / "catalog"
        site.mkdir()
        catalog.mkdir()
        (root / "readme.png").write_bytes(b"png")
        (site / "styles.css").write_text("body { color: #111; }\n", encoding="utf-8")
        (site / "app.js").write_text(
            "fetch('../catalog/search-index.json');\n",
            encoding="utf-8",
        )
        (site / "collisions.js").write_text(
            "fetch('../catalog/collisions.json');\n",
            encoding="utf-8",
        )
        (site / "index.html").write_text(
            f"""
<html>
  <head><link rel="stylesheet" href="styles.css"></head>
  <body>
    <img src="../readme.png" alt="">
    {"".join(f'<div id="{value}"></div>' for value in check_site.REQUIRED_INDEX_IDS)}
    <noscript>Fallback</noscript>
    <script src="app.js"></script>
  </body>
</html>
""",
            encoding="utf-8",
        )
        (site / "collisions.html").write_text(
            f"""
<html>
  <head><link rel="stylesheet" href="styles.css"></head>
  <body>
    {"".join(f'<div id="{value}"></div>' for value in check_site.REQUIRED_COLLISIONS_IDS)}
    <script src="collisions.js"></script>
  </body>
</html>
""",
            encoding="utf-8",
        )
        (catalog / "search-index.json").write_text(
            """
{
  "totals": {"skill_files": 1, "unique_skills": 1, "collections": 1, "name_collisions": 0},
  "tags": [],
  "collections": [{"name": "demo", "skill_files": 1, "unique_skills": 1}],
  "skills": [{"name": "x", "collection": "demo", "trigger": "Run x.", "path": "skills/demo/x/SKILL.md"}]
}
""",
            encoding="utf-8",
        )
        (catalog / "collisions.json").write_text(
            """
{
  "count": 1,
  "collisions": [
    {
      "name": "analysis",
      "collections": 2,
      "distinct_bodies": 2,
      "variants": [{"collection": "a", "trigger": "Analyze data.", "path": "skills/a/analysis/SKILL.md"}]
    }
  ]
}
""",
            encoding="utf-8",
        )

    def test_main_accepts_valid_site_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_site_fixture(root)
            with (
                mock.patch.object(check_site, "ROOT", root),
                mock.patch.object(check_site, "SITE", root / "site"),
                mock.patch.object(check_site, "INDEX", root / "catalog" / "search-index.json"),
                mock.patch.object(check_site, "COLLISIONS", root / "catalog" / "collisions.json"),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                result = check_site.main()

        self.assertEqual(result, 0)

    def test_main_rejects_asset_that_escapes_repo_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_site_fixture(root)
            (root / "site" / "index.html").write_text(
                '<link rel="stylesheet" href="../../outside.css">',
                encoding="utf-8",
            )
            with (
                mock.patch.object(check_site, "ROOT", root),
                mock.patch.object(check_site, "SITE", root / "site"),
                mock.patch.object(check_site, "INDEX", root / "catalog" / "search-index.json"),
                mock.patch.object(check_site, "COLLISIONS", root / "catalog" / "collisions.json"),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                result = check_site.main()

        self.assertEqual(result, 1)

    def test_main_rejects_malformed_search_index(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write_site_fixture(root)
            (root / "catalog" / "search-index.json").write_text("{not json", encoding="utf-8")
            with (
                mock.patch.object(check_site, "ROOT", root),
                mock.patch.object(check_site, "SITE", root / "site"),
                mock.patch.object(check_site, "INDEX", root / "catalog" / "search-index.json"),
                mock.patch.object(check_site, "COLLISIONS", root / "catalog" / "collisions.json"),
                contextlib.redirect_stderr(io.StringIO()),
            ):
                result = check_site.main()

        self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
