#!/usr/bin/env python3
"""Install the research crew into Codex as skills.

Writes one skill per role into the Codex skills directory (default
~/.codex/skills): `crew-pi` (start or resume a crew project as the PI) and
`crew-<role>` for each role. Each skill points at this checkout's crew/ files by
absolute path, so the workspace tool and playbooks stay in one place.

Usage:
  python3 crew/adapters/codex/install.py [--dest DIR] [--force] [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n", re.DOTALL)


def parse(text: str) -> tuple[dict[str, str], str]:
    match = FRONTMATTER.match(text)
    meta: dict[str, str] = {}
    if match:
        for line in match.group(1).splitlines():
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
        text = text[match.end():]
    return meta, text.strip()


def codex_notes() -> str:
    crew = PLUGIN / "scripts" / "crew.py"
    review = PLUGIN / "scripts" / "cross_review.py"
    return f"""## Running in Codex

- Plugin root: `{PLUGIN}`. Wherever the instructions say `<plugin root>` or
  `${{CLAUDE_PLUGIN_ROOT}}`, use that path.
- Workspace tool: `python3 {crew}`.
- Roles are the `crew-<role>` skills (`crew-scout`, `crew-designer`, `crew-data-ra`,
  `crew-econometrician`, `crew-experimenter`, `crew-figures-ra`, `crew-writer`,
  `crew-replicator`, `crew-reviewer`). Where the instructions say "delegate to
  `crew:<role>`", spawn a sub-agent with that skill if your Codex supports it; otherwise
  finish your current role, then act as the next role yourself, reading only the files
  that role reads.
- **The Reviewer must not be you.** Run reviews on Claude:
  `python3 {review} <workspace> <target> <round> --via claude`.
  If the Claude CLI is not available, start a fresh Codex session for the review with the
  `crew-reviewer` skill and nothing else in its context.
"""


def render_role(path: Path) -> tuple[str, str]:
    meta, body = parse(path.read_text(encoding="utf-8"))
    name = f"crew-{meta.get('name', path.stem)}"
    description = meta.get("description", "")
    text = f"---\nname: {name}\ndescription: {description}\n---\n\n{body}\n\n{codex_notes()}"
    return name, text


def render_pi() -> tuple[str, str]:
    _, body = parse((PLUGIN / "PI.md").read_text(encoding="utf-8"))
    start = parse((PLUGIN / "skills" / "start" / "SKILL.md").read_text(encoding="utf-8"))[1]
    start = start.replace("${CLAUDE_PLUGIN_ROOT}", str(PLUGIN)).replace("$ARGUMENTS", "the user's request")
    description = ("Start or resume a research-crew project that produces a computer-science or "
                   "social-science paper with real experiments or data modeling, acting as the PI. "
                   "Use when the user wants the crew to write a paper or names a crew bench seed.")
    text = (f"---\nname: crew-pi\ndescription: {description}\n---\n\n{start}\n\n---\n\n"
            f"{body.replace('<plugin root>', str(PLUGIN))}\n\n{codex_notes()}")
    return "crew-pi", text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dest", default=str(Path.home() / ".codex" / "skills"))
    parser.add_argument("--force", action="store_true", help="overwrite existing crew-* skills")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    skills = [render_pi()] + [render_role(p) for p in sorted((PLUGIN / "agents").glob("*.md"))]
    dest = Path(args.dest).expanduser()
    for name, text in skills:
        target = dest / name / "SKILL.md"
        if target.exists() and not args.force:
            print(f"ERROR: {target} exists (use --force to overwrite)", file=sys.stderr)
            return 1
    for name, text in skills:
        target = dest / name / "SKILL.md"
        print(f"{'would write' if args.dry_run else 'wrote'} {target}")
        if not args.dry_run:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
    if not args.dry_run:
        print(f"Installed {len(skills)} crew skills. In Codex, ask: use crew-pi to start seed ss-dml-401k")
    return 0


if __name__ == "__main__":
    sys.exit(main())
