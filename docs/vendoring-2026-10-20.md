# Vendoring Log — 2026-10-20 (Q3 2026 discovery round)

This round refreshed the whole shelf and then vendored **21 new projects** that
emerged or became prominent between July and October 2026. It follows the
[`CURATION.md`](../CURATION.md) rubric: an OSI license, active maintenance, a
real gap filled, a checkout size that doesn't break `./setup.sh`, and a
focused safety scan with every finding triaged by hand.

Reviewer: automated maintenance pass, done on 2026-10-19/20. Sources:

- GitHub API metadata, fetched live with `gh api repos/OWNER/REPO`.
- Two parallel web and GitHub landscape sweeps, one over skills and one over
  systems, benchmarks and lists, de-duplicated against `.gitmodules`, both
  READMEs, `CURATION.md` and `catalog/DISCOVERY.md`.
- The hub's own scanner, run against a scratch shallow clone of each candidate:

```bash
python3 scripts/scan-skill-safety.py <clone> --min-severity high \
  --context skill,script,other --fail-on none
```

> **Process note.** Earlier rounds used one PR per project. Under the repo's
> push-to-`main` policy, this round lands as one commit per shelf. Every
> project's evidence is recorded below, and each one stays independently
> revertible with `git rm <path>` plus `make catalog`.

## Step 0 — refresh the existing 87

All 87 submodules were bumped to their upstream default branch (55 moved). Two
things surfaced:

- **`skills/academicforge`**: upstream renamed its default branch from `master`
  to `site-first` and deleted `master`. Without a branch pin, `git submodule
  update --remote` aborted the whole bump, so `.gitmodules` now pins
  `branch = site-first`. Stale nested clones that upstream had dropped were
  removed from the local checkout so local counts match a fresh CI clone.
- **`skills/franklee-academic-research-skills`** absorbed *Awesome-Journal-Skills*:
  95 per-journal packs, going from 97 to 2,135 `SKILL.md` files. That accounts
  for most of the jump from 3,433 to 5,897. It is real upstream content: the
  per-journal packs are distinct and are not re-bundled copies.

## Verdicts at a glance

| Project | ★ | License | Dir | SKILL.md | Size | Focused scan (skill/script/other, high+) | Verdict |
|---|---:|---|---|---:|---:|---|---|
| [google-deepmind/science-skills](https://github.com/google-deepmind/science-skills) | 3.3k | Apache-2.0 | `skills/deepmind-science-skills` | 40 | 4 MB | 2 critical: the official `uv` installer quoted in the `uv` skill (benign) | **vendored** |
| [Norman-bury/research-writing-skill](https://github.com/Norman-bury/research-writing-skill) | 3.5k | MIT | `skills/research-writing-skill` | 20 | 12 MB | clean | **vendored** |
| [mikubaka88/CCFA-Skills](https://github.com/mikubaka88/CCFA-Skills) | 3.2k | MIT | `skills/ccfa-skills` | 17 | 373 MB | clean | **vendored** (large: LaTeX templates and sample papers) |
| [openags/paper-search-mcp](https://github.com/openags/paper-search-mcp) | 2.9k | MIT | `skills/paper-search-mcp` | 2 | 2 MB | clean | **vendored** (July "top vendor pick") |
| [huangkiki/dailypaper-skills](https://github.com/huangkiki/dailypaper-skills) | 1.3k | Apache-2.0 | `skills/dailypaper-skills` | 7 | 2 MB | clean | **vendored** |
| [lllllllama/RigorPilot-Skills](https://github.com/lllllllama/RigorPilot-Skills) | 485 | MIT | `skills/rigorpilot-skills` | 11 | 32 MB | 1 critical: `wget … \| bash` inside a *benchmark showcase fixture* (an upstream ImageNet script), not in a skill | **vendored** |
| [NVIDIA-BioNeMo/bionemo-agent-toolkit](https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit) | 484 | Apache-2.0 (code), CC-BY-4.0 (skills) | `skills/bionemo-agent-toolkit` | 70 (35 unique) | 10 MB | 18 high: `echo "$NGC_API_KEY" \| docker login --password-stdin`, NVIDIA's documented login. The key goes to stdin and is never echoed to the agent (benign) | **vendored** (keep CC-BY attribution) |
| [K-Dense-AI/science-superpowers](https://github.com/K-Dense-AI/science-superpowers) | 359 | MIT (LICENSE file; API says NOASSERTION) | `skills/science-superpowers` | 16 | 2 MB | clean | **vendored** |
| [ai4s-research/ai4s-skills](https://github.com/ai4s-research/ai4s-skills) | 246 | MIT | `skills/ai4s-skills` | 7 | 2 MB | clean | **vendored** (July candidate) |
| [alphaXiv/OpenResearch](https://github.com/alphaXiv/OpenResearch) | 7.4k | MIT | `systems/openresearch` | 15 | 24 MB | 24 critical / 6 high, all official agent-CLI installers (Claude, Codex, Cursor, OpenCode, Antigravity, uv, rustup), CI, or test fixtures. **One behavioral note below.** | **vendored, telemetry noted** |
| [EvoScientist/EvoScientist](https://github.com/EvoScientist/EvoScientist) | 5.0k | Apache-2.0 | `systems/evoscientist` | 2 | 25 MB | 13 critical: its own installers, a TinyTeX installer, and two hits inside its *defensive* `curl \| bash` prompt-injection guard | **vendored** (July candidate) |
| [ruc-datalab/DeepAnalyze](https://github.com/ruc-datalab/DeepAnalyze) | 4.7k | MIT | `systems/deepanalyze` | 0 | 43 MB | 1 critical: `uv` installer in a Dockerfile | **vendored** (July candidate) |
| [EvoMap/AutoResearch](https://github.com/EvoMap/AutoResearch) | 3.2k | Apache-2.0 | `systems/evomap-autoresearch` | 4 | 2 MB | 2 high, inside its own *secret scanner*'s output strings | **vendored** |
| [RUC-NLPIR/Arbor](https://github.com/RUC-NLPIR/Arbor) | 1.1k | Apache-2.0 | `systems/arbor` | 11 | 60 MB | 1 high: an opt-in `--show-secrets` CLI flag (masked by default) | **vendored** |
| [SakanaAI/AI-Scientist-v3](https://github.com/SakanaAI/AI-Scientist-v3) | 408 | Apache-2.0 | `systems/ai-scientist-v3` | 13 | 16 MB | 1 critical: Cursor installer in a Dockerfile. 2 high: docstrings saying it "never prints secret values" | **vendored**. Note: agents run with full permissions *inside* Docker |
| [Ayanami0730/deep_research_bench](https://github.com/Ayanami0730/deep_research_bench) | 843 | Apache-2.0 | `benchmarks/deep-research-bench` | 0 | 172 MB | 1 high: prints whether a key env var is *set* (a boolean) | **vendored** |
| [apexin-ai/ASI-Bench](https://github.com/apexin-ai/ASI-Bench) | 302 | Apache-2.0 | `benchmarks/asi-bench` | 0 | 31 MB | 2 critical: nodesource/uv installers in task-image builders. 1 high: a `_redact_secret()` print | **vendored** |
| [scicode-bench/SciCode](https://github.com/scicode-bench/SciCode) | 242 | Apache-2.0 | `benchmarks/scicode` | 0 | 0.2 MB | 1 critical: `uv` installer in CI | **vendored** |
| [allenai/asta-bench](https://github.com/allenai/asta-bench) | 141 | Apache-2.0 | `benchmarks/asta-bench` | 0 | 3 MB | 1 critical: `rustup` installer in a Dockerfile | **vendored** |
| [modelscope/Awesome-Vibe-Research](https://github.com/modelscope/Awesome-Vibe-Research) | 462 | Apache-2.0 | `lists/awesome-vibe-research` | 0 | 1 MB | clean | **vendored** |
| [kael-odin/awesome-academic-research-skills](https://github.com/kael-odin/awesome-academic-research-skills) | 163 | MIT | `lists/awesome-academic-research-skills` | 0 | 8 MB | clean | **vendored**. Its daily `data/rankings.json` is a useful discovery feed |

**Net impact:** repos 87 → **108**, broken down as skills 42 → 51, systems
32 → 38, benchmarks 4 → 8 and lists 9 → 11. Headline `SKILL.md` count went
5,897 → **6,087** (unique: 5,255 → 5,410). The catalog `SAFETY.md`
must-review count (findings in `skill`/`script` files) went 142 → 163. All 21
new findings are triaged above as benign: 18 are bionemo's docker login, 2 are
DeepMind's `uv` skill and 1 is RigorPilot's fixture.

## Notes worth carrying forward

- **OpenResearch `orx-feedback` skill (telemetry).** This skill tells the agent
  to send feedback reports to the vendor without stopping the current task. It
  tells the user only if the send succeeds, and drops failures silently. The
  skill does tell users how to opt out (`orx telemetry off`), and the text
  forbids including code, prompts or data. This is acceptable for a `systems/`
  entry, but anyone installing OpenResearch's skills into a shared profile
  should know about it. Revisit if the reporting scope widens.
- **AI-Scientist-v3 and Arbor** run coding agents with broad permissions. v3
  contains this inside Docker; Arbor's own docs ask for a sandbox. Neither
  belongs in a personal agent profile without isolation.
- **bionemo-agent-toolkit** ships each skill twice: `nim-skills/` plus a plugin
  copy under `skills/bionemo-agent-toolkit/skills/`. That's why it has 70 files
  but only 35 unique skills. The catalog's dedup handles it.
- **CCFA-Skills** is the largest new checkout at 373 MB, mostly
  `ccf-paper-writer` reference material. It's in line with the existing shelf,
  which has up to 900 MB in `systems/ai-researcher`, but it is the first place
  to look if `setup.sh` time becomes a complaint.

## List-only (README rows, not vendored)

| Project | Why not vendored |
|---|---|
| [InternScience/ResearchClawBench](https://github.com/InternScience/ResearchClawBench) | Excellent benchmark (7 agents × 17 LLMs), but ~2.5 GB of task data would roughly double a full `setup.sh`. Revisit if upstream splits the data out. |
| [sapientinc/PRAXIST](https://github.com/sapientinc/PRAXIST) | Fair Source v1.0, which is not an OSI license. Its installer also suggests `codex --yolo`. |
| [aipoch/open-science](https://github.com/aipoch/open-science) | A desktop app rather than a skill pack. The same org's `medical-research-skills` is already vendored. |
| [K-Dense-AI/k-dense-byok](https://github.com/K-Dense-AI/k-dense-byok) | A desktop app built on the already-vendored `scientific-agent-skills`. |
| [mims-harvard/ToolUniverse](https://github.com/mims-harvard/ToolUniverse) | A 531-skill Claude plugin. Needs a collision review against the K-Dense and medical packs first. |
| [anthropics/life-sciences](https://github.com/anthropics/life-sciences) | No license file. |
| [TobiasLee/Rebuttal-Skill](https://github.com/TobiasLee/Rebuttal-Skill) | No license (although rebuttal is a real gap). |
| [Adkid-Zephyr/anti-defensive-writing-Skill](https://github.com/Adkid-Zephyr/anti-defensive-writing-Skill) | Two prompt-style files, too thin to vendor. |
| [facebookresearch/airs-bench](https://github.com/facebookresearch/airs-bench) | CC-BY-NC-4.0 (non-commercial). |
| [openai/frontier-evals](https://github.com/openai/frontier-evals) | PaperBench's home. No research-relevant push since June, and the repo also bundles unrelated evals. |
| [VoltAgent/awesome-agent-skills](https://github.com/VoltAgent/awesome-agent-skills) | A broad general-purpose list of 1,000+ skills; useful as a discovery feed only. |

## Rejected / suspicious

- **`Tyche-MKR/scientific-agent-skills`** is an uncredited re-upload of the
  vendored K-Dense pack that still carries K-Dense's badges. The account was
  created 2026-08-21 and already shows about 1k followers. Treat it as a
  supply-chain warning sign.
- **A cluster of `*/r16-voltagent-awesome-agent-skills-*` repos**, with 45–57★
  each. All were created on the same day by zero-follower accounts, which is
  consistent with star farming.
- **`Spark-To-Paper-Skills/spark-to-paper-skills` and `/paperjury`** have
  near-identical star counts and close to zero weekly growth. Held until the
  signals look organic.
- **`GPTomics/bioSkills`**, previously queued, is now **archived** upstream.
  Dropped from the second-review queue.
- Off-scope despite high stars: `zhaoxuya520/reverse-skill` (security),
  `yb2460/harness-anything` (general office automation) and
  `NVlabs/SoL-Pi` (harness efficiency).
