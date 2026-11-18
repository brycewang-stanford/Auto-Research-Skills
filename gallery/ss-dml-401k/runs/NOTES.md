# Run notes (Econometrician)

What was run, in order, and what surprised me. The design gate is **not** approved. No analysis
run has been executed. No eligibility coefficient and no relationship between `e401` and
`net_tfa` has been computed. Every number below comes from synthetic outcomes and treatments
built on the nine real covariates.

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

Smoke test, unlogged and in the scratchpad: every learner of `dml_plr.run`, `check_noctrl.py`
and `verdict.py` ran end to end with S = 1-2 on a synthetic outcome and treatment saved under
the names net_tfa/e401. Those numbers are meaningless and are not reported.

## 2026-11-18: check-learner-ports (data-prep, synthetic only)

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

### Measured deviations (recorded, not re-tuned)

1. **Lasso.** The Python port's theta is **$87 lower** on average than the authors' rlasso
   path (unit range -$3 to -$151; 10 of 10 units negative). The deviation sits in the
   **Y lasso** (out-of-fold prediction correlation 0.994-0.998). The D logistic lasso agrees
   (0.99999). It is about 11% of the K = 2 lasso tolerance ($825) and 14% of the K = 5
   tolerance ($636).
   - Candidate explanation (conjecture, from design.candidate_deviations.lasso): the
     optimizer. hdm's LassoShooting.fit stops at maxIter 1000 or a 1e-5 absolute change on
     raw-scale columns up to inc^8. The Python port solves the same penalized problem to
     tol 1e-6 on standardized columns.
   - Evidence for that explanation: an unlogged scratchpad diagnostic on one 400-row
     synthetic training fold. There, hdm's final coefficients violate the lasso optimality
     (KKT) conditions by many orders of magnitude on the zero coefficients, while both
     implementations select 10 columns. This is consistent with an unconverged R solution,
     not with a different penalty.
   - I found no place where `rlasso_fit_predict` departs from design.learners.lasso, so no
     code was changed.
2. **Forest.** The Python port's theta is **$216 lower** (unit range -$165 to -$258; 10 of 10
   negative). That is 21x the R seed-to-seed rms ($16), about 49% of the K = 2 forest
   tolerance ($438) and 75% of the K = 5 tolerance ($287).
   - The deviation sits in the **D forest** (nodesize 1): the m-hat correlation with R is
     0.973, against 0.995 between two R seeds. The out-of-fold RMSE of m-hat is 0.4798 in
     Python and 0.4715 in R. The Y forest agrees as closely as two R seeds do.
   - Candidate explanation (conjecture, from design.candidate_deviations.forest): the
     mapping of randomForest's nodesize to `min_samples_split = nodesize + 1`, or
     split-search differences, at nodesize = 1. Not tested.
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

## Main analysis runs: commands (NOT executed; they run only after the design gate)

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
python3 $CREW run $WS --id verdict --role econometrician --kind analysis --code code/verdict.py --code code/dml_plr.py --input runs/check-noctrl/metrics.json --input runs/main-lasso/metrics.json --input runs/main-tree/metrics.json --input runs/main-nnet/metrics.json --input runs/main-forest/metrics.json --input runs/main-boosting/metrics.json --input runs/sens-lasso-c11/metrics.json --input data/derived/sipp1991.csv --metrics runs/verdict/metrics.json -- .venv/bin/python code/verdict.py
```

`dml_plr.py` refuses a `main-*` run whose S differs from design.splits.
