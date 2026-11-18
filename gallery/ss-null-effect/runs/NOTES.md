# Run notes (Econometrician)

## Before the design gate

1. **diag-overlap** (data-prep; `code/diag_overlap.py`; input `data/derived/covariates.csv` only,
   no outcome read). Cross-fitted propensity exactly as the primary estimator (B(X), 17 terms,
   LogisticRegressionCV L2, 5 folds x 5 repetitions, seeds 20261118 + s). Results:
   - B1 pass: max ATT-weighted |SMD| over the B(X) terms = 0.037 (married); 0 terms >= 0.10.
     The B+ escalation rule did not fire, so diag-overlap-ext is not run. Final basis: B(X).
   - O1 pass: 0 of 1,621 treated have m_bar > 0.9 (max treated m_bar 0.881).
   - O2 pass: 0 units clipped at [0.01, 0.99] in any repetition.
   - Raw Imbens-Wooldridge normalized differences above 0.25 (flagged regression-sensitive,
     no action, per plan): re75 -0.630, unemp75 0.500, re74 -0.270.
   - 3.3% of all units (133; 122 of them controls below 0.1) have m_bar outside [0.1, 0.9];
     Kish ESS of the weighted controls 1,062 of 2,379; largest control weight 10.8.

   Implementation choices the plan left open (recorded here, fixed before any outcome):
   control weights for (b) are w = m/(1 - m) with each repetition's clipped m, averaged over
   the five repetitions; SMD denominators use unweighted group SDs; a unit counts as clipped
   if any of its five out-of-fold propensities falls outside [0.01, 0.99]. The selected
   penalty is strong (C median and max 0.046, min 0.006 over the 25 fits); balance is still within B1.
   Note: the codebook's standardized differences use sqrt((s1^2 + s0^2) / 2); the raw nd here
   uses sqrt(s1^2 + s0^2) per the plan, so they differ by a factor of sqrt(2).

## Data-prep reruns before the design gate (recorded by the Designer, design-r1 F6)

`prepare-covariates` and `margin` each ran twice (log.jsonl 12:27:54 and 12:28:10-11 UTC).
Per the Data RA's report, after the first pass it added a check to
`code/prepare_covariates.py` that counts rows where `unemp74`/`unemp75` differ from
1{`re74`/`re75` = 0} (metrics `unemp74_ne_re74_zero_rows`, `unemp75_ne_re75_zero_rows`;
both 0, so the indicators are exactly zero-earnings flags), and reran `prepare-covariates`
with `--replace`. `margin` reads `data/derived/covariates.csv`, whose hash the rerun
refreshed, so it was rerun with `--replace` as well, so that its recorded input hash
matched. The ledger keeps only the second run of each. Neither script reads an outcome
(`usecols` and run inputs checked by the Reviewer in design-r1). The M recorded in the
ledger (483.47) is the second run's; the first run's metrics were overwritten.

## After the design gate (analysis runs, 2026-11-18, design gate approved 13:00:13Z)

All runs below are `--kind analysis`, executed through `crew.py run` in the order of
`design.analysis_plan`. Each script fixes its seeds (20261118 + s for folds, inner CV and
learners; 20261119 for the multiplier bootstrap; 20261120 for the IPW bootstrap) and writes
flat metrics only; no timing is in any metrics file. Shared code: `code/aipw_lib.py`
(imports `propensity_learner` and `basis_B` from `code/diag_overlap.py`, so the propensity
fits are the pre-gate code; every run records both files under `--code`). Outcomes are
read from `data/raw/null_extract.csv` with `usecols` limited to `id` and the run's own
outcomes; the survey items are never read. All scripts were smoke-tested beforehand in a
scratch copy on synthetic noise outcomes (no real outcome read); no analysis run was
repeated or replaced.

| Order | Run | Script | Result (nominal dollars unless stated) |
|---|---|---|---|
| 1 | main-aipw | main_aipw.py | ATT -9.8 (SE 177.6); 95% CI [-358.0, 338.4], p = 0.956; 90% CI [-302.0, 282.4] inside (-483.47, 483.47), p_TOST = 0.0038; smallest satisfied margin 302.0; relative effect -0.12% [-4.3%, 4.1%] of the counterfactual mean 7,939.7 |
| 2 | secondary-family | secondary_family.py | 0 of 5 outcomes detected (Romano-Wolf p: re79 0.744, employed78 0.744, hours78 0.204, benefits78 0.166, wellbeing78 0.744); max-t c = 2.477 |
| 3 | select-re75 | select_re75.py | -3,541 [-3,878, -3,204] (7.3 x M); descriptive only |
| 4 | rob-trim | rob_trim.py | 35.7 [-299.6, 371.0], n = 3,867 (133 dropped: 10 treated, 123 controls) |
| 5 | rob-covsets | rob_covsets.py | (a) -31.5 [-370.5, 307.5]; (b) -139.3 [-493.7, 215.1] |
| 6 | rob-learners | rob_learners.py | (a) linear -115.7 [-449.6, 218.2]; (b) random forest -10.0 [-358.1, 338.1] |
| 7 | rob-diff74 | rob_diff74.py | -1,086.5 [-1,495.5, -677.5] (different estimand and assumption) |
| 8 | rob-estimators | rob_estimators.py | (a) OLS coefficient -126.5 [-434.0, 181.0] (HC2); (b) Hajek IPW -191.1 [-521.3, 139.1] (bootstrap SE 168.5) |
| - | rob-ipow | not run | trigger did not fire (0 missing, 0 inadmissible values in every outcome and arm; missing-counts, range-counts), as fixed before the gate |
| 9 | sens-imbens | sens_imbens.py | R2* = 0.060 (target M), 0.042 (zero-crossing, t_0 = 338.4), 0.023 (equivalence-ending, t_E = 181.5); earnings75 benchmark (R2_D 0.189, R2_Y 0.237) gives |bias| 1,716 |

### Decisions under the fixed rules

- **H1** (zero ATT on re78): not rejected; the 95% CI includes 0. Per the plan this is not
  reported as "no effect".
- **H1b** (|ATT| < M = 483.47): supported, p_TOST = 0.0038; the 90% CI lies inside (-M, M).
  O1 and O2 passed (0 treated above 0.9; 0 clipped units, recomputed in main-aipw), so the
  trimmed interval is not needed for the H1b rule; it is also inside (-M, M).
- **H2**: no secondary outcome is detected. benefits78 has an unadjusted p of 0.044 (ATT 86.9,
  max-t interval [-19.8, 193.5]) but Romano-Wolf p = 0.166, so by the plan it is not
  detected and must not be described as an effect. hours78: unadjusted p 0.067, RW 0.204.
- **Disagreement rule**: no check triggers it. rob-trim, rob-covsets (a), rob-learners (a)
  and (b) reach the same H1 and H1b decisions as main-aipw; the Hajek IPW point estimate
  (-191.1) is inside main-aipw's 95% CI. rob-covsets (b), rob-diff74, rob-estimators (a) and
  select-re75 are reported but never trigger (rob-diff74 rejects zero and fails H1b; it is an
  estimate under conditional parallel trends 1974-78, not a defence or refutation of the primary).
- **Sensitivity reading rule** (sens-imbens): for every target the conclusion is **not robust**
  to an unobserved confounder as strong as earnings75 (|bias| 1,716 > M, > t_0, > t_E), so the
  paper must say the result could be produced by unobserved selection of that strength.
  Targets M and zero: robust to 8 of 9 groups; strongest group robust to: earnings74 (|bias| 204);
  weakest not robust to: earnings75. Equivalence target (t_E = 181.5): robust to 7 of 9; strongest
  robust: age (|bias| 128); weakest not robust: earnings74 (|bias| 204), then earnings75.
  tau(0, 0) = -126.5 equals the rob-estimators (a) OLS coefficient (difference 1.3e-6).
  All 169 EM fits converged (at most 9 iterations).

### Implementation choices the plan left open (fixed in code before any analysis run)

1. Relative-effect delta method uses psi_bar (mean over repetitions) for psi_theta, so its SE
   has no between-split variance term (the ATT SE does).
2. Multiplier bootstrap: xi drawn as a 10,000 x 4,000 standard-normal matrix in row blocks of
   1,000 from default_rng(20261119); max-t c is the numpy (linear) 95% quantile; Romano-Wolf
   p made monotone by a running maximum. The bootstrap t* SDs fall short of 1 by up to 4.2%
   because SE_k (mean aggregation) exceeds the SD of psi_bar_k; the plan anticipated this
   (threats: "the max-t intervals use the aggregated SE").
3. rob-trim recomputes the primary propensity fits; m_bar matches runs/diag-overlap/propensity.csv
   to 5e-11. Units with m_bar exactly 0.1 or 0.9 would be kept (none sit on a bound).
4. rob-learners: OLS outcome model standardized within fold (no effect on predictions); random
   forests use n_jobs = -1 (deterministic given random_state); RF propensity clipped to
   [0.01, 0.99] like the primary (0 clipped).
5. rob-estimators (b): propensity fitted in-sample on all units with B(X) standardized, C =
   0.0464 picked by LogisticRegressionCV (inner-CV seed 20261118); m clipped to [0.01, 0.99]
   as in the primary (0 clipped); 95% CI = estimate +/- 1.96 bootstrap SE; the percentile
   interval [-536.1, 118.9] is recorded for information.
6. sens-imbens: Z = [1, B(X) standardized]; EM starts from the U-free fits with intercepts
   shifted by -alpha/2 and -delta/2; convergence on the full observed-data log-likelihood;
   sigma0^2 = RSS/n; V uses ddof = 1; the diagonal for R2* interpolation starts at (0, 0);
   benchmark groups are ranked by the larger |bias| of the two signs for the "strongest robust"
   and "weakest non-robust" names.
7. Echoed counts: main-aipw and secondary-family copy missing and inadmissible counts from
   data/derived/missing_counts.json and range_counts.json and also recompute the validity rule
   on the data (0 rows dropped in every outcome).

### Surprises and notes

- The two parametric checks (linear AIPW -115.7, OLS -126.5) and Hajek IPW (-191.1) sit below
  the flexible AIPW (-9.8 and RF -10.0); all are inside the primary 95% CI and none changes a
  decision.
- rob-diff74 is strongly negative: enrolees' 1974-78 earnings growth is about 1,087 below that
  of comparable non-enrolees. Under the plan this is a different assumption and does not
  trigger anything; it is consistent with enrolees being on a lower growth path, which would
  bias the DiD downward (plan.json analysis_plan, rob-diff74).
- Wall time: the machine was shared with another session's 8-process job, so
  secondary-family took about 30 minutes instead of about 2. No metric depends on timing.

### Deviations from the approved design

None. rob-ipow was not run because its pre-gate trigger did not fire, as the plan specifies.
Only `tasks[].status` in plan.json was changed (a-main ... a-claims set to done); the hash of
plan.json without `tasks` and `gates` is unchanged
(146cb81e36128153f6ac1f88e081c6c430010282d2c202d99caa75fccee0b38e before and after).
