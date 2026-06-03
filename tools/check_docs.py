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
    "README_EN.md",
    "STARS.md",
    "catalog",
    "docs",
    "site/README.md",
)
SKIP_DIRS = {".git", "benchmarks", "lists", "skills", "systems", "node_modules"}
MARKDOWN_TARGET = r"(<[^>]+>|[^)\s]+)"
MARKDOWN_TITLE = r"(?:\s+(?:\"[^\"]*\"|'[^']*'))?"
MARKDOWN_LINK_RE = re.compile(rf"(?<!!)\[[^\]]+\]\({MARKDOWN_TARGET}{MARKDOWN_TITLE}\)")
MARKDOWN_IMAGE_RE = re.compile(rf"!\[[^\]]*\]\({MARKDOWN_TARGET}{MARKDOWN_TITLE}\)")
MARKDOWN_REFERENCE_RE = re.compile(
    rf"^[ \t]{{0,3}}\[(?!\^)[^\]]+\]:[ \t]*{MARKDOWN_TARGET}"
    r"(?:[ \t]+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?[ \t]*$",
    re.MULTILINE,
)
HTML_ATTR_RE = re.compile(r"\b(?:href|src)=[\"']([^\"']+)[\"']", re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
HTML_ID_RE = re.compile(r"\b(?:id|name)=[\"']([^\"']+)[\"']", re.IGNORECASE)
HTML_TAG_RE = re.compile(r"<[^>]+>")
MARKDOWN_LINK_TEXT_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")
ANCHOR_UNSAFE_RE = re.compile(r"[^\w\-\ufe0f]", re.UNICODE)


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


def resolve_root(value: str) -> Path:
    root = Path(value)
    return root if root.is_absolute() else ROOT / root


def missing_roots(roots: list[Path]) -> list[str]:
    return [rel(root) for root in roots if not root.exists()]


def iter_markdown_files(roots: list[str]) -> list[Path]:
    files: set[Path] = set()
    for value in roots:
        path = resolve_root(value)
        if path.is_file() and path.suffix.lower() == ".md":
            files.add(path)
            continue
        if not path.exists():
            continue
        for candidate in path.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() != ".md":
                continue
            if any(part in SKIP_DIRS for part in candidate.relative_to(ROOT).parts):
                continue
            files.add(candidate)
    return sorted(files)


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def links_in_text(source: Path, text: str) -> list[DocLink]:
    cleaned = strip_code_fences(text)
    links: list[DocLink] = []
    for pattern in (MARKDOWN_LINK_RE, MARKDOWN_IMAGE_RE, MARKDOWN_REFERENCE_RE, HTML_ATTR_RE):
        for match in pattern.finditer(cleaned):
            target = match.group(1)
            if target.startswith("<") and target.endswith(">"):
                target = target[1:-1]
            links.append(DocLink(source, target, line_number(cleaned, match.start(1))))
    return links


def is_external(target: str) -> bool:
    if not target:
        return True
    parsed = urlsplit(target)
    return bool(parsed.scheme or parsed.netloc)


def resolve_local_target(source: Path, target: str) -> Path:
    path_part = unquote(urlsplit(target).path)
    if not path_part:
        return source.resolve()
    if path_part.startswith("/"):
        return (ROOT / path_part.lstrip("/")).resolve()
    return (source.parent / path_part).resolve()


def github_heading_slug(text: str) -> str:
    """Best-effort match for GitHub's Markdown heading ids."""
    text = HTML_TAG_RE.sub("", text)
    text = MARKDOWN_LINK_TEXT_RE.sub(r"\1", text)
    text = text.strip().lower()
    text = re.sub(r"\s+", "-", text)
    return ANCHOR_UNSAFE_RE.sub("", text)


def markdown_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for match in HEADING_RE.finditer(strip_code_fences(text)):
        base = github_heading_slug(match.group(2))
        if not base:
            continue
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    anchors.update(unquote(value) for value in HTML_ID_RE.findall(text))
    return anchors


def check_anchor(source: Path, target: Path, fragment: str, line: int) -> str | None:
    if target.suffix.lower() not in {".md", ".markdown"}:
        return None
    try:
        anchors = markdown_anchors(target.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        return f"{rel(source)}:{line} local link anchor target is not UTF-8: {rel(target)}"
    if fragment not in anchors:
        return f"{rel(source)}:{line} local link anchor missing: {link_label(target, fragment)}"
    return None


def link_label(path: Path, fragment: str) -> str:
    path_label = rel(path)
    return f"{path_label}#{fragment}" if fragment else path_label


def check_link(link: DocLink) -> str | None:
    if is_external(link.target):
        return None
    target = resolve_local_target(link.source, link.target)
    try:
        target.relative_to(ROOT.resolve())
    except ValueError:
        return f"{rel(link.source)}:{link.line} local link escapes repo root: {link.target}"
    if not target.exists():
        return f"{rel(link.source)}:{link.line} local link target missing: {link.target}"
    fragment = unquote(urlsplit(link.target).fragment)
    if fragment:
        return check_anchor(link.source, target, fragment, link.line)
    return None


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def main() -> int:
    errors: list[str] = []
    args = parse_args()
    missing = missing_roots([resolve_root(value) for value in args.roots])
    if missing:
        for root in missing:
            print(f"ERROR: docs root does not exist: {root}", file=sys.stderr)
        return 2

    files = iter_markdown_files(args.roots)
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
