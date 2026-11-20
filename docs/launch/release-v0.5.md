# Free-Research-Crew v0.5

The first release of the crew: research-assistant agents that take a question to a compiled paper in empirical social science or machine learning, inside Claude Code, with a Reviewer that attacks every stage and a human who approves four gates.

## Install

```bash
claude plugin marketplace add brycewang-stanford/Free-Research-Crew
claude plugin install crew@free-research-crew
```

Then run `/crew:start` in an empty folder. How it works: [`crew/README.md`](https://github.com/brycewang-stanford/Free-Research-Crew/blob/main/crew/README.md).

## What is in it

- **The crew plugin** (`crew/`, plugin version 0.1.0): a PI playbook and nine roles (Scout, Designer, Data RA, Econometrician, Experimenter, Figures RA, Writer, Replicator, Reviewer); `/crew:start`, `/crew:status`, `/crew:gate`.
- **`crew.py`**, a stdlib workspace tool that enforces the protocol: no analysis run before the design gate; every result number in the paper is a macro generated from a logged run; editing code after a run invalidates it; every citation needs a verification record; submission needs a clean rerun that reproduces every run.
- **A gate guard hook** (`crew/hooks/guard.py`) that refuses a gate approval unless the human's own latest message approves that gate.
- **A bench** of eight seed tasks, with hidden answer keys kept outside the plugin (`answer-keys/`) and a scorer (`crew/bench/score.py`).
- **Cross-family review** through the Codex CLI (`crew/scripts/cross_review.py`), opt-in; the gallery papers used same-family (Claude) review by the human's choice.
- **Cost measurement** from Claude Code transcripts (`crew/scripts/usage.py`).

## Six gallery papers

All six passed all four human gates and a clean rerun. They are demonstrations and are not submitted anywhere.

| Paper | Outcome | Clean rerun |
|---|---|---|
| [Label noise](https://github.com/brycewang-stanford/Free-Research-Crew/tree/main/gallery/cs-label-noise) (ML) | Both hypotheses inconclusive | 20/20 |
| [Null-effect test](https://github.com/brycewang-stanford/Free-Research-Crew/tree/main/gallery/ss-null-effect) | −$9.8 [−358, 338] on data with a true effect of zero; answer key **pass** | 23/23 |
| [401(k) DML replication](https://github.com/brycewang-stanford/Free-Research-Crew/tree/main/gallery/ss-dml-401k) | All 10 published cells within pre-registered tolerances; answer key **pass** | passed |
| [Card–Krueger replication](https://github.com/brycewang-stanford/Free-Research-Crew/tree/main/gallery/ss-card-krueger) | Two of three targets reproduced; the third within tolerance but not at published precision; answer key **pass** | 15/15 |
| [Probability calibration](https://github.com/brycewang-stanford/Free-Research-Crew/tree/main/gallery/cs-calibration) (ML) | H1 contradicted; H2a inconclusive; H2b no difference | 13/13 |
| [LaLonde observational comparison](https://github.com/brycewang-stanford/Free-Research-Crew/tree/main/gallery/ss-lalonde-observational) | $1,573 [9.6, 3,136], within cross-fitting noise; placebo failed, so a statistical contrast, not a program effect; answer key **pass** | 19/19 |

Across the six: 68 review rounds; 12 critical, 210 major and 373 minor findings; no gate approved over an open critical finding. Each paper took 18–25 hours from question to submission gate, including time waiting for the human, and about $58–103 of model usage at Claude API list prices ([`gallery/usage.json`](https://github.com/brycewang-stanford/Free-Research-Crew/blob/main/gallery/usage.json)).

## Known limits

- The gate guard is a Claude Code hook; an agent running outside it, or a human editing files by hand, is not stopped by it.
- The tool checks that numbers trace to runs, not that a source says what a claim attributes to it; that is the Reviewer's job, and the Reviewer can be wrong.
- Same-family review shares the authors' blind spots; cross-family review needs the Codex CLI and your consent to send the workspace to OpenAI.
- Seeds are laptop-sized by design.

The Reviewer's design follows [ARIS](https://github.com/wanshuiyin/Auto-claude-code-research-in-sleep). CC0.
