# Repo Audit — 2026-10-20 (Q3 2026 refresh)

This audit picks up where [`repo-audit-2026-06-24.md`](repo-audit-2026-06-24.md)
left off, after a quiet summer during which only the weekly star bot touched
`main`. The goal was to catch the hub up with the July–October 2026 wave of
academic-research skills and systems, then make 6,000+ skills *usable* rather
than just *countable*.

## Baseline → end state

| Metric | Start (2026-10-19) | End (2026-10-20) | Source |
|---|---:|---:|---|
| Top-level submodules | 87 (42 / 32 / 4 / 9) | **108** (51 skills / 38 systems / 8 benchmarks / 11 lists) | `scripts/check-repo.py` |
| `SKILL.md` files on disk | 3,433 (pointers from June) | **6,087** | [`../catalog/skills.json`](../catalog/skills.json) |
| Distinct skills (content hash) | ~2,700 | **5,410** | `catalog/skills.json` |
| Colliding skill names | — | 309 | [`../catalog/collisions.json`](../catalog/collisions.json) |
| "Rich" skills (≥3 depth signals) | 442 after bump | **460** | [`../catalog/MATURITY.md`](../catalog/MATURITY.md) |
| Safety findings in `skill`/`script` files | 142 after bump | 163 (+21, all triaged benign) | [`../catalog/SAFETY.md`](../catalog/SAFETY.md) |
| Repo unit tests | 175 | **185** | `make test` |
| Generated reports checked in CI | 4 | **7** | [`../.github/workflows/repo-check.yml`](../.github/workflows/repo-check.yml) |

## What was done

1. **Merged the stranded branch.** Commit `7df561a` on `improve/discovery-suite`
   had never reached `main`. It contains the maturity and frontmatter reports,
   the design-patterns guide and the scored rubric.
2. **Refreshed every submodule** to upstream HEAD (55 of 87 moved). Fixed the
   `academicforge` default-branch rename (`master` → `site-first`), which
   otherwise aborts `git submodule update --remote` for the whole shelf.
3. **Ran a landscape sweep** for July–October 2026 using two parallel
   researchers, with every repo verified through the GitHub API and
   de-duplicated against the hub. Field-level findings went into the
   [Q3 2026 update](landscape-2026.md#q3-2026-update-july--october).
4. **Vendored 21 projects** after license, checkout-size and focused safety
   review. Triage is in [`vendoring-2026-10-20.md`](vendoring-2026-10-20.md).
   Gaps filled:
   - big-lab science skills (DeepMind, NVIDIA BioNeMo);
   - paper search MCP;
   - top-CS-venue and Chinese-language writing;
   - README-first reproduction;
   - research-process discipline;
   - four benchmarks: deep research, project-level autonomy, discovery
     breadth and scientific coding.
5. **Added 11 list-only rows** for projects that matter but can't be vendored
   (non-OSI or no license, 2.5 GB of data, app-not-skill), and **rejected**
   a copycat re-upload and a star-farmed cluster.
6. **Built research-stage starter kits.** [`../tools/build_starter_kits.py`](../tools/build_starter_kits.py)
   generates [`../catalog/STARTER-KITS.md`](../catalog/STARTER-KITS.md) and
   [`../catalog/starter-kits.json`](../catalog/starter-kits.json): 12 stages ×
   5 skills.
   - **Ranking:** depth signals and trigger and license hygiene.
   - **Gates:** canonical copies only, no templates, the safety scanner, one
     skill per collection per stage, and globally unique names.
   - **Install:** one-command `--install <stage|all> --dest <skills dir>`,
     which refuses to overwrite.
   - **Checks:** wired into `make check` and CI with a `--check` drift guard,
     plus 8 tests.
7. **Closed a CI gap.** The frontmatter and maturity reports added in `7df561a`
   were in `make check` but not in the CI catalog job. All three new or merged
   generators are now validated in CI.
8. **Updated the docs:**
   - READMEs: 32 new rows, star-sorted, 🧩 marks, counts, and a starter-kit
     callout.
   - [`../CURATION.md`](../CURATION.md): promotions, second-review queue and
     round status.
   - [`systems-matrix-2026.md`](systems-matrix-2026.md): 6 new 🟢 rows.
   - [`../SECURITY.md`](../SECURITY.md): 2026 skill supply-chain incidents.
   - [`TOOLING.md`](TOOLING.md), [`../catalog/README.md`](../catalog/README.md),
     [`../AGENTS.md`](../AGENTS.md), and the site nav.
9. **Refreshed the network snapshots:** [`../STARS.md`](../STARS.md), the README
   Top 20 and [`../catalog/HEALTH.md`](../catalog/HEALTH.md) (108 repos).

## Findings to act on next

- **`langchain-ai/open_deep_research` is now archived upstream** (`HEALTH.md`).
  Keep it as a reference implementation, but stop recommending it as a live
  system. Consider swapping in a maintained deep-research agent from
  `catalog/DISCOVERY.md` (e.g. `Alibaba-NLP/DeepResearch`, Apache-2.0).
- **License hygiene:** 24 of 108 repos are license-unclear or missing,
  including `openai/mle-bench`, which is now `NOASSERTION`. The upstream issue
  drafts in [`upstream-license-requests-2026-06-24.md`](upstream-license-requests-2026-06-24.md)
  are still unfiled.
- **Selection over breadth:** 59% of skills remain bare prompts (`MATURITY.md`),
  and the per-journal packs dominate raw counts. Future rounds should favor
  depth (evals, scripts, references) over volume, and could weight the starter
  kits by install telemetry from skills.sh once a stable API exists.
- **Next candidates:**
  - `mims-harvard/ToolUniverse`, pending a collision estimate;
  - `InternScience/ResearchClawBench`, if upstream splits its data out;
  - `ClawBio/ClawBio`, pending a license.
- **Multi-agent hygiene:** three Claude sessions edited this checkout
  concurrently during this audit. Shared-index races (`index.lock`) broke one
  batch of `git submodule add`. For multi-session work, prefer separate
  worktrees, or announce file ownership first, as [`../AGENTS.md`](../AGENTS.md)
  asks.
