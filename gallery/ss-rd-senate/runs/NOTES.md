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

## bw_capped flag (code-r2 F7, rewritten after code-r3 F7)

The unit test checks only the equality comparison. It forces h and b to bw_max as inputs to `rdrobust` on a synthetic one-sided sample and checks that `capped_flag()` returns 1; a bandwidth of half bw_max returns 0. It does not show that the cap binds. The cap was never observed to trigger on real `rdrobust` output, and no synthetic search in code-r3 (240 fits across four data-generating processes, plus 40 more) found a binding cap. The paper reports `bw_capped` only as recorded. On the real runs every recorded `bw_capped` value is 0 (H2(b) and H2(c)).

## Printed comparison (code-r2 F1)

`h2_covariates.py` compares the four CCFT p. 397 values under both settings: `*_off_minus_printed` and `*_off_printed_match` for 'off' (primary), and `*_adj_*` for 'adjust' (secondary). A match means agreement to 0.0005, the printed precision. Any paper statement must name the setting.

## Code-r1 changes (before any analysis run)

- `code/h2_covariates.py` declares `runs/design-mde/metrics.json` as an input and records, per covariate, its SE and MDE differences from the design values and a match flag (F3).
- `code/h1_replication.py` moves the H1 tolerance rule into `tolerance_flags()` so that the tests can exercise it (F4).
- `code/test_analysis.py` now has 43 synthetic checks, including H1 tolerance pass and fail cases, a synthetic effect of 3 checked to 0.25, and the design-mde match and mismatch cases (F4). The suite never reads the real raw file; the design-mde comparison uses a fixture file.
- No analysis script has been run on the real data since code-r1.

## Phase 2: analysis runs (2026-11-20, plan order)

Runs (all `crew.py run --kind analysis`, `.venv`, raw seed file, no re-specification): `h1-rdrobust`, `h2-density`, `h2-covariates` (declares `runs/design-mde/metrics.json` as input), `h2-placebo`, `h2-selection`, `h3-sensitivity`. No run failed; no tolerance check was re-run or changed after seeing a number. Claims are in `claims.jsonl` (95 result claims, all linked to these runs) and `paper/numbers.tex`.

### H1 verdict: pass on 'off' (computational reproduction, not evidence about the incumbency advantage)

| Quantity | Replicated ('off', decision) | Printed (CCFT 2017) | Difference | Flag |
|---|---|---|---|---|
| Conventional estimate (rd-effect) | 7.41604 pp | 7.416 | 3.8e-05 | pass (0.01 pp) |
| Robust CI lower (rd-ci-low) | 4.09441 pp | 4.09441 | 4.6e-06 | pass |
| Robust CI upper (rd-ci-high) | 10.92546 pp | 10.9255 | -3.5e-05 | pass |
| N | 1,297 | 1,297 | 0 | pass (exact) |
| h (rd-bw) | 17.70803 | 17.708 | 3.0e-05 | pass (0.0005) |
| b (rd-b, F8) | 27.98412 | 27.984 (printed; H3 baseline) | 0.00012 | recorded, not a tolerance |

All five flags are 1 (`h1_pass_off` = 1). Side counts on the 1,297-row estimation sample: 595 left, 702 right. Mass points: none on the left; 38 right observations at +100 (share 0.053 of right-side rows, 0.0527 exactly); 665 distinct right values.

'adjust' reading (secondary, same run): conventional 7.41413 pp, robust CI [4.09370, 10.91931], h = 17.75440, b = 28.02809. Against 'off' the estimate moves by -0.0019 pp, the CI endpoints by -0.0007 and -0.0062, and h by +0.046. The bwcheck trigger is not met on either side (mass shares 0.0 and 0.053, below 0.20).

### H2 results against their MDEs

- **H2(a) density** (rddensity, robust T_Q, single test): T_Q = -0.875, p = 0.381. Estimated density difference -0.00355 (SE 0.00405, jackknife) against an MDE of 0.01136 (from design-mde; 0.52 of the left density 0.02169). The estimate is about 31% of the MDE. Non-rejection is read only as no evidence of a discontinuity larger than the MDE. Recorded surprise: the conventional statistic from the same data (useall) gives T = -1.651, p = 0.099; the robust statistic is the primary and is reported with its own p. The p_Q with massPoints = False is 0.381 (identical to the decimal reported).
- **H2(b) covariates** ('off' primary; Holm over four, within this family): class p = 0.897 (coef -0.021, MDE 0.401, N 1,390); termshouse p = 0.561 (coef -0.173, MDE 1.400, N 1,108); termssenate p = 0.901 (coef -0.192, MDE 2.091, N 1,108); population p = 0.634 (coef -318,455 persons, MDE 2,185,253, N 1,390). Holm-adjusted p = 1.0 for all four; none rejects at 5%. Each |coef| is 5 to 15% of its MDE. Against the printed p. 397 values (CCFT 2017), 'off' matches to 0.0005 for all four (flags 1); 'adjust' matches for termshouse and population only (flags 0 for class and termssenate, differences -0.00058 and -0.00092). The paper must name 'off' for any match statement. The design-mde SEs and MDEs match exactly (rel. tol 1e-6; flags 1).
- **H2(c) placebo cutoffs** (report-only, no MDE, no test): c_L = -14.3449, c_R = 20.4399. Left (N = 595): estimate -0.029 pp, robust CI [-12.17, 14.14], width 26.3 pp, bandwidth h = 4.81. Right (N = 702): estimate -1.068 pp, CI [-11.29, 11.27], width 22.6 pp, h = 5.69. Neither placebo is a conclusion. Recorded: both bw_capped flags are 0, so no placebo window was boundary-limited. Surprise: the placebo CIs are wider than the main CI (width 6.8 pp), and the placebo bandwidths are about 0.27 to 0.32 of the main H1 bandwidth.
- **H2(d) selection** (observed-outcome indicator, single test): coefficient -0.062 on the proportion scale (about -6.2 pp), robust CI [-14.5, 1.8] pp, p = 0.125, N = 1,390, observed share 0.933. MDE 11.6 pp. The estimate is about 53% of the MDE. Surprise: this is the largest falsification point estimate relative to its MDE; the sign means the observed-outcome share is lower just on the Democratic-win side of the cutoff. Non-rejection does not rule out a selection effect of about 6 pp. This is the threat to watch for H1.

### H3 descriptive sensitivity (no decision rule; table)

| Specification | Estimate (pp) | Robust CI (pp) | h | b | N |
|---|---|---|---|---|---|
| i. printed 2014 bandwidths (h 16.79369, b 27.43745) | 7.4253 | [4.0697, 10.9833] | 16.794 | 27.437 | 1,297 |
| ii. half H1 bandwidth (h 8.854, b 13.992) | 8.3726 | [4.7557, 14.0305] | 8.854 | 13.992 | 1,297 |
| iii. double H1 bandwidth (h 35.416, b 55.968) | 7.1675 | [5.3578, 10.6456] | 35.416 | 55.968 | 1,297 |
| iv. p = 2, q = 3, mserd bandwidth | 8.0457 | [4.2134, 12.4228] | 22.210 | 33.246 | 1,297 |
| v. H1 specification, masspoints adjust | 7.4141 | [4.0937, 10.9193] | 17.754 | 28.028 | 1,297 |

The b baseline for (ii) and (iii) is the printed 27.984. The H1 'off' b is 27.98412, so the baseline is the same to 0.0001 and (ii) and (iii) are half and double the printed b, which equals the H1 b. The printed 2014 row (i) reproduces the 2014 CI shown in CCFT 2017 to the printed precision ([4.06975, 10.9833]). Surprise: the half-bandwidth row has the widest CI of the five (9.3 pp wide); all five point estimates lie between 7.2 and 8.4 pp (7.17 to 8.37) and every CI overlaps the H1 CI.

### Other surprises and points for the paper

- The estimate is local to close elections (bandwidth about 17.7 points, 595 left and 702 right observations within the estimation sample). The paper must not call it the incumbency advantage in all elections.
- The existing citation claim for the McCrary-type density test in CFT (2015) reports p = 0.39; the rddensity robust test here gives 0.381. These are different tests; the paper should not present them as the same number.
- Holm adjustment is 1.0 for every covariate because the smallest p-value (termshouse, 0.561) times four is above 1.
- No `bw_capped` flag fired on any real run (see above).
- design-mde is a data-prep run and cannot support result claims. Its density MDE (0.01136) and the relative MDE (0.52) are therefore not in claims.jsonl; the paper takes them from `runs/design-mde/metrics.json` and the NOTES above. The covariate MDEs are also in `h2-covariates` (`*_mde`) and are claimed there.
- Literal fields (code-r2 F6, code-r3 F2): `outcome_loaded` and `sha256_matches_seed` are not cited as checks.

### Open items

- The clean rerun (`crew.py rerun`, task `t-rerun`) is not part of this round and stays `todo`.
- code-r3 F9 (test guard, substring) stays open; the scripts were not changed in this round.
