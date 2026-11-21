# Run notes (Econometrician)

## Order of runs

1. `check-methods` (data-prep, 2026-11-21; code/test_sclib.py with sclib.py, select.py,
   level_mde.py; inputs: the Prop 99 file, state_panel_pre.csv (the pop column for the Monte
   Carlo; all rows for the seasonal-factor check), state_panel.csv (seasonal-factor check only:
   2014Q1-2019Q4 rows, no later statistic)). Results: see "check-methods results" below.

2. `check-methods` again with `--replace` (task e-check-r2, after design.method C1-C5; the first
   record is under runs/.superseded/). Code: test_sclib.py, sclib.py, select_rule.py (renamed from
   select.py, C4), level_mde.py; same inputs. Results: "check-methods rerun (e-check-r2)" below.

3. `select` (analysis, after the design gate and code-r1 pass; code select_rule.py, sclib.py,
   test_sclib.py; input state_panel_pre.csv only). Run once. Selected DDT-POPW-E-R50 (RMSE 0.0112,
   max |tau| 0.0154; no tie). Runner-up DDT-AGG-E-R50 (0.0125). Best of the other families:
   SC-E-D20 0.0191, SDID-E-D20 0.0200, DD-POPW-E-R50 0.0240. SC solver gaps <= 6.6e-7.
   As T17 anticipates, an R50 and DDT winner may reflect California's shared 2014-2022 general
   minimum-wage ramp.
4. `level-mde` (analysis; code level_mde.py, sclib.py; inputs state_panel_pre.csv,
   runs/select/metrics.json, runs/check-methods/metrics.json and mc_rates.csv). nu_h2 14.06,
   MDE_h2 0.092, h90_h2 0.054 (above b = 0.02, so 'no effect as large as 2%' is unreachable at
   the pre-period SE), MDE_h3 0.065 > 0.04, so h3_informative = 0 and H3 will be reported as
   uninformative whatever its estimate. Surprises: the H1 (wage) L quantiles are large
   (c_hi(0.95) 3.45, c_hi(0.975) 4.32, both from L), which makes MDE_h1 0.148; the S2 run had
   29 of 5,052 weight solves with a KKT residual above 1e-6 (max 3.0e-6; report-only).

5. Post-period runs, each once, in analysis_plan order, code as code-r1 stamped it: h1-wage,
   h2-emp, h3-years, anticip, sec-cemn, sec-dube, rob-base-2023q4, rob-pre-ab257, rob-pool,
   rob-7225, rob-final-quarters, plc-nonff, plc-722511, event-path, verdict. All exit 0.
   Main results (selected DDT-POPW-E-R50):
   - H1: pooled wage ATT +0.092 log points (+9.7%, about $50 a week at the 2023Q3 $521), SE
     0.035, t = 2.66, below the pre-specified one-sided critical value 3.45, which the decision
     set L's 0.95 quantile set (t at nu would be 1.76); so H1 is "not supported" and H2 is
     reported as uninformative about the wage floor. Years: +0.084 (t 2.04) and +0.101 (t 2.99),
     neither above 3.45.
   - H2: -0.0295 log points (-2.9%, about -16,700 jobs), 95% CI [-0.106, 0.047], 90% CI
     [-0.092, 0.033]: "inconclusive". plc-nonff fails (+0.0245, 95% CI [0.003, 0.046]), so the
     verdict appends "not separable from a California-wide shock".
   - H3: year 2 minus year 1 -0.008 [-0.050, 0.034]; the rule gives "no detectable change" but
     the MDE gate (0.065 > 0.04) makes it "uninformative". Elasticities not computed (H1 does not
     reject).
   - S1 -0.036 [-0.112, 0.040] and S2 -0.010 [-0.047, 0.028]: both "inconclusive"; no check
     changes the sign category, so no "not robust to" qualifier.
   - Cross-checks: our CEMN fixed horizon -2.97 / -3.95 vs print -2.74 / -3.72 (both -0.23);
     our Dube-timing SDID -0.46 (SE_s 0.47) vs print -0.26 [0.54]; wage +8.31 vs +6.99.
   Surprises: (1) H1 turns on the L quantile of the wage statistic (3.45), far above t at nu;
   the wage effect is large and its t-statistic would pass at t_nu or t_J. (2) The non-722513
   placebo fails with a positive sign: California's rest-of-economy employment ran above the
   R50 trend-adjusted counterfactual. (3) S2's reused-weights wage effect, +0.075 [0.035, 0.116],
   excludes 0 under S2's own critical values, while H1's does not under H1's.
6. e-claims: 960 result claims in claims.jsonl (938 macros), every number of design.claims_plan,
   including the results that contradict the hypotheses (H1 not supported, the plc-nonff failure)
   and the check-methods values echoed by level-mde; `crew.py numbers` run. The Prop 99 DID and
   SDID values are only in check-methods (a data-prep run), so no result claim can cite them;
   level-mde echoes only the SC values (as C3 lists).

## check-methods rerun (e-check-r2)

Exit 0, 1218 metrics. Every first-run (iv) number reproduced exactly: all 21 rate and bound
columns of mc_rates.csv in all 80 cells, and all 884 per-cell mc_ metrics, are identical (compared
against a copy of the first run's files), as are the MC KKT maximum (4.3e-6) and the
non-convergence count (0).

- (i) DID -27.349 and SDID -15.604 pass as before. i-SC-1: sclib SC -19.5138 (KKT 1.6e-8) vs the
  independent active-set solve -19.5136 (its KKT 2.6e-15), difference 1.2e-4 <= 1e-3: pass.
  i-SC-2: Frank-Wolfe port with sparsification, fed sclib.sdid_unit_problem and sclib.sigma_hat,
  -19.620 in [-19.65, -19.55): pass (unsparsified -19.587).
- (ii), (iii), (v) pass as before (part (v) now imports select_rule and level_mde by name).
- SDID floor q_cal (C1; default_rng(20261122); pure A; D20 4,000 and R50 1,000 per rho):
  D20 hi95 1.8541, hi975 2.2768, lo05 -1.7990, lo025 -2.1690 (all from rho = 0);
  R50 hi95 1.8081, hi975 2.2687 (rho = 0), lo05 -1.6692, lo025 -2.1419 (rho = 0.5). The R50
  lo05 is inside -t_50,0.95 = -1.676, so there the t_J value binds.
- (a) on the DD, DDT and SC cells: pass. (a-SDID) with the floor: pass in all 12 cells; D20 pure
  A rho 0: upper 0.0565, lower 0.0465, two-sided 0.0575 (uncorrected t_J: 0.0670, 0.0510,
  0.0705); D20 pure A rho 0.5: 0.0460 / 0.0465 / 0.0500; R50 pure A: two-sided 0.032 and 0.042.
- (b) fails again in SDID-E, D20, hetero-A, rho 0 (two-sided 0.0765 at t_J, 0.0700 at t_nu_MC),
  the C2 recorded result; every other hetero-A cell passes. With the floor (report-only), this
  cell's rates are 0.0470 / 0.0575 / 0.0635 two-sided.
- (c) hetero-A-CA2 unchanged; SDID with the floor (report-only), two-sided: D20 0.158 (rho 0) and
  0.137 (rho 0.5); R50 0.114 and 0.166.

## check-methods results (first run, superseded)

Run `check-methods` (exit 0; metrics in runs/check-methods/metrics.json, Monte Carlo table in
runs/check-methods/mc_rates.csv). Run once, as instructed.

- (i) Prop 99: DID -27.349 in [-27.35, -27.25): pass. SDID -15.604 in [-15.65, -15.55): pass.
  **SC -19.514, outside [-19.65, -19.55): FAIL.** KKT max 3.9e-7. No bug found: the exact
  minimiser of the stated SC objective (no intercept, zeta = 1e-6 sigma_hat) is -19.514 with
  SLSQP (KKT 1.6e-8) and with an independent NNLS solve; the printed -19.6 is what synthdid's
  Frank-Wolfe solver returns (diagnostic port in test_sclib.py: -19.587 without its default
  sparsification, -19.620 with it), i.e. it reflects that solver's stopping rule and
  sparsification, not the minimiser. Returned to the PI and Designer; the algorithm is not changed.
- (ii) Synthetic identities: pass. DD/DDT closed forms equal WLS TWFE to at most 1.4e-13 (all
  AGG/POPW x E/P x D20/R50 x flat/trend panels); known effects recovered to 1e-14; SC and SDID
  (zeta = 0) weights recovered to 3.9e-7, SDID time weights to 3.2e-7; demeaned SC = SDID
  routine with zeta = 0 and uniform lambda to 1.3e-15; KKT max 7.0e-7.
- (iii) Seasonal factors from state_panel_pre.csv and state_panel.csv: identical (max |diff| 0)
  over 23 series.
- (v) select.py and level_mde.py raise on a 2020Q1 row and accept the pre-2020 rows: pass.
- (iv) Monte Carlo (80 estimator x pool x design x rho cells):
  - **(a) FAIL in one cell: SDID-E, D20, pure A, rho = 0** (R = 2000, bound 0.0646): upper
    0.0670, lower 0.0510, two-sided 0.0705. Every other (a) cell passes (pure A rates
    0.044-0.068 within their bounds; pure B and mixed 0.000-0.018). Per analysis_plan 0f a
    failure of (a) goes to the Designer before the design gate.
  - **(b) FAIL in one cell: SDID-E, D20, hetero-A, rho = 0** (nu_MC 13.19; r2 = 0.0570, bound
    0.0725): two-sided at t_J 0.0765 > 0.0725 and two-sided at t_nu_MC 0.0700 > 0.0646
    (one-sided: t_J 0.0565 / 0.0650 within 0.0691; t_nu 0.0540 / 0.0595 within 0.0646). Every
    other hetero-A cell passes. Per the design a failure of (b) is a bug to look for.
  - (c) hetero-A-CA2 (report-only), two-sided at t_J / t_nu_MC: D20 0.145-0.183 / 0.134-0.170,
    R50 0.141-0.186 / 0.137-0.186; nu_MC 13.3-14.5 (D20), 34.1-37.2 (R50).
  - Scaled-only (SE_s) two-sided rates at t_J: pure A 0.43-0.46, mixed 0.33-0.41, pure B
    0.06-0.13 (SC 0.12-0.13).
  - Solver: MC KKT max 4.3e-6 (above 1e-6 in at least one of about 2 million solves; not a
    pass condition of (iv)); no SLSQP non-convergence.
  - Search for a bug in the SDID cells (development check on synthetic data, not a run, no
    claim): with equal populations and two other seeds (R = 4000 each), SDID-E D20 pure A
    two-sided rates at t_20 were 0.0575 and 0.0655 (SC 0.051, 0.055), and the SE is right on
    average (sd of California's estimate 0.0055 vs RMS SE 0.0056). The SDID excess persists
    across seeds, so it is not this seed alone; it is in the tails (t_J too thin for SDID's
    placebo SE), not in the SE's scale. I found no bug: SDID passes Prop 99 and every synthetic
    identity, and the same inference code gives level-correct rates for DD, DDT and SC.

## Implementation choices the design does not fix (for the code review)

1. **Renamed (design.method C4):** code/select.py, which shadowed the standard-library module
   `select`, is now code/select_rule.py; the import prologue is dropped from every script I
   wrote (the figures RA's fig_*.py and figlib.py still carry it; harmless). The run id stays
   `select`. select_rule.py imports test_sclib.exact_simplex_ls for its sc_solver_gap
   diagnostic, so the select run must name code/test_sclib.py with --code.
2. **Weight solver.** SLSQP with the design's options (simplex, uniform start, ftol 1e-12,
   maxiter 2000), on the objective divided by b'b (same minimiser; makes ftol and the KKT
   tolerance scale-free: log-employment objectives are near 1e-4, Prop 99 near 1e5). SLSQP's
   ftol bounds the objective, so its gradient accuracy is about sqrt(ftol) = 1e-6; when the KKT
   residual exceeds 1e-7 SLSQP is restarted from its own solution (same options, at most 3
   times, kept only if the residual falls). The KKT residual reported is that of the normalised
   problem. Unpenalised intercepts (SDID omega0, lambda0) are profiled out exactly by centring.
3. **Demeaned SC has no penalty**, so its weights are not unique when the fit window is shorter
   than the number of donors (every pseudo-date, and R50 in the real window): the fitted path
   over F is unique, the weights and hence the post-period estimate need not be. The solver is
   deterministic, so reruns reproduce; a different solver could give a different SC estimate.
4. **SDID zeta's T_post** is the length of the run's own post window: 8 normally, 7 for
   rob-final-quarters and the second rob-7225 number, 6 for the Dube-timing cross-check.
   anticip uses the 8-quarter omega.
5. **Critical values where the design names no statistic:** S1's simple version uses S1's (s1)
   nu and L quantile; S2's reused-weights wage interval uses S2's (s2); anticip's employment
   uses h2, its wage h1; h3-years' yearly employment ATTs use h2.
6. **Tie-break** compares max |tau| exactly (only the RMSE is rounded to 4 decimals).
7. **Level-mde band:** rates are read against 0.05 +/- 1.96 sqrt(0.05 x 0.95 / n_eff).
   Terciles: np.array_split of the J+1 units sorted by population at B'.
8. **Monte Carlo:** pop_med is the median of the J+1 units of each panel; AR(1) errors are
   stationary with the stated marginal variances; sigma^2 = 1e-4 (all estimators are scale
   equivariant); no seasonality in the DGP, so no seasonal adjustment; unit effects
   ln(pop_j), quarter effects linear. SC/SDID R50 use the first 500 of the 2,000 panels drawn
   for DD/DDT. The panels are drawn in a fixed order from default_rng(20261121); the SC/SDID
   replications run in 8 worker processes, which does not change any number.
9. **Implied jobs** = mean of California's published (not seasonally adjusted) 2024Q2-2026Q1
   quarterly employment x (1 - exp(-tau)).
10. **CEM cross-check:** indexed to September 2023 = 100; detrended = simple minus twice the
    annual trend, the annual trend being half the September 2021 to September 2023 change in
    the California-minus-48-states indexed difference. CEM's placebo rank p counts placebo
    estimates at or below California's (unscaled), one-sided.
11. **Dube cross-check SE** is our scaled placebo SE (root mean square of the scaled placebo
    estimates), not a standard deviation around their mean.
12. **verdict** (changed, C5) also reads runs/plc-nonff/metrics.json and appends 'not separable
    from a California-wide shock' to the H2 label if its 95% CI excludes 0.
13. **Elasticity gating** (H1 rejects and the reused-weights wage ATT is positive) applies to the
    refitted-weights ratio too.
14. **requirements.txt** is `pip freeze` of a fresh Python 3.14.6 venv after installing the four
    design packages, matplotlib (3.11.2, for code/fig_*.py) and wrapt==2.5.2: on the PI's
    instruction only released versions are pinned, so wrapt is its latest release instead of
    the 2.6.0.dev1 pre-release pip resolved by itself (design.method IMPLEMENTATION CHOICES 14
    still says "keeping the resolved wrapt 2.6.0.dev1"; the PI's later instruction overrides it).
    `pip check` reports no broken requirement.
15. **SDID floor in the run scripts** (C1): sclib.crit_for applies q_cal of the run's pool to
    every SDID statistic (S2 always; the selected candidate's statistics if it is SDID); level-mde
    echoes q_cal of both pools (qcal_<pool>_<k>) and reports crit_<stat>_<k>_nofloor; it copies the
    cited check-methods values with prefix cm_. Every run reports solver_kkt_above_1e6.

## After results-r1 (2026-11-21)

- Claim texts revised for R1, R2, R4-R8 (values and macros unchanged; 14 claims added: the
  California H1 pseudo-date ATTs and SEs, r-h1-crit-georgia, r-plc-nonff-sign). Responses are in
  reviews/results-r1/review.json.
- code/posthoc.py (deviation D7, report-only, post hoc) is written and was unit-tested on synthetic
  inputs in the scratchpad (15 checks with known answers). It has not been run: it waits for a code
  review. The posthoc run must name code/posthoc.py and code/sclib.py with --code, and declare as
  --input data/derived/qcew_panel.csv, data/derived/state_panel_pre.csv,
  runs/level-mde/tests.csv, runs/level-mde/metrics.json, runs/h1-wage/metrics.json,
  runs/event-path/event_path.csv and runs/select/metrics.json, with --output
  runs/posthoc/georgia.csv. Part (b) drops Georgia's six L values (54 remain) and keeps
  level-mde's nu_h1 unchanged; Georgia's own placebo variance also lowers nu_hat, which part (b)
  does not recompute.
- posthoc (analysis, unreviewed, human agreed 2026-11-21 via AskUserQuestion; code-r4 C6-C8 fixed
  after the last code round). Results: see the posthoc claims (prefix "Post hoc (deviation D7").
  Known defect, not rerun (single run agreed): the leave-one-out flags b_loo_<fips>_changes_chi,
  b_loo_n_changing and b_loo_changing_states use a 1e-12 tolerance against level-mde's in-memory
  critical values, while runs/level-mde/tests.csv stores T inputs at %.10g, so every flag reads 1
  (differences about 9e-10 for the nine non-Georgia states). The b_loo_<fips>_crit_h1_* values are
  correct; only Georgia's removal moves c_hi. The flags are not claimed.
- describe (D8; analysis, unreviewed, human agreed 2026-11-21; code/describe.py, unit-tested on
  synthetic data, 10 checks): levels only for the summary-statistics table, California, R50 and
  D20, pre-period fit window (31 quarters) and post window (8 quarters). Claims r-desc-*.
- paper-r1 P1: claims added for k under SE_s and SE_n (r-k-<stat>-ses/-sen), the h2-emp
  Ferman-Pinto diagnostic (r-h2-emp-fp-a/-b/-se; A_hat < 0, SE_FP = 0) and r-h2-ses-only (with
  SE_s alone the 95% interval would lie below zero; not the pre-specified inference). The tercile
  and California rejection-rate claims already existed (r-rej-<stat>-<se>-<t1|t2|t3|ca>-<test>).
