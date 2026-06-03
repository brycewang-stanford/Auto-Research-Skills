#!/usr/bin/env python3
"""Build the discovery layer that powers the browsable website.

``build_catalog.py`` produces the canonical manifest (``catalog/skills.json``).
This tool sits *on top* of it and emits two small, enrichment-only files:

  catalog/search-index.json   compact, web-ready index (the website's only data
                              dependency) — drops heavy fields, adds derived
                              ``tags`` and per-skill ``flags``.
  catalog/collisions.json     resolves the name-collision usability hazard from
                              QUALITY.md: every skill name that means *different*
                              things across collections, with each variant's
                              trigger so a user can pick deliberately.

It reuses ``build_catalog``'s frontmatter parser and dedup logic verbatim — so
the index is always consistent with the manifest and never depends on a stale
``skills.json`` on disk. Fully offline, standard library only.

    python3 tools/build_index.py            # write the two files
    python3 tools/build_index.py --check    # verify they are current (for CI)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# Import the canonical parser rather than re-implementing it. Works both as a
# package module (``from tools import build_index`` — what the unittest suite
# uses) and as a standalone script (``python3 tools/build_index.py``).
try:
    from tools import build_catalog as bc
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build_catalog as bc  # noqa: E402

ROOT = bc.ROOT
OUT_DIR = bc.OUT_DIR
INDEX_PATH = OUT_DIR / "search-index.json"
COLLISIONS_PATH = OUT_DIR / "collisions.json"


# --------------------------------------------------------------------------
# Tagging — a small, deterministic, researcher-facing facet taxonomy.
# Each tag maps to substrings matched (case-insensitively) against a skill's
# name + description. Order does not matter; a skill can carry several tags.
# Keep this list curated and small: tags are a *filter*, not a folksonomy.
# --------------------------------------------------------------------------
TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    "literature-review": (
        "literature review", "lit review", "systematic review", "survey of",
        "related work", "prisma", "meta-analysis", "scoping review",
    ),
    "paper-search": (
        "arxiv", "semantic scholar", "google scholar", "pubmed", "openalex",
        "paper search", "find papers", "search papers", "crossref",
    ),
    "writing": (
        "paper writing", "paper writer", "academic paper", "manuscript",
        "write paper", "drafting", "academic writing", "scientific writing",
        "abstract", "introduction section", "proofread", "copyedit", "editing",
    ),
    "citations": (
        "zotero", "mendeley", "endnote", "reference manager", "bibtex",
        "citation", "bibliograph", "reference",
    ),
    "peer-review": (
        "peer review", "peer-review", "reviewer", "rebuttal", "referee",
        "review response", "respond to review", "review loop",
    ),
    "causal-inference": (
        "causal", "difference-in-difference", "difference in difference",
        "diff-in-diff", "did regression", "event study", "instrumental variable",
        "regression discontinuity", "synthetic control", "propensity",
        "treatment effect", "counterfactual",
    ),
    "statistics": (
        "statistic", "regression", "econometric", "hypothesis test", "p-value",
        "bayesian", "inference", "estimation", "confidence interval", "anova",
    ),
    "data": (
        "data analysis", "dataset", "data cleaning", "pandas", "dataframe",
        "visualization", "visualisation", "plot", "figure", "chart", "table",
    ),
    "reproducibility": (
        "reproducib", "replicat", "audit", "provenance", "preregistration",
        "pre-registration",
    ),
    "bioinformatics": (
        "bioinformatic", "genomic", "sequencing", "rna-seq", "single-cell",
        "protein", "phylogen", "variant calling", "samtools",
    ),
    "medical": (
        "medical", "clinical", "patient", "diagnosis", "health", "disease",
        "epidemiolog",
    ),
    "grants": (
        "grant", "funding", "proposal", "nih", "nsf", "fellowship",
    ),
    "presentation": (
        "slides", "presentation", "poster", "keynote", "talk", "beamer",
    ),
    "ideation": (
        "ideation", "hypothesis generation", "research idea", "brainstorm",
        "novelty", "research question", "research direction",
    ),
    "latex": (
        "latex", "overleaf", "tex ", "beamer", "tikz",
    ),
    "automation": (
        "pipeline", "orchestrat", "workflow", "autonomous", "multi-agent",
        "end-to-end", "agent loop", "automated research",
    ),
    "experiment": (
        "experiment", "ablation", "benchmark", "evaluation", "training run",
        "hyperparameter",
    ),
}


# Skill *names* are the highest-signal text but are hyphen/underscore-joined
# ("lit-review-assistant", "academic-paper-writer"), while needles read as prose
# ("lit review"). Normalising separators on BOTH sides lets a name match a
# multi-word needle without weakening hyphenated needles like "rna-seq".
_SEP_RE = re.compile(r"[\s\-_/]+")


def _normalize(text: str) -> str:
    return _SEP_RE.sub(" ", text.lower()).strip()


_NORMALIZED_TAG_KEYWORDS: dict[str, tuple[str, ...]] = {
    tag: tuple(_normalize(n) for n in needles) for tag, needles in TAG_KEYWORDS.items()
}


def tags_for(name: str, description: str) -> list[str]:
    """Return the sorted set of facet tags matched by a skill's text.

    Matching is separator-insensitive, so a hyphenated skill name like
    ``peer-review`` matches the needle ``peer review``.
    """
    haystack = _normalize(f"{name} {description}")
    return sorted(
        tag
        for tag, needles in _NORMALIZED_TAG_KEYWORDS.items()
        if any(n in haystack for n in needles)
    )


# --------------------------------------------------------------------------
# Collision detection — a name "collides" when the same (lowercased) name
# resolves to *different* content in *more than one* collection. This matches
# QUALITY.md's definition exactly (cross-collection, distinct bodies).
# --------------------------------------------------------------------------
def colliding_names(skills: list[bc.Skill]) -> set[str]:
    bodies: dict[str, set[str]] = defaultdict(set)
    colls: dict[str, set[str]] = defaultdict(set)
    for s in skills:
        key = s.name.lower()
        bodies[key].add(s.content_hash)
        colls[key].add(s.collection)
    return {
        name
        for name in bodies
        if len(bodies[name]) > 1 and len(colls[name]) > 1
    }


def skill_flags(s: bc.Skill, collisions: set[str]) -> list[str]:
    flags: list[str] = []
    if s.is_template:
        flags.append("template")
    if s.duplicate_of:
        flags.append("dup")
    if not s.has_frontmatter:
        flags.append("no-fm")
    if s.name.lower() in collisions:
        flags.append("collision")
    return flags


# --------------------------------------------------------------------------
# Payload builders
# --------------------------------------------------------------------------
def build_index_payload(
    skills: list[bc.Skill], collections: list[bc.Collection]
) -> dict:
    collisions = colliding_names(skills)
    unique = len({s.content_hash for s in skills})
    used_tags: set[str] = set()

    index_skills = []
    for s in sorted(skills, key=lambda s: (s.collection.lower(), s.name.lower())):
        tags = tags_for(s.name, s.description)
        used_tags.update(tags)
        entry = {
            "name": s.name,
            "collection": s.collection,
            "trigger": bc.trigger_sentence(s.description, 200),
            "license": s.license,
            "path": s.path,
        }
        flags = skill_flags(s, collisions)
        if flags:
            entry["flags"] = flags
        if tags:
            entry["tags"] = tags
        index_skills.append(entry)

    return {
        "generated_by": "tools/build_index.py",
        "note": (
            "Compact discovery index consumed by site/. The canonical, complete "
            "manifest is catalog/skills.json. Regenerate with "
            "`python3 tools/build_index.py`."
        ),
        "totals": {
            "skill_files": len(skills),
            "unique_skills": unique,
            "collections": len(collections),
            "templates": sum(1 for s in skills if s.is_template),
            "no_frontmatter": sum(1 for s in skills if not s.has_frontmatter),
            "rebundled": sum(1 for s in skills if s.duplicate_of),
            "name_collisions": len(collisions),
        },
        "tags": sorted(used_tags),
        "collections": [
            {
                "name": c.name,
                "repo_url": c.repo_url,
                "skill_files": c.skill_count,
                "unique_skills": c.unique_count,
            }
            for c in sorted(collections, key=lambda c: c.name.lower())
        ],
        "skills": index_skills,
    }


def build_collisions_payload(skills: list[bc.Skill]) -> dict:
    collisions = colliding_names(skills)
    by_name: dict[str, list[bc.Skill]] = defaultdict(list)
    for s in skills:
        if s.name.lower() in collisions:
            by_name[s.name.lower()].append(s)

    groups = []
    for name in sorted(by_name):
        variants = by_name[name]
        # One representative per COLLECTION — the actionable view is "which
        # collection's <name> do I get", not how many nested copies exist.
        per_collection: dict[str, list[bc.Skill]] = defaultdict(list)
        for v in variants:
            per_collection[v.collection].append(v)
        reps = []
        for collection in sorted(per_collection, key=str.lower):
            items = sorted(per_collection[collection], key=lambda s: s.path.lower())
            bodies_here = len({s.content_hash for s in items})
            reps.append({
                "collection": collection,
                "repo_url": items[0].repo_url,
                "trigger": bc.trigger_sentence(items[0].description, 160),
                "path": items[0].path,
                "bodies_in_collection": bodies_here,
            })
        groups.append({
            "name": variants[0].name,
            "collections": len(per_collection),
            "distinct_bodies": len({v.content_hash for v in variants}),
            "total_copies": len(variants),
            "variants": reps,
        })
    groups.sort(key=lambda g: (-g["collections"], -g["distinct_bodies"], g["name"]))
    return {
        "generated_by": "tools/build_index.py",
        "note": (
            "Skill names that mean different things across collections. Most "
            "agent runtimes resolve skills by name, so installing two of these "
            "collections at once makes the winner undefined. Pick deliberately."
        ),
        "count": len(groups),
        "collisions": groups,
    }


def render(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def load_all() -> tuple[list[bc.Skill], list[bc.Collection]]:
    urls = bc.load_submodule_urls()
    skills = bc.load_skills(urls)
    bc.mark_duplicates(skills)
    collections = bc.build_collections(skills, urls)
    return skills, collections


def write_outputs(skills: list[bc.Skill], collections: list[bc.Collection]) -> list[Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(render(build_index_payload(skills, collections)), encoding="utf-8")
    COLLISIONS_PATH.write_text(render(build_collisions_payload(skills)), encoding="utf-8")
    return [INDEX_PATH, COLLISIONS_PATH]


def check_outputs(skills: list[bc.Skill], collections: list[bc.Collection]) -> int:
    expected = {
        INDEX_PATH: render(build_index_payload(skills, collections)),
        COLLISIONS_PATH: render(build_collisions_payload(skills)),
    }
    stale: list[str] = []
    for path, want in expected.items():
        if not path.exists():
            stale.append(f"missing: catalog/{path.name}")
        elif path.read_text(encoding="utf-8") != want:
            stale.append(f"outdated: catalog/{path.name}")
    if stale:
        for s in stale:
            print(f"ERROR: {s}")
        print("Run: python3 tools/build_index.py")
        return 1
    print("OK: discovery index files are current")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check", action="store_true",
        help="verify the index files are current without writing them",
    )
    args = parser.parse_args()

    if not bc.SKILLS_DIR.exists():
        print("skills/ not found; initialize submodules first.")
        return 1

    skills, collections = load_all()
    print(
        f"Indexed {len(skills)} skills, {len({s.content_hash for s in skills})} unique, "
        f"{len(colliding_names(skills))} colliding names."
    )
    if args.check:
        return check_outputs(skills, collections)

    written = write_outputs(skills, collections)
    for path in written:
        size_kb = path.stat().st_size / 1024
        print(f"  wrote {path.relative_to(ROOT)} ({size_kb:.0f} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
