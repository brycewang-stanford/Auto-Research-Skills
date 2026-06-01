#!/usr/bin/env python3
"""Validate local links in repository-owned Markdown documentation."""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROOTS = (
    "AGENTS.md",
    "CONTRIBUTING.md",
    "CURATION.md",
    "README.md",
    "README_CN.md",
    "STARS.md",
    "catalog",
    "docs",
    "site/README.md",
)
SKIP_DIRS = {".git", "benchmarks", "lists", "skills", "systems", "node_modules"}
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
MARKDOWN_IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HTML_ATTR_RE = re.compile(r"\b(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)


@dataclass(frozen=True)
class DocLink:
    source: Path
    target: str
    line: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roots",
        nargs="*",
        default=list(DEFAULT_ROOTS),
        help="Markdown files or directories to check.",
    )
    return parser.parse_args()


def strip_code_fences(text: str) -> str:
    lines = text.splitlines(keepends=True)
    in_fence = False
    fence_marker = ""
    out: list[str] = []
    for line in lines:
        match = re.match(r"^(\s*)(`{3,}|~{3,})", line)
        if match:
            marker = match.group(2)[0]
            if not in_fence:
                in_fence = True
                fence_marker = marker
            elif marker == fence_marker:
                in_fence = False
            out.append("\n")
            continue
        out.append("\n" if in_fence else line)
    return "".join(out)


def iter_markdown_files(roots: list[str]) -> list[Path]:
    files: set[Path] = set()
    for value in roots:
        root = Path(value)
        path = root if root.is_absolute() else ROOT / root
        if path.is_file() and path.suffix.lower() == ".md":
            files.add(path)
            continue
        if not path.exists():
            continue
        for candidate in path.rglob("*.md"):
            if any(part in SKIP_DIRS for part in candidate.relative_to(ROOT).parts):
                continue
            files.add(candidate)
    return sorted(files)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def links_in_text(source: Path, text: str) -> list[DocLink]:
    cleaned = strip_code_fences(text)
    links: list[DocLink] = []
    for pattern in (MARKDOWN_LINK_RE, MARKDOWN_IMAGE_RE, HTML_ATTR_RE):
        for match in pattern.finditer(cleaned):
            links.append(DocLink(source, match.group(1), line_number(cleaned, match.start(1))))
    return links


def is_external_or_anchor(target: str) -> bool:
    if not target or target.startswith("#"):
        return True
    parsed = urlsplit(target)
    return bool(parsed.scheme or parsed.netloc)


def resolve_local_target(source: Path, target: str) -> Path:
    path_part = unquote(urlsplit(target).path)
    if path_part.startswith("/"):
        return (ROOT / path_part.lstrip("/")).resolve()
    return (source.parent / path_part).resolve()


def check_link(link: DocLink) -> str | None:
    if is_external_or_anchor(link.target):
        return None
    target = resolve_local_target(link.source, link.target)
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        return f"{rel(link.source)}:{link.line} local link escapes repo root: {link.target}"
    if not target.exists():
        return f"{rel(link.source)}:{link.line} local link target missing: {link.target}"
    return None


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    errors: list[str] = []
    files = iter_markdown_files(parse_args().roots)
    for path in files:
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            errors.append(f"{rel(path)} cannot be decoded as UTF-8")
            continue
        for link in links_in_text(path, text):
            error = check_link(link)
            if error:
                errors.append(error)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print(f"OK: checked local Markdown links in {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
