# Replication: ss-rd-senate

## Outcome of the clean rerun (2026-11-20)

`crew.py rerun` **FAILED**: 7 of 15 runs reproduced. `replication.json` has `passed: false`.
The `results` gate and the `submission` gate cannot pass on this file. Causes are listed below;
none is a metric that moved, except one NaN comparison (h2-density).

| Run | Status | Cause |
|---|---|---|
| h1-rdrobust | match | |
| h2-placebo | match | |
| h2-selection | match | |
| h3-sensitivity | match | |
| tab-main | match | |
| fig-rd | match | |
| fig-density | match | |
| fetch-data | failed | Script writes `runs/fetch-data/metrics.json`; directory absent in the rerun copy |
| prepare-data | failed | Same: `runs/prepare-data/metrics.json` |
| dr-checks | failed | Same: `runs/dr-checks/metrics.json` |
| design-mde | failed | Same: `runs/design-mde/metrics.json` |
| h2-covariates | failed | Reads `runs/design-mde/metrics.json`, missing because design-mde failed |
| tab-falsification | failed | Reads `runs/h2-covariates/metrics.json`, missing (downstream of h2-covariates) |
| unit-tests | failed | Runs h2_covariates.py, which fails as above |
| h2-density | mismatch | `T_Q_asy` and `p_Q_asy` are NaN in both the recorded and the rerun metrics; `same_value` uses `math.isclose`, which treats NaN as unequal |

### Diagnosis (for the PI; not fixed here)

1. **Missing run directories in the rerun copy.** `cmd_rerun` copies the workspace with
   `shutil.ignore_patterns("runs", "replication.json")`, so `runs/<id>/` does not exist in the
   copy. Scripts that do not call `os.makedirs` before writing their metrics file then fail.
   Scripts that do create the directory (h1-rdrobust and others) run fine. This is a defect in
   the rerun harness (`crew/scripts/crew.py`, `cmd_rerun`) together with scripts that assume
   the directory exists. The cascade (h2-covariates, tab-falsification, unit-tests) follows
   from design-mde failing.
2. **NaN comparison.** `T_Q_asy` / `p_Q_asy` come out NaN in the original run, so the recorded
   values are NaN. `rddensity`'s asymptotic test is NaN for this sample. The comparator in
   `crew.py` (`same_value`) returns unequal for NaN, so the run is flagged even though the
   value is identical in form. Either the metric should not be recorded when NaN, or the
   comparator should treat NaN == NaN. Tolerances were not changed.

No analysis code, data or tolerance was edited. No `--reuse-data` was used.

## Environment

- Python 3.12.11 (uv-managed), built outside the workspace from `code/requirements.txt` alone.
- `uv venv --python 3.12 <env>` then `uv pip install --python <env>/bin/python -r code/requirements.txt`
  (27 packages, pinned, including `rdrobust==2.1.1` and `rddensity==3.0`).
- The workspace `.venv` was parked and symlinked to the fresh environment for the rerun, then
  restored. The symlink was never committed.
- Platform of the original runs: macOS on arm64 (Python 3.12.11). The rerun record reports
  Python 3.14.6 for the crew tool itself; the analysis scripts run under `.venv/bin/python`.

## Data

- `data/raw/rdrobust_senate.csv`, fetched by `code/fetch_data.py` (run fetch-data) from the
  rdrobust repository at commit 2589686d. SHA-256 `def1fc6b…2ad44`, recorded in
  `data/manifest.json`. Raw data are not committed (`data/raw/` is gitignored).

## Commands, in order

1. `code/fetch_data.py` (fetch-data)
2. `code/prepare_data.py` (prepare-data)
3. `code/prepare_checks.py` (dr-checks)
4. `code/design_mde.py` (design-mde)
5. `code/h1_replication.py` (h1-rdrobust)
6. `code/h2_density.py` (h2-density)
7. `code/h2_covariates.py` (h2-covariates)
8. `code/h2_placebo.py` (h2-placebo)
9. `code/h3_sensitivity.py` (h3-sensitivity)
10. `code/h2_selection.py` (h2-selection)
11. `code/test_analysis.py` (unit-tests)
12. `code/fig_rd.py`, `code/fig_density.py`, `code/tab_main.py`, `code/tab_falsification.py`

Each command is the one recorded in `runs/<id>/run.json`, run from the workspace root with
`.venv/bin/python`.

## Time on a laptop

- Environment build: about 30 seconds (uv, 27 wheels, warm cache).
- Full rerun via `python3 crew/scripts/crew.py rerun <workspace>`: about 16 seconds on the
  machine used here (macOS, arm64).

## Reproduce

```
cd gallery/ss-rd-senate
uv venv --python 3.12 /path/outside/workspace/.venv
uv pip install --python /path/outside/workspace/.venv/bin/python -r code/requirements.txt
ln -s /path/outside/workspace/.venv .venv      # after parking any existing .venv
python3 /path/to/crew/scripts/crew.py rerun .
```

The rerun is expected to pass only after the two causes above are fixed by their owners.
