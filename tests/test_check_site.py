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
<a href="collisions.html">Collisions</a>
"""

        self.assertEqual(
            check_site.linked_assets(html),
            {"styles.css", "app.js", "../readme.png", "collisions.html"},
        )

    def test_linked_assets_extracts_single_quoted_references(self) -> None:
        html = """
<link rel='stylesheet' href='styles.css'>
<script src='app.js'></script>
<img src='../readme.png' alt=''>
"""

        self.assertEqual(
            check_site.linked_assets(html),
            {"styles.css", "app.js", "../readme.png"},
        )

    def test_check_local_assets_ignores_query_and_fragment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "site"
            site.mkdir()
            (site / "styles.css").write_text("ok", encoding="utf-8")
            html_path = site / "index.html"
            html_path.write_text("", encoding="utf-8")

            errors = check_site.check_local_assets(
                '<link rel="stylesheet" href="styles.css?v=1#main">',
                html_path,
                root.resolve(),
            )

        self.assertEqual(errors, [])

    def test_check_local_assets_accepts_root_relative_repo_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "site"
            site.mkdir()
            (site / "styles.css").write_text("ok", encoding="utf-8")
            html_path = site / "index.html"
            html_path.write_text("", encoding="utf-8")

            errors = check_site.check_local_assets(
                '<link rel="stylesheet" href="/site/styles.css">',
                html_path,
                root.resolve(),
            )

        self.assertEqual(errors, [])

    def test_css_assets_extracts_url_references(self) -> None:
        css = """
.hero { background-image: url("../readme.png"); }
@font-face { src: url(fonts/site.woff2); }
.external { background: url(https://example.com/a.png); }
"""

        self.assertEqual(
            check_site.css_assets(css),
            {"../readme.png", "fonts/site.woff2", "https://example.com/a.png"},
        )

    def test_check_local_css_assets_reports_missing_local_references(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            site = root / "site"
            site.mkdir()
            css_path = site / "styles.css"
            css_path.write_text("", encoding="utf-8")

            errors = check_site.check_local_css_assets(
                ".hero { background-image: url(missing.png); }",
                css_path,
                root.resolve(),
            )

        self.assertIn("site CSS asset not found: missing.png", errors)


class HtmlContractTests(unittest.TestCase):
    def valid_html(self) -> str:
        controls = "\n".join(f'<div id="{value}"></div>' for value in check_site.REQUIRED_INDEX_IDS)
        return f"<html><body>{controls}<noscript>Fallback</noscript></body></html>"

    def test_element_ids_extracts_single_and_double_quoted_ids(self) -> None:
        html = "<div id='query'></div><div id=\"results\"></div>"

        self.assertEqual(check_site.element_ids(html), {"query", "results"})

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

    def test_check_html_contract_accepts_single_quoted_ids(self) -> None:
        controls = "\n".join(f"<div id='{value}'></div>" for value in check_site.REQUIRED_INDEX_IDS)
        html = f"<html><body>{controls}<noscript>Fallback</noscript></body></html>"

        self.assertEqual(
            check_site.check_html_contract(
                html,
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
            "generated_by": "tools/build_index.py",
            "totals": {
                "skill_files": 1,
                "unique_skills": 1,
                "collections": 1,
                "templates": 0,
                "no_frontmatter": 0,
                "rebundled": 0,
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
                    "tags": ["writing"],
                }
            ],
        }

    def test_check_index_payload_accepts_valid_index(self) -> None:
        self.assertEqual(check_site.check_index_payload(self.valid_payload()), [])

    def test_check_index_payload_reports_wrong_generator(self) -> None:
        payload = self.valid_payload()
        payload["generated_by"] = "manual"

        errors = check_site.check_index_payload(payload)

        self.assertIn("generated_by must be tools/build_index.py", "\n".join(errors))

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

    def test_check_index_payload_reports_total_drift(self) -> None:
        payload = self.valid_payload()
        payload["totals"]["skill_files"] = 2

        errors = check_site.check_index_payload(payload)

        self.assertIn("totals.skill_files is 2, but expected 1", "\n".join(errors))

    def test_check_index_payload_reports_collection_count_drift(self) -> None:
        payload = self.valid_payload()
        payload["collections"][0]["skill_files"] = 2

        errors = check_site.check_index_payload(payload)

        self.assertIn("collections[0].skill_files is 2, but skills contain 1", "\n".join(errors))

    def test_check_index_payload_reports_path_collection_mismatch(self) -> None:
        payload = self.valid_payload()
        payload["skills"][0]["path"] = "skills/other/paper-writing/SKILL.md"

        errors = check_site.check_index_payload(payload)

        self.assertIn("path is outside collection", "\n".join(errors))

    def test_check_index_payload_reports_invalid_collection_repo_url(self) -> None:
        payload = self.valid_payload()
        payload["collections"][0]["repo_url"] = "javascript:alert(1)"

        errors = check_site.check_index_payload(payload)

        self.assertIn("repo_url must be an HTTP(S) URL", "\n".join(errors))

    def test_check_index_payload_reports_tag_drift(self) -> None:
        payload = self.valid_payload()
        payload["tags"] = ["unused"]

        errors = check_site.check_index_payload(payload)

        messages = "\n".join(errors)
        self.assertIn("tags missing used tags: writing", messages)
        self.assertIn("tags include unused tags: unused", messages)

    def test_check_index_payload_reports_duplicate_flags(self) -> None:
        payload = self.valid_payload()
        payload["skills"][0]["flags"] = ["collision", "collision"]

        errors = check_site.check_index_payload(payload)

        self.assertIn("duplicate flags: collision", "\n".join(errors))


class CollisionsContractTests(unittest.TestCase):
    def valid_payload(self) -> dict:
        return {
            "generated_by": "tools/build_index.py",
            "count": 1,
            "collisions": [
                {
                    "name": "analysis",
                    "collections": 2,
                    "distinct_bodies": 2,
                    "total_copies": 2,
                    "variants": [
                        {
                            "collection": "a",
                            "trigger": "Analyze data.",
                            "path": "skills/a/analysis/SKILL.md",
                            "bodies_in_collection": 1,
                        },
                        {
                            "collection": "b",
                            "trigger": "Analyze data differently.",
                            "path": "skills/b/analysis/SKILL.md",
                            "bodies_in_collection": 1,
                        }
                    ],
                }
            ],
        }

    def test_check_collisions_payload_accepts_valid_payload(self) -> None:
        self.assertEqual(check_site.check_collisions_payload(self.valid_payload()), [])

    def test_check_collisions_payload_reports_wrong_generator(self) -> None:
        payload = self.valid_payload()
        payload["generated_by"] = "manual"

        errors = check_site.check_collisions_payload(payload)

        self.assertIn("generated_by must be tools/build_index.py", "\n".join(errors))

    def test_check_collisions_payload_reports_missing_variant_keys(self) -> None:
        payload = self.valid_payload()
        del payload["collisions"][0]["variants"][0]["path"]

        errors = check_site.check_collisions_payload(payload)

        self.assertIn("missing keys: path", "\n".join(errors))

    def test_check_collisions_payload_reports_count_drift(self) -> None:
        payload = self.valid_payload()
        payload["count"] = 2

        errors = check_site.check_collisions_payload(payload)

        self.assertIn("count is 2, but contains 1 groups", "\n".join(errors))

    def test_check_collisions_payload_reports_collection_drift(self) -> None:
        payload = self.valid_payload()
        payload["collisions"][0]["collections"] = 3

        errors = check_site.check_collisions_payload(payload)

        self.assertIn("collections is 3, but variants cover 2 collections", "\n".join(errors))

    def test_check_collisions_payload_reports_non_collision_group(self) -> None:
        payload = self.valid_payload()
        payload["collisions"][0]["collections"] = 1
        payload["collisions"][0]["distinct_bodies"] = 1

        errors = check_site.check_collisions_payload(payload)

        messages = "\n".join(errors)
        self.assertIn("collections must be at least 2", messages)
        self.assertIn("distinct_bodies must be at least 2", messages)

    def test_check_collisions_payload_reports_variant_path_collection_mismatch(self) -> None:
        payload = self.valid_payload()
        payload["collisions"][0]["variants"][0]["path"] = "skills/other/analysis/SKILL.md"

        errors = check_site.check_collisions_payload(payload)

        self.assertIn("path is outside collection", "\n".join(errors))

    def test_check_collisions_payload_reports_duplicate_variant_collection(self) -> None:
        payload = self.valid_payload()
        payload["collisions"][0]["variants"][1]["collection"] = "a"
        payload["collisions"][0]["variants"][1]["path"] = "skills/a/other/SKILL.md"
        payload["collisions"][0]["collections"] = 1

        errors = check_site.check_collisions_payload(payload)

        self.assertIn("duplicate variant collections: a", "\n".join(errors))

    def test_check_collisions_payload_reports_invalid_variant_repo_url(self) -> None:
        payload = self.valid_payload()
        payload["collisions"][0]["variants"][0]["repo_url"] = "ftp://example.com/repo"

        errors = check_site.check_collisions_payload(payload)

        self.assertIn("repo_url must be an HTTP(S) URL", "\n".join(errors))

    def test_check_collisions_payload_reports_total_copy_drift(self) -> None:
        payload = self.valid_payload()
        payload["collisions"][0]["total_copies"] = 1

        errors = check_site.check_collisions_payload(payload)

        self.assertIn("total_copies is 1, but variants contain at least 2 bodies", "\n".join(errors))


class CrossPayloadTests(unittest.TestCase):
    def index_payload(self) -> dict:
        return {
            "totals": {
                "skill_files": 1,
                "unique_skills": 1,
                "collections": 1,
                "templates": 0,
                "no_frontmatter": 0,
                "rebundled": 0,
                "name_collisions": 1,
            },
            "tags": [],
            "collections": [{"name": "demo", "skill_files": 1, "unique_skills": 1}],
            "skills": [
                {
                    "name": "analysis",
                    "collection": "demo",
                    "trigger": "Analyze data.",
                    "path": "skills/demo/analysis/SKILL.md",
                    "flags": ["collision"],
                }
            ],
        }

    def collisions_payload(self) -> dict:
        return {
            "count": 1,
            "collisions": [
                {
                    "name": "analysis",
                    "collections": 2,
                    "distinct_bodies": 2,
                    "total_copies": 2,
                    "variants": [
                        {
                            "collection": "a",
                            "trigger": "Analyze data.",
                            "path": "skills/a/analysis/SKILL.md",
                            "bodies_in_collection": 1,
                        },
                        {
                            "collection": "b",
                            "trigger": "Analyze data differently.",
                            "path": "skills/b/analysis/SKILL.md",
                            "bodies_in_collection": 1,
                        },
                    ],
                }
            ],
        }

    def test_check_cross_payloads_accepts_matching_collision_names(self) -> None:
        self.assertEqual(
            check_site.check_cross_payloads(self.index_payload(), self.collisions_payload()),
            [],
        )

    def test_check_cross_payloads_reports_count_mismatch(self) -> None:
        payload = self.collisions_payload()
        payload["count"] = 2

        errors = check_site.check_cross_payloads(self.index_payload(), payload)

        self.assertIn("catalog collision count mismatch", "\n".join(errors))

    def test_check_cross_payloads_reports_name_mismatch(self) -> None:
        payload = self.collisions_payload()
        payload["collisions"][0]["name"] = "other"

        errors = check_site.check_cross_payloads(self.index_payload(), payload)

        messages = "\n".join(errors)
        self.assertIn("names missing from search-index collision flags: other", messages)
        self.assertIn("search-index collision flags missing from catalog/collisions.json: analysis", messages)


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
  "generated_by": "tools/build_index.py",
  "totals": {
    "skill_files": 1,
    "unique_skills": 1,
    "collections": 1,
    "templates": 0,
    "no_frontmatter": 0,
    "rebundled": 0,
    "name_collisions": 0
  },
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
  "generated_by": "tools/build_index.py",
  "count": 0,
  "collisions": []
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
