#!/usr/bin/env python3
"""Build catalog/STARTER-KITS.md: collision-free skill kits per research stage.

The hub bundles thousands of `SKILL.md` files, and hundreds of skill names
collide across collections (see ``catalog/collisions.json``). "Install
everything" is therefore the wrong default, but "pick the right five skills for
literature review" is hard to do by hand. This generator answers that question
for each stage of a research project.

For every stage it ranks catalogued skills by:

* **relevance** — stage keywords matched against the skill name (weighted) and
  its description;
* **depth** — the on-disk depth signals from ``build_maturity_report`` (bundled
  references, scripts, examples, evals, tests, ...), so production-grade skills
  beat bare prompts;
* **hygiene** — a clear trigger description and declared license metadata.

and then applies hard gates:

* only canonical copies (``duplicate_of`` empty) and real skills (no templates);
* no skill whose own directory carries a high/critical safety finding in a
  ``skill``/``script``/``other`` file (reusing ``scripts/scan-skill-safety.py``);
* no collection-root skills (whose "directory" is an entire repo);
* at most one skill per collection per stage, so each kit spans collections;
* skill names are unique across *all* kits, so every kit — or all of them
  together — can be installed into one agent profile without name collisions.

Output is deterministic (ties break on path) so ``--check`` is byte-stable.

    python3 tools/build_starter_kits.py                  # write the report + JSON
    python3 tools/build_starter_kits.py --check          # verify both are current
    python3 tools/build_starter_kits.py --install literature --dest ~/.claude/skills
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.build_maturity_report import SIGNAL_LABELS, _dir_signals  # noqa: E402

SKILLS_JSON = ROOT / "catalog" / "skills.json"
REPORT_PATH = ROOT / "catalog" / "STARTER-KITS.md"
JSON_PATH = ROOT / "catalog" / "starter-kits.json"
SCAN_PATH = ROOT / "scripts" / "scan-skill-safety.py"

KIT_SIZE = 5
MIN_RELEVANCE = 3
RELEVANCE_CAP = 6
REVIEW_CONTEXTS = {"skill", "script", "other"}
SCAN_MAX_BYTES = 1_000_000


@dataclass(frozen=True)
class Stage:
    key: str
    title: str
    blurb: str
    keywords: tuple[str, ...]
    # Skills whose *name* contains any of these phrases are off-target here.
    exclude: tuple[str, ...] = ()


# Ordered along a research project's lifecycle. Keywords are matched as
# lowercase whole words/phrases; keep them specific to limit false positives.
STAGES: tuple[Stage, ...] = (
    Stage("ideation", "Ideation & research questions",
          "Generate, stress-test, and sharpen research ideas and hypotheses.",
          ("ideation", "brainstorm", "brainstorming", "hypothesis", "hypotheses",
           "research question", "research idea", "novelty", "topic selection", "idea")),
    Stage("literature", "Literature search & review",
          "Find papers and synthesize them into a structured review.",
          ("literature review", "literature search", "systematic review", "literature",
           "paper search", "arxiv", "pubmed", "semantic scholar", "related work", "survey")),
    Stage("reading", "Paper reading & notes",
          "Read, summarize, and annotate papers; keep a connected reading library.",
          ("paper reading", "read paper", "reading notes", "summarize paper",
           "paper summary", "zotero", "pdf", "daily paper", "reader"),
          exclude=("variant", "gene", "protein")),
    Stage("experiment", "Experiment design & reproduction",
          "Plan experiments and reproduce published results with an audit trail.",
          ("experiment design", "experimental design", "experiment", "experiments",
           "reproduce", "reproduction", "replication", "reproducibility", "ablation",
           "pre-registration", "preregistration")),
    Stage("analysis", "Data analysis & statistics",
          "Run statistical, econometric, and causal analyses on research data.",
          ("statistics", "statistical", "regression", "econometrics", "econometric",
           "causal inference", "difference-in-differences", "data analysis", "stata",
           "panel data", "hypothesis testing")),
    Stage("writing", "Paper drafting & polishing",
          "Draft, structure, and polish manuscripts in an academic register.",
          ("academic writing", "paper writing", "write paper", "manuscript",
           "scientific writing", "polish", "polishing", "abstract", "introduction",
           "writing")),
    Stage("figures", "Figures, tables & LaTeX",
          "Produce publication-grade figures, tables, and LaTeX.",
          ("figure", "figures", "plot", "plotting", "visualization", "latex",
           "table", "tables", "tikz", "chart")),
    Stage("review", "Peer review, rebuttal & revision",
          "Simulate referees, answer reviewers, and revise.",
          ("peer review", "referee", "reviewer", "reviewers", "rebuttal",
           "response to reviewers", "revision", "revise", "critique")),
    Stage("integrity", "Citations & research integrity",
          "Verify references and catch fabricated or unsupported claims.",
          ("citation", "citations", "bibtex", "reference check", "references",
           "hallucination", "fact-check", "fact check", "plagiarism", "integrity",
           "verification", "retraction")),
    Stage("grants", "Grant & proposal writing",
          "Write funding proposals and specific-aims pages.",
          ("grant", "grants", "proposal", "nsf", "nih", "funding", "specific aims"),
          exclude=("template", "templates", "venue")),
    Stage("presentation", "Slides, posters & dissemination",
          "Turn a paper into a talk, poster, or public summary.",
          ("slides", "slide", "presentation", "poster", "beamer", "talk",
           "pptx", "keynote")),
    Stage("lifescience", "Life-science databases & tools",
          "Query biological databases and run computational-biology tools.",
          ("protein", "uniprot", "alphafold", "genomics", "genomic", "single-cell",
           "chembl", "pubchem", "bioinformatics", "sequence", "variant", "gene")),
)
STAGE_KEYS = tuple(s.key for s in STAGES)

TRIGGER_RE = re.compile(r"\b(use when|use this|use for|trigger|triggers|when the user|when user)\b", re.I)
SAFE_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")


@dataclass
class Pick:
    stage: str
    name: str
    collection: str
    path: str
    description: str
    license: str
    signals: list[str] = field(default_factory=list)
    relevance: int = 0
    score: float = 0.0

    @property
    def skill_dir(self) -> str:
        return str(Path(self.path).parent)


def load_scan_module():
    spec = importlib.util.spec_from_file_location("scan_skill_safety_kits_module", SCAN_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {SCAN_PATH.relative_to(ROOT)}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _phrase_re(phrase: str) -> re.Pattern[str]:
    return re.compile(r"(?<![a-z0-9])" + re.escape(phrase) + r"(?![a-z0-9])")


_PHRASES: dict[str, re.Pattern[str]] = {}


def keyword_hits(text: str, keywords: tuple[str, ...]) -> int:
    """Count distinct stage keywords present in ``text`` (lowercased)."""
    hits = 0
    for kw in keywords:
        pattern = _PHRASES.get(kw)
        if pattern is None:
            pattern = _PHRASES[kw] = _phrase_re(kw)
        if pattern.search(text):
            hits += 1
    return hits


def relevance(skill: dict, stage: Stage) -> int:
    name = re.sub(r"[-_./]+", " ", skill.get("name", "").lower())
    if stage.exclude and keyword_hits(name, stage.exclude):
        return 0
    desc = skill.get("description", "").lower()
    return 3 * keyword_hits(name, stage.keywords) + keyword_hits(desc, stage.keywords)


def is_collection_root(path: str, collection: str) -> bool:
    parent = Path(path).parent
    return parent == Path("skills") / collection


def eligible(skill: dict) -> bool:
    if skill.get("duplicate_of") or skill.get("is_template"):
        return False
    if not skill.get("has_frontmatter") or not skill.get("name"):
        return False
    if not SAFE_NAME_RE.match(skill["name"]):
        return False
    if len(skill.get("description", "")) < 40:
        return False
    return not is_collection_root(skill["path"], skill["collection"])


def base_score(skill: dict, rel: int, signals: set[str]) -> float:
    score = min(rel, RELEVANCE_CAP) + 2.0 * len(signals)
    if TRIGGER_RE.search(skill.get("description", "")):
        score += 1.0
    if skill.get("license"):
        score += 0.5
    return score


class SafetyGate:
    """Memoised "does this skill directory need manual review?" check."""

    def __init__(self, root: Path = ROOT, scan_module=None) -> None:
        self.root = root
        self._scan = scan_module
        self._cache: dict[str, bool] = {}

    def flagged(self, skill_dir: str) -> bool:
        if skill_dir not in self._cache:
            if self._scan is None:
                self._scan = load_scan_module()
            files = self._scan.iter_files([self.root / skill_dir], SCAN_MAX_BYTES)
            self._cache[skill_dir] = any(
                finding.context in REVIEW_CONTEXTS
                for path in files
                for finding in self._scan.scan_file(path, "high")
            )
        return self._cache[skill_dir]


def build_kits(skills: list[dict], root: Path = ROOT, gate: SafetyGate | None = None,
               kit_size: int = KIT_SIZE) -> dict[str, list[Pick]]:
    """Return {stage key: ranked picks} honouring every gate in the module doc."""
    gate = gate or SafetyGate(root)
    pool = [s for s in skills if eligible(s) and (root / s["path"]).exists()]
    signal_cache: dict[str, set[str]] = {}

    def signals_for(path: str) -> set[str]:
        if path not in signal_cache:
            signal_cache[path] = _dir_signals((root / path).parent)
        return signal_cache[path]

    used_names: set[str] = set()
    kits: dict[str, list[Pick]] = {}
    for stage in STAGES:
        ranked: list[Pick] = []
        for skill in pool:
            rel = relevance(skill, stage)
            if rel < MIN_RELEVANCE:
                continue
            sig = signals_for(skill["path"])
            ranked.append(Pick(
                stage=stage.key,
                name=skill["name"],
                collection=skill["collection"],
                path=skill["path"],
                description=skill.get("description", ""),
                license=skill.get("license", ""),
                signals=[k for k in SIGNAL_LABELS if k in sig],
                relevance=rel,
                score=base_score(skill, rel, sig),
            ))
        ranked.sort(key=lambda p: (-p.score, p.path))

        picks: list[Pick] = []
        seen_collections: set[str] = set()
        for cand in ranked:
            if len(picks) >= kit_size:
                break
            key = cand.name.lower()
            if key in used_names or cand.collection in seen_collections:
                continue
            if gate.flagged(cand.skill_dir):
                continue
            picks.append(cand)
            used_names.add(key)
            seen_collections.add(cand.collection)
        kits[stage.key] = picks
    return kits


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ").strip()


def short(text: str, limit: int = 140) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def render_report(kits: dict[str, list[Pick]], total_skills: int) -> str:
    picked = sum(len(v) for v in kits.values())
    collections = sorted({p.collection for v in kits.values() for p in v})
    lines = [
        "# 🧰 Starter Kits — collision-free skills per research stage",
        "",
        "> Generated by [`tools/build_starter_kits.py`](../tools/build_starter_kits.py). "
        "Do not edit by hand; run `make starter-kits`.",
        "",
        f"Out of **{total_skills:,}** catalogued `SKILL.md` files, these **{picked}** skills "
        f"from **{len(collections)}** collections form one kit per research stage. "
        "Every skill name is unique across all kits, so you can install one kit, "
        "several, or all of them into a single agent profile without the name "
        "collisions listed in [`collisions.json`](collisions.json).",
        "",
        "**How picks are made.** Stage keywords are matched against each skill's name "
        "(weighted ×3) and description. Matches are ranked by on-disk depth (bundled "
        "references, scripts, examples, evals, tests — see [`MATURITY.md`](MATURITY.md)), "
        "a clear trigger description, and declared license metadata. Hard gates:",
        "canonical copies only, no templates, no collection-root skills, at most one "
        "skill per collection per stage, and no skill whose own directory has a "
        "high/critical safety finding in a skill/script file "
        "(see [`SAFETY.md`](SAFETY.md)).",
        "",
        "**Install a kit** (copies each skill directory; refuses to overwrite):",
        "",
        "```bash",
        "./setup.sh   # or: git submodule update --init --depth 1",
        "python3 tools/build_starter_kits.py --install literature --dest ~/.claude/skills",
        "python3 tools/build_starter_kits.py --install all --dest ~/.codex/skills --dry-run",
        "```",
        "",
        "> These are heuristic, reviewer-assist picks — a strong starting point, not an "
        "endorsement. Read each `SKILL.md` before relying on it; the safety gate catches "
        "known-dangerous patterns, not every risk.",
        "",
        "## Stages",
        "",
    ]
    for stage in STAGES:
        n = len(kits.get(stage.key, []))
        lines.append(f"- [{stage.title}](#{stage.key}) — {n} skills (`--install {stage.key}`)")
    lines.append("")
    for stage in STAGES:
        lines += [
            f'<a id="{stage.key}"></a>',
            "",
            f"## {stage.title}",
            "",
            f"{stage.blurb}",
            "",
        ]
        picks = kits.get(stage.key, [])
        if not picks:
            lines += ["_No skill cleared the gates for this stage._", ""]
            continue
        lines += [
            "| # | Skill | Collection | Depth | What it does |",
            "|--:|---|---|---|---|",
        ]
        for i, p in enumerate(picks, 1):
            depth = ", ".join(SIGNAL_LABELS[s] for s in p.signals) or "bare prompt"
            lines.append(
                f"| {i} | [`{md_escape(p.name)}`](../{p.path}) | `{p.collection}` | "
                f"{md_escape(depth)} | {md_escape(short(p.description))} |"
            )
        lines.append("")
    lines += [
        "## Collections represented",
        "",
        ", ".join(f"`{c}`" for c in collections) + ".",
        "",
    ]
    return "\n".join(lines)


def render_json(kits: dict[str, list[Pick]]) -> str:
    payload = {
        "_generated_by": "tools/build_starter_kits.py",
        "_note": "Collision-free, safety-gated skill picks per research stage. Do not hand-edit.",
        "stages": [
            {
                "key": stage.key,
                "title": stage.title,
                "skills": [
                    {
                        "name": p.name,
                        "collection": p.collection,
                        "path": p.path,
                        "skill_dir": p.skill_dir,
                        "license": p.license,
                        "depth_signals": p.signals,
                    }
                    for p in kits.get(stage.key, [])
                ],
            }
            for stage in STAGES
        ],
    }
    return json.dumps(payload, indent=1, ensure_ascii=False) + "\n"


def install(kits: dict[str, list[Pick]], stage: str, dest: Path, dry_run: bool,
            force: bool, root: Path = ROOT) -> int:
    keys = STAGE_KEYS if stage == "all" else (stage,)
    picks = [p for k in keys for p in kits.get(k, [])]
    if not picks:
        print(f"ERROR: no skills in kit {stage!r}", file=sys.stderr)
        return 1
    dest = dest.expanduser()
    planned = []
    for p in picks:
        src = root / p.skill_dir
        target = dest / p.name
        if not (src / "SKILL.md").exists():
            print(f"ERROR: {p.skill_dir} is not checked out; run ./setup.sh first", file=sys.stderr)
            return 1
        if target.exists() and not force:
            print(f"ERROR: {target} already exists (use --force to replace)", file=sys.stderr)
            return 1
        planned.append((src, target))
    for src, target in planned:
        print(f"{'would copy' if dry_run else 'copy'} {src.relative_to(root)} -> {target}")
        if dry_run:
            continue
        if target.exists():
            shutil.rmtree(target)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, target, symlinks=True)
    print(f"{'Planned' if dry_run else 'Installed'} {len(planned)} skill(s) into {dest}")
    return 0


def check_file(path: Path, expected: str) -> int:
    rel = path.relative_to(ROOT)
    if not path.exists():
        print(f"ERROR: missing {rel}")
        print("Run: python3 tools/build_starter_kits.py")
        return 1
    if path.read_text(encoding="utf-8") != expected:
        print(f"ERROR: {rel} is outdated")
        print("Run: python3 tools/build_starter_kits.py")
        return 1
    print(f"OK: {rel} is current")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="verify outputs are current without writing")
    parser.add_argument("--install", metavar="STAGE", choices=STAGE_KEYS + ("all",),
                        help="copy a kit's skill directories into --dest")
    parser.add_argument("--dest", type=Path, help="target skills directory for --install")
    parser.add_argument("--dry-run", action="store_true", help="with --install: print the plan only")
    parser.add_argument("--force", action="store_true", help="with --install: replace existing skill dirs")
    args = parser.parse_args(argv)

    if not SKILLS_JSON.exists():
        print("ERROR: catalog/skills.json is missing; run python3 tools/build_catalog.py", file=sys.stderr)
        return 2
    catalog = json.loads(SKILLS_JSON.read_text(encoding="utf-8"))
    kits = build_kits(catalog["skills"])

    if args.install:
        if args.dest is None:
            parser.error("--install requires --dest")
        return install(kits, args.install, args.dest, args.dry_run, args.force)

    report = render_report(kits, len(catalog["skills"]))
    data = render_json(kits)
    if args.check:
        return check_file(REPORT_PATH, report) | check_file(JSON_PATH, data)
    REPORT_PATH.write_text(report, encoding="utf-8")
    JSON_PATH.write_text(data, encoding="utf-8")
    picked = sum(len(v) for v in kits.values())
    print(f"wrote {REPORT_PATH.relative_to(ROOT)} and {JSON_PATH.relative_to(ROOT)} ({picked} picks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
