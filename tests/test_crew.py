"""Tests for the crew workspace tool (crew/scripts/crew.py)."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("crew_tool", ROOT / "crew" / "scripts" / "crew.py")
crew = importlib.util.module_from_spec(SPEC)
sys.modules["crew_tool"] = crew
SPEC.loader.exec_module(crew)


def call(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
        try:
            code = crew.main(list(argv))
        except SystemExit as exc:  # sys.exit("message") paths
            code = exc.code if isinstance(exc.code, int) else 1
            if not isinstance(exc.code, int):
                out.write(str(exc.code))
    return code, out.getvalue()


def edit_json(path: Path, change) -> None:
    data = json.loads(path.read_text())
    change(data)
    path.write_text(json.dumps(data))


def write_review(ws: Path, target: str, number: int = 1, findings: list | None = None,
                 verdict: str = "pass") -> Path:
    directory = ws / "reviews" / f"{target}-r{number}"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / "review.json"
    path.write_text(json.dumps({
        "id": directory.name, "target": target, "round": number, "created": crew.now(),
        "reviewer": {"model": "test-model", "independence": "fresh-context"},
        "files_read": ["plan.json"],
        "kill_argument": "The strongest objection that survived.",
        "verdict": verdict,
        "findings": findings or [],
    }))
    return path


CRITICAL = {"id": "F1", "severity": "critical", "status": "open",
            "text": "The design does not identify the effect.", "evidence": "plan.json design.method"}


class CrewWorkspaceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ws = Path(self.tmp.name) / "ws"
        code, _ = call("init", str(self.ws), "--track", "cs", "--title", "Test paper")
        self.assertEqual(code, 0)

    # -- helpers
    def fill_plan(self) -> None:
        def change(plan):
            plan["question"] = "Does X change Y?"
            plan["hypotheses"] = ["X raises Y."]
            plan["design"].update(summary="s", method="m", analysis_plan=["main run"])
            plan["tasks"] = [{"id": "t1", "title": "main run", "owner": "experimenter", "status": "todo"}]
        edit_json(self.ws / "plan.json", change)

    def approve(self, gate: str, *extra: str) -> tuple[int, str]:
        return call("gate", str(self.ws), gate, "approve", "--by", "Human", *extra)

    def to_design(self) -> None:
        self.fill_plan()
        write_review(self.ws, "question")
        self.assertEqual(self.approve("question")[0], 0)
        write_review(self.ws, "design")
        self.assertEqual(self.approve("design")[0], 0)

    def run_main(self, value: float = 0.5) -> None:
        script = self.ws / "code" / "main.py"
        script.write_text(f"import json\njson.dump({{'acc': {value}}}, open('metrics.json', 'w'))\n")
        code, out = call("run", str(self.ws), "--id", "main", "--role", "experimenter",
                         "--kind", "analysis", "--code", "code/main.py",
                         "--metrics", "metrics.json", "--", sys.executable, "code/main.py")
        self.assertEqual(code, 0, out)

    def add_claim(self, **overrides) -> None:
        claim = {"id": "c1", "kind": "result", "text": "Accuracy is 0.5.",
                 "support": [{"run": "main", "metric": "acc"}], "value": 0.5,
                 "macro": "AccMain", "format": ".2f"}
        claim.update(overrides)
        with (self.ws / "claims.jsonl").open("a") as handle:
            handle.write(json.dumps(claim) + "\n")

    def errors(self, strict: bool = False) -> list[str]:
        return crew.validate(self.ws, strict=strict)[0]

    # -- tests
    def test_new_workspace_is_valid(self) -> None:
        self.assertEqual(self.errors(), [])
        self.assertEqual(call("validate", str(self.ws))[0], 0)

    def test_init_refuses_non_empty_directory(self) -> None:
        self.assertEqual(call("init", str(self.ws), "--track", "cs", "--title", "Again")[0], 1)

    def test_gates_must_be_approved_in_order(self) -> None:
        self.fill_plan()
        code, out = self.approve("design")
        self.assertEqual(code, 1)
        self.assertIn("must be approved first", out)

    def test_gate_needs_a_human_name(self) -> None:
        self.fill_plan()
        self.assertEqual(call("gate", str(self.ws), "question", "approve")[0], 1)

    def test_gate_needs_a_review(self) -> None:
        self.fill_plan()
        code, out = self.approve("question")
        self.assertEqual(code, 1)
        self.assertIn("without a review", out)
        plan = json.loads((self.ws / "plan.json").read_text())
        self.assertEqual(plan["gates"]["question"]["status"], "pending")

    def test_open_critical_finding_blocks_gate(self) -> None:
        self.fill_plan()
        write_review(self.ws, "question", findings=[CRITICAL], verdict="block")
        code, out = self.approve("question")
        self.assertEqual(code, 1)
        self.assertIn("open critical finding", out)

    def test_human_can_accept_a_finding_with_a_note(self) -> None:
        self.fill_plan()
        write_review(self.ws, "question", findings=[CRITICAL], verdict="block")
        self.assertEqual(self.approve("question", "--accept-findings", "F1")[0], 1)  # no note
        code, out = self.approve("question", "--accept-findings", "F1", "--note", "Scope is narrowed in the paper.")
        self.assertEqual(code, 0, out)

    def test_later_round_resolving_the_finding_unblocks_gate(self) -> None:
        self.fill_plan()
        write_review(self.ws, "question", findings=[CRITICAL], verdict="block")
        write_review(self.ws, "question", number=2, findings=[dict(CRITICAL, status="resolved")])
        self.assertEqual(self.approve("question")[0], 0)

    def test_review_must_commit_to_a_kill_argument(self) -> None:
        path = write_review(self.ws, "question")
        edit_json(path, lambda review: review.update(kill_argument=""))
        self.assertTrue(any("kill_argument" in e for e in self.errors()))

    def test_pass_verdict_with_open_critical_is_rejected(self) -> None:
        write_review(self.ws, "question", findings=[CRITICAL], verdict="pass")
        self.assertTrue(any("verdict is pass" in e for e in self.errors()))

    def test_review_rounds_are_bounded_and_gapless(self) -> None:
        write_review(self.ws, "question", number=2)
        self.assertTrue(any("missing round" in e for e in self.errors()))
        write_review(self.ws, "design", number=5)
        self.assertTrue(any("exceeds the limit" in e for e in self.errors()))

    def test_analysis_run_blocked_before_design_gate(self) -> None:
        (self.ws / "code" / "main.py").write_text("print('hi')\n")
        code, out = call("run", str(self.ws), "--id", "main", "--role", "experimenter",
                         "--kind", "analysis", "--code", "code/main.py", "--", sys.executable, "code/main.py")
        self.assertEqual(code, 1)
        self.assertIn("design gate", out)
        self.assertFalse((self.ws / "runs" / "main").exists())

    def test_run_records_metrics_and_hashes(self) -> None:
        self.to_design()
        self.run_main()
        record = json.loads((self.ws / "runs" / "main" / "run.json").read_text())
        self.assertEqual(record["exit_code"], 0)
        self.assertEqual(record["metrics"], {"acc": 0.5})
        self.assertEqual(record["code"][0]["path"], "code/main.py")
        self.assertEqual(self.errors(), [])

    def test_failed_run_cannot_support_a_claim(self) -> None:
        self.to_design()
        (self.ws / "code" / "bad.py").write_text("raise SystemExit(3)\n")
        code, _ = call("run", str(self.ws), "--id", "main", "--role", "experimenter",
                       "--kind", "analysis", "--code", "code/bad.py", "--", sys.executable, "code/bad.py")
        self.assertEqual(code, 1)
        self.add_claim(value=None, macro=None)
        self.assertTrue(any("did not finish successfully" in e for e in self.errors()))

    def test_claim_value_must_match_run_metric(self) -> None:
        self.to_design()
        self.run_main()
        self.add_claim(value=0.9)
        self.assertTrue(any("does not match the run metric" in e for e in self.errors()))

    def test_claim_without_support_is_rejected(self) -> None:
        self.add_claim(support=[])
        self.assertTrue(any("no support" in e for e in self.errors()))

    def test_numbers_file_is_generated_and_checked(self) -> None:
        self.to_design()
        self.run_main()
        self.add_claim()
        self.assertTrue(any("numbers.tex: missing" in e for e in self.errors()))
        self.assertEqual(call("numbers", str(self.ws))[0], 0)
        text = (self.ws / "paper" / "numbers.tex").read_text()
        self.assertIn("\\newcommand{\\AccMain}{0.50}", text)
        self.assertEqual(self.errors(), [])
        (self.ws / "paper" / "numbers.tex").write_text(text.replace("0.50", "0.99"))
        self.assertTrue(any("out of date" in e for e in self.errors()))

    def test_editing_code_after_a_run_invalidates_it(self) -> None:
        self.to_design()
        self.run_main()
        with (self.ws / "code" / "main.py").open("a") as handle:
            handle.write("# changed\n")
        self.assertTrue(any("changed since the run" in e for e in self.errors()))

    def test_rerun_reproduces_deterministic_runs(self) -> None:
        self.to_design()
        self.run_main()
        code, out = call("rerun", str(self.ws))
        self.assertEqual(code, 0, out)
        report = json.loads((self.ws / "replication.json").read_text())
        self.assertTrue(report["passed"])
        self.assertEqual(report["runs"][0]["status"], "match")

    def test_rerun_catches_irreproducible_runs(self) -> None:
        self.to_design()
        script = self.ws / "code" / "noisy.py"
        script.write_text("import json, random\njson.dump({'acc': random.random()}, open('metrics.json', 'w'))\n")
        call("run", str(self.ws), "--id", "noisy", "--role", "experimenter", "--kind", "analysis",
             "--code", "code/noisy.py", "--metrics", "metrics.json", "--", sys.executable, "code/noisy.py")
        code, _ = call("rerun", str(self.ws))
        self.assertEqual(code, 1)
        report = json.loads((self.ws / "replication.json").read_text())
        self.assertEqual(report["runs"][0]["status"], "mismatch")

    def test_rerun_must_be_newer_than_the_runs(self) -> None:
        self.to_design()
        self.run_main()
        call("rerun", str(self.ws))
        edit_json(self.ws / "replication.json", lambda r: r.update(created="2000-01-01T00:00:00Z"))
        problems = crew.check_replication(self.ws, crew.read_runs(self.ws)[0], required=True)
        self.assertTrue(any("older than the latest run" in p for p in problems))

    def test_log_entries_cannot_be_in_the_future(self) -> None:
        self.assertEqual(call("log", str(self.ws), "--role", "scout", "--action", "done")[0], 0)
        self.assertEqual(self.errors(), [])
        with (self.ws / "log.jsonl").open("a") as handle:
            handle.write(json.dumps({"time": "2999-01-01T00:00:00Z", "role": "scout", "action": "x"}) + "\n")
        self.assertTrue(any("in the future" in e for e in self.errors()))

    def test_citations_need_verified_sources(self) -> None:
        (self.ws / "refs.bib").write_text("@article{known2020,\n  title={A},\n}\n")
        self.assertTrue(any("no verification record" in e for e in self.errors()))
        edit_json(self.ws / "sources" / "sources.json", lambda sources: sources.update(
            known2020={"doi": "10.1/x", "verified_on": "2026-11-18", "verified_by": "scout",
                       "method": "fetched-abstract"}))
        self.assertEqual(self.errors(), [])
        (self.ws / "paper" / "main.tex").write_text(
            "As shown by \\citet{known2020} and \\citep[p.~3]{ghost1999}.\n% \\cite{commented}\n")
        found = self.errors()
        self.assertTrue(any("ghost1999" in e for e in found))
        self.assertFalse(any("commented" in e or "known2020" in e for e in found))

    def test_dataset_hash_is_checked(self) -> None:
        raw = self.ws / "data" / "raw"
        raw.mkdir(parents=True)
        (raw / "d.csv").write_text("a,b\n1,2\n")
        entry = {"id": "d", "origin": "https://example.org/d.csv", "license": "CC0", "path": "data/raw/d.csv",
                 "sha256": crew.sha256(raw / "d.csv"), "retrieved_on": "2026-11-18"}
        edit_json(self.ws / "data" / "manifest.json", lambda manifest: manifest["datasets"].append(entry))
        self.assertEqual(self.errors(), [])
        (raw / "d.csv").write_text("a,b\n1,3\n")
        self.assertTrue(any("does not match the recorded sha256" in e for e in self.errors()))
        (raw / "d.csv").unlink()
        self.assertEqual(self.errors(), [])
        self.assertTrue(any("not present" in e for e in self.errors(strict=True)))

    def test_full_path_through_all_four_gates(self) -> None:
        self.to_design()
        self.run_main()
        self.add_claim()
        call("numbers", str(self.ws))
        write_review(self.ws, "results")
        self.assertEqual(self.approve("results")[0], 0)
        write_review(self.ws, "paper")
        code, out = self.approve("submission")
        self.assertEqual(code, 1)
        self.assertIn("main.pdf", out)
        (self.ws / "paper" / "main.pdf").write_bytes(b"%PDF-1.4\n")
        (self.ws / "paper" / "ai-use.tex").write_text("AI-use statement.\n")
        code, out = self.approve("submission")
        self.assertEqual(code, 1)
        self.assertIn("replication.json: missing", out)
        self.assertEqual(call("rerun", str(self.ws))[0], 0)
        self.assertEqual(self.approve("submission")[0], 0)
        self.assertEqual(self.errors(strict=True), [])
        code, out = call("status", str(self.ws))
        self.assertEqual(code, 0)
        self.assertIn("submission  approved", out)


SCORE_SPEC = importlib.util.spec_from_file_location("crew_score", ROOT / "crew" / "bench" / "score.py")
score = importlib.util.module_from_spec(SCORE_SPEC)
SCORE_SPEC.loader.exec_module(score)


class BenchScoreTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.ws = Path(self.tmp.name) / "ws"
        call("init", str(self.ws), "--track", "social-science", "--title", "T")

    def claims(self, values: dict) -> None:
        with (self.ws / "claims.jsonl").open("w") as handle:
            for claim_id, value in values.items():
                handle.write(json.dumps({"id": claim_id, "kind": "result", "text": "x",
                                         "support": [{"run": "r"}], "value": value}) + "\n")

    def test_bounds_check(self) -> None:
        key = {"machine_check": {"claims": {"plr-forest": [7400, 10600], "plr-tree": [7400, 10600]},
                                 "min_matched": 2}}
        self.claims({"plr-forest": 9100.0, "plr-tree": 8800.0})
        self.assertEqual(score.check_answer(self.ws, key)["status"], "pass")
        self.claims({"plr-forest": 9100.0, "plr-tree": 12000.0})
        self.assertEqual(score.check_answer(self.ws, key)["status"], "fail")
        self.claims({"plr-forest": 9100.0})
        self.assertEqual(score.check_answer(self.ws, key)["status"], "fail")

    def test_interval_must_contain_zero(self) -> None:
        key = {"machine_check": {"interval_contains_zero": ["lo", "hi"]}}
        self.claims({"lo": -250.0, "hi": 180.0})
        self.assertEqual(score.check_answer(self.ws, key)["status"], "pass")
        self.claims({"lo": 20.0, "hi": 400.0})
        self.assertEqual(score.check_answer(self.ws, key)["status"], "fail")

    def test_every_answer_key_has_a_machine_check_or_none(self) -> None:
        for key_path in (ROOT / "crew" / "bench" / "seeds").glob("*/answer.json"):
            rule = json.loads(key_path.read_text()).get("machine_check", {})
            self.assertTrue(set(rule) <= {"claims", "min_matched", "interval_contains_zero"}, key_path)


class PluginFilesTest(unittest.TestCase):
    def test_manifests_agree(self) -> None:
        plugin = json.loads((ROOT / "crew" / ".claude-plugin" / "plugin.json").read_text())
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
        entry = market["plugins"][0]
        self.assertEqual(entry["name"], plugin["name"])
        self.assertTrue((ROOT / entry["source"]).is_dir())

    def test_every_agent_is_a_known_role(self) -> None:
        agents = sorted(p.stem for p in (ROOT / "crew" / "agents").glob("*.md"))
        self.assertTrue(agents)
        for name in agents:
            self.assertIn(name, crew.ROLES)
            text = (ROOT / "crew" / "agents" / f"{name}.md").read_text()
            self.assertTrue(text.startswith(f"---\nname: {name}\n"), name)
            self.assertIn("\ndescription: ", text)
        self.assertIn("reviewer", agents)

    def test_every_role_has_a_role_kit(self) -> None:
        from tools import build_starter_kits as kits
        self.assertEqual(set(kits.ROLE_KITS), set(crew.ROLES) - {"pi"})
        for stages in kits.ROLE_KITS.values():
            self.assertTrue(set(stages) <= set(kits.STAGE_KEYS))

    def test_seed_tasks_are_well_formed(self) -> None:
        seeds = sorted((ROOT / "crew" / "bench" / "seeds").iterdir())
        self.assertTrue(seeds)
        for seed in seeds:
            task = json.loads((seed / "task.json").read_text())
            self.assertEqual(task["id"], seed.name)
            self.assertIn(task["track"], crew.TRACKS)
            self.assertTrue(task["question"])


if __name__ == "__main__":
    unittest.main()
