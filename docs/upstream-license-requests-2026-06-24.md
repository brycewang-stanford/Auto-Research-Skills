# Upstream license requests — drafts (2026-06-24)

`catalog/HEALTH.md` flags **5 vendored systems with no upstream license**. A repo
with no license is *all-rights-reserved by default* — it cannot be legally
redistributed or built upon, which blocks the reproduce-and-extend half of the
"reproducibility" story (see
[`reproducibility-2026-06-23.md`](reproducibility-2026-06-23.md)).

Below are ready-to-post issue drafts, one per repo. **These are drafts for a
maintainer to file** — this hub does not post to third-party repositories
automatically. Post them from your own GitHub account (or via
`gh issue create -R <repo> -t "<title>" -b "<body>"`), and tweak the tone to
taste.

| Repo | Bundled at | Stars | gh command |
|---|---|---:|---|
| [HKUDS/AI-Researcher](https://github.com/HKUDS/AI-Researcher) | `systems/ai-researcher` | 5.5k | `gh issue create -R HKUDS/AI-Researcher` |
| [HKUDS/Auto-Deep-Research](https://github.com/HKUDS/Auto-Deep-Research) | `systems/auto-deep-research` | 1.6k | `gh issue create -R HKUDS/Auto-Deep-Research` |
| [AutoSurveys/AutoSurvey](https://github.com/AutoSurveys/AutoSurvey) | `systems/autosurvey` | 470 | `gh issue create -R AutoSurveys/AutoSurvey` |
| [snap-stanford/POPPER](https://github.com/snap-stanford/POPPER) | `systems/popper` | 275 | `gh issue create -R snap-stanford/POPPER` |
| [Sibyl-Research-Team/AutoResearch-SibylSystem](https://github.com/Sibyl-Research-Team/AutoResearch-SibylSystem) | `systems/sibyl-system` | 257 | `gh issue create -R Sibyl-Research-Team/AutoResearch-SibylSystem` |

---

## Shared body (reuse for each; swap the project name)

**Title:** `Please add an open-source LICENSE file`

**Body:**

> Hi — thanks for open-sourcing **<PROJECT>**; it's a great contribution to the
> autonomous-research space.
>
> I noticed the repository currently has **no `LICENSE` file**, so GitHub reports
> it as having no license. Under default copyright law that makes it
> *all-rights-reserved*: others can read the code, but cannot legally
> redistribute, modify, or build on it — which is usually not the intent for a
> research codebase meant to be reproduced and extended.
>
> Would you consider adding an OSI-approved license? The common choices in this
> space are:
> - **MIT** or **BSD-3-Clause** — maximally permissive;
> - **Apache-2.0** — permissive + an explicit patent grant (what several peer
>   projects here use).
>
> Adding a `LICENSE` file (GitHub's "Add file → Create new file → `LICENSE`"
> flow offers a template picker) would let the community reproduce and build on
> the work with confidence. Thanks for considering!
>
> *Context: <PROJECT> is one of the systems indexed by the community hub
> [Auto-Research-Skills](https://github.com/brycewang-stanford/Auto-Research-Skills);
> we track upstream license/maintenance health and flag no-license repos so users
> know the reuse terms.*

---

## Per-repo notes

- **HKUDS/AI-Researcher** & **HKUDS/Auto-Deep-Research** — same org; you could file
  one issue per repo or a single combined note to the org. NeurIPS-adjacent work,
  actively used; a license would meaningfully increase reuse.
- **AutoSurveys/AutoSurvey** — also stale (last push 1y4m); a license + a "still
  maintained?" note would both help.
- **snap-stanford/POPPER** — paper code ("Automated Hypothesis Testing with
  Agentic Sequential Falsifications"); Stanford SNAP repos are usually
  MIT/Apache, so this is likely an oversight.
- **Sibyl-Research-Team/AutoResearch-SibylSystem** — Claude-Code-native; active
  (3mo); good candidate for a quick MIT add.

If a maintainer declines or is unresponsive, the fallback is to keep the repo
flagged 🔴 in `catalog/HEALTH.md` and the systems matrix, and treat it as
study-only (do not redistribute the vendored copy beyond the submodule pointer,
which is just a URL + commit SHA and carries no license obligation itself).
