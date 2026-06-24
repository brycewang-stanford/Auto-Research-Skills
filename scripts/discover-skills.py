#!/usr/bin/env python3
"""Discover new research-oriented skill / agent repos on GitHub.

Runs a curated set of GitHub search queries, de-duplicates the hits against
everything already bundled (`.gitmodules`) and against the existing backlog
(`catalog/DISCOVERY.md`, `CURATION.md`, the READMEs), drops forks / archived /
low-star noise, ranks what remains, and writes:

  * ``catalog/discovery-candidates.json`` — machine-readable candidate list, and
  * a markdown table on stdout — ready to triage into ``catalog/DISCOVERY.md``.

This is a *discovery aid*, not a vendoring step: it never edits ``.gitmodules``,
the READMEs, or ``STARS.md``. A human still runs the CURATION.md second-review
checklist before any ``git submodule add``.

    GITHUB_TOKEN=$(gh auth token) python3 scripts/discover-skills.py
    python3 scripts/discover-skills.py --min-stars 100 --top 40

Needs the network (GitHub Search API); ``$GITHUB_TOKEN`` lifts the rate limit.
"""
from __future__ import annotations

import argparse
import configparser
import datetime as dt
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
GITMODULES = ROOT / ".gitmodules"
OUT_JSON = ROOT / "catalog" / "discovery-candidates.json"
SEARCH_API = "https://api.github.com/search/repositories"

# Files whose GitHub links count as "already on our radar".
BACKLOG_FILES = [
    ROOT / "catalog" / "DISCOVERY.md",
    ROOT / "CURATION.md",
    ROOT / "README.md",
    ROOT / "README_EN.md",
]

# Curated, high-signal queries over the autonomous-research skill space.
# Each is run with sort=stars; keep them targeted to limit noise.
QUERIES = [
    "topic:claude-skills",
    "topic:agent-skills",
    "claude skills research in:name,description,readme",
    "agent skills scientific research in:name,description",
    "autonomous research agent in:name,description",
    "academic paper writing skills in:name,description",
    "deep research agent in:name,description",
    "literature review agent in:name,description",
    '"SKILL.md" research in:readme',
    "reference manager zotero agent in:name,description",
]

SLUG_RE = re.compile(r"github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)")

# A candidate must read as *research*-flavored, not just any agent/skill repo.
# Star-sorted search otherwise drowns the niche in generic mega-repos
# (awesome-python, crewAI, mem0, …). Require one of these in name+description.
RESEARCH_TERMS = (
    "research", "paper", "literature", "academic", "scientific", "science",
    "scholar", "citation", "arxiv", "zotero", "hypothesis", "experiment",
    "survey", "peer review", "manuscript", "thesis", "dissertation",
    "bibliograph", "reproducib", "discovery", "lab notebook",
)
# Generic catch-all lists / unrelated domains to exclude even if they slip
# a research word into a long description.
OFFTOPIC_TERMS = (
    "awesome lists about", "frameworks, libraries", "self-hosted",
    "ios apps", "cursorrules", "system prompts", "free tier",
    "job search", "career", "ui/ux", "design intelligence",
    "second brain", "product management", "pm skills", "seo ", " seo",
    "penetration test", "reverse engineer", "financial research",
    "company research", "stock", "blog skill", "deutsches recht",
    "bureaucratie", "time series", "workspace cli", "supply-chain bottleneck",
)


def github_slug(url: str) -> str | None:
    value = url.strip().rstrip("/")
    if value.endswith(".git"):
        value = value[:-4]
    if value.startswith("git@github.com:"):
        parts = value.split(":", 1)[1].split("/")
    else:
        parsed = urlsplit(value)
        if (parsed.hostname or "").lower() not in {"github.com", "www.github.com"}:
            return None
        parts = [p for p in parsed.path.split("/") if p]
    if len(parts) != 2 or not all(parts):
        return None
    return f"{parts[0]}/{parts[1]}"


def vendored_slugs() -> set[str]:
    cfg = configparser.ConfigParser()
    cfg.read(GITMODULES)
    out = set()
    for section in cfg.sections():
        slug = github_slug(cfg[section].get("url", ""))
        if slug:
            out.add(slug.lower())
    return out


def backlog_slugs(files: list[Path]) -> set[str]:
    """Slugs already mentioned in DISCOVERY/CURATION/README markdown."""
    out = set()
    for path in files:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for m in SLUG_RE.findall(text):
            slug = m[:-4] if m.endswith(".git") else m
            out.add(slug.lower())
    return out


def search(query: str, token: str | None, per_page: int = 50) -> list[dict]:
    params = urllib.parse.urlencode(
        {"q": query, "sort": "stars", "order": "desc", "per_page": per_page}
    )
    req = urllib.request.Request(f"{SEARCH_API}?{params}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "Auto-Research-Skills discovery")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r).get("items", [])
    except urllib.error.HTTPError as e:
        print(f"  ! query {query!r}: HTTP {e.code}", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f"  ! query {query!r}: {e}", file=sys.stderr)
    return []


def normalize(item: dict, matched_query: str) -> dict:
    return {
        "slug": item.get("full_name", ""),
        "stars": item.get("stargazers_count", 0),
        "language": item.get("language"),
        "license": (item.get("license") or {}).get("spdx_id"),
        "pushed_at": item.get("pushed_at"),
        "archived": bool(item.get("archived")),
        "fork": bool(item.get("fork")),
        "description": (item.get("description") or "").strip(),
        "matched_query": matched_query,
    }


def is_on_topic(candidate: dict) -> bool:
    """True if the repo reads as research-flavored and not generic noise. Pure."""
    haystack = f"{candidate['slug']} {candidate['description']}".lower()
    if any(term in haystack for term in OFFTOPIC_TERMS):
        return False
    return any(term in haystack for term in RESEARCH_TERMS)


def dedupe_and_filter(
    candidates: list[dict],
    known: set[str],
    min_stars: int,
    topic_filter: bool = True,
) -> list[dict]:
    """Keep the best record per fresh, on-bar, non-fork, live, on-topic slug. Pure."""
    best: dict[str, dict] = {}
    for c in candidates:
        slug = c["slug"]
        if not slug or slug.lower() in known:
            continue
        if c["fork"] or c["archived"]:
            continue
        if (c["stars"] or 0) < min_stars:
            continue
        if topic_filter and not is_on_topic(c):
            continue
        prev = best.get(slug.lower())
        # Keep the first query that surfaced it, but the max star reading.
        if prev is None:
            best[slug.lower()] = dict(c)
        else:
            prev["stars"] = max(prev["stars"], c["stars"])
    ranked = sorted(best.values(), key=lambda c: c["stars"], reverse=True)
    return ranked


def fmt_stars(n: int | None) -> str:
    if not n:
        return "0"
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def render_markdown(candidates: list[dict], now: dt.datetime) -> str:
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")
    out = [
        f"<!-- generated by scripts/discover-skills.py at {stamp} -->",
        "",
        f"### Auto-discovered candidates ({len(candidates)}) — {stamp}",
        "",
        "Fresh GitHub hits not already vendored or in the backlog. Triage the "
        "on-topic ones into the tiers above; ignore the rest. Re-run the "
        "discovery script to refresh.",
        "",
        "| Candidate | ⭐ | License | Lang | Last push | Description |",
        "|---|---:|---|---|---|---|",
    ]
    for c in candidates:
        push = (c["pushed_at"] or "")[:10] or "?"
        desc = c["description"].replace("|", "\\|")
        if len(desc) > 110:
            desc = desc[:107] + "…"
        out.append(
            f"| [{c['slug']}](https://github.com/{c['slug']}) | "
            f"{fmt_stars(c['stars'])} | {c['license'] or '—'} | "
            f"{c['language'] or '—'} | {push} | {desc} |"
        )
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-stars", type=int, default=80)
    parser.add_argument("--top", type=int, default=50, help="cap on candidates emitted")
    parser.add_argument("--per-page", type=int, default=100)
    parser.add_argument(
        "--no-topic-filter", action="store_true",
        help="skip the research-relevance filter (raw star-ranked hits)",
    )
    parser.add_argument("--json", type=Path, default=OUT_JSON)
    args = parser.parse_args(argv)

    token = os.environ.get("GITHUB_TOKEN")
    known = vendored_slugs() | backlog_slugs(BACKLOG_FILES)
    print(f"Known (vendored + backlog): {len(known)} slugs", file=sys.stderr)

    raw: list[dict] = []
    for q in QUERIES:
        items = search(q, token, args.per_page)
        print(f"  query {q!r}: {len(items)} hits", file=sys.stderr)
        raw.extend(normalize(it, q) for it in items)
        time.sleep(2)  # be gentle with the search rate limit

    candidates = dedupe_and_filter(
        raw, known, args.min_stars, topic_filter=not args.no_topic_filter
    )[: args.top]
    now = dt.datetime.now(dt.timezone.utc)

    args.json.write_text(
        json.dumps(
            {"generated_at": now.isoformat(), "count": len(candidates),
             "min_stars": args.min_stars, "candidates": candidates},
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"Wrote {args.json} ({len(candidates)} candidates).", file=sys.stderr)
    print(render_markdown(candidates, now))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
