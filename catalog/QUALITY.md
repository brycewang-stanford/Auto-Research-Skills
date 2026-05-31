# 🔬 Quality & redundancy findings

Observations from indexing all **3,250** bundled `SKILL.md` files (see
[`CATALOG.md`](CATALOG.md) and [`skills.json`](skills.json)). These are
**findings and suggestions for the maintainer**, not edits — curation
decisions live in [`../CURATION.md`](../CURATION.md). All numbers are
reproducible from `catalog/skills.json`; the exact commands are at the bottom.

Snapshot date: **2026-05-31**.

## 1. The headline count is ~22% redundant

| Metric | Count |
|---|---:|
| `SKILL.md` files on disk (README headline) | **3,250** |
| Distinct skills (by name + body hash) | **2,521** |
| Re-bundled copies | **729** |

Aggregator collections vendor other collections *inside themselves*, so the
same skill is counted many times. The worst offenders (copies also present in
another collection):

- `empirical-research-skills` — 978 files, **571** re-bundled.
- `research-plugins` — 473 files, **464** re-bundled.
- `franklee-academic-research-skills` — 97 files, **53** re-bundled.
- `claude-scientific-writer` — 81 files, only **34** unique.

**Suggestion:** keep the 3,250 headline (it's honest about what's on disk) but
cite the **2,521 unique** figure alongside it so users aren't misled about
breadth. The catalog now surfaces both automatically.

## 2. Name collisions are the real usability hazard ⚠️

**192 skill names** resolve to *different content* across collections — i.e.
the same name means different things depending on which collection an agent
loaded. Examples:

| Skill name | Distinct bodies | Appears in |
|---|---:|---|
| `paper-writing` | 8 | `aris`, `empirical-research-skills`, `phd-skills`, `scienceclaw` |
| `paper-write` | 8 | `aris`, `empirical-research-skills` |
| `auto-review-loop` | 8 | `aris`, `empirical-research-skills` |
| `paper-plan` | 8 | `aris`, `empirical-research-skills` |
| `research-grants` | 7 | `claude-scientific-writer`, `empirical-…`, `franklee-…`, `medical-research-skills` |
| `research-ideation` | 7 | `claude-code-my-workflow`, `claude-scholar`, `empirical-…` |

This matters because most agent runtimes resolve skills **by name**. If a user
installs two collections that both ship a `paper-writing`, which one wins is
undefined and version-dependent. **Suggestion:** document that collections are
meant to be installed *individually*, not all at once, and/or note the top
colliding names in the README so users pick deliberately. The catalog's
per-collection pages make it easy to see what each `paper-writing` actually
does before choosing.

## 3. Watermark banners hide frontmatter from strict loaders ⚠️

While indexing, **28 skills** turned out to carry a watermark HTML comment
(e.g. a `CoPaper.AI 收集整理` banner) **prepended above** the `---` frontmatter
delimiter. A naive parser — or an agent runtime that requires frontmatter on
line 1 — sees the comment first and treats the skill as having **no
`name`/`description` at all**, so it silently won't trigger.

The catalog handles this (it strips a leading comment block before parsing, and
recovered all 28). But for the agents that *consume* these skills this is a real
defect. **Suggestion:** flag injected-watermark frontmatter in the
consistency/safety checker, and consider an upstream issue — a prepended
watermark that breaks skill discovery is also a mild supply-chain smell worth
noting in `CURATION.md`.

## 4. 11 skills genuinely have no frontmatter

After recovering the watermarked ones, **11** files still ship no YAML
frontmatter, so they won't auto-trigger by `name`/`description` in runtimes that
require it:

- `claude-scientific-writer` (3 × `scholar-evaluation`),
  `empirical-research-skills` (4), `scienceclaw` (2),
  `franklee-academic-research-skills` (1), `oneresearchclaw` (1).

The catalog still lists them (falling back to the directory name + first
paragraph) and tags each `no-fm`. These are upstream issues — better as an
upstream PR than a local patch, since submodules are vendored read-only.

## 5. Only 29% of skills declare a license

**941 / 3,250** skills carry a `license:` field in their frontmatter. The rest
inherit their repo's top-level license (if any) — fine, but it means a user
copying a single skill out of a collection can't tell its license from the
`SKILL.md` alone. **Suggestion:** a soft recommendation in `CONTRIBUTING.md`
that vendored collections prefer per-skill `license:` fields; not a blocker.

## 6. Placeholder / template skill

One scaffolding skill ships the unedited Anthropic template
(`empirical-research-skills/.../test-skill`, description "A brief description of
what this skill does"), flagged `template` in the catalog. Harmless, but a good
candidate for the consistency checker to warn on so future template leakage is
caught.

---

## Reproduce these numbers

```bash
python tools/build_catalog.py          # regenerate skills.json + the catalog
python - <<'PY'
import json, collections
S = json.load(open("catalog/skills.json"))["skills"]
print("files:", len(S), "unique:", len({s["content_hash"] for s in S}))
byname = collections.defaultdict(set)
ncoll = collections.defaultdict(set)
for s in S:
    byname[s["name"].lower()].add(s["content_hash"])
    ncoll[s["name"].lower()].add(s["collection"])
print("cross-collection name collisions:",
      sum(1 for n, h in byname.items() if len(h) > 1 and len(ncoll[n]) > 1))
print("declare a license:", sum(1 for s in S if s["license"].strip()))
print("no frontmatter:", sum(1 for s in S if not s["has_frontmatter"]))
PY
```
