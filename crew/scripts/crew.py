#!/usr/bin/env python3
"""Workspace tool for the Free-Research-Crew protocol (v0.1).

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
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

PROTOCOL_VERSION = "0.1"
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
    for directory in sorted(p for p in root.iterdir() if p.is_dir()):
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
        if meta.get("protocol") != PROTOCOL_VERSION:
            errors.append(f"crew.json: protocol must be {PROTOCOL_VERSION!r}")
        if meta.get("track") not in TRACKS:
            errors.append(f"crew.json: track must be one of {', '.join(TRACKS)}")
        if not meta.get("title"):
            errors.append("crew.json: title is empty")

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
        if parse_time(review.get("created")) is None:
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
    for sub in ("sources", "data", "runs", "code", "paper", "reviews"):
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
    (ws / ".gitignore").write_text("data/raw/\ndata/derived/\n.venv\n__pycache__/\n", encoding="utf-8")
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
        entries.append({"path": value, "sha256": sha256(target)})
    return entries


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
    if args.kind == "analysis":
        gate = read_json(ws / "plan.json").get("gates", {}).get("design", {})
        if gate.get("status") != "approved":
            sys.exit("ERROR: analysis runs are blocked until the design gate is approved")
    code = hash_entries(ws, args.code, must_exist=True)
    inputs = hash_entries(ws, args.input, must_exist=True)
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
        "env": {"python": platform.python_version(), "platform": platform.platform()},
    })
    append_log(ws, args.role, "run", f"{args.id} exit={completed.returncode}")
    print(f"Run {args.id}: exit code {completed.returncode}, {len(metrics)} metric(s) recorded")
    return 0 if completed.returncode == 0 else 1


def same_value(old: object, new: object, rtol: float, atol: float) -> bool:
    numeric = (int, float)
    if isinstance(old, numeric) and isinstance(new, numeric) and not isinstance(old, bool) and not isinstance(new, bool):
        return math.isclose(old, new, rel_tol=rtol, abs_tol=atol)
    return old == new


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
    ordered = sorted(runs.values(), key=lambda r: (str(r.get("started")), str(r.get("id"))))
    keep_data = set()
    if args.reuse_data:
        manifest = ws / "data" / "manifest.json"
        if manifest.exists():
            keep_data = {d.get("path") for d in read_json(manifest).get("datasets", []) if isinstance(d, dict)}
    results, passed = [], True
    with tempfile.TemporaryDirectory(prefix="crew-rerun-") as tmp:
        copy = Path(tmp) / "ws"
        shutil.copytree(ws, copy, symlinks=True, ignore=shutil.ignore_patterns("runs", "replication.json"))
        # remove everything the runs produced, so each run must recreate it
        for run in ordered:
            for item in run.get("outputs") or []:
                path = item.get("path") if isinstance(item, dict) else None
                if path and path not in keep_data:
                    target = inside(copy, path)
                    if target is not None and target.is_file():
                        target.unlink()
        for run in ordered:
            entry = {"run": run.get("id")}
            metrics_path = run.get("metrics_file")
            completed = subprocess.run(
                run.get("command") or ["false"], cwd=copy, check=False,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            )
            entry["exit_code"] = completed.returncode
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
        "env": {"python": platform.python_version(), "platform": platform.platform()},
        "runs": results,
    }
    write_json(ws / "replication.json", report)
    append_log(ws, "replicator", "rerun", f"passed={passed}")
    print(f"Rerun {'PASSED' if passed else 'FAILED'}: {sum(r['status'] in ('match', 'ran') for r in results)}"
          f"/{len(results)} run(s) reproduced; report in replication.json")
    return 0 if passed else 1


def cmd_log(args: argparse.Namespace) -> int:
    ws = require_workspace(args.workspace)
    append_log(ws, args.role, args.action, args.detail or "")
    print(f"Logged: {args.role} {args.action}")
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
    p.set_defaults(func=cmd_run, command=[])

    p = sub.add_parser("rerun", help="re-execute every run in a fresh copy and compare metrics")
    p.add_argument("workspace")
    p.add_argument("--rtol", type=float, default=1e-6, help="relative tolerance for numeric metrics")
    p.add_argument("--atol", type=float, default=1e-9, help="absolute tolerance for numeric metrics")
    p.add_argument("--reuse-data", action="store_true",
                   help="keep files listed in data/manifest.json instead of re-downloading them")
    p.set_defaults(func=cmd_rerun)

    p = sub.add_parser("log", help="append an entry to log.jsonl with the current time")
    p.add_argument("workspace")
    p.add_argument("--role", required=True, choices=ROLES)
    p.add_argument("--action", required=True, help="short verb, e.g. sources-verified")
    p.add_argument("--detail", help="one line of detail")
    p.set_defaults(func=cmd_log)

    p = sub.add_parser("numbers", help="render paper/numbers.tex from claims.jsonl")
    p.add_argument("workspace")
    p.set_defaults(func=cmd_numbers)
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
