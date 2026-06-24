#!/usr/bin/env python3
"""Refresh upstream health metadata for every bundled submodule.

Reads .gitmodules, queries the GitHub API for each repo's current
stars / license / last-push / archived state, classifies staleness and
license gaps, and writes ``catalog/HEALTH.md``.

Unlike the offline ``make check`` validators, this needs the network and is
meant to be run intentionally (like ``scripts/update-stars.py``). Uses
``$GITHUB_TOKEN`` if present to lift the rate limit.

    python3 scripts/check-submodule-health.py            # write catalog/HEALTH.md
    python3 scripts/check-submodule-health.py --json out.json
    python3 scripts/check-submodule-health.py --stale-days 540

The script never edits .gitmodules, the READMEs, or STARS.md.
"""
from __future__ import annotations

import argparse
import configparser
import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
GITMODULES = ROOT / ".gitmodules"
OUT = ROOT / "catalog" / "HEALTH.md"
API = "https://api.github.com/repos/"

# A repo with no push in this many days is flagged "stale".
DEFAULT_STALE_DAYS = 365
# SPDX ids the GitHub API uses for "no clear OSI license".
UNCLEAR_LICENSES = {None, "", "NOASSERTION"}


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
    """Return (path, owner/repo) for each submodule, sorted by path."""
    cfg = configparser.ConfigParser()
    cfg.read(GITMODULES)
    out = []
    for section in cfg.sections():
        path = cfg[section].get("path", "")
        slug = github_slug(cfg[section].get("url", ""))
        if path and slug:
            out.append((path, slug))
    out.sort()
    return out


def fetch_repo(slug: str) -> dict | None:
    """Return the raw GitHub repo object, or None on error."""
    req = urllib.request.Request(API + slug)
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", "Auto-Research-Skills health checker")
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        print(f"  ! {slug}: HTTP {e.code}", file=sys.stderr)
    except Exception as e:  # noqa: BLE001
        print(f"  ! {slug}: {e}", file=sys.stderr)
    return None


def parse_pushed_at(value: str | None) -> dt.datetime | None:
    """Parse an ISO-8601 'pushed_at' timestamp into an aware datetime."""
    if not value:
        return None
    try:
        return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def classify(
    path: str,
    slug: str,
    repo: dict | None,
    now: dt.datetime,
    stale_days: int = DEFAULT_STALE_DAYS,
) -> dict:
    """Pure classification of one submodule's health. No network."""
    if repo is None:
        return {
            "path": path,
            "slug": slug,
            "reachable": False,
            "stars": None,
            "license": None,
            "archived": None,
            "pushed_at": None,
            "days_since_push": None,
            "stale": False,
            "license_unclear": False,
            "flags": ["unreachable"],
        }
    license_id = (repo.get("license") or {}).get("spdx_id")
    pushed = parse_pushed_at(repo.get("pushed_at"))
    days = (now - pushed).days if pushed else None
    archived = bool(repo.get("archived"))
    stale = days is not None and days > stale_days
    license_unclear = license_id in UNCLEAR_LICENSES
    flags = []
    if archived:
        flags.append("archived")
    if stale:
        flags.append("stale")
    if license_unclear:
        flags.append("license")
    return {
        "path": path,
        "slug": slug,
        "reachable": True,
        "stars": repo.get("stargazers_count"),
        "license": license_id,
        "archived": archived,
        "pushed_at": repo.get("pushed_at"),
        "days_since_push": days,
        "stale": stale,
        "license_unclear": license_unclear,
        "flags": flags,
    }


def fmt_stars(n: int | None) -> str:
    if n is None:
        return "n/a"
    return f"{n/1000:.1f}k" if n >= 1000 else str(n)


def fmt_age(days: int | None) -> str:
    if days is None:
        return "?"
    if days >= 365:
        return f"{days // 365}y{(days % 365) // 30}m"
    if days >= 30:
        return f"{days // 30}mo"
    return f"{days}d"


def render(rows: list[dict], now: dt.datetime, stale_days: int) -> str:
    """Render the HEALTH.md report from classified rows. No network."""
    flagged = [r for r in rows if r["flags"]]
    archived = [r for r in rows if r.get("archived")]
    stale = [r for r in rows if r.get("stale")]
    unclear = [r for r in rows if r.get("license_unclear")]
    unreachable = [r for r in rows if not r["reachable"]]
    stamp = now.strftime("%Y-%m-%d %H:%M UTC")

    out = [
        "# 🩺 Submodule Health",
        "",
        "Auto-generated by "
        "[`scripts/check-submodule-health.py`](../scripts/check-submodule-health.py). "
        f"Last refreshed: **{stamp}**.",
        "",
        f"Upstream metadata for all **{len(rows)}** bundled submodules. A repo is "
        f"**stale** if it has had no push in over **{stale_days}** days, and "
        "**license-flagged** if GitHub reports no clear OSI license "
        "(`NOASSERTION` or none). This file is a live snapshot — re-run the "
        "script to refresh; it is not validated by the offline `make check`.",
        "",
        "## Summary",
        "",
        f"- Total submodules: **{len(rows)}**",
        f"- 🟢 Healthy (no flags): **{len(rows) - len(flagged)}**",
        f"- 🗄️ Archived upstream: **{len(archived)}**",
        f"- 🕸️ Stale (> {stale_days}d no push): **{len(stale)}**",
        f"- ⚖️ License unclear / missing: **{len(unclear)}**",
        f"- 🔌 Unreachable at scan time: **{len(unreachable)}**",
        "",
    ]

    if flagged:
        out += [
            "## ⚠️ Needs attention",
            "",
            "| Repo | Bundled at | ⭐ | License | Last push | Flags |",
            "|---|---|---:|---|---|---|",
        ]
        # Worst first: archived, then most stale, then by path.
        flagged.sort(
            key=lambda r: (
                not r.get("archived"),
                -(r.get("days_since_push") or 0),
                r["path"],
            )
        )
        for r in flagged:
            lic = r["license"] or "—"
            badges = " ".join(
                {
                    "archived": "🗄️archived",
                    "stale": "🕸️stale",
                    "license": "⚖️license",
                    "unreachable": "🔌unreachable",
                }[f]
                for f in r["flags"]
            )
            out.append(
                f"| [{r['slug']}](https://github.com/{r['slug']}) | `{r['path']}` "
                f"| {fmt_stars(r['stars'])} | {lic} | {fmt_age(r['days_since_push'])} ago "
                f"| {badges} |"
            )
        out.append("")

    out += [
        "## All submodules",
        "",
        "| Repo | Bundled at | ⭐ | License | Last push |",
        "|---|---|---:|---|---|",
    ]
    for r in sorted(rows, key=lambda r: r["path"]):
        lic = r["license"] or ("—" if r["reachable"] else "n/a")
        out.append(
            f"| [{r['slug']}](https://github.com/{r['slug']}) | `{r['path']}` "
            f"| {fmt_stars(r['stars'])} | {lic} | {fmt_age(r['days_since_push'])} ago |"
        )
    out.append("")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stale-days", type=int, default=DEFAULT_STALE_DAYS,
        help=f"days-since-push threshold for 'stale' (default {DEFAULT_STALE_DAYS})",
    )
    parser.add_argument(
        "--json", type=Path, default=None,
        help="also write the classified rows as JSON to this path",
    )
    args = parser.parse_args(argv)

    now = dt.datetime.now(dt.timezone.utc)
    rows = []
    for path, slug in parse_submodules():
        repo = fetch_repo(slug)
        row = classify(path, slug, repo, now, args.stale_days)
        flag_note = f" [{','.join(row['flags'])}]" if row["flags"] else ""
        print(f"  {slug}: {fmt_stars(row['stars'])}{flag_note}")
        rows.append(row)

    OUT.write_text(render(rows, now, args.stale_days), encoding="utf-8")
    print(f"Wrote {OUT} ({len(rows)} submodules, "
          f"{sum(1 for r in rows if r['flags'])} flagged).")
    if args.json:
        args.json.write_text(json.dumps(rows, indent=2), encoding="utf-8")
        print(f"Wrote {args.json}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
