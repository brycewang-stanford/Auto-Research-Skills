# Run notes: cs-calibration (Experimenter)

## Status (2026-11-19 UTC)

The code is written; the unit tests ran as a data-prep run on synthetic data only. **No analysis run
has touched the study data.** design.method step 13 requires a Reviewer code review (target `code`)
with no open critical finding before `main`. If the review changes any file under `code/`, rerun
`unit-tests` with `--replace` first. Validation fails while a recorded code hash is stale.

| Order | Run id | Kind | Status |
|---|---|---|---|
| (done) | `timing-synthetic` | data-prep | designer, budget estimate |
| (done) | `fetch-data` | data-prep | data-ra, pinned data |
| 1 | `unit-tests` | data-prep | **done**: 32/32 tests passed, exit 0, synthetic only |
| 2 | code review | Reviewer, target `code` | **pending; blocks every run below** |
| 3 | `main` | analysis | not run |
| 4 | `h-tests` | analysis | not run (needs `main`) |
| 5 | `describe` | analysis | not run (needs `main`) |
| 6 | `sens-ncal` | analysis | not run (needs `main`: checks its base models against `results/cells.csv`) |
| 7 | `sens-elec-time` | analysis | not run |

## Code (all under `code/`)

| File | Run | Design step |
|---|---|---|
| `experiment.py` | `main`; also the shared library that the sensitivity scripts and tests import | 1-8 |
| `analyze.py` | `h-tests` (H1, H2a, H2b, and H1 on `ece_db` as sensitivity a) | 9-10, 12(a) |
| `describe.py` | `describe` | 11 |
| `sens_ncal.py` | `sens-ncal` | 12(b) |
| `sens_elec_time.py` | `sens-elec-time` | 12(c) |
| `test_metrics.py` | `unit-tests` | 13 |

The sensitivity scripts import `experiment.py`, so they reuse the main code's subsample, split,
preprocessing, model, calibrator and metric code rather than copies of it. Every run that imports a
file lists it as `--code`, so a later edit invalidates the run.

## Exact commands

All commands are run from the repository root. `crew.py run` executes the command with the workspace
as its working directory. Python is the workspace `.venv` (3.12.11, `code/requirements.txt`).

### 1. unit-tests (data-prep; done)

```bash
TMPDIR=<any scratch dir> python3 crew/scripts/crew.py run gallery/cs-calibration --id unit-tests --role experimenter --kind data-prep \
  --code code/test_metrics.py --code code/experiment.py --code code/analyze.py --code code/sens_ncal.py --code code/sens_elec_time.py \
  --metrics runs/unit-tests/metrics.json -- .venv/bin/python code/test_metrics.py
```

(`TMPDIR` only places the one throwaway toy CSV that the reader test writes; it does not affect results.)

### 3. main (analysis; only after the code review passes)

```bash
python3 crew/scripts/crew.py run gallery/cs-calibration --id main --role experimenter --kind analysis \
  --code code/experiment.py \
  --input data/manifest.json --input data/raw/adult.csv --input data/raw/bank-marketing.csv \
  --input data/raw/electricity.csv --input data/raw/phoneme.csv \
  --output results/cells.csv --output results/main_timing.json \
  --metrics runs/main/metrics.json -- .venv/bin/python code/experiment.py
```

Writes `results/cells.csv` (360 rows) and `results/main_timing.json`. It also writes 40 `.npz` files
under `results/preds/main/`, which are git-ignored and rebuilt by rerunning. **Budget check (step 14):**
read `cpu_minutes` in `results/main_timing.json` (the script also prints it). If it exceeds 30, stop
and tell the PI before any further run.

### 4. h-tests (analysis)

```bash
python3 crew/scripts/crew.py run gallery/cs-calibration --id h-tests --role experimenter --kind analysis \
  --code code/analyze.py --input results/cells.csv --output results/htests.csv \
  --metrics runs/h-tests/metrics.json -- .venv/bin/python code/analyze.py
```

### 5. describe (analysis)

```bash
python3 crew/scripts/crew.py run gallery/cs-calibration --id describe --role experimenter --kind analysis \
  --code code/describe.py --code code/analyze.py --input results/cells.csv \
  --output results/describe_summary.csv --output results/describe_paired.csv \
  --metrics runs/describe/metrics.json -- .venv/bin/python code/describe.py
```

### 6. sens-ncal (analysis)

```bash
python3 crew/scripts/crew.py run gallery/cs-calibration --id sens-ncal --role experimenter --kind analysis \
  --code code/sens_ncal.py --code code/experiment.py --code code/analyze.py \
  --input data/manifest.json --input data/raw/adult.csv --input data/raw/bank-marketing.csv \
  --input data/raw/electricity.csv --input results/cells.csv \
  --output results/sens_ncal_cells.csv --output results/sens_ncal_tests.csv \
  --metrics runs/sens-ncal/metrics.json -- .venv/bin/python code/sens_ncal.py
```

### 7. sens-elec-time (analysis)

```bash
python3 crew/scripts/crew.py run gallery/cs-calibration --id sens-elec-time --role experimenter --kind analysis \
  --code code/sens_elec_time.py --code code/experiment.py --code code/analyze.py \
  --input data/manifest.json --input data/raw/electricity.csv \
  --output results/sens_elec_time_cells.csv --output results/sens_elec_time_tests.csv \
  --metrics runs/sens-elec-time/metrics.json -- .venv/bin/python code/sens_elec_time.py
```

After all five runs: `python3 crew/scripts/crew.py validate gallery/cs-calibration`.

## Metric keys (for claims)

- `h-tests`: `{h1,h2a,h2b,h1db}_{adult,bank_marketing,electricity,phoneme}_{mean,sd,lo,hi,cat}`;
  `{h}_overall` (text), `{h}_overall_code`, `{h}_n_holds|n_contradicted|n_nodiff|n_inconclusive`.
  Category codes: 0 no difference, 1 holds, 2 contradicted, 3 inconclusive. Overall codes: 0 no
  difference, 1 supported, 2 contradicted, 3 inconclusive. `h1db` is sensitivity (a) and never
  changes H1.
- `describe`: `<ds>_<model>_<cal>_<metric>_{mean,sd}`; `<ds>_<model>_{platt_minus_none,iso_minus_platt}_<metric>_{mean,lo,hi}`;
  `<ds>_rf_minus_lr_none_{brier,logloss}_{mean,lo,hi}`; `lr_nonconverged_cells`, `hgb_n_iter_{min,max}`,
  `electricity_n_vicfill_{train,cal,test}_{mean,min,max}`.
- `sens-ncal`: `{h2a,h2b}_ncal_<ds>_{mean,sd,lo,hi,cat}`, `{h}_ncal_overall`; `<ds>_<model>_isoncal_<metric>_{mean,sd}`.
- `sens-elec-time`: `{h1,h2a,h2b}_time_electricity_{mean,sd,lo,hi,cat}` (no k-of-4 verdict);
  `electricity_time_<model>_<cal>_<metric>_{mean,sd}`; `n_vicfill_{train,cal,test}_{min,max}`.

## Implementation choices (within the design)

- `results/cells.csv` is deterministic. The run wrote byte-identical files twice on the synthetic
  smoke test, because floats are written with `%.17g` and round-trip exactly. Fit times are in the
  separate `results/main_timing.json` and are not metrics. This keeps the input hashes of
  `h-tests`, `describe` and `sens-ncal` valid after a clean rerun.
- `sens-ncal` rebuilds each main cell rather than unpickling models. It asserts that every base
  model's uncalibrated test Brier equals `results/cells.csv` exactly, so the frozen models are the
  ones `main` scored.
- `runs/main/metrics.json` carries counts and checks plus the grand mean Brier and ECE per dataset.
  The two means are for the clean-rerun comparison only and are not results to cite.
- Workers are loky processes (`N_JOBS = min(8, cpu_count)`) under `threadpool_limits(1)`. Results do
  not depend on `N_JOBS`.

## Things that surprised me (for the Reviewer and the PI)

1. **Isotonic on the logit is not exactly isotonic on the clipped probability.** design.method step 7
   says isotonic on the logit, "being rank-based, equals isotonic on the clipped probability." That
   holds at the calibration scores. But scikit-learn's `IsotonicRegression.predict` interpolates
   linearly *in the input scale* between thresholds, so a test point between two thresholds gets
   slightly different values on the two scales. On the synthetic unit-test models, the largest
   difference was 0.0002 (LR), 0.0010 (RF) and 0.0009 (HGB). The code does what the method
   prescribes: isotonic on the logit, through CalibratedClassifierCV. Only the parenthetical
   equivalence is inexact. Suggest rewording it in the paper ("equal at the calibration points;
   interpolation between them is linear in the logit").
2. **Kumar Def. G.3 removes only about 41% of the plug-in l1 floor on a well-calibrated bin, not
   "about the floor".** Under the normal approximation, the plug-in term has expectation
   0.798σ and ece_db has expectation (2 − √2)·0.798σ = 0.468σ, a ratio of 0.586. The unit test
   measured 0.559 on calibrated synthetic data with n = 5,000. For a strongly miscalibrated model,
   ece_db ≈ ece (0.2489 vs 0.2490), as the design says. So the threats text and step 8 overstate
   how much ece_db corrects for a calibrated model; sensitivity (a) will still be partly biased
   upward. This is the estimator's property, not a code issue: the implementation matches Def. G.3
   term by term (test `ece_db_matches_explicit_formula_and_draw_layout`). The PI should decide
   whether the paper's wording changes; the procedure does not.
3. The first synthetic smoke run of `experiment.py` failed in loky (the `__main__` worker could not
   be unpickled because of an `lru_cache`). Fixed by dispatching `experiment.main_cell` by module
   reference. No result was involved.

## Synthetic smoke test (not a ledger run)

Before recording `unit-tests`, all five analysis scripts ran end to end on a fully synthetic
workspace in the session scratch directory. It used make_classification data with the four study
shapes and column names, plus a synthetic manifest; no study file was read. The scripts wrote
360 / 90 / 90 cell rows, 40 + 30 + 10 `.npz` files and every metrics file. A rerun of `main` and
`sens-ncal` reproduced the CSVs byte for byte. Synthetic `main` took 1.19 CPU-minutes (11 s wall
on 8 workers). That run was for debugging only and is not evidence.
