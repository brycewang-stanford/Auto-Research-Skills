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
