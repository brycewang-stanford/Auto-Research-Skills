#!/usr/bin/env python3
"""Validate the static discovery site and its data contract."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
INDEX = ROOT / "catalog" / "search-index.json"
COLLISIONS = ROOT / "catalog" / "collisions.json"
REQUIRED_INDEX_IDS = {
    "collectionBars",
    "collectionCount",
    "collectionFilter",
    "flagCollision",
    "flagNoFrontmatter",
    "flagTemplate",
    "query",
    "reset",
    "resultCount",
    "results",
    "status",
    "summary",
    "tagFilter",
}
REQUIRED_COLLISIONS_IDS = {
    "query",
    "resultCount",
    "results",
    "status",
    "summary",
}
INDEX_TOTAL_KEYS = (
    "skill_files",
    "unique_skills",
    "collections",
    "templates",
    "no_frontmatter",
    "rebundled",
    "name_collisions",
)
ALLOWED_SKILL_FLAGS = {"collision", "dup", "no-fm", "template"}
ASSET_ATTR_RE = re.compile(
    r"<(?:a|link|script|img)\b[^>]*\b(?:href|src)=([\"'])(.*?)\1",
    re.IGNORECASE,
)
CSS_URL_RE = re.compile(r"\burl\(\s*([\"']?)(.*?)\1\s*\)", re.IGNORECASE)


def error(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def linked_assets(html: str) -> set[str]:
    return {match.group(2) for match in ASSET_ATTR_RE.finditer(html)}


def css_assets(css: str) -> set[str]:
    return {match.group(2) for match in CSS_URL_RE.finditer(css)}


def is_http_url(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def element_ids(html: str) -> set[str]:
    return set(element_id_values(html))


def element_id_values(html: str) -> list[str]:
    return [match.group(2) for match in re.finditer(r"\bid=([\"'])(.*?)\1", html)]


def check_html_contract(
    html: str,
    required_ids: set[str],
    label: str,
    require_noscript: bool = False,
) -> list[str]:
    errors: list[str] = []
    ids = element_id_values(html)
    missing = sorted(required_ids - set(ids))
    if missing:
        errors.append(f"{label} missing required ids: {', '.join(missing)}")
    duplicates = sorted(value for value, count in Counter(ids).items() if count > 1)
    if duplicates:
        errors.append(f"{label} contains duplicate ids: {', '.join(duplicates)}")
    if require_noscript and "<noscript" not in html.lower():
        errors.append(f"{label} must include a noscript fallback")
    return errors


def check_index_payload(payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["catalog/search-index.json must contain a JSON object"]
    if payload.get("generated_by") != "tools/build_index.py":
        errors.append("catalog/search-index.json generated_by must be tools/build_index.py")
    for key in ("totals", "tags", "collections", "skills"):
        if key not in payload:
            errors.append(f"catalog/search-index.json missing key: {key}")
    totals = payload.get("totals", {})
    if not isinstance(totals, dict):
        errors.append("catalog/search-index.json totals must be an object")
    else:
        for key in INDEX_TOTAL_KEYS:
            if not isinstance(totals.get(key), int):
                errors.append(f"catalog/search-index.json totals.{key} must be an integer")

    declared_tags = payload.get("tags", [])
    if not isinstance(declared_tags, list) or not all(isinstance(tag, str) for tag in declared_tags):
        errors.append("catalog/search-index.json tags must be a list of strings")
        declared_tag_set: set[str] = set()
    else:
        if declared_tags != sorted(set(declared_tags)):
            errors.append("catalog/search-index.json tags must be sorted and unique")
        declared_tag_set = set(declared_tags)

    collections = payload.get("collections", [])
    collection_names: list[str] = []
    if not isinstance(collections, list) or not collections:
        errors.append("catalog/search-index.json collections must be a non-empty list")
    else:
        for i, collection in enumerate(collections):
            if not isinstance(collection, dict):
                errors.append(f"catalog/search-index.json collections[{i}] must be an object")
                continue
            missing = {"name", "skill_files", "unique_skills"} - set(collection)
            if missing:
                errors.append(
                    f"catalog/search-index.json collections[{i}] missing keys: "
                    f"{', '.join(sorted(missing))}"
                )
            name = collection.get("name")
            if isinstance(name, str) and name:
                collection_names.append(name)
            else:
                errors.append(f"catalog/search-index.json collections[{i}].name must be a non-empty string")
            for key in ("skill_files", "unique_skills"):
                if not isinstance(collection.get(key), int):
                    errors.append(f"catalog/search-index.json collections[{i}].{key} must be an integer")
            repo_url = collection.get("repo_url", "")
            if repo_url:
                if not isinstance(repo_url, str):
                    errors.append(f"catalog/search-index.json collections[{i}].repo_url must be a string")
                elif not is_http_url(repo_url):
                    errors.append(f"catalog/search-index.json collections[{i}].repo_url must be an HTTP(S) URL")
        duplicates = sorted(name for name, count in Counter(collection_names).items() if count > 1)
        if duplicates:
            errors.append(f"catalog/search-index.json collections contain duplicate names: {', '.join(duplicates)}")

    skills = payload.get("skills", [])
    if not isinstance(skills, list) or not skills:
        errors.append("catalog/search-index.json skills must be a non-empty list")
        return errors
    required = {"name", "collection", "trigger", "path"}
    paths: list[str] = []
    skill_collections: Counter[str] = Counter()
    used_tags: set[str] = set()
    flag_counts: Counter[str] = Counter()
    colliding_names: set[str] = set()
    known_collections = set(collection_names)
    for i, skill in enumerate(skills):
        if not isinstance(skill, dict):
            errors.append(f"catalog/search-index.json skills[{i}] must be an object")
            continue
        missing = sorted(required - set(skill))
        if missing:
            errors.append(
                f"catalog/search-index.json skills[{i}] missing keys: {', '.join(missing)}"
            )
            continue
        for key in required:
            if not isinstance(skill.get(key), str) or not skill.get(key):
                errors.append(f"catalog/search-index.json skills[{i}].{key} must be a non-empty string")
        collection = skill.get("collection")
        if isinstance(collection, str):
            skill_collections[collection] += 1
            if known_collections and collection not in known_collections:
                errors.append(
                    f"catalog/search-index.json skills[{i}] uses unknown collection: {collection}"
                )
        path = skill.get("path")
        if isinstance(path, str):
            paths.append(path)
            if isinstance(collection, str) and not path.startswith(f"skills/{collection}/"):
                errors.append(
                    f"catalog/search-index.json skills[{i}] path is outside collection: {path}"
                )
        tags = skill.get("tags", [])
        if tags:
            if not isinstance(tags, list) or not all(isinstance(tag, str) for tag in tags):
                errors.append(f"catalog/search-index.json skills[{i}].tags must be a list of strings")
            else:
                if tags != sorted(set(tags)):
                    errors.append(f"catalog/search-index.json skills[{i}].tags must be sorted and unique")
                used_tags.update(tags)
        flags = skill.get("flags", [])
        if flags:
            if not isinstance(flags, list) or not all(isinstance(flag, str) for flag in flags):
                errors.append(f"catalog/search-index.json skills[{i}].flags must be a list of strings")
            else:
                duplicate_flags = sorted(flag for flag, count in Counter(flags).items() if count > 1)
                if duplicate_flags:
                    errors.append(
                        f"catalog/search-index.json skills[{i}] has duplicate flags: "
                        f"{', '.join(duplicate_flags)}"
                    )
                unknown = sorted(set(flags) - ALLOWED_SKILL_FLAGS)
                if unknown:
                    errors.append(
                        f"catalog/search-index.json skills[{i}] has unknown flags: {', '.join(unknown)}"
                    )
                flag_counts.update(flags)
                if "collision" in flags and isinstance(skill.get("name"), str):
                    colliding_names.add(skill["name"].lower())
    duplicate_paths = sorted(path for path, count in Counter(paths).items() if count > 1)
    if duplicate_paths:
        errors.append(
            "catalog/search-index.json skills contain duplicate paths: "
            + ", ".join(duplicate_paths[:5])
        )

    if declared_tag_set != used_tags:
        missing = sorted(used_tags - declared_tag_set)
        stale = sorted(declared_tag_set - used_tags)
        if missing:
            errors.append(f"catalog/search-index.json tags missing used tags: {', '.join(missing)}")
        if stale:
            errors.append(f"catalog/search-index.json tags include unused tags: {', '.join(stale)}")

    if isinstance(collections, list):
        for i, collection in enumerate(collections):
            if not isinstance(collection, dict) or not isinstance(collection.get("name"), str):
                continue
            name = collection["name"]
            if isinstance(collection.get("skill_files"), int) and collection["skill_files"] != skill_collections[name]:
                errors.append(
                    f"catalog/search-index.json collections[{i}].skill_files is "
                    f"{collection['skill_files']}, but skills contain {skill_collections[name]}"
                )
            if (
                isinstance(collection.get("unique_skills"), int)
                and isinstance(collection.get("skill_files"), int)
                and collection["unique_skills"] > collection["skill_files"]
            ):
                errors.append(
                    f"catalog/search-index.json collections[{i}].unique_skills cannot exceed skill_files"
                )

    if isinstance(totals, dict):
        expected_totals = {
            "skill_files": len(skills),
            "collections": len(collection_names),
            "templates": flag_counts["template"],
            "no_frontmatter": flag_counts["no-fm"],
            "rebundled": flag_counts["dup"],
            "name_collisions": len(colliding_names),
        }
        for key, expected in expected_totals.items():
            if isinstance(totals.get(key), int) and totals[key] != expected:
                errors.append(
                    f"catalog/search-index.json totals.{key} is {totals[key]}, but expected {expected}"
                )
        if (
            isinstance(totals.get("unique_skills"), int)
            and isinstance(totals.get("skill_files"), int)
            and totals["unique_skills"] > totals["skill_files"]
        ):
            errors.append("catalog/search-index.json totals.unique_skills cannot exceed totals.skill_files")
    return errors


def check_collisions_payload(payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["catalog/collisions.json must contain a JSON object"]
    if payload.get("generated_by") != "tools/build_index.py":
        errors.append("catalog/collisions.json generated_by must be tools/build_index.py")
    if not isinstance(payload.get("count"), int):
        errors.append("catalog/collisions.json count must be an integer")
    collisions = payload.get("collisions")
    if not isinstance(collisions, list):
        errors.append("catalog/collisions.json collisions must be a list")
        return errors
    if isinstance(payload.get("count"), int) and payload["count"] != len(collisions):
        errors.append(
            f"catalog/collisions.json count is {payload['count']}, but contains {len(collisions)} groups"
        )
    group_names: list[str] = []
    for i, group in enumerate(collisions):
        if not isinstance(group, dict):
            errors.append(f"catalog/collisions.json collisions[{i}] must be an object")
            continue
        for key in ("name", "collections", "distinct_bodies", "total_copies", "variants"):
            if key not in group:
                errors.append(f"catalog/collisions.json collisions[{i}] missing key: {key}")
        name = group.get("name")
        if isinstance(name, str) and name:
            group_names.append(name.lower())
        else:
            errors.append(f"catalog/collisions.json collisions[{i}].name must be a non-empty string")
        for key in ("collections", "distinct_bodies", "total_copies"):
            if key in group and not isinstance(group.get(key), int):
                errors.append(f"catalog/collisions.json collisions[{i}].{key} must be an integer")
        if isinstance(group.get("collections"), int) and group["collections"] < 2:
            errors.append(f"catalog/collisions.json collisions[{i}].collections must be at least 2")
        if isinstance(group.get("distinct_bodies"), int) and group["distinct_bodies"] < 2:
            errors.append(f"catalog/collisions.json collisions[{i}].distinct_bodies must be at least 2")
        variants = group.get("variants", [])
        if not isinstance(variants, list) or not variants:
            errors.append(f"catalog/collisions.json collisions[{i}].variants must be a non-empty list")
            continue
        variant_collections: list[str] = []
        bodies_total = 0
        for j, variant in enumerate(variants):
            if not isinstance(variant, dict):
                errors.append(f"catalog/collisions.json collisions[{i}].variants[{j}] must be an object")
                continue
            missing = {"collection", "trigger", "path", "bodies_in_collection"} - set(variant)
            if missing:
                errors.append(
                    "catalog/collisions.json "
                    f"collisions[{i}].variants[{j}] missing keys: {', '.join(sorted(missing))}"
                )
                continue
            for key in ("collection", "trigger", "path"):
                if not isinstance(variant.get(key), str) or not variant.get(key):
                    errors.append(
                        "catalog/collisions.json "
                        f"collisions[{i}].variants[{j}].{key} must be a non-empty string"
                    )
            collection = variant.get("collection")
            if isinstance(collection, str):
                variant_collections.append(collection)
            path = variant.get("path")
            if isinstance(collection, str) and isinstance(path, str) and not path.startswith(f"skills/{collection}/"):
                errors.append(
                    "catalog/collisions.json "
                    f"collisions[{i}].variants[{j}].path is outside collection: {path}"
                )
            if not isinstance(variant.get("bodies_in_collection"), int):
                errors.append(
                    "catalog/collisions.json "
                    f"collisions[{i}].variants[{j}].bodies_in_collection must be an integer"
                )
            elif variant["bodies_in_collection"] < 1:
                errors.append(
                    "catalog/collisions.json "
                    f"collisions[{i}].variants[{j}].bodies_in_collection must be positive"
                )
            else:
                bodies_total += variant["bodies_in_collection"]
            repo_url = variant.get("repo_url", "")
            if repo_url:
                if not isinstance(repo_url, str):
                    errors.append(
                        "catalog/collisions.json "
                        f"collisions[{i}].variants[{j}].repo_url must be a string"
                    )
                elif not is_http_url(repo_url):
                    errors.append(
                        "catalog/collisions.json "
                        f"collisions[{i}].variants[{j}].repo_url must be an HTTP(S) URL"
                    )
        if isinstance(group.get("collections"), int) and group["collections"] != len(set(variant_collections)):
            errors.append(
                f"catalog/collisions.json collisions[{i}].collections is "
                f"{group['collections']}, but variants cover {len(set(variant_collections))} collections"
            )
        duplicate_variant_collections = sorted(
            collection
            for collection, count in Counter(variant_collections).items()
            if count > 1
        )
        if duplicate_variant_collections:
            errors.append(
                f"catalog/collisions.json collisions[{i}] has duplicate variant collections: "
                + ", ".join(duplicate_variant_collections[:5])
            )
        if isinstance(group.get("total_copies"), int) and bodies_total and group["total_copies"] < bodies_total:
            errors.append(
                f"catalog/collisions.json collisions[{i}].total_copies is "
                f"{group['total_copies']}, but variants contain at least {bodies_total} bodies"
            )
        if (
            isinstance(group.get("distinct_bodies"), int)
            and isinstance(group.get("total_copies"), int)
            and group["distinct_bodies"] > group["total_copies"]
        ):
            errors.append(f"catalog/collisions.json collisions[{i}].distinct_bodies cannot exceed total_copies")
    duplicates = sorted(name for name, count in Counter(group_names).items() if count > 1)
    if duplicates:
        errors.append(f"catalog/collisions.json contains duplicate collision names: {', '.join(duplicates)}")
    return errors


def check_cross_payloads(index_payload: object, collisions_payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(index_payload, dict) or not isinstance(collisions_payload, dict):
        return errors

    totals = index_payload.get("totals")
    collisions = collisions_payload.get("collisions")
    if not isinstance(totals, dict) or not isinstance(collisions, list):
        return errors

    declared_count = collisions_payload.get("count")
    indexed_count = totals.get("name_collisions")
    if isinstance(declared_count, int) and isinstance(indexed_count, int) and declared_count != indexed_count:
        errors.append(
            "catalog collision count mismatch: "
            f"search-index.json totals.name_collisions is {indexed_count}, "
            f"but collisions.json count is {declared_count}"
        )

    skills = index_payload.get("skills")
    if not isinstance(skills, list):
        return errors

    index_names = {
        skill["name"].lower()
        for skill in skills
        if isinstance(skill, dict)
        and isinstance(skill.get("name"), str)
        and isinstance(skill.get("flags"), list)
        and "collision" in skill["flags"]
    }
    collision_names = {
        group["name"].lower()
        for group in collisions
        if isinstance(group, dict) and isinstance(group.get("name"), str)
    }
    missing = sorted(collision_names - index_names)
    stale = sorted(index_names - collision_names)
    if missing:
        errors.append(
            "catalog/collisions.json names missing from search-index collision flags: "
            + ", ".join(missing[:10])
        )
    if stale:
        errors.append(
            "search-index collision flags missing from catalog/collisions.json: "
            + ", ".join(stale[:10])
        )
    return errors


def check_local_assets(html: str, html_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    for asset in linked_assets(html):
        parsed = urlsplit(asset)
        if parsed.scheme or parsed.netloc:
            continue
        path_part = unquote(parsed.path)
        if not path_part:
            continue
        if path_part.startswith("/"):
            asset_path = (repo_root / path_part.lstrip("/")).resolve()
        else:
            asset_path = (html_path.parent / path_part).resolve()
        try:
            asset_path.relative_to(repo_root)
        except ValueError:
            errors.append(f"site asset escapes repo root: {asset}")
            continue
        if not asset_path.exists():
            errors.append(f"site asset not found: {asset}")
    return errors


def check_local_css_assets(css: str, css_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    for asset in css_assets(css):
        parsed = urlsplit(asset)
        if parsed.scheme or parsed.netloc:
            continue
        path_part = unquote(parsed.path)
        if not path_part:
            continue
        if path_part.startswith("/"):
            asset_path = (repo_root / path_part.lstrip("/")).resolve()
        else:
            asset_path = (css_path.parent / path_part).resolve()
        try:
            asset_path.relative_to(repo_root)
        except ValueError:
            errors.append(f"site CSS asset escapes repo root: {asset}")
            continue
        if not asset_path.exists():
            errors.append(f"site CSS asset not found: {asset}")
    return errors


def main() -> int:
    errors: list[str] = []
    repo_root = ROOT.resolve()
    html_path = SITE / "index.html"
    collisions_html_path = SITE / "collisions.html"
    css_path = SITE / "styles.css"
    js_path = SITE / "app.js"
    collisions_js_path = SITE / "collisions.js"
    for path in (html_path, collisions_html_path, css_path, js_path, collisions_js_path, INDEX, COLLISIONS):
        if not path.exists():
            errors.append(f"missing {path.relative_to(ROOT)}")

    if not errors:
        html = read(html_path)
        collisions_html = read(collisions_html_path)
        css = read(css_path)
        errors.extend(
            check_html_contract(
                html,
                REQUIRED_INDEX_IDS,
                "site/index.html",
                require_noscript=True,
            )
        )
        errors.extend(
            check_html_contract(
                collisions_html,
                REQUIRED_COLLISIONS_IDS,
                "site/collisions.html",
            )
        )
        errors.extend(check_local_assets(html, html_path, repo_root))
        errors.extend(check_local_assets(collisions_html, collisions_html_path, repo_root))
        errors.extend(check_local_css_assets(css, css_path, repo_root))

        js = read(js_path)
        if "../catalog/search-index.json" not in js:
            errors.append("site/app.js must fetch ../catalog/search-index.json")
        collisions_js = read(collisions_js_path)
        if "../catalog/collisions.json" not in collisions_js:
            errors.append("site/collisions.js must fetch ../catalog/collisions.json")

        payload: object | None = None
        collisions_payload: object | None = None
        try:
            payload = json.loads(read(INDEX))
        except json.JSONDecodeError as exc:
            errors.append(f"cannot parse catalog/search-index.json: {exc}")
        else:
            errors.extend(check_index_payload(payload))
        try:
            collisions_payload = json.loads(read(COLLISIONS))
        except json.JSONDecodeError as exc:
            errors.append(f"cannot parse catalog/collisions.json: {exc}")
        else:
            errors.extend(check_collisions_payload(collisions_payload))
        if payload is not None and collisions_payload is not None:
            errors.extend(check_cross_payloads(payload, collisions_payload))

    if errors:
        for message in errors:
            error(message)
        return 1
    print("OK: static discovery site assets and search index contract are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
