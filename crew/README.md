# The crew

A Claude Code plugin: six research-assistant agents that take a question to a compiled
paper, through four gates a human approves. Version 0.1.

| Role | Does | Runs as |
|---|---|---|
| **PI** | Plans, delegates, brings decisions to the human | The main session ([`PI.md`](PI.md)) |
| **Scout** | Finds prior work; verifies every reference against its source | [`agents/scout.md`](agents/scout.md) |
| **Designer** | Fixes the study design before any outcome is seen | [`agents/designer.md`](agents/designer.md) |
| **Econometrician** | Social-science track: data, estimation, robustness | [`agents/econometrician.md`](agents/econometrician.md) |
| **Experimenter** | CS track: experiments with seeds and fair baselines | [`agents/experimenter.md`](agents/experimenter.md) |
| **Writer** | Drafts the LaTeX paper from recorded claims | [`agents/writer.md`](agents/writer.md) |
| **Reviewer** | Attacks every other role's work before each gate | [`agents/reviewer.md`](agents/reviewer.md) |

## Install

```bash
claude plugin marketplace add brycewang-stanford/Free-Research-Crew
claude plugin install crew@free-research-crew
```

Or, from a clone, load it for one session: `claude --plugin-dir ./crew`.

Needs Python 3.9+ and, to compile papers, a LaTeX installation.

## Use

```text
/crew:start ss-dml-401k                      run a bench seed
/crew:start "does X affect Y?" — track: social-science
/crew:status                                 where the project stands; resume it
/crew:gate <workspace> design approve        record your decision on a gate
```

The crew stops at each gate — question, design, results, submission — and shows you the
Reviewer's verdict and open objections. Nothing proceeds until you approve.

## How it stays honest

- **Agents hand off through files**, and [`scripts/crew.py`](scripts/crew.py) checks
  them. See [`PROTOCOL.md`](PROTOCOL.md).
- **Analysis cannot run before the design is approved.** The tool refuses.
- **Every number in the paper is a macro generated from a logged run.** If the code
  changes after the run, validation fails until it is rerun.
- **Every reference has a verification record.** A citation recalled from memory fails.
- **The Reviewer never sees the author's account of the work**, only the files. A gate
  cannot be approved while it has an open critical finding, unless the human overrules it
  on the record.

## Layout

```text
agents/      the roles
skills/      /crew:start, /crew:status, /crew:gate
scripts/     crew.py, the workspace tool (standard library only)
tracks/      what a finished paper needs, per track
templates/   LaTeX paper skeleton and AI-use statement
bench/       seed tasks and answer keys
```

## Credit

The Reviewer's design follows
[ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep) (vendored at
[`skills/aris`](../skills/aris)): the role that does the work never judges it, the
reviewer reads the artifacts and not a summary, every review commits to one strongest
argument for rejection, and review rounds are bounded.

## Limits of v0.1

- Not yet run end to end on the seeds; the gallery is empty.
- The Reviewer runs on the same model family as the other roles (`fresh-context`).
  Review by a different provider's model is planned.
- Gate approval by a human is a rule the agents follow, not a technical lock.
- Claude Code only. Codex support is planned.
