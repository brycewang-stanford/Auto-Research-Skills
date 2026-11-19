# Codebook: NSW-treated (Dehejia-Wahba subsample) and CPS-1 comparison group

Prepared by the Data RA on 2026-11-19 (UTC), before the design gate. Only data-prep runs
exist (`fetch-data`, `prepare-data`). No statistic relating treatment to any outcome
was computed, RE75 was not used as an outcome, and nothing was computed under the
placebo's conditioning set (the covariates without RE75 and u75).

## Files

| id | file | rows | columns | sha256 | produced by |
|---|---|---:|---:|---|---|
| nswre74-treated | `data/raw/nswre74_treated.txt` | 185 | 10 | `e7b742fe0ff07a0f45e129b4ff108bb9611cd83d53604732c48a8a0a3e20eda3` | `code/fetch_data.py` |
| cps1-controls | `data/raw/cps_controls.txt` | 15,992 | 10 | `dce640066f8bcdf447864b158b2cb0390bd3f8d6cbe3a27576a06926477d51f8` | `code/fetch_data.py` |
| analysis-noRE78 | `data/derived/analysis_noRE78.csv` | 16,177 | 13 | `35195cc4c3ce0dce11803b3c1f866b73f844ae16896cdf95d1ea639b90c3b524` | `code/prepare_data.py` |

Source: Rajeev Dehejia's data page, <https://users.nber.org/~rdehejia/data/.nswdata2.html>
(`dehejiadata`), fetched 2026-11-19. The experimental control file
(`nswre74_control.txt`, 260 rows) was **not** fetched. Terms: no licence is stated; the
page says LaLonde gave permission to publish the data (see `data/manifest.json`).

## Handling of RE78

Each raw line has ten whitespace-separated fields. `code/fetch_data.py` counts lines and
fields and reads only field 1 (treat); `code/prepare_data.py` converts only fields 1-9 to
numbers. Field 10 (RE78) is never converted, summarised or written, and it is not in
`analysis_noRE78.csv` (`prepare_metrics.json`: `re78_written = false`). The row key
(`src`, `row`) lets the first analysis run after the design gate join RE78 back from
`data/raw`.

## Variables in `data/derived/analysis_noRE78.csv`

| variable | definition | units / coding | source |
|---|---|---|---|
| `src` | source file | `nswre74_treated` or `cps_controls` | added by prepare_data.py |
| `row` | line number of the unit in its raw file (1-based) | integer | added by prepare_data.py |
| `treat` | treatment indicator | 1 = NSW treated, 0 = CPS-1 comparison | raw field 1 |
| `age` | age | years | raw field 2 |
| `educ` | education | years of schooling | raw field 3 |
| `black` | Black | 1/0 | raw field 4 |
| `hisp` | Hispanic | 1/0 | raw field 5 |
| `married` | married | 1/0 | raw field 6 |
| `nodegree` | no high-school degree | 1/0 | raw field 7 |
| `re74` | earnings in 1974 | dollars (1982 dollars per Dehejia and Wahba 1999; the data page states no unit) | raw field 8 |
| `re75` | earnings in 1975 | as `re74` | raw field 9 |
| `u74` | zero earnings in 1974 | 1 if `re74 == 0`, else 0 | constructed (not in the files) |
| `u75` | zero earnings in 1975 | 1 if `re75 == 0`, else 0 | constructed (not in the files) |

Not in the working file: `re78` (earnings in 1978, raw field 10, the outcome).

Earnings for CPS men are SSA administrative earnings, top-coded at the Social Security
maximum; for NSW men they are survey earnings (lalonde1986; smith2005; sources/notes.md).

## Checks against the data page

| check | data page | found | match |
|---|---|---|---|
| rows, `nswre74_treated.txt` | 185 | 185 | yes |
| rows, `cps_controls.txt` | 15,992 | 15,992 | yes |
| fields per row, both files | 10 (treat, age, educ, black, hisp, married, nodegree, RE74, RE75, RE78) | 10 on every row | yes |
| treat in treated file | 1 | 1 on every row (written `1.0000000e+000`) | yes |
| treat in CPS file | 0 | 0 on every row | yes |
| binary variables coded 1/0 | yes | black, hisp, married, nodegree: no other values | yes |
| u74 / u75 columns | absent (must be built) | absent; built from RE = 0 | yes |

Further coding checks (`data/prepare_metrics.json`): no missing values in fields 1-9;
age and educ are whole numbers; no negative earnings; no unit is both Black and
Hispanic; `nodegree` equals `educ < 12` on every row. No rows were dropped (16,177 kept:
185 treated, 15,992 CPS).

## Covariate summaries by group

Each variable summarised on its own within each group (`data/derived/covariate_summary.json`).
No between-group difference, test or model was computed.

| variable | NSW treated (n = 185) mean | sd | min | max | CPS-1 (n = 15,992) mean | sd | min | max |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| age | 25.82 | 7.16 | 17 | 48 | 33.23 | 11.05 | 16 | 55 |
| educ | 10.35 | 2.01 | 4 | 16 | 12.03 | 2.87 | 0 | 18 |
| black | 0.843 | 0.365 | 0 | 1 | 0.074 | 0.261 | 0 | 1 |
| hisp | 0.059 | 0.237 | 0 | 1 | 0.072 | 0.259 | 0 | 1 |
| married | 0.189 | 0.393 | 0 | 1 | 0.712 | 0.453 | 0 | 1 |
| nodegree | 0.708 | 0.456 | 0 | 1 | 0.296 | 0.456 | 0 | 1 |
| re74 | 2,095.57 | 4,886.62 | 0 | 35,040.07 | 14,016.80 | 9,569.80 | 0 | 25,862.32 |
| re75 | 1,532.06 | 3,219.25 | 0 | 25,142.24 | 13,650.80 | 9,270.40 | 0 | 25,243.55 |
| u74 | 0.708 | 0.456 | 0 | 1 | 0.120 | 0.325 | 0 | 1 |
| u75 | 0.600 | 0.491 | 0 | 1 | 0.109 | 0.312 | 0 | 1 |

### Comparison with Dehejia and Wahba (1999) Table 1

Reference values as transcribed by the Scout from the NBER WP 6586 version
(sources/notes.md); the Data RA did not re-read the paper.

| group | variable | DW (1999) Table 1 | this file | note |
|---|---|---:|---:|---|
| CPS-1 | N | 15,992 | 15,992 | match |
| CPS-1 | age | 33.22 | 33.2252 | last digit: truncated, not rounded |
| CPS-1 | educ | 12.02 | 12.0275 | last digit: truncated, not rounded |
| CPS-1 | black | 0.07 | 0.0735 | match |
| CPS-1 | married | 0.71 | 0.7117 | match |
| CPS-1 | RE74 | 14,016 | 14,016.80 | last digit: truncated, not rounded |
| CPS-1 | RE75 | 13,650 | 13,650.80 | last digit: truncated, not rounded |
| NSW treated | N | 185 | 185 | match |
| NSW treated | age | 25.81 | 25.8162 | last digit: truncated, not rounded |
| NSW treated | black | 0.84 | 0.8432 | match |
| NSW treated | married | 0.19 | 0.1892 | match (rounded) |
| NSW treated | RE74 | 2,096 | 2,095.57 | match (rounded) |
| NSW treated | RE75 | 1,532 | 1,532.06 | match |

Every reference value agrees with the file to within one unit of the last digit printed.
Five of them look truncated rather than rounded, while two treated values look rounded;
this is a presentation difference in the table (or its transcription), not a data
discrepancy. educ, hisp, nodegree, u74 and u75 have no reference values in the notes and
were not checked against the paper.

## Observations for the design (no action taken)

- **Top-coding in CPS earnings.** 3,052 CPS men (19.1%) are at the file maximum of
  `re74` ($25,862.32) and 3,007 (18.8%) at the maximum of `re75` ($25,243.55). This is
  consistent with the SSA top-code that lalonde1986 reports (21% of men at the maximum
  in 1976). In the treated file, one man is at each maximum, and the treated maximum of
  `re74` ($35,040.07) exceeds the CPS top-code.
- **Repeated covariate vectors.** 2,401 CPS rows repeat another CPS row's nine raw
  covariates exactly (largely a consequence of the top-code and coarse covariates). All
  are kept.
- **Range differences.** CPS men are 16-55 (lalonde1986: men over 55 excluded); treated
  men are 17-48. CPS `educ` runs 0-18, treated 4-16.

## Discrepancies

- None between the files and the data page (row counts, column count, order, coding).
- The data page's heading reads "Dehejia-Wahha Sample" (a typo for Dehejia-Wahba).
- imbens2025 Table 1 reports 15,922 CPS observations; the file has 15,992, as the data
  page, dehejia1999 and athey2024 state (already noted by the Scout as a typo in imbens2025).
