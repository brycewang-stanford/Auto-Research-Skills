<div align="center">
  <img src="assets/banner.svg" alt="Auto-Research-Skills banner" width="100%">
</div>

<h1 align="center">Auto-Research-Skills</h1>

<p align="center">
  <b>A curated hub of autonomous-research <i>skills</i> & agents</b> — from idea → experiment → paper, on autopilot.
</p>

<p align="center">
  <a href="#"><img src="https://img.shields.io/badge/Awesome-Auto%20Research-ff7aa2?style=flat-square" alt="awesome"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-CC0%201.0-4aa6ff?style=flat-square" alt="license"></a>
  <img src="https://img.shields.io/github/stars/brycewang-stanford/Auto-Research-Skills?style=flat-square&color=ffd23f" alt="stars">
  <a href="CONTRIBUTING.md"><img src="https://img.shields.io/badge/PRs-welcome-7ee0a8?style=flat-square" alt="PRs welcome"></a>
</p>

---

### ⭐ Featured Skill

> **[Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills)** &nbsp;·&nbsp; ~22.7k ⭐ &nbsp;·&nbsp; 🧩 bundled
> Academic Research Skills for Claude Code — a full **research → write → review → revise → finalize** pipeline, covering literature review and peer review. Vendored here at [`skills/academic-research-skills`](skills/academic-research-skills).

---

> **What is this?** A community-curated collection of *reusable, composable skills* for **autonomous research** — packaged so that coding agents (Claude Code, Codex, OpenClaw, and any LLM agent) can plug them in directly. Selected skill repos are vendored here as **git submodules** so you can clone the whole toolbox in one shot.

```bash
# grab everything, including all skill submodules
git clone --recurse-submodules https://github.com/brycewang-stanford/Auto-Research-Skills.git

# already cloned? pull the skills in
git submodule update --init --recursive
```

## Table of Contents

- [🧠 End-to-End Autonomous Research Systems](#-end-to-end-autonomous-research-systems)
- [🔎 Deep Research & Literature Synthesis](#-deep-research--literature-synthesis)
- [🧪 Automated Experiment & Code Agents](#-automated-experiment--code-agents)
- [🧩 Research Skills & Plugin Collections](#-research-skills--plugin-collections)
- [📚 Awesome Lists & Surveys](#-awesome-lists--surveys)
- [🗂️ Bundled Skills (submodules)](#️-bundled-skills-submodules)
- [🤝 Contributing](#-contributing)
- [📄 License](#-license)

> **Legend:** ⭐ = approximate star count · 🧩 = vendored here as a submodule

---

## 🧠 End-to-End Autonomous Research Systems

> Projects that automate the *full* research lifecycle: idea → experiment → paper → review.

| Project | ⭐ | Stack | Notes |
|---|---|---|---|
| [aiming-lab/AutoResearchClaw](https://github.com/aiming-lab/AutoResearchClaw) | ~12.8k | Agent | Fully autonomous & self-evolving research, from idea to paper. |
| [SakanaAI/AI-Scientist](https://github.com/SakanaAI/AI-Scientist) | ~13.8k | Python | Generate ideas, run experiments, write & auto-review papers. |
| [Sibyl-Research-Team/AutoResearch-SibylSystem](https://github.com/Sibyl-Research-Team/AutoResearch-SibylSystem) | ~247 | Claude Code | Self-evolving autonomous research system, Claude-Code native. |

## 🔎 Deep Research & Literature Synthesis

> Automated information gathering, literature review, and cited report generation.

| Project | ⭐ | Stack | Notes |
|---|---|---|---|
| [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) | ~27.3k | Python | Plan → scrape → cited report. The classic. |
| [stanford-oval/storm](https://github.com/stanford-oval/storm) | ~28.3k | Python | Wikipedia-style long-form report synthesis. |
| [bytedance/deer-flow](https://github.com/bytedance/deer-flow) | ~70k | LangGraph | Deep research w/ human-in-the-loop. |
| [HKUDS/Auto-Deep-Research](https://github.com/HKUDS/Auto-Deep-Research) | ~1.5k | Agent | Low-cost, fully-automated personal research assistant. |

## 🧪 Automated Experiment & Code Agents

> Coding, experiment execution, and iterative optimization on autopilot.

| Project | ⭐ | Stack | Notes |
|---|---|---|---|
| [Xiangyue-Zhang/auto-deep-researcher-24x7](https://github.com/Xiangyue-Zhang/auto-deep-researcher-24x7) | ~975 | Agent | Runs DL experiments 24/7, Leader-Worker, constant-size memory. |
| [TheBlewish/Automated-AI-Web-Researcher-Ollama](https://github.com/TheBlewish/Automated-AI-Web-Researcher-Ollama) | ~3.0k | Ollama | Local-LLM automated web researcher. |

## 🧩 Research Skills & Plugin Collections

> Reusable skill sets and plugins that drop into coding agents.

| Project | ⭐ | Stack | Notes |
|---|---|---|---|
| [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills) 🧩 ⭐ | ~22.7k | Claude Code · Python | **Featured.** Academic research → write → review → revise → finalize pipeline. |
| [wanshuiyin/Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) 🧩 | ~10.8k | Markdown skills | ARIS — cross-model review loops, idea discovery, experiment automation. No framework lock-in. |
| [mshumer/autonomous-researcher](https://github.com/mshumer/autonomous-researcher) | ~804 | Agent | Lightweight autonomous research agent. |
| [openags/auto-research](https://github.com/openags/auto-research) | ~284 | Agent + UI | Generalist "AI Scientist" across fields. |

## 📚 Awesome Lists & Surveys

| Project | ⭐ | Notes |
|---|---|---|
| [handsome-rich/Awesome-Auto-Research-Tools](https://github.com/handsome-rich/Awesome-Auto-Research-Tools) | ~778 | The list that inspired this repo. |
| [worldbench/awesome-ai-auto-research](https://github.com/worldbench/awesome-ai-auto-research) | ~187 | A survey on AI auto-research. |
| [MinhaoXiong/awesome-automated-research](https://github.com/MinhaoXiong/awesome-automated-research) | ~116 | Curated list of autonomous research systems. |

---

## 🗂️ Bundled Skills (submodules)

**27 research-skill repos** (every one with 100+ ⭐) are vendored under [`skills/`](skills/) as git submodules, sorted by stars. Run `git submodule update --init --recursive` to fetch them all.

| Path | Source | ⭐ | What it gives you |
|---|---|---|---|
| `skills/last30days` | [mvanhorn/last30days-skill](https://github.com/mvanhorn/last30days-skill) | ~26.7k | Research any topic across Reddit, X, YouTube, HN, Polymarket. |
| `skills/scientific-agent-skills` | [K-Dense-AI/scientific-agent-skills](https://github.com/K-Dense-AI/scientific-agent-skills) | ~26.2k | Ready-to-use agent skills for research, science, engineering, analysis, finance. |
| `skills/academic-research-skills` ⭐ | [Imbad0202/academic-research-skills](https://github.com/Imbad0202/academic-research-skills) | ~22.7k | **Featured.** research → write → review → revise → finalize. |
| `skills/aris` | [wanshuiyin/Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) | ~10.8k | Markdown-only autonomous-ML-research skills. |
| `skills/ai-research-skills` | [Orchestra-Research/AI-Research-SKILLs](https://github.com/Orchestra-Research/AI-Research-SKILLs) | ~9.0k | Open library of AI research & engineering skills for any model. |
| `skills/paper-writing-skills` | [Master-cai/Research-Paper-Writing-Skills](https://github.com/Master-cai/Research-Paper-Writing-Skills) | ~3.0k | ML/CV/NLP paper-writing skill package. |
| `skills/academic-research-skills-codex` | [Imbad0202/academic-research-skills-codex](https://github.com/Imbad0202/academic-research-skills-codex) | ~1.9k | Codex-native academic research suite, human-in-the-loop. |
| `skills/academicforge` | [HughYau/AcademicForge](https://github.com/HughYau/AcademicForge) | ~1.3k | Curated skill collection for academic writing & research. |
| `skills/empirical-research-skills` | [brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research](https://github.com/brycewang-stanford/Awesome-Agent-Skills-for-Empirical-Research) | ~1.3k | 23k+ agent skills for empirical research across social sciences. |
| `skills/x-research-skill` | [rohunvora/x-research-skill](https://github.com/rohunvora/x-research-skill) | ~1.1k | X/Twitter research: agentic search, thread following. |
| `skills/supervisor-skills` | [HKUSTDial/Supervisor-Skills](https://github.com/HKUSTDial/Supervisor-Skills) | ~1.1k | "AI 科研副导师" — from idea to paper submission. |
| `skills/medical-research-skills` | [aipoch/medical-research-skills](https://github.com/aipoch/medical-research-skills) | ~858 | Medical research: protocol design, data analysis, evidence. |
| `skills/scienceclaw` | [beita6969/ScienceClaw](https://github.com/beita6969/ScienceClaw) | ~823 | Self-evolving AI research colleague, 285 skills. |
| `skills/claude-deep-research-skill` | [199-biotechnologies/claude-deep-research-skill](https://github.com/199-biotechnologies/claude-deep-research-skill) | ~726 | Enterprise deep-research, 8-phase pipeline, source credibility. |
| `skills/research-skills` | [luwill/research-skills](https://github.com/luwill/research-skills) | ~639 | Common research processes encapsulated as agent skills. |
| `skills/research-units-pipeline` | [WILLOSCAR/research-units-pipeline-skills](https://github.com/WILLOSCAR/research-units-pipeline-skills) | ~441 | Research pipelines as semantic execution units. |
| `skills/oneresearchclaw` | [gaotiexinqu/OneResearchClaw](https://github.com/gaotiexinqu/OneResearchClaw) | ~434 | Any materials → fully autonomous, skill-driven research. |
| `skills/openclaw-search-skills` | [blessonism/openclaw-search-skills](https://github.com/blessonism/openclaw-search-skills) | ~434 | OpenClaw deep-search: multi-source search & extraction. |
| `skills/awesome-scientific-skills` | [InternScience/Awesome-Scientific-Skills](https://github.com/InternScience/Awesome-Scientific-Skills) | ~400 | Curated Agent Skills for scientific research. |
| `skills/claudeblattman` | [chrisblattman/claudeblattman](https://github.com/chrisblattman/claudeblattman) | ~373 | Claude Code for academics — skills, agents, setup guides. |
| `skills/ai-research-feedback` | [claesbackman/AI-research-feedback](https://github.com/claesbackman/AI-research-feedback) | ~354 | Claude Code skills for academic research review. |
| `skills/phd-skills` | [fcakyon/phd-skills](https://github.com/fcakyon/phd-skills) | ~246 | Paper reproduction, experiment design, paper review. |
| `skills/academic-skills` | [chtc66/academic-skills](https://github.com/chtc66/academic-skills) | ~227 | Paper reading, survey writing, experiment summary, rebuttal. |
| `skills/research-plugins` | [wentorai/research-plugins](https://github.com/wentorai/research-plugins) | ~223 | 350+ academic research skills, MCP configs & plugins. |
| `skills/codex-academic-skills` | [zLanqing/codex-claude-academic-skills](https://github.com/zLanqing/codex-claude-academic-skills) | ~172 | Three academic skills: reading, writing, scientific computing. |
| `skills/franklee-academic-research-skills` | [franklee16/academic-research-skills](https://github.com/franklee16/academic-research-skills) | ~149 | Claude Code skills for econ/finance academic research. |

> Want your skill bundled? See [CONTRIBUTING](CONTRIBUTING.md) — open a PR adding a submodule under `skills/`.

## 🤝 Contributing

PRs welcome! Add a tool to the right category, or vendor a skill as a submodule. See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

[CC0 1.0 Universal](LICENSE) — public domain. The submodules retain their own licenses.
