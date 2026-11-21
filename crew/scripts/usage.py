#!/usr/bin/env python3
"""Measure what a crew project cost: model tokens, API-equivalent dollars and time.

Reads the Claude Code transcripts on this machine (~/.claude/projects) and the
workspace's own log, so it works only where the crew actually ran.

Attribution:
- A subagent transcript belongs to a workspace when its working directory is inside
  the workspace or its first message names the workspace path.
- In a PI session (one whose shell commands ran `crew.py init` or `crew.py gate` on
  the workspace), an API request that names one or more
  workspaces is split evenly among them. A request that names none is split evenly
  among the workspaces active at that moment (between their first and last log entry).
  This is an estimate; the totals across workspaces add up to the PI sessions' totals.

Time:
- elapsed: first log entry to the submission gate (or the last log entry);
- human wait: the sum of gate request -> decision intervals;
- compute: the sum of the logged runs' durations;
- subagent minutes by role: first to last API request of each subagent transcript, with
  the role read from the brief it was given (`briefs/<time>-<role>.md`). Roles that ran
  in parallel overlap, so these add up to more than the elapsed time; a role that
  dominates is where to look when a paper is slow.

Dollar figures use the Claude API list prices below. Under a Claude subscription the
same work is billed to the subscription, not per token.

Usage:
  python3 crew/scripts/usage.py <workspace> [<workspace> ...] [--out FILE] [--projects DIR]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# USD per million tokens: input, output, cache read, 5-minute cache write, 1-hour cache write.
PRICES = {
    "claude-opus-5-5": (4.00, 20.00, 0.20, 5.00, 8.00),
    "claude-fable-5-2": (8.00, 40.00, 0.20, 10.00, 16.00),
    "claude-sonnet-5-5": (2.00, 10.00, 0.10, 2.50, 4.00),
    "claude-haiku-5-5": (0.10, 0.50, 0.01, 0.125, 0.20),
}
PRICES_AS_OF = "2026-11-03"
BRIEF_ROLE = re.compile(r"briefs/\d{8}T\d{6}Z-([a-z-]+)\.md")
PI_ACTION = re.compile(r"crew\.py[\"']?\s+(init|gate)\s")
TOKEN_FIELDS = ("input", "output", "cache_read", "cache_write_5m", "cache_write_1h")


def parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def usage_of(usage: dict) -> dict:
    cache = usage.get("cache_creation") or {}
    write_total = usage.get("cache_creation_input_tokens") or 0
    write_1h = cache.get("ephemeral_1h_input_tokens") or 0
    return {
        "input": usage.get("input_tokens") or 0,
        "output": usage.get("output_tokens") or 0,
        "cache_read": usage.get("cache_read_input_tokens") or 0,
        "cache_write_5m": write_total - write_1h,
        "cache_write_1h": write_1h,
    }


def requests(path: Path):
    """Yield (time, model, tokens, text, shell commands) once per API request in a transcript."""
    by_id: dict[str, dict] = {}
    order: list[str] = []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            message = entry.get("message") or {}
            if entry.get("type") != "assistant" or not message.get("usage"):
                continue
            key = f"{message.get('id')}/{entry.get('requestId')}"
            if key not in by_id:
                by_id[key] = {"time": entry.get("timestamp"), "model": message.get("model"), "parts": [], "shell": []}
                order.append(key)
            record = by_id[key]
            record["tokens"] = usage_of(message["usage"])
            for block in message.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    record["parts"].append(json.dumps(block.get("input"), ensure_ascii=False))
                    if block.get("name") == "Bash":
                        record["shell"].append(str((block.get("input") or {}).get("command", "")))
                elif isinstance(block, dict) and block.get("type") == "text":
                    record["parts"].append(block.get("text", ""))
    for key in order:
        r = by_id[key]
        yield parse_time(r["time"]), r["model"], r["tokens"], "\n".join(r["parts"]), r["shell"]


def first_context(path: Path) -> str:
    """The first working directory and first user message of a subagent transcript."""
    cwd, text = "", ""
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            try:
                entry = json.loads(line)
            except ValueError:
                continue
            cwd = cwd or entry.get("cwd", "")
            content = (entry.get("message") or {}).get("content")
            if entry.get("type") == "user" and isinstance(content, str) and not text:
                text = content
            if cwd and text:
                break
    return cwd + "\n" + text


class Workspace:
    def __init__(self, path: Path):
        self.path = path.resolve()
        self.name = self.path.name
        self.log = []
        log_path = self.path / "log.jsonl"
        if log_path.exists():
            for line in log_path.read_text().splitlines():
                try:
                    self.log.append(json.loads(line))
                except ValueError:
                    pass
        times = [t for t in (parse_time(e.get("time")) for e in self.log) if t]
        self.start = min(times) if times else None
        self.end = max(times) if times else None
        self.tokens = defaultdict(lambda: defaultdict(float))  # source -> model/field -> tokens
        self.subagents = 0
        self.role_minutes: dict[str, list[float]] = defaultdict(list)

    def mentioned_in(self, text: str) -> bool:
        return str(self.path) in text or re.search(rf"(^|[/\s\"'`]){re.escape(self.name)}(/|\b)", text) is not None

    def active_at(self, when: datetime | None) -> bool:
        return bool(when and self.start and self.end and self.start <= when <= self.end)

    def add(self, source: str, model: str, tokens: dict, share: float) -> None:
        bucket = self.tokens[source]
        for field in TOKEN_FIELDS:
            bucket[f"{model}|{field}"] += tokens[field] * share

    def timing(self) -> dict:
        plan_path = self.path / "plan.json"
        gates = json.loads(plan_path.read_text()).get("gates", {}) if plan_path.exists() else {}
        submission = parse_time((gates.get("submission") or {}).get("decided_on"))
        end = submission if submission and gates["submission"].get("status") == "approved" else self.end
        wait = 0.0
        for gate in gates.values():
            asked, decided = parse_time(gate.get("requested_on")), parse_time(gate.get("decided_on"))
            if asked and decided and decided > asked:
                wait += (decided - asked).total_seconds()
        compute = 0.0
        for run in (self.path / "runs").glob("*/run.json"):
            record = json.loads(run.read_text())
            started, finished = parse_time(record.get("started")), parse_time(record.get("finished"))
            if started and finished:
                compute += (finished - started).total_seconds()
        return {
            "started": self.start.isoformat() if self.start else None,
            "finished": end.isoformat() if end else None,
            "complete": bool(submission and gates["submission"].get("status") == "approved"),
            "elapsed_hours": round((end - self.start).total_seconds() / 3600, 1) if end and self.start else None,
            "human_gate_wait_hours": round(wait / 3600, 1),
            "logged_compute_minutes": round(compute / 60, 1),
        }


def cost(model_fields: dict) -> tuple[float, list[str]]:
    total, unknown = 0.0, set()
    for key, tokens in model_fields.items():
        model, field = key.split("|")
        price = PRICES.get(model)
        if price is None:
            unknown.add(model)
            continue
        total += tokens * price[TOKEN_FIELDS.index(field)] / 1e6
    return total, sorted(unknown)


def summarize(ws: Workspace) -> dict:
    out = {"workspace": ws.name, **ws.timing(), "subagent_transcripts": ws.subagents, "by_source": {}}
    out["subagent_minutes_by_role"] = {
        role: {"runs": len(spans), "minutes": round(sum(spans), 1), "longest": round(max(spans), 1)}
        for role, spans in sorted(ws.role_minutes.items(), key=lambda kv: -sum(kv[1]))}
    grand: dict[str, float] = defaultdict(float)
    for source, fields in ws.tokens.items():
        usd, unknown = cost(fields)
        totals = {f: round(sum(v for k, v in fields.items() if k.endswith("|" + f))) for f in TOKEN_FIELDS}
        out["by_source"][source] = {"tokens": totals, "api_usd": round(usd, 2), "unpriced_models": unknown}
        for key, value in fields.items():
            grand[key] += value
    usd, unknown = cost(grand)
    out["tokens"] = {f: round(sum(v for k, v in grand.items() if k.endswith("|" + f))) for f in TOKEN_FIELDS}
    out["models"] = sorted({k.split("|")[0] for k in grand})
    out["api_usd"] = round(usd, 2)
    out["unpriced_models"] = unknown
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("workspaces", nargs="+")
    parser.add_argument("--projects", default=str(Path.home() / ".claude" / "projects"))
    parser.add_argument("--out", help="write the result as JSON to this file")
    args = parser.parse_args(argv)

    spaces = [Workspace(Path(p)) for p in args.workspaces]
    projects = Path(args.projects)
    for main_path in sorted(projects.glob("*/*.jsonl")):
        session_dir = main_path.with_suffix("")
        for sub in sorted((session_dir / "subagents").glob("*.jsonl")):
            context = first_context(sub)
            owners = [ws for ws in spaces if ws.mentioned_in(context)]
            if not owners:
                continue
            for ws in owners:
                ws.subagents += 1
            times = []
            for when, model, tokens, _, _ in requests(sub):
                times.append(when)
                for ws in owners:
                    ws.add("subagents", model, tokens, 1 / len(owners))
            role = BRIEF_ROLE.search(context)
            times = [t for t in times if t]
            if role and times:
                for ws in owners:
                    ws.role_minutes[role.group(1)].append((max(times) - min(times)).total_seconds() / 60)

        rows = list(requests(main_path))
        pi_of = [ws for ws in spaces if any(PI_ACTION.search(cmd) and ws.mentioned_in(cmd)
                                            for *_, shell in rows for cmd in shell)]
        for when, model, tokens, text, _ in rows:
            named = [ws for ws in pi_of if ws.mentioned_in(text)]
            targets = named or [ws for ws in pi_of if ws.active_at(when)]
            for ws in targets:
                ws.add("pi", model, tokens, 1 / len(targets))

    result = {
        "measured_on": datetime.now().astimezone().isoformat(timespec="seconds"),
        "prices_usd_per_mtok": {m: dict(zip(TOKEN_FIELDS, p)) for m, p in PRICES.items()},
        "prices_as_of": PRICES_AS_OF,
        "method": "crew/scripts/usage.py; PI requests naming no workspace are split among the workspaces active at that time",
        "workspaces": [summarize(ws) for ws in spaces],
    }
    for row in result["workspaces"]:
        t = row["tokens"]
        print(f"{row['workspace']:<26} {row['elapsed_hours']}h elapsed, {row['human_gate_wait_hours']}h at gates, "
              f"{row['logged_compute_minutes']} min compute | out {t['output']/1e6:.2f}M, "
              f"cache-read {t['cache_read']/1e6:.0f}M | ~${row['api_usd']:,.0f} API-equivalent")
        slow = list(row["subagent_minutes_by_role"].items())[:3]
        if slow:
            print("  slowest roles: " + ", ".join(f"{r} {v['minutes']:.0f} min over {v['runs']} run(s)"
                                                  for r, v in slow))
    if args.out:
        Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
