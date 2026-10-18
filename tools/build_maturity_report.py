#!/usr/bin/env python3
"""Build catalog/MATURITY.md: per-skill depth signals and per-collection scores.

The headline catalog counts *how many* skills exist. This report measures *how
deep* they are. A `SKILL.md` that ships `references/`, runnable `scripts/`,
worked `examples/`, an `evals/` gold set, and `tests/` is a production-grade
skill; a lone `SKILL.md` is a bare prompt. Both count as "1 skill" today — this
report lets a maintainer tell them apart and reward the former.

The depth signals are drawn straight from the two exemplar collections studied
in `docs/skill-design-patterns.md`: `nature-figure` ships `references/` +
`assets/` + `evals/`; `academic-paper` ships `references/` + `examples/` +
`templates/` + `agents/`.

Method: read skill paths from ``catalog/skills.json`` (so the skill universe
matches the catalog), then inspect each skill's on-disk directory (the parent
of its ``SKILL.md``) for supporting-asset signals. Requires the top-level
submodules to be checked out, same as the safety/quality reports.

Output is timestamp-free so ``--check`` compares byte-for-byte.

    python3 tools/build_maturity_report.py           # write catalog/MATURITY.md
    python3 tools/build_maturity_report.py --check    # verify it is current
"""
from __future__ import annotations

import argparse
import collections
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_JSON = ROOT / "catalog" / "skills.json"
REPORT_PATH = ROOT / "catalog" / "MATURITY.md"

# A skill counts as "rich" (production-grade) when it presents at least this
# many distinct depth signals beyond its bare SKILL.md.
RICH_THRESHOLD = 3

# Ordered for stable display. Each maps to a human label used in the report.
SIGNAL_LABELS = {
    "references": "references/",
    "code": "scripts/ or code",
    "examples": "examples/",
    "tests": "tests/",
    "evals": "evals/",
    "assets": "assets/",
    "templates": "templates/",
    "manifest": "manifest.yaml",
    "requirements": "requirements.txt",
}


@dataclass
class SkillDepth:
    path: str
    collection: str
    signals: set[str] = field(default_factory=set)

    @property
    def score(self) -> int:
        return len(self.signals)

    @property
    def is_rich(self) -> bool:
        return self.score >= RICH_THRESHOLD

    @property
    def is_bare(self) -> bool:
        return self.score == 0


def _dir_signals(skill_dir: Path) -> set[str]:
    """Inspect a skill directory for supporting-asset depth signals."""
    signals: set[str] = set()
    try:
        entries = list(skill_dir.iterdir())
    except OSError:
        return signals

    dir_names = {e.name.lower() for e in entries if e.is_dir()}
    file_names = {e.name.lower() for e in entries if e.is_file()}

    if "references" in dir_names or "reference" in dir_names:
        signals.add("references")
    if "examples" in dir_names or "example" in dir_names:
        signals.add("examples")
    if "tests" in dir_names or "test" in dir_names:
        signals.add("tests")
    if "assets" in dir_names:
        signals.add("assets")
    if "templates" in dir_names or "template" in dir_names:
        signals.add("templates")

    # Runnable code: a scripts/ dir, or any script file sitting next to SKILL.md.
    if "scripts" in dir_names or any(
        name.endswith((".py", ".sh", ".r", ".rb", ".js", ".ts"))
        for name in file_names
    ):
        signals.add("code")

    # Eval sets: an evals/ dir or an eval*.json fixture.
    if "evals" in dir_names or "eval" in dir_names or any(
        name.startswith("eval") and name.endswith(".json") for name in file_names
    ):
        signals.add("evals")

    if "manifest.yaml" in file_names or "manifest.yml" in file_names:
        signals.add("manifest")
    if "requirements.txt" in file_names:
        signals.add("requirements")

    return signals


def load_catalog() -> dict:
    if not SKILLS_JSON.exists():
        raise FileNotFoundError(
            f"{SKILLS_JSON.relative_to(ROOT)} is missing; run "
            "`python3 tools/build_catalog.py` first"
        )
    return json.loads(SKILLS_JSON.read_text(encoding="utf-8"))


def scan(catalog: dict) -> tuple[list[SkillDepth], int]:
    """Return (per-skill depth rows, count of paths missing on disk)."""
    rows: list[SkillDepth] = []
    missing = 0
    for skill in catalog["skills"]:
        skill_md = ROOT / skill["path"]
        if not skill_md.exists():
            missing += 1
            continue
        rows.append(
            SkillDepth(
                path=skill["path"],
                collection=skill["collection"],
                signals=_dir_signals(skill_md.parent),
            )
        )
    return rows, missing


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def pct(part: int, whole: int) -> int:
    return round(100 * part / whole) if whole else 0


def render_report(rows: list[SkillDepth], missing: int, top_rows: int = 20) -> str:
    total = len(rows)
    rich = sum(1 for r in rows if r.is_rich)
    bare = sum(1 for r in rows if r.is_bare)

    signal_counts: collections.Counter = collections.Counter()
    for r in rows:
        for sig in r.signals:
            signal_counts[sig] += 1

    # Per-collection aggregation.
    by_collection: dict[str, list[SkillDepth]] = collections.defaultdict(list)
    for r in rows:
        by_collection[r.collection].append(r)

    collection_stats = []
    for name, items in by_collection.items():
        n = len(items)
        rich_n = sum(1 for r in items if r.is_rich)
        avg = sum(r.score for r in items) / n if n else 0.0
        collection_stats.append((name, n, rich_n, avg))

    # Rank by share of rich skills, then average depth, then size — surfaces the
    # genuinely production-grade collections rather than the biggest ones.
    ranked = sorted(
        collection_stats,
        key=lambda s: (-(s[2] / s[1] if s[1] else 0), -s[3], -s[1], s[0]),
    )

    lines: list[str] = [
        "# 🧱 Skill maturity & depth",
        "",
        "Generated by `tools/build_maturity_report.py` from `catalog/skills.json`",
        "(paths) plus an on-disk inspection of each skill's directory. These are",
        "**findings for the maintainer**, not edits. Regenerate with",
        "`make maturity-report`; CI fails if this file drifts.",
        "",
        "The catalog counts *how many* skills exist; this counts *how deep* they",
        "are. A skill that ships `references/`, `scripts/`, `examples/`, `evals/`,",
        "and `tests/` is production-grade; a lone `SKILL.md` is a bare prompt.",
        "Both count as one skill in the headline — this report tells them apart.",
        "See `docs/skill-design-patterns.md` for what these signals mean.",
        "",
        "## Depth signals",
        "",
        "Each skill scores one point per distinct signal found next to its",
        f"`SKILL.md`. A skill is **rich** at **{RICH_THRESHOLD}+** signals, **bare**",
        "at zero.",
        "",
        "| Signal | Skills with it | Share |",
        "|---|---:|---:|",
    ]
    for key, label in SIGNAL_LABELS.items():
        count = signal_counts.get(key, 0)
        lines.append(f"| `{md_escape(label)}` | {count:,} | {pct(count, total)}% |")

    lines += [
        "",
        "## At a glance",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| Skills inspected | **{total:,}** |",
        f"| Rich (≥{RICH_THRESHOLD} signals) | **{rich:,}** ({pct(rich, total)}%) |",
        f"| Bare (only `SKILL.md`) | {bare:,} ({pct(bare, total)}%) |",
        "",
        "## Deepest collections",
        "",
        "Ranked by share of **rich** skills, then average depth — the collections",
        "that invested in references, scripts, examples, evals, and tests rather",
        "than shipping bare prompts. Size is shown but does not drive the rank.",
        "",
        "| Collection | Skills | Rich | Rich % | Avg depth |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, n, rich_n, avg in ranked[:top_rows]:
        lines.append(
            f"| `{md_escape(name)}` | {n:,} | {rich_n:,} "
            f"| {pct(rich_n, n)}% | {avg:.1f} |"
        )

    lines += [
        "",
        "> Reading this: a high **Rich %** with a modest skill count is the",
        "> profile of a focused, production-grade collection. A large collection",
        "> with a low Rich % is broad but shallow — useful for coverage, less so",
        "> as a template to imitate.",
        "",
        "---",
        "",
        "## Reproduce these numbers",
        "",
        "```bash",
        "python3 tools/build_catalog.py         # refresh catalog/skills.json",
        "python3 tools/build_maturity_report.py # regenerate this file",
        "make maturity-report-check             # verify it is current",
        "```",
        "",
        "> Related: frontmatter conformance is in [`FRONTMATTER.md`](FRONTMATTER.md);",
        "> redundancy and licensing gaps are in [`QUALITY.md`](QUALITY.md).",
    ]
    if missing:
        lines += [
            "",
            f"> Note: {missing} `SKILL.md` path(s) from the catalog were not present",
            "> on disk when this scan ran (initialise the top-level submodules).",
        ]
    return "\n".join(lines) + "\n"


def check_report(report: str) -> int:
    if not REPORT_PATH.exists():
        print("ERROR: missing catalog/MATURITY.md")
        print("Run: python3 tools/build_maturity_report.py")
        return 1
    if REPORT_PATH.read_text(encoding="utf-8") != report:
        print("ERROR: catalog/MATURITY.md is outdated")
        print("Run: python3 tools/build_maturity_report.py")
        return 1
    print("OK: catalog/MATURITY.md is current")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify catalog/MATURITY.md is current without writing it",
    )
    args = parser.parse_args()

    try:
        catalog = load_catalog()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    rows, missing = scan(catalog)
    report = render_report(rows, missing)

    if args.check:
        return check_report(report)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)} ({len(rows)} skills inspected)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
