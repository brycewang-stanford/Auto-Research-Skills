# Run notes: cs-calibration (Experimenter)

## Status (2026-11-19 UTC)

Every planned run is done, in the planned order, with the commands below. The five analysis runs
each ran once and were not repeated or changed after their results were seen. The data-prep run
`unit-tests` ran twice: the second time with `--replace`, after the code-r1 F1 fix and before
`main`. The first record is archived under `runs/.superseded/`.

| Order | Run id | Kind | Status |
|---|---|---|---|
| (done) | `timing-synthetic` | data-prep | designer, budget estimate |
| (done) | `fetch-data` | data-prep | data-ra, pinned data |
| 1 | `unit-tests` | data-prep | done 07:28Z (32/32); rerun `--replace` 07:43Z after code-r1 F1: **33/33 passed** |
| 2 | code review | Reviewer, `code-r1` | verdict revise, 0 critical. F1 (code) fixed. F2/F3 (plan wording) were narrowed by the designer: `plan-narrowed` log entry 07:41:34Z, plan sha256 `bee7499f…`. The diff changes only step 7/8, threats[0], the H1 label and contribution wording; procedure, metric, margin and rule are unchanged |
| 3 | `main` | analysis | done 07:43Z; **2.55 CPU-minutes**, 23 s wall (under the 30 CPU-minute stop) |
| 4 | `h-tests` | analysis | done |
| 5 | `describe` | analysis | done |
| 6 | `sens-ncal` | analysis | done; base models asserted identical to main's |
| 7 | `sens-elec-time` | analysis | done |

## Results (seed-paired t(9) 95% intervals; verdicts scoped to these samples)

| | adult | bank-marketing | electricity | phoneme | overall |
|---|---|---|---|---|---|
| **H1** ECE RF − LR (pred. > 0, margin 0.005) | +0.0033 [−0.0001, +0.0068] inconclusive | −0.0147 [−0.0161, −0.0134] **contradicted** | +0.0270 [+0.0232, +0.0308] holds | −0.0263 [−0.0339, −0.0187] **contradicted** | **contradicted** |
| **H2a** Brier RF iso − none (pred. < 0, margin 0.001) | +0.0003 [−0.0001, +0.0007] no difference | −0.0000 [−0.0003, +0.0002] no difference | −0.0028 [−0.0030, −0.0025] holds | −0.0007 [−0.0018, +0.0005] inconclusive | **inconclusive** |
| **H2b** Brier HGB iso − none (pred. < 0, margin 0.001) | +0.0002 [+0.0001, +0.0004] no difference | −0.0005 [−0.0008, −0.0002] no difference | −0.0004 [−0.0007, −0.0002] no difference | +0.0006 [−0.0001, +0.0014] inconclusive | **no difference** |
| H1 on ece_db (sens. a, descriptive) | holds | contradicted | holds | contradicted | contradicted |
| H2a, n_cal = 1,351 (sens. b) | contradicted [+0.0005, +0.0012] | contradicted [+0.0006, +0.0011] | holds | (main) inconclusive | (unplanned aggregation: contradicted) |
| H2b, n_cal = 1,351 (sens. b) | contradicted | no difference | no difference | (main) inconclusive | (unplanned aggregation: inconclusive) |
| Electricity chronological (sens. c) | H1 inconclusive [−0.0100, +0.0116]; H2a contradicted [+0.0209, +0.0322]; H2b holds [−0.1013, −0.0551] | | | | not counted |

How to read the rows above (results-r1):
- **Sensitivity (b) overall.** The plan asks only for per-dataset categories. The overall entries
  are an unplanned aggregation and are labelled that way in their claims. Adult's and
  bank-marketing's H2a 'contradicted' rest on mean rises of about 0.0009 Brier, whose intervals
  cross the 0.001 margin only at their upper ends.
- **Sensitivity (c), electricity chronological.** Under the chronological split, all three
  uncalibrated models are badly miscalibrated on the test quarter. ECE is 0.168 for LR, 0.169 for
  RF and 0.334 for HGB, against 0.022, 0.049 and 0.028 under random splits. Recalibration fitted on
  the calibration quarter can make the test quarter worse: LR's Brier is 0.202 with no
  recalibration, 0.251 with Platt and 0.253 with isotonic. The run therefore measures drift from the
  calibration quarter to the test quarter, mixed with the Victoria fill regime (every fill row is in
  train) and with test-quarter normalised dates lying beyond most of the training range. It does not show whether
  random-split leakage drives main's electricity results. **That question remains open.**
- **What depends on electricity.** H1's 'contradicted' does not: it is contradicted whatever
  electricity's category, because bank-marketing and phoneme are contradicted. H2a is not supported
  without electricity, because electricity is its only 'holds'. H2b's 'no difference' does depend on
  electricity, which is one of the three 'no difference' datasets that verdict needs.
- **H1 'contradicted'.** It reflects default LR's own miscalibration on bank-marketing (ECE 0.031)
  and phoneme (ECE 0.063, not reduced by Platt; AUC 0.81 against RF's 0.95). It does not show that
  RF is well calibrated. Uncalibrated RF also scores ECE on fewer non-empty bins: 13 on adult and
  phoneme and 11.1 on bank-marketing, against LR's 15.
- **H2b 'no difference'.** It means each interval lies inside ±0.001 Brier, not that isotonic had
  no effect. Adult's interval lies wholly above 0, and bank-marketing's and electricity's wholly
  below 0.

Claims now also cover the seed SD of every reported mean, the ece_bins of each uncalibrated model,
and the chronological per-model levels (mean and SD of ECE, Brier and AUC for none, Platt and
isotonic). That makes 576 result claims.

Every number above is a claim in `claims.jsonl` with a macro in `paper/numbers.tex`. There are
354 result claims: every per-dataset mean, lo, hi and category, the overall codes, both
sensitivities, seed means of ece, ece_db and Brier for every cell, log-loss and AUC for none and
isotonic, the RF − LR and Platt − none descriptive intervals, the isotonic AUC control, clip counts
and the procedure checks. Values are copied from the run metrics by a generator script, not typed.
Overall verdicts and categories are numeric codes (validation requires numbers), and each claim's
text gives the word.

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

### 1. unit-tests (data-prep; done, rerun with `--replace` after code-r1 F1)

```bash
TMPDIR=<any scratch dir> python3 crew/scripts/crew.py run gallery/cs-calibration --id unit-tests --role experimenter --kind data-prep --replace \
  --code code/test_metrics.py --code code/experiment.py --code code/analyze.py --code code/describe.py \
  --code code/sens_ncal.py --code code/sens_elec_time.py \
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
   *Status:* code-r1 F2 and F3 agreed. The designer narrowed the plan wording before `main`.
   H1 is no longer called a replication, and ece_db is descriptive.
3. **code-r1 F1 (fixed before `main`):** the one-hot width is not constant across seeds. The
   encoder is fitted on each seed's training split, and a rare adult level is sometimes absent from
   it. `main` had asserted a constant width. It now records the min and max (`summarize_main`), and
   `describe` does the same. On the study data, adult's width was 106-107, so the old assertion
   would have failed `main`. A unit test with a single-row level covers this.
4. **Results that weaken the hypotheses, as pre-registered.** H1 is contradicted overall: on
   bank-marketing and phoneme the uncalibrated RF has *lower* plug-in ECE than LR. ece_db agrees in
   sign on all four datasets, and on adult it moves from inconclusive to holds. Per code-r1 F2,
   that agreement is not evidence against a floor artefact. On adult and bank-marketing, H2a ends
   in the margin, not in a gain. For H2b, the adult interval lies wholly above 0 and the
   bank-marketing and electricity intervals lie wholly below 0. All three lie inside ±0.001, so
   the pre-registered precedence rule makes them 'no difference'.
   With isotonic fitted on 1,351 calibration rows (sens. b), isotonic *raises* RF Brier on adult and
   bank-marketing ('contradicted') and HGB Brier on adult. On the chronological electricity split
   (sens. c), isotonic raises RF Brier by about 0.027 but lowers HGB Brier by about 0.078. In that
   split, the calibration and test quarters contain no Victoria fill-value rows (min = max = 0), and
   the train half contains 7,642-7,753 of them. So drift and the fill regime are confounded, as
   threats[4] says. None of this changes a verdict.
5. The first synthetic smoke run of `experiment.py` failed in loky (the `__main__` worker could not
   be unpickled because of an `lru_cache`). Fixed by dispatching `experiment.main_cell` by module
   reference. No result was involved.

## Synthetic smoke test (not a ledger run)

Before recording `unit-tests`, all five analysis scripts ran end to end on a fully synthetic
workspace in the session scratch directory. It used make_classification data with the four study
shapes and column names, plus a synthetic manifest; no study file was read. The scripts wrote
360 / 90 / 90 cell rows, 40 + 30 + 10 `.npz` files and every metrics file. A rerun of `main` and
`sens-ncal` reproduced the CSVs byte for byte. Synthetic `main` took 1.19 CPU-minutes (11 s wall
on 8 workers). That run was for debugging only and is not evidence.
