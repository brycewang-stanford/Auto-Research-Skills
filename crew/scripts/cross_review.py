#!/usr/bin/env python3
"""Run the crew's Reviewer on a different provider's model than the authors.

When the crew runs in Claude Code, the Reviewer runs on an OpenAI model through
`codex exec` (--via codex, the default). When the crew runs in Codex, it runs on
Claude through `claude -p` (--via claude). Either way the critic does not share
the authors' blind spots. This is the cross-family review that ARIS
(skills/aris) is built around.

The Reviewer gets only what crew/agents/reviewer.md allows: the workspace path,
the target, the round and the track. It reads the files itself, inside a
sandbox that lets it write only within the workspace.

Usage:
  python3 cross_review.py <workspace> <target> <round> [--via codex|claude] [--model MODEL]

Requires the chosen CLI, logged in. Sends the workspace's files to that provider.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parent
sys.path.insert(0, str(HERE))
import crew  # noqa: E402  (the workspace tool, same directory)


def reviewer_instructions() -> str:
    text = (PLUGIN / "agents" / "reviewer.md").read_text(encoding="utf-8")
    return re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.DOTALL).strip()


def configured_model() -> str | None:
    config = Path.home() / ".codex" / "config.toml"
    if not config.exists():
        return None
    match = re.search(r'^model\s*=\s*"([^"]+)"', config.read_text(encoding="utf-8"), re.MULTILINE)
    return match.group(1) if match else None


def build_prompt(ws: Path, target: str, number: int, track: str, model: str, authors: str) -> str:
    return f"""{reviewer_instructions()}

---

## Your assignment

- Workspace (read everything you need yourself): {ws}
- Protocol (file formats; read it first): {PLUGIN / "PROTOCOL.md"}
- Track playbook: {PLUGIN / "tracks" / f"{track}.md"}
- Target: {target}
- Round: {number}
- Workspace tool: python3 {HERE / "crew.py"}

You are running on a different provider's model ({model}) from the agents that wrote
this work ({authors}), so set `reviewer.model` to "{model}" and `reviewer.independence` to
"cross-family". Write your review to reviews/{target}-r{number}/review.json and keep
reviews/REVIEWER_MEMORY.md, as the instructions above say. Do not modify any other
file. Finish by running `python3 {HERE / "crew.py"} validate {ws}` and fixing errors in
your own review record only.
"""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("workspace")
    parser.add_argument("target", choices=crew.REVIEW_TARGETS)
    parser.add_argument("round", type=int)
    parser.add_argument("--via", choices=("codex", "claude"), default="codex",
                        help="codex: review on OpenAI (crew runs on Claude); claude: review on Claude (crew runs on Codex)")
    parser.add_argument("--model", help="model for the reviewer (default: the CLI's configured model)")
    parser.add_argument("--effort", default="high", help="reasoning effort for codex (default: high)")
    args = parser.parse_args(argv)

    if shutil.which(args.via) is None:
        print(f"ERROR: the {args.via} CLI is not installed; fall back to a fresh-context reviewer", file=sys.stderr)
        return 2
    ws = Path(args.workspace).resolve()
    if not (ws / "crew.json").exists():
        print(f"ERROR: {ws} is not a crew workspace", file=sys.stderr)
        return 1
    if args.round < 1 or args.round > crew.MAX_REVIEW_ROUNDS:
        print(f"ERROR: round must be between 1 and {crew.MAX_REVIEW_ROUNDS}", file=sys.stderr)
        return 1
    if args.via == "codex":
        model = args.model or configured_model() or "codex-default"
        authors = "Claude"
    else:
        model = args.model or "claude-default"
        authors = "an OpenAI model via Codex"
    track = crew.read_json(ws / "crew.json").get("track", "cs")
    out_dir = ws / "reviews" / f"{args.target}-r{args.round}"
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt = build_prompt(ws, args.target, args.round, track, model, authors)
    if args.via == "codex":
        command = [
            "codex", "exec", "--skip-git-repo-check", "--sandbox", "workspace-write",
            "--cd", str(ws), "-c", f"model_reasoning_effort={args.effort}",
            "--output-last-message", str(out_dir / "reviewer-reply.md"),
        ]
        if args.model:
            command += ["--model", args.model]
        command.append(prompt)
    else:
        command = [
            "claude", "-p", prompt, "--permission-mode", "acceptEdits",
            "--allowedTools", f"Read,Write,Edit,Glob,Grep,Bash(python3 {HERE / 'crew.py'} validate *)",
        ]
        if args.model:
            command += ["--model", args.model]
    log_path = out_dir / f"{args.via}.log"
    print(f"Running cross-family review of {args.target!r}, round {args.round}, on {model} via {args.via} ...")
    with log_path.open("w", encoding="utf-8") as log:
        completed = subprocess.run(command, cwd=ws, stdout=log, stderr=subprocess.STDOUT, check=False)
    if args.via == "claude" and log_path.exists():
        (out_dir / "reviewer-reply.md").write_text(log_path.read_text(encoding="utf-8"), encoding="utf-8")
    if completed.returncode != 0:
        print(f"ERROR: {args.via} exited with {completed.returncode}; see {log_path}", file=sys.stderr)
        return 1

    record = out_dir / "review.json"
    if not record.exists():
        print(f"ERROR: the reviewer wrote no {record}", file=sys.stderr)
        return 1
    review = crew.read_json(record)
    reviewer = review.setdefault("reviewer", {})
    if reviewer.get("model") != model or reviewer.get("independence") != "cross-family":
        reviewer.update(model=model, independence="cross-family", via=args.via)
        crew.write_json(record, review)
    errors, _ = crew.validate(ws)
    own = [e for e in errors if f"reviews/{args.target}-r{args.round}" in e]
    for message in own:
        print(f"ERROR: {message}", file=sys.stderr)
    print(f"Verdict: {review.get('verdict')}  ({len(review.get('findings') or [])} finding(s))")
    print(f"Kill argument: {review.get('kill_argument', '').strip()}")
    return 1 if own else 0


if __name__ == "__main__":
    sys.exit(main())
