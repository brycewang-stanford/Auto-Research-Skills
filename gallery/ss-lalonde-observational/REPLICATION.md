# Replication: ss-lalonde-observational

How to reproduce every number in `paper/main.pdf` from this workspace, and what happened
when the Replicator did so. Current result: the clean rerun of 2026-11-19
(**passed, 19 of 19 runs reproduced**, `replication.json` created 2026-11-19T13:59:29Z).
Written by the Replicator; section 5 reports `replication.json`.

## 1. Environment

- Python 3.12 (the rerun used CPython 3.12.11 for the runs, macOS 26.6 arm64, 8 cores;
  `replication.json` records `python 3.14.6`, which is the interpreter that ran `crew.py`
  itself, not the runs' `.venv`).
- Packages: `code/requirements.txt` only (25 pinned packages: numpy 2.5.5, pandas 3.1.1,
  scikit-learn 1.9.1, scipy 1.18.1, statsmodels 0.15.0, matplotlib 3.11.2, pyreadstat 1.3.8,
  ...).
- The runs call `.venv/bin/python -I ...` from the workspace root, so the environment must
  live at `.venv` inside the workspace (a real directory or a symlink).

```bash
cd gallery/ss-lalonde-observational
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r code/requirements.txt
uv pip freeze --python .venv/bin/python | diff - <(sort code/requirements.txt)   # expect no output
```

The Replicator built this environment outside the workspace, confirmed that
`uv pip freeze` equals `code/requirements.txt` exactly (25 packages, nothing extra) and
that `uv pip check` passes, then symlinked it at `.venv` for the rerun. The authors'
`.venv` was moved aside to `gallery/.ss-lalonde-observational-venv-orig` and restored by an
exit trap when the rerun ended (13:59:29Z; a real directory again, no copy or symlink left).
No package beyond the requirements file was needed.

## 2. Data

Two public files from Rajeev Dehejia's data page (`data/manifest.json`; no licence stated,
used for non-commercial replication, not redistributed: `data/raw` and `data/derived` are
git-ignored):

| File | Origin | Rows | SHA-256 |
|---|---|---|---|
| `data/raw/nswre74_treated.txt` | https://users.nber.org/~rdehejia/data/nswre74_treated.txt | 185 | `e7b742fe...20eda3` |
| `data/raw/cps_controls.txt` | https://users.nber.org/~rdehejia/data/cps_controls.txt | 15,992 | `dce64006...51f8` |

`code/fetch_data.py` (run `fetch-data`) downloads both over HTTPS and checks row counts,
field counts and treat tokens; its metrics record the SHA-256 of each file. Everything
else in `data/derived` is produced by the runs (`prepare-data` writes
`analysis_noRE78.csv`; `main-aipw` writes `re78_by_key.csv`, the only derived file with
the outcome). Network access to `users.nber.org` is therefore required.

The rerun **re-downloaded** both files (no `--reuse-data`; `reuse_data: false`). The
fetched files had the recorded hashes (fetch-data matched on
`nswre74_treated_sha256` and `cps_controls_sha256`), so the source has not changed since
2026-11-19.

## 3. Commands

Automatic (what the Replicator ran):

```bash
python3 <repo>/crew/scripts/crew.py rerun gallery/ss-lalonde-observational
python3 <repo>/crew/scripts/crew.py validate gallery/ss-lalonde-observational --strict
```

No environment variable is needed. The analysis commands set `OMP_NUM_THREADS=1`
themselves (`env OMP_NUM_THREADS=1 ...`, recorded in each `run.json`); the four data-prep
runs before the design gate use the default thread count, as recorded.

By hand, from the workspace root, in the order `crew.py rerun` used (a run comes after
every run that produced one of its inputs, otherwise the order the runs were recorded);
each writes the metrics file recorded in `runs/<id>/run.json`:

| # | Run | Command |
|---|---|---|
| 1 | fetch-data | `.venv/bin/python -I code/fetch_data.py` |
| 2 | prepare-data | `.venv/bin/python -I code/prepare_data.py` |
| 3 | timing-synthetic | `.venv/bin/python -I code/timing_synthetic.py` |
| 4 | diag-overlap | `.venv/bin/python -I code/diag_overlap.py` |
| 5 | unit-tests | `env OMP_NUM_THREADS=1 .venv/bin/python -I code/test_analysis.py` (synthetic data only) |
| 6 | main-aipw | `env OMP_NUM_THREADS=1 .venv/bin/python -I code/main_aipw.py` (joins re78) |
| 7 | placebo-re75 | `... code/placebo_re75.py` |
| 8 | rob-trim | `... code/rob_trim.py` |
| 9 | rob-learners | `... code/rob_learners.py` |
| 10 | rob-covsets | `... code/rob_covsets.py` |
| 11 | rob-estimators | `... code/rob_estimators.py` |
| 12 | rob-diff74 | `... code/rob_diff74.py` |
| 13 | sens-imbens | `... code/sens_imbens.py` |
| 14 | post-results-derived | `... code/post_results_derived.py` |
| 15 | h2-benchmark | `... code/h2_benchmark.py` (refuses unless `plan.json` has the results gate approved) |
| 16-18 | fig-overlap, fig-forest, fig-sensitivity | `... code/fig_<name>.py --out paper/figures/fig_<name>.pdf --metrics runs/fig-<name>/metrics.json` |
| 19 | tab-main | `... code/tab_main.py --out paper/tables/tab_main.tex --metrics runs/tab-main/metrics.json` |

(`...` is `env OMP_NUM_THREADS=1 .venv/bin/python -I`.) `rob-ipow` has no run: its
missing-outcome trigger did not fire (runs/NOTES.md). Then `crew.py numbers
gallery/ss-lalonde-observational` regenerates `paper/numbers.tex` from `claims.jsonl`,
and the paper compiles from `paper/main.tex`.

## 4. Expected time

- **About 15 minutes** on an 8-core laptop: the passing rerun took 859 s wall time
  (13:45:10Z to 13:59:29Z), with load average 3.0 at the start and 10-15 at the end from
  other sessions' jobs.
- The ledger's own timings sum to 842 s. The longest steps are unit-tests (about 4.5 min,
  two end-to-end synthetic pipelines), timing-synthetic (about 3 min) and the robustness
  runs (20-95 s each).
- On a heavily loaded machine, scikit-learn's HistGradientBoosting can spin-wait in
  libomp (runs/NOTES.md, code-r1 F1); the analysis runs already use one thread for this
  reason. If the pre-gate data-prep runs stall, `export OMP_NUM_THREADS=1` is safe: fitted
  values do not depend on the thread count (unit test `test_hgb_thread_invariance`). The
  Replicator did not need it.

## 5. Outcome of the rerun: 2026-11-19, PASSED (19 of 19)

**`replication.json`: PASSED, 19 of 19 runs reproduced** (created 2026-11-19T13:59:29Z;
rtol 1e-6, atol 1e-9, the protocol defaults; `reuse_data: false`).

- Fresh environment built outside the workspace from `code/requirements.txt` alone
  (section 1), symlinked at `.venv`, authors' `.venv` restored afterwards.
- Run detached with `nohup`, so a session restart could not kill it (the session did
  restart while it ran; the rerun and the restore completed).
- No code, data, setting or tolerance was changed; no environment variable was set.

| Run (in rerun order) | Status |
|---|---|
| fetch-data, prepare-data, timing-synthetic, diag-overlap, unit-tests | match |
| main-aipw, placebo-re75, rob-trim, rob-learners, rob-covsets, rob-estimators, rob-diff74 | match |
| sens-imbens, post-results-derived, h2-benchmark | match |
| fig-overlap, fig-forest, fig-sensitivity, tab-main | match |

Every run exited 0 and every recorded metric matched. Notes:

- The `record_sha256` of every run in `replication.json` equals the current
  `runs/<id>/run.json`, and the rerun is newer than every run (latest run finished
  2026-11-19T13:15:43Z).
- tab-main and the three figure runs read only the metrics of the logged analysis runs
  (`code/figlib.py`; no new estimate, no read of `claims.jsonl`), and were regenerated
  from the rerun's own metrics; their recorded metrics matched. The paper's quoted
  numbers come from `claims.jsonl` macros, whose values `crew.py validate` checks against
  the runs' metrics.
- timing-synthetic's metrics are its fixed settings (n, folds, seed, basis sizes); the
  measured times in `timing.json` are not compared, by design.

No mismatch to explain.
