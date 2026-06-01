import unittest

from tools import build_catalog
from tools import build_index


class BuildIndexTests(unittest.TestCase):
    def test_tags_for_matches_research_facets(self) -> None:
        tags = build_index.tags_for(
            "zotero-literature-review",
            "Search papers, manage citations, and write related work.",
        )

        self.assertIn("citations", tags)
        self.assertIn("literature-review", tags)
        self.assertIn("paper-search", tags)

    def test_colliding_names_requires_distinct_bodies_across_collections(self) -> None:
        skills = [
            build_catalog.Skill(
                name="paper-review",
                collection="a",
                path="skills/a/paper-review/SKILL.md",
                description="Review papers.",
                content_hash="hash-a",
            ),
            build_catalog.Skill(
                name="paper-review",
                collection="b",
                path="skills/b/paper-review/SKILL.md",
                description="Review papers differently.",
                content_hash="hash-b",
            ),
            build_catalog.Skill(
                name="shared",
                collection="a",
                path="skills/a/shared/SKILL.md",
                description="Same body.",
                content_hash="same",
            ),
            build_catalog.Skill(
                name="shared",
                collection="b",
                path="skills/b/shared/SKILL.md",
                description="Same body.",
                content_hash="same",
            ),
        ]

        self.assertEqual(build_index.colliding_names(skills), {"paper-review"})

    def test_skill_flags_include_collision_state(self) -> None:
        skill = build_catalog.Skill(
            name="example",
            collection="a",
            path="skills/a/example/SKILL.md",
            description="Example.",
            has_frontmatter=False,
            is_template=True,
            duplicate_of="skills/other/example/SKILL.md",
        )

        self.assertEqual(
            build_index.skill_flags(skill, {"example"}),
            ["template", "dup", "no-fm", "collision"],
        )

    def test_build_collisions_payload_groups_by_collection(self) -> None:
        skills = [
            build_catalog.Skill(
                name="analysis",
                collection="a",
                path="skills/a/analysis/SKILL.md",
                description="Analyze data.",
                content_hash="hash-a",
            ),
            build_catalog.Skill(
                name="analysis",
                collection="a",
                path="skills/a/nested/analysis/SKILL.md",
                description="Analyze data variant.",
                content_hash="hash-a2",
            ),
            build_catalog.Skill(
                name="analysis",
                collection="b",
                path="skills/b/analysis/SKILL.md",
                description="Analyze papers.",
                content_hash="hash-b",
            ),
        ]

        payload = build_index.build_collisions_payload(skills)

        self.assertEqual(payload["count"], 1)
        group = payload["collisions"][0]
        self.assertEqual(group["name"], "analysis")
        self.assertEqual(group["collections"], 2)
        self.assertEqual(group["distinct_bodies"], 3)
        self.assertEqual(group["total_copies"], 3)
        self.assertEqual(len(group["variants"]), 2)


if __name__ == "__main__":
    unittest.main()
