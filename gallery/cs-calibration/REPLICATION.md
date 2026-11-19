# Replication: cs-calibration

This file explains how to reproduce every number in `paper/main.pdf` from this workspace,
and reports what happened when the Replicator did so. Result of the clean rerun of
2026-11-19: **passed, 13 of 13 runs reproduced** (`replication.json`, created
2026-11-19T12:52:00Z). Written by the Replicator. The outcome section reports
`replication.json`.

## 1. Environment

- **Python 3.12.** The rerun used CPython 3.12.11 for every run (macOS 26.6.2 arm64,
  8 cores). That is the interpreter version recorded in each `runs/<id>/run.json`.
  `replication.json` records `python 3.14.6`, which is the interpreter that ran `crew.py`
  itself, not the runs' `.venv`.
- **Python packages:** `code/requirements.txt` only. It pins 25 packages, including
  numpy 2.5.5, pandas 3.1.1, scipy 1.18.1, scikit-learn 1.9.1, statsmodels 0.15.0,
  matplotlib 3.11.2 and joblib 1.6.0. The runs need no R, Stata or LaTeX. LaTeX is needed
  only to compile the paper (section 3).
- **Seeds are fixed in code.** `code/experiment.py` derives every random stream from the
  (dataset, seed) pair, for seeds 0-9. Each model is fit with `n_jobs=1` under
  `threadpool_limits(1)`, and joblib parallelises over cells only, with
  `N_JOBS = min(8, cpu_count)`. The results should therefore not depend on the number of
  workers. The rerun used 8 workers, the same as the original runs, so this was not tested
  with any other worker count.
- The runs call `.venv/bin/python code/<script>.py ...` from the workspace root, so the
  environment must live at `.venv` inside the workspace. It can be a real directory or a
  symlink.

```bash
cd gallery/cs-calibration
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r code/requirements.txt
uv pip freeze --python .venv/bin/python | diff - <(grep -v '^#' code/requirements.txt | sort)   # expect no output
```

The Replicator built the environment outside the workspace with uv 0.7.15 and confirmed
that `uv pip freeze` matches `code/requirements.txt` exactly: 25 packages, nothing extra.
The environment was then symlinked at `.venv` for the rerun. The runs needed nothing beyond
the requirements file.

## 2. Data

There are four public OpenML datasets, pinned in `data/manifest.json` and described in
`data/CODEBOOK.md`:

- adult: OpenML id 1590, version 2, file 1595261
- bank-marketing: OpenML id 1461, version 1, file 1586218
- electricity: OpenML id 151, version 1, file 2419
- phoneme: OpenML id 1489, version 1, file 1592281

Run `fetch-data` (`code/fetch_data.py`) downloads them with
`sklearn.datasets.fetch_openml` into `data/raw/sklearn_home/`, which needs network
access. It checks the data id, name, version, file id and md5 of each ARFF against the pins
and the published qualities, then writes `data/raw/<name>.csv` and `data/manifest.json`.
Everything under `data/raw/` and `results/preds/` is git-ignored, and nothing is
redistributed.

**The cached download is not a recorded output.** `crew.py rerun` copies the whole
workspace and deletes only the files that the runs recorded as outputs. Run `fetch-data`
records the four CSVs and the manifest, but not its download cache
`data/raw/sklearn_home/`. That cache was therefore copied in, and the rerun's `fetch-data`
rebuilt the CSVs from the cached ARFF files without contacting OpenML. This is not a
mismatch: the script re-checks the md5 of each cached ARFF against OpenML's pinned
checksum, and the rebuilt CSVs matched. Still, the rerun alone does not show that the
download step works from scratch.

To close that gap, the Replicator also ran `code/fetch_data.py` (unmodified) with the fresh
environment in an empty scratch directory with no cache. That run downloaded all four
datasets from OpenML (exit 0, about 100 s), and the results matched the workspace:

- The SHA-256 of all four CSVs equals `data/manifest.json` (adult `0626dc27…`,
  bank-marketing `0e933553…`, electricity `a882e1fb…`, phoneme `4f8eecda…`).
- All 32 `fetch-data` metrics equal the recorded ones.

So the data as served by OpenML on 2026-11-19T12:53Z was identical to the first retrieval.

## 3. Commands

These are the automatic commands the Replicator ran:

```bash
python3 <repo>/crew/scripts/crew.py rerun gallery/cs-calibration
python3 <repo>/crew/scripts/crew.py validate gallery/cs-calibration --strict
```

To run the same steps by hand, work from the workspace root and follow the order that
`crew.py rerun` used. A run comes after every run that produced one of its inputs;
otherwise runs keep the order in which they were first recorded. Every command is
`.venv/bin/python code/<script> ...`, and each command writes the metrics file recorded
in `runs/<id>/run.json`.

| # | Run | Script and arguments | Writes besides metrics |
|---|---|---|---|
| 1 | fetch-data | `code/fetch_data.py` | `data/raw/{adult,bank-marketing,electricity,phoneme}.csv`, `data/raw/sklearn_home/`, `data/manifest.json`, `runs/fetch-data/profile.json` |
| 2 | timing-synthetic | `code/timing_synthetic.py` | `runs/timing-synthetic/timing.json` |
| 3 | unit-tests | `code/test_metrics.py` | (33 tests, uses no study data) |
| 4 | main | `code/experiment.py` | `results/cells.csv`, `results/main_timing.json`, `results/preds/main/*.npz` (40 files, git-ignored) |
| 5 | h-tests | `code/analyze.py` | `results/htests.csv` |
| 6 | describe | `code/describe.py` | `results/describe_summary.csv`, `results/describe_paired.csv` |
| 7 | sens-ncal | `code/sens_ncal.py` | `results/sens_ncal_cells.csv`, `results/sens_ncal_tests.csv` |
| 8 | sens-elec-time | `code/sens_elec_time.py` | `results/sens_elec_time_cells.csv`, `results/sens_elec_time_tests.csv` |
| 9 | tab-decision | `code/tab_decision.py --out paper/tables/tab_decision.tex --metrics runs/tab-decision/metrics.json` | `paper/tables/tab_decision.tex` |
| 10 | tab-levels | `code/tab_levels.py --out paper/tables/tab_levels.tex --metrics runs/tab-levels/metrics.json` | `paper/tables/tab_levels.tex` |
| 11 | tab-sensitivity | `code/tab_sensitivity.py --out-tests paper/tables/tab_sensitivity.tex --out-elec paper/tables/tab_elec_time.tex --metrics runs/tab-sensitivity/metrics.json` | `paper/tables/tab_sensitivity.tex`, `paper/tables/tab_elec_time.tex` |
| 12 | fig-reliability | `code/fig_reliability.py --out paper/figures/fig_reliability.pdf --metrics runs/fig-reliability/metrics.json` | `paper/figures/fig_reliability.pdf` (reads `results/preds/main/*.npz`) |
| 13 | fig-intervals | `code/fig_intervals.py --out paper/figures/fig_intervals.pdf --metrics runs/fig-intervals/metrics.json` | `paper/figures/fig_intervals.pdf` |

Run `main` must come before `fig-reliability`, because the figure reads the git-ignored
prediction files that only `main` writes. After the runs, `crew.py numbers
gallery/cs-calibration` regenerates `paper/numbers.tex` from `claims.jsonl`. The paper then
compiles from `paper/main.tex`: run pdflatex, then bibtex with `refs.bib` and
`paper/plainnat-crew.bst`, then pdflatex twice.

## 4. Expected time

**About 2 minutes on a laptop, plus about 2 minutes if the data must be downloaded.**

- The whole rerun took 95 s of wall-clock time (12:50:25Z to 12:52:00Z) on an 8-core
  Apple-silicon laptop. The load average was about 5 when it started. Run `main` is the
  largest step: the original took 23 s of wall-clock time and 2.55 CPU-minutes on 8
  workers.
- The cold download in section 2 added about 100 s.
- Building the environment with uv took well under a minute, because the packages were
  already in uv's cache. A cold install downloads 25 wheels.

## 5. Outcome of the rerun

**`replication.json`: PASSED, 13 of 13 runs reproduced** (created 2026-11-19T12:52:00Z).
The rerun used the protocol defaults, rtol 1e-6 and atol 1e-9, with `reuse_data: false`.

| Run (in rerun order) | Status |
|---|---|
| fetch-data, timing-synthetic, unit-tests | match |
| main | match |
| h-tests, describe | match |
| sens-ncal, sens-elec-time | match |
| tab-decision, tab-levels, tab-sensitivity | match |
| fig-reliability, fig-intervals | match |

Every run exited 0 and every recorded metric matched, so there is no mismatch to explain.
That covers 42 metrics for `main`, 106 for `h-tests`, 986 for `describe`, 144 for
`sens-ncal` and 116 for `sens-elec-time`. The per-dataset H1, H2a and H2b intervals and
categories in the paper are among them. Notes:

- **The prediction files used by fig-reliability.** `results/preds/` is git-ignored and
  is not a recorded output of `main`, so the copied workspace still held the old files
  when the rerun started. `main` writes all 40 files on every run (`save_preds` inside the
  loop over the 40 dataset-seed cells), so the rerun's `fig-reliability` read the files
  that the rerun itself produced. The figure's own check confirms this:
  `ece_matches_describe_1e12 = 1` recomputes ECE from those prediction files and compares
  it with the rerun's `describe` metrics.
- **The rerun compares metrics, not output bytes.** The metrics of the table and figure
  runs matched. The regenerated `.tex` and `.pdf` files in the temporary copy were not
  byte-compared with the committed ones.
- **No run changed during the rerun.** The rerun is newer than every run record; the
  latest is fig-intervals, 2026-11-19T12:39:10Z. After the rerun, the SHA-256 of every
  `runs/<id>/run.json` still equals the `record_sha256` in `replication.json`.
- **unit-tests uses its current record.** The record of the first unit-tests run is
  archived under `runs/.superseded/` and is not rerun. The current record (33 of 33 tests
  passed) is the one that was rerun.

## 6. Procedure and workarounds

1. The Replicator built a fresh environment outside the workspace (a scratch directory,
   uv 0.7.15, CPython 3.12.11) from `code/requirements.txt` alone. Its `uv pip freeze`
   matches the requirements file exactly.
2. The authors' `.venv` was moved aside to `gallery/.cs-calibration-venv-orig`, and the
   fresh environment was symlinked at `.venv`. An exit trap restored the original at
   12:52:00Z: `.venv` is a real directory again and the moved copy is gone. The symlink was
   never committed, since `.venv` is git-ignored.
3. `crew.py rerun` (without `--reuse-data`) was run detached with `nohup`. There was one
   attempt and no restarts.
4. The cold-download check of `fetch_data.py` in section 2 ran separately, in a scratch
   directory, after the rerun.

The environment symlink was the only workaround. No code, data, metric or tolerance was
changed, and `--reuse-data` was not used. One finding goes to the PI, and it is not
blocking: `fetch-data` does not record `data/raw/sklearn_home/` as an output, so a clean
rerun reuses the download cache. The md5 checks make this safe, and the separate cold
download confirmed the same data.
