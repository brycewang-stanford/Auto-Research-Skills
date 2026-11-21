# The crew

Nine research-assistant agents that take a question to a compiled paper, through four
gates a human approves. A Claude Code plugin that also installs into Codex; it runs on
the plan you already have. Version 0.2.

| Role | Does | Runs as |
|---|---|---|
| **PI** | Plans, delegates, brings decisions to the human | The main session ([`PI.md`](PI.md)) |
| **Scout** | Finds prior work; verifies every reference against its source | [`agents/scout.md`](agents/scout.md) |
| **Designer** | Fixes the study design before any outcome is seen | [`agents/designer.md`](agents/designer.md) |
| **Econometrician** | Social-science track: data, estimation, robustness | [`agents/econometrician.md`](agents/econometrician.md) |
| **Experimenter** | CS track: experiments with seeds and fair baselines | [`agents/experimenter.md`](agents/experimenter.md) |
| **Data RA** | Fetches and documents data; provenance and codebook | [`agents/data-ra.md`](agents/data-ra.md) |
| **Figures RA** | Builds every figure and table by script from logged runs | [`agents/figures-ra.md`](agents/figures-ra.md) |
| **Writer** | Drafts the LaTeX paper from recorded claims | [`agents/writer.md`](agents/writer.md) |
| **Replicator** | Rebuilds the environment and reruns everything from scratch | [`agents/replicator.md`](agents/replicator.md) |
| **Reviewer** | Attacks every other role's work before each gate | [`agents/reviewer.md`](agents/reviewer.md) |

## Install

```bash
claude plugin marketplace add brycewang-stanford/Free-Research-Crew
claude plugin install crew@free-research-crew
```

Or, from a clone, load it for one session: `claude --plugin-dir ./crew`.

Needs Python 3.9+ and, to compile papers, a LaTeX installation.

To give a role extra skills from the hub, install its role kit (from a clone, after
`./setup.sh`):

```bash
python3 tools/build_starter_kits.py --install-role reviewer --dest ~/.claude/skills
```

For **Codex**, install the PI skill, the nine roles as Codex custom agents and the guard
hook from a clone:

```bash
python3 crew/adapters/codex/install.py
```

then open `/hooks` in Codex once to trust the guard, and ask *"use crew-pi to start seed
ss-dml-401k"*. Details in [`adapters/codex/`](adapters/codex/).

## Use

```text
/crew:start ss-dml-401k                      run a bench seed
/crew:start "does X affect Y?" — track: social-science
/crew:status                                 where the project stands; resume it
/crew:gate <workspace> design approve        record your decision on a gate
```

Between gates, `python3 scripts/crew.py next <ws>` lists the next steps and what can run
in parallel, and the Reviewer starts round 2 and later from
`python3 scripts/crew.py changes <ws> <target>` (what changed since its last round).

The crew stops at each gate — question, design, results, submission — and shows you the
Reviewer's verdict and open objections. Nothing proceeds until you approve.

## How it stays honest

- **Agents hand off through files**, and [`scripts/crew.py`](scripts/crew.py) checks
  them. See [`PROTOCOL.md`](PROTOCOL.md).
- **Analysis cannot run before the design is approved.** The tool refuses.
- **Analysis code is reviewed before it runs.** The tool refuses an analysis run unless
  the latest code review passed and read exactly the code it executes; a fix after the
  review needs another round, or the human's recorded consent.
- **Every number in the paper is a macro generated from a logged run.** If the code
  changes after the run, validation fails until it is rerun. A claim's value typed out by
  hand is flagged, and so are the paper's statements about its own process: review
  rounds, findings, runs and the rerun come from `paper/process.tex`, computed from the
  ledger.
- **Every reference has a verification record.** A citation recalled from memory fails.
- **The Reviewer never sees the author's account of the work**, only the files, and can
  run on another provider's model ([`scripts/cross_review.py`](scripts/cross_review.py)).
  A gate cannot be approved while it has an open critical finding, unless the human
  overrules it on the record.
- **Submission needs a clean rerun**: every logged run re-executed from scratch, every
  metric reproduced.

## Layout

```text
agents/      the roles
skills/      /crew:start, /crew:status, /crew:gate
scripts/     crew.py, the workspace tool (standard library only); usage.py, cost and time
hooks/       guard.py: only the human approves a gate; agents never read answer keys
tracks/      what a finished paper needs, per track
templates/   LaTeX paper skeleton and AI-use statement
bench/       seed tasks (their answer keys live outside the plugin, in ../answer-keys/)
```

## Credit

The Reviewer's design follows
[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) (vendored at
[`skills/aris`](../skills/aris)): the role that does the work never judges it, the
reviewer reads the artifacts and not a summary, every review commits to one strongest
argument for rejection, and review rounds are bounded.

## Choosing models

Every role inherits the model of the Claude Code (or Codex) session that runs the PI, so
the crew runs on the plan you already have, with no separate bill. Use the strongest
model your plan offers: the six gallery papers run that way needed the fewest review
rounds.

A smaller model also works. In the `ss-rd-senate` trial every role, the Reviewer
included, ran on Claude Haiku 5.5 (`model: haiku` in the frontmatter of the files in
[`agents/`](agents/)). The protocol held and the paper passed its answer key, but the
Reviewer needed more rounds and the roles made more slips for it to catch. `python3
scripts/usage.py <workspace>` reports what a project used.

## Limits

- Eight seed papers have passed all four gates; see
  [`gallery/`](../gallery/README.md). All eight are replications or synthetic tests
  with a known answer; none yet asks an open question.
- Cross-family review needs the Codex CLI and your consent to send the workspace to
  OpenAI; without it the Reviewer runs on the same model family in a fresh context.
- Gate approval is guarded by a hook ([`hooks/guard.py`](hooks/guard.py)): an approve
  command, or an edit of `plan.json` that approves a gate, is refused unless the human's
  latest message or AskUserQuestion answer approves that gate, and subagents can never
  approve. The same hook keeps agents out of the bench answer keys. It narrows the
  agents to the honest path; a determined workaround (a script written to disk and run
  later) is still possible, so the rule in `PI.md` stays.
- All eight gallery papers were written in Claude Code. The Codex adapter
  ([`adapters/codex/`](adapters/codex/)) installs the same roles as Codex custom agents
  and the same guard; Codex loads them, but no paper has yet been run end to end in Codex.
- Protocol 0.2's checks (code review before analysis, process macros, typed numbers)
  came after the first seven gallery papers, which were written under 0.1; for them the
  new rules are warnings. The eighth, `ss-card-proximity`, was written under 0.2: four
  code rounds, 15 review rounds in all, and every analysis run covered by a code review
  except one label-only figure rerun the human approved.
