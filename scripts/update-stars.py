#!/usr/bin/env python3
"""Refresh star counts for every bundled submodule and write STARS.md.

Reads .gitmodules, queries the GitHub API for each repo's current star count,
writes a sorted STARS.md leaderboard, and rewrites the Top 20 block between the
TOP20 markers in README.md / README_EN.md. Uses $GITHUB_TOKEN if present to lift
the rate limit. Safe to run locally or in CI.
"""
from __future__ import annotations

import configparser
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from urllib.parse import urlsplit
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITMODULES = ROOT / ".gitmodules"
OUT = ROOT / "STARS.md"
READMES = {"README.md": "zh", "README_EN.md": "en"}
TOP_N = 20
TOP_START = "<!-- TOP20:START -->"
TOP_END = "<!-- TOP20:END -->"
TOP_RE = re.compile(re.escape(TOP_START) + r".*?" + re.escape(TOP_END), re.S)
CATEGORY = {
    "skills": {"en": "Skills", "zh": "技能"},
    "systems": {"en": "System", "zh": "系统"},
    "benchmarks": {"en": "Benchmark", "zh": "评测"},
    "lists": {"en": "List", "zh": "清单"},
}
MEDALS = {1: "🥇", 2: "🥈", 3: "🥉"}
API = "https://api.github.com/repos/"


def github_slug(url: str) -> str | None:
    """Return owner/repo for supported GitHub remote URLs."""
    value = url.strip().rstrip("/")
    if value.endswith(".git"):
        value = value[:-4]
    if value.startswith("git@github.com:"):
        parts = value.split(":", 1)[1].split("/")
    else:
        parsed = urlsplit(value)
        host = parsed.hostname or ""
        if host.lower() not in {"github.com", "www.github.com"}:
            return None
        parts = [part for part in parsed.path.split("/") if part]
    if len(parts) != 2 or not all(parts):
        return None
    return f"{parts[0]}/{parts[1]}"


def parse_submodules() -> list[tuple[str, str]]:
    """Return (path, owner/repo) for each submodule."""
    cfg = configparser.ConfigParser()
    cfg.read(GITMODULES)
    out = []
    for section in cfg.sections():
        path = cfg[section].get("path", "")
        slug = github_slug(cfg[section].get("url", ""))
        if path and slug:
            out.append((path, slug))
    return out


def get_stars(slug: str) -> int | None:
    req = urllib.request.Request(API + slug)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "Auto-Research-Skills star refresher")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r).get("stargazers_count")
    except urllib.error.HTTPError as e:
        print(f"  ! {slug}: HTTP {e.code}", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f"  ! {slug}: {e}", file=sys.stderr)
    return None


def fmt(n: int) -> str:
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def render_top(rows: list[tuple[int, str, str]], lang: str, when: str) -> str:
    """Render the README Top-N table for rows sorted by stars (descending)."""
    if lang == "zh":
        note = f"> 按 GitHub star 数排名的前 {TOP_N} 个已收录仓库，由 [`scripts/update-stars.py`](scripts/update-stars.py) 每周自动刷新（最近：{when}）。完整榜单见 [STARS.md](STARS.md)。"
        header = "| # | 仓库 | ⭐ Stars | 类别 | 收录位置 |"
    else:
        note = f"> The {TOP_N} most-starred bundled repos, auto-refreshed weekly by [`scripts/update-stars.py`](scripts/update-stars.py) (last: {when}). Full ranking in [STARS.md](STARS.md)."
        header = "| # | Repo | ⭐ Stars | Type | Bundled at |"
    lines = [TOP_START, note, "", header, "|:-:|---|--:|:-:|---|"]
    for i, (stars, path, slug) in enumerate([r for r in rows if r[0] >= 0][:TOP_N], 1):
        cat = CATEGORY.get(path.split("/", 1)[0], {}).get(lang, path.split("/", 1)[0])
        rank = MEDALS.get(i, str(i))
        lines.append(
            f"| {rank} | [{slug}](https://github.com/{slug}) | {fmt(stars)} | {cat} | [`{path}`]({path}) |"
        )
    lines.append(TOP_END)
    return "\n".join(lines)


def update_readmes(rows: list[tuple[int, str, str]], when: str) -> None:
    for name, lang in READMES.items():
        path = ROOT / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        if not TOP_RE.search(text):
            print(f"  ! {name}: no {TOP_START} block, skipped", file=sys.stderr)
            continue
        block = render_top(rows, lang, when)
        path.write_text(TOP_RE.sub(lambda _: block, text, count=1), encoding="utf-8")
        print(f"Updated Top {TOP_N} in {name}.")


def main() -> int:
    subs = parse_submodules()
    rows = []
    for path, slug in subs:
        stars = get_stars(slug)
        print(f"  {slug}: {stars}")
        rows.append((stars if stars is not None else -1, path, slug))
    rows.sort(reverse=True)

    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# ⭐ Star Leaderboard",
        "",
        f"Auto-generated by [`scripts/update-stars.py`](scripts/update-stars.py). "
        f"Last refreshed: **{now}**.",
        "",
        f"Total bundled repos: **{len(rows)}**",
        "",
        "| # | ⭐ | Repo | Bundled at |",
        "|---|---|---|---|",
    ]
    for i, (stars, path, slug) in enumerate(rows, 1):
        s = fmt(stars) if stars >= 0 else "n/a"
        lines.append(f"| {i} | {s} | [{slug}](https://github.com/{slug}) | `{path}` |")
    lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {OUT} ({len(rows)} repos).")
    update_readmes(rows, now.split(" ")[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
