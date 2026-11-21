#!/usr/bin/env python3
"""Workspace tool for the Free-Research-Crew protocol (v0.2).

A crew workspace is a directory of plain files that research-assistant agents
hand off through. This tool creates one, records runs, moves gates, renders
paper numbers from the run ledger, and validates that every claim in the paper
traces to a logged run or a verified source.

Standard library only, so it runs anywhere Python 3.9+ does.
See crew/PROTOCOL.md for the file formats.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROTOCOL_VERSION = "0.2"
# 0.1 workspaces (the first gallery papers) still validate; rules added in 0.2 are
# errors for 0.2 workspaces and warnings for 0.1 ones.
SUPPORTED_PROTOCOLS = ("0.1", "0.2")
TRACKS = ("cs", "social-science")
GATES = ("question", "design", "results", "submission")
GATE_STATUSES = ("pending", "requested", "approved", "rejected")
TASK_STATUSES = ("todo", "doing", "done", "blocked")
RUN_KINDS = ("data-prep", "analysis")
CLAIM_KINDS = ("result", "citation")
ROLES = (
    "pi", "scout", "designer", "data-ra", "experimenter", "econometrician",
    "writer", "figures-ra", "reviewer", "replicator",
)
REVIEW_TARGETS = ("question", "literature", "design", "code", "results", "paper")
GATE_REVIEW = {"question": "question", "design": "design", "results": "results", "submission": "paper"}
VERDICTS = ("block", "revise", "pass")
SEVERITIES = ("critical", "major", "minor")
FINDING_STATUSES = ("open", "resolved", "conceded", "withdrawn")
INDEPENDENCE = ("cross-family", "fresh-context")
MAX_REVIEW_ROUNDS = 4
ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
MACRO_RE = re.compile(r"^[A-Za-z]+$")
BIB_KEY_RE = re.compile(r"@\s*(\w+)\s*\{\s*([^,\s]+)\s*,")
CITE_RE = re.compile(r"\\[A-Za-z]*cite[A-Za-z]*\*?(?:\[[^\]]*\])*\{([^}]*)\}")
TEX_COMMENT_RE = re.compile(r"(?<!\\)%.*")
TEMP_PREFIXES = tuple(sorted({"/tmp/", "/private/tmp/", "/var/folders/", "/private/var/folders/",
                              tempfile.gettempdir().rstrip("/") + "/"}))
GENERATED_TEX = ("numbers.tex", "process.tex")
SOURCE_METHODS = ("fetched-fulltext", "fetched-abstract", "doi-resolved")


# ---------------------------------------------------------------- helpers

def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(value: object) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_log(ws: Path, role: str, action: str, detail: str = "") -> None:
    entry = {"time": now(), "role": role, "action": action, "detail": detail}
    with (ws / "log.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(entry, ensure_ascii=False) + "\n")


def inside(ws: Path, value: str) -> Path | None:
    """Resolve a workspace-relative path; None if it escapes the workspace."""
    if not isinstance(value, str) or not value or Path(value).is_absolute():
        return None
    target = (ws / value).resolve()
    try:
        target.relative_to(ws.resolve())
    except ValueError:
        return None
    return target


def read_claims(ws: Path) -> tuple[list[dict], list[str]]:
    claims, errors = [], []
    path = ws / "claims.jsonl"
    if not path.exists():
        return claims, errors
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"claims.jsonl:{number}: not valid JSON ({exc.msg})")
            continue
        if not isinstance(item, dict):
            errors.append(f"claims.jsonl:{number}: expected an object")
            continue
        item["_line"] = number
        claims.append(item)
    return claims, errors


def read_runs(ws: Path) -> tuple[dict[str, dict], list[str]]:
    runs, errors = {}, []
    root = ws / "runs"
    if not root.is_dir():
        return runs, errors
    for directory in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith(".")):
        record = directory / "run.json"
        if not record.exists():
            errors.append(f"runs/{directory.name}: missing run.json")
            continue
        try:
            data = read_json(record)
        except json.JSONDecodeError as exc:
            errors.append(f"runs/{directory.name}/run.json: not valid JSON ({exc.msg})")
            continue
        if not isinstance(data, dict):
            errors.append(f"runs/{directory.name}/run.json: expected an object")
            continue
        runs[directory.name] = data
    return runs, errors


def read_reviews(ws: Path) -> tuple[dict[str, dict], list[str]]:
    reviews, errors = {}, []
    root = ws / "reviews"
    if not root.is_dir():
        return reviews, errors
    for directory in sorted(p for p in root.iterdir() if p.is_dir()):
        record = directory / "review.json"
        if not record.exists():
            errors.append(f"reviews/{directory.name}: missing review.json")
            continue
        try:
            data = read_json(record)
        except json.JSONDecodeError as exc:
            errors.append(f"reviews/{directory.name}/review.json: not valid JSON ({exc.msg})")
            continue
        if not isinstance(data, dict):
            errors.append(f"reviews/{directory.name}/review.json: expected an object")
            continue
        reviews[directory.name] = data
    return reviews, errors


def open_critical(review: dict) -> list[str]:
    return [
        str(f.get("id")) for f in review.get("findings") or []
        if isinstance(f, dict) and f.get("severity") == "critical" and f.get("status") == "open"
    ]


def latest_reviews(reviews: dict[str, dict], before: datetime | None = None) -> dict[str, dict]:
    """Target -> the highest-round review of it (optionally created no later than `before`)."""
    latest: dict[str, dict] = {}
    for review in reviews.values():
        target, number = review.get("target"), review.get("round")
        if target not in REVIEW_TARGETS or not isinstance(number, int):
            continue
        created = parse_time(review.get("created"))
        if before is not None and (created is None or created > before):
            continue
        if target not in latest or number > latest[target]["round"]:
            latest[target] = review
    return latest


def bib_keys(ws: Path) -> set[str]:
    path = ws / "refs.bib"
    if not path.exists():
        return set()
    return {
        key for kind, key in BIB_KEY_RE.findall(path.read_text(encoding="utf-8"))
        if kind.lower() not in ("comment", "string", "preamble")
    }


def cited_keys(ws: Path) -> dict[str, str]:
    """Citation key -> first .tex file that cites it."""
    found: dict[str, str] = {}
    paper = ws / "paper"
    if not paper.is_dir():
        return found
    for tex in sorted(paper.rglob("*.tex")):
        text = TEX_COMMENT_RE.sub("", tex.read_text(encoding="utf-8", errors="replace"))
        for group in CITE_RE.findall(text):
            for key in group.split(","):
                key = key.strip()
                if key:
                    found.setdefault(key, str(tex.relative_to(ws)))
    return found


def format_value(value: float, spec: str) -> str:
    return format(value, spec or "g")


def render_numbers(claims: list[dict]) -> str:
    lines = [
        "% Generated by `crew.py numbers` from claims.jsonl. Do not edit by hand.",
        "% Each macro is a number taken from a logged run; see claims.jsonl.",
    ]
    for claim in claims:
        macro = claim.get("macro")
        if not macro or claim.get("kind") != "result" or "value" not in claim:
            continue
        try:
            text = format_value(claim["value"], claim.get("format", ""))
        except (TypeError, ValueError):
            continue
        lines.append(f"\\newcommand{{\\{macro}}}{{{text}}}  % {claim.get('id', '?')}")
    return "\n".join(lines) + "\n"


def temp_paths(command: list) -> list[str]:
    """Arguments of a command that point into a temporary directory outside the workspace."""
    found = []
    for token in command[1:]:
        for part in re.split(r"[\s=:,]", str(token)):
            if part.startswith(TEMP_PREFIXES) or part in ("/tmp", "/private/tmp"):
                found.append(part)
    return found


def tex_files(ws: Path, generated: set[str]) -> list[Path]:
    paper = ws / "paper"
    if not paper.is_dir():
        return []
    return [p for p in sorted(paper.rglob("*.tex"))
            if p.name not in GENERATED_TEX and rel(ws, p.resolve()) not in generated]


def hand_typed_numbers(ws: Path, claims: list[dict], runs: dict[str, dict]) -> list[str]:
    """Places where the paper types out a claim's number instead of using its macro.

    Only values with a decimal point and at least three significant digits are matched, and
    files a run produced (generated tables) are skipped, so a hit is almost surely a copy.
    A line marked `% crew:literal` is skipped: a published value quoted next to its
    replication can equal the replicated number.
    """
    values: dict[str, str] = {}
    for claim in claims:
        macro = claim.get("macro")
        if not macro or claim.get("kind") != "result" or "value" not in claim:
            continue
        try:
            text = format_value(claim["value"], claim.get("format", "")).lstrip("+-")
        except (TypeError, ValueError):
            continue
        if "." in text and len(text.replace(".", "").lstrip("0")) >= 3:
            values.setdefault(text, macro)
    if not values:
        return []
    generated = set()
    for run in runs.values():
        for item in run.get("outputs") or []:
            target = inside(ws, str(item.get("path", ""))) if isinstance(item, dict) else None
            if target is not None:
                generated.add(rel(ws, target))
    pattern = re.compile(r"(?<![\d.])(" + "|".join(map(re.escape, sorted(values, key=len, reverse=True)))
                         + r")(?![\d])")
    found = []
    for path in tex_files(ws, generated):
        for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            if "crew:literal" in line:
                continue
            line = TEX_COMMENT_RE.sub("", line)
            if "\\newcommand" in line:
                continue
            for match in pattern.finditer(line):
                found.append(f"{path.relative_to(ws)}:{number}: {match.group(1)} is the value of "
                             f"\\{values[match.group(1)]}; use the macro, not a typed number")
    return found


def stale_paper_inputs(ws: Path) -> list[str]:
    """Paper sources newer than paper/main.pdf."""
    pdf = ws / "paper" / "main.pdf"
    if not pdf.exists():
        return []
    built = pdf.stat().st_mtime
    inputs = [p for p in (ws / "paper").rglob("*") if p.suffix in (".tex", ".bib", ".pdf", ".png") and p != pdf]
    inputs += [ws / "refs.bib"]
    return sorted(str(p.relative_to(ws)) for p in inputs if p.is_file() and p.stat().st_mtime > built)


def latex_text(value: object) -> str:
    text = str(value).replace("\\", "/")
    for char in ("&", "%", "$", "#", "_", "{", "}"):
        text = text.replace(char, "\\" + char)
    return text


def process_facts(ws: Path) -> list[tuple[str, object, str]]:
    """Facts about how the paper was made, taken from the ledger rather than typed by a writer."""
    reviews, _ = read_reviews(ws)
    runs, _ = read_runs(ws)
    claims, _ = read_claims(ws)
    facts: list[tuple[str, object, str]] = []
    rounds = {target: 0 for target in REVIEW_TARGETS}
    severity = {name: 0 for name in SEVERITIES}
    models, independence = set(), set()
    distinct: dict[tuple[str, str], str] = {}  # (target, finding id) -> severity in its latest round
    ordered = sorted(reviews.values(), key=lambda r: r.get("round") if isinstance(r.get("round"), int) else 0)
    for review in ordered:
        target = review.get("target")
        if target in rounds and isinstance(review.get("round"), int):
            rounds[target] = max(rounds[target], review["round"])
        for finding in review.get("findings") or []:
            if isinstance(finding, dict) and finding.get("severity") in severity:
                # a finding carried into later rounds keeps its id; count it once
                distinct[(str(target), str(finding.get("id") or id(finding)))] = finding["severity"]
    for value in distinct.values():
        severity[value] += 1
        reviewer = review.get("reviewer") if isinstance(review.get("reviewer"), dict) else {}
        if reviewer.get("model"):
            models.add(str(reviewer["model"]))
        if reviewer.get("independence"):
            independence.add(str(reviewer["independence"]))
    facts.append(("CrewReviewRounds", len(reviews), "review records in reviews/"))
    for target in REVIEW_TARGETS:
        facts.append((f"CrewRounds{target.capitalize()}", rounds[target], f"rounds of the {target} review"))
    for name in SEVERITIES:
        facts.append((f"CrewFindings{name.capitalize()}", severity[name], f"distinct {name} findings raised (a finding carried across rounds counts once, at its latest severity)"))
    facts.append(("CrewReviewerModels", ", ".join(sorted(models)) or "none", "models the Reviewer ran on"))
    facts.append(("CrewReviewIndependence", ", ".join(sorted(independence)) or "none", "how independent the reviews were"))
    analysis = [r for r in runs.values() if r.get("kind") == "analysis"]
    superseded = ws / "runs" / ".superseded"
    facts.append(("CrewRuns", len(runs), "runs in the ledger"))
    facts.append(("CrewRunsAnalysis", len(analysis), "analysis runs"))
    facts.append(("CrewRunsDataPrep", len(runs) - len(analysis), "data-prep runs"))
    facts.append(("CrewRunsSuperseded", sum(1 for d in superseded.iterdir() if d.is_dir()) if superseded.is_dir() else 0,
                  "runs replaced by a later run with the same id (archived)"))
    facts.append(("CrewRunsUnreviewed", sum(1 for r in analysis if r.get("unreviewed")),
                  "analysis runs not covered by a passing code review"))
    facts.append(("CrewResultClaims", sum(1 for c in claims if c.get("kind") == "result"), "result claims"))
    facts.append(("CrewCitationClaims", sum(1 for c in claims if c.get("kind") == "citation"), "citation claims"))
    report = {}
    if (ws / "replication.json").exists():
        try:
            loaded = read_json(ws / "replication.json")
            report = loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError:
            report = {}
    entries = [e for e in report.get("runs") or [] if isinstance(e, dict)]
    facts.append(("CrewRerunReproduced", sum(1 for e in entries if e.get("status") in ("match", "ran")),
                  "runs the clean rerun reproduced"))
    facts.append(("CrewRerunTotal", len(entries), "runs the clean rerun re-executed"))
    status = "not run" if not report else ("passed" if report.get("passed") is True else "failed")
    facts.append(("CrewRerunStatus", status, "outcome of the latest clean rerun"))
    return facts


def render_process(ws: Path) -> str:
    lines = [
        "% Generated by `crew.py numbers` from reviews/, runs/ and replication.json. Do not edit by hand.",
        "% Use these macros for any statement about how the paper was made (rounds, runs, rerun).",
    ]
    for macro, value, comment in process_facts(ws):
        lines.append(f"\\newcommand{{\\{macro}}}{{{latex_text(value)}}}  % {comment}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- validate

def validate(ws: Path, strict: bool = False) -> tuple[list[str], list[str]]:
    """Return (errors, warnings). `strict` turns missing files into errors."""
    errors: list[str] = []
    warnings: list[str] = []
    soft = errors if strict else warnings

    # crew.json
    meta: dict = {}
    try:
        loaded = read_json(ws / "crew.json")
        meta = loaded if isinstance(loaded, dict) else {}
        if not meta:
            errors.append("crew.json: expected an object")
    except FileNotFoundError:
        return [f"{ws}: not a crew workspace (crew.json missing)"], warnings
    except json.JSONDecodeError as exc:
        errors.append(f"crew.json: not valid JSON ({exc.msg})")
    if meta:
        if meta.get("protocol") not in SUPPORTED_PROTOCOLS:
            errors.append(f"crew.json: protocol must be one of {', '.join(SUPPORTED_PROTOCOLS)}")
        if meta.get("track") not in TRACKS:
            errors.append(f"crew.json: track must be one of {', '.join(TRACKS)}")
        if not meta.get("title"):
            errors.append("crew.json: title is empty")

    # rules added in protocol 0.2: errors for new workspaces, warnings for older ones
    rule = warnings if meta.get("protocol") == "0.1" else errors

    # plan.json
    plan: dict = {}
    try:
        loaded = read_json(ws / "plan.json")
        plan = loaded if isinstance(loaded, dict) else {}
        if not plan:
            errors.append("plan.json: expected an object")
    except FileNotFoundError:
        errors.append("plan.json: missing")
    except json.JSONDecodeError as exc:
        errors.append(f"plan.json: not valid JSON ({exc.msg})")

    gates = plan.get("gates") if isinstance(plan.get("gates"), dict) else {}
    approved_at: dict[str, datetime] = {}
    previous_ok = True
    for name in GATES:
        gate = gates.get(name)
        if not isinstance(gate, dict):
            if plan:
                errors.append(f"plan.json: gates.{name} missing")
            previous_ok = False
            continue
        status = gate.get("status")
        if status not in GATE_STATUSES:
            errors.append(f"plan.json: gates.{name}.status must be one of {', '.join(GATE_STATUSES)}")
        if status == "approved":
            when = parse_time(gate.get("decided_on"))
            if not gate.get("decided_by"):
                errors.append(f"plan.json: gates.{name} approved without decided_by (a human name)")
            if when is None:
                errors.append(f"plan.json: gates.{name} approved without a valid decided_on time")
            else:
                approved_at[name] = when
            if not previous_ok:
                errors.append(f"plan.json: gates.{name} approved before an earlier gate")
        else:
            previous_ok = False

    if "question" in approved_at:
        if not str(plan.get("question", "")).strip():
            errors.append("plan.json: question gate approved but question is empty")
        if not plan.get("hypotheses"):
            errors.append("plan.json: question gate approved but hypotheses is empty")
    if "design" in approved_at:
        design = plan.get("design") if isinstance(plan.get("design"), dict) else {}
        for field in ("summary", "method", "analysis_plan"):
            if not design.get(field):
                errors.append(f"plan.json: design gate approved but design.{field} is empty")

    task_ids: set[str] = set()
    for index, task in enumerate(plan.get("tasks") or []):
        label = f"plan.json: tasks[{index}]"
        if not isinstance(task, dict):
            errors.append(f"{label}: expected an object")
            continue
        task_id = task.get("id")
        if not isinstance(task_id, str) or not ID_RE.match(task_id):
            errors.append(f"{label}: id missing or malformed")
        elif task_id in task_ids:
            errors.append(f"{label}: duplicate id {task_id!r}")
        else:
            task_ids.add(task_id)
        if task.get("owner") not in ROLES:
            errors.append(f"{label}: owner must be a crew role")
        if task.get("status") not in TASK_STATUSES:
            errors.append(f"{label}: status must be one of {', '.join(TASK_STATUSES)}")

    # sources: every bibliography entry must have a verification record
    keys = bib_keys(ws)
    sources: dict = {}
    sources_path = ws / "sources" / "sources.json"
    if sources_path.exists():
        try:
            loaded = read_json(sources_path)
            sources = loaded if isinstance(loaded, dict) else {}
        except json.JSONDecodeError as exc:
            errors.append(f"sources/sources.json: not valid JSON ({exc.msg})")
    verified: set[str] = set()
    for key in sorted(keys):
        record = sources.get(key)
        if not isinstance(record, dict):
            errors.append(f"refs.bib: {key} has no verification record in sources/sources.json")
            continue
        missing = [f for f in ("verified_on", "verified_by", "method") if not record.get(f)]
        if not (record.get("url") or record.get("doi")):
            missing.append("url or doi")
        if missing:
            errors.append(f"sources/sources.json: {key} is missing {', '.join(missing)}")
        else:
            verified.add(key)
            if record["method"] not in SOURCE_METHODS:
                rule.append(f"sources/sources.json: {key} has method {record['method']!r}; "
                            f"use one of {', '.join(SOURCE_METHODS)}")
    for key in sorted(set(sources) - keys):
        warnings.append(f"sources/sources.json: {key} is not in refs.bib")
    for key, where in sorted(cited_keys(ws).items()):
        if key not in keys:
            errors.append(f"{where}: cites {key}, which is not in refs.bib")

    # data manifest
    manifest_path = ws / "data" / "manifest.json"
    dataset_ids: set[str] = set()
    if manifest_path.exists():
        try:
            manifest = read_json(manifest_path)
        except json.JSONDecodeError as exc:
            manifest = {}
            errors.append(f"data/manifest.json: not valid JSON ({exc.msg})")
        datasets = manifest.get("datasets") if isinstance(manifest, dict) else None
        for index, item in enumerate(datasets or []):
            label = f"data/manifest.json: datasets[{index}]"
            if not isinstance(item, dict):
                errors.append(f"{label}: expected an object")
                continue
            for field in ("id", "origin", "license", "path", "sha256", "retrieved_on"):
                if not item.get(field):
                    errors.append(f"{label}: {field} is empty")
            dataset_ids.add(str(item.get("id")))
            target = inside(ws, item.get("path", ""))
            if target is None:
                errors.append(f"{label}: path must be relative and inside the workspace")
            elif not target.exists():
                soft.append(f"{label}: file {item.get('path')} is not present (cannot check its hash)")
            elif item.get("sha256") and sha256(target) != item["sha256"]:
                errors.append(f"{label}: {item.get('path')} does not match the recorded sha256")

    # runs
    runs, run_errors = read_runs(ws)
    errors.extend(run_errors)
    design_time = approved_at.get("design")
    for run_id, run in runs.items():
        label = f"runs/{run_id}/run.json"
        if run.get("id") != run_id:
            errors.append(f"{label}: id does not match its directory name")
        if run.get("role") not in ROLES:
            errors.append(f"{label}: role must be a crew role")
        if run.get("kind") not in RUN_KINDS:
            errors.append(f"{label}: kind must be one of {', '.join(RUN_KINDS)}")
        if not run.get("command"):
            errors.append(f"{label}: command is empty")
        started, finished = parse_time(run.get("started")), parse_time(run.get("finished"))
        if started is None or finished is None:
            errors.append(f"{label}: started/finished must be UTC times like 2026-01-01T00:00:00Z")
        if not isinstance(run.get("metrics", {}), dict):
            errors.append(f"{label}: metrics must be an object")
        if meta.get("protocol") != "0.1" and run.get("kind") == "analysis" \
                and not run.get("code_review") and not run.get("unreviewed"):
            errors.append(f"{label}: analysis run records neither the code review that covered it nor "
                          "an --unreviewed reason; record runs with `crew.py run`")
        temp = temp_paths(run.get("command") or [])
        if temp:
            rule.append(f"{label}: command uses temporary path(s) outside the workspace ({', '.join(temp)}); "
                        "a rerun cannot reproduce them")
        if run.get("kind") == "analysis" and started is not None:
            if design_time is None:
                errors.append(f"{label}: analysis run recorded but the design gate is not approved")
            elif started < design_time:
                errors.append(f"{label}: analysis run started before the design gate was approved")
        for group in ("code", "inputs", "outputs"):
            for item in run.get(group) or []:
                if not isinstance(item, dict) or not item.get("path") or not item.get("sha256"):
                    errors.append(f"{label}: {group} entries need path and sha256")
                    continue
                target = inside(ws, item["path"])
                if target is None:
                    errors.append(f"{label}: {group} path {item['path']!r} is outside the workspace")
                elif not target.exists():
                    soft.append(f"{label}: {group} file {item['path']} is not present")
                elif sha256(target) != item["sha256"]:
                    errors.append(
                        f"{label}: {group} file {item['path']} changed since the run; rerun it"
                    )

    # claims
    claims, claim_errors = read_claims(ws)
    errors.extend(claim_errors)
    claim_ids: set[str] = set()
    macros: set[str] = set()
    for claim in claims:
        label = f"claims.jsonl:{claim['_line']}"
        claim_id = claim.get("id")
        if not isinstance(claim_id, str) or not ID_RE.match(claim_id):
            errors.append(f"{label}: id missing or malformed")
        elif claim_id in claim_ids:
            errors.append(f"{label}: duplicate id {claim_id!r}")
        else:
            claim_ids.add(claim_id)
        if not str(claim.get("text", "")).strip():
            errors.append(f"{label}: text is empty")
        kind = claim.get("kind")
        if kind not in CLAIM_KINDS:
            errors.append(f"{label}: kind must be one of {', '.join(CLAIM_KINDS)}")
            continue
        support = claim.get("support")
        if not isinstance(support, list) or not support:
            errors.append(f"{label}: no support; every claim needs a run or a source")
            continue
        if kind == "citation":
            for item in support:
                key = item.get("source") if isinstance(item, dict) else None
                if key not in keys:
                    errors.append(f"{label}: source {key!r} is not in refs.bib")
                elif key not in verified:
                    errors.append(f"{label}: source {key!r} is not verified")
            continue
        # result claim
        first_metric_value = None
        for position, item in enumerate(support):
            run_id = item.get("run") if isinstance(item, dict) else None
            run = runs.get(run_id)
            if run is None:
                errors.append(f"{label}: run {run_id!r} does not exist")
                continue
            if run.get("exit_code") != 0:
                errors.append(f"{label}: run {run_id!r} did not finish successfully")
            if run.get("kind") != "analysis":
                errors.append(f"{label}: run {run_id!r} is not an analysis run")
            metric = item.get("metric")
            if metric is not None:
                metrics = run.get("metrics") if isinstance(run.get("metrics"), dict) else {}
                if metric not in metrics:
                    errors.append(f"{label}: run {run_id!r} has no metric {metric!r}")
                elif position == 0:
                    first_metric_value = metrics[metric]
        if "value" in claim:
            value = claim["value"]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                errors.append(f"{label}: value must be a number")
            elif first_metric_value is None:
                errors.append(f"{label}: value given but the first support names no metric")
            elif isinstance(first_metric_value, bool) or not isinstance(first_metric_value, (int, float)):
                errors.append(f"{label}: the supporting metric is not a number")
            elif not math.isclose(value, first_metric_value, rel_tol=1e-9, abs_tol=1e-12):
                errors.append(
                    f"{label}: value {value} does not match the run metric {first_metric_value}"
                )
        macro = claim.get("macro")
        if macro is not None:
            if not isinstance(macro, str) or not MACRO_RE.match(macro):
                errors.append(f"{label}: macro must be letters only (a LaTeX command name)")
            elif macro in macros:
                errors.append(f"{label}: duplicate macro {macro!r}")
            else:
                macros.add(macro)
            if "value" not in claim:
                errors.append(f"{label}: macro given without a value")
            else:
                try:
                    format_value(claim["value"], claim.get("format", ""))
                except (TypeError, ValueError):
                    errors.append(f"{label}: format {claim.get('format')!r} is not a valid number format")

    # reviews: the Reviewer criticises every stage; gates need its latest verdict
    reviews, review_errors = read_reviews(ws)
    errors.extend(review_errors)
    rounds_seen: dict[str, set[int]] = {}
    for review_id, review in reviews.items():
        label = f"reviews/{review_id}/review.json"
        if review.get("id") != review_id:
            errors.append(f"{label}: id does not match its directory name")
        target = review.get("target")
        if target not in REVIEW_TARGETS:
            errors.append(f"{label}: target must be one of {', '.join(REVIEW_TARGETS)}")
        number = review.get("round")
        if isinstance(number, bool) or not isinstance(number, int) or number < 1:
            errors.append(f"{label}: round must be a positive integer")
        elif number > MAX_REVIEW_ROUNDS:
            errors.append(f"{label}: round {number} exceeds the limit of {MAX_REVIEW_ROUNDS}; escalate to the human PI")
        elif target in REVIEW_TARGETS:
            if number in rounds_seen.setdefault(target, set()):
                errors.append(f"{label}: duplicate round {number} for target {target!r}")
            rounds_seen[target].add(number)
        created_at = parse_time(review.get("created"))
        if created_at is not None and created_at.timestamp() > datetime.now(timezone.utc).timestamp() + 300:
            errors.append(f"{label}: created {review.get('created')} is in the future")
        if created_at is None:
            errors.append(f"{label}: created must be a UTC time like 2026-01-01T00:00:00Z")
        reviewer = review.get("reviewer") if isinstance(review.get("reviewer"), dict) else {}
        if not reviewer.get("model"):
            errors.append(f"{label}: reviewer.model is empty")
        if reviewer.get("independence") not in INDEPENDENCE:
            errors.append(f"{label}: reviewer.independence must be one of {', '.join(INDEPENDENCE)}")
        if not review.get("files_read"):
            errors.append(f"{label}: files_read is empty; the reviewer must read the artifacts itself")
        if not str(review.get("kill_argument", "")).strip():
            errors.append(f"{label}: kill_argument is empty; every review states the strongest case against")
        verdict = review.get("verdict")
        if verdict not in VERDICTS:
            errors.append(f"{label}: verdict must be one of {', '.join(VERDICTS)}")
        findings = review.get("findings")
        if not isinstance(findings, list):
            errors.append(f"{label}: findings must be a list")
            findings = []
        finding_ids: set[str] = set()
        for index, finding in enumerate(findings):
            where = f"{label}: findings[{index}]"
            if not isinstance(finding, dict):
                errors.append(f"{where}: expected an object")
                continue
            finding_id = finding.get("id")
            if not isinstance(finding_id, str) or not ID_RE.match(finding_id):
                errors.append(f"{where}: id missing or malformed")
            elif finding_id in finding_ids:
                errors.append(f"{where}: duplicate id {finding_id!r}")
            else:
                finding_ids.add(finding_id)
            if finding.get("severity") not in SEVERITIES:
                errors.append(f"{where}: severity must be one of {', '.join(SEVERITIES)}")
            if finding.get("status") not in FINDING_STATUSES:
                errors.append(f"{where}: status must be one of {', '.join(FINDING_STATUSES)}")
            if not str(finding.get("text", "")).strip():
                errors.append(f"{where}: text is empty")
            if not str(finding.get("evidence", "")).strip():
                errors.append(f"{where}: evidence is empty; point to the file and place")
        if verdict == "pass" and open_critical(review):
            errors.append(f"{label}: verdict is pass but critical findings are still open")
    for target, seen in rounds_seen.items():
        missing = sorted(set(range(1, max(seen) + 1)) - seen)
        if missing:
            errors.append(f"reviews: target {target!r} is missing round(s) {', '.join(map(str, missing))}")
    for name, when in approved_at.items():
        target = GATE_REVIEW[name]
        review = latest_reviews(reviews, before=when).get(target)
        if review is None:
            errors.append(f"plan.json: gates.{name} approved without a review of {target!r} by the Reviewer")
            continue
        gate = gates.get(name, {})
        accepted = set(gate.get("accepted_findings") or [])
        remaining = [f for f in open_critical(review) if f not in accepted]
        if remaining:
            errors.append(
                f"plan.json: gates.{name} approved with open critical finding(s) "
                f"{', '.join(remaining)} in reviews/{review.get('id')}"
            )
        if accepted and not str(gate.get("note", "")).strip():
            errors.append(f"plan.json: gates.{name} accepts open findings without a note explaining why")

    # activity log: written only by the tool, so its times can be trusted
    log_path = ws / "log.jsonl"
    if log_path.exists():
        limit = datetime.now(timezone.utc).timestamp() + 300
        for number, line in enumerate(log_path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                errors.append(f"log.jsonl:{number}: not valid JSON; append with `crew.py log`")
                continue
            when = parse_time(entry.get("time")) if isinstance(entry, dict) else None
            if when is None:
                errors.append(f"log.jsonl:{number}: time missing or malformed; append with `crew.py log`")
            elif when.timestamp() > limit:
                errors.append(f"log.jsonl:{number}: time {entry.get('time')} is in the future; "
                              "never write log.jsonl by hand, use `crew.py log`")

    # paper
    numbers_path = ws / "paper" / "numbers.tex"
    if macros:
        if not numbers_path.exists():
            errors.append("paper/numbers.tex: missing; run `crew.py numbers`")
        elif numbers_path.read_text(encoding="utf-8") != render_numbers(claims):
            errors.append("paper/numbers.tex: out of date; run `crew.py numbers`")
    if "results" in approved_at:
        if not any(c.get("kind") == "result" for c in claims):
            errors.append("claims.jsonl: results gate approved but there are no result claims")
    process_path = ws / "paper" / "process.tex"
    process_fresh = process_path.exists() and process_path.read_text(encoding="utf-8") == render_process(ws)
    if process_path.exists() and not process_fresh:
        warnings.append("paper/process.tex: out of date; run `crew.py numbers`")
    typed = hand_typed_numbers(ws, claims, runs)
    open_tasks = [str(t.get("id")) for t in plan.get("tasks") or []
                  if isinstance(t, dict) and t.get("status") in ("todo", "doing")]
    stale_pdf = stale_paper_inputs(ws)
    submitting = "submission" in approved_at
    later = rule if submitting else warnings
    for message in typed:
        later.append(message)
    submission_gate = gates.get("submission") if isinstance(gates.get("submission"), dict) else {}
    if open_tasks and (submitting or submission_gate.get("status") == "requested"):
        later.append(f"plan.json: task(s) {', '.join(open_tasks)} are still todo/doing; "
                     "mark them done or blocked before submission")
    if stale_pdf and not submitting:  # file times are not kept by git, so only checked before approval
        warnings.append(f"paper/main.pdf: older than {', '.join(stale_pdf[:5])}; recompile the paper")
    if submitting and not process_fresh:
        rule.append("paper/process.tex: missing or out of date at submission; run `crew.py numbers` "
                    "and state process facts (rounds, runs, rerun) through its macros")
    if "submission" in approved_at:
        if not (ws / "paper" / "main.pdf").exists():
            errors.append("paper/main.pdf: submission gate approved but the paper is not compiled")
        if not (ws / "paper" / "ai-use.tex").exists():
            errors.append("paper/ai-use.tex: submission gate approved without an AI-use statement")
        errors.extend(check_replication(ws, runs, required=True))
    elif (ws / "replication.json").exists():
        warnings.extend(check_replication(ws, runs, required=False))
    return errors, warnings


def check_replication(ws: Path, runs: dict[str, dict], required: bool) -> list[str]:
    """Problems with replication.json: missing, failed, or older than the run ledger."""
    path = ws / "replication.json"
    if not path.exists():
        return ["replication.json: missing; the Replicator must run `crew.py rerun` before submission"] if required else []
    try:
        report = read_json(path)
    except json.JSONDecodeError as exc:
        return [f"replication.json: not valid JSON ({exc.msg})"]
    if not isinstance(report, dict):
        return ["replication.json: expected an object"]
    problems = []
    if report.get("passed") is not True:
        problems.append("replication.json: the clean rerun did not reproduce every run")
    created = parse_time(report.get("created"))
    latest = max((parse_time(r.get("finished")) for r in runs.values() if parse_time(r.get("finished"))), default=None)
    if created is None:
        problems.append("replication.json: created is not a valid time")
    elif latest is not None and created < latest:
        problems.append("replication.json: older than the latest run; rerun `crew.py rerun`")
    covered = {item.get("run") for item in report.get("runs") or [] if isinstance(item, dict)}
    missing = sorted(set(runs) - covered)
    if missing:
        problems.append(f"replication.json: run(s) {', '.join(missing)} were not rerun")
    for item in report.get("runs") or []:
        if not isinstance(item, dict) or item.get("run") not in runs:
            continue
        recorded = item.get("record_sha256")
        current = sha256(ws / "runs" / str(item["run"]) / "run.json")
        if not recorded:
            problems.append(f"replication.json: run {item['run']} has no record fingerprint; rerun `crew.py rerun`")
        elif recorded != current:
            problems.append(f"replication.json: run {item['run']} was replaced after the rerun; rerun `crew.py rerun`")
    return problems


# ---------------------------------------------------------------- commands

def require_workspace(path: str) -> Path:
    ws = Path(path)
    if not (ws / "crew.json").exists():
        sys.exit(f"ERROR: {ws} is not a crew workspace (crew.json missing)")
    return ws


def cmd_init(args: argparse.Namespace) -> int:
    ws = Path(args.workspace)
    if ws.exists() and any(ws.iterdir()):
        print(f"ERROR: {ws} already exists and is not empty", file=sys.stderr)
        return 1
    for sub in ("sources", "data", "runs", "code", "paper", "reviews", "briefs"):
        (ws / sub).mkdir(parents=True, exist_ok=True)
    meta = {"protocol": PROTOCOL_VERSION, "track": args.track, "title": args.title, "created": now()}
    if args.seed:
        meta["seed"] = args.seed
    write_json(ws / "crew.json", meta)
    write_json(ws / "plan.json", {
        "question": "",
        "hypotheses": [],
        "contribution": "",
        "design": {"summary": "", "method": "", "data": "", "analysis_plan": [], "threats": []},
        "tasks": [],
        "gates": {name: {"status": "pending"} for name in GATES},
    })
    write_json(ws / "sources" / "sources.json", {})
    write_json(ws / "data" / "manifest.json", {"datasets": []})
    (ws / "refs.bib").write_text("", encoding="utf-8")
    (ws / "claims.jsonl").write_text("", encoding="utf-8")
    (ws / ".gitignore").write_text(
        "data/raw/\ndata/derived/\n.venv\n__pycache__/\n"
        "# LaTeX build files the Writer's compile leaves behind\n"
        "paper/*.aux\npaper/*.bbl\npaper/*.blg\npaper/*.fdb_latexmk\npaper/*.fls\npaper/*.log\npaper/*.out\n",
        encoding="utf-8")
    append_log(ws, "pi", "init", f"track={args.track}")
    print(f"Created crew workspace at {ws}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    errors, warnings = validate(Path(args.workspace), strict=args.strict)
    for message in warnings:
        print(f"WARN: {message}")
    for message in errors:
        print(f"ERROR: {message}")
    if errors:
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"OK: workspace is valid ({len(warnings)} warning(s))")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    ws = require_workspace(args.workspace)
    meta, plan = read_json(ws / "crew.json"), read_json(ws / "plan.json")
    runs, _ = read_runs(ws)
    claims, _ = read_claims(ws)
    errors, warnings = validate(ws)
    print(f"{meta.get('title')}  [{meta.get('track')}]")
    print("Gates:")
    for name in GATES:
        gate = plan.get("gates", {}).get(name, {})
        extra = f" by {gate['decided_by']} on {gate['decided_on']}" if gate.get("decided_by") else ""
        print(f"  {name:<11} {gate.get('status', '?')}{extra}")
    tasks = plan.get("tasks") or []
    if tasks:
        print("Tasks:")
        for task in tasks:
            print(f"  [{task.get('status', '?'):<7}] {task.get('id')}  {task.get('owner')}: {task.get('title', '')}")
    results = sum(1 for c in claims if c.get("kind") == "result")
    print(f"Runs: {len(runs)}   Claims: {results} result, {len(claims) - results} citation   "
          f"Sources: {len(bib_keys(ws))}")
    reviews, _ = read_reviews(ws)
    for target, review in latest_reviews(reviews).items():
        findings = [f for f in review.get("findings") or [] if isinstance(f, dict)]
        still_open = sum(1 for f in findings if f.get("status") == "open")
        print(f"Review of {target}: round {review.get('round')}, verdict {review.get('verdict')}, "
              f"{still_open} open finding(s), {len(open_critical(review))} critical")
    print(f"Validation: {len(errors)} error(s), {len(warnings)} warning(s)")
    return 0


def cmd_gate(args: argparse.Namespace) -> int:
    ws = require_workspace(args.workspace)
    plan = read_json(ws / "plan.json")
    gates = plan.setdefault("gates", {})
    gate = gates.setdefault(args.gate, {"status": "pending"})
    before = dict(gate)
    if args.action == "request":
        gate.update({"status": "requested", "requested_on": now(), "summary": args.note or ""})
    else:
        if not args.by:
            print("ERROR: --by <human name> is required to approve or reject a gate", file=sys.stderr)
            return 1
        if args.action == "approve":
            index = GATES.index(args.gate)
            for earlier in GATES[:index]:
                if gates.get(earlier, {}).get("status") != "approved":
                    print(f"ERROR: gate {earlier!r} must be approved first", file=sys.stderr)
                    return 1
        status = "approved" if args.action == "approve" else "rejected"
        gate.update({"status": status, "decided_by": args.by, "decided_on": now(), "note": args.note or ""})
        gate.pop("accepted_findings", None)
        if args.action == "approve" and args.accept_findings:
            gate["accepted_findings"] = [f.strip() for f in args.accept_findings.split(",") if f.strip()]
    write_json(ws / "plan.json", plan)
    if args.action == "approve":
        errors, _ = validate(ws)
        stale = stale_paper_inputs(ws) if args.gate == "submission" else []
        if stale:
            errors.append(f"paper/main.pdf: older than {', '.join(stale[:5])}; recompile the paper")
        if errors:
            gates[args.gate] = before
            write_json(ws / "plan.json", plan)
            for message in errors:
                print(f"ERROR: {message}", file=sys.stderr)
            print(f"ERROR: gate {args.gate!r} not approved; fix the errors above first", file=sys.stderr)
            return 1
    append_log(ws, "pi", f"gate-{args.action}", f"{args.gate} {args.by or ''}".strip())
    print(f"Gate {args.gate}: {gates[args.gate]['status']}")
    return 0


def command_env(ws: Path, command: list[str]) -> dict:
    """Describe the environment a run's command used, not the one crew.py runs in."""
    env = {"crew_python": platform.python_version(), "platform": platform.platform()}
    if not command:
        return env
    exe = command[0]
    resolved = shutil.which(exe, path=str(ws)) if not Path(exe).is_absolute() else exe
    candidate = ws / exe if not Path(exe).is_absolute() else Path(exe)
    if candidate.exists():
        resolved = str(candidate)
    env["command_executable"] = exe
    if Path(exe).name.startswith("python") and resolved:
        try:
            out = subprocess.run([resolved, "-c", "import platform,sys;print(platform.python_version());print(sys.prefix)"],
                                 capture_output=True, text=True, timeout=30, check=False)
            if out.returncode == 0:
                version, prefix = (out.stdout.strip().splitlines() + ["", ""])[:2]
                env["python"] = version
                env["python_prefix"] = prefix
        except (OSError, subprocess.TimeoutExpired):
            pass
    return env


def archive_run(ws: Path, run_dir: Path) -> str:
    """Keep a replaced run's record, logs and metrics: a superseded result must leave a trace."""
    old = read_json(run_dir / "run.json")
    stamp = str(old.get("finished") or now()).replace(":", "").replace("-", "")
    dest = ws / "runs" / ".superseded" / f"{run_dir.name}-{stamp}"
    dest.mkdir(parents=True, exist_ok=True)
    for name in ("run.json", "stdout.log", "stderr.log"):
        if (run_dir / name).exists():
            shutil.copy2(run_dir / name, dest / name)
    metrics_file = old.get("metrics_file")
    target = inside(ws, metrics_file) if metrics_file else None
    if target is not None and target.is_file():
        shutil.copy2(target, dest / "metrics.json")
    return str(dest.relative_to(ws))


def rel(ws: Path, target: Path) -> str:
    """A workspace path in one canonical spelling (no ./, no symlinked prefixes)."""
    return target.relative_to(ws.resolve()).as_posix()


def hash_entries(ws: Path, values: list[str], must_exist: bool) -> list[dict]:
    entries = []
    for value in values:
        target = inside(ws, value)
        if target is None:
            sys.exit(f"ERROR: {value!r} must be a relative path inside the workspace")
        if not target.is_file():
            if must_exist:
                sys.exit(f"ERROR: {value} does not exist")
            continue
        entries.append({"path": rel(ws, target), "sha256": sha256(target)})
    return entries


def code_review_covering(ws: Path, code: list[dict]) -> tuple[str | None, str | None]:
    """(review id, None) when the latest code review passed and read exactly this code."""
    reviews, _ = read_reviews(ws)
    latest = latest_reviews(reviews).get("code")
    if latest is None:
        return None, "no code review exists yet; analysis code is reviewed before it runs"
    review_id = latest.get("id")
    if latest.get("verdict") != "pass":
        return None, f"the latest code review ({review_id}) has verdict {latest.get('verdict')!r}, not pass"
    stamped = latest.get("files_sha256")
    if not isinstance(stamped, dict):
        return None, (f"code review {review_id} was not recorded with `crew.py review`, so the code it "
                      "read is unknown")
    for item in code:
        if item["path"] not in stamped:
            return None, f"{item['path']} was not among the files code review {review_id} read"
        if stamped[item["path"]] != item["sha256"]:
            return None, f"{item['path']} changed after code review {review_id}"
    return str(review_id), None


def review_files(ws: Path, listed: list, unmatched: list | None = None) -> dict[str, str]:
    """Hash every workspace file a review lists in files_read.

    Entries may be files, directories (expanded), globs, or paths followed by a note in
    parentheses ("code/x.py (docstring)"). Entries that match no file go to `unmatched`.
    """
    hashes: dict[str, str] = {}
    skip = {".venv", "venv", "__pycache__", ".git", ".superseded"}
    ws = ws.resolve()  # inside() returns resolved paths
    for value in listed:
        spec = re.sub(r"\s+\(.*\)\s*$", "", str(value)).strip().rstrip("/")
        if not spec or Path(spec).is_absolute() or ".." in Path(spec).parts:
            matches = []
        elif any(c in spec for c in "*?["):
            matches = sorted(ws.glob(spec))
        else:
            target = inside(ws, spec)
            matches = [target] if target is not None and target.exists() else []
        files = []
        for match in matches:
            if match.is_file():
                files.append(match)
            elif match.is_dir():
                files += [p for p in sorted(match.rglob("*")) if p.is_file()]
        named = skip & set(Path(spec).parts)  # an entry that names e.g. runs/.superseded/... opts in
        files = [p for p in files if not (skip - named) & set(p.relative_to(ws).parts)]
        if not files and unmatched is not None:
            unmatched.append(str(value))
        for path in files:
            if path.stat().st_size <= 50 * 1024 * 1024:
                hashes[rel(ws, path)] = sha256(path)
    return hashes


def cmd_review(args: argparse.Namespace) -> int:
    """Check a review the Reviewer wrote and stamp the files it read, with their hashes."""
    ws = require_workspace(args.workspace)
    path = ws / "reviews" / args.review / "review.json"
    if not path.is_file():
        print(f"ERROR: {path} does not exist; write the review first", file=sys.stderr)
        return 1
    prefix = f"reviews/{args.review}/"
    problems = [e for e in validate(ws)[0] if e.startswith(prefix)]
    if problems:
        for message in problems:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1
    review = read_json(path)
    if review.get("recorded"):
        print(f"ERROR: review {args.review} was already recorded on {review['recorded']}; a review "
              "stamps the files it read once. Changed files need the next round.", file=sys.stderr)
        return 1
    unmatched: list = []
    review["files_sha256"] = review_files(ws, review.get("files_read") or [], unmatched)
    review["recorded"] = now()
    write_json(path, review)
    for value in unmatched:
        print(f"WARN: files_read entry {value!r} matches no file in the workspace")
    append_log(ws, "reviewer", "review-recorded",
               f"{args.review} verdict={review.get('verdict')} files={len(review['files_sha256'])}")
    print(f"Recorded review {args.review}: verdict {review.get('verdict')}, "
          f"{len(review['files_sha256'])} file(s) stamped")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    ws = require_workspace(args.workspace)
    if not ID_RE.match(args.id):
        sys.exit("ERROR: --id may contain only letters, digits, dot, dash and underscore")
    run_dir = ws / "runs" / args.id
    if run_dir.exists() and not args.replace:
        sys.exit(f"ERROR: run {args.id!r} already exists (use --replace to rerun it)")
    command = list(args.command)
    if not command:
        sys.exit("ERROR: give the command to run after `--`")
    protocol = read_json(ws / "crew.json").get("protocol")
    if args.kind == "analysis":
        gate = read_json(ws / "plan.json").get("gates", {}).get("design", {})
        if gate.get("status") != "approved":
            sys.exit("ERROR: analysis runs are blocked until the design gate is approved")
    temp = temp_paths(command)
    if temp and protocol != "0.1":
        sys.exit(f"ERROR: the command uses temporary path(s) outside the workspace ({', '.join(temp)}); "
                 "copy what it needs into the workspace so a clean rerun can reproduce it")
    code = hash_entries(ws, args.code, must_exist=True)
    coverage: dict = {}
    if args.kind == "analysis" and protocol != "0.1":
        if args.unreviewed:
            coverage = {"unreviewed": args.unreviewed}
        else:
            if not code:
                sys.exit("ERROR: name every script an analysis run executes with --code, so the code "
                         "review can be checked against it")
            reviewed, problem = code_review_covering(ws, code)
            if problem:
                sys.exit(f"ERROR: {problem}. Ask the Reviewer for a code review round of the current "
                         "code, or, if the human agrees, rerun with --unreviewed \"<reason>\" "
                         "(recorded and counted in paper/process.tex)")
            coverage = {"code_review": reviewed}
    inputs = hash_entries(ws, args.input, must_exist=True)
    if run_dir.exists() and (run_dir / "run.json").exists():
        archived = archive_run(ws, run_dir)
        append_log(ws, args.role, "run-superseded", f"{args.id} archived to {archived}")
    run_dir.mkdir(parents=True, exist_ok=True)
    metrics_file = inside(ws, args.metrics) if args.metrics else None
    if args.metrics and metrics_file is None:
        sys.exit("ERROR: --metrics must be a relative path inside the workspace")
    if metrics_file is not None and metrics_file.exists():
        metrics_file.unlink()  # never record metrics left over from an earlier run
    started = now()
    with (run_dir / "stdout.log").open("w", encoding="utf-8") as out, \
            (run_dir / "stderr.log").open("w", encoding="utf-8") as err:
        completed = subprocess.run(command, cwd=ws, stdout=out, stderr=err, check=False)
    finished = now()
    metrics: dict = {}
    if metrics_file is not None and metrics_file.is_file():
        loaded = read_json(metrics_file)
        if isinstance(loaded, dict):
            metrics = loaded
    outputs = hash_entries(ws, args.output + ([args.metrics] if args.metrics else []), must_exist=False)
    write_json(run_dir / "run.json", {
        "id": args.id,
        "role": args.role,
        "kind": args.kind,
        "command": command,
        "started": started,
        "finished": finished,
        "exit_code": completed.returncode,
        "code": code,
        "inputs": inputs,
        "outputs": outputs,
        "metrics": metrics,
        "metrics_file": args.metrics or None,
        "env": command_env(ws, command),
        **coverage,
    })
    if coverage.get("unreviewed"):
        append_log(ws, args.role, "run-unreviewed", f"{args.id}: {coverage['unreviewed']}")
    append_log(ws, args.role, "run", f"{args.id} exit={completed.returncode}")
    print(f"Run {args.id}: exit code {completed.returncode}, {len(metrics)} metric(s) recorded")
    return 0 if completed.returncode == 0 else 1


def same_value(old: object, new: object, rtol: float, atol: float) -> bool:
    numeric = (int, float)
    if isinstance(old, numeric) and isinstance(new, numeric) and not isinstance(old, bool) and not isinstance(new, bool):
        if isinstance(old, float) and isinstance(new, float) and math.isnan(old) and math.isnan(new):
            return True  # a metric that is NaN in both runs is reproduced
        return math.isclose(old, new, rel_tol=rtol, abs_tol=atol)
    return old == new


def rerun_order(runs: dict[str, dict]) -> list[dict]:
    """Order runs so that a run comes after every run that produced one of its inputs.

    Ties (and runs with no data dependency) keep the order in which they first ran:
    start time, then finish time, then id. Start times only have one-second
    resolution, so they alone cannot order runs started in the same second.
    """
    def first_ran(run: dict) -> tuple:
        return (str(run.get("started")), str(run.get("finished")), str(run.get("id")))

    producers: dict[str, set[str]] = {}
    for run_id, run in runs.items():
        for item in run.get("outputs") or []:
            if isinstance(item, dict) and item.get("path"):
                producers.setdefault(item["path"], set()).add(run_id)
    needs: dict[str, set[str]] = {}
    for run_id, run in runs.items():
        deps = set()
        for item in run.get("inputs") or []:
            if isinstance(item, dict) and item.get("path"):
                deps |= producers.get(item["path"], set()) - {run_id}
        needs[run_id] = deps
    ordered, done = [], set()
    pending = sorted(runs, key=lambda r: first_ran(runs[r]))
    while pending:
        ready = [r for r in pending if needs[r] <= done]
        if not ready:  # a cycle: fall back to the order in which they first ran
            ready = pending[:1]
        nxt = ready[0]
        ordered.append(runs[nxt])
        done.add(nxt)
        pending.remove(nxt)
    return ordered


def cmd_rerun(args: argparse.Namespace) -> int:
    """Re-execute every run in a fresh copy of the workspace and compare metrics."""
    ws = require_workspace(args.workspace).resolve()
    runs, errors = read_runs(ws)
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1
    if not runs:
        print("ERROR: there are no runs to reproduce", file=sys.stderr)
        return 1
    ordered = rerun_order(runs)
    keep_data = set()
    if args.reuse_data:
        manifest = ws / "data" / "manifest.json"
        if manifest.exists():
            keep_data = {d.get("path") for d in read_json(manifest).get("datasets", []) if isinstance(d, dict)}
    results, passed = [], True
    with tempfile.TemporaryDirectory(prefix="crew-rerun-") as tmp:
        copy = Path(tmp) / "ws"
        skip = ["runs", "replication.json", "replication-history.jsonl"]
        if args.setup:  # a fresh environment: do not carry the author's over
            skip += [".venv", "venv", "__pycache__"]
        shutil.copytree(ws, copy, symlinks=True, ignore=shutil.ignore_patterns(*skip))
        setup = None
        run_env = dict(os.environ)
        if args.setup:  # the fresh environment comes first on PATH, as if activated
            run_env["PATH"] = f"{copy / '.venv' / 'bin'}{os.pathsep}{run_env.get('PATH', '')}"
            run_env["VIRTUAL_ENV"] = str(copy / ".venv")
        if args.setup:
            done = subprocess.run(args.setup, shell=True, cwd=copy, check=False,
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            setup = {"command": args.setup, "exit_code": done.returncode, "output_tail": done.stdout[-2000:]}
            print(f"  setup: exit code {done.returncode}")
            if done.returncode != 0:
                passed = False
                ordered = []
        # remove everything the runs produced, so each run must recreate it
        for run in ordered:
            for item in run.get("outputs") or []:
                path = item.get("path") if isinstance(item, dict) else None
                if path and path not in keep_data:
                    target = inside(copy, path)
                    if target is not None and target.is_file():
                        target.unlink()
        for run in ordered:
            entry = {"run": run.get("id"),
                     "record_sha256": sha256(ws / "runs" / str(run.get("id")) / "run.json")}
            metrics_path = run.get("metrics_file")
            # `crew.py run` creates the run's folder before the command starts; do the same
            (copy / "runs" / str(run.get("id"))).mkdir(parents=True, exist_ok=True)
            # a path into the original workspace (an author's .venv/bin/python, say) points into the copy
            command = [str(t).replace(str(ws), str(copy)) for t in run.get("command") or ["false"]]
            completed = subprocess.run(
                command, cwd=copy, check=False, env=run_env,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            entry["exit_code"] = completed.returncode
            entry["env"] = command_env(copy, run.get("command") or [])
            if completed.returncode != 0:
                entry["status"] = "failed"
                entry["output_tail"] = completed.stdout[-2000:]
            elif not run.get("metrics"):
                entry["status"] = "ran"  # nothing to compare (for example a data-prep run)
            elif not metrics_path:
                entry["status"] = "no-metrics-file"
            else:
                target = inside(copy, metrics_path)
                new = read_json(target) if target is not None and target.is_file() else None
                if not isinstance(new, dict):
                    entry["status"] = "no-metrics-file"
                else:
                    diffs = {
                        key: [old, new.get(key)] for key, old in run["metrics"].items()
                        if not same_value(old, new.get(key), args.rtol, args.atol)
                    }
                    entry["status"] = "mismatch" if diffs else "match"
                    if diffs:
                        entry["diffs"] = diffs
            if entry["status"] not in ("match", "ran"):
                passed = False
            results.append(entry)
            print(f"  {entry['run']:<24} {entry['status']}")
    report = {
        "created": now(), "passed": passed, "rtol": args.rtol, "atol": args.atol,
        "reuse_data": bool(args.reuse_data),
        "setup": setup,
        # crew.py's own interpreter; each run's entry records the interpreter its command used
        "env": {"crew_python": platform.python_version(), "platform": platform.platform()},
        "runs": results,
    }
    write_json(ws / "replication.json", report)
    with (ws / "replication-history.jsonl").open("a", encoding="utf-8") as handle:  # keep every attempt
        handle.write(json.dumps({
            "created": report["created"], "passed": passed, "setup": args.setup,
            "reproduced": sum(r["status"] in ("match", "ran") for r in results), "total": len(results),
            "not_reproduced": {r["run"]: r["status"] for r in results if r["status"] not in ("match", "ran")},
        }) + "\n")
    append_log(ws, "replicator", "rerun", f"passed={passed}")
    print(f"Rerun {'PASSED' if passed else 'FAILED'}: {sum(r['status'] in ('match', 'ran') for r in results)}"
          f"/{len(results)} run(s) reproduced; report in replication.json")
    return 0 if passed else 1


def cmd_log(args: argparse.Namespace) -> int:
    ws = require_workspace(args.workspace)
    append_log(ws, args.role, args.action, args.detail or "")
    print(f"Logged: {args.role} {args.action}")
    return 0


def cmd_brief(args: argparse.Namespace) -> int:
    ws = require_workspace(args.workspace)
    text = Path(args.file).read_text(encoding="utf-8") if args.file else sys.stdin.read()
    if not text.strip():
        print("ERROR: the brief is empty", file=sys.stderr)
        return 1
    stamp = now().replace("-", "").replace(":", "")
    folder = ws / "briefs"
    folder.mkdir(exist_ok=True)
    target = folder / f"{stamp}-{args.role}.md"
    n = 1
    while target.exists():
        n += 1
        target = folder / f"{stamp}-{args.role}-{n}.md"
    target.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
    detail = f"{args.role} {target.stem.split('-', 1)[0]}" + (f" ({args.note})" if args.note else "")
    append_log(ws, "pi", "brief-archived", detail)
    print(target)
    return 0


def cmd_numbers(args: argparse.Namespace) -> int:
    ws = require_workspace(args.workspace)
    claims, errors = read_claims(ws)
    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        return 1
    target = ws / "paper" / "numbers.tex"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_numbers(claims), encoding="utf-8")
    count = sum(1 for c in claims if c.get("macro") and "value" in c)
    print(f"Wrote {target} with {count} macro(s)")
    (ws / "paper" / "process.tex").write_text(render_process(ws), encoding="utf-8")
    print(f"Wrote {ws / 'paper' / 'process.tex'} with {len(process_facts(ws))} process macro(s)")
    return 0


# Review targets each gate needs, in order; targets in one tuple entry can be reviewed in parallel.
STAGE_TARGETS = {
    "question": (("question",),),
    "design": (("literature", "design"),),
    "results": (("code",), ("results",)),
    "submission": (("paper",),),
}
SETTLED = ("resolved", "withdrawn", "conceded")


def reviews_of(ws: Path, target: str) -> list[dict]:
    reviews, _ = read_reviews(ws)
    found = [r for r in reviews.values() if r.get("target") == target and isinstance(r.get("round"), int)]
    return sorted(found, key=lambda r: r["round"])


def cmd_changes(args: argparse.Namespace) -> int:
    """What changed since the last recorded review round of a target (read-only).

    Computed from the hashes `crew.py review` stamped, not from anyone's account, so a
    Reviewer can start round n+1 with the files that changed and the findings still in play.
    """
    ws = require_workspace(args.workspace).resolve()
    rounds = reviews_of(ws, args.target)
    if args.round is not None:
        rounds = [r for r in rounds if r["round"] == args.round]
    if not rounds:
        print(f"No review of {args.target}{'' if args.round is None else f' round {args.round}'}: "
              "read everything (this is round 1).")
        return 0
    base = rounds[-1]
    stamped = base.get("files_sha256")
    if not isinstance(stamped, dict):  # a 0.1 review, not recorded with `crew.py review`
        print(f"NOTE: {base.get('id')} was not recorded with `crew.py review`; only modification times "
              "are available, so read everything that matters.")
        stamped = {}
    current = review_files(ws, base.get("files_read") or []) if stamped else {}
    changed = sorted(p for p in stamped if p in current and current[p] != stamped[p] and p != "log.jsonl")
    removed = sorted(p for p in stamped if p not in current and not (ws / p).exists())
    added = sorted(p for p in current if p not in stamped)
    since = parse_time(base.get("recorded") or base.get("created"))
    skip = {".venv", "venv", "__pycache__", ".git", ".superseded", "briefs", "reviews"}
    elsewhere = []
    if since is not None:
        cutoff = since.timestamp()
        for path in ws.rglob("*"):
            relative = path.relative_to(ws)
            if (path.is_file() and not skip & set(relative.parts) and str(relative) not in current
                    and str(relative) != "log.jsonl" and path.stat().st_mtime > cutoff):
                elsewhere.append(str(relative))
    findings = [f for f in base.get("findings") or [] if isinstance(f, dict)]
    live = [f for f in findings if f.get("status") not in SETTLED]
    log = []
    if since is not None and (ws / "log.jsonl").exists():
        for line in (ws / "log.jsonl").read_text(encoding="utf-8").splitlines():
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            when = parse_time(entry.get("time"))
            if when and when > since and entry.get("action") not in ("brief-archived",):
                log.append(entry)
    report = {
        "since": base.get("id"), "recorded": base.get("recorded") or base.get("created"), "verdict": base.get("verdict"),
        "changed": changed, "added": added, "removed": removed, "other_files_modified": sorted(elsewhere),
        "findings_in_play": [{"id": f.get("id"), "severity": f.get("severity"), "status": f.get("status"),
                              "has_response": bool(f.get("response"))} for f in live],
        "log_since": [f"{e.get('time')} {e.get('role')} {e.get('action')}" for e in log],
    }
    if args.json:
        print(json.dumps(report, indent=2))
        return 0
    print(f"Since {base.get('id')} (verdict {base.get('verdict')}, recorded {report['recorded']}):")
    for label, items in (("changed", changed), ("added (matched by its files_read)", added),
                         ("removed", removed), ("modified elsewhere", report["other_files_modified"])):
        print(f"  {label}: {len(items)}")
        for item in items[: args.limit]:
            print(f"    {item}")
        if len(items) > args.limit:
            print(f"    ... {len(items) - args.limit} more (use --json)")
    print(f"Findings still in play: {len(live)} of {len(findings)}")
    for f in live:
        print(f"    {f.get('id')} [{f.get('severity')}] {f.get('status')}"
              f"{' (has a response)' if f.get('response') else ' (no response)'}")
    print(f"Ledger entries since: {len(log)}")
    for line in report["log_since"][-args.limit:]:
        print(f"    {line}")
    print("Unchanged files were already read in that round; re-read changed and added files in full "
          "and spot-check the rest.")
    return 0


def next_actions(ws: Path) -> list[str]:
    """The next steps for the PI, derived from the workspace alone. Lines starting with
    `parallel:` list steps with no dependency on each other."""
    plan = read_json(ws / "plan.json")
    gates = plan.get("gates", {})
    errors, _ = validate(ws)
    out: list[str] = []
    if errors:
        out.append(f"fix {len(errors)} validation error(s) first (`crew.py validate`): {errors[0]}")
    stage = next((g for g in GATES if (gates.get(g) or {}).get("status") != "approved"), None)
    if stage is None:
        return out + ["all four gates approved: the paper is final"]
    status = (gates.get(stage) or {}).get("status", "pending")
    if status == "requested":
        out.append(f"wait: the {stage} gate is with the human; present it and stop")
        return out
    if status == "rejected":
        out.append(f"the human rejected the {stage} gate: act on their note, then review and request it again")
    runs, _ = read_runs(ws)
    analysis = [r for r in runs.values() if r.get("kind") == "analysis"]
    tasks = [t for t in plan.get("tasks") or [] if isinstance(t, dict) and t.get("status") in ("todo", "doing")]
    reviews = {t: reviews_of(ws, t) for t in REVIEW_TARGETS}
    ready = True
    for group in STAGE_TARGETS[stage]:
        steps = []
        for target in group:
            done = reviews[target]
            latest = done[-1] if done else None
            if latest and latest.get("verdict") == "pass" and not open_critical(latest):
                continue
            ready = False
            missing = {
                "question": not plan.get("question") and "PI drafts question, hypotheses and contribution in plan.json",
                "literature": not bib_keys(ws) and "Scout: verified refs.bib and sources/",
                "design": not (plan.get("design") or {}).get("summary") and "Designer: design and task board in plan.json",
                "code": not (ws / "code").is_dir() or not any((ws / "code").iterdir()),
            }
            if target == "code" and missing["code"]:
                steps.append("analysis code: the Econometrician/Experimenter writes code/ (and synthetic checks)")
                continue
            if latest is None and missing.get(target):
                steps.append(str(missing[target]))
                continue
            if target == "results" and not analysis:
                steps.append("analysis runs: run the plan through `crew.py run --kind analysis --code ...`")
                continue
            if target == "paper" and not (ws / "paper" / "main.tex").exists():
                steps.append("paper: Figures RA builds figures/tables, then the Writer drafts paper/main.tex")
                continue
            if latest is None:
                steps.append(f"Reviewer: {target} round 1")
                continue
            live = [f for f in latest.get("findings") or [] if isinstance(f, dict) and f.get("status") == "open"]
            if latest["round"] >= MAX_REVIEW_ROUNDS:
                steps.append(f"{target}: round {latest['round']} was the last; take open findings "
                             f"{', '.join(str(f.get('id')) for f in live) or '(none open)'} to the human")
                continue
            answered = all(f.get("response") for f in live)
            if live and not answered:
                steps.append(f"{target}: send all {len(live)} open finding(s) of {latest.get('id')} to their owners "
                             "at once (one brief per owner, in parallel), then Reviewer round "
                             f"{latest['round'] + 1}")
            else:
                steps.append(f"Reviewer: {target} round {latest['round'] + 1} (start it with "
                             f"`crew.py changes <ws> {target}`)")
        if steps:
            out.append(("parallel: " if len(steps) > 1 else "") + " | ".join(steps))
            break  # later groups depend on this one
    if stage == "submission":
        problems = check_replication(ws, runs, required=True)
        if problems and runs:
            out.append("parallel: Replicator: `crew.py rerun --setup ...` (needs only the runs; it can go "
                       "alongside the Writer and the paper review once the Figures RA's runs are logged) "
                       f"— {problems[0]}")
            ready = False
        if stale_paper_inputs(ws):
            out.append("run `crew.py numbers` and recompile: paper inputs are stale")
    # Review, rerun and gate tasks are scheduled by the stage logic above, not as free work.
    tasks = [t for t in tasks if t.get("owner") not in ("reviewer", "replicator", "pi")]
    if tasks:
        owners: dict[str, list[str]] = {}
        for task in tasks:
            owners.setdefault(str(task.get("owner")), []).append(str(task.get("id")))
        line = " | ".join(f"{owner}: {', '.join(ids)}" for owner, ids in owners.items())
        out.append(("parallel (one subagent per owner): " if len(owners) > 1 else "open tasks: ") + line)
        ready = False
    if stage == "results" and not (ws / "paper" / "main.tex").exists():
        out.append("off the critical path, now: the Writer may draft the sections that need no results "
                   "(introduction, background, data, method) from plan.json and refs.bib")
    if ready and not errors:
        out.append(f"request the {stage} gate: `crew.py gate <ws> {stage} request --note ...`")
    return out


def cmd_next(args: argparse.Namespace) -> int:
    """Print the next steps for the PI (read-only)."""
    ws = require_workspace(args.workspace)
    steps = next_actions(ws)
    if args.json:
        print(json.dumps(steps, indent=2))
    else:
        for step in steps:
            print(f"- {step}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command_name", required=True)

    p = sub.add_parser("init", help="create a new workspace")
    p.add_argument("workspace")
    p.add_argument("--track", required=True, choices=TRACKS)
    p.add_argument("--title", required=True)
    p.add_argument("--seed", help="id of the bench seed task this workspace answers")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("validate", help="check the workspace against the protocol")
    p.add_argument("workspace")
    p.add_argument("--strict", action="store_true", help="treat missing data and run files as errors")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("status", help="show gates, tasks and counts")
    p.add_argument("workspace")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("gate", help="request, approve or reject a human gate")
    p.add_argument("workspace")
    p.add_argument("gate", choices=GATES)
    p.add_argument("action", choices=("request", "approve", "reject"))
    p.add_argument("--by", help="name of the human who decided (approve/reject)")
    p.add_argument("--note", help="summary of the request, or the human's words")
    p.add_argument("--accept-findings", help="comma-separated open critical finding ids the human "
                   "accepts anyway (needs --note; disclosed in the paper)")
    p.set_defaults(func=cmd_gate)

    p = sub.add_parser("run", help="execute a command (given after `--`) and record it in the run ledger")
    p.add_argument("workspace")
    p.add_argument("--id", required=True)
    p.add_argument("--role", required=True, choices=ROLES)
    p.add_argument("--kind", required=True, choices=RUN_KINDS)
    p.add_argument("--code", action="append", default=[], help="script the run executes (repeatable)")
    p.add_argument("--input", action="append", default=[], help="input file (repeatable)")
    p.add_argument("--output", action="append", default=[], help="output file (repeatable)")
    p.add_argument("--metrics", help="JSON file of metrics the command writes")
    p.add_argument("--replace", action="store_true", help="overwrite an existing run with this id")
    p.add_argument("--unreviewed", metavar="REASON",
                   help="run analysis code no passing code review covers (the human agreed; recorded)")
    p.set_defaults(func=cmd_run, command=[])

    p = sub.add_parser("rerun", help="re-execute every run in a fresh copy and compare metrics")
    p.add_argument("workspace")
    p.add_argument("--rtol", type=float, default=1e-6, help="relative tolerance for numeric metrics")
    p.add_argument("--atol", type=float, default=1e-9, help="absolute tolerance for numeric metrics")
    p.add_argument("--reuse-data", action="store_true",
                   help="keep files listed in data/manifest.json instead of re-downloading them")
    p.add_argument("--setup", metavar="SHELL_COMMAND",
                   help="build a fresh environment in the copy first (e.g. 'python3 -m venv .venv && "
                        ".venv/bin/pip install -r requirements.txt'); .venv is then not copied")
    p.set_defaults(func=cmd_rerun)

    p = sub.add_parser("review", help="check a review the Reviewer wrote and stamp the files it read")
    p.add_argument("workspace")
    p.add_argument("review", help="review id, e.g. code-r2")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("log", help="append an entry to log.jsonl with the current time")
    p.add_argument("workspace")
    p.add_argument("--role", required=True, choices=ROLES)
    p.add_argument("--action", required=True, help="short verb, e.g. sources-verified")
    p.add_argument("--detail", help="one line of detail")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("brief", help="archive a brief (from --file or stdin) in briefs/ and log it; prints its path")
    p.add_argument("workspace")
    p.add_argument("role", choices=[r for r in ROLES if r != "pi"])
    p.add_argument("--file", help="read the brief from this file instead of stdin")
    p.add_argument("--note", help="what the brief is for, e.g. design-r2")
    p.set_defaults(func=cmd_brief)

    p = sub.add_parser("numbers", help="render paper/numbers.tex from claims.jsonl")
    p.add_argument("workspace")
    p.set_defaults(func=cmd_numbers)

    p = sub.add_parser("changes", help="what changed since the last recorded review round of a target (read-only)")
    p.add_argument("workspace")
    p.add_argument("target", choices=REVIEW_TARGETS)
    p.add_argument("--round", type=int, help="compare against this round instead of the latest recorded one")
    p.add_argument("--limit", type=int, default=40, help="list at most this many paths per group")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_changes)

    p = sub.add_parser("next", help="the PI's next steps, with the ones that can run in parallel (read-only)")
    p.add_argument("workspace")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_next)
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    command: list[str] = []
    if "--" in argv:  # everything after the first `--` is the command for `run`
        split = argv.index("--")
        argv, command = argv[:split], argv[split + 1:]
    args = build_parser().parse_args(argv)
    if command:
        if args.command_name != "run":
            sys.exit("ERROR: only `run` takes a command after `--`")
        args.command = command
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
