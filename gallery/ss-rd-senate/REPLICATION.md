# Replication: ss-rd-senate

## Outcome of the clean rerun (2026-11-20)

Table below: the third run (crew.py commit 87890ae, `replication.json` created 07:16:07Z). The fourth run, described below, also passed 15 of 15.

`crew.py rerun` **PASSED**: 15 of 15 runs reproduced, in a fresh environment built from
`code/requirements.txt` alone (27 pinned packages, Python 3.12.11). `replication.json` has
`passed: true` and is newer than every run. The run record is in `replication.json`.

| Run | Status |
|---|---|
| fetch-data | match |
| prepare-data | match |
| dr-checks | match |
| design-mde | match |
| h1-rdrobust | match |
| h2-density | match |
| h2-covariates | match |
| h2-placebo | match |
| h2-selection | match |
| h3-sensitivity | match |
| unit-tests | match |
| fig-rd | match |
| fig-density | match |
| tab-falsification | match |
| tab-main | match |

Time: environment build about 30 seconds; rerun about 20 seconds (macOS, arm64). No
`--reuse-data` was used. No analysis code, data or tolerance was changed.

## Two attempts and the tool fix

**Attempt 1 (failed, 7 of 15 reproduced).** The rerun copy omitted `runs/`, so scripts that
write `runs/<id>/metrics.json` without creating the folder failed (fetch-data, prepare-data,
dr-checks, design-mde), and their dependents failed through the missing metrics file
(h2-covariates, tab-falsification, unit-tests). h2-density was flagged because `T_Q_asy` and
`p_Q_asy` are NaN in both the recorded and the rerun metrics, and the comparator treated
NaN as unequal.

**Tool fix.** Commit `0a72b72` (crew.py): `rerun` creates each run's folder as `run` does,
and a metric that is NaN in both runs counts as reproduced. A test was added. The PI
disclosed the fix in `plan.json`.

**Attempt 2 (passed, 15 of 15).** The same procedure, unchanged analysis code and tolerances,
on the fixed tool. The table in the outcome section is the third run (see the third-run paragraph below, commit 87890ae; `replication.json` created 07:16:07Z). Attempt 2's `replication.json` was overwritten by the third run;
attempt 1's record is preserved in git history at commit `2dce826`.

**Third run (passed, 15 of 15), same procedure.** Repeated after crew.py commit 87890ae,
which records each run's command interpreter in its `replication.json` entry and labels the
top-level `env.crew_python` as the tool's own interpreter. Attempt 2's record put Python 3.14
(the tool's interpreter) at the top level with no per-run version, so it did not show which
interpreter ran the analysis. In the third run, every run entry records `python: 3.12.11` and
`command_executable: .venv/bin/python`; the top-level `crew_python: 3.14.6` is the tool only.
Pass/fail is unchanged: 15 of 15 match.

**Fourth run (passed, 15 of 15), same procedure.** Repeated on crew.py main at a6d7c45
(`replication.json` created 07:31:59Z) because the Econometrician edited two claim texts in
`claims.jsonl` (values unchanged) and reran `tab-main` and `tab-falsification` with `--replace`,
which declare `claims.jsonl` as an input. The earlier `replication.json` was then older than
those two runs. Every run entry records `python: 3.12.11`. The table above is still the
third run's; the fourth run's per-run result is in `replication.json`, with 15 of 15 matching.

## Environment

- Python 3.12.11 (uv-managed), built outside the workspace from `code/requirements.txt` alone:
  `uv venv --python 3.12 <env>` then `uv pip install --python <env>/bin/python -r code/requirements.txt`.
- Pinned versions include `rdrobust==2.1.1` and `rddensity==3.0`.
- The workspace `.venv` was parked, replaced by a symlink to the fresh environment for the
  rerun, and restored afterwards. The symlink was never committed.

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

## Reproduce

```
cd gallery/ss-rd-senate
uv venv --python 3.12 /path/outside/workspace/.venv
uv pip install --python /path/outside/workspace/.venv/bin/python -r code/requirements.txt
ln -s /path/outside/workspace/.venv .venv      # after parking any existing .venv
python3 /path/to/crew/scripts/crew.py rerun .
```
