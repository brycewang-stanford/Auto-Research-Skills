#!/usr/bin/env python3
"""Validate repository metadata that commonly drifts in this hub.

The check is intentionally offline: it validates .gitmodules, tracked gitlinks,
headline counts in README files, generated catalog freshness, STARS.md totals,
and obvious nested submodule mapping problems without calling the GitHub API.
"""
from __future__ import annotations

import argparse
import configparser
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
GITMODULES = ROOT / ".gitmodules"
CATEGORIES = ("skills", "systems", "benchmarks", "lists")
CONTENT_HASH_RE = re.compile(r"[0-9a-f]{16}")
STARS_ROW_RE = re.compile(
    r"^\|\s*\d+\s*\|\s*[^|]+\|\s*\[[^\]]+\]\(https://github\.com/([^)]+)\)\s*\|\s*`([^`]+)`\s*\|$",
    re.MULTILINE,
)


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


def github_repo_slug(url: str) -> str | None:
    """Return owner/repo for supported GitHub repository remote URLs."""
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


def safe_submodule_path(value: str) -> bool:
    path = PurePosixPath(value)
    return not value.startswith(("/", "\\")) and ".." not in path.parts


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
        section_match = re.fullmatch(r'submodule "(.+)"', section)
        if not section_match:
            reporter.error(f"malformed .gitmodules section: {section}")
        module_path = parser[section].get("path", "").strip()
        url = parser[section].get("url", "").strip().rstrip("/")
        if not module_path:
            reporter.error(f"{section} has no path")
            continue
        if not safe_submodule_path(module_path):
            reporter.error(f"{section} path is not a safe relative path: {module_path}")
        if not url:
            reporter.error(f"{section} has no url")
            continue
        if github_repo_slug(url) is None:
            reporter.error(f"{section} url is not a GitHub repository URL: {url}")
        if section_match and section_match.group(1) != module_path:
            reporter.error(
                f"{section} path mismatch: section names {section_match.group(1)}, "
                f"but path is {module_path}"
            )
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
    slugs = [github_repo_slug(module.url) for module in submodules]
    seen_slugs: set[str] = set()
    for module, slug in zip(submodules, slugs):
        if not slug:
            continue
        if slug in seen_slugs:
            reporter.error(f"duplicate submodule GitHub repo: {slug}")
        seen_slugs.add(slug)

    gitlinks = tracked_gitlinks()
    for path in paths:
        if path.split("/", 1)[0] not in CATEGORIES:
            reporter.error(f".gitmodules path uses unknown top-level category: {path}")
    for path in paths:
        if path not in gitlinks:
            reporter.error(f".gitmodules path is not a tracked gitlink: {path}")
    for path in gitlinks:
        if path.split("/", 1)[0] not in CATEGORIES:
            reporter.error(f"tracked gitlink uses unknown top-level category: {path}")
        elif path not in paths:
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


def skill_file_paths() -> list[Path]:
    skills_dir = ROOT / "skills"
    if not skills_dir.exists():
        return []
    return sorted(
        path
        for path in skills_dir.rglob("*")
        if path.is_file() and path.name.lower() == "skill.md"
    )


def numbers_from(pattern: str, text: str) -> set[int]:
    values: set[int] = set()
    for match in re.finditer(pattern, text, flags=re.IGNORECASE):
        values.add(int(match.group(1).replace(",", "")))
    return values


def check_readme_counts(
    submodules: list[Submodule],
    counts: dict[str, int],
    skill_files: list[Path],
    reporter: Reporter,
) -> None:
    total = len(submodules)

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
        if not repo_claims:
            reporter.error(f"{name} is missing a bundled repo count claim")
        for claim in repo_claims:
            if claim != total:
                reporter.error(f"{name} claims {claim} repos, but .gitmodules has {total}")

        if skill_files:
            headline_claims = set()
            headline_claims |= numbers_from(r"\*\*([0-9][0-9,]*)\s+skills\*\*", text)
            headline_claims |= numbers_from(r"\*\*([0-9][0-9,]*)\s+个\s+skills\*\*", text)
            headline_claims |= numbers_from(r"alt=\"(?:已收录\s+)?([0-9][0-9,]*)\s+(?:个\s+)?skills", text)
            headline_claims |= numbers_from(
                r"shields\.io/badge/[^\"'\s>]*?skills[^\"'\s>]*?-([0-9][0-9,]*)-",
                unquote(text),
            )
            if not headline_claims:
                reporter.error(f"{name} is missing a headline skill count claim")
            for claim in {claim for claim in headline_claims if claim >= 100}:
                if claim != len(skill_files):
                    reporter.error(
                        f"{name} claims {claim} skills, but found {len(skill_files)} SKILL.md files"
                    )
        else:
            reporter.warn("skills/ is not initialized; skipped raw SKILL.md count check")

    category_expectations = {
        "README.md": {
            "skills": (r"([0-9,]+)\s+reusable skill", counts["skills"]),
            "systems": (r"([0-9,]+)\s+end-to-end systems", counts["systems"]),
            "benchmarks": (r"([0-9,]+)\s+benchmarks", counts["benchmarks"]),
            "lists": (r"([0-9,]+)\s+curated collections", counts["lists"]),
        },
        "README_CN.md": {
            "skills": (r"`skills/`[^\n]*?([0-9,]+)\s+个", counts["skills"]),
            "systems": (r"`systems/`[^\n]*?([0-9,]+)\s+个", counts["systems"]),
            "benchmarks": (r"`benchmarks/`[^\n]*?([0-9,]+)\s+个", counts["benchmarks"]),
            "lists": (r"`lists/`[^\n]*?([0-9,]+)\s+个", counts["lists"]),
        },
    }
    for name, expectations in category_expectations.items():
        text = readmes[name]
        for label, (pattern, expected) in expectations.items():
            claims = numbers_from(pattern, text)
            if not claims:
                reporter.error(f"{name} is missing a {label} category count claim")
            for claim in claims:
                if claim != expected:
                    reporter.error(
                        f"{name} claims {claim} {label}, but .gitmodules has {expected}"
                    )


def sample(values: list[str], limit: int = 3) -> str:
    shown = values[:limit]
    suffix = "" if len(values) <= limit else f", ... (+{len(values) - limit} more)"
    return ", ".join(shown) + suffix


def check_int_field(label: str, value: object, expected: int, reporter: Reporter) -> None:
    if not isinstance(value, int):
        reporter.error(f"{label} is missing or not an integer")
    elif value != expected:
        reporter.error(f"{label} is {value}, but expected {expected}")


def check_catalog_manifest(skill_files: list[Path], reporter: Reporter) -> None:
    if not skill_files:
        return

    path = ROOT / "catalog" / "skills.json"
    if not path.exists():
        reporter.warn("catalog/skills.json is missing; run python3 tools/build_catalog.py")
        return

    try:
        payload = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        reporter.error(f"cannot parse catalog/skills.json: {exc}")
        return

    skills = payload.get("skills")
    if not isinstance(skills, list):
        reporter.error("catalog/skills.json has no skills list")
        return

    manifest_paths: list[str] = []
    path_hashes: dict[str, str] = {}
    duplicate_refs: list[tuple[str, str, str]] = []
    content_hashes: set[str] = set()
    hash_counts: Counter[str] = Counter()
    skill_records: list[tuple[str, str]] = []
    collection_counts: Counter[str] = Counter()
    collection_hashes: dict[str, set[str]] = defaultdict(set)
    collection_templates: Counter[str] = Counter()
    template_count = 0
    without_frontmatter_count = 0
    rebundled_count = 0
    for item in skills:
        if not isinstance(item, dict):
            reporter.error("catalog/skills.json contains a non-object skill entry")
            return
        skill_path = item.get("path")
        if isinstance(skill_path, str) and skill_path:
            manifest_paths.append(skill_path)
        else:
            reporter.error("catalog/skills.json contains a skill entry without a path")
            return
        content_hash = item.get("content_hash")
        if isinstance(content_hash, str) and content_hash:
            if not CONTENT_HASH_RE.fullmatch(content_hash):
                reporter.error(f"catalog/skills.json entry {skill_path} has invalid content_hash")
                return
            content_hashes.add(content_hash)
            hash_counts[content_hash] += 1
            path_hashes[skill_path] = content_hash
        else:
            reporter.error("catalog/skills.json contains a skill entry without a content_hash")
            return
        collection = item.get("collection")
        if not isinstance(collection, str) or not collection:
            reporter.error(f"catalog/skills.json entry {skill_path} has no collection")
            return
        if not skill_path.startswith(f"skills/{collection}/"):
            reporter.error(
                f"catalog/skills.json entry {skill_path} has collection {collection}, "
                "but path is outside that collection"
            )
            return
        collection_counts[collection] += 1
        collection_hashes[collection].add(content_hash)
        skill_records.append((collection, content_hash))
        is_template = item.get("is_template")
        if not isinstance(is_template, bool):
            reporter.error(f"catalog/skills.json entry {skill_path} has invalid is_template")
            return
        if is_template:
            template_count += 1
            collection_templates[collection] += 1
        has_name = item.get("has_name")
        if has_name is not None and not isinstance(has_name, bool):
            reporter.error(f"catalog/skills.json entry {skill_path} has invalid has_name")
            return
        nested_depth = item.get("nested_depth")
        if nested_depth is not None and (
            not isinstance(nested_depth, int) or nested_depth < 0
        ):
            reporter.error(f"catalog/skills.json entry {skill_path} has invalid nested_depth")
            return
        has_frontmatter = item.get("has_frontmatter")
        if not isinstance(has_frontmatter, bool):
            reporter.error(f"catalog/skills.json entry {skill_path} has invalid has_frontmatter")
            return
        if not has_frontmatter:
            without_frontmatter_count += 1
        duplicate_of = item.get("duplicate_of", "")
        if duplicate_of:
            if not isinstance(duplicate_of, str):
                reporter.error(f"catalog/skills.json entry {skill_path} has invalid duplicate_of")
                return
            duplicate_refs.append((skill_path, duplicate_of, content_hash))
            rebundled_count += 1

    manifest_path_set = set(manifest_paths)
    if len(manifest_path_set) != len(manifest_paths):
        reporter.error("catalog/skills.json contains duplicate skill paths")
    expected_rebundled = max(0, len(manifest_paths) - len(content_hashes))
    if rebundled_count != expected_rebundled:
        reporter.error(
            "catalog/skills.json rebundled flags do not match content hashes: "
            f"{rebundled_count} flagged, expected {expected_rebundled}"
        )
    for skill_path, duplicate_of, content_hash in duplicate_refs:
        if duplicate_of == skill_path:
            reporter.error(f"catalog/skills.json entry {skill_path} duplicate_of points to itself")
            continue
        target_hash = path_hashes.get(duplicate_of)
        if target_hash is None:
            reporter.error(
                f"catalog/skills.json entry {skill_path} duplicate_of target missing: {duplicate_of}"
            )
            continue
        if target_hash != content_hash:
            reporter.error(
                f"catalog/skills.json entry {skill_path} duplicate_of target has different content_hash"
            )
    duplicate_ref_paths = {path for path, _, _ in duplicate_refs}
    unflagged_by_hash: dict[str, list[str]] = defaultdict(list)
    for skill_path, content_hash in path_hashes.items():
        if hash_counts[content_hash] > 1 and skill_path not in duplicate_ref_paths:
            unflagged_by_hash[content_hash].append(skill_path)
    invalid_canonical_groups = [
        paths for paths in unflagged_by_hash.values() if len(paths) != 1
    ]
    if invalid_canonical_groups:
        reporter.error(
            "catalog/skills.json duplicate hashes must have exactly one unflagged canonical path: "
            f"{sample(sorted(invalid_canonical_groups[0]))}"
        )
    hash_collections: dict[str, set[str]] = defaultdict(set)
    for collection, content_hash in skill_records:
        hash_collections[content_hash].add(collection)
    cross_collection_rebundled: Counter[str] = Counter(
        collection
        for collection, content_hash in skill_records
        if len(hash_collections[content_hash]) > 1
    )

    current_paths = {path.relative_to(ROOT).as_posix() for path in skill_files}
    missing = sorted(current_paths - manifest_path_set)
    stale = sorted(manifest_path_set - current_paths)
    if missing:
        reporter.error(
            "catalog/skills.json is stale; missing current skill path(s): "
            f"{sample(missing)}"
        )
    if stale:
        reporter.error(
            "catalog/skills.json is stale; includes removed skill path(s): "
            f"{sample(stale)}"
        )

    totals = payload.get("totals")
    if not isinstance(totals, dict):
        reporter.error("catalog/skills.json has no totals object")
        return
    check_int_field(
        "catalog/skills.json totals.total_skill_files",
        totals.get("total_skill_files"),
        len(current_paths),
        reporter,
    )
    check_int_field(
        "catalog/skills.json totals.unique_skills",
        totals.get("unique_skills"),
        len(content_hashes),
        reporter,
    )
    check_int_field(
        "catalog/skills.json totals.collections",
        totals.get("collections"),
        len(collection_counts),
        reporter,
    )
    check_int_field(
        "catalog/skills.json totals.template_skills",
        totals.get("template_skills"),
        template_count,
        reporter,
    )
    check_int_field(
        "catalog/skills.json totals.without_frontmatter",
        totals.get("without_frontmatter"),
        without_frontmatter_count,
        reporter,
    )
    check_int_field(
        "catalog/skills.json totals.rebundled_copies",
        totals.get("rebundled_copies"),
        rebundled_count,
        reporter,
    )

    collections = payload.get("collections")
    if not isinstance(collections, list):
        reporter.error("catalog/skills.json has no collections list")
        return

    collection_names: list[str] = []
    for i, collection in enumerate(collections):
        if not isinstance(collection, dict):
            reporter.error(f"catalog/skills.json collections[{i}] is not an object")
            return
        name = collection.get("name")
        if not isinstance(name, str) or not name:
            reporter.error(f"catalog/skills.json collections[{i}] has no name")
            return
        collection_names.append(name)
        check_int_field(
            f"catalog/skills.json collections[{i}].skill_files",
            collection.get("skill_files"),
            collection_counts[name],
            reporter,
        )
        check_int_field(
            f"catalog/skills.json collections[{i}].unique_skills",
            collection.get("unique_skills"),
            len(collection_hashes[name]),
            reporter,
        )
        check_int_field(
            f"catalog/skills.json collections[{i}].template_skills",
            collection.get("template_skills"),
            collection_templates[name],
            reporter,
        )
        check_int_field(
            f"catalog/skills.json collections[{i}].rebundled_copies",
            collection.get("rebundled_copies"),
            cross_collection_rebundled[name],
            reporter,
        )

    duplicate_collections = sorted(
        name for name, count in Counter(collection_names).items() if count > 1
    )
    if duplicate_collections:
        reporter.error(
            "catalog/skills.json collections contains duplicate name(s): "
            f"{sample(duplicate_collections)}"
        )

    summary_names = set(collection_names)
    skill_collection_names = set(collection_counts)
    missing_collections = sorted(skill_collection_names - summary_names)
    stale_collections = sorted(summary_names - skill_collection_names)
    if missing_collections:
        reporter.error(
            "catalog/skills.json collections missing current collection(s): "
            f"{sample(missing_collections)}"
        )
    if stale_collections:
        reporter.error(
            "catalog/skills.json collections includes removed collection(s): "
            f"{sample(stale_collections)}"
        )


def check_stars_total(submodules: list[Submodule], reporter: Reporter) -> None:
    text = read_text(ROOT / "STARS.md")
    if not text:
        reporter.warn("STARS.md is missing or empty")
        return
    expected = len(submodules)
    claims = numbers_from(r"Total bundled repos:\s+\*\*([0-9,]+)\*\*", text)
    if not claims:
        reporter.warn("STARS.md has no total bundled repos claim")
    for claim in claims:
        if claim != expected:
            reporter.error(f"STARS.md claims {claim} repos, but .gitmodules has {expected}")

    expected_by_path = {
        module.path: github_repo_slug(module.url)
        for module in submodules
    }
    rows = [(repo, path) for repo, path in STARS_ROW_RE.findall(text)]
    if not rows:
        reporter.warn("STARS.md has no leaderboard rows")
        return
    row_paths = [path for _, path in rows]
    duplicate_paths = sorted(path for path, count in Counter(row_paths).items() if count > 1)
    if duplicate_paths:
        reporter.error(f"STARS.md contains duplicate bundled path(s): {sample(duplicate_paths)}")

    row_path_set = set(row_paths)
    expected_path_set = set(expected_by_path)
    missing = sorted(expected_path_set - row_path_set)
    stale = sorted(row_path_set - expected_path_set)
    if missing:
        reporter.error(f"STARS.md is missing bundled path(s): {sample(missing)}")
    if stale:
        reporter.error(f"STARS.md includes unknown bundled path(s): {sample(stale)}")
    for repo, path in rows:
        expected_repo = expected_by_path.get(path)
        if expected_repo and repo != expected_repo:
            reporter.error(
                f"STARS.md row for {path} links {repo}, but .gitmodules has {expected_repo}"
            )


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
    skill_files = skill_file_paths()

    check_submodule_index(submodules, reporter)
    check_readme_counts(submodules, counts, skill_files, reporter)
    check_catalog_manifest(skill_files, reporter)
    check_stars_total(submodules, reporter)
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
