import datetime as dt
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def load_discover_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "discover-skills.py"
    spec = importlib.util.spec_from_file_location("discover_skills_module", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/discover-skills.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


discover = load_discover_module()
NOW = dt.datetime(2026, 6, 23, tzinfo=dt.timezone.utc)


def item(slug, stars=100, fork=False, archived=False, license="MIT"):
    return {
        "full_name": slug,
        "stargazers_count": stars,
        "language": "Python",
        "license": {"spdx_id": license} if license else None,
        "pushed_at": "2026-06-01T00:00:00Z",
        "archived": archived,
        "fork": fork,
        "description": "a skill",
    }


class SlugTests(unittest.TestCase):
    def test_github_slug(self) -> None:
        self.assertEqual(discover.github_slug("https://github.com/o/r.git"), "o/r")
        self.assertIsNone(discover.github_slug("https://example.com/o/r"))


class BacklogSlugTests(unittest.TestCase):
    def test_backlog_slugs_extracts_and_lowercases(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "DISCOVERY.md"
            md.write_text(
                "See [x](https://github.com/Owner/Repo) and github.com/foo/bar.git",
                encoding="utf-8",
            )
            slugs = discover.backlog_slugs([md, Path(tmp) / "missing.md"])
        self.assertIn("owner/repo", slugs)
        self.assertIn("foo/bar", slugs)


class DedupeFilterTests(unittest.TestCase):
    def test_drops_known_forks_archived_and_lowstar(self) -> None:
        raw = [
            discover.normalize(item("new/keep", stars=200), "q1"),
            discover.normalize(item("old/vendored", stars=999), "q1"),
            discover.normalize(item("a/fork", fork=True, stars=300), "q1"),
            discover.normalize(item("a/archived", archived=True, stars=300), "q1"),
            discover.normalize(item("a/tiny", stars=10), "q1"),
        ]
        known = {"old/vendored"}
        # Isolate fork/archived/star/known filtering from the topic filter.
        result = discover.dedupe_and_filter(raw, known, min_stars=80, topic_filter=False)
        slugs = [c["slug"] for c in result]
        self.assertEqual(slugs, ["new/keep"])

    def test_dedupes_by_slug_keeping_max_stars(self) -> None:
        raw = [
            discover.normalize(item("dup/repo", stars=120), "q1"),
            discover.normalize(item("dup/repo", stars=180), "q2"),
        ]
        result = discover.dedupe_and_filter(raw, set(), min_stars=80, topic_filter=False)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["stars"], 180)

    def test_ranks_by_stars_desc(self) -> None:
        raw = [
            discover.normalize(item("a/low", stars=90), "q"),
            discover.normalize(item("b/high", stars=500), "q"),
        ]
        result = discover.dedupe_and_filter(raw, set(), min_stars=80, topic_filter=False)
        self.assertEqual([c["slug"] for c in result], ["b/high", "a/low"])


class OnTopicTests(unittest.TestCase):
    def test_research_terms_pass(self) -> None:
        for desc in ["literature review agent", "autonomous paper writing", "arxiv search skill"]:
            it = discover.normalize(item("o/r"), "q")
            it["description"] = desc
            self.assertTrue(discover.is_on_topic(it), desc)

    def test_slug_can_carry_the_signal(self) -> None:
        it = discover.normalize(item("someone/zotero-helper"), "q")
        it["description"] = ""
        self.assertTrue(discover.is_on_topic(it))

    def test_generic_repos_rejected(self) -> None:
        for slug, desc in [
            ("vinta/awesome-python", "frameworks, libraries, tools and resources"),
            ("crewAIInc/crewAI", "framework for orchestrating autonomous AI agents"),
            ("santifer/career-ops", "AI-powered job search system"),
        ]:
            it = discover.normalize(item(slug), "q")
            it["description"] = desc
            self.assertFalse(discover.is_on_topic(it), slug)

    def test_offtopic_term_overrides_research_word(self) -> None:
        it = discover.normalize(item("x/ui-ux-pro-max-skill"), "q")
        it["description"] = "design intelligence for research dashboards"
        self.assertFalse(discover.is_on_topic(it))

    def test_filter_can_be_disabled(self) -> None:
        raw = [discover.normalize(item("crew/ai", stars=500), "q")]
        raw[0]["description"] = "agent framework"
        kept = discover.dedupe_and_filter(raw, set(), 80, topic_filter=False)
        self.assertEqual(len(kept), 1)
        dropped = discover.dedupe_and_filter(raw, set(), 80, topic_filter=True)
        self.assertEqual(len(dropped), 0)


class RenderTests(unittest.TestCase):
    def test_render_markdown_table(self) -> None:
        cands = [discover.normalize(item("new/keep", stars=2500), "q1")]
        md = discover.render_markdown(cands, NOW)
        self.assertIn("Auto-discovered candidates (1)", md)
        self.assertIn("new/keep", md)
        self.assertIn("2.5k", md)

    def test_render_escapes_pipes_in_description(self) -> None:
        it = item("new/keep")
        it["description"] = "does a | b | c"
        md = discover.render_markdown([discover.normalize(it, "q")], NOW)
        self.assertIn("a \\| b \\| c", md)


if __name__ == "__main__":
    unittest.main()
