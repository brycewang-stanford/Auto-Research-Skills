# Skill Design Patterns

*What the strongest research-skill collections in this hub do well — distilled
into patterns you can imitate, and into the criteria this hub uses when it
curates.*

This guide is derived from a close read of two of the most production-grade
collections vendored here:

- [`skills/nature-skills`](../skills/nature-skills) — Nature-grade academic
  phrasing + scientific figure workflows ([Yuan1z0825/nature-skills](https://github.com/Yuan1z0825/nature-skills)).
- [`skills/academic-research-skills`](../skills/academic-research-skills) — a
  full research → write → review → revise → finalize pipeline
  ([Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)).

It has two audiences:

- **Skill authors** looking for concrete structure to copy.
- **Hub maintainers** deciding what is worth vendoring — the "Curation
  signals" callouts map each pattern to something the catalog tooling can (or
  should) measure. See also [`../CURATION.md`](../CURATION.md).

> These are *patterns*, not hard requirements. A tight 40-line `SKILL.md` with
> no `references/` can be excellent. The point is to recognize the moves that
> make a skill robust, cheap to run, and hard to misuse — and to reward them.

---

## 1. A shared, non-skill layer for content used by ≥2 skills

`nature-skills` keeps a `skills/_shared/` directory that is **explicitly not a
skill** — it has no `SKILL.md` and is never registered with the loader. It
exists so multiple skills can reference the same taxonomy, ethics guidance, or
journal-format notes without copy-paste drift.

Its governance rule is the part worth stealing (`skills/nature-skills/skills/_shared/README.md`):

- Promote content to `_shared/` **only when ≥2 skills need it**.
- Put the **definition layer** there (a paper-type taxonomy, an ethics
  traffic-light), never the **action layer**. Two skills can share the *same*
  vocabulary and still apply *different* actions on top of it — `nature-writing`
  adds construction rules, `nature-polishing` adds diagnostic rules, both over
  one shared taxonomy.

**Why it matters:** it removes duplication without over-coupling skills, and it
keeps each skill's own logic local and legible.

> **Curation signal:** a `_shared/` (or equivalent) layer *plus* skills that
> actually reference it is a sign of a maintained collection, not a dumped bag
> of prompts. Beware the failure mode too: a packaged copy that drops `_shared/`
> silently breaks the skills that load it (see §7).

---

## 2. Manifest-driven routing: the `SKILL.md` is a thin router

`nature-writing` and `nature-polishing` keep `SKILL.md` short and push the real
logic into a declarative `manifest.yaml` + a `static/fragments/` tree. The
manifest declares orthogonal **axes** (`paper_type` / `section` / `language` /
`journal`); each axis value maps to one fragment file that is loaded **only when
detected**.

The router's own words (`skills/nature-skills/skills/nature-writing/SKILL.md`):

> "Do not try to apply the drafting logic from memory or from this router.
> Always load fragments from disk as described below."

Two payoffs the author calls out directly:

- **Cheap invocations** — "only the fragments relevant to this draft enter
  context, instead of the full multi-thousand-line reference set."
- **Cheap extension** — "adding a new journal style … is one new file plus one
  manifest line."

**Pattern:** when a skill has to handle a matrix of cases (journals × sections ×
languages), don't inline all of it. Make `SKILL.md` a router that detects the
axis values, states them back to the user, and loads only the matching
fragments from disk.

> **Curation signal:** presence of `manifest.yaml` + `static/`/`fragments/` +
> `references/` is a strong maturity signal — the collection has invested in
> token economy and maintainability.

---

## 3. Acceptance criteria as first-class, on-disk assets

The best skills do not leave "did this succeed?" to the model's improvisation.
They ship the rubric next to the skill:

- **QA contracts** — `skills/nature-skills/skills/nature-figure/references/qa-contract.md`
  is a pre-submission checklist (final size 89 mm / 183 mm, text 5–7 pt,
  editable text, no rainbow colormap, statistics completeness, image
  integrity) with fill-in templates.
- **Scoring rubrics** — `skills/nature-skills/skills/nature-response/tests/rubric.md`
  scores output on 6 dimensions (Completeness / Traceability / Factuality /
  Tone / Actionability / Nature-fit), each with a Pass/Fail criterion.
- **Eval sets** — `evals/evals.json` files pair a prompt with an
  `expected_output` so behavior can be checked, not just asserted.

`academic-research-skills` takes this furthest: gold sets under `evals/gold/<task>/`
with declared thresholds (`accuracy >= 0.90` aggregate, per-class `>= 0.85`) and
a claim-audit calibration with fixed acceptance gates
(`DEFAULT_FNR_THRESHOLD = 0.15`, `DEFAULT_FPR_THRESHOLD = 0.10`) — and a rule
that *tightening a threshold is a spec bump*, not a silent edit.

**Pattern:** write the acceptance test down. A `references/qa-contract.md`, a
`tests/rubric.md`, or an `evals/*.json` turns "quality" from vibes into an
artifact a reviewer (human or CI) can run.

> **Curation signal:** `evals/`, `tests/`, and a QA-contract-style file are
> exactly the depth signals [`../catalog/MATURITY.md`](../catalog/MATURITY.md)
> counts. They separate a *tested* skill from a bare prompt.

---

## 4. Anti-fabrication discipline built into the instructions

Both collections refuse to let "missing evidence" become a hallucination.

- **Structured "I don't have this" outputs** — instead of inventing content,
  emit a placeholder (`AUTHOR_INPUT_NEEDED`) or a graded support label
  (`strong-support` / `partial-support` / `background-support`).
- **Red lines** — `nature-response`'s "Red lines" forbid fabricating line
  numbers, figures, or citations, and forbid using time/cost as an excuse to
  skip a requested experiment.
- **Citation locators + claim audit** — `academic-research-skills` attaches a
  locator anchor to every citation (`<!--anchor:quote:…-->`) and has an opt-in
  audit (`ARS_CLAIM_AUDIT=1`) that fetches the source and judges whether the
  claim is actually supported, refusing to emit output on a `HIGH-WARN` class.
- **Anti-sycophancy** — a Devil's-Advocate agent scores rebuttals 1–5 with "no
  concession below 4/5," so the pipeline can't be flattered into agreement.

The one-liner that captures the whole stance
(`skills/nature-skills/skills/_shared/core/ethics.md`):

> "The main danger is not that AI cannot write. The main danger is that it can
> write incorrectly with great confidence."

**Pattern:** name the failure modes in the prompt and give the model a
*structured* way to say "not enough evidence" — a placeholder token, a graded
label, a refuse-to-emit gate — rather than trusting it to volunteer uncertainty.

> **Curation signal:** during safety/quality review, a skill that ships explicit
> "red lines" and placeholder conventions is lower-risk than one that promises
> fluent output with no guardrails. This complements
> [`../catalog/SAFETY.md`](../catalog/SAFETY.md).

---

## 5. Blocking clarification gates before expensive work

Cheap correction beats expensive cleanup. `nature-figure` asks "Python or R?"
and **stops** — once chosen, the other backend is forbidden for that run
(backend exclusivity). `nature-writing`/`nature-polishing` require the router to
**state the detected axis values back to the user in one line** before drafting.

`academic-research-skills` formalizes this into two kinds of checkpoint:

- **Decision-heavy checkpoints** (🧑) — the user picks a branch or accepts a
  substantive decision.
- **Post-stage confirmation checkpoints** (✓) — machine-verified *first*, then
  confirmed by the user; "they are not skipped."

**Pattern:** put a one-line, low-cost gate in front of any branch that is
expensive to redo (backend choice, detected scope, integrity check). Verify
mechanically where you can, then have the human confirm.

---

## 6. Honest, declarative annotations — don't claim more than you enforce

`academic-research-skills` annotates each skill with a `data_access_level`
(`raw` → `redacted` → `verified_only`) — and then says so plainly in
`docs/ARCHITECTURE.md`:

> "`data_access_level` is a **declarative** annotation, not a runtime-enforced
> permission system."

The same honesty shows up in its `repro_lock` ("not read by the gate at runtime
— post-hoc documentation"). It documents the *intent* and enforces what it
actually can (a CI lint checks the field exists; the real enforcement is the
integrity gate + human review), without pretending the annotation is a sandbox.

**Pattern:** label intent explicitly, but state what is and isn't enforced. An
annotation the reader can trust is worth more than one that overpromises.

> **Curation signal:** collections that are candid about their limits
> (`SECURITY.md` with an out-of-scope section, "this is a proposal not a
> standard") are easier to vendor responsibly than ones that market themselves
> as fully autonomous and bug-free.

---

## 7. Packaging & versioning discipline (and its failure modes)

Good moves seen here:

- **Multi-platform packaging** — `nature-skills` ships a `.claude-plugin/`
  marketplace manifest *and* a Codex `.codex-plugin/plugin.json` with interface
  metadata (display name, default prompts, brand color, icon).
- **A single source of truth for modes** — `academic-research-skills`'s
  `MODE_REGISTRY.md`: "When adding or modifying modes, update this file first."
- **CI headers as post-mortems** — every workflow in
  `academic-research-skills/.github/workflows/` opens with *why it exists* and
  the real incident that motivated it (a 6-hour hotfix, a 30-commit squash that
  hid 4 spec deviations). This is the single most imitable practice in either
  repo: it turns institutional memory into code.
- **Two-layer invariants** — JSON Schema enforces structure; a Python lint
  enforces the conditional matrix the schema can't express, and the schema's
  own description says so.

The failure modes to avoid (both observed here):

- **Packaging drift** — `nature-skills`'s packaged copy under
  `plugins/nature-skills/skills/` omits `_shared/` and some `static/`
  fragments, so a router skill installed from the package can silently
  break its `always_load: ../_shared/…` references. If you maintain a
  packaged mirror, add a check that keeps it in sync with source.
- **Inconsistent frontmatter** — some skills carry `version`/`author`/`status`,
  others don't; versions jump around (6.0.0 vs 1.0.0 vs 0.1.0) with no schema.
  A frontmatter schema + conformance check catches this.
- **Machine-specific eval paths** — an `evals.json` that references
  `/Users/<author>/…pdf` can't be reproduced by anyone else. Keep eval fixtures
  in-repo and relative.

> **Curation signal:** the hub checks frontmatter conformance in
> [`../catalog/FRONTMATTER.md`](../catalog/FRONTMATTER.md) and surfaces the
> "declares a license" gap in [`../catalog/QUALITY.md`](../catalog/QUALITY.md).

---

## Pattern → hub-tooling map

| Pattern | Where the hub measures / documents it |
|---|---|
| Shared non-skill layer (§1) | maturity signals in [`../catalog/MATURITY.md`](../catalog/MATURITY.md) |
| Manifest-driven routing (§2) | maturity signals (`manifest.yaml`, `references/`) |
| Acceptance criteria on disk (§3) | `evals/` + `tests/` depth signals in [`../catalog/MATURITY.md`](../catalog/MATURITY.md) |
| Anti-fabrication (§4) | [`../catalog/SAFETY.md`](../catalog/SAFETY.md) + review notes |
| Clarification gates (§5) | qualitative review (see [`../CURATION.md`](../CURATION.md)) |
| Honest annotations (§6) | [`SECURITY.md`](../SECURITY.md) + positioning in review |
| Packaging / frontmatter (§7) | [`../catalog/FRONTMATTER.md`](../catalog/FRONTMATTER.md), license row in [`../catalog/QUALITY.md`](../catalog/QUALITY.md) |

---

*Maintainers: when a newly vendored collection shows several of these patterns,
say so in its [`../CURATION.md`](../CURATION.md) review note — it is the
qualitative half of the depth score the catalog computes automatically.*
