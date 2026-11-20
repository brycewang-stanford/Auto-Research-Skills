# Codebook: Senate RD data (`senate-rd`)

Prepared by the Data RA on 2026-11-20. No sample restriction has been applied; the
design gate has not yet fixed one. Every row of the raw file is kept.

## Source and files

- Origin: `https://raw.githubusercontent.com/rdpackages/rdrobust/2589686d980af0eb2c0edd945d4a43e8bc081872/R/rdrobust_senate.csv`
- Raw file: `data/raw/rdrobust_senate.csv` (git-ignored), sha256 `def1fc6b8ae5af273f2140aa449c81b3ecfe1d0f325aa80ceccb0d9638a2ad44`, matches the seed task.
- Derived file: `data/derived/senate_rd.csv` (git-ignored), written by `code/prepare_data.py` with one added column, `vote_observed`.
- Licence: no explicit licence is stated for the data file. It is distributed publicly with the rdrobust package for replication.
- Metrics: `runs/prepare-data/metrics.json`, `runs/fetch-data/metrics.json`.

## Variables

| Variable | Definition | Units | Source column | Missing | Range (non-missing) |
|---|---|---|---|---|---|
| `state` | State of the Senate seat (string, 50 distinct values) | text | `state` | 0 | n/a |
| `year` | Election year of the current race (t) | year | `year` | 0 | 1914 to 2010 |
| `vote` | Democratic vote share in the next election for the same seat (t+2, outcome) | percent | `vote` | 93 | not reported (outcome, see note) |
| `margin` | Democratic margin of victory in the current election (t), running variable, cutoff 0 | percentage points | `margin` | 0 | -100 to 100 |
| `class` | Senate class of the seat (predetermined covariate) | 1 to 3 | `class` | 0 | 1 to 3 |
| `termshouse` | Number of prior House terms of the Democratic candidate (predetermined covariate) | count | `termshouse` | 282 | 0 to 16 |
| `termssenate` | Number of prior Senate terms of the Democratic candidate (predetermined covariate) | count | `termssenate` | 282 | 1 to 20 |
| `population` | State population (predetermined covariate) | persons | `population` | 0 | 78,000 to 37,253,956 |
| `vote_observed` | 1 if `vote` is non-missing (derived) | 0/1 | derived | 0 | 0 to 1 |

Note on `vote`: the range and summary statistics of the outcome are deliberately not
tabulated, and no statistic of `vote` is computed by side of the cutoff, before the design
gate.

Note on the covariates: the seed file has four predetermined covariates. The other four
covariates used by Cattaneo, Frandsen and Titiunik (2015) are not in the file.

## Counts

| Count | Value |
|---|---|
| Rows in raw file | 1,390 |
| Rows kept | 1,390 |
| Rows dropped | 0 |
| Rows with non-missing `vote` | 1,297 |
| Rows with `margin` < 0 | 640 |
| Rows with `margin` = 0 | 0 |
| Rows with `margin` > 0 | 750 |

## Missingness

- `vote`: 93 missing (6.7 percent of 1,390).
- `termshouse` and `termssenate`: 282 missing each (20.3 percent). These two covariates
  have the same missing rows. Any balance test on them uses a smaller sample than 1,390.
- `margin`, `year`, `state`, `class`, `population`: no missing values.

## Checks against the source

Compared with CCFT (2017), Section 7.2, p. 390 and p. 392, and CFT (2015), Section 5:

| Check | Source reports | Data file | Result |
|---|---|---|---|
| Rows in file | 1,390 | 1,390 | Match |
| Non-missing outcome (N in the default output) | N = 1,297 | 1,297 | Match |
| Year range | 1914 to 2010 | 1914 to 2010 | Match |
| Variable names | `vote`, `margin`, and the covariates named in the source | as listed above | Match |

Not checked here: the 8-covariate list in CFT (2015), and the printed balance-test
regressions in CCFT (2017) p. 397 (those are regressions of covariates on margin, reserved
for the design-stage tests). The printed summary statistics for non-outcome variables were
compared in the design-stage checks below.

Discrepancies: none found in the checks above. The covariate missingness (282 rows for
`termshouse` and `termssenate`) was not compared with any source, because the source's
missing-value counts were not checked.

## Restrictions not applied

No restriction is applied. Any sample restriction (for example, a bandwidth window or a
requirement of non-missing covariates) follows the approved design and will be applied
in a later data-prep run.

## Design-stage checks (dr-checks)

Run `dr-checks` (`code/prepare_checks.py`, metrics in `runs/dr-checks/metrics.json`) on
2026-11-20. The script computes no statistic of `vote` by side of the cutoff and no regression.
The only use of `vote` is a count of non-missing cases by side (595 left, 702 right).

### Ties and mass points in `margin`

| Sample | Obs | Distinct values | Values shared by 2+ obs | Obs at a shared value | Largest multiplicity |
|---|---|---|---|---|---|
| All rows with non-missing `margin` | 1,390 | 1,352 | 2 | 40 (2.9%) | 38 at +100 |
| \|`margin`\| <= 30 | 995 | 995 | 0 | 0 | 1 |

- The only mass points are at the bounds of the running variable: +100 (38 observations) and
  -100 (2 observations). No other value is shared. The within-30 sample has no ties.
- The 38 observations at +100 lie far outside any bandwidth used in the design (h = 17.708,
  b = 27.984, and the 2014 values 16.79 and 27.44), so they do not enter the H1 targets.
  Whether they are unopposed races is an interpretation, not verified against the source.
- 97.1% of margins are non-integer, so ties do not come from rounding.

### Printed descriptive statistics versus the file

Printed values: CCFT (2017), Sec. 7.2, `sum vote margin class termshouse termssenate population`,
p. 390 (Stata output; the file is `rdrobust_senate.dta`). PDF sha256
`c41e81d2b3763ea5e2ac060747f7c6a22cf6ae3f7fd27d44dfece82e2fe63c8a`, read from the Scout's
scratchpad copy (`pdftotext`). Matching is at the printed precision.

| Variable | Statistic | Printed | File | Match |
|---|---|---|---|---|
| margin | Obs | 1,390 | 1,390 | Yes |
| margin | Mean | 7.171159 | 7.171159 | Yes |
| margin | SD | 34.32488 | 34.32488 | Yes |
| margin | Min / Max | -100 / 100 | -100 / 100 | Yes |
| class | Obs | 1,390 | 1,390 | Yes |
| class | Mean | 2.023022 | 2.023022 (raw 2.0230216) | Yes |
| class | SD | 0.8231983 | 0.8231983 | Yes |
| class | Min / Max | 1 / 3 | 1 / 3 | Yes |
| termshouse | Obs | 1,108 | 1,108 | Yes |
| termshouse | Mean / SD | 1.436823 / 2.357133 | 1.436823 / 2.357133 | Yes |
| termshouse | Min / Max | 0 / 16 | 0 / 16 | Yes |
| termssenate | Obs | 1,108 | 1,108 | Yes |
| termssenate | Mean / SD | 4.555957 / 3.720294 | 4.555957 / 3.720294 | Yes |
| termssenate | Min / Max | 1 / 20 | 1 / 20 | Yes |
| population | Obs | 1,390 | 1,390 | Yes |
| population | Mean / SD | 3,827,919 / 4,436,950 | 3,827,919 / 4,436,950 | Yes |
| population | Min / Max | 78,000 / 3.73e+07 | 78,000 / 37,253,956 | Yes |

The 1,108 observations for `termshouse` and `termssenate` are the rows with non-missing
values, which matches the 282 missing rows recorded above.

### Counts printed elsewhere in Sec. 7.2 (non-missing outcome, counts only)

| Statistic | Printed | File | Match |
|---|---|---|---|
| Non-missing `vote` (N), p. 390 | 1,297 | 1,297 | Yes |
| N left of cutoff, p. 391 and p. 392 | 595 | 595 | Yes |
| N right of cutoff, p. 391 and p. 392 | 702 | 702 | Yes |
| Closest negative `margin` to 0, rdbwselect output, p. 400 | -0.079 | -0.0789 | Yes |
| Closest non-negative `margin` to 0, rdbwselect output, p. 400 | 0.036 | 0.0357 | Yes |

The p. 400 minimum and maximum (-100 and 100 on the two sides) also match.

### Result

No discrepancy found in any compared statistic. The file matches CCFT (2017) Sec. 7.2's printed
non-outcome moments (margin, class, termshouse, termssenate, population), counts (N per side, and
the non-missing outcome N) and bounds. Vote's moments were not compared, so identity with the
.dta used by CCFT is supported but not established. H1 (the first outcome check, against the
printed conventional estimate and CI) is where that identity is tested.


## Design-stage MDE values (run design-mde)

Run `design-mde` (`code/design_mde.py`, metrics in `runs/design-mde/metrics.json`, 2026-11-20).
It uses only `margin` and the four predetermined covariates; `vote` is never loaded.
Multiplier (z_0.975 + z_0.80) = 2.8016.

- H2(a) density test (rddensity, N = 1,390): MDE 0.01136 in density-difference units, about 0.52 of the left-side density (0.02169).
- H2(b) covariate tests: class MDE 0.401 (N 1,390); termshouse 1.400 (N 1,108); termssenate 2.091 (N 1,108); population 2,185,253 persons (N 1,390).
- H2(c) placebo: report-only, with no equivalence bound and no MDE; its precision is the CI width (estimate and CI reported for each one-sided placebo cutoff).
- Disclosure: the run also records the margin-only rddensity robust test (T_Q -0.875, p 0.381), computed before the design gate.
