# Replication: ss-dml-401k

How to reproduce every number in `paper/main.pdf` from this workspace, and what happened
when the Replicator did so. Result of the clean rerun of 2026-11-19: **passed, 16 of 16
runs reproduced** (`replication.json`, created 2026-11-19T09:16:58Z). Written by the
Replicator; the outcome section reports `replication.json`.

## 1. Environment

- **Python 3.12.** The rerun used CPython 3.12.11 for every run (macOS 26.6.2 arm64,
  8 cores). `replication.json` records `python 3.14.6`: that is the interpreter that ran
  `crew.py` itself, not the runs' `.venv`.
- **Python packages:** `code/requirements.txt` only (25 pinned packages: numpy 2.5.5,
  pandas 3.1.1, scikit-learn 1.9.1, scipy 1.18.1, statsmodels 0.15.0, matplotlib 3.11.2,
  pyreadstat 1.3.8, joblib 1.6.0, ...).
- **R** (run check-learner-ports only; it calls `Rscript code/check_learner_ports.R`).
  R is not pip-installable. `code/requirements.txt` names the versions in a comment, and
  the rerun used the system R with exactly those versions:
  R 4.5.2 (2025-10-31), hdm 0.3.2, rpart 4.1.24, randomForest 4.7.1.2, gbm 2.3.1,
  nnet 7.3.20, glmnet 4.1.10. `Rscript` must be on `PATH`.
- The runs call `.venv/bin/python ...` from the workspace root, so the environment must
  live at `.venv` inside the workspace (a real directory or a symlink).

```bash
cd gallery/ss-dml-401k
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r code/requirements.txt
uv pip freeze --python .venv/bin/python | diff - <(grep -v '^#' code/requirements.txt | sort)   # expect no output
# R side (once, from CRAN), then check:
Rscript -e 'for (p in c("hdm","rpart","randomForest","gbm","nnet","glmnet")) cat(p, format(packageVersion(p)), "\n")'
```

The Replicator built the Python environment outside the workspace with uv 0.7.15,
confirmed that `uv pip freeze` equals `code/requirements.txt` exactly (25 packages,
nothing extra), and symlinked it at `.venv` for the rerun. Nothing beyond the
requirements file and the listed R packages was needed.

## 2. Data

One public dataset (`data/manifest.json`): the 1991 SIPP 401(k) extract `sipp1991.dta`
from the replication repository of Chernozhukov et al. (2018),
`https://github.com/VC2015/DMLonGitHub/raw/master/sipp1991.dta` (260,726 bytes, 9,915
rows; SHA-256 `1123d5f0...57b4b2`). Run fetch-sipp downloads it (network access needed)
and checks its size and the git blob SHA-1 that GitHub publishes; run prepare-sipp
derives `data/derived/sipp1991.csv` (SHA-256 `4c73b63b...916`). The rerun re-downloaded
and re-derived both; it did not reuse data (`reuse_data: false`), and both runs matched
their recorded metrics, so the bytes were identical.

## 3. Commands

Automatic (what the Replicator ran):

```bash
python3 <repo>/crew/scripts/crew.py rerun gallery/ss-dml-401k
python3 <repo>/crew/scripts/crew.py validate gallery/ss-dml-401k --strict
```

By hand, from the workspace root, in the order `crew.py rerun` used (a run comes after
every run that produced one of its inputs, otherwise the order the runs were recorded).
Each writes the metrics file recorded in `runs/<id>/run.json`.

| # | Run | Command (`.venv/bin/python ...`) | Rerun time |
|---|---|---|---|
| 1 | fetch-sipp | `-I code/fetch_sipp.py` | seconds |
| 2 | prepare-sipp | `-I code/prepare_sipp.py` | seconds |
| 3 | timing-synthetic | `code/timing_synthetic.py` (timing only, no metrics compared) | ~2 min |
| 4 | check-learner-ports | `code/check_learner_ports.py` (calls Rscript) | ~11 min |
| 5 | check-noctrl | `code/check_noctrl.py` | seconds |
| 6 | main-lasso | `code/dml_plr.py --learner lasso --splits 100` | ~39 min |
| 7 | main-tree | `code/dml_plr.py --learner tree --splits 100` | ~8 min |
| 8 | main-nnet | `code/dml_plr.py --learner nnet --splits 100` | ~4.5 min |
| 9 | main-forest | `code/dml_plr.py --learner forest --splits 40` | ~8 min |
| 10 | main-boosting | `code/dml_plr.py --learner boosting --splits 30` | ~15 min |
| 11 | sens-lasso-c11 | `code/dml_plr.py --learner lasso --splits 100 --lasso-c-y 1.1 --run-id sens-lasso-c11` | ~14 min |
| 12 | verdict | `code/verdict.py` | seconds |
| 13 | fig-h2-diff | `-I code/fig_h2_diff.py --out paper/figures/fig_h2_diff.pdf --metrics runs/fig-h2-diff/metrics.json` | seconds |
| 14 | tab-port-check | `-I code/tab_port_check.py --out paper/tables/tab_port_check.tex --metrics runs/tab-port-check/metrics.json` | seconds |
| 15 | tab-side-by-side | `-I code/tab_side_by_side.py --out paper/tables/tab_side_by_side.tex --metrics runs/tab-side-by-side/metrics.json` | seconds |
| 16 | fig-split-spread | `-I code/fig_split_spread.py --out paper/figures/fig_split_spread.pdf --metrics runs/fig-split-spread/metrics.json` | seconds |

Rerun times are from a process monitor polling every 20 s, so they are approximate.
Then `crew.py numbers gallery/ss-dml-401k` regenerates `paper/numbers.tex` from
`claims.jsonl`, and the paper compiles from `paper/main.tex` (pdflatex, bibtex with
`refs.bib`, pdflatex twice).

## 4. Expected time

- **About 1 hour 40 minutes** on an 8-core laptop: the rerun took 6,087 s (101 min), from
  07:35:31Z to 09:16:58Z. The machine was shared: the load average was 3.3 at the start,
  then 20-166 from other sessions' jobs during most of the main runs (peak 166 at
  08:05Z, during main-lasso), and 20 at the end.
- About 90% of the time goes to the six `dml_plr.py` runs; main-lasso alone takes about
  40-50 minutes (51 minutes when first recorded, 39 minutes here). On an idle machine
  the total should be somewhat shorter.
- `dml_plr.py` and `check_learner_ports.py` parallelise over splits with joblib
  (`n_jobs=-1`). **`OMP_NUM_THREADS` was not set**: the machine was not overloaded when
  the rerun started (load 3.3 on 8 cores), and once it was running the workers kept
  making progress (about 40% CPU each at the peak) without the stalls seen in other
  workspaces, so it was not restarted. No thread setting changed any result.

## 5. Outcome of the rerun

**`replication.json`: PASSED, 16 of 16 runs reproduced** (created 2026-11-19T09:16:58Z;
rtol 1e-6, atol 1e-9, the protocol defaults; `reuse_data: false`).

| Run (in rerun order) | Status |
|---|---|
| fetch-sipp, prepare-sipp | match |
| timing-synthetic | ran (no metrics to compare: it records wall-clock timings only) |
| check-learner-ports, check-noctrl | match |
| main-lasso, main-tree, main-nnet, main-forest, main-boosting, sens-lasso-c11 | match |
| verdict | match |
| fig-h2-diff, tab-port-check, tab-side-by-side, fig-split-spread | match |

No run failed or mismatched, so there is no mismatch to explain. Notes:

- check-learner-ports also reproduced its R side (the Rscript calls) with the system R
  and package versions listed in section 1.
- timing-synthetic is recorded as `ran`: its outputs are timings, which are machine- and
  load-dependent by nature and are not compared. The paper's run-time statements come
  from the ledger, not from this rerun.
- The rerun is newer than every run record (latest: the figure and table runs,
  2026-11-19T07:04:32Z). After the rerun the SHA-256 of every `runs/<id>/run.json` still
  equals the `record_sha256` in `replication.json`, so no run was re-recorded while the
  rerun was going on.
- `crew.py rerun` copied the workspace at 07:35:31Z. Other crew members edited
  `claims.jsonl` and `paper/` during the rerun (log entries at 08:08Z and 08:10Z). Those
  edits do not change any run's command, inputs or recorded metrics, so they do not
  affect this result.

## 6. Procedure and workarounds

1. Fresh environment built outside the workspace (scratch directory, uv 0.7.15,
   CPython 3.12.11) from `code/requirements.txt` alone; `uv pip freeze` identical to the
   requirements file. R and its packages were the system installation, at the versions
   listed in the requirements comment.
2. The authors' `.venv` was parked at `gallery/.ss-dml-401k-venv-orig`, the fresh
   environment was symlinked at `.venv`, and an exit trap restored the original
   (restored 09:16:58Z; `.venv` is a real directory again and the parked copy is gone).
   The symlink was never committed (`.venv` is gitignored).
3. `crew.py rerun` was run detached with `nohup` so a session restart could not kill
   it. One attempt, no restarts.

Workarounds: none beyond the environment symlink. No code, data, metric or tolerance was
changed, `--reuse-data` was not used, and `OMP_NUM_THREADS` was not set.
