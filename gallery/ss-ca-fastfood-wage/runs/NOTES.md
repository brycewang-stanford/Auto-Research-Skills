# Run notes (Econometrician)

## Order of runs

1. `check-methods` (data-prep, 2026-11-21; code/test_sclib.py with sclib.py, select.py,
   level_mde.py; inputs: the Prop 99 file, state_panel_pre.csv (the pop column for the Monte
   Carlo; all rows for the seasonal-factor check), state_panel.csv (seasonal-factor check only:
   2014Q1-2019Q4 rows, no later statistic)). Results: see "check-methods results" below.

No analysis run has been made (the design gate is pending).

## check-methods results

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

1. **code/select.py shadows the standard-library module `select`.** Running any script in code/
   puts code/ first on `sys.path`, and scipy imports subprocess -> selectors -> select, which
   would load code/select.py and crash. Every script in code/ therefore starts with a four-line
   prologue that imports the standard `select` before code/ is on the path. test_sclib.py
   loads select.py under another module name. Renaming the script (e.g. select_rule.py) would
   remove the need; the design names it select.py, so the name was kept.
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
12. **verdict** reads the runs analysis_plan 17 lists (2-5, 7, 8, 9-13); the plc-nonff
    qualification of the H2 label (analysis_plan 14) is applied by the paper from runs/plc-nonff.
13. **Elasticity gating** (H1 rejects and the reused-weights wage ATT is positive) applies to the
    refitted-weights ratio too.
14. **requirements.txt** is `pip freeze` of a fresh Python 3.14.6 venv with the four design
    packages; pip resolved wrapt to 2.6.0.dev1 (a statsmodels/formulaic dependency).
