# Contributing to Auto-Research-Skills

Thanks for helping grow the toolbox! Two ways to contribute:

## 1. Add a tool to the list

Edit [`README.md`](README.md), put the project in the most fitting category, and keep the table format:

```md
| [owner/repo](https://github.com/owner/repo) | ~⭐ | Stack | One-line description. |
```

Keep descriptions to a single sentence. Sort within a category by relevance, not stars.

## 2. Vendor a skill as a submodule

If the project is a reusable *skill* (markdown skills, agent plugins, etc.), vendor it under `skills/`:

```bash
git submodule add --depth 1 https://github.com/owner/repo skills/<short-name>
git commit -m "Add <short-name> skill submodule"
```

Then add a row to the **Bundled Skills** table in the README.

For systems, benchmarks, and lists, use the matching top-level folder:

```bash
git submodule add --depth 1 https://github.com/owner/repo systems/<short-name>
git submodule add --depth 1 https://github.com/owner/repo benchmarks/<short-name>
git submodule add --depth 1 https://github.com/owner/repo lists/<short-name>
```

## Curation bar

- Keep the scope tight: autonomous research, research-oriented agent skills,
  domain-science agents, evaluation benchmarks, and high-signal curated lists.
- Prefer canonical GitHub repos with a clear license, active maintenance, useful
  docs, and roughly 100+ stars. Exceptions are fine when install counts or
  domain coverage make the project unusually valuable.
- If a candidate is promising but uncertain, add it to [`CURATION.md`](CURATION.md)
  first instead of vendoring it immediately.
- Avoid adding broad skill dumps unless they have a clear reason to live in this
  research-focused hub.

## Safety review

Third-party skills can contain instructions and scripts that an agent may later
execute. Before vendoring, read the candidate and check for:

- destructive shell commands or install scripts that pipe remote code into a shell;
- credential or environment-variable harvesting;
- unexpected network calls or hidden binaries;
- prompt-injection style instructions such as hiding behavior from the user;
- unclear license or provenance.

## Local checks

Before opening a PR, run:

```bash
python scripts/check-repo.py
./scripts/count-skills.sh
```

Run `python scripts/update-stars.py` only when intentionally refreshing
[`STARS.md`](STARS.md); the scheduled GitHub Action also refreshes it weekly.

## Guidelines

- One project per PR keeps review easy.
- Link to the canonical repo, not a mirror.
- Star counts are approximate — no need to keep them perfectly current.
- Update both [`README.md`](README.md) and [`README_CN.md`](README_CN.md) when
  changing the public index.
- Be kind. This is a community list.
