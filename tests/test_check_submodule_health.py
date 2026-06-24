import datetime as dt
import importlib.util
import sys
import unittest
from pathlib import Path


def load_health_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "check-submodule-health.py"
    spec = importlib.util.spec_from_file_location("check_submodule_health_module", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load scripts/check-submodule-health.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


health = load_health_module()
NOW = dt.datetime(2026, 6, 23, tzinfo=dt.timezone.utc)


def repo(spdx="MIT", pushed="2026-06-01T00:00:00Z", archived=False, stars=100):
    return {
        "stargazers_count": stars,
        "license": {"spdx_id": spdx} if spdx is not None else None,
        "pushed_at": pushed,
        "archived": archived,
    }


class ParsePushedAtTests(unittest.TestCase):
    def test_parses_z_suffix(self) -> None:
        parsed = health.parse_pushed_at("2026-06-01T12:00:00Z")
        self.assertEqual(parsed.year, 2026)
        self.assertIsNotNone(parsed.tzinfo)

    def test_handles_missing_and_bad_values(self) -> None:
        self.assertIsNone(health.parse_pushed_at(None))
        self.assertIsNone(health.parse_pushed_at(""))
        self.assertIsNone(health.parse_pushed_at("not-a-date"))


class ClassifyTests(unittest.TestCase):
    def test_healthy_repo_has_no_flags(self) -> None:
        row = health.classify("skills/x", "o/x", repo(), NOW)
        self.assertTrue(row["reachable"])
        self.assertEqual(row["flags"], [])
        self.assertFalse(row["stale"])
        self.assertFalse(row["license_unclear"])

    def test_stale_repo_flagged(self) -> None:
        row = health.classify(
            "systems/y", "o/y", repo(pushed="2024-01-01T00:00:00Z"), NOW
        )
        self.assertTrue(row["stale"])
        self.assertIn("stale", row["flags"])
        self.assertGreater(row["days_since_push"], 365)

    def test_missing_and_noassertion_license_flagged(self) -> None:
        none_lic = health.classify("skills/a", "o/a", repo(spdx=None), NOW)
        noassert = health.classify("skills/b", "o/b", repo(spdx="NOASSERTION"), NOW)
        self.assertIn("license", none_lic["flags"])
        self.assertIn("license", noassert["flags"])

    def test_archived_flagged(self) -> None:
        row = health.classify("skills/c", "o/c", repo(archived=True), NOW)
        self.assertIn("archived", row["flags"])

    def test_unreachable_repo(self) -> None:
        row = health.classify("skills/d", "o/d", None, NOW)
        self.assertFalse(row["reachable"])
        self.assertEqual(row["flags"], ["unreachable"])

    def test_stale_days_threshold_is_configurable(self) -> None:
        old = repo(pushed="2025-06-01T00:00:00Z")  # ~1 year before NOW
        self.assertTrue(health.classify("s/e", "o/e", old, NOW, stale_days=180)["stale"])
        self.assertFalse(health.classify("s/e", "o/e", old, NOW, stale_days=720)["stale"])


class FormatTests(unittest.TestCase):
    def test_fmt_stars(self) -> None:
        self.assertEqual(health.fmt_stars(None), "n/a")
        self.assertEqual(health.fmt_stars(42), "42")
        self.assertEqual(health.fmt_stars(3964), "4.0k")

    def test_fmt_age(self) -> None:
        self.assertEqual(health.fmt_age(None), "?")
        self.assertEqual(health.fmt_age(5), "5d")
        self.assertEqual(health.fmt_age(60), "2mo")
        self.assertTrue(health.fmt_age(400).endswith("m") or "y" in health.fmt_age(400))


class RenderTests(unittest.TestCase):
    def test_render_includes_summary_and_flagged_section(self) -> None:
        rows = [
            health.classify("skills/ok", "o/ok", repo(), NOW),
            health.classify("systems/old", "o/old", repo(pushed="2024-01-01T00:00:00Z", spdx=None), NOW),
        ]
        md = health.render(rows, NOW, health.DEFAULT_STALE_DAYS)
        self.assertIn("# 🩺 Submodule Health", md)
        self.assertIn("Total submodules: **2**", md)
        self.assertIn("Needs attention", md)
        self.assertIn("o/old", md)
        # Healthy repo still appears in the full table.
        self.assertIn("o/ok", md)

    def test_render_omits_attention_section_when_all_healthy(self) -> None:
        rows = [health.classify("skills/ok", "o/ok", repo(), NOW)]
        md = health.render(rows, NOW, health.DEFAULT_STALE_DAYS)
        self.assertNotIn("Needs attention", md)


if __name__ == "__main__":
    unittest.main()
