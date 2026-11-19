# Run notes (Econometrician)

What was run, in order, and what surprised me. The design gate was approved by Bryce Wang on
2026-11-18 at 14:38 UTC. Everything up to the section "Main analysis runs: commands" was written
before that gate. In that part no eligibility coefficient and no relationship between `e401` and
`net_tfa` had been computed; every number there comes from synthetic outcomes and treatments built
on the nine real covariates. The analysis runs and their results are in the sections after it.

## 2026-11-18: e-code (code written, not run on the study data)

| File | Purpose | Run(s) |
|---|---|---|
| `code/dml_plr.py` | DML2 PLR with the partialling-out score, HC0 SE, eq. 3.14 aggregation, partitions from `SeedSequence([1211, K, s])`, fit seeds from `SeedSequence([1211, K, s, fold, learner, nuisance])`, the five learner ports as importable functions, joblib `n_jobs=-1` (loky) with one BLAS thread per fit. The design constants (tolerance table, `se_pub`, S) are checked against `plan.json` design at start-up | main-lasso, main-tree, main-nnet, main-forest, main-boosting, sens-lasso-c11 |
| `code/check_noctrl.py` | No-controls OLS (intercept, HC0 and classical SEs) on all 9,915 rows. The 9,275-row Abadie band is computed as a descriptive diagnostic only | check-noctrl |
| `code/verdict.py` | H1, H2 (one-sided not-testable rule), H3 (main runs; sens-lasso-c11 descriptive), `tol_obs` with the fixed wording, side-by-side table, baseline (ineligible mean, eligible mean, SD of net_tfa), diagnostics | verdict |
| `code/check_learner_ports.py`, `code/check_learner_ports.R` | Pre-gate port check (analysis plan 0) | check-learner-ports |
| `code/authors/ML_Functions.R`, `code/authors/LICENSE.Rmd` | Verbatim copies from github.com/VC2015/DMLonGitHub at commit `ff35d21e19eedf78197243064e39616ef12705a0` (2018-01-22), fetched from raw.githubusercontent.com. ML_Functions.R git blob `4e90ed647607c8a9e05fff64af3b212e1f90eaed`, which equals the design value and the GitHub contents API. The driver re-checks the blob on every run. Never edited | check-learner-ports |

Choices the design left open (implementation details, not tuning):

- The partition is `numpy.array_split` of the permutation. At K = 2 the folds have 4,958 and
  4,957 rows.
- The integer seed of each estimator is `SeedSequence(entropy).generate_state(1)[0]`. The
  liblinear logistic lasso is also given this seed.
- The lasso port does not use `warm_start`, because the design's `Lasso(...)` call lists none.
  The timing prototype used it.
- `plan.json` is read only to assert the constants. It is not declared as an `--input`,
  because every gate decision rewrites it and would invalidate the run hash.
- Main-run wall time goes to `runs/<id>/timing.json` (an `--output`, never a metric).
- The R package versions are recorded as comments in `code/requirements.txt`.

Smoke test (**unlogged**, scratchpad only, not a run): every learner of `dml_plr.run`, `check_noctrl.py`
and `verdict.py` ran end to end with S = 1-2 on a synthetic outcome and treatment saved under
the names net_tfa/e401. Those numbers are meaningless and are not reported.

## 2026-11-18, first run: check-learner-ports (data-prep, synthetic only)

Superseded for the lasso by the re-run below, after the lasso port gained hdm's zero
threshold (code-r1 F1). The first run's record is in git at commit b57c415
(`runs/check-learner-ports/run.json`, `metrics.json`, `units.csv`). The forest, tree,
boosting and nnet code did not change.

Command, exactly as in `design.check_learner_ports.command`. Exit 0, 13:13:16-13:29:47 UTC,
**990 s wall** (R phase 725 s for 20 calls, 4,877 s summed; Python phase 254 s for 200 fits).
The design estimated 10-12 minutes; the run took 16.5. Ten synthetic units, a 2-fold
partition and true theta = 9000.

Authors' call path in the installed R (R 4.5.2, **hdm 0.3.2**, rpart 4.1.24, randomForest
4.7.1.2, gbm 2.3.1, nnet 7.3.20, glmnet 4.1.10; scikit-learn 1.9.1):

- `lasso_c_eff_y = 0.5`. `rlassoF -> rlasso.formula -> rlasso.default` resets the authors'
  c = 1.1 to 0.5, because the penalty list with gamma added equals hdm's default. This matches
  the primary Y-lasso choice (c = 0.5), so there is nothing to escalate.
- `lasso_c_eff_d = 1.1`. The rlassologit c is honoured.
- p = 275 in R as well.

Theta differences are measured against R seed A. The yardstick is R seed B minus R seed A.

| Learner | theta py / R-A (mean) | shift (se) | rms port | rms seed | max abs | cor l / m min (py vs R) | cor l / m min (R-B vs R-A) | Result |
|---|---|---|---|---|---|---|---|---|
| lasso | 9,113 / 9,200 | **-87** (16) | 99 | 0 | **151** | **0.9942** / 1.0000 | 1 / 1 | **FAIL** (rule: max <= $25 and both cor >= 0.999) |
| tree | 9,246 / 9,270 | -25 (26) | 81 | 84 | 255 | 0.9951 / 0.9654 | 1.0000 / 0.9654 | pass |
| forest | 8,881 / 9,097 | **-216** (9) | **218** | 16 | 258 | 0.9993 / **0.9732** | 0.9995 / 0.9951 | **FAIL** (location and spread) |
| boosting | 9,116 / 9,120 | -5 (3) | 9 | 9 | 18 | 0.9996 / 0.9983 | 0.9997 / 0.9975 | pass |
| nnet | 8,932 / 8,935 | -3 (16) | 48 | 34 | 79 | 0.9983 / 0.9206 | 0.9998 / 0.9191 | pass |

Pass rules, fixed in the design:

- **Tree, forest, boosting, nnet.** `|shift| <= max(2.262 x shift_se, $25)` and
  `rms_port <= max(1.75 x rms_seed, $25)`.
- **Lasso.** `location_ok` is the max-abs rule and `spread_ok` is the correlation rule. The
  design names only the combined pass rule, so this split of the metric names is mine.

Per-unit values are in `runs/check-learner-ports/units.csv`.

### Measured deviations in the first run (recorded, not re-tuned)

1. **Lasso.** The Python port's theta is **$87 lower** on average than the authors' rlasso
   path (unit range -$3 to -$151; 10 of 10 units negative). The deviation sits in the
   **Y lasso** (out-of-fold prediction correlation 0.994-0.998). The D logistic lasso agrees
   (0.99999). It is about 11% of the K = 2 lasso tolerance ($825) and 14% of the K = 5
   tolerance ($636).
   - **Corrected explanation (code-r1 F1/F2).** The shift comes from hdm's zero threshold.
     LassoShooting.fit ends every solve with `w[abs(w) < control$zeroThreshold] <- 0`
     (zeroThreshold = 1e-6). It applies this to coefficients on the centered, unscaled
     dictionary columns, and rlasso uses the thresholded coefficients for the residuals and
     loadings of every iteration. The first port had no threshold.
   - Evidence: the Reviewer's diagnostic (reviews/code-r1, notes item 2; unlogged,
     scratchpad, synthetic units 1 and 8). With the threshold switched off in hdm, R and
     Python predictions agreed to $0.09-0.19 RMS. Tightening hdm's optTol and maxIter changed
     nothing.
   - **Retracted:** my first note blamed LassoShooting stopping early (maxIter, optTol). That
     was an unlogged conjecture, with no script, run or output in the workspace. Its only
     support was an **unlogged** scratchpad KKT check on one 400-row synthetic fold, which I
     misread: the "violations" I saw are what thresholding raw-scale coefficients on columns
     like inc^8 produces, not a sign that the solver had not converged.
   - The design was amended (design.learners.lasso.Y_learner, PI ruling on code-r1 F1,
     remedy (a)), the threshold was ported, and the check was re-run (below).
2. **Forest.** The Python port's theta is **$216 lower** (unit range -$165 to -$258; 10 of 10
   negative). The port rms ($218) is 13x the R seed-to-seed rms ($16). The shift is about 49% of the K = 2 forest
   tolerance ($438) and 75% of the K = 5 tolerance ($287).
   - The deviation sits in the **D forest** (nodesize 1): the m-hat correlation with R is
     0.973, against 0.995 between two R seeds. The out-of-fold RMSE of m-hat is 0.4798 in
     Python and 0.4715 in R. The Y forest agrees as closely as two R seeds do.
   - Candidate explanations (conjectures, design.candidate_deviations.forest; not tested by
     any run):
     - sklearn keeps searching beyond max_features until it finds a valid split, while
       randomForest makes the node terminal;
     - the nodesize mapping;
     - other split-search details.
   - The code matches design.learners.forest exactly, so nothing was changed.
3. Passes, with notes:
   - **Tree.** 9 units within $5. Unit 9 is -$255, which is no bigger than the R seed spread
     there.
   - **Boosting.** Shift -$5.
   - **nnet.** Shift -$3. The Python D fits hit `max_iter` = 1000 (median iterations: 1000
     for D, 80.5 for Y). The D-nnet m-hat correlates with R at only 0.92, but two R seeds
     also correlate at only 0.92.

Under design.check_learner_ports.on_failure, the two failures are measured deviations. The
paper reports them next to the lasso and forest cells, and they are the first candidate
explanation if those cells fail H2. The check was done at K = 2 only, at 4,957-4,958 training
rows. That the deviations carry over to K = 5 is an assumption.

## 2026-11-18, re-run: check-learner-ports after the lasso zero-threshold fix (code-r1 F1)

Code change, the only one, made under on_failure's bug clause after the PI's ruling (remedy (a)):
`rlasso_fit_predict` in `code/dml_plr.py` now applies hdm's `zeroThreshold = 1e-6` after every
solve, as design.learners.lasso.Y_learner was amended to say. Each coefficient is expressed on
the centered, unscaled dictionary column (`coef / sd`), every coefficient with |b_j| < 1e-6 is
set to 0, with no re-optimization, and the residuals, loadings and the final prediction use the
thresholded coefficients. No other learner changed.

Before the re-run I checked the change on one 800-row synthetic unit (**unlogged**, scratchpad
only). The Y-lasso prediction correlation with hdm rose from 0.9987 to 0.99999.

Command: design.check_learner_ports.command_rerun (the stored command plus `--replace`). Exit
0, 13:49:54-14:02:00 UTC, **725 s wall** (R phase 610 s, Python phase 110 s).

| Learner | shift (se) | rms port | rms seed | max abs | cor l / m min | Result |
|---|---|---|---|---|---|---|
| lasso | **+0.04** (0.06) | 0.19 | 0 | **0.36** | **0.99999997** / 0.99999 | **pass** (was FAIL: -87, max 151, cor_l 0.994) |
| tree | -24.7 (25.7) | 80.8 | 83.9 | 255 | 0.9951 / 0.9654 | pass (identical to the first run) |
| forest | **-216.0** (9.4) | **217.9** | 16.4 | 258 | 0.9993 / **0.9732** | **FAIL** (identical to the first run) |
| boosting | -4.7 (2.6) | 9.1 | 8.7 | 18 | 0.9996 / 0.9983 | pass (identical) |
| nnet | -3.0 (16.1) | 48.2 | 33.6 | 79 | 0.9983 / 0.9206 | pass (identical) |

- The tree, forest, boosting and nnet metrics equal the first run's to the last digit. Their
  code did not change and the run is deterministic, so this also shows the check reproduces.
- `lasso_c_eff_y = 0.5` and `lasso_c_eff_d = 1.1` are unchanged.
- The remaining measured deviation is the forest's -$216, in the D forest. It is disclosed and
  priced into H2, and the port is kept as specified (PI ruling on design-r2 (a)).
- In plan.json I updated, from this run, with the design's fixed formula
  p = P(|N(shift, tol/2.81)| > tol):
  - design.tolerance_table lasso rows: port_shift_measured 0.0, se 0.1, p_outside 0.005,
    2-SE range [0.005, 0.005], x4.5 0.005;
  - decision_rules.H2_size_under_measured_ports, hypotheses[1] and threats[12]: H2's
    false-failure rate stays about 33% (33.1%). The lasso-rescaled variant falls from about
    46% to about 33%.

### Post-run code change (does not affect any run)

`code/verdict.py` (code-r1 F3) now:

- declares `runs/check-learner-ports/metrics.json` as an `--input`;
- copies `port_shift_<L>`, `port_shift_se_<L>`, `port_rms_<L>`, `port_rms_seed_<L>`,
  `port_pass_<L>`, `lasso_c_eff_y` and `lasso_c_eff_d` into its metrics;
- writes the amended reading of failed cells
  (decision_rules.H2_reading_of_failures: 'consistent with the measured port deviation' /
  'not explained by the measured deviation', plus the descriptive tol_obs note).

I smoke-tested it on the synthetic metrics (**unlogged**, scratchpad).

Note: the lasso's measured shift is +$0.04. A failed lasso cell will therefore in practice
always read 'not explained by the measured deviation'.

## Main analysis runs: commands (written before the design gate; executed after it, see below)

All are run from the repository with `WS=/Users/brycewang/Auto-Research-Skills/gallery/ss-dml-401k`
and `CREW=/Users/brycewang/Auto-Research-Skills/crew/scripts/crew.py`, in this order:

```bash
python3 $CREW run $WS --id check-noctrl --role econometrician --kind analysis --code code/check_noctrl.py --input data/derived/sipp1991.csv --metrics runs/check-noctrl/metrics.json -- .venv/bin/python code/check_noctrl.py
python3 $CREW run $WS --id main-lasso --role econometrician --kind analysis --code code/dml_plr.py --input data/derived/sipp1991.csv --output runs/main-lasso/splits.csv --output runs/main-lasso/timing.json --metrics runs/main-lasso/metrics.json -- .venv/bin/python code/dml_plr.py --learner lasso --splits 100
python3 $CREW run $WS --id main-tree --role econometrician --kind analysis --code code/dml_plr.py --input data/derived/sipp1991.csv --output runs/main-tree/splits.csv --output runs/main-tree/timing.json --metrics runs/main-tree/metrics.json -- .venv/bin/python code/dml_plr.py --learner tree --splits 100
python3 $CREW run $WS --id main-nnet --role econometrician --kind analysis --code code/dml_plr.py --input data/derived/sipp1991.csv --output runs/main-nnet/splits.csv --output runs/main-nnet/timing.json --metrics runs/main-nnet/metrics.json -- .venv/bin/python code/dml_plr.py --learner nnet --splits 100
python3 $CREW run $WS --id main-forest --role econometrician --kind analysis --code code/dml_plr.py --input data/derived/sipp1991.csv --output runs/main-forest/splits.csv --output runs/main-forest/timing.json --metrics runs/main-forest/metrics.json -- .venv/bin/python code/dml_plr.py --learner forest --splits 40
python3 $CREW run $WS --id main-boosting --role econometrician --kind analysis --code code/dml_plr.py --input data/derived/sipp1991.csv --output runs/main-boosting/splits.csv --output runs/main-boosting/timing.json --metrics runs/main-boosting/metrics.json -- .venv/bin/python code/dml_plr.py --learner boosting --splits 30
python3 $CREW run $WS --id sens-lasso-c11 --role econometrician --kind analysis --code code/dml_plr.py --input data/derived/sipp1991.csv --output runs/sens-lasso-c11/splits.csv --output runs/sens-lasso-c11/timing.json --metrics runs/sens-lasso-c11/metrics.json -- .venv/bin/python code/dml_plr.py --learner lasso --splits 100 --lasso-c-y 1.1 --run-id sens-lasso-c11
python3 $CREW run $WS --id verdict --role econometrician --kind analysis --code code/verdict.py --code code/dml_plr.py --input runs/check-noctrl/metrics.json --input runs/main-lasso/metrics.json --input runs/main-tree/metrics.json --input runs/main-nnet/metrics.json --input runs/main-forest/metrics.json --input runs/main-boosting/metrics.json --input runs/sens-lasso-c11/metrics.json --input runs/check-learner-ports/metrics.json --input data/derived/sipp1991.csv --metrics runs/verdict/metrics.json -- .venv/bin/python code/verdict.py
```

`dml_plr.py` refuses a `main-*` run whose S differs from design.splits.

## 2026-11-18, after the design gate: analysis runs

All analysis runs used the commands above verbatim, in the planned order. No script, learner,
tuning value, S or tolerance was changed after the gate. Every run exited 0.

### check-noctrl (14:38 UTC, previous Econometrician session)

No-controls OLS on all 9,915 rows: **$19,559.34** (HC0 SE 1,412.8; classical 1,305.7) against
the published $19,559 (SE 1,413). The difference is $0.34, inside the $1 rounding rule, and
N = 9,915, so there is no data discrepancy. The HC0 SE matches the published 1,413. Descriptive
only (design.sample_rule): on the 9,275-row Abadie band the coefficient is $18,858.

### Session restart (no effect on any recorded run)

The first attempt at main-lasso was interrupted by a session restart. It had written an
incomplete `runs/main-lasso/` record, which was removed before this session was launched. Nothing
from it was read, kept or reported. main-lasso was then run from scratch with the same command
and the same seeds, so the restart changes no number. The PI archived the relaunch brief in
`briefs/`.

### Main runs, sens-lasso-c11 and verdict (16:10-17:42 UTC)

I ran the seven commands back to back from a scratchpad shell script that stopped at the first
non-zero exit; none occurred. Wall time comes from the run records and timing.json, which are
`--output` files, never metrics:

| Run | S | Started (UTC) | Wall (s) | Nuisance fits | Timing-model estimate |
|---|---|---|---|---|---|
| main-lasso | 100 | 16:10:03 | 3,101 | 1,400 | 743 s serial |
| main-tree | 100 | 17:01:47 | 293 | 1,400 | 793 s serial |
| main-nnet | 100 | 17:06:42 | 214 | 1,400 | 395 s serial |
| main-forest | 40 | 17:10:18 | 421 | 560 | 1,899 s serial |
| main-boosting | 30 | 17:17:21 | 802 | 420 | 3,831 s serial |
| sens-lasso-c11 | 100 | 17:30:45 | 669 | 1,400 | 743 s serial |
| verdict | - | 17:41:55 | 1 | - | 5 s |

Total wall time was **92 minutes** (16:10:03-17:41:56). That is above the 60-minute budget. Under
design.splits.rule the overrun is disclosed and was not traded for power. The machine was shared
with other heavy jobs: the load average was 46-90 on 8 cores during main-lasso, and each loky
worker got about a third of a core. That is why main-lasso took 52 minutes but sens-lasso-c11,
with the same code under lighter load, took 11. This affects time only. Every fit is seeded, so
the numbers do not depend on the load.

**The ten cells** (1991 US dollars; tolerance and testability from design.tolerance_table):

| Cell | Replicated | Published | Diff | Tolerance | Diff / pub. bracketed SE | Bracketed SE rep (pub) | Adjusted SE rep (pub) | H2 |
|---|---|---|---|---|---|---|---|---|
| lasso 2-fold | 7,701 | 7,717 | -16 | 825 | -0.01 | 1,345 (1,346) | 1,377 (1,749) | inside, not testable |
| lasso 5-fold | 8,173 | 8,187 | -14 | 636 | -0.01 | 1,300 (1,298) | 1,309 (1,558) | inside, not testable |
| tree 2-fold | 8,767 | 8,709 | +58 | 312 | +0.04 | 1,355 (1,363) | 1,413 (1,427) | pass |
| tree 5-fold | 8,934 | 8,871 | +63 | 301 | +0.05 | 1,353 (1,358) | 1,375 (1,418) | pass |
| forest 2-fold | 9,064 | 9,116 | -52 | 438 | -0.04 | 1,255 (1,302) | 1,319 (1,377) | pass |
| forest 5-fold | 9,041 | 9,247 | -206 | 287 | -0.16 | 1,230 (1,295) | 1,259 (1,328) | pass |
| boosting 2-fold | 8,830 | 8,759 | +71 | 372 | +0.05 | 1,336 (1,339) | 1,363 (1,382) | pass |
| boosting 5-fold | 9,020 | 9,110 | -90 | 209 | -0.07 | 1,315 (1,314) | 1,325 (1,328) | pass |
| nnet 2-fold | 9,107 | 8,950 | +157 | 330 | +0.12 | 1,387 (1,335) | 1,428 (1,408) | pass |
| nnet 5-fold | 9,126 | 9,038 | +88 | 219 | +0.07 | 1,383 (1,322) | 1,408 (1,355) | pass |

No cell is outside its tolerance, so no H2 failure reading applies (the `h2_reading_*` metrics are
empty).

- **H1 holds.** All ten estimates are positive. The lowest 95% lower bound, theta - 1.96 x
  adjusted SE, is $5,002 (lasso, 2-fold).
- **H2 holds.** 0 of 10 cells are outside their tolerance and 8 of 8 testable cells are inside.
  The two lasso cells are inside but not testable at this resolution, so they are not counted as
  passes. Under the design, "holds" means no shift larger than a cell's 80%-power detectable
  shift was detected. It does not mean the estimates are identical.
- **H3 holds.** The lasso is below every flexible learner at both fold counts. The smallest
  margin is $1,066 at K = 2 (lasso vs tree) and $761 at K = 5 (lasso vs tree).
- **Baseline.** Mean net_tfa is $10,788 for ineligible households and $30,347 for eligible
  households. The SD of net_tfa is $63,523. The replicated cells are 71-85% of the ineligible
  mean, or 0.12-0.14 SD.
- **sens-lasso-c11 (descriptive only, decision_rules.sens_lasso_c11).** With c = 1.1 for the
  Y lasso the estimates are $7,479 at 2-fold and $7,878 at 5-fold. That is $223 and $295 below
  the primary c = 0.5 lasso, and $238 and $309 below the published cells. Both are still inside
  the lasso tolerances, and the H3 ordering also holds with them (margins $1,289 and $1,056).
  Under the primary specification no lasso cell fails, so no c = 1.1 attribution is needed.

### What surprised me (diagnostics; none changes a tolerance, S, claim or verdict)

1. **The lasso split spread is much smaller than the published one.** Our 1.4826 x MAD of the
   per-split estimates is $354 at 2-fold and $190 at 5-fold. The published SEs imply $1,656 and
   $1,278. So the replicated adjusted SEs (1,377; 1,309) are well below the published ones
   (1,749; 1,558), while the bracketed SEs match to within $2. The other learners' spreads are
   also smaller than the published ones, but only by a factor of 1.2-1.7 rather than 4.7-6.7.
   This is consistent with the published lasso path being noisier across splits. That is a
   conjecture; no run tests it. The tolerances use the published spread as fixed. The descriptive
   tol_obs values are smaller than the tolerances for every cell (lasso 596 / 455), and every
   cell is inside tol_obs too.
2. **The 5-fold forest difference (-$206) is close to the forest port shift measured before the
   gate** (-$216, synthetic data, 2-fold size). The cell is inside its $287 tolerance, so this is
   only an observation. The 2-fold forest cell is -$52.
3. **The D neural network still hits max_iter.** The median L-BFGS iterations are 1,000 for D and
   62 for Y, as in the port check. The share of m_hat outside [0.01, 0.99] is 2.3% (2-fold) and
   2.0% (5-fold) for nnet, 1.5-1.6% for forest, and 0 for lasso, tree and boosting.

### Claims and macros

`claims.jsonl` now has 312 result claims alongside the 18 citation claims. Values are copied from
the run records by a scratchpad script, and `crew.py validate` checks each against its metric.
They cover:

- the ten `plr-<learner>-<k>fold` claims (value `theta_k<k>` of `main-<learner>`);
- per cell: the bracketed and adjusted SEs, the 95% lower bound, the difference in dollars and
  in published-SE units, the tolerance, the 80%-power detectable shift, the H2 verdict (text,
  backed by the `h2_status`/`h2_inside` metrics), tol_obs, the baseline scalings and the
  diagnostics;
- the H1, H2 and H3 decisions, with the counts and margins;
- the baseline;
- check-noctrl;
- the port deviations (copied from verdict);
- the descriptive c = 1.1 sensitivity;
- the nnet iteration counts.

Pass/fail claims carry no `value`, because the tool accepts only numeric values; their text
states the outcome. `paper/numbers.tex` was regenerated with 291 macros. The macro names are
`<Quantity><Learner><Two|Five>`, for example `\ThetaForestFive`, `\TolNnetTwo` and
`\SeAdjLassoFive`. Wall times are in this file only, never in a metric or a macro.

### Deviations

There are none in the analysis runs: every run used the planned command, S and specification.
Disclosures:

- total wall time was 92 minutes against the 60-minute budget (shared machine), disclosed under
  design.splits.rule;
- the session restart and the removed, incomplete main-lasso record (above);
- the pre-gate measured port deviation of the forest (-$216, port check FAIL), which is
  unchanged and already priced into H2.

## 2026-11-18: response to results-r1 (no new estimation run; verdict not re-run)

Claims-only changes, with the responses written in reviews/results-r1 F1-F4. claims.jsonl now
has 343 result claims; numbers.tex has 321 macros.

- **F1.** Every H2 cell claim and h2-decision now uses the decision rule's meaning of a pass:
  'no shift larger than the cell's 80%-power detectable shift was detected', never 'identical'.
  The decision rule (design.decision_rules.H2) governs the verdict. hypotheses[1] instead says
  'no shift larger than the stated per-cell tolerance'. Both apply the same test,
  |diff| <= tolerance; they differ only in which shift they name (the tolerance is detected
  about half the time, the MDS80 80% of the time). The forest 5-fold claim now carries the -$206
  vs -$216 port-shift observation and the $373 detectable shift.
- **F2.**
  - The 30 published numbers are now claims and macros (`\PubTheta*`, `\PubSeMed*`,
    `\PubSeAdj*`), backed by the verdict metrics.
  - The ~33% H2 false-failure rate and the per-cell p_outside are not in any run metric; they
    exist only in plan.json, so they have no claim, pending the PI's decision.
  - Wall time (92 min against the 60-min budget) is in no metric by design and stays in this
    file.
- **F3.** New claim lasso-spread-discrepancy (adjusted-SE ratios 0.79/0.84; split spread 4.7x and
  6.7x narrower than published; cause untested; the lasso match is weak evidence and is read
  only as not testable).
- **F4.** The port-shift claims are labelled synthetic-outcome dollars.
- **F5** went to the Scout.

## 2026-11-18: response to results-r2 F6 (claim text only)

plr-forest-2fold-h2 now names the failed pre-gate forest port check (-$216, synthetic-outcome
dollars, measured at the 2-fold training size). plr-forest-5fold-h2 adds that the shift was
measured at the 2-fold training size only and that the 2-fold cell (-$52) does not show it.
Neither forest cell can tell a zero shift from a -$216 shift.
