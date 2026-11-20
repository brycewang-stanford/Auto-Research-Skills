# Econometrician notes (ss-rd-senate)

## Phase 1 (code only, 2026-11-20)

Scripts written under `code/` from the approved analysis plan (design gate approved
2026-11-20 05:23 UTC). No analysis script has been run on the real data. Each script
takes the metrics path as its first argument and `--data PATH` (default
`data/raw/rdrobust_senate.csv`); only the unit test passes a different file.

| Script | Run id | Status |
|---|---|---|
| `code/h1_replication.py` | h1-rdrobust | written, not run |
| `code/h2_density.py` | h2-density | written, not run |
| `code/h2_covariates.py` | h2-covariates | written, not run |
| `code/h2_placebo.py` | h2-placebo | written, not run |
| `code/h2_selection.py` | h2-selection | written, not run; run only after the gate (gate already approved, run when instructed) |
| `code/h3_sensitivity.py` | h3-sensitivity | written, not run |
| `code/test_analysis.py` | unit-tests | run on SYNTHETIC data only: 31 of 31 checks passed |

`unit-tests` lists all six scripts as `--code`, so editing any of them makes the run stale.

## Order of operations so far

1. `fetch-data`, `prepare-data`, `dr-checks`, `design-mde` (earlier sessions; see their run records).
2. `unit-tests` (data-prep): `code/test_analysis.py` writes a synthetic file (1,390 rows, same columns, 93 missing outcomes, 282 missing termshouse/termssenate, mass points at +/-100) to the scratch directory and runs every script on it. The real raw file is not passed to any script.

## Choices made while coding (within the approved plan)

- All analysis scripts read the raw seed file, not `data/derived/senate_rd.csv`, to match `design-mde`. `vote_observed` is computed in code (`h2_selection.py`).
- `h2_density.py` and `h2_covariates.py` do not load the `vote` column.
- rdrobust's sides follow its convention: left is x < c, right is x >= c. The estimation sample is rows with non-missing vote (1,297 expected).
- rddensity: `T_Q`/`p_Q` are the robust statistic (`test`, jackknife) with the package defaults, matching `design-mde`. The conventional statistic (`T_conv`, `p_conv`) comes from a second call with `useall = True` (`test_p`). A third call with `massPoints = False` gives `p_Q_nomass`. `T_Q_asy` is NaN under `vce = 'jackknife'`; it is not used.
- H2(b) reports both masspoints settings. The decision uses `off`; the `adjust` reading (`*_adj_*`) is compared with the four printed p-values (0.897, 0.561, 0.901, 0.634), which are read as CCFT (2017) p. 397 default-option output (design-r3 F13). The plan text cites Sec. 7.4; the p. 397 reference from F13 is the one used in the metrics.
- H2(c) cutoffs: `c_L` and `c_R` are medians of the full margin column on each side (outcome-free; design-r3 F11). Each one-sided sample is restricted to rows with a non-missing vote. `bw_max` is computed from that sample.
- H3 bandwidths: (ii) and (iii) use the fixed values h = 8.854, b = 13.992 and h = 35.416, b = 55.968, as in the plan. The H1 `off` row is not recomputed in H3.
- H1 side counts, distinct values and mass shares are recorded on the 1,297-row estimation sample (design-r3 F12).

## Claim ids to fill in after the runs (not yet written to claims.jsonl)

- H1: `rd-effect`, `rd-ci-low`, `rd-ci-high`, `rd-n`, `rd-bw`
- H2(a): `rd-density-p`
- H2(b): `rd-cov-class-p`, `rd-cov-termshouse-p`, `rd-cov-termssenate-p`, `rd-cov-population-p`
- H2(c): `rd-placebo-left-est`, `rd-placebo-right-est`
- H2(d): `rd-selection-p`
- H3: `rd-h3-2014-bw-effect`, `rd-h3-half-bw-effect`, `rd-h3-double-bw-effect`, `rd-h3-p2-effect`, `rd-h3-adjust-effect`

## Open items for the PI

- None blocking. The analysis runs (h1 through h3) wait for the PI's instruction; h2-selection is also post-gate and is not run yet.
