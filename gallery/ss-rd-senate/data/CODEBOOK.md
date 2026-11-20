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

Not checked: the source's printed summary statistics (means, SDs) and the 8-covariate
list in CFT (2015). The summary statistics were not compared here, because the brief
bars any statistic of `vote` before the design gate.

Discrepancies: none found in the checks above. The covariate missingness (282 rows for
`termshouse` and `termssenate`) was not compared with any source, because the source's
missing-value counts were not checked.

## Restrictions not applied

No restriction is applied. Any sample restriction (for example, a bandwidth window or a
requirement of non-missing covariates) follows the approved design and will be applied
in a later data-prep run.
