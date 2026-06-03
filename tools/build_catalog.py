#!/usr/bin/env python3
"""Build a browsable, machine-readable catalog of every bundled skill.

This hub vendors dozens of upstream collections as git submodules. Each
collection ships many individual skills (a directory with a ``SKILL.md``),
but there is no way to discover or search an *individual* skill across all
collections. This tool fixes that.

It walks ``skills/**/skill.md`` case-insensitively, parses each skill's YAML
frontmatter with a dependency-free parser (block scalars, quotes, and missing/garbled
frontmatter are all handled), maps each skill back to its source submodule
and GitHub URL, detects duplicate skills re-bundled by aggregator
collections, flags placeholder/template skills, and emits:

  catalog/skills.json              full machine-readable manifest
  catalog/skills.csv               flat one-row-per-skill table (grep/sheets)
  catalog/CATALOG.md               human overview + dedup analysis + index
  catalog/collections/<name>.md    per-collection skill tables

The check is fully offline and reads only ``.gitmodules`` and the working
tree. Re-run after submodules change:

    python3 tools/build_catalog.py

Counts are intentionally reported two ways: the raw ``SKILL.md`` file count
(the README headline number, inflated by aggregators) and the de-duplicated
unique-skill count (how many distinct skills actually exist).
"""
from __future__ import annotations

import argparse
import configparser
import csv
import hashlib
import json
import re
import tempfile
from collections import defaultdict
from dataclasses import dataclass, asdict, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = ROOT / "skills"
GITMODULES = ROOT / ".gitmodules"
OUT_DIR = ROOT / "catalog"
COLLECTIONS_DIR = OUT_DIR / "collections"

# Descriptions/names that mark a placeholder or scaffolding skill rather than
# a real one. Matched case-insensitively against the parsed values.
TEMPLATE_DESCRIPTIONS = {
    "a brief description of what this skill does",
    "brief description of what this skill does",
    "description of what this skill does",
    "a brief description of the skill",
}
TEMPLATE_NAMES = {"test-skill", "example-skill", "skill-template", "your-skill-name"}

# Crude marker that a SKILL.md body is the upstream Anthropic scaffold.
TEMPLATE_BODY_MARKERS = (
    "instructions for the agent to follow when this skill is activated",
    "1. first step\n2. second step",
)


# --------------------------------------------------------------------------
# Frontmatter parsing (dependency-free; handles the variance seen in the wild)
# --------------------------------------------------------------------------
_QUOTE_PAIRS = (('"', '"'), ("'", "'"))
_KEY_RE = re.compile(r"^([A-Za-z0-9_.-]+):\s?(.*)$")
_HTML_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
# A line carries no real text if it has no latin letter, digit, or CJK ideograph
# (e.g. box-drawing banners like ╔═══╗ that some vendored skills inject).
_HAS_TEXT_RE = re.compile(r"[A-Za-z0-9一-鿿]")


def clean_description(text: str) -> str:
    """Drop HTML-comment watermark banners and collapse whitespace."""
    text = _HTML_COMMENT_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def _strip_quotes(value: str) -> str:
    value = value.strip()
    for left, right in _QUOTE_PAIRS:
        if len(value) >= 2 and value.startswith(left) and value.endswith(right):
            return value[1:-1]
    return value


def parse_frontmatter(text: str) -> tuple[dict[str, str], str, bool]:
    """Return (top-level scalar metadata, body, has_frontmatter).

    Only top-level scalar keys are captured (``name``, ``description``,
    ``license``, ``version``, ``author``, ...). Nested mappings such as
    ``metadata:`` are skipped. Block scalars (``|`` / ``>`` and their
    ``-``/``+`` chomping variants) are folded to a single spaced string,
    which is what a catalog wants.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    if text.startswith("﻿"):
        text = text[1:]
    # Some vendored skills prepend a watermark HTML comment ABOVE the frontmatter
    # delimiter, which would otherwise hide the real ``name``/``description``.
    text = re.sub(r"\A\s*(?:<!--.*?-->\s*)+", "", text, flags=re.DOTALL)

    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}, text, False

    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return {}, text, False

    fm = lines[1:end]
    body = "\n".join(lines[end + 1 :])

    meta: dict[str, str] = {}
    i = 0
    while i < len(fm):
        line = fm[i]
        if not line.strip() or line.lstrip().startswith("#"):
            i += 1
            continue
        # Skip lines indented under a previous key (nested mapping/sequence).
        if line[:1] in (" ", "\t"):
            i += 1
            continue
        match = _KEY_RE.match(line)
        if not match:
            i += 1
            continue
        key = match.group(1).strip().lower()
        raw = match.group(2).strip()

        if raw in ("|", ">", "|-", ">-", "|+", ">+"):
            block: list[str] = []
            i += 1
            while i < len(fm):
                nxt = fm[i]
                if nxt.strip() == "":
                    block.append("")
                    i += 1
                    continue
                if nxt[:1] in (" ", "\t"):
                    block.append(nxt.strip())
                    i += 1
                else:
                    break
            meta[key] = re.sub(r"\s+", " ", " ".join(block)).strip()
            continue

        meta[key] = _strip_quotes(raw)
        i += 1
    return meta, body, True


def first_paragraph(body: str) -> str:
    """Best-effort description fallback from a frontmatter-less SKILL.md."""
    body = _HTML_COMMENT_RE.sub(" ", body)  # drop watermark banners first
    paragraph: list[str] = []
    in_fence = False
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("#") or not stripped:
            if paragraph:
                break
            continue
        if not _HAS_TEXT_RE.search(stripped):  # skip decorative / box-drawing lines
            continue
        paragraph.append(stripped)
        if len(" ".join(paragraph)) > 240:
            break
    return re.sub(r"\s+", " ", " ".join(paragraph)).strip()


def trigger_sentence(description: str, limit: int = 200) -> str:
    """A compact one-line summary for table cells."""
    description = re.sub(r"\s+", " ", description).strip()
    if len(description) <= limit:
        return description
    cut = description[:limit]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut + "…"


# --------------------------------------------------------------------------
# Data model
# --------------------------------------------------------------------------
@dataclass
class Skill:
    name: str
    collection: str
    path: str
    description: str
    repo_url: str = ""
    license: str = ""
    version: str = ""
    author: str = ""
    has_frontmatter: bool = True
    has_name: bool = True
    is_template: bool = False
    content_hash: str = ""
    duplicate_of: str = ""  # path of the canonical (first-seen) copy
    nested_depth: int = 0  # path components between the collection root and SKILL.md


@dataclass
class Collection:
    name: str
    repo_url: str
    skill_count: int = 0
    unique_count: int = 0
    template_count: int = 0
    rebundled_count: int = 0  # skills also present in another collection
    skills: list[Skill] = field(default_factory=list)


# --------------------------------------------------------------------------
# Loading
# --------------------------------------------------------------------------
def load_submodule_urls() -> dict[str, str]:
    """Map ``skills/<collection>`` -> GitHub URL from .gitmodules."""
    urls: dict[str, str] = {}
    if not GITMODULES.exists():
        return urls
    cfg = configparser.ConfigParser()
    try:
        cfg.read(GITMODULES)
    except configparser.Error:
        return urls
    for section in cfg.sections():
        path = cfg[section].get("path", "").strip()
        url = cfg[section].get("url", "").strip().rstrip("/")
        if url.endswith(".git"):
            url = url[:-4]
        if path:
            urls[path] = url
    return urls


def iter_skill_files() -> list[Path]:
    """Return skill files case-insensitively while preserving on-disk casing."""
    return sorted(
        path
        for path in SKILLS_DIR.rglob("*")
        if path.is_file() and path.name.lower() == "skill.md"
    )


def collection_of(skill_md: Path) -> tuple[str, int]:
    """Return (top-level collection name, nesting depth) for a SKILL.md path."""
    rel = skill_md.relative_to(SKILLS_DIR)
    parts = rel.parts
    collection = parts[0]
    # depth = directories between the collection root and the skill directory
    depth = max(0, len(parts) - 2)
    return collection, depth


def normalize_body(body: str) -> str:
    return re.sub(r"\s+", " ", body).strip().lower()


def load_skills(urls: dict[str, str]) -> list[Skill]:
    skills: list[Skill] = []
    for skill_md in iter_skill_files():
        try:
            text = skill_md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        meta, body, has_fm = parse_frontmatter(text)
        collection, depth = collection_of(skill_md)
        rel_path = str(skill_md.relative_to(ROOT))

        name = meta.get("name", "").strip()
        has_name = bool(name)
        if not has_name:
            name = skill_md.parent.name

        description = clean_description(meta.get("description", ""))
        if not description:
            description = first_paragraph(body)

        norm_desc = description.lower().strip()
        norm_body = normalize_body(body)
        is_template = (
            name.lower() in TEMPLATE_NAMES
            or any(norm_desc.startswith(t) for t in TEMPLATE_DESCRIPTIONS)
            or any(marker in norm_body for marker in TEMPLATE_BODY_MARKERS)
        )

        content_hash = hashlib.sha1(
            (name.lower() + " " + norm_body).encode("utf-8")
        ).hexdigest()[:16]

        skills.append(
            Skill(
                name=name,
                collection=collection,
                path=rel_path,
                description=description,
                repo_url=urls.get(f"skills/{collection}", ""),
                license=meta.get("license", "").strip(),
                version=meta.get("version", "").strip(),
                author=(meta.get("author", "") or meta.get("skill-author", "")).strip(),
                has_frontmatter=has_fm,
                has_name=has_name,
                is_template=is_template,
                content_hash=content_hash,
                nested_depth=depth,
            )
        )
    return skills


def mark_duplicates(skills: list[Skill]) -> None:
    """First-seen copy is canonical; later identical copies point to it."""
    canonical: dict[str, str] = {}
    for skill in skills:
        if skill.content_hash in canonical:
            skill.duplicate_of = canonical[skill.content_hash]
        else:
            canonical[skill.content_hash] = skill.path


def build_collections(skills: list[Skill], urls: dict[str, str]) -> list[Collection]:
    by_collection: dict[str, list[Skill]] = defaultdict(list)
    for skill in skills:
        by_collection[skill.collection].append(skill)

    # Which content hashes appear in more than one collection?
    hash_collections: dict[str, set[str]] = defaultdict(set)
    for skill in skills:
        hash_collections[skill.content_hash].add(skill.collection)

    collections: list[Collection] = []
    for name, items in sorted(by_collection.items()):
        items.sort(key=lambda s: (s.path.lower()))
        unique_hashes = {s.content_hash for s in items}
        rebundled = sum(
            1 for s in items if len(hash_collections[s.content_hash]) > 1
        )
        collections.append(
            Collection(
                name=name,
                repo_url=urls.get(f"skills/{name}", ""),
                skill_count=len(items),
                unique_count=len(unique_hashes),
                template_count=sum(1 for s in items if s.is_template),
                rebundled_count=rebundled,
                skills=items,
            )
        )
    collections.sort(key=lambda c: c.skill_count, reverse=True)
    return collections


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------
def md_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ").strip()


def write_json(
    skills: list[Skill], collections: list[Collection], out_dir: Path = OUT_DIR
) -> Path:
    unique_hashes = {s.content_hash for s in skills}
    payload = {
        "_generated_by": "tools/build_catalog.py",
        "_note": (
            "Auto-generated. 'total_skill_files' is the raw SKILL.md count "
            "(matches the README headline and includes copies re-bundled by "
            "aggregator collections). 'unique_skills' de-duplicates by "
            "name+body content hash."
        ),
        "totals": {
            "total_skill_files": len(skills),
            "unique_skills": len(unique_hashes),
            "collections": len(collections),
            "template_skills": sum(1 for s in skills if s.is_template),
            "without_frontmatter": sum(1 for s in skills if not s.has_frontmatter),
            "rebundled_copies": sum(1 for s in skills if s.duplicate_of),
        },
        "collections": [
            {
                "name": c.name,
                "repo_url": c.repo_url,
                "skill_files": c.skill_count,
                "unique_skills": c.unique_count,
                "template_skills": c.template_count,
                "rebundled_copies": c.rebundled_count,
            }
            for c in collections
        ],
        "skills": [asdict(s) for s in sorted(skills, key=lambda s: s.path.lower())],
    }
    out = out_dir / "skills.json"
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def write_csv(skills: list[Skill], out_dir: Path = OUT_DIR) -> Path:
    out = out_dir / "skills.csv"
    fields = [
        "name", "collection", "path", "repo_url", "license", "version",
        "author", "has_frontmatter", "is_template", "duplicate_of", "description",
    ]
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(fields)
        for s in sorted(skills, key=lambda s: (s.collection.lower(), s.path.lower())):
            writer.writerow([
                s.name, s.collection, s.path, s.repo_url, s.license, s.version,
                s.author, s.has_frontmatter, s.is_template, s.duplicate_of,
                re.sub(r"\s+", " ", s.description).strip(),
            ])
    return out


def write_collection_pages(
    collections: list[Collection], collections_dir: Path = COLLECTIONS_DIR
) -> list[Path]:
    collections_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for c in collections:
        lines = [
            f"# {c.name}",
            "",
            f"Source: [{c.repo_url}]({c.repo_url})" if c.repo_url else "Source: (local)",
            "",
            f"- Skill files: **{c.skill_count}**",
            f"- Unique skills: **{c.unique_count}**",
        ]
        if c.template_count:
            lines.append(f"- Placeholder/template skills: **{c.template_count}**")
        if c.rebundled_count:
            lines.append(
                f"- Copies also bundled by another collection: **{c.rebundled_count}**"
            )
        lines += [
            "",
            "> Auto-generated by `tools/build_catalog.py`. Do not edit by hand.",
            "",
            "| Skill | Trigger / description | Flags | Path |",
            "|---|---|---|---|",
        ]
        for s in c.skills:
            flags = []
            if s.is_template:
                flags.append("template")
            if s.duplicate_of:
                flags.append("dup")
            if not s.has_frontmatter:
                flags.append("no-fm")
            flag_str = ", ".join(flags) or "—"
            # Path is rendered as inline code, NOT a link: GitHub can't browse
            # into submodule contents from the parent repo, and the link checker
            # only materializes submodule top-dirs — so a file link would 404.
            # The path is exact for a local clone (after `setup.sh`/submodule init).
            lines.append(
                f"| `{md_escape(s.name)}` "
                f"| {md_escape(trigger_sentence(s.description))} "
                f"| {flag_str} "
                f"| `{md_escape(s.path)}` |"
            )
        lines.append("")
        out = collections_dir / f"{c.name}.md"
        out.write_text("\n".join(lines), encoding="utf-8")
        written.append(out)
    return written


def write_catalog_md(
    skills: list[Skill], collections: list[Collection], out_dir: Path = OUT_DIR
) -> Path:
    unique_hashes = {s.content_hash for s in skills}
    total = len(skills)
    unique = len(unique_hashes)
    templates = sum(1 for s in skills if s.is_template)
    no_fm = sum(1 for s in skills if not s.has_frontmatter)
    rebundled = sum(1 for s in skills if s.duplicate_of)

    lines = [
        "# 📚 Skill Catalog",
        "",
        "> **Auto-generated by [`tools/build_catalog.py`](../tools/build_catalog.py). Do not edit by hand.**",
        "> Re-run `python3 tools/build_catalog.py` after submodules change.",
        "",
        "An index of every individual skill bundled across all collections, so you "
        "can find a single skill without grepping dozens of submodules. Full "
        "machine-readable data lives in [`skills.json`](skills.json) and "
        "[`skills.csv`](skills.csv).",
        "",
        "## At a glance",
        "",
        "| Metric | Count |",
        "|---|---:|",
        f"| `SKILL.md` files (README headline number) | **{total:,}** |",
        f"| Unique skills (de-duplicated by name + body) | **{unique:,}** |",
        f"| Copies re-bundled by aggregator collections | {rebundled:,} |",
        f"| Placeholder / template skills | {templates:,} |",
        f"| Skills without YAML frontmatter | {no_fm:,} |",
        f"| Collections | {len(collections)} |",
        "",
        f"> The headline **{total:,}** counts every `SKILL.md` on disk. Aggregator "
        f"collections re-bundle other collections inside themselves, so only "
        f"**{unique:,}** of those skills are actually distinct — a ~{(1 - unique / total) * 100:.0f}% "
        "redundancy rate worth knowing when you browse.",
        "",
        "## Collections",
        "",
        "Sorted by skill count. Click a collection for its full skill list.",
        "",
        "| Collection | Skills | Unique | Re-bundled | Template | Source |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for c in collections:
        repo = f"[repo]({c.repo_url})" if c.repo_url else "—"
        lines.append(
            f"| [{c.name}](collections/{c.name}.md) "
            f"| {c.skill_count} | {c.unique_count} "
            f"| {c.rebundled_count} | {c.template_count} | {repo} |"
        )

    # Cross-collection duplicate clusters (the aggregator-inflation evidence).
    hash_to_paths: dict[str, list[Skill]] = defaultdict(list)
    for s in skills:
        hash_to_paths[s.content_hash].append(s)
    cross = [
        group
        for group in hash_to_paths.values()
        if len({s.collection for s in group}) > 1
    ]
    cross.sort(key=lambda g: len(g), reverse=True)

    lines += [
        "",
        "## Most re-bundled skills",
        "",
        "Identical skills (same name + body) that appear in multiple collections — "
        "the clearest signal of aggregator overlap. Showing the top 25 by copy count.",
        "",
        "| Skill | Copies | Found in collections |",
        "|---|---:|---|",
    ]
    for group in cross[:25]:
        name = group[0].name
        collections_in = sorted({s.collection for s in group})
        shown = ", ".join(f"`{c}`" for c in collections_in[:6])
        if len(collections_in) > 6:
            shown += f" +{len(collections_in) - 6} more"
        lines.append(f"| `{md_escape(name)}` | {len(group)} | {shown} |")

    lines += [
        "",
        "---",
        "",
        "*Want to add a new collection? See "
        "[`CURATION.md`](../CURATION.md). Want to discover candidate skills not "
        "yet bundled? See [`DISCOVERY.md`](DISCOVERY.md).*",
        "",
    ]
    out = out_dir / "CATALOG.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def write_outputs(
    skills: list[Skill], collections: list[Collection], out_dir: Path = OUT_DIR
) -> tuple[list[Path], list[Path]]:
    out_dir.mkdir(parents=True, exist_ok=True)
    collections_dir = out_dir / "collections"
    outputs = [
        write_json(skills, collections, out_dir),
        write_csv(skills, out_dir),
        write_catalog_md(skills, collections, out_dir),
    ]
    pages = write_collection_pages(collections, collections_dir)
    return outputs, pages


def stale_generated_collection_pages(
    written_pages: list[Path], collections_dir: Path = COLLECTIONS_DIR
) -> list[Path]:
    expected = {path.resolve() for path in written_pages}
    if not collections_dir.exists():
        return []
    return sorted(
        path
        for path in collections_dir.glob("*.md")
        if path.resolve() not in expected
    )


def relative_to_catalog(path: Path, out_dir: Path) -> str:
    return path.relative_to(out_dir).as_posix()


def check_generated_outputs(skills: list[Skill], collections: list[Collection]) -> int:
    with tempfile.TemporaryDirectory(prefix="ars-catalog-check-") as tmp:
        tmp_out = Path(tmp) / "catalog"
        outputs, pages = write_outputs(skills, collections, tmp_out)
        expected = sorted(path.relative_to(tmp_out) for path in [*outputs, *pages])

        missing: list[str] = []
        changed: list[str] = []
        for rel in expected:
            actual = OUT_DIR / rel
            generated = tmp_out / rel
            label = rel.as_posix()
            if not actual.exists():
                missing.append(label)
                continue
            if actual.read_bytes() != generated.read_bytes():
                changed.append(label)

        extra = [
            relative_to_catalog(path, OUT_DIR)
            for path in stale_generated_collection_pages([OUT_DIR / rel for rel in expected])
        ]

    if not (missing or changed or extra):
        print("OK: generated catalog files are current")
        return 0

    for label, values in (
        ("missing generated file", missing),
        ("outdated generated file", changed),
        ("stale generated file", extra),
    ):
        for value in values[:10]:
            print(f"ERROR: {label}: catalog/{value}")
        if len(values) > 10:
            print(f"ERROR: {label}: ... (+{len(values) - 10} more)")
    print("Run: python3 tools/build_catalog.py")
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify generated catalog files are current without writing them",
    )
    args = parser.parse_args()

    if not SKILLS_DIR.exists():
        print("skills/ not found; initialize submodules first.")
        return 1

    urls = load_submodule_urls()
    skills = load_skills(urls)
    mark_duplicates(skills)
    collections = build_collections(skills, urls)

    unique = len({s.content_hash for s in skills})
    print(
        f"Parsed {len(skills)} SKILL.md files across {len(collections)} collections "
        f"({unique} unique, "
        f"{sum(1 for s in skills if s.is_template)} template, "
        f"{sum(1 for s in skills if not s.has_frontmatter)} without frontmatter)."
    )

    if args.check:
        return check_generated_outputs(skills, collections)

    outputs, pages = write_outputs(skills, collections)
    stale_pages = stale_generated_collection_pages(pages)
    for path in stale_pages:
        path.unlink()

    for out in outputs:
        print(f"  wrote {out.relative_to(ROOT)}")
    print(f"  wrote {len(pages)} collection pages under {COLLECTIONS_DIR.relative_to(ROOT)}/")
    if stale_pages:
        print(f"  removed {len(stale_pages)} stale collection pages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
