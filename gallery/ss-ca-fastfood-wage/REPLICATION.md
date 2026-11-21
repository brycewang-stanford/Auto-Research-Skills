# Replication: ss-ca-fastfood-wage

How to reproduce every number in `paper/main.pdf` from this workspace, and what happened
when the Replicator did so. Result of the clean rerun of 2026-11-21: **passed, 27 of 27
runs reproduced, all 4,416 recorded metrics matched** (`replication.json`, created
2026-11-21T14:47:52Z). Written by the Replicator; the outcome section reports
`replication.json`.

## 1. What was rerun

Every run in the ledger (`runs/<id>/run.json`), 27 in all: the five data runs
(fetch-pop, fetch-prop99, fetch-data, prepare-data, prepare-state), the method check
check-methods (`code/test_sclib.py`), the candidate selection (select) and the
pre-period inference calibration (level-mde), the pre-specified post-period runs for
H1-H3, the secondary, robustness and placebo runs, event-path and the verdict, the three
figure runs, and the post hoc run posthoc (design deviation D7, run with `--unreviewed`;
the latest run in the ledger, finished 2026-11-21T13:47:05Z). Nothing was skipped and
`--reuse-data` was not used: every raw file was downloaded again from BLS, the Census
Bureau and GitHub.

## 2. Environment

- **Python 3.14.6** (Homebrew CPython, macOS 26.6.2 arm64, Apple M3, 8 cores), the same
  interpreter version recorded in every run's `run.json`.
- **A fresh virtual environment built from `code/requirements.txt` alone.** `crew.py
  rerun --setup` created it inside the temporary copy of the workspace; the authors'
  `.venv` was not copied. The install (pip 26.1.2) exited 0, and `pip freeze` of the new
  environment equals the 20 pinned lines of `code/requirements.txt` exactly (numpy 2.5.3,
  scipy 1.18.1, pandas 3.0.5, statsmodels 0.15.0, matplotlib 3.11.2, wrapt 2.5.2, ...):
  nothing more and nothing missing. Nothing beyond the requirements file was needed.
- Every run calls `python3 <script> [arg]` from the workspace root. In the rerun the fresh
  `.venv/bin` was first on `PATH`, so `python3` was that environment's 3.14.6 (each
  run's `env` in `replication.json` records it). Run by hand, activate the environment
  first (below) so that `python3` resolves to it.
- **Seeds.** The only randomness is in check-methods: the SDID calibration draws use
  `numpy.random.default_rng(20261122)` and the synthetic panels
  `default_rng(20261121)`, both fixed in `code/test_sclib.py`. check-methods spreads its
  Monte Carlo over up to 8 worker processes (`min(8, os.cpu_count())`); on this 8-core
  machine the rerun used the same number of workers as the first run and its 1,218
  metrics matched. No other run draws random numbers.
- No R, Stata or LaTeX is needed for the runs; LaTeX is needed only to compile the paper.

```bash
cd gallery/ss-ca-fastfood-wage
python3.14 -m venv .venv
.venv/bin/pip install -r code/requirements.txt
source .venv/bin/activate
```

## 3. Data

All public, listed in `data/manifest.json` (203 entries, each with its SHA-256); raw and
derived files are git-ignored and nothing is redistributed. Network access is needed.

- **BLS QCEW** quarterly industry slices, `https://data.bls.gov/cew/data/api/<year>/<qtr>/industry/<code>.csv`,
  for NAICS 722513, 722511, 7225 and 10, 2014Q1-2026Q1: 196 CSV files, 288,941,864
  bytes, written to `data/raw/qcew/` by fetch-data. BLS publishes no checksum;
  `code/fetch_data.py` compares the bytes with the manifest's SHA-256 and prints a
  warning on a mismatch (BLS revises recent quarters), and probes the quarter after
  2026Q1 without downloading it (`data/fetch_index.json`).
- **Census Bureau** population estimates: `sc-est2020int-alldata6.csv` (2010-2020
  intercensal, by age) and `NST-EST2025-ALLDATA.csv` (2020-2025 totals), written to
  `data/raw/census/` by fetch-pop.
- **synthdid's `california_prop99.csv`** at commit `70c1ce3e`, written to
  `data/raw/synthdid/` by fetch-prop99, which checks the published git blob SHA-1.
- **Derived**: `qcew_panel.csv` and `suppression_by_state_year.csv` (prepare-data),
  `state_panel.csv` and `state_panel_pre.csv` (prepare-state), in `data/derived/`.

In the rerun, downloaded between about 14:13:35Z and 14:20:41Z on 2026-11-21, **every
one of the 203 files in the manifest, raw and derived, was byte-identical to its
recorded SHA-256**: no BLS file had been revised since the first retrieval earlier the
same day. The data runs' metrics (file counts, bytes, rows and the Census SHA-256s)
matched the ledger. A later rerun may find revised QCEW vintages; `fetch_data.py` then
prints a warning per file and fetch-data's `total_bytes` and the downstream metrics
would no longer match. In that case `crew.py rerun --reuse-data` with the archived files
of the first retrieval is the way to check the code, and the revision is a finding to
report.

## 4. Commands

Automatic (what the Replicator ran, from the repository root):

```bash
python3 crew/scripts/crew.py rerun gallery/ss-ca-fastfood-wage \
  --setup "python3 -m venv .venv && .venv/bin/pip install -r code/requirements.txt"
python3 crew/scripts/crew.py validate gallery/ss-ca-fastfood-wage
```

By hand, from the workspace root with the environment of section 2 active, in the order
`crew.py rerun` used (a run comes after every run that produced one of its inputs,
otherwise the order the runs were first recorded). Each command writes the metrics file
named in `runs/<id>/run.json` (`data/*_metrics.json` for the data runs,
`runs/<id>/metrics.json` otherwise); create `runs/<id>/` first if it does not exist.

| # | Run | Command | Writes besides metrics |
|---|---|---|---|
| 1 | fetch-pop | `python3 code/fetch_pop.py` | `data/raw/census/*.csv` |
| 2 | fetch-prop99 | `python3 code/fetch_prop99.py` | `data/raw/synthdid/california_prop99.csv` |
| 3 | fetch-data | `python3 code/fetch_data.py` | `data/raw/qcew/*.csv` (196), `data/fetch_index.json` |
| 4 | prepare-data | `python3 code/prepare_data.py` | `data/derived/qcew_panel.csv`, `data/derived/suppression_by_state_year.csv` |
| 5 | prepare-state | `python3 code/prepare_state.py` | `data/derived/state_panel.csv`, `data/derived/state_panel_pre.csv` |
| 6 | check-methods | `python3 code/test_sclib.py` | `runs/check-methods/mc_rates.csv` |
| 7 | select | `python3 code/select_rule.py` | `runs/select/pseudo_atts.csv` |
| 8 | level-mde | `python3 code/level_mde.py` | `runs/level-mde/tests.csv` |
| 9 | h1-wage | `python3 code/h1_wage.py` | |
| 10 | h2-emp | `python3 code/h2_emp.py` | `runs/h2-emp/placebos.csv` |
| 11 | h3-years | `python3 code/h3_years.py` | |
| 12 | anticip | `python3 code/anticip.py` | |
| 13 | sec-cemn | `python3 code/sec_cemn.py` | |
| 14 | sec-dube | `python3 code/sec_dube.py` | |
| 15 | rob-base-2023q4 | `python3 code/robust.py base2023q4` | |
| 16 | rob-pre-ab257 | `python3 code/robust.py preab257` | |
| 17 | rob-pool | `python3 code/robust.py pool` | |
| 18 | rob-7225 | `python3 code/robust.py naics7225` | |
| 19 | rob-final-quarters | `python3 code/robust.py final7` | |
| 20 | plc-nonff | `python3 code/placebo_outcome.py nonff` | |
| 21 | plc-722511 | `python3 code/placebo_outcome.py 722511` | |
| 22 | event-path | `python3 code/event_path.py` | `runs/event-path/event_path.csv` |
| 23 | verdict | `python3 code/verdict.py` | |
| 24 | fig-select | `python3 code/fig_select.py` | `paper/figures/fig_select.pdf`, `.caption.md` |
| 25 | fig-event | `python3 code/fig_event.py` | `paper/figures/fig_event.pdf`, `.caption.md` |
| 26 | fig-placebo | `python3 code/fig_placebo.py` | `paper/figures/fig_placebo.pdf`, `.caption.md` |
| 27 | posthoc | `python3 code/posthoc.py` | `runs/posthoc/georgia.csv` |

Then `crew.py numbers gallery/ss-ca-fastfood-wage` regenerates `paper/numbers.tex` and
`paper/process.tex` from `claims.jsonl` and the ledger, and the paper compiles from
`paper/main.tex` (pdflatex, bibtex with `refs.bib`, pdflatex twice).

## 5. Expected time

**About 35 minutes on an 8-core laptop; budget 30-75.** The whole rerun took **2,071 s
(34 min 31 s) wall clock**, 14:13:21Z to 14:47:52Z, including the environment build
(about 15 s with a warm pip cache) and the downloads (about 7 minutes for the 199 raw
files, most of it the 196 QCEW slices fetched one at a time with a 0.3 s pause). One run
dominates: check-methods, the Monte Carlo of `test_sclib.py`, which started at 14:21:02Z
and took about 26 minutes in the rerun on 8 worker processes (10,401 s of CPU time for
the whole rerun). When first recorded it took 4,110 s (68 min), on the same machine
under heavier load from other sessions; the 1-minute load average was about 9-14 during
this rerun, so neither figure is a quiet-machine time. Every other run takes a few
seconds (level-mde about 8 s).

## 6. Outcome of the rerun

**`replication.json`: PASSED, 27 of 27 runs reproduced** (created 2026-11-21T14:47:52Z;
rtol 1e-6, atol 1e-9, the protocol defaults; `reuse_data: false`; setup exit code 0).

| Runs (in rerun order) | Status |
|---|---|
| fetch-pop, fetch-prop99, fetch-data, prepare-data, prepare-state | match |
| check-methods, select, level-mde | match |
| h1-wage, h2-emp, h3-years, anticip, sec-cemn, sec-dube | match |
| rob-base-2023q4, rob-pre-ab257, rob-pool, rob-7225, rob-final-quarters | match |
| plc-nonff, plc-722511, event-path, verdict | match |
| fig-select, fig-event, fig-placebo, posthoc | match |

Every run exited 0 and every one of the 4,416 recorded metrics matched within tolerance,
so **no metric failed to match** and there is no mismatch to explain. Notes:

- The headline numbers therefore reproduce from a fresh environment and freshly
  downloaded data, for example the selected candidate DDT-POPW-E-R50 and the H1 pooled
  wage effect of 0.09217 log points (SE 0.03461, nu 14.41).
- **Known defect, reproduced as expected (D7).** posthoc's leave-one-out change flags
  (`b_loo_*_changes_chi`, `b_loo_n_changing` = 10, `b_loo_changing_states` listing all
  ten L states, and the matching stdout line) are all set because a 1e-12 tolerance is
  applied to values stored at 10 significant digits. The rerun reproduces the same
  flags, as `plan.json` design D7 states; no claim uses them. The rerun checks that the
  code is reproducible, not that it is right.
- The rerun compares metrics, not output bytes. The regenerated figures, captions and CSV
  files in the temporary copy were not byte-compared with the workspace's copies; their
  runs' metrics matched.
- `replication.json` is newer than every run record (latest: posthoc, finished
  2026-11-21T13:47:05Z). After the rerun the SHA-256 of every `runs/<id>/run.json` still
  equals its `record_sha256` in `replication.json`, so no run was re-recorded while the
  rerun was going on. The Writer and Reviewer edited `paper/`, `reviews/` and `plan.json`
  during the rerun; no run reads those files, so that does not affect the result.

## 7. Attempts and workarounds

1. One attempt, 2026-11-21T14:13:21Z-14:47:52Z: passed, recorded in
   `replication-history.jsonl` (27 of 27 reproduced, nothing not reproduced).

Workarounds: none. No code, data, metric or tolerance was changed, nothing was installed
beyond `code/requirements.txt`, and `--reuse-data` was not used.
