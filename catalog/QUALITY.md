# 🔬 Quality & redundancy findings

Observations from indexing all **3,250** bundled `SKILL.md` files (see
[`CATALOG.md`](CATALOG.md) and [`skills.json`](skills.json)). These are
**findings and suggestions for the maintainer**, not edits — curation
decisions live in [`../CURATION.md`](../CURATION.md). All numbers are
reproducible from `catalog/skills.json`; the exact commands are at the bottom.

Snapshot date: **2026-05-31**.

## 1. The headline count is ~22% redundant

| | |
|---|---:|
| `SKILL.md` files on disk (README headline) | **3,250** |
| Distinct skills (by name + body hash) | **2,534** |
| Re-bundled copies | **716** |

Aggregator collections vendor other collections *inside themselves*, so the
same skill is counted many times. The worst offenders:

- `empirical-research-skills` — 978 files, **559** of them re-bundled copies.
- `research-plugins` — 473 files, **464** re-bundled.
- `franklee-academic-research-skills` — 97 files, **53** re-bundled.
- `claude-scientific-writer` — 81 files, only **34** unique.

**Suggestion:** keep the 3,250 headline (it's honest about what's on disk) but
cite the **2,534 unique** figure alongside it so users aren't misled about
breadth. The catalog now surfaces both automatically.

## 2. Name collisions are the real usability hazard ⚠️

**194 skill names** resolve to *different content* across collections — i.e.
the same name means different things depending on which collection an agent
loaded. Examples:

| Skill name | Distinct bodies | Appears in |
|---|---:|---|
| `paper-writing` | 8 | `aris`, `empirical-research-skills`, `phd-skills`, `scienceclaw` |
| `scientific-writing` | 7 | `claude-scientific-writer`, `empirical-research-skills`, `franklee-…`, `nature-paper-skills` |
| `research-grants` | 7 | `claude-scientific-writer`, `empirical-…`, `franklee-…`, `medical-research-skills` |
| `research-ideation` | 7 | `claude-code-my-workflow`, `claude-scholar`, `empirical-…` |
| `grant-proposal` | 6 | `aris`, `empirical-research-skills` |

This matters because most agent runtimes resolve skills **by name**. If a user
installs two collections that both ship a `paper-writing`, which one wins is
undefined and version-dependent. **Suggestion:** document that collections are
meant to be installed *individually*, not all at once, and/or note the top
colliding names in the README so users pick deliberately. The catalog's
per-collection pages already make it easy to see what each `paper-writing`
actually does before choosing.

## 3. 39 skills have no YAML frontmatter

These won't auto-trigger by `name`/`description` in runtimes that require
frontmatter — they're effectively invisible to skill discovery. Concentrated in:

- `empirical-research-skills` (32), `claude-scientific-writer` (3),
  `scienceclaw` (2), `franklee-academic-research-skills` (1), `oneresearchclaw` (1).

The catalog still lists them (it falls back to the directory name + first
paragraph), and flags each with a `no-fm` tag on its collection page.
**Suggestion:** these are upstream issues — worth an upstream issue/PR rather
than a local patch, since the submodules are vendored read-only.

## 4. Only 28% of skills declare a license

**935 / 3,250** skills carry a `license:` field in their frontmatter. The rest
inherit their repo's top-level license (if any) — which is fine, but means a
user copying a single skill out of a collection can't tell its license from the
`SKILL.md` alone. **Suggestion:** a soft recommendation in `CONTRIBUTING.md`
that vendored collections prefer per-skill `license:` fields; not a blocker.

## 5. Placeholder / template skills

One scaffolding skill ships the unedited Anthropic template
(`empirical-research-skills/.../test-skill`, description "A brief description of
what this skill does"). It's flagged `template` in the catalog. **Suggestion:**
harmless, but a candidate for the consistency checker to warn on so future
template leakage is caught.

---

## Reproduce these numbers

```bash
python tools/build_catalog.py          # regenerate skills.json + the catalog
python - <<'PY'
import json, collections
S = json.load(open("catalog/skills.json"))["skills"]
print("files:", len(S), "unique:", len({s["content_hash"] for s in S}))
byname = collections.defaultdict(set)
for s in S: byname[s["name"].lower()].add(s["content_hash"])
print("name collisions (same name, different body):",
      sum(1 for h in byname.values() if len(h) > 1))
print("declare a license:", sum(1 for s in S if s["license"].strip()))
print("no frontmatter:", sum(1 for s in S if not s["has_frontmatter"]))
PY
```
