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
| `code/test_analysis.py` | unit-tests | run on SYNTHETIC data only: 43 of 43 checks passed |

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

## Literal metric fields (code-r1 F2)

Two recorded metrics are literals written by scripts that have already run; those scripts are not edited, because editing them would invalidate their runs:

- `runs/design-mde/metrics.json` field `outcome_loaded` is written as the constant 0 by `code/design_mde.py`. It is true by construction (the script reads only `margin` and the covariates through `usecols`), but nothing in the run measures it.
- `runs/fetch-data/metrics.json` field `sha256_matches_seed` is written as the constant 1 by `code/fetch_data.py` after a check against a constant hard-coded in that file. The field shows agreement with that constant, not with the seed task.

The raw file's sha256 (def1fc6b...2ad44) matches `data/manifest.json` and the constant in `code/fetch_data.py`. It has not been checked against the seed task by any reviewer. The absence of `vote` reads is verified for `design_mde.py`, `h2_density.py` and `h2_covariates.py` by `usecols` and by the static check in `test_analysis.py`.

## bw_capped flag (code-r2 F7)

The positive branch of `bw_capped` is exercised by a unit test, not only by the full script. `test_analysis.py` fits `rdrobust` on a synthetic one-sided sample with h and b forced to `bw_max`, and checks that `capped_flag()` in `h2_placebo.py` and `h2_covariates.py` returns 1; a bandwidth of half `bw_max` returns 0. The full placebo path cannot be forced to a cap by its inputs, so the flag is shown to fire on a real rdrobust output, not through `one_side()` end to end.

## Printed comparison (code-r2 F1)

`h2_covariates.py` compares the four CCFT p. 397 values under both settings: `*_off_minus_printed` and `*_off_printed_match` for 'off' (primary), and `*_adj_*` for 'adjust' (secondary). A match means agreement to 0.0005, the printed precision. Any paper statement must name the setting.

## Code-r1 changes (before any analysis run)

- `code/h2_covariates.py` declares `runs/design-mde/metrics.json` as an input and records, per covariate, its SE and MDE differences from the design values and a match flag (F3).
- `code/h1_replication.py` moves the H1 tolerance rule into `tolerance_flags()` so that the tests can exercise it (F4).
- `code/test_analysis.py` now has 43 synthetic checks, including H1 tolerance pass and fail cases, a synthetic effect of 3 checked to 0.25, and the design-mde match and mismatch cases (F4). The suite never reads the real raw file; the design-mde comparison uses a fixture file.
- No analysis script has been run on the real data since code-r1.
