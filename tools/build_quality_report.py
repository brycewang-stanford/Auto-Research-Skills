#!/usr/bin/env python3
"""Build catalog/QUALITY.md: a reproducible quality & redundancy report.

Everything except the watermark count is derived from the already-generated
``catalog/skills.json`` (so it stays consistent with the catalog's own
definitions of "unique" and "re-bundled"). The watermark finding reads the
vendored ``SKILL.md`` files directly, mirroring how
``tools/build_safety_report.py`` scans files; it is therefore meant to run in
the same context as the catalog tooling (top-level submodules checked out).

The output is intentionally free of timestamps so ``--check`` can compare it
byte-for-byte against a fresh regeneration.
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_JSON = ROOT / "catalog" / "skills.json"
REPORT_PATH = ROOT / "catalog" / "QUALITY.md"

# A watermark banner is one or more HTML comments prepended ABOVE the YAML
# frontmatter delimiter. This mirrors the strip in build_catalog.parse_frontmatter
# so the count matches the skills the catalog had to "recover".
_LEADING_COMMENTS_RE = re.compile(r"\A\s*(?:<!--.*?-->\s*)+", re.DOTALL)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify catalog/QUALITY.md is current without writing it",
    )
    parser.add_argument(
        "--collision-rows",
        type=int,
        default=12,
        help="how many top colliding skill names to tabulate",
    )
    parser.add_argument(
        "--offender-rows",
        type=int,
        default=8,
        help="how many top re-bundling collections to tabulate",
    )
    return parser.parse_args()


def load_skills() -> dict:
    if not SKILLS_JSON.exists():
        raise FileNotFoundError(
            f"{SKILLS_JSON.relative_to(ROOT)} is missing; run "
            "`python3 tools/build_catalog.py` first"
        )
    return json.loads(SKILLS_JSON.read_text(encoding="utf-8"))


def md_escape(value: object) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def pct(part: int, whole: int) -> int:
    return round(100 * part / whole) if whole else 0


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------
def name_collisions(skills: list[dict]) -> list[tuple[str, int, list[str]]]:
    """Names whose content differs across more than one collection.

    Returns (name, distinct_body_count, sorted_collections), ordered by the
    number of distinct bodies (desc) then name, so the output is deterministic.
    """
    bodies: dict[str, set] = collections.defaultdict(set)
    where: dict[str, set] = collections.defaultdict(set)
    for skill in skills:
        key = skill["name"].lower()
        bodies[key].add(skill["content_hash"])
        where[key].add(skill["collection"])
    rows = [
        (name, len(bodies[name]), sorted(where[name]))
        for name in bodies
        if len(bodies[name]) > 1 and len(where[name]) > 1
    ]
    rows.sort(key=lambda row: (-row[1], -len(row[2]), row[0]))
    return rows


def count_watermarks(skills: list[dict]) -> tuple[collections.Counter, int, int]:
    """Count SKILL.md files that hide their frontmatter behind a leading comment.

    Returns (per-collection counter, total watermarked, files missing on disk).
    """
    per_collection: collections.Counter = collections.Counter()
    total = 0
    missing = 0
    for skill in skills:
        path = ROOT / skill["path"]
        if not path.exists():
            missing += 1
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            missing += 1
            continue
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        if text.startswith("﻿"):
            text = text[1:]
        match = _LEADING_COMMENTS_RE.match(text)
        if match and text[match.end():].lstrip().startswith("---"):
            total += 1
            per_collection[skill["collection"]] += 1
    return per_collection, total, missing


def no_frontmatter(skills: list[dict]) -> collections.Counter:
    return collections.Counter(
        skill["collection"] for skill in skills if not skill["has_frontmatter"]
    )


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def render_report(data: dict, collision_rows: int, offender_rows: int) -> str:
    skills = data["skills"]
    totals = data["totals"]
    collections_meta = data["collections"]

    files = totals["total_skill_files"]
    unique = totals["unique_skills"]
    rebundled = totals["rebundled_copies"]
    templates = totals["template_skills"]
    without_fm = totals["without_frontmatter"]

    collisions = name_collisions(skills)
    wm_by_collection, wm_total, wm_missing = count_watermarks(skills)
    nofm_by_collection = no_frontmatter(skills)
    licensed = sum(1 for skill in skills if skill.get("license", "").strip())

    offenders = sorted(
        (c for c in collections_meta if c.get("rebundled_copies", 0) > 0),
        key=lambda c: (-c["rebundled_copies"], c["name"]),
    )[:offender_rows]

    lines: list[str] = [
        "# 🔬 Quality & redundancy findings",
        "",
        "Generated by `tools/build_quality_report.py` from `catalog/skills.json`",
        f"(the watermark count reads the vendored `SKILL.md` files). These are",
        "**findings and suggestions for the maintainer**, not edits — curation",
        "decisions live in [`../CURATION.md`](../CURATION.md). Regenerate with",
        "`make quality-report`; CI fails if this file drifts from the catalog.",
        "",
        "## 1. The headline count is partly redundant",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| `SKILL.md` files on disk (README headline) | **{files:,}** |",
        f"| Distinct skills (by content hash) | **{unique:,}** |",
        f"| Re-bundled copies | **{rebundled:,}** ({pct(rebundled, files)}%) |",
        "",
        "Aggregator collections vendor other collections *inside themselves*, so",
        "the same skill is counted many times. The collections re-bundling the",
        "most copies (a copy is a skill whose body also appears earlier in the",
        "scan order):",
        "",
        "| Collection | Files | Unique | Re-bundled |",
        "|---|---:|---:|---:|",
    ]
    for c in offenders:
        lines.append(
            f"| `{md_escape(c['name'])}` | {c['skill_files']:,} | "
            f"{c['unique_skills']:,} | {c['rebundled_copies']:,} |"
        )
    lines.extend([
        "",
        "**Suggestion:** keep the on-disk headline (it is honest about what is",
        f"vendored) but cite the **{unique:,} unique** figure alongside it so",
        "users are not misled about breadth. The catalog surfaces both.",
        "",
        "## 2. Name collisions are the real usability hazard ⚠️",
        "",
        f"**{len(collisions)} skill names** resolve to *different content* across",
        "collections — the same name means different things depending on which",
        "collection an agent loaded. Most colliding names:",
        "",
        "| Skill name | Distinct bodies | Appears in |",
        "|---|---:|---|",
    ])
    for name, distinct, where in collisions[:collision_rows]:
        appears = ", ".join(f"`{md_escape(w)}`" for w in where)
        lines.append(f"| `{md_escape(name)}` | {distinct} | {appears} |")
    if len(collisions) > collision_rows:
        lines.append(f"| _… and {len(collisions) - collision_rows} more_ | | |")
    lines.extend([
        "",
        "This matters because most agent runtimes resolve skills **by name**. If",
        "a user installs two collections that both ship a `paper-writing`, which",
        "one wins is undefined. **Suggestion:** document that collections are",
        "meant to be installed *individually*, not all at once. The catalog's",
        "per-collection pages show what each colliding name actually does.",
        "",
        "## 3. Watermark banners hide frontmatter from strict loaders ⚠️",
        "",
        f"**{wm_total} skills** carry a watermark HTML comment (e.g. a collector",
        "banner) **prepended above** the `---` frontmatter delimiter. A naive",
        "parser — or a runtime that requires frontmatter on line 1 — sees the",
        "comment first and treats the skill as having **no `name`/`description`**,",
        "so it silently will not trigger.",
        "",
    ])
    if wm_total:
        lines.extend([
            "| Collection | Watermarked skills |",
            "|---|---:|",
        ])
        for name, count in sorted(wm_by_collection.items(), key=lambda kv: (-kv[1], kv[0])):
            lines.append(f"| `{md_escape(name)}` | {count} |")
        lines.append("")
    lines.extend([
        "The catalog handles this (it strips a leading comment block before",
        "parsing). But for the agents that *consume* these skills it is a real",
        "defect worth an upstream fix; a prepended watermark that breaks skill",
        "discovery is also a mild supply-chain smell.",
        "",
        f"## 4. {without_fm} skills genuinely have no frontmatter",
        "",
        "After recovering the watermarked ones, these files ship no YAML",
        "frontmatter, so they will not auto-trigger by `name`/`description` in",
        "runtimes that require it:",
        "",
        "| Collection | Skills without frontmatter |",
        "|---|---:|",
    ])
    for name, count in sorted(nofm_by_collection.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"| `{md_escape(name)}` | {count} |")
    lines.extend([
        "",
        "The catalog still lists them (falling back to the directory name + first",
        "paragraph) and tags each `no-fm`. These are best fixed upstream, since",
        "submodules are vendored read-only.",
        "",
        f"## 5. Only {pct(licensed, files)}% of skills declare a license",
        "",
        f"**{licensed:,} / {files:,}** skills carry a `license:` field in their",
        "frontmatter. The rest inherit their repo's top-level license (if any) —",
        "fine, but it means a user copying a single skill out of a collection",
        "cannot tell its license from the `SKILL.md` alone. **Suggestion:** a",
        "soft recommendation in `CONTRIBUTING.md` that vendored collections prefer",
        "per-skill `license:` fields; not a blocker.",
        "",
        "For the complementary **per-repo** license picture (which submodules "
        "have no clear OSI license upstream, plus staleness), see "
        "[`HEALTH.md`](HEALTH.md), refreshed by "
        "`scripts/check-submodule-health.py`.",
        "",
        f"## 6. Placeholder / template skills ({templates})",
        "",
    ])
    template_paths = [s["path"] for s in skills if s["is_template"]]
    if template_paths:
        lines.append(
            "Skills still shipping an unedited Anthropic template "
            "(description \"A brief description of what this skill does\"), "
            "flagged `template` in the catalog:"
        )
        lines.append("")
        for path in sorted(template_paths):
            lines.append(f"- `{md_escape(path)}`")
    else:
        lines.append("No unedited template skills detected. ✅")
    lines.extend([
        "",
        "Harmless, but a good signal for the consistency checker so future",
        "template leakage is caught.",
        "",
        "---",
        "",
        "## Reproduce these numbers",
        "",
        "```bash",
        "python3 tools/build_catalog.py        # refresh catalog/skills.json",
        "python3 tools/build_quality_report.py # regenerate this file",
        "make quality-report-check             # verify it is current",
        "```",
    ])
    if wm_missing:
        lines.extend([
            "",
            f"> Note: {wm_missing} `SKILL.md` path(s) from the catalog were not",
            "> present on disk when the watermark scan ran (initialise the",
            "> top-level submodules to include them).",
        ])
    return "\n".join(lines) + "\n"


def check_report(report: str) -> int:
    if not REPORT_PATH.exists():
        print("ERROR: missing catalog/QUALITY.md")
        print("Run: python3 tools/build_quality_report.py")
        return 1
    if REPORT_PATH.read_text(encoding="utf-8") != report:
        print("ERROR: catalog/QUALITY.md is outdated")
        print("Run: python3 tools/build_quality_report.py")
        return 1
    print("OK: catalog/QUALITY.md is current")
    return 0


def main() -> int:
    args = parse_args()
    try:
        data = load_skills()
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    report = render_report(data, args.collision_rows, args.offender_rows)

    if args.check:
        return check_report(report)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"wrote {REPORT_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
