# Second-Review Log — 2026-06-23

Executes the **Second-Review Queue** in [`../CURATION.md`](../CURATION.md).
Each candidate was checked live with the GitHub API, cloned to a scratch
directory, and scanned with the repo's own tool focused on executable contexts:

```bash
python3 scripts/scan-skill-safety.py <scratch-clone> \
    --min-severity high --max-findings 0 --fail-on none \
    --context skill,script,other
```

Reviewer: automated maintenance pass. Metadata refreshed 2026-06-23.
"Focused findings" counts only `skill`/`script`/`other` contexts (install-doc
and example hits are excluded, since those rarely execute).

## Verdicts at a glance

| Candidate | Stars | License | Focused findings | Verdict |
|---|---:|---|---|---|
| [54yyyu/zotero-mcp](https://github.com/54yyyu/zotero-mcp) | 3,964 | MIT | 1 high (false positive) | **vendor-ready** |
| [GPTomics/bioSkills](https://github.com/GPTomics/bioSkills) | 945 | MIT | 0 | **vendor-candidate** (breadth) |
| [ClawBio/ClawBio](https://github.com/ClawBio/ClawBio) | 993 | MIT | 3 crit (benign) / 14 high | **vendor-candidate** (focused) |
| [jaechang-hits/SciAgent-Skills](https://github.com/jaechang-hits/SciAgent-Skills) | 210 | CC BY 4.0 | 1 crit (benign) / 9 high | **hold** (license fit) |
| [EvoScientist/EvoSkills](https://github.com/EvoScientist/EvoSkills) | 398 | Apache-2.0 | 3 high | **hold** (secret exposure) |
| [zsyggg/paper-craft-skills](https://github.com/zsyggg/paper-craft-skills) | 552 | none | 0 | **hold** (no license) |

Recommended next vendoring action: **zotero-mcp** (cleanest, fills the Zotero
gap), then exactly one bioinformatics collection — lead with **bioSkills**
(scan-clean, zero cross-collection name collisions) or **ClawBio** if a smaller
curated set is preferred. One project per PR; do not batch.

---

## 1. zotero-mcp — vendor-ready

- **Metadata:** 3,964★, MIT, Python, pushed 2026-06-22, not archived.
- **Shape:** an MCP server (`src/`, `pyproject.toml`, `Dockerfile`), **0
  `SKILL.md` files** — the same category as the already-vendored
  [`skills/arxiv-mcp-server`](../skills/arxiv-mcp-server). Vendoring adds a tool,
  not catalog skills.
- **Safety:** the lone focused finding is
  `src/zotero_mcp/setup_helper.py:695`, `print(f" API Key: {_obfuscate_sensitive(api_key)}")`
  — it prints an **obfuscated** key for confirmation, i.e. good practice. False
  positive.
- **Gap fit:** the hub has no reference-manager integration today; this fills
  the Zotero gap cleanly and matches the existing MCP-server precedent.
- **Verdict: vendor-ready.** When the catalog/README files are quiescent:
  `git submodule add --depth 1 https://github.com/54yyyu/zotero-mcp skills/zotero-mcp`,
  then update both READMEs + STARS and run `make catalog safety-report quality-report check`.

## 2. bioSkills — vendor-candidate (breadth)

- **Metadata:** 945★, MIT, Python, pushed 2026-06-20, not archived.
- **Size:** 547 `SKILL.md` files (~25M).
- **Safety:** focused scan is **completely clean** (0 findings) — notable for a
  collection this large.
- **Collision estimate:** **0** of its 547 skill names collide with names
  already in `catalog/skills.json`. The bioinformatics vocabulary is distinct
  from the hub's paper-writing-heavy catalog, so the usual aggregator-collision
  hazard is low here.
- **Caveat:** internal redundancy across 547 skills is unmeasured; expect the
  catalog's `unique_skills` to absorb some. Breadth is the selling point and the
  risk.
- **Verdict: vendor-candidate.** Strong breadth pick. If chosen, note the size
  in the README row.

## 3. ClawBio — vendor-candidate (focused / reproducible-first)

- **Metadata:** 993★, MIT, Python, pushed 2026-06-23 (today), not archived.
  "Bioinformatics-native, local-first, reproducible, built on OpenClaw."
- **Size:** 90 `SKILL.md` files, but the checkout is ~204M (bundles data /
  fixtures) — vendor `--depth 1` and watch the clone weight.
- **Safety:** 3 criticals, all the **official Nextflow installer**
  (`curl -s https://get.nextflow.io | bash`) in
  `skills/wgs-prs/SKILL.md`, `clawbio/common/sarek.py`, and a bioconda
  `meta.yaml` — legitimate tool bootstrap, same class as the uv/astral
  installers already common in the catalog. The 14 high findings are
  credential-help text, not leaks.
- **Verdict: vendor-candidate.** The reproducible-first, 90-skill scope is a
  cleaner single bioinformatics pick than bioSkills's 547. Choose one.

## 4. SciAgent-Skills — hold (license fit)

- **Metadata:** 210★, pushed 2026-06-15, not archived, 202 `SKILL.md` files,
  "BixBench 92.0% accuracy."
- **License:** the GitHub API reports `NOASSERTION`; the `LICENSE` file is
  **Creative Commons Attribution 4.0**. CC BY is a *content* license that
  Creative Commons itself discourages for software/code. It is permissive
  (attribution), but it is the wrong instrument for a Python + markdown skill
  library and muddies per-skill reuse.
- **Safety:** 1 critical = the Nextflow installer (benign); 9 high are help
  text / credential references.
- **Verdict: hold.** Ask upstream to (dual-)license under MIT/Apache for the
  code before vendoring; otherwise consider list-only.

## 5. EvoSkills — hold confirmed (secret exposure not fixed)

- **Metadata:** 398★, Apache-2.0, pushed 2026-06-19, not archived, 16 skills.
- **Blocking issue (still present):** `skills/nano-banana/SKILL.md:37` instructs
  `echo $GOOGLE_API_KEY`, which prints the **secret's value** into
  agent-visible output. This is the exact concern that put EvoSkills on hold in
  `CURATION.md`, and it is **not fixed** as of this review.
- The 3 focused scanner findings (`nano-banana/scripts/*.py`) are usage-help
  `print()`s, not leaks.
- **Verdict: hold.** Do not vendor until the `echo $GOOGLE_API_KEY` guidance is
  removed or moved to non-executable docs.
- **Scanner gap uncovered:** our `credential-print` rule does **not** flag
  `echo $GOOGLE_API_KEY` — the `\bAPI[_-]?KEY\b` word boundary misses prefixed
  env vars like `GOOGLE_API_KEY`. Worth tightening so the scanner catches the
  very pattern that justifies this hold.

## 6. paper-craft-skills — hold (no license)

- **Metadata:** 552★, pushed 2026-05-29, not archived, 3 skills
  (`paper-deck`, `paper-comic`, `paper-analyzer`).
- **License:** **no LICENSE file** and the GitHub API reports none. Vendoring
  unlicensed code leaves users without redistribution rights.
- **Safety:** focused scan clean.
- **Verdict: hold/reject.** The paper→comic/deck niche is genuinely novel;
  revisit only if upstream adds an OSI-approved license.
