# Run and implementation notes

## 2026-11-21 — c-implement

The prior data-ra fetch-seed record is unchanged. No seed analysis has been executed in this step. Implemented eight planned run scripts, shared estimation code, fixed dependency pins and execution_manifest.json. Executed four memory-only artificial-data checks: exact linear counterfactual recovery with and without capping; repeatability of the full 499-refit bootstrap; rank/invalid-SE failure rules; fixed five-test Holm adjustment. All passed using CPython 3.14.6 and package versions in code/requirements.txt. Artificial checks do not validate identification, actual cohort support or actual-cohort inference.

Execution remains blocked pending independent code review and PI resolution of D1 ordering/benchmark wording and D2 region validation; see code/IMPLEMENTATION.md. The manifest proposes precision-plan before main-att to satisfy the prospective precision promise but does not claim an approved amendment. No plan, review or task status was edited; no result claims were created.

Metrics that should not become paper claims: computational seeds, fit/status flags and exact bookkeeping can remain in the reproducibility record if not used as paper numbers; the OLS mechanical ci90 endpoints are unused helper outputs, not an extra equivalence analysis. Failed-run point estimates without valid uncertainty must be clearly labeled failures if displayed. All other computed substantive metrics are intended for subsequent all-result reporting/claims after the results stage; the final claims writer must explain any unused metric here rather than selectively omit adverse findings. At this stage there are no actual-cohort computed metrics to claim.

## 2026-11-21 — execution preparation

C1 response: stale blocker wording above is superseded by recorded plan.json prospective clarifications D1/D2. Precision runs first; fixed ±1000 supplied-unit benchmark has no welfare calibration; region vocabulary checks extract consistency only. Documentation and manifest aligned, response recorded without ruling. All executable code and requirements hashes match code-r1. No estimator or specification deviation.

## 2026-11-21 — environment correction, analysis stopped

Initial manifest setup used plain python3, which selected Python 3.11 in this execution shell; installation failed because numpy==2.5.3 requires >=3.12. Retried with explicit /opt/homebrew/bin/python3.14 (3.14.6), exposing five unpinned transitive dependencies. PI instructed correction before analysis and another independent code review. Added exact transitive pins and explicit python3.14 setup with disabled pip cache; no executable analysis scripts changed and no analysis run executed. This corrects the earlier implementation claim of complete pins. The failed setup produced no result metrics or claims.

Environment verification completed: explicit Python 3.14.6 installation succeeded, all thirteen requirement pins match installed distribution metadata, and pip check reported no broken requirements. code/environment.json records versions and requirements hash. pip check emitted a cache-permission warning and disabled the external cache; installation used --no-cache-dir. No seed analysis or result claim was produced. This is setup verification only, not independent replication.

Executed precision-plan through crew.py run, reviewed code-r2, exit 0; ledger elapsed 5 seconds, cumulative 5/1800 seconds.

Executed main-att through crew.py run, reviewed code-r2, exit 0; ledger elapsed 8 seconds, cumulative 13/1800 seconds.

Executed support-diagnostics through crew.py run, reviewed code-r2, exit 0; ledger elapsed 4 seconds, cumulative 17/1800 seconds.

Executed alternative-ols through crew.py run, reviewed code-r2, exit 0; ledger elapsed 2 seconds, cumulative 19/1800 seconds.

Executed capped-odds through crew.py run, reviewed code-r2, exit 0; ledger elapsed 7 seconds, cumulative 26/1800 seconds.

Executed preprogram-placebo through crew.py run, reviewed code-r2, exit 0; ledger elapsed 4 seconds, cumulative 30/1800 seconds.

Executed bias-sensitivity through crew.py run, reviewed code-r2, exit 0; ledger elapsed 2 seconds, cumulative 32/1800 seconds.

Executed decision-report through crew.py run, reviewed code-r2, exit 0; ledger elapsed 2 seconds, cumulative 34/1800 seconds.

## Results coverage

All eight approved analysis runs completed successfully in order, under code-r2 with unchanged executable hashes and reviewed requirement pins. Total ledger elapsed analysis time: 34 seconds. No command failed and no statistical fit failed; all three bootstrap runs retained all 499 resamples. All numeric metrics have claims except computational seed and mechanical 90% endpoints for OLS/capped/placebo: these remain reproducibility/helper outputs, are not extra equivalence tests, and are not intended for the paper. Empty failure-reason strings report no failure and are not numerical claims. Claims include all null/contradictory findings, all support diagnostics and every prospective grid cell. No sample, model, threshold, bootstrap, outcome or multiplicity change was made.

## Factual results handoff for independent review

Primary synthetic full-cohort participant ATT in supplied re78 earnings units: -119.65942860150413; bootstrap SE 167.7504666865724; marginal 95% interval [-448.4443016969631, 209.12544449395483]; marginal 90% interval [-395.5843921534679, 156.2655349504596]. Primary claim ids are primary-effect/primary-ci-low/primary-ci-high. The sample is 4000, including 1621 participants. The interval spans zero, so H1 positive support is inconclusive, not evidence of no effect; it is not entirely below zero either. Raw zero-effect p=0.4756489971297513 and Holm p=1. The conditional marginal interval excludes effects outside its endpoints under the identification/inference assumptions; it does not bound hidden bias.

The fixed ±1000 supplied-unit benchmark TOST raw p is 7.691417113876829e-08 and Holm p is 3.0765668455507316e-07. Both the marginal 90% interval and conservative 98% interval [-509.90537014717074,270.58651294416245] lie inside the fixed bounds. The planned software decision is h2_supported=1. This is conditional benchmark equivalence only, with no documented currency, price base, welfare calibration or smallest economically relevant threshold. It must not be described as absence of a causal effect or policy irrelevance, particularly given the placebo result.

All five tests are retained. OLS constant additive re78 coefficient=-123.1592216146125, HC3 SE=157.30753940515368, marginal 95% interval [-431.47633334532054,185.15789011609556], raw p=0.43367408136304186, Holm p=1. Capped-control-odds re78 sensitivity=-109.63038399839611, bootstrap SE=166.37525256884135, marginal 95% interval [-435.71988695207125,216.45911895527905], raw p=0.509937868534754, Holm p=1. They give similar null-spanning adjusted associations, but OLS is not generally the heterogeneous-effect ATT and capping changes the equation; neither replaces primary.

Adverse diagnostic: future participation pseudo-effect on preprogram re75=-3595.9868303137723, bootstrap SE=167.86521308252495, marginal 95% interval [-3924.996602212654,-3266.9770584148905], raw p=8.356534366389994e-102, Holm p=4.178267183194997e-101. The placebo excludes re75/unemp75 covariates as planned. This challenges selection adjustment across preprogram earnings dynamics, although it does not directly test the exact main exchangeability assumption. It materially weakens causal credibility and must accompany the benchmark equivalence statement. The software permission flag only checks primary fitting/support, not placebo credibility or hidden selection.

Conservative simultaneous 99% intervals (Bonferroni over the fixed five-test family): main [-551.7559963767809,312.43713917377266]; OLS [-528.3565912835807,282.0381480543557]; capped [-538.1846349505671,318.9238669537749]; placebo [-4028.3789652182204,-3163.5946954093242]. Marginal 95% intervals are not simultaneous discovery intervals.

Support: no prespecified inadequacy flag fired. Control odds ESS=1022.4785895028086, maximum control odds=12.021324510424272; no participants exceed score .95 or fall outside the control score range. All feature-level raw/weighted SMDs and score quantiles are in claims; largest absolute weighted SMD is married at 0.04186241818689084. Observed balance cannot verify exchangeability. Control re78 mean=11392.762614543926 and SD=6258.935536351515; primary ratios to them are -0.010503109092148352 and -0.019118175591764684, respectively.

Prospective precision: the grid was executed before any re78 analysis, using fixed hypothetical counts/variances, with every cell claimed. For hypothetical SD 10000/VIF 4, raw and conservative equivalence power are zero and even centered intervals cannot fit; for SD 5000/VIF 4 the raw power is 0.8539240862465467 and conservative power 0.5599084795795666. This demonstrates dependence on assumed precision, not observed/post-hoc power. Authorized baseline re74 mean/SD=8004.470897500001/5818.809375151773; re75 mean/SD=7695.7872075/5932.948071018141. They contextualize supplied units without establishing welfare relevance or changing the benchmark.

Bias sensitivity: all seven prespecified signed b scenarios and every boundary shift are claimed. At b=-500 the shifted marginal 95% interval is [51.55569830303688,709.1254444939548]; at b=500 it is [-948.4443016969631,-290.87455550604517]. At b=-2000 the point/interval is 1880.340571398496/[1551.555698303037,2209.125444493955]; at b=2000 it is -2119.6594286015043/[-2448.444301696963,-1790.8745555060452]. These are assumption scenarios, not identified bounds, and show how unobserved selection can change signs and benchmark conclusions. Signed boundary shifts retain the tau_true=tau_hat-b direction.

Limitations and deviations: synthetic application only, not an actual historical program estimate or a published-estimate replication. Voluntary participation supplies no natural experiment. Exchangeability, consistency/no interference, working-model correctness and IID regular bootstrap inference remain assumptions; no cluster identifier exists and region is a covariate. All fits succeeding does not establish finite-sample validity. Retain the post-design-gate/pre-analysis D1 precision scheduling and supplied-unit benchmark clarification and D2 observed-region encoding/absence of independent semantics. The setup correction and additional transitive pins were independently reviewed in code-r2 before execution. Apart from these documented prospective clarifications and environment correction, no analysis deviation, tuning, excluded-outcome read, alternate target, added test or unreviewed run occurred. No failed run was suppressed. Independent clean-environment replication is still pending; local setup checks are not replication.

Claims/macros: 288 result claims plus existing citation claims; every substantive numeric metric is copied directly, with computational seed and unused sensitivity/OLS 90% helper endpoints excluded for the reasons above. numbers.tex and process.tex generated by crew.py numbers; workspace validation passed with zero warnings. No paper section was written and no gate advanced.

## Results-r1 R1 response — claim semantics only

Corrected 27 hypothetical precision containment flags to Boolean descriptions, including strict containment and zero centering, and six signed endpoint-to-boundary bias thresholds to the direction endpoint_shifted=endpoint_original-b. Values, provenance, ids, macro names/formats and executable code unchanged. Checked every result value against its supporting metric. No new run or estimate; response recorded without ruling or status change.
