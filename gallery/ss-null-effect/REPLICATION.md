# Replication: ss-null-effect

How to reproduce every number in `paper/main.pdf` from this workspace, and what happened
when the Replicator did so. The current result is the clean rerun of 2026-11-19
(**passed, 23 of 23 runs**); the failed rerun of 2026-11-18 is kept below (section 5.2).
Written by the Replicator; the outcome section reports `replication.json`.

## 1. Environment

- Python 3.12 (both reruns used CPython 3.12.11 for the runs, macOS 26.6 arm64, 8 cores;
  `replication.json` records `python 3.14.6`, which is the interpreter that ran `crew.py`
  itself, not the runs' `.venv`).
- Packages: `code/requirements.txt` only (25 pinned packages: numpy 2.5.5, pandas 3.1.1,
  scikit-learn 1.9.1, scipy 1.18.1, statsmodels 0.15.0, matplotlib 3.11.2, ...).
- The runs call `.venv/bin/python -I ...` from the workspace root, so the environment must
  live at `.venv` inside the workspace (a real directory or a symlink).

```bash
cd gallery/ss-null-effect
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r code/requirements.txt
uv pip freeze --python .venv/bin/python | diff - <(sort code/requirements.txt)   # expect no output
```

The Replicator built this environment outside the workspace, confirmed that
`uv pip freeze` equals `code/requirements.txt` exactly (25 packages, nothing extra) and
that `uv pip check` passes, then symlinked it at `.venv` for the rerun (the authors'
`.venv` was moved aside and restored afterwards). No package beyond the requirements
file was needed.

## 2. Data

One dataset (`data/manifest.json`): the synthetic extract
`crew/bench/seeds/ss-null-effect/data.csv` shipped in this repository (CC0-1.0),
SHA-256 `f09fba86...6048ca9`, 483,855 bytes, 4,000 rows. `code/fetch_data.py` (run
`fetch-data`) copies it to `data/raw/null_extract.csv` and checks the hash.

The script finds the seed by walking up from the current directory to the repository
root. `crew.py rerun` executes in a temporary copy outside the repository, so the walk
fails there; set

```bash
export CREW_SEED_DIR=<repo>/crew/bench/seeds/ss-null-effect
```

before rerunning. The Replicator did this; the data were re-copied and re-verified, not
reused (`reuse_data: false`).

## 3. Commands

Automatic (what the Replicator ran):

```bash
export CREW_SEED_DIR=<repo>/crew/bench/seeds/ss-null-effect
export OMP_NUM_THREADS=1            # strongly advised on a shared machine (section 4)
python3 <repo>/crew/scripts/crew.py rerun gallery/ss-null-effect
python3 <repo>/crew/scripts/crew.py validate gallery/ss-null-effect --strict
```

By hand, from the workspace root, in this order (the order `crew.py rerun` used on
2026-11-19: a run comes after every run that produced one of its inputs, otherwise the
order the runs were recorded; each writes the metrics file recorded in
`runs/<id>/run.json`):

| # | Run | Command (`.venv/bin/python -I ...`) |
|---|---|---|
| 1 | fetch-data | `code/fetch_data.py` |
| 2 | prepare-covariates | `code/prepare_covariates.py` |
| 3 | margin | `code/margin.py` (needs `data/derived/covariates.csv` from step 2) |
| 4 | timing-synthetic | `code/timing_synthetic.py` |
| 5 | diag-overlap | `code/diag_overlap.py` |
| 6 | missing-counts | `code/missing_counts.py` |
| 7 | range-counts | `code/range_counts.py` |
| 8 | main-aipw | `code/main_aipw.py` |
| 9 | secondary-family | `code/secondary_family.py` |
| 10 | select-re75 | `code/select_re75.py` |
| 11 | rob-trim | `code/rob_trim.py` |
| 12 | rob-covsets | `code/rob_covsets.py` |
| 13 | rob-diff74 | `code/rob_diff74.py` |
| 14 | rob-estimators | `code/rob_estimators.py` |
| 15 | sens-imbens | `code/sens_imbens.py` |
| 16-17 | fig-propensity, fig-sensitivity | `code/fig_<name>.py --out paper/figures/fig_<name>.pdf --metrics runs/fig-<name>/metrics.json` |
| 18 | rob-learners | `code/rob_learners.py` (re-recorded 2026-11-19, runs/NOTES.md; any position after step 7 works) |
| 19 | fig-forest | as steps 16-17 (reads rob-learners) |
| 20-23 | tab-balance, tab-main, tab-secondary, tab-sensitivity | `code/tab_<name>.py --out paper/tables/tab_<name>.tex --metrics runs/tab-<name>/metrics.json` |

Then `crew.py numbers gallery/ss-null-effect` regenerates `paper/numbers.tex` from
`claims.jsonl`, and the paper compiles from `paper/main.tex`.

## 4. Expected time

- **About 3 minutes** on an 8-core laptop with `OMP_NUM_THREADS=1`: the passing rerun of
  2026-11-19 took 183 s (load average 14-22 from other sessions); the 2026-11-18 rerun
  took 160 s and a diagnostic rerun 137 s, at load average 20-30.
- With the default OpenMP thread count on an idle machine, the ledger's own timings
  suggest roughly 6-8 minutes. secondary-family's recorded 30.5 minutes was measured while
  another job loaded the machine (runs/NOTES.md); the plan expects about 2.
- **Set `OMP_NUM_THREADS=1` on a shared or busy machine.** scikit-learn's
  HistGradientBoosting (used by main-aipw, the shared `aipw_lib.py` and timing-synthetic)
  parallelises with libomp, whose spin barriers collapse under oversubscription. With
  default threads and a load average of 60-160 from other jobs, timing-synthetic alone ran
  74 minutes without finishing; a stack sample showed all of its OpenMP threads in
  `__kmp_barrier` / `cthread_yield`. The thread count did not change any result: with
  `OMP_NUM_THREADS=1`, every metric except the random-forest ones below is bit-identical
  to the ledger, which was produced with default threads (2026-11-18; the random-forest
  metrics were made thread-stable on 2026-11-19, section 5.1).

## 5. Outcome of the rerun

### 5.1 Current: 2026-11-19, PASSED (23 of 23)

**`replication.json`: PASSED, 23 of 23 runs reproduced** (created 2026-11-19T01:26:40Z;
`crew.py rerun` started 01:23:37Z, wall time 183 s). Same method as the 2026-11-18 rerun:

- Fresh environment built outside the workspace from `code/requirements.txt` alone
  (CPython 3.12.11; `uv pip freeze` equal to the requirements file, 25 packages, nothing
  extra; `uv pip check` clean), symlinked at `.venv`; the authors' `.venv` was parked at
  `gallery/.ss-null-effect-venv-orig` and restored by an exit trap (restored 01:26:40Z,
  a real directory again).
- `CREW_SEED_DIR=<repo>/crew/bench/seeds/ss-null-effect`; data re-copied and re-verified,
  not reused (`reuse_data: false`).
- **`OMP_NUM_THREADS=1`** set as an environment setting, because the machine was shared
  (load average 17.7 at start, 13.8 at the end, on 8 cores). No code, data or tolerance
  was changed (rtol 1e-6, atol 1e-9, the protocol defaults).
- Run detached with `nohup` so a session restart could not kill it.

| Run (in rerun order) | Status |
|---|---|
| fetch-data, prepare-covariates, margin, timing-synthetic, diag-overlap, missing-counts, range-counts | match |
| main-aipw, secondary-family, select-re75, rob-trim, rob-covsets, rob-diff74, rob-estimators, sens-imbens | match |
| fig-propensity, fig-sensitivity, rob-learners, fig-forest | match |
| tab-balance, tab-main, tab-secondary, tab-sensitivity | match |

Both causes of the 2026-11-18 failure (section 5.2) were fixed by their owners before this
rerun, and the rerun confirms both fixes:

- **Cause A fixed in the tooling** (commit `716b6c3`): `crew.py rerun` now orders runs so
  that a run comes after every run that produced one of its inputs, with ties broken by
  start time, finish time, then id. margin ran third, after prepare-covariates, and
  matched; so did all eight analysis runs that read its `margin_metrics.json`.
- **Cause B fixed by the Econometrician** (runs/NOTES.md, "Implementation fix:
  rob-learners made bit-stable"; commit `9f3133a`): the random forests are still fitted
  with `n_jobs=-1` but predict with `n_jobs=1`, so the per-tree sum has a fixed order.
  rob-learners and the downstream figure/table runs were re-recorded with `--replace`
  (which is why rob-learners now runs after fig-sensitivity). tab-main, whose
  `figlib.Macros.cell` requires each claimed value to equal the recomputed metric
  *exactly*, passed: the claimed rob-learners metrics it prints (random-forest and linear
  effect, SE, 95% and 90% bounds, p, p_TOST, n) were therefore bit-identical to the
  record. `replication.json` itself records match at tolerance, not exact equality.

No mismatch to explain. The rerun is newer than every run record (latest re-record
2026-11-19T01:22:19Z).

### 5.2 Earlier: 2026-11-18, FAILED (10 of 23), kept for the record

**`replication.json` (since overwritten): FAILED, 10 of 23 runs reproduced**
(2026-11-18T17:27:41Z; fresh environment; `OMP_NUM_THREADS=1`; data re-fetched; rtol 1e-6,
atol 1e-9). Every run that
executed matched its recorded metrics; the 13 failures are crashes with two causes. Neither
cause is a wrong number in the paper.

| Run | Status | Cause |
|---|---|---|
| fetch-data, prepare-covariates, timing-synthetic, diag-overlap, missing-counts, range-counts, secondary-family, fig-propensity, tab-balance, tab-secondary | match | |
| margin | failed | A (FileNotFoundError: data/derived/covariates.csv) |
| main-aipw, select-re75, rob-trim, rob-covsets, rob-learners, rob-diff74, rob-estimators, sens-imbens | failed | A (cascade: data/derived/margin_metrics.json missing) |
| fig-forest, tab-main, fig-sensitivity, tab-sensitivity | failed | A (cascade: runs/main-aipw or runs/sens-imbens metrics missing) |

#### Cause A: two runs share a start time and the rerun orders them wrongly

`margin` reads `data/derived/covariates.csv`, which `prepare-covariates` writes. In the
ledger both runs have `started = 2026-11-18T12:28:10Z`; prepare-covariates finished within
that second (`finished` 12:28:10Z, margin's 12:28:11Z). `crew.py rerun` orders runs by
`(started, id)`, so the tie is broken alphabetically, `margin` runs first, and it crashes on
the missing file. All eight analysis runs read `margin_metrics.json` (the margin M), so
they crash too, and so do the figure and table runs built from their metrics. The tie is a
side effect of the data-prep reruns before the design gate (runs/NOTES.md): prepare-covariates
was re-run with `--replace` and margin immediately after.

Evidence: in a scratch copy, `margin.py` run first fails with this error; run after
`prepare_covariates.py`, it writes M = 483.47 with every metric equal to the ledger, and
the regenerated `covariates.csv` has the recorded SHA-256 `4118e964...6843459`.

Who can fix it: either the owner of `margin` (Data RA) re-records it with
`crew.py run --replace` so that it starts after prepare-covariates (same command, same
output), or the crew tooling breaks start-time ties by `finished` or by declared inputs and
outputs. The Replicator changed neither.

#### Cause B: tab-main needs bit-identical random-forest results, which rob-learners does not give

A diagnostic rerun with the same procedure, environment and tolerance, but with ties broken
by `finished` (script and output kept outside the workspace, so `replication.json` is the
tool's unmodified result), reproduced **22 of 23 runs**: everything in the table above,
including all eight analysis runs and all figures, matched. Every metric was
bit-identical to the ledger except the eight random-forest metrics of rob-learners
(`rf_effect`, `rf_ci_low`, `rf_ci_high`, `rf_ci90_low`, `rf_ci90_high`, `rf_p`,
`rf_p_tost`, `rf_min_margin`), which differed only in the last bits (relative
differences 2e-16 to 2e-15; `rf_effect` -10.006344405782134 recorded, -10.006344405782112
rerun). rob-learners therefore matches at the protocol tolerance.

The one failure was **tab-main**: `code/tab_main.py` calls `figlib.Macros.cell`, which
asserts that a claim's value in `claims.jsonl` equals the freshly computed metric
*exactly* (`claim["value"] != value` raises), and it stops at
`AssertionError: claim learner-rf-ci-low value -358.0902593943298 != rob-learners:rf_ci_low
-358.09025939432973`.

The last-bit noise is not caused by the environment. Five repeated runs of `rob_learners.py`
on identical inputs gave five different `rf_effect` values (-10.006344405782125, ...098,
...118 with default threads; ...148, ...144 with `OMP_NUM_THREADS=1`). The random forests
use `n_jobs=-1`, and scikit-learn 1.9.1's forest `predict` adds each tree's prediction
into a shared array under a lock, in whatever order the threads finish
(`sklearn/ensemble/_forest.py`, `_accumulate_prediction`). Floating-point addition is not
associative, so the sum changes in the last bits from run to run. runs/NOTES.md
(implementation choice 4) describes the forests as "deterministic given random_state",
which holds for the fitted trees but not for the summed prediction. tab-main will
therefore fail on most clean reruns, whatever the run order.

Who can fix it: the owners of rob-learners (Econometrician) and tab-main (Figures RA).
Either rob-learners is made bit-stable (for example single-threaded prediction) and re-run
with its claims refreshed, or the table check compares at a stated tolerance. No published
number would change at the precision printed (the claims are formatted to whole dollars: -10 and
[-358, 338]).

#### What reproduced on 2026-11-18

Every number the analysis runs produce reproduces at the protocol tolerance from a fresh
environment and re-fetched data, and all but the eight random-forest metrics reproduce bit
for bit. The crew's submission check still fails: `replication.json` reports
`passed: false` until causes A and B are fixed by their owners and the Replicator reruns.
(Both were fixed on 2026-11-19; see section 5.1.)

## 6. Attempts and workarounds

1. **First attempt (killed).** Started 2026-11-18T15:03:31Z from the same fresh
   environment; a session restart killed it before it finished. Its temporary copy showed
   fetch-data and prepare-covariates done, no margin output (cause A), and no `runs/`
   directory yet, so it died during timing-synthetic. It wrote no `replication.json` and
   no log entry. The workspace `.venv` was restored afterwards; the Replicator removed the
   orphaned temporary copy.
2. **Second attempt (stopped by the Replicator).** Started 16:10:32Z with default
   threads. Other sessions' jobs (16 joblib workers) pushed the load average to 60-160 on
   8 cores, and timing-synthetic stalled in libomp barriers (section 4). Stopped at
   17:24:48Z after 74 minutes; nothing was written to the workspace.
3. **Recorded rerun (failed).** 17:25:01Z to 17:27:41Z (160 s) with `OMP_NUM_THREADS=1` and
   `CREW_SEED_DIR` set; result in section 5.2.
4. **Diagnostic reruns (not recorded).** Two runs of the same procedure with ties broken by
   `finished` (about 2-3 minutes each with `OMP_NUM_THREADS=1`; 137 s for the second), plus repeated `rob_learners.py`
   runs, all in scratch copies with the fresh environment.
5. **Clean rerun after the fixes (passed).** 2026-11-19T01:23:37Z to 01:26:40Z (183 s),
   detached with `nohup`, same fresh environment and settings (`OMP_NUM_THREADS=1`,
   `CREW_SEED_DIR`, no `--reuse-data`); result in section 5.1. Nothing had to be worked
   around beyond the settings listed below.

Workarounds, all environmental, none in the analysis: the fresh environment was
symlinked at `.venv` and the original restored after each attempt; `CREW_SEED_DIR` was set
because the rerun's temporary copy is outside the repository; `OMP_NUM_THREADS=1` was set
because of CPU contention. No code, data, metric or tolerance was changed, and
`--reuse-data` was not used.
