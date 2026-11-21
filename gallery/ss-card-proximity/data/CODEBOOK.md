# Data codebook: ss-card-proximity

Prepared by the Data RA on 2026-11-21, before the design gate: data preparation only. No
statistic relating the instrument (`nearc4`) to education or wages has been computed, and
`read1.lst` (the SAS output of Card's example program, which holds regression output) was
neither extracted nor opened. Every number below comes from `data/fetch_metrics.json` or
`data/prepare_metrics.json` (runs `fetch-data` and `prepare-data`) unless a published
source is named.

## Source

| Item | Value |
|---|---|
| Archive | `https://davidcard.berkeley.edu/data_sets/proximity.zip`, 134,563 bytes, SHA-256 `0e9b2ad4182ea631ca3dd8a5fff6c1b0ab86b56c6a3fa868870f716e8d82691f` (server Last-Modified 27 Jul 2007; members dated 2002-05-30) |
| Retrieved | 2026-11-21 by `code/fetch_data.py` (run `fetch-data`). No checksum is published; the script pins the hash the Scout observed on 2026-11-20 and the member list, so a rerun gets the same bytes or fails |
| Members | `nls.dat` (3,613 rows x 52 variables), `code_bk.txt` (codebook), `read1.sas` (Card's example SAS program), `readme`; `read1.lst` left in the zip, unopened |
| Terms | None stated; posted publicly by the author for research use (see `data/manifest.json`). Raw and derived files are git-ignored and rebuilt by the runs |
| Population | Men in the 1976 cross-section of the National Longitudinal Survey of Young Men (original cohort aged 14-24 in 1966), interviewed in 1976 with valid education (`code_bk.txt`; Card WP 4483, Table 1 col. 2) |
| Citation note | `code_bk.txt` cites "NBER Working Paper 4832, August 1994". The proximity paper is NBER WP 4483 (1993); see `sources/notes.md` sec. 0 |
| Derived file | `data/derived/card_analysis.csv`, 3,010 rows x 63 columns, made by `code/prepare_data.py` (run `prepare-data`); SHA-256 in `data/manifest.json` |

## Parsing and checks against the codebook

- `nls.dat` is read at the column positions printed in `code_bk.txt`. `read1.sas` reads it
  instead with SAS list input (whitespace-separated, `.` = missing). Both readings were
  applied: every row has exactly 52 tokens and the two readings agree on all 3,613 rows
  (`fixed_vs_list_parse_mismatched_rows` = 0). `id` is unique.
- **Codebook statistics reproduced.** For all 52 variables, N, mean, standard deviation
  (n - 1), minimum and maximum on the 3,613 rows equal the values printed in `code_bk.txt`
  at the printed precision (260 of 260 statistics; the largest difference is 0.98 of half a
  unit in the last printed digit, for `id`, whose mean and s.d. are printed to 2 decimals).
- Missing values (`.`) become empty cells in the CSV. Raw values are written exactly as
  they appear in `nls.dat`; nothing is recoded.

## Sample

Rule (plan.json task `dr-prepare`; `sources/notes.md` sec. 1): keep rows with a
non-missing `lwage76`. Unweighted (`weight` is carried along, not applied). `lwage76` is
Card's already-trimmed log wage and is not re-trimmed.

| Step | Rows |
|---|---|
| `nls.dat` | 3,613 |
| Dropped: `lwage76` missing | 603 |
| **Kept (analysis file)** | **3,010** |

- Of the 603 dropped rows, 596 have no `wage76` and 7 have a `wage76` below 100 cents
  (under $1/hour); none of the dropped rows has a wage above 3,000 cents. So
  `wage76` has 3,017 non-missing values and `lwage76` 3,010, as the codebook says, and the
  difference is the $1 lower trim of Kling's (2001) stated rule ($1-$30; the largest
  `wage76` in the file is 2,404 cents, so the $30 cap binds on no one).
- In every kept row `lwage76` = ln(`wage76`) to 1e-6 (wage in cents), and no kept row lacks
  `wage76`.
- Kept rows have no missing value in any variable of Card's specifications (`lwage76`,
  `ed76`, `nearc4`, `age76`, `black`, `smsa76r`, `reg76r`, `smsa66r`, `reg662`-`reg669`,
  `daded`, `momed`, `nodaded`, `nomomed`, `famed`, `momdad14`, `sinmom14`).
- N = 3,010 equals Card's N (Tables 1-3) and the codebook's N for `lwage76`.

## Variables used in Card's specifications

Units and definitions from `code_bk.txt` and `read1.sas`. Means are over the 3,010 kept
rows (`prepare_metrics.json`, `sample_*`), univariate only.

| Variable | Definition | Units | Role | Mean in sample |
|---|---|---|---|---|
| `lwage76` | Log hourly wage, 1976, "outliers trimmed" (= ln of `wage76` in cents) | log cents/hour | Outcome | 6.2618 (s.d. 0.4438) |
| `ed76` | Completed education in 1976 | years (1-18 in sample) | Endogenous regressor | 13.2635 (s.d. 2.6769) |
| `nearc4` | Grew up near (in the local labour market of) an accredited 4-year college, 1966 | 0/1 | Instrument | 0.6821 |
| `exp76` | **Constructed**: `age76 - ed76 - 6` (potential experience) | years (0-23; none negative) | Control (Panel A) / endogenous (Panel B) | 8.8561 (s.d. 4.1417) |
| `exp762` | **Constructed**: `exp76^2`. Card's Table 2 prints the coefficient on `exp762/100` | years squared | as `exp76` | 95.5791 |
| `age76` | Age in 1976 | years (24-34) | Instrument for experience in Panel B | 28.1196 |
| `age762` | **Constructed**: `age76^2` (Card Table 3 note b: "age and age squared") | years squared | Instrument for `exp762` in Panel B | |
| `black` | 1 if black | 0/1 | Base control | 0.2336 |
| `smsa76r` | Lived in an SMSA in 1976 | 0/1 | Base control | 0.7130 |
| `reg76r` | Lived in the South in 1976 | 0/1 | Base control | 0.4037 |
| `smsa66r` | Lived in an SMSA in 1966 | 0/1 | Base control | 0.6495 |
| `reg661`-`reg669` | Region of residence in 1966, regions 1-9 (one dummy each; exactly one equals 1 in every row). `read1.sas` enters `reg662`-`reg669` (region 1 omitted) = Card's "8 indicators" | 0/1 | Base controls | 0.0465, 0.1608, 0.1957, 0.0641, 0.2083, 0.0960, 0.1100, 0.0282, 0.0904 |
| `daded` | Father's education; missing replaced by the overall mean ("missing=avg") | years | Family background | 9.9889 |
| `nodaded` | 1 if father's education imputed | 0/1 | Family background | 0.2292 |
| `momed` | Mother's education; missing replaced by the mean | years | Family background | 10.3366 |
| `nomomed` | 1 if mother's education imputed | 0/1 | Family background | 0.1173 |
| `famed` | Mother-father education class, 1-9 (raw; used to build `f1`-`f8`) | category | source of `f1`-`f8` | shares 1-9: .0615 .0787 .1249 .0475 .0791 .1329 .0505 .2203 .2047 |
| `f1`-`f8` | **Constructed**: `fk = 1{famed = k}`, k = 1..8; `famed = 9` omitted (616 men). `read1.sas` labels: f1 mom and dad both > 12 yrs; f2 mom & dad >= 12 and not both exactly 12; f3 mom = dad = 12; f4 mom >= 12 and dad missing; f5 father >= 12 and mom not in f1-f4; f6 mom >= 12 and dad nonmissing; f7 mom and dad both >= 9; f8 mom and dad both nonmissing. The labels are Card's and are terse; the classes are mutually exclusive and applied in order | 0/1 | Family background | as `famed` shares |
| `momdad14` | Lived with mother and father at age 14 | 0/1 | Family background | 0.7894 |
| `sinmom14` | Lived with single mother at age 14 | 0/1 | Family background | 0.1007 |

- **Base controls** (Card Table 3 note; `read1.sas` third model): `black smsa76r reg76r
  smsa66r reg662-reg669 exp76 exp762`: 14 variables (4 + 8 region dummies + 2 experience
  terms), or 15 columns with the intercept (`plan.json` design.method `BASE_A`).
- **Family background** (14 variables, Card Table 3 note a; `read1.sas` fourth model):
  `daded momed nodaded nomomed f1-f8 momdad14 sinmom14` (2 + 2 + 8 + 2; design.method `FB`).
- **Panel B** (experience endogenous): `exp76 exp762` move to the endogenous list, leaving
  12 exogenous base controls, or 13 columns with the intercept (design.method `BASE_B`);
  excluded instruments `nearc4 age76 age762` (3).

## Other variables in the analysis file (not in Card's specifications)

Carried unchanged from `nls.dat` for possible robustness work; definitions from
`code_bk.txt`. Units: 0/1 indicators unless stated.

| Variable | Definition |
|---|---|
| `id` | Sequential NLSYM id, 1-5225 (key) |
| `nearc2` | Grew up near a 2-year college |
| `nearc4a`, `nearc4b` | Grew up near a 4-year public / private college |
| `ed66` | Education in 1966, years |
| `weight` | NLS sampling weight for the 1976 cross-section (not applied) |
| `step14` | Lived with a step-parent at age 14 |
| `south66` | Lived in the South in 1966 |
| `work76`, `work78` | Worked in 1976 / 1978 |
| `lwage78` | Log wage 1978, outliers trimmed (log cents/hour) |
| `smsa78r`, `reg78r`, `reg80r` | In an SMSA in 1978; in the South in 1978 / 1980 |
| `wage76`, `wage78`, `wage80` | Raw wage, cents per hour |
| `noint78`, `noint80` | Not interviewed in 1978 / 1980 |
| `enroll76`, `enroll78`, `enroll80` | Enrolled in school |
| `kww` | Knowledge of the World of Work test score (2,963 non-missing in sample) |
| `iq` | Normed IQ score (2,061 non-missing in sample) |
| `marsta76`, `marsta78`, `marsta80` | Marital status (1 = married, spouse present; codes 1-6) |
| `libcrd14` | Library card in the home at age 14 |

## Comparison with what Card prints

Card (1993, NBER WP 4483), Table 1 (PDF p. 33), read by the Data RA from the page image of
the NBER scan (`https://www.nber.org/system/files/working_papers/w4483/w4483.pdf`, fetched
2026-11-21), column 2 (interviewed 1976, valid education, N = 3,613) and column 3 (valid
wage and education, N = 3,010); and the dependent-variable and education means in the
notes to Tables 2 and 3 (`sources/notes.md` sec. 1). A row matches if our value rounds to
Card's at his printed precision (|difference| <= 0.05 for one decimal). Regions in 1966 are
grouped as Northeast = regions 1-2, Midwest = 3-4, South = 5-7, West = 8-9: the codebook
does not name the nine regions, and this grouping (the order of the nine Census divisions)
is an inference from the fact that it reproduces Card's column 2 to rounding, and that
`reg665` + `reg666` + `reg667` equals `south66` (lived in the South in 1966) in all 3,613
rows (`all_reg665_to_667_ne_south66` = 0).

| Table 1 row | Card col. 2 (3,613) | Ours | Card col. 3 (3,010) | Ours | Match |
|---|---|---|---|---|---|
| Age in 1966 14-15 (%) | 25.3 | 25.30 | 25.5 | 25.48 | yes / yes |
| Age 16-17 | 23.8 | 23.83 | 24.1 | 24.09 | yes / yes |
| Age 18-20 | 24.1 | 24.14 | 24.6 | **24.65** (742 men) | yes / **no** (rounds to 24.7) |
| Age 21-24 | 26.7 | 26.74 | 25.8 | 25.78 | yes / yes |
| Northeast 1966 (%) | 20.0 | 19.96 | 20.7 | 20.73 | yes / yes |
| Midwest | 26.3 | 26.32 | 26.0 | 25.98 | yes / yes |
| South | 41.3 | 41.27 | 41.4 | 41.43 | yes / yes |
| West | 12.5 | 12.46 | 11.9 | 11.86 | yes / yes |
| Lived in SMSA 1966 (%) | 64.3 | 64.27 | 65.0 | 64.95 | yes / yes |
| Near 4-year college 1966 (%) | 67.8 | 67.81 | 68.2 | 68.21 | yes / yes |
| Mother & father at 14 (%) | 79.2 | 79.21 | 78.9 | 78.94 | yes / yes |
| Mother only at 14 (%) | 10.0 | 10.02 | 10.1 | 10.07 | yes / yes |
| Mother's education (yrs), non-imputed | 10.4 | 10.35 | 10.3 | 10.35 | yes / yes |
| Father's education (yrs), non-imputed | 10.0 | 10.02 | 10.0 | 10.00 | yes / yes |
| Black (%) | 23.0 | 23.00 | 23.0 | **23.36** (703 men) | yes / **no** |
| KWW score (available obs.) | 33.5 | 33.49 (N 3,543) | 33.5 | 33.54 (N 2,963) | yes / yes |
| Education in 1976 (yrs) | 13.2 | 13.23 | 13.3 | 13.26 | yes / yes |
| Live in South 1976 (%) | 40.0 | 39.97 | 40.3 | **40.37** (1,215 men) | yes / **no** (rounds to 40.4) |
| Sample size | 3,613 | 3,613 | 3,010 | 3,010 | yes / yes |

| Table note (N = 3,010) | Card | Ours | Match |
|---|---|---|---|
| Log hourly wage, mean (s.d.) (Table 2 note) | 6.262 (0.444) | 6.2618 (0.4438) | yes |
| Years of education, mean (s.d.) (Table 3 note) | 13.263 (2.677) | 13.2635 (2.6769) | yes |

**Discrepancies, stated plainly.** All 18 Table 1 rows of column 2 match. In column 3,
15 of 18 rows match and three do not: age 18-20 in 1966 (24.65 vs 24.6; 742 men),
live in South 1976 (40.37 vs 40.3; 1,215 men) and per cent black (23.36 vs 23.0, i.e. 703
men where 23.0% would be about 692). The first two are each one man from the published
rounding: 741 men would give 24.62 and 1,214 men 40.33, both rounding to Card's figures.
The cause of the black-share difference is unknown. That column 3 repeats column 2's 23.0
exactly is consistent with a transcription error in Card's Table 1, but that is a
conjecture, not an established explanation. The sample itself is not in doubt: N, the
mean and s.d. of log wage and of education match Card's table notes to three decimals,
and the same 3,010 rows are the codebook's non-missing `lwage76`. None of these is
adjusted; they do not affect the sample or any variable the specifications use.

The column 3 values are also recomputed and asserted equal by the analysis run
`describe-sample` (deviation D7, added at the paper stage after the results gate), whose
metrics back the result claims `t1-*` in `claims.jsonl`.

Card prints no mean of experience; ours is 8.86 years (s.d. 4.14) in the sample.

## Variables that could not be built as described

None. Every variable of Card's base controls, family background, experience terms and
Panel B instruments is either in `nls.dat` or constructed exactly as in `read1.sas`. Two
points for the Econometrician:

- **Parental education** is the file's mean-imputed version; the imputation was done by
  Card before release and cannot be redone (raw parental education is not in the file).
  The codebook says "missing=avg" without saying over which sample the average was taken.
- **Sample-exclusion detail.** Kling (2001) reports that Card also excluded 49 men with a
  missing 1966 interview month. The file has no interview-month variable, so this cannot
  be verified directly; the match of N = 3,010 and of the log-wage and education moments
  indicates the released file already reflects it.
