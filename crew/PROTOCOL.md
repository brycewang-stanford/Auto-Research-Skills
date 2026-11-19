# Crew protocol v0.1

Crew agents do not hand work to each other through chat. They read and write files in
one **workspace**, and a small tool, [`scripts/crew.py`](scripts/crew.py), checks that
the files are consistent. The paper is trustworthy only to the extent that this check
passes, so the rules below are enforced by the tool, not left to the agents' goodwill.

## Three kinds of judgment

| Judgment | Who makes it | Example |
|---|---|---|
| **What happened** | The tool (`crew.py validate`) | The run finished; the number in the paper equals the run's metric |
| **Whether it is good** | The Reviewer, never the role that did the work | The design does not identify the effect it claims |
| **Whether to go on** | The human PI, at four gates | Approve the design before any analysis runs |

A role may keep working toward a target as long as it likes. It may not declare its own
work good.

## Workspace layout

```text
<workspace>/
  crew.json              protocol version, track, title
  plan.json              question, hypotheses, design, task board, gates
  refs.bib               bibliography
  sources/sources.json   verification record for every bibliography entry
  data/manifest.json     every dataset: origin, license, hash
  code/                  scripts the runs execute
  runs/<id>/run.json     one record per executed run (written by the tool)
  claims.jsonl           every claim in the paper, linked to a run or a source
  paper/                 main.tex, numbers.tex (generated), ai-use.tex, figures
  reviews/<id>/          review.json and the Reviewer's memory
  replication.json       result of the last clean rerun (written by the tool)
  log.jsonl              who did what, when (append only with `crew.py log`)
```

## Gates

`question` → `design` → `results` → `submission`, in that order. Each is approved by a
named human with `crew.py gate <ws> <gate> approve --by "<name>"`. Agents request gates;
they never approve them.

| Gate | Needs before approval | Unlocks |
|---|---|---|
| `question` | Question and hypotheses; a review of `question` | Literature and design work |
| `design` | Design summary, method, analysis plan; a review of `design` | **Analysis runs.** The tool refuses them before this gate |
| `results` | Result claims backed by runs; a review of `results` | Writing the paper |
| `submission` | Compiled `paper/main.pdf`, `paper/ai-use.tex`; a review of `paper`; a passing `replication.json` newer than every run | Release to the gallery |

A gate cannot be approved while the Reviewer's latest review of that stage has an open
**critical** finding. The human may overrule a finding with
`--accept-findings <ids> --note "<why>"`; the override is recorded and must be disclosed
in the paper's AI-use statement.

## Files

### `plan.json`

```json
{
  "question": "…",
  "hypotheses": ["…"],
  "contribution": "…",
  "design": {"summary": "…", "method": "…", "data": "…", "analysis_plan": ["…"], "threats": ["…"]},
  "tasks": [{"id": "t1", "title": "…", "owner": "scout", "status": "todo"}],
  "gates": {"question": {"status": "pending"}, "design": {}, "results": {}, "submission": {}}
}
```

Task `status` is `todo`, `doing`, `done` or `blocked`. `owner` is a crew role.

### `refs.bib` and `sources/sources.json`

Every BibTeX key needs a verification record, and every `\cite` in the paper must be in
`refs.bib`:

```json
{"chernozhukov2018": {"doi": "10.1111/ectj.12097", "url": "https://…",
  "verified_on": "2026-11-18", "verified_by": "scout", "method": "fetched-fulltext"}}
```

`method` says how the entry was checked (`fetched-fulltext`, `fetched-abstract`,
`doi-resolved`). An entry recalled from memory and not checked does not get a record,
and so fails validation.

### `data/manifest.json`

```json
{"datasets": [{"id": "sipp1991", "origin": "https://…", "license": "…",
  "path": "data/raw/sipp1991.dta", "sha256": "…", "retrieved_on": "2026-11-18"}]}
```

`data/raw/` and `data/derived/` are git-ignored: data are fetched and rebuilt by the
logged data-prep runs, never committed, so their licenses are respected. When a file is
present its hash must match.

### Runs

Runs are created only by the tool, which executes the command and records what it saw:

```bash
python3 crew.py run <ws> --id main-plr --role econometrician --kind analysis \
  --code code/plr.py --input data/raw/sipp1991.dta --metrics runs/main-plr/metrics.json \
  -- python3 code/plr.py
```

The command runs with the workspace as its working directory and must write its metrics
as a flat JSON object to the `--metrics` path. The record stores the command, times,
exit code, and the hash of every code, input and output file. `kind` is `data-prep`
(allowed any time) or `analysis` (allowed only after the design gate). If a code file
changes after the run, validation fails until the run is repeated. Repeating a run with `--replace` archives the old record, logs and metrics under
`runs/.superseded/` and logs it, so a superseded result always leaves a trace.

### Clean rerun

`crew.py rerun <ws>` copies the workspace to a temporary directory, deletes every output
the runs recorded, re-executes each run in the order it was first run, and compares each
run's metrics with the ledger (relative tolerance `1e-6` by default). It writes
`replication.json`. The Replicator runs it from an environment built only from
`code/requirements.txt`.

### `claims.jsonl`

One JSON object per line. Two kinds:

```json
{"id": "c-ate", "kind": "result", "text": "Eligibility raises net financial assets by …",
 "support": [{"run": "main-plr", "metric": "ate"}], "value": 9123.4, "macro": "AteMain", "format": ",.0f"}
{"id": "c-dml", "kind": "citation", "text": "DML removes regularization bias …",
 "support": [{"source": "chernozhukov2018"}]}
```

- A `result` claim needs at least one successful analysis run. If it has a `value`, the
  value must equal the named metric of its first supporting run.
- A `citation` claim needs a verified source.
- A claim with a `macro` becomes a LaTeX command in `paper/numbers.tex`
  (`crew.py numbers <ws>`). **The Writer never types a result number**; it writes
  `\AteMain`. Validation fails if `numbers.tex` is out of date.

### Reviews

The Reviewer writes `reviews/<id>/review.json`:

```json
{
  "id": "design-r1", "target": "design", "round": 1, "created": "2026-11-18T12:00:00Z",
  "reviewer": {"model": "…", "independence": "fresh-context"},
  "files_read": ["plan.json", "refs.bib"],
  "kill_argument": "The strongest case for rejecting this, in under 200 words.",
  "verdict": "revise",
  "findings": [{"id": "F1", "severity": "critical", "status": "open",
    "text": "…", "evidence": "plan.json design.method", "response": "", "ruling": ""}]
}
```

- `target` is `question`, `literature`, `design`, `code`, `results` or `paper`.
- `verdict` is `block`, `revise` or `pass`. `pass` is not allowed with an open critical finding.
- `severity` is `critical`, `major` or `minor`; `status` is `open`, `resolved`,
  `conceded` or `withdrawn`.
- `independence` is `cross-family` when the Reviewer runs on a model from a different
  provider than the authoring agents (`scripts/cross_review.py` does this through the
  Codex CLI), otherwise `fresh-context`.
- Rounds for a target are numbered from 1 with no gaps, and stop at 4. After round 4 the
  open findings go to the human.

## Commands

```bash
python3 crew.py init <ws> --track cs|social-science --title "…" [--seed <id>]
python3 crew.py status <ws>
python3 crew.py validate <ws> [--strict]
python3 crew.py gate <ws> <gate> request|approve|reject [--by "<human>"] [--note "…"]
python3 crew.py run <ws> --id … --role … --kind … [--code …] [--input …] [--metrics …] -- <command>
python3 crew.py numbers <ws>
python3 crew.py log <ws> --role <role> --action <verb> [--detail "…"]
python3 crew.py rerun <ws> [--rtol 1e-6] [--reuse-data]
python3 cross_review.py <ws> <target> <round> [--model …]   # Reviewer on another provider's model
```

`--strict` also fails when data, code or output files recorded in the ledger are absent,
which is what a clean-environment rerun needs.

## What the tool cannot check

- Whether the human, and not an agent, typed the approval. The tool cannot tell; the
  crew's Claude Code hook ([`hooks/guard.py`](hooks/guard.py)) narrows it by refusing an
  approve command, or an edit of `plan.json` that approves a gate, unless the human's
  latest message or AskUserQuestion answer approves that gate. An agent that writes and
  runs its own script can still get around the hook, so the rule stays.
- Whether a number written by hand in the paper matches a run. Use macros.
- Whether a source actually says what the claim attributes to it. That is the Reviewer's job.
