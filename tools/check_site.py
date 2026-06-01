#!/usr/bin/env python3
"""Validate the static discovery site and its data contract."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

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


def error(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def linked_assets(html: str) -> set[str]:
    values: set[str] = set()
    values.update(re.findall(r'<link[^>]+href="([^"]+)"', html))
    values.update(re.findall(r'<script[^>]+src="([^"]+)"', html))
    values.update(re.findall(r'<img[^>]+src="([^"]+)"', html))
    return values


def element_ids(html: str) -> set[str]:
    return set(re.findall(r'\bid="([^"]+)"', html))


def check_html_contract(
    html: str,
    required_ids: set[str],
    label: str,
    require_noscript: bool = False,
) -> list[str]:
    errors: list[str] = []
    ids = re.findall(r'\bid="([^"]+)"', html)
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
    for key in ("totals", "tags", "collections", "skills"):
        if key not in payload:
            errors.append(f"catalog/search-index.json missing key: {key}")
    totals = payload.get("totals", {})
    if not isinstance(totals, dict):
        errors.append("catalog/search-index.json totals must be an object")
    else:
        for key in ("skill_files", "unique_skills", "collections", "name_collisions"):
            if not isinstance(totals.get(key), int):
                errors.append(f"catalog/search-index.json totals.{key} must be an integer")

    skills = payload.get("skills", [])
    if not isinstance(skills, list) or not skills:
        errors.append("catalog/search-index.json skills must be a non-empty list")
        return errors
    required = {"name", "collection", "trigger", "path"}
    for i, skill in enumerate(skills[:50]):
        if not isinstance(skill, dict):
            errors.append(f"catalog/search-index.json skills[{i}] must be an object")
            continue
        missing = sorted(required - set(skill))
        if missing:
            errors.append(
                f"catalog/search-index.json skills[{i}] missing keys: {', '.join(missing)}"
            )
    return errors


def check_collisions_payload(payload: object) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["catalog/collisions.json must contain a JSON object"]
    if not isinstance(payload.get("count"), int):
        errors.append("catalog/collisions.json count must be an integer")
    collisions = payload.get("collisions")
    if not isinstance(collisions, list):
        errors.append("catalog/collisions.json collisions must be a list")
        return errors
    for i, group in enumerate(collisions[:50]):
        if not isinstance(group, dict):
            errors.append(f"catalog/collisions.json collisions[{i}] must be an object")
            continue
        for key in ("name", "collections", "distinct_bodies", "variants"):
            if key not in group:
                errors.append(f"catalog/collisions.json collisions[{i}] missing key: {key}")
        variants = group.get("variants", [])
        if not isinstance(variants, list) or not variants:
            errors.append(f"catalog/collisions.json collisions[{i}].variants must be a non-empty list")
            continue
        for j, variant in enumerate(variants[:10]):
            if not isinstance(variant, dict):
                errors.append(f"catalog/collisions.json collisions[{i}].variants[{j}] must be an object")
                continue
            missing = {"collection", "trigger", "path"} - set(variant)
            if missing:
                errors.append(
                    "catalog/collisions.json "
                    f"collisions[{i}].variants[{j}] missing keys: {', '.join(sorted(missing))}"
                )
    return errors


def check_local_assets(html: str, html_path: Path, repo_root: Path) -> list[str]:
    errors: list[str] = []
    for asset in linked_assets(html):
        if asset.startswith(("http://", "https://")):
            continue
        asset_path = (html_path.parent / asset).resolve()
        try:
            asset_path.relative_to(repo_root)
        except ValueError:
            errors.append(f"site asset escapes repo root: {asset}")
            continue
        if not asset_path.exists():
            errors.append(f"site asset not found: {asset}")
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

        js = read(js_path)
        if "../catalog/search-index.json" not in js:
            errors.append("site/app.js must fetch ../catalog/search-index.json")
        collisions_js = read(collisions_js_path)
        if "../catalog/collisions.json" not in collisions_js:
            errors.append("site/collisions.js must fetch ../catalog/collisions.json")

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

    if errors:
        for message in errors:
            error(message)
        return 1
    print("OK: static discovery site assets and search index contract are valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
