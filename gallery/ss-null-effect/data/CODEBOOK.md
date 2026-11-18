# Codebook: ss-null-effect extract

Source: `data/raw/null_extract.csv`, a byte-for-byte copy of
`crew/bench/seeds/ss-null-effect/data.csv` (synthetic, CC0-1.0; SHA-256
`f09fba86…048ca9`, matching `task.json`). See `data/manifest.json`.

The task brief describes the file as "an administrative extract for 4,000 working-age
adults, of whom about 40% enrolled in a voluntary job-training program in 1976-77.
Enrolment was not randomized." The brief gives no units beyond the variable names and
no price year; earnings are in the file's nominal units. Definitions below are taken
from the brief; where the brief only names a variable, the definition says so, and
anything added from inspecting the covariates is marked *observed*.

## Identifier and treatment

| Variable | Definition | Type / range (observed) |
|---|---|---|
| `id` | Person identifier | integer, unique, 1 row per person |
| `treat` | Enrolment indicator: 1 = enrolled in the voluntary 1976-77 job-training program. The brief says people "enrolled"; nothing in the brief says whether it records completion. This is the treatment of the ATT in `plan.json` (round-1 question review, F5). | 0/1 |

## Pre-program covariates (the eleven in `plan.json`)

| Variable | Definition (brief: "pre-program characteristics") | Type / range (observed) |
|---|---|---|
| `age` | Age (years) | integer, 18-55 |
| `educ` | Education (years of schooling, presumed; the brief only names it) | integer, 3-18 |
| `married` | Married indicator | 0/1 |
| `urban` | Urban residence indicator | 0/1 |
| `region` | Region of residence | categorical: midwest, northeast, south, west |
| `children` | Number of children | integer, 0-7 |
| `health_limit` | Health-limitation indicator | 0/1 |
| `re74` | Earnings in 1974 (nominal; brief: "earnings re74 and re75") | float, 0-27,864 |
| `re75` | Earnings in 1975 (nominal) | float, 0-27,807 |
| `unemp74` | Unemployment indicator, 1974 | 0/1; *observed*: equals 1 exactly when `re74` = 0 (0 rows differ) |
| `unemp75` | Unemployment indicator, 1975 | 0/1; *observed*: equals 1 exactly when `re75` = 0 (0 rows differ) |

No missing values in `id`, `treat` or any covariate.

## Checks against the source (runs `fetch-data`, `prepare-covariates`)

| Check | Source says | Found | Match |
|---|---|---|---|
| SHA-256 | `task.json`: f09fba86…048ca9 | same | yes |
| Rows | brief: 4,000 adults | 4,000 | yes |
| Share enrolled | brief: "about 40%" | 1,621 / 4,000 = 40.5% | yes |
| Columns | brief: id/treatment not listed; 11 covariates, 6 outcomes, 20 survey items | 39 = id + `treat` + 11 + 6 + 20; no unexpected or missing names | yes |

Not stated by the brief, and worth knowing: `unemp74` and `unemp75` are exactly the
zero-earnings indicators of `re74` and `re75`, so they add no information beyond the
earnings levels except the zero/non-zero split.

## Covariate balance (run `prepare-covariates`, `data/derived/prep_metrics.json`)

Standardized difference = (mean treated - mean control) / sqrt((var_t + var_c) / 2).

| Variable | Mean, treated (n = 1,621) | Mean, control (n = 2,379) | Std. diff. |
|---|---|---|---|
| age | 34.47 | 37.82 | -0.311 |
| educ | 11.12 | 11.74 | -0.251 |
| married | 0.339 | 0.377 | -0.078 |
| urban | 0.580 | 0.614 | -0.070 |
| children | 1.115 | 1.093 | 0.021 |
| health_limit | 0.144 | 0.113 | 0.095 |
| re74 | 6,712.7 | 8,884.6 | -0.382 |
| re75 | 4,834.7 | 9,645.3 | **-0.891** |
| unemp74 | 0.245 | 0.171 | 0.183 |
| unemp75 | 0.403 | 0.111 | 0.707 |
| region = midwest / northeast / south / west | 0.192 / 0.194 / 0.405 / 0.209 | 0.190 / 0.197 / 0.406 / 0.208 | all within ±0.01 |

Enrolees' mean earnings fall from 6,713 in 1974 to 4,835 in 1975 (40% had zero 1975
earnings), while non-enrolees' rise from 8,885 to 9,645: a pre-program dip among
enrolees. SDs for every row are in the metrics file.

## H1b margin and precision proxy (run `margin`, `data/derived/margin_metrics.json`)

Computed from `treat` and `re75` only, before the design gate:

- M = 0.10 × mean(re75 | treat = 1) = 0.10 × 4,834.70 = **483.47**
- Precision proxy = sqrt(var_t(re75)/n_t + var_c(re75)/n_c) = **172.59**
  (sample variances; the SE a difference in means would have if the outcome had
  re75's variance in each group). M / proxy = 2.80; the 90% half-width at that SE is
  283.9, so H1b would be testable at that precision.
- M rests on enrolees' 1975 earnings, which are depressed by the dip above
  (enrolees' 1974 mean is 39% higher), so M is smaller than a margin based on 1974
  earnings would be. This is recorded, not changed: H1b fixes M on re75.

## Sealed outcome columns (names only; not read, not summarized)

Primary: `re78`. Secondary family: `re79`, `employed78`, `hours78`, `benefits78`,
`wellbeing78`. Not analysed (plan.json `outcomes.not_analysed`): `survey_q01`,
`survey_q02`, `survey_q03`, `survey_q04`, `survey_q05`, `survey_q06`, `survey_q07`,
`survey_q08`, `survey_q09`, `survey_q10`, `survey_q11`, `survey_q12`, `survey_q13`,
`survey_q14`, `survey_q15`, `survey_q16`, `survey_q17`, `survey_q18`, `survey_q19`,
`survey_q20`.

The brief defines them only as "outcomes measured after the program (re78, re79,
employed78, hours78, benefits78, wellbeing78) and twenty survey items". `code/prepare_covariates.py`
loads only `id`, `treat` and the eleven covariates (`pandas.read_csv(usecols=…)`), and
`code/margin.py` reads only the derived covariate file.

## Missing outcome values (run `missing-counts`, `data/derived/missing_counts.json`)

Missingness only, read as text; no outcome value was summarized. For each of re78, re79,
employed78, hours78, benefits78 and wellbeing78: 0 of 1,621 treated and 0 of 2,379
controls are missing (share difference 0), and 0 non-missing entries are non-numeric.
The rob-ipow trigger (|difference| > 0.02) does not fire for any outcome.
