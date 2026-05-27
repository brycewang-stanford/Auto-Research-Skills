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

These skill repos are vendored under [`skills/`](skills/) as git submodules. Run `git submodule update --init --recursive` to fetch them.

| Path | Source | What it gives you |
|---|---|---|
| `skills/aris` | [wanshuiyin/Auto-claude-code-research-in-sleep](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) | Markdown-only autonomous-ML-research skills. |

> Want your skill bundled? See [CONTRIBUTING](CONTRIBUTING.md) — open a PR adding a submodule under `skills/`.

## 🤝 Contributing

PRs welcome! Add a tool to the right category, or vendor a skill as a submodule. See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📄 License

[CC0 1.0 Universal](LICENSE) — public domain. The submodules retain their own licenses.
