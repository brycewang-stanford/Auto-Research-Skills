# Run notes (econometrician)

## diag-overlap (data-prep, before the design gate), 2026-11-19

- Script: `code/diag_overlap.py`, adopted from `gallery/ss-null-effect/code/diag_overlap.py`
  (sha256 235d2ecb...acf5) with only DEV-1, DEV-2, DEV-4, DEV-5, DEV-6 applied (ten covariates,
  14-term B(X), 56-term B+(X), upper clip 0.99 only, control-only trimming count).
- Input: `data/derived/analysis_noRE78.csv` only (no re78 column; refuses to run if one exists).
  Nothing was built or fitted on X- (covariates without re75/u75).
- Seeds: 20261118 + s, s = 0..4 (outer 5-fold StratifiedKFold and inner CV). 37 treated per test fold.
- Only addition to the learner code: FutureWarnings from scikit-learn 1.9.1 are silenced with a
  warnings filter (no learner argument changed); ConvergenceWarnings are counted (0).
- Outcome: B1 pass (max weighted |SMD| 0.059, age^2), O1 pass (0 of 185 treated with m_bar > 0.9),
  O2 pass (0 clipped units). Final basis B(X); diag-overlap-ext not run. Kish ESS of weighted
  controls 126.4; largest control weight 6.41. rob-trim would drop 8,125 CPS men (all below the
  treated minimum m_bar 1.03e-4), keeping 7,867.
- Worth noting: the trimmed set is large (about half the CPS men) because the lowest treated
  m_bar (1.03e-4) sits just above the CPS median m_bar (9.5e-5).

## Analysis code (written after the design gate, 2026-11-19; NOT yet run on the study data)

Status: the design gate was approved 2026-11-19T07:34:42Z. The analysis scripts are written and
tested on synthetic data only (run `unit-tests`, data-prep). **No analysis run has been made and
re78 has not been read.** design.analysis_plan requires a Reviewer code review (target `code`)
with no open critical or major finding before any analysis run. If the review changes any file
under `code/`, rerun `unit-tests` with `--replace` first, then have the changed file re-reviewed.

| File | Run | Design source |
|---|---|---|
| `aipw_lib.py` | shared by every analysis run | method.primary_estimator, cross_fitting, propensity_clipping, join_rule, outcome_validity, relative_effect |
| `main_aipw.py` | `main-aipw` | H1; the only script that reads `data/raw` (join_rule) |
| `placebo_re75.py` | `placebo-re75` | method.h3_placebo (H3) |
| `rob_trim.py` | `rob-trim` | method.control_only_trimming (DEV-6) |
| `rob_learners.py` | `rob-learners` | analysis_plan rob-learners |
| `rob_covsets.py` | `rob-covsets` | DEV-13 |
| `rob_estimators.py` | `rob-estimators` | DEV-14 |
| `rob_diff74.py` | `rob-diff74` | DEV-15 |
| `rob_ipow.py` | `rob-ipow` (only if main-aipw's `ipow_trigger` is true) | method.missing_outcomes, DEV-17 |
| `sens_imbens.py` | `sens-imbens` | method.sensitivity, DEV-16 |
| `h2_benchmark.py` | `h2-benchmark` (only after the results gate) | method.h2_descriptive |
| `test_analysis.py` | `unit-tests` (data-prep, synthetic only) | analysis_plan code-review prerequisites |

### How the code follows the adopted code

Each script is the ss-null-effect script at commit 716b6c3 with the plan's deviations only
(DEV-1 to DEV-17), as stated in its docstring. Shared choices:

- **Reuse of the pre-gate code.** `aipw_lib.py` imports `code/diag_overlap.py` (unchanged since
  run diag-overlap) for the covariate loader (`load`, refuses a file with an re78 column), the
  propensity learner, the outer folds and the primary propensity cross-fit (`crossfit`), so the
  primary fits are the code that ran before the gate; `basis()` is checked against
  `diag_overlap.basis_B`. On synthetic data main-aipw's m_bar equals diag-overlap's exactly.
- **Clip.** Upper 0.99 only (DEV-5) everywhere, including Hajek IPW and the random forests.
- **H1 decision.** `h1_holds = ci_low > 0`. The disagreement rule compares this flag with
  main-aipw's (rob-trim, rob-covsets (a), rob-learners (a) and (b)); rob-estimators (b) triggers
  only if its point estimate lies outside main-aipw's 95% CI. The metric
  `*_triggers_abstract_statement` records each case; rob-covsets (b), rob-diff74,
  rob-estimators (a) and rob-ipow never trigger.
- **re78.** Only `main_aipw.py` reads `data/raw`. It applies method.join_rule (fields 1-9 of each
  raw line must equal the working-file row exactly, u74/u75 rebuilt and compared, every key
  matched both ways; a non-numeric field 10 becomes missing) and writes
  `data/derived/re78_by_key.csv` (src, row, re78; registered with `--output`). Every later run
  that needs re78 reads that file and checks that its keys are the working file's keys in the
  same order. `data/derived` is git-ignored, so the joined outcome is never committed.
- **Placebo.** `placebo_re75.py` reads only `data/derived/analysis_noRE78.csv` (and
  diag-overlap's metrics for the basis check); it never opens `data/raw` or the joined file
  (the unit test runs it with both removed). B(X-) has 11 terms, T(X-) 8 columns.
- **Benchmark.** Only `h2_benchmark.py` contains the experimental benchmark (unit test
  `test_benchmark_only_in_h2` scans every other script).
- **Warnings.** scikit-learn 1.9.1 FutureWarnings are silenced inside each fit (no argument
  changed); ConvergenceWarnings are counted and reported (`n_convergence_warnings`).

Implementation choices the plan left open (fixed now, before any outcome is read):

1. Missing outcomes. A field-10 token that is not a number is "missing"; a present value that
   fails the outcome-validity rule is "inadmissible". Both are excluded (complete cases) and
   counted by arm (`missing_re78_*`, `inadmissible_re78_*`, `unobserved_re78_*`). The rob-ipow
   trigger uses the unobserved shares: `ipow_trigger = |share_treated - share_control| > 0.02`.
   Claims `primary-re78-invalid-treated/-control` use `unobserved_re78_treated/_control`.
2. rob-trim's m_bar is re-fitted with the primary code on main-aipw's analysis sample (as the
   adopted script did); with no missing re78 this is the full sample and the script reports
   `max_abs_diff_mbar_vs_diag_overlap` and whether its dropped count equals diag-overlap's 8,125.
3. rob-learners predicts the forests single-threaded (fit unchanged, n_jobs = -1), the
   determinism fix ss-null-effect made after 716b6c3 (commit 9f3133a), so reruns are bit-stable.
4. rob-ipow had no adopted script (its trigger never fired in ss-null-effect); it is written
   from the adopted text in method.missing_outcomes: r(X, D) by LogisticRegressionCV (primary
   settings) on (treat, B(X)), cross-fitted on folds stratified on treat over all 16,177 units,
   floored at 0.05; m from the primary full-sample fits; g0 on observed CPS men; SE from the
   influence function with r treated as known. It refuses to run unless `ipow_trigger` is true.
5. sens-imbens reports t_0 = min(|ci_low|, |ci_high|) of main-aipw exactly as specified, also
   if the 95% CI includes zero. `r2star_zero` is 0.30 with `r2star_zero_out_of_grid` true when
   no diagonal point reaches t_0 (claim text '> 0.30').
6. h2-benchmark does not read plan.json to check the results gate (listing plan.json as an
   input would invalidate the run whenever the task board changes); the gate is enforced by
   running it only after approval, as below.

## unit-tests (data-prep, synthetic data only)

`code/test_analysis.py`, run `unit-tests` (2026-11-19T08:11:54Z to 08:17:29Z): **19/19 tests passed,
exit 0, no study file read** (`--input` empty; synthetic workspaces in a temporary directory).
Its metrics equal, to the last bit, those of an identical dry run in the scratch directory, so
the code is deterministic on fixed inputs.

What is tested: design constants (seeds 20261118 + s, K = S = 5, clip 0.99, placebo bound 900,
IPW bootstrap 999 / seed 20261120, EM settings, 128 + 22 + 16 sensitivity points, learner
hyperparameters); B(X), B(X-) (11 terms, no re75/u75), covset and time-invariant bases and
T(X) widths; the outcome-validity and sentinel rule and the counts by arm; the AIPW score, the
upper-only clip and the aggregation/variance rule on hand cases; the estimator with oracle
nuisances on 200,000 synthetic units; the H1, H3 and disagreement rules; control-only
trimming; the relative-effect delta method against finite differences; the IPOW score (equals
AIPW when R = r = 1; oracle MAR check); Hajek IPW and HC2 against hand computations; the
Imbens model (R2 maps, tau(0,0) = OLS, bias signs, R2* interpolation and '> 0.30'); H2's
formula; that pandas' default CSV parser round-trips floats exactly (the join compares
exactly); the join rule (exact match, a covariate changed in its last digit, a missing raw
line, an extra field, a non-numeric re78); that only `h2_benchmark.py` contains the benchmark;
that only `main_aipw.py` refers to `data/raw`; and two end-to-end runs of the real
`prepare_data.py`, `diag_overlap.py` and every analysis script on synthetic workspaces in the
raw-file format: (A) 2,500 units, 131 treated, true ATT 1,500, no missing re78: main-aipw
1,647.7 (SE 243.5); its m_bar equals diag-overlap's; rob-trim's dropped count equals
diag-overlap's; the placebo runs with `data/raw` and the joined outcome removed; rob-ipow
refuses (trigger off); every metric named in design.claim_ids exists; a second main-aipw
run gives identical metrics. (B) the same data with 10% of treated re78 set to the sentinel
9999999, one CPS value non-numeric and one negative: the counts are exact, main-aipw uses the
complete cases, the trigger fires, rob-ipow runs (1,523.8, SE 254.1) on all 2,500 units.

Test-only setting: the tests run with one OpenMP thread (threadpoolctl). On this machine, with
other sessions' runs in progress (load average above 40), HistGradientBoosting spin-waited in
libomp and a first attempt had not finished main-aipw on 2,500 synthetic units after ten
minutes. The analysis runs do not limit threads; if they stall the same way, the fix is to
set `OMP_NUM_THREADS` for the run, which I would raise with the PI first.

## Exact commands

Run from the repository root (`/Users/brycewang/Auto-Research-Skills`). `crew.py run` executes the
command with the workspace as working directory. Python: the workspace `.venv`
(`code/requirements.txt`). `WS=gallery/ss-lalonde-observational`, `CREW=crew/scripts/crew.py`.
`L` below abbreviates `--code code/aipw_lib.py --code code/diag_overlap.py`, and `D` abbreviates
`--input data/derived/analysis_noRE78.csv --input data/derived/re78_by_key.csv
--input runs/diag-overlap/metrics.json --input runs/main-aipw/metrics.json`; write them out in full.

```bash
WS=gallery/ss-lalonde-observational; CREW=crew/scripts/crew.py

# 0. unit tests (data-prep; done, see above; rerun with --replace after any code change)
python3 $CREW run $WS --id unit-tests --role econometrician --kind data-prep \
  --code code/test_analysis.py --code code/aipw_lib.py --code code/diag_overlap.py \
  --code code/prepare_data.py --code code/main_aipw.py --code code/placebo_re75.py \
  --code code/rob_trim.py --code code/rob_learners.py --code code/rob_covsets.py \
  --code code/rob_estimators.py --code code/rob_diff74.py --code code/rob_ipow.py \
  --code code/sens_imbens.py --code code/h2_benchmark.py \
  --metrics runs/unit-tests/metrics.json -- .venv/bin/python -I code/test_analysis.py

# --- STOP: Reviewer code review (target 'code'); no open critical or major finding ---

# 1. main-aipw (the only run that reads data/raw; writes data/derived/re78_by_key.csv)
python3 $CREW run $WS --id main-aipw --role econometrician --kind analysis \
  --code code/main_aipw.py --code code/aipw_lib.py --code code/diag_overlap.py \
  --input data/derived/analysis_noRE78.csv --input data/raw/nswre74_treated.txt \
  --input data/raw/cps_controls.txt --input runs/diag-overlap/metrics.json \
  --input runs/diag-overlap/propensity.csv \
  --output data/derived/re78_by_key.csv \
  --metrics runs/main-aipw/metrics.json -- .venv/bin/python -I code/main_aipw.py

# 2. placebo-re75 (never reads re78)
python3 $CREW run $WS --id placebo-re75 --role econometrician --kind analysis \
  --code code/placebo_re75.py --code code/aipw_lib.py --code code/diag_overlap.py \
  --input data/derived/analysis_noRE78.csv --input runs/diag-overlap/metrics.json \
  --metrics runs/placebo-re75/metrics.json -- .venv/bin/python -I code/placebo_re75.py

# 3. rob-trim
python3 $CREW run $WS --id rob-trim --role econometrician --kind analysis \
  --code code/rob_trim.py --code code/aipw_lib.py --code code/diag_overlap.py \
  --input data/derived/analysis_noRE78.csv --input data/derived/re78_by_key.csv \
  --input runs/diag-overlap/metrics.json --input runs/diag-overlap/propensity.csv \
  --input runs/main-aipw/metrics.json \
  --metrics runs/rob-trim/metrics.json -- .venv/bin/python -I code/rob_trim.py

# 4. rob-learners
python3 $CREW run $WS --id rob-learners --role econometrician --kind analysis \
  --code code/rob_learners.py --code code/aipw_lib.py --code code/diag_overlap.py \
  --input data/derived/analysis_noRE78.csv --input data/derived/re78_by_key.csv \
  --input runs/diag-overlap/metrics.json --input runs/main-aipw/metrics.json \
  --metrics runs/rob-learners/metrics.json -- .venv/bin/python -I code/rob_learners.py

# 5. rob-covsets
python3 $CREW run $WS --id rob-covsets --role econometrician --kind analysis \
  --code code/rob_covsets.py --code code/aipw_lib.py --code code/diag_overlap.py \
  --input data/derived/analysis_noRE78.csv --input data/derived/re78_by_key.csv \
  --input runs/diag-overlap/metrics.json --input runs/main-aipw/metrics.json \
  --metrics runs/rob-covsets/metrics.json -- .venv/bin/python -I code/rob_covsets.py

# 6. rob-estimators
python3 $CREW run $WS --id rob-estimators --role econometrician --kind analysis \
  --code code/rob_estimators.py --code code/aipw_lib.py --code code/diag_overlap.py \
  --input data/derived/analysis_noRE78.csv --input data/derived/re78_by_key.csv \
  --input runs/diag-overlap/metrics.json --input runs/main-aipw/metrics.json \
  --metrics runs/rob-estimators/metrics.json -- .venv/bin/python -I code/rob_estimators.py

# 7. rob-diff74
python3 $CREW run $WS --id rob-diff74 --role econometrician --kind analysis \
  --code code/rob_diff74.py --code code/aipw_lib.py --code code/diag_overlap.py \
  --input data/derived/analysis_noRE78.csv --input data/derived/re78_by_key.csv \
  --input runs/diag-overlap/metrics.json --input runs/main-aipw/metrics.json \
  --metrics runs/rob-diff74/metrics.json -- .venv/bin/python -I code/rob_diff74.py

# 8. rob-ipow: ONLY if runs/main-aipw/metrics.json has "ipow_trigger": true (else not run, and say so)
python3 $CREW run $WS --id rob-ipow --role econometrician --kind analysis \
  --code code/rob_ipow.py --code code/aipw_lib.py --code code/diag_overlap.py \
  --input data/derived/analysis_noRE78.csv --input data/derived/re78_by_key.csv \
  --input runs/diag-overlap/metrics.json --input runs/main-aipw/metrics.json \
  --metrics runs/rob-ipow/metrics.json -- .venv/bin/python -I code/rob_ipow.py

# 9. sens-imbens
python3 $CREW run $WS --id sens-imbens --role econometrician --kind analysis \
  --code code/sens_imbens.py --code code/aipw_lib.py --code code/diag_overlap.py \
  --input data/derived/analysis_noRE78.csv --input data/derived/re78_by_key.csv \
  --input runs/diag-overlap/metrics.json --input runs/main-aipw/metrics.json \
  --metrics runs/sens-imbens/metrics.json -- .venv/bin/python -I code/sens_imbens.py

# --- claims (design.claim_ids, table below); results gate (human) ---

# 10. h2-benchmark: ONLY after the results gate is approved
python3 $CREW run $WS --id h2-benchmark --role econometrician --kind analysis \
  --code code/h2_benchmark.py --input runs/main-aipw/metrics.json \
  --metrics runs/h2-benchmark/metrics.json -- .venv/bin/python -I code/h2_benchmark.py

python3 $CREW validate $WS
```

After main-aipw, add `data/derived/re78_by_key.csv` to `data/manifest.json` (derived from the
two raw files by run main-aipw; same terms) with its sha256 from `runs/main-aipw/run.json`.

## Claim ids and the metrics they copy

Every metric below is checked to exist by `test_end_to_end_synthetic` (rob-ipow's in
`test_end_to_end_missing_outcomes`).

| claim ids (design.claim_ids) | run | metric |
|---|---|---|
| primary-effect, -ci-low, -ci-high, -se, -p | main-aipw | effect, ci_low, ci_high, se, p |
| primary-n, -n-treated, -n-control, -n-clipped | main-aipw | n, n_treated, n_control, n_clipped_units |
| primary-treated-mean, -cf-mean | main-aipw | treated_mean, cf_mean |
| primary-rel-effect, -rel-ci-low, -rel-ci-high | main-aipw | rel_effect, rel_ci_low, rel_ci_high (fractions; `*_pct` also reported) |
| primary-re78-invalid-treated, -control | main-aipw | unobserved_re78_treated, unobserved_re78_control |
| overlap-treated-above-09, overlap-kish-ess, overlap-max-control-weight | main-aipw | share_treated_above_09, kish_ess_controls, max_control_weight |
| placebo-effect, -se, -ci-low, -ci-high | placebo-re75 | effect, se, ci_low, ci_high |
| placebo-verdict (1 pass, 0 inconclusive, -1 fail), placebo-n-clipped | placebo-re75 | verdict_code, n_clipped_units |
| trim-effect, -ci-low, -ci-high, -n-control-kept, -n-control-dropped | rob-trim | effect, ci_low, ci_high, n_control_kept, n_control_dropped |
| covset-a-/covset-b- effect, ci-low, ci-high | rob-covsets | covset_a_/covset_b_ effect, ci_low, ci_high |
| learner-linear-/learner-rf- effect, ci-low, ci-high | rob-learners | linear_/rf_ effect, ci_low, ci_high |
| ols-coef, ols-ci-low, ols-ci-high | rob-estimators | ols_effect, ols_ci_low, ols_ci_high |
| ipw-effect, ipw-ci-low, ipw-ci-high | rob-estimators | ipw_effect, ipw_ci_low, ipw_ci_high |
| diff74-effect, -ci-low, -ci-high | rob-diff74 | effect, ci_low, ci_high |
| ipow-re78-effect, -ci-low, -ci-high (only if run) | rob-ipow | effect, ci_low, ci_high |
| sens-r2-zero, sens-tau00 | sens-imbens | r2star_zero (text from r2star_zero_text), tau00 |
| sens-bench-g-r2d, -r2y, -bias, g in age, educ, black, hisp, married, nodegree, earn74, earn75 | sens-imbens | bench_g_r2d, bench_g_r2y, bench_g_abs_bias |
| h2-diff, h2-se-combined, h2-ci-low, h2-ci-high (after the results gate) | h2-benchmark | h2_diff, h2_se_combined, h2_ci_low, h2_ci_high |

Decision flags for the paper's wording (not claims): main-aipw `h1_holds`; placebo-re75
`verdict`; `*_triggers_abstract_statement` in rob-trim, rob-covsets (covset_a), rob-learners
(linear, rf) and rob-estimators (ipw); sens-imbens `robust_zero_<g>`, `strongest_robust_zero`,
`weakest_nonrobust_zero`, `robust_zero_earn75`.
