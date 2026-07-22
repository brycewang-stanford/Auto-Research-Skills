# Security Policy

Auto-Research-Skills is a **curation hub**: it vendors third-party skill
collections, systems, benchmarks, and lists as git submodules, and ships a
small amount of first-party Python tooling to catalog and audit them. This
policy states what the hub is responsible for, what it is not, and how to report
a problem. The framing is adapted from the exemplar
[`skills/academic-research-skills`](skills/academic-research-skills)'s
`SECURITY.md`.

## The core threat model: vendored skills are executable supply-chain inputs

A `SKILL.md` is an instruction bundle an agent will *execute*. Treating vendored
collections as untrusted third-party code is the whole point of this hub's
tooling. See [`CURATION.md`](CURATION.md) and
[`catalog/SAFETY.md`](catalog/SAFETY.md).

## In scope

Report these against **this repository** (the hub's own code and curation):

- **First-party tooling flaws** — a bug in `tools/` or `scripts/` (catalog,
  safety scan, doc/site checks) that produces wrong or misleading output,
  crashes on hostile input, or could be made to write outside the repo.
- **Curation-process gaps** — a vendored submodule that should have been caught
  by the review checklist: credential harvesting (`echo $SECRET`), `curl | sh`
  bootstrap, `rm -rf`/`mkfs` outside a refusal guard, hidden network calls,
  obfuscated payloads, or prompt-injection instructions that tell the consuming
  agent to hide behavior from its user.
- **Safety-scanner blind spots** — a class of dangerous pattern that
  `scripts/scan-skill-safety.py` fails to flag (a false negative). These are the
  most valuable reports; they close a gap for every future candidate.
- **Catalog integrity** — a way to make the generated catalog understate risk
  (e.g. frontmatter crafted so a skill's real `name`/`description` is hidden from
  the parser but still triggers in a runtime).

## Out of scope

- **Vulnerabilities in vendored upstream projects themselves.** Report those to
  the upstream repository. If an upstream issue means a collection should be
  pulled or flagged here, open an issue on this hub *in addition*.
- **Skill output quality** — hallucinated citations, wrong analysis, or weak
  writing from a vendored skill are research-quality limitations, not
  vulnerabilities in this hub.
- **The hub does not sandbox or execute skills.** The catalog is a *read* layer
  (see [`catalog/README.md`](catalog/README.md)); it never runs vendored code.
  Any agent that loads these skills is responsible for its own execution
  sandboxing. The declarative flags this hub emits (safety findings, maturity,
  frontmatter conformance) are **advisory signals, not an enforcement boundary** —
  the same honesty the design-patterns guide asks of skill authors
  ([`docs/skill-design-patterns.md`](docs/skill-design-patterns.md) §6).

## Reporting

- **Sensitive reports** (an active credential leak or injection in a vendored
  skill): use GitHub's private vulnerability reporting on this repository, or
  email the maintainer listed in the repo profile. Please do not open a public
  issue that republishes a working exploit.
- **Everything else** (scanner blind spots, tooling bugs, curation
  suggestions): a normal GitHub issue is ideal, ideally with the offending path
  and the `scripts/scan-skill-safety.py` output.

When you report a vendored-skill risk, include the submodule path, the specific
`SKILL.md`/script line, and why it is dangerous in an agent-executed context.
That maps directly onto the review checklist in [`CURATION.md`](CURATION.md).

## What we do on a valid report

1. Reproduce with `make safety-scan` / `python3 scripts/check-repo.py`.
2. For a scanner blind spot: add a detection rule **and** a regression test
   under `tests/`, then regenerate [`catalog/SAFETY.md`](catalog/SAFETY.md).
3. For a bad vendored collection: flag it in [`CURATION.md`](CURATION.md), and
   remove the submodule if the risk is not isolated to non-executable docs.
4. Record the decision (reviewer, date, commit inspected, verdict) in the
   relevant `docs/` review log.
