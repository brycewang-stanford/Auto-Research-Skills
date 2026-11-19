# The crew

A Claude Code plugin: nine research-assistant agents that take a question to a compiled
paper, through four gates a human approves. Version 0.1.

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

For Codex, see [`adapters/codex/`](adapters/codex/).

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

## Limits of v0.1

- Five seed papers have passed all four gates; the sixth is in progress in
  [`gallery/`](../gallery/README.md). Each cost about $58–103 of model usage at API list
  prices; `python3 scripts/usage.py <workspace>` measures a project from the local
  Claude Code transcripts.
- Cross-family review needs the Codex CLI and your consent to send the workspace to
  OpenAI; without it the Reviewer runs on the same model family in a fresh context.
- Gate approval is guarded by a hook ([`hooks/guard.py`](hooks/guard.py)): an approve
  command, or an edit of `plan.json` that approves a gate, is refused unless the human's
  latest message or AskUserQuestion answer approves that gate, and subagents can never
  approve. The same hook keeps agents out of the bench answer keys. It narrows the
  agents to the honest path; a determined workaround (a script written to disk and run
  later) is still possible, so the rule in `PI.md` stays.
- Claude Code is the primary runtime; the Codex adapter ([`adapters/codex/`](adapters/codex/))
  is newer and less tested.
