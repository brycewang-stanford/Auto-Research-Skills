import json
import tempfile
import unittest
from pathlib import Path

from tools import build_starter_kits as bsk


class _NoFlags:
    """Safety gate stub: nothing is flagged unless listed."""

    def __init__(self, flagged=()):
        self._flagged = set(flagged)

    def flagged(self, skill_dir):
        return skill_dir in self._flagged


def _skill(name, collection, rel_dir, description, **extra):
    data = {
        "name": name,
        "collection": collection,
        "path": f"skills/{collection}/{rel_dir}/SKILL.md",
        "description": description,
        "license": "",
        "has_frontmatter": True,
        "is_template": False,
        "duplicate_of": "",
    }
    data.update(extra)
    return data


LIT = "Use when the user needs a systematic literature review with paper search across arXiv and PubMed."


class StarterKitTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)

    def _materialise(self, skills, rich=()):
        for s in skills:
            d = self.root / Path(s["path"]).parent
            d.mkdir(parents=True, exist_ok=True)
            (d / "SKILL.md").write_text(f"---\nname: {s['name']}\n---\n", encoding="utf-8")
            if s["name"] in rich:
                for sub in ("references", "scripts", "examples"):
                    (d / sub).mkdir()
                    (d / sub / "README.md").write_text("x", encoding="utf-8")
        return skills

    def _kits(self, skills, flagged=()):
        return bsk.build_kits(skills, root=self.root, gate=_NoFlags(flagged))

    def test_relevance_weights_name_over_description(self):
        stage = next(s for s in bsk.STAGES if s.key == "literature")
        by_name = _skill("literature-review", "c", "a", "Helps with things.")
        by_desc = _skill("helper", "c", "b", LIT)
        self.assertGreaterEqual(bsk.relevance(by_name, stage), 3)
        self.assertGreater(bsk.relevance(by_desc, stage), 0)
        self.assertEqual(bsk.relevance(_skill("x", "c", "d", "Cook pasta well, every day."), stage), 0)

    def test_stage_exclusions_zero_out_relevance(self):
        stage = next(s for s in bsk.STAGES if s.key == "reading")
        self.assertEqual(bsk.relevance(_skill("variant-reader", "c", "a", "Zotero reader for pdf."), stage), 0)

    def test_depth_ranks_rich_skills_first(self):
        skills = self._materialise(
            [_skill("lit-bare", "a", "s1", LIT), _skill("lit-rich", "b", "s2", LIT)],
            rich=("lit-rich",),
        )
        picks = self._kits(skills)["literature"]
        self.assertEqual([p.name for p in picks][:2], ["lit-rich", "lit-bare"])
        self.assertIn("references", picks[0].signals)

    def test_gates_drop_duplicates_templates_roots_and_flagged(self):
        skills = self._materialise([
            _skill("lit-dup", "a", "s1", LIT, duplicate_of="skills/x/SKILL.md"),
            _skill("lit-tpl", "b", "s2", LIT, is_template=True),
            _skill("lit-flag", "c", "s3", LIT),
            _skill("lit-ok", "d", "s4", LIT),
        ])
        root_skill = _skill("lit-root", "e", ".", LIT)
        root_skill["path"] = "skills/e/SKILL.md"
        self._materialise([root_skill])
        picks = self._kits(skills + [root_skill], flagged={"skills/c/s3"})["literature"]
        self.assertEqual([p.name for p in picks], ["lit-ok"])

    def test_one_per_collection_and_names_unique_across_stages(self):
        both = "Use when doing a literature review and drafting a manuscript with academic writing polish."
        skills = self._materialise([
            _skill("lit-a1", "a", "s1", LIT),
            _skill("lit-a2", "a", "s2", LIT),
            _skill("shared-writing-literature", "b", "s3", both),
        ])
        kits = self._kits(skills)
        lit = [p.collection for p in kits["literature"]]
        self.assertEqual(len(lit), len(set(lit)))
        names = [p.name.lower() for picks in kits.values() for p in picks]
        self.assertEqual(len(names), len(set(names)))

    def test_render_is_deterministic_and_json_round_trips(self):
        skills = self._materialise([_skill("lit-ok", "d", "s4", LIT)])
        kits = self._kits(skills)
        self.assertEqual(bsk.render_report(kits, 1), bsk.render_report(kits, 1))
        data = json.loads(bsk.render_json(kits))
        lit = next(s for s in data["stages"] if s["key"] == "literature")
        self.assertEqual(lit["skills"][0]["skill_dir"], "skills/d/s4")

    def test_install_copies_and_refuses_overwrite(self):
        skills = self._materialise([_skill("lit-ok", "d", "s4", LIT)])
        kits = self._kits(skills)
        dest = self.root / "dest"
        self.assertEqual(bsk.install(kits, "literature", dest, dry_run=True, force=False, root=self.root), 0)
        self.assertFalse((dest / "lit-ok").exists())
        self.assertEqual(bsk.install(kits, "literature", dest, dry_run=False, force=False, root=self.root), 0)
        self.assertTrue((dest / "lit-ok" / "SKILL.md").exists())
        self.assertEqual(bsk.install(kits, "literature", dest, dry_run=False, force=False, root=self.root), 1)
        self.assertEqual(bsk.install(kits, "literature", dest, dry_run=False, force=True, root=self.root), 0)

    def test_unsafe_names_are_ineligible(self):
        self.assertFalse(bsk.eligible(_skill("../escape", "a", "s1", LIT)))
        self.assertTrue(bsk.eligible(_skill("ok-name", "a", "s1", LIT)))


if __name__ == "__main__":
    unittest.main()
