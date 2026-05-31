#!/usr/bin/env python3
"""Heuristic safety scan for vendored agent skills.

This is an offline reviewer-assist tool. It does not prove a skill is safe;
it highlights patterns that deserve manual review before vendoring or updating
third-party skill collections.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SEVERITY = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
}

TEXT_SUFFIXES = {
    "",
    ".bash",
    ".cfg",
    ".cmd",
    ".conf",
    ".css",
    ".env",
    ".fish",
    ".ini",
    ".ipynb",
    ".js",
    ".json",
    ".jsx",
    ".md",
    ".mdx",
    ".mjs",
    ".ps1",
    ".py",
    ".rb",
    ".rs",
    ".sh",
    ".toml",
    ".ts",
    ".tsx",
    ".txt",
    ".yaml",
    ".yml",
    ".zsh",
}


@dataclass(frozen=True)
class Rule:
    rule_id: str
    severity: str
    pattern: re.Pattern[str]
    reason: str


@dataclass(frozen=True)
class Finding:
    severity: str
    rule_id: str
    path: str
    line: int
    match: str
    reason: str


RULES = [
    Rule(
        "remote-shell-pipe",
        "critical",
        re.compile(
            r"\b(?:curl|wget)\b[^\n|]{0,240}\|\s*"
            r"(?:sudo\s+)?(?:sh|bash|zsh|python3?|perl|ruby)\b",
            re.IGNORECASE,
        ),
        "Remote downloads piped directly into an interpreter need explicit review.",
    ),
    Rule(
        "powershell-iex",
        "critical",
        re.compile(
            r"\b(?:irm|iwr|Invoke-WebRequest|Invoke-RestMethod)\b[^\n|]{0,240}"
            r"\|\s*(?:iex|Invoke-Expression)\b",
            re.IGNORECASE,
        ),
        "PowerShell download-and-execute patterns are high-risk installer behavior.",
    ),
    Rule(
        "destructive-root-delete",
        "critical",
        re.compile(
            r"\brm\s+-[A-Za-z]*r[A-Za-z]*f[A-Za-z]*\s+(?:/\*|/)(?=$|[\s;&|])",
            re.IGNORECASE,
        ),
        "Recursive deletion from filesystem root should never appear in a skill.",
    ),
    Rule(
        "destructive-system-device",
        "critical",
        re.compile(r"\b(?:mkfs\.[A-Za-z0-9]+|dd\s+if=.*\s+of=/dev/)", re.IGNORECASE),
        "Disk formatting or raw device writes are destructive system operations.",
    ),
    Rule(
        "credential-print",
        "high",
        re.compile(
            r"\b(?:print|echo|console\.log|logger\.(?:info|debug)|logging\.(?:info|debug))"
            r"\b[^\n]{0,160}\b(?:API[_-]?KEY|TOKEN|SECRET|PASSWORD)\b",
            re.IGNORECASE,
        ),
        "Credentials should not be printed or logged into agent-visible output.",
    ),
    Rule(
        "credential-file-reference",
        "medium",
        re.compile(
            r"(?:~|\$HOME|/home/[^/\s]+|/Users/[^/\s]+)/\."
            r"(?:ssh|aws|config|kube)|\bid_rsa\b|\b\.env\b|"
            r"\b(?:OPENAI_API_KEY|ANTHROPIC_API_KEY|GITHUB_TOKEN|AWS_SECRET_ACCESS_KEY)\b",
            re.IGNORECASE,
        ),
        "Credential file or secret references need review when paired with logging or exfiltration.",
    ),
    Rule(
        "concealment-instruction",
        "high",
        re.compile(
            r"(?:do not|don't)\s+(?:tell|show|mention|reveal)[^\n]{0,100}"
            r"(?:user|developer)|\bsecretly\b|\bhide\s+(?:this|your|the)\s+"
            r"(?:behavior|instruction|action)\b",
            re.IGNORECASE,
        ),
        "Instructions that conceal behavior from the user are prompt-injection risk.",
    ),
    Rule(
        "prompt-override",
        "medium",
        re.compile(
            r"\bignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions\b|"
            r"\bsystem\s+prompt\b|\bdeveloper\s+message\b",
            re.IGNORECASE,
        ),
        "Prompt override language should be checked in third-party instructions.",
    ),
    Rule(
        "world-writable-permissions",
        "medium",
        re.compile(r"\bchmod\s+(?:-R\s+)?777\b", re.IGNORECASE),
        "World-writable permissions are rarely appropriate in installer scripts.",
    ),
    Rule(
        "privileged-package-operation",
        "medium",
        re.compile(r"\bsudo\s+(?:pip|npm|gem|apt|apt-get|brew|cp|mv|rm)\b", re.IGNORECASE),
        "Privileged package or filesystem operations should be justified.",
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "roots",
        nargs="*",
        default=["skills"],
        help="Directories to scan, relative to repo root unless absolute.",
    )
    parser.add_argument(
        "--min-severity",
        choices=SEVERITY,
        default="high",
        help="Only report findings at this severity or above.",
    )
    parser.add_argument(
        "--fail-on",
        choices=["none", *SEVERITY.keys()],
        default="critical",
        help="Exit non-zero if any finding reaches this severity.",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=750_000,
        help="Skip individual files larger than this many bytes.",
    )
    parser.add_argument(
        "--max-findings",
        type=int,
        default=200,
        help="Maximum findings to print before truncating output.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON instead of human-readable text.",
    )
    return parser.parse_args()


def resolve_root(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def is_probably_text(path: Path, max_bytes: int) -> bool:
    if path.suffix.lower() not in TEXT_SUFFIXES:
        return False
    try:
        return path.stat().st_size <= max_bytes
    except OSError:
        return False


def iter_files(roots: list[Path], max_bytes: int) -> list[Path]:
    files: list[Path] = []
    for root in roots:
        if root.is_file() and is_probably_text(root, max_bytes):
            files.append(root)
            continue
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.is_file() and is_probably_text(path, max_bytes):
                files.append(path)
    return files


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return None
    except OSError:
        return None


def line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def relative_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def scan_file(path: Path, min_severity: str) -> list[Finding]:
    text = read_text(path)
    if text is None:
        return []

    findings: list[Finding] = []
    threshold = SEVERITY[min_severity]
    for rule in RULES:
        if SEVERITY[rule.severity] < threshold:
            continue
        for match in rule.pattern.finditer(text):
            snippet = " ".join(match.group(0).split())
            findings.append(
                Finding(
                    severity=rule.severity,
                    rule_id=rule.rule_id,
                    path=relative_path(path),
                    line=line_number(text, match.start()),
                    match=snippet[:180],
                    reason=rule.reason,
                )
            )
    return findings


def sort_key(finding: Finding) -> tuple[int, str, int, str]:
    return (-SEVERITY[finding.severity], finding.path, finding.line, finding.rule_id)


def print_text(findings: list[Finding], max_findings: int) -> None:
    if not findings:
        print("OK: no matching high-risk skill patterns found")
        return

    shown = findings if max_findings <= 0 else findings[:max_findings]
    for finding in shown:
        print(
            f"{finding.severity.upper():8} {finding.path}:{finding.line} "
            f"[{finding.rule_id}] {finding.match}"
        )
        print(f"         {finding.reason}")
    if max_findings > 0 and len(findings) > max_findings:
        print(f"... truncated {len(findings) - max_findings} additional findings")

    counts: dict[str, int] = {}
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    summary = ", ".join(f"{severity}={counts[severity]}" for severity in sorted(counts))
    print(f"SUMMARY: {len(findings)} findings ({summary})")


def main() -> int:
    args = parse_args()
    roots = [resolve_root(value) for value in args.roots]
    files = iter_files(roots, args.max_bytes)
    findings: list[Finding] = []
    for path in files:
        findings.extend(scan_file(path, args.min_severity))
    findings.sort(key=sort_key)

    try:
        if args.json:
            shown = findings if args.max_findings <= 0 else findings[: args.max_findings]
            print(json.dumps([asdict(finding) for finding in shown], indent=2))
        else:
            print_text(findings, args.max_findings)
    except BrokenPipeError:
        return 0

    if args.fail_on != "none":
        fail_threshold = SEVERITY[args.fail_on]
        if any(SEVERITY[finding.severity] >= fail_threshold for finding in findings):
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
