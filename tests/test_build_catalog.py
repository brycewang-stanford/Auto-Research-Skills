import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tools import build_catalog


class FrontmatterParsingTests(unittest.TestCase):
    def test_parses_frontmatter_after_leading_html_comment(self) -> None:
        text = """<!-- collected upstream -->
---
name: literature-review
description: Find and synthesize related papers.
license: MIT
---

# Body
"""

        meta, body, has_frontmatter = build_catalog.parse_frontmatter(text)

        self.assertTrue(has_frontmatter)
        self.assertEqual(meta["name"], "literature-review")
        self.assertEqual(meta["description"], "Find and synthesize related papers.")
        self.assertEqual(meta["license"], "MIT")
        self.assertIn("# Body", body)

    def test_folds_block_scalar_descriptions(self) -> None:
        text = """---
name: paper-review
description: >
  Review a manuscript for
  claims, evidence, and fit.
---
Body
"""

        meta, _, has_frontmatter = build_catalog.parse_frontmatter(text)

        self.assertTrue(has_frontmatter)
        self.assertEqual(
            meta["description"],
            "Review a manuscript for claims, evidence, and fit.",
        )

    def test_first_paragraph_skips_headings_and_fences(self) -> None:
        body = """# Skill title

```python
print("ignore me")
```

Use this skill for reproducibility audits.

Second paragraph.
"""

        self.assertEqual(
            build_catalog.first_paragraph(body),
            "Use this skill for reproducibility audits.",
        )


class SkillFileDiscoveryTests(unittest.TestCase):
    def test_iter_skill_files_is_case_insensitive_and_preserves_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills_dir = Path(tmp) / "skills"
            upper = skills_dir / "collection-a" / "alpha" / "SKILL.md"
            lower = skills_dir / "collection-b" / "beta" / "skill.md"
            other = skills_dir / "collection-c" / "gamma" / "README.md"
            for path in (upper, lower, other):
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("placeholder", encoding="utf-8")

            with mock.patch.object(build_catalog, "SKILLS_DIR", skills_dir):
                found = [
                    path.relative_to(skills_dir).as_posix()
                    for path in build_catalog.iter_skill_files()
                ]

        self.assertEqual(
            found,
            [
                "collection-a/alpha/SKILL.md",
                "collection-b/beta/skill.md",
            ],
        )


class RenderingHelperTests(unittest.TestCase):
    def test_trigger_sentence_truncates_on_word_boundary(self) -> None:
        sentence = "alpha beta gamma delta"

        self.assertEqual(
            build_catalog.trigger_sentence(sentence, limit=13),
            "alpha beta\u2026",
        )

    def test_stale_generated_collection_pages_reports_unwritten_pages(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            collections_dir = Path(tmp) / "collections"
            collections_dir.mkdir()
            current = collections_dir / "current.md"
            stale = collections_dir / "stale.md"
            current.write_text("current", encoding="utf-8")
            stale.write_text("stale", encoding="utf-8")

            result = build_catalog.stale_generated_collection_pages(
                [current],
                collections_dir,
            )

        self.assertEqual([path.name for path in result], ["stale.md"])


if __name__ == "__main__":
    unittest.main()
