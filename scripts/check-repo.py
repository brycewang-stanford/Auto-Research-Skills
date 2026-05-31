#!/usr/bin/env python3
"""Validate repository metadata that commonly drifts in this hub.

The check is intentionally offline: it validates .gitmodules, tracked gitlinks,
headline counts in README files, STARS.md totals, and obvious nested submodule
mapping problems without calling the GitHub API.
"""
from __future__ import annotations

import argparse
import configparser
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GITMODULES = ROOT / ".gitmodules"
CATEGORIES = ("skills", "systems", "benchmarks", "lists")


@dataclass(frozen=True)
class Submodule:
    path: str
    url: str


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)

    def print(self) -> None:
        for message in self.errors:
            print(f"ERROR: {message}", file=sys.stderr)
        for message in self.warnings:
            print(f"WARN: {message}", file=sys.stderr)


def run_git(args: list[str], cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def parse_gitmodules(path: Path, reporter: Reporter) -> list[Submodule]:
    if not path.exists():
        reporter.error(f"missing {path.relative_to(ROOT)}")
        return []

    parser = configparser.ConfigParser()
    try:
        parser.read(path)
    except configparser.Error as exc:
        reporter.error(f"cannot parse {path.relative_to(ROOT)}: {exc}")
        return []

    submodules: list[Submodule] = []
    for section in parser.sections():
        module_path = parser[section].get("path", "").strip()
        url = parser[section].get("url", "").strip().rstrip("/")
        if not module_path:
            reporter.error(f"{section} has no path")
            continue
        if not url:
            reporter.error(f"{section} has no url")
            continue
        submodules.append(Submodule(module_path, url))
    return submodules


def tracked_gitlinks(cwd: Path = ROOT) -> set[str]:
    proc = run_git(["ls-files", "--stage"], cwd=cwd)
    if proc.returncode != 0:
        return set()
    out: set[str] = set()
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[0] == "160000":
            out.add(parts[3])
    return out


def check_submodule_index(submodules: list[Submodule], reporter: Reporter) -> None:
    paths = [module.path for module in submodules]
    urls = [module.url for module in submodules]
    for label, values in (("path", paths), ("url", urls)):
        seen: set[str] = set()
        for value in values:
            if value in seen:
                reporter.error(f"duplicate submodule {label}: {value}")
            seen.add(value)

    gitlinks = tracked_gitlinks()
    for path in paths:
        if path not in gitlinks:
            reporter.error(f".gitmodules path is not a tracked gitlink: {path}")
    for path in gitlinks:
        if path.split("/", 1)[0] in CATEGORIES and path not in paths:
            reporter.error(f"tracked gitlink is missing from .gitmodules: {path}")


def category_counts(submodules: list[Submodule]) -> dict[str, int]:
    counts = {category: 0 for category in CATEGORIES}
    for module in submodules:
        prefix = module.path.split("/", 1)[0]
        if prefix in counts:
            counts[prefix] += 1
    return counts


def read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def numbers_from(pattern: str, text: str) -> set[int]:
    values: set[int] = set()
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        values.add(int(match.group(1).replace(",", "")))
    return values


def check_readme_counts(
    submodules: list[Submodule], counts: dict[str, int], reporter: Reporter
) -> None:
    total = len(submodules)
    skill_files = list((ROOT / "skills").rglob("SKILL.md")) if (ROOT / "skills").exists() else []

    readmes = {
        "README.md": read_text(ROOT / "README.md"),
        "README_CN.md": read_text(ROOT / "README_CN.md"),
    }

    for name, text in readmes.items():
        if not text:
            reporter.warn(f"{name} is missing or empty")
            continue

        repo_claims = set()
        repo_claims |= numbers_from(r"\*\*([0-9,]+)\s+repos\*\*", text)
        repo_claims |= numbers_from(r"<b>([0-9,]+)\s+repos</b>", text)
        repo_claims |= numbers_from(r"\*\*([0-9,]+)\s+个仓库\*\*", text)
        repo_claims |= numbers_from(r"<b>([0-9,]+)\s+个仓库</b>", text)
        for claim in repo_claims:
            if claim != total:
                reporter.error(f"{name} claims {claim} repos, but .gitmodules has {total}")

        if skill_files:
            headline_claims = set()
            headline_claims |= numbers_from(r"\*\*([0-9][0-9,]*)\s+skills\*\*", text)
            headline_claims |= numbers_from(r"\*\*([0-9][0-9,]*)\s+个\s+skills\*\*", text)
            headline_claims |= numbers_from(r"alt=\"(?:已收录\s+)?([0-9][0-9,]*)\s+(?:个\s+)?skills", text)
            for claim in {claim for claim in headline_claims if claim >= 100}:
                if claim != len(skill_files):
                    reporter.error(
                        f"{name} claims {claim} skills, but found {len(skill_files)} SKILL.md files"
                    )
        else:
            reporter.warn("skills/ is not initialized; skipped raw SKILL.md count check")

    english = readmes["README.md"]
    english_expectations = {
        "skills": (r"([0-9,]+)\s+reusable skill", counts["skills"]),
        "systems": (r"([0-9,]+)\s+end-to-end systems", counts["systems"]),
        "benchmarks": (r"([0-9,]+)\s+benchmarks", counts["benchmarks"]),
        "lists": (r"([0-9,]+)\s+curated collections", counts["lists"]),
    }
    for label, (pattern, expected) in english_expectations.items():
        claims = numbers_from(pattern, english)
        for claim in claims:
            if claim != expected:
                reporter.error(f"README.md claims {claim} {label}, but .gitmodules has {expected}")


def check_stars_total(expected: int, reporter: Reporter) -> None:
    text = read_text(ROOT / "STARS.md")
    if not text:
        reporter.warn("STARS.md is missing or empty")
        return
    claims = numbers_from(r"Total bundled repos:\s+\*\*([0-9,]+)\*\*", text)
    if not claims:
        reporter.warn("STARS.md has no total bundled repos claim")
    for claim in claims:
        if claim != expected:
            reporter.error(f"STARS.md claims {claim} repos, but .gitmodules has {expected}")


def parse_nested_paths(path: Path, reporter: Reporter) -> set[str]:
    nested_file = path / ".gitmodules"
    if not nested_file.exists():
        return set()
    parser = configparser.ConfigParser()
    try:
        parser.read(nested_file)
    except configparser.Error as exc:
        reporter.warn(f"cannot parse {path.relative_to(ROOT)}/.gitmodules: {exc}")
        return set()
    return {parser[section].get("path", "").strip() for section in parser.sections()}


def check_nested_gitlinks(submodules: list[Submodule], reporter: Reporter, strict: bool) -> None:
    for module in submodules:
        path = ROOT / module.path
        if not path.exists():
            continue
        proc = run_git(["rev-parse", "--is-inside-work-tree"], cwd=path)
        if proc.returncode != 0:
            continue
        gitlinks = tracked_gitlinks(cwd=path)
        if not gitlinks:
            continue
        declared = parse_nested_paths(path, reporter)
        missing = sorted(gitlinks - declared)
        if missing:
            message = (
                f"{module.path} has nested gitlinks without .gitmodules mappings: "
                + ", ".join(missing)
            )
            if strict:
                reporter.error(message)
            else:
                reporter.warn(message)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--strict-nested",
        action="store_true",
        help="treat broken nested submodule mappings as errors instead of warnings",
    )
    args = parser.parse_args()

    reporter = Reporter()
    submodules = parse_gitmodules(GITMODULES, reporter)
    counts = category_counts(submodules)

    check_submodule_index(submodules, reporter)
    check_readme_counts(submodules, counts, reporter)
    check_stars_total(len(submodules), reporter)
    check_nested_gitlinks(submodules, reporter, strict=args.strict_nested)

    reporter.print()
    if reporter.errors:
        return 1

    print(
        "OK: "
        f"{len(submodules)} submodules "
        f"({counts['skills']} skills, {counts['systems']} systems, "
        f"{counts['benchmarks']} benchmarks, {counts['lists']} lists)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
