# Codebook: 1991 SIPP 401(k) extract (`sipp1991`)

Written by the Data RA on 2026-11-18. Files and runs:

| File | Made by | Rows x cols | sha256 |
|---|---|---|---|
| `data/raw/sipp1991.dta` (git-ignored) | `code/fetch_sipp.py`, run `fetch-sipp` | 9,915 x 14 | `1123d5f0abf6adae1d8e200f756d2a22b0ce0ce30cb228e69342a0098e57b4b2` |
| `data/derived/sipp1991.csv` | `code/prepare_sipp.py`, run `prepare-sipp` | 9,915 x 11 | `4c73b63b77217460e25c2847ebcdb9a2a3273630758c6172879e62dddb8f4916` |

Counts are in `data/prepare_metrics.json`; per-variable summary statistics are in
`data/derived/sipp1991_summary.json`. Provenance and terms are in `data/manifest.json`.

## Sources used for definitions

- **[F] File labels.** Stata variable labels stored in `sipp1991.dta` itself (file
  timestamp 2013-06-20).
- **[R] Authors' code.** Header comment of `401K.R` in VC2015/DMLonGitHub `[dmlongithub]`,
  read 2026-11-18: "Data source: SIPP 1991 (Abadie, 2003)"; "the sample selection and
  variable contruction follow Abadie (2003)".
- **[C] Chernozhukov et al. (2018), Sec. 6.2** `[chernozhukov2018dml]`, as transcribed in
  `sources/notes.md` §1 (outcome definition, treatment, list of nine controls).
- **[B] Belloni et al. (2017), Sec. 7** `[belloni2017]`, arXiv:1311.2645v8 full text, read
  2026-11-18: "We use the same data as Chernozhukov and Hansen (2004). The data consist of
  9,915 observations at the household level drawn from the 1991 SIPP."
- **[A] Abadie, NBER Technical Working Paper 260 (2000)**, the working-paper version of
  `[abadie2003]`, full text read 2026-11-18 (the journal version was not read). Sec. on the
  401(k) application and Table I: "The data consist of 9,275 observations from the Survey
  of Income and Program Participation (SIPP) of 1991. These data were prepared for
  Poterba, Venti and Wise (1996). The observational units are household reference persons
  aged 25-64 and spouse if present. The sample is restricted to families with at least one
  member employed and where no member has income from self-employment. [...] here family
  income is required to fall in the $10,000-$200,000 interval."
- Chernozhukov & Hansen (2004) `[chernozhukov2004]` is named by [C] and [B] as the data's
  source, but its full text is paywalled and was **not read**. No definition below relies
  on it.

## Variables kept in `data/derived/sipp1991.csv`

Units: money variables are in US dollars as recorded in the file (nominal, survey year).
None of the sources read states the reference period (for example annual) of `inc`.

| Variable | Role | Definition | Units / coding | Source |
|---|---|---|---|---|
| `net_tfa` | Outcome Y | Net total financial assets: IRA balances + 401(k) balances + checking accounts + U.S. saving bonds + other interest-earning accounts + other interest-earning assets + stocks + mutual funds, minus non-mortgage debt | US dollars; can be negative | [F] "Net total financial assets"; [R]; components from [C]; [A] "Family Net Financial Assets (in $)" |
| `e401` | Treatment D | Eligible to enroll in a 401(k) plan (employer offers a 401(k)) | 0/1 | [F] "401(k) eligibility"; [R] "= 1 if employer offers 401(k)"; [C]; [B] |
| `age` | Control | Age of the head of the household (reference person in [A]) | Years, integer, 25-64 | [F]; [A] |
| `inc` | Control | Household (family) income | US dollars | [F] "Household income"; [R] "income"; [A] "Family Income" |
| `educ` | Control | Years of education of the head of the household | Years, integer | [F]; [R] "years of education" |
| `fsize` | Control | Household (family) size | Persons, integer | [F] "Household size"; [R] "family size" |
| `marr` | Control | Married | 0/1 | [F] "Married indicator"; [R] "= 1 if married" |
| `twoearn` | Control | Two-earner household | 0/1 | [F] "Two-earner status indicator"; [R] |
| `db` | Control | Has a defined-benefit pension | 0/1 | [F] "Defined benefit pension status indicator"; [R] |
| `pira` | Control | Participates in an IRA | 0/1 | [F] "IRA participation indicator"; [R] |
| `hown` | Control | Owns home | 0/1 | [F] "House ownership indicator"; [R] "= 1 if home owner" |

Columns in the raw file **not kept** (not used by the PLR question): `nifa` [F] "Net
non-401(k) financial assets", `tw` [F] "Total wealth", `p401` [F] "401(k) participation"
(the treatment of the LATE in [C], not part of this study).

## Summary statistics (all 9,915 rows, each variable on its own)

From `data/derived/sipp1991_summary.json`. No statistic is computed by `e401` or across
`e401` and `net_tfa`.

| Variable | Mean | SD | Min | Median | Max | Distinct |
|---|---|---|---|---|---|---|
| `net_tfa` | 18,051.5 | 63,522.5 | -502,302 | 1,499 | 1,536,798 | 5,168 |
| `e401` | 0.371 | 0.483 | 0 | 0 | 1 | 2 |
| `age` | 41.06 | 10.34 | 25 | 40 | 64 | 40 |
| `inc` | 37,200.6 | 24,774.3 | -2,652 | 31,476 | 242,124 | 7,334 |
| `educ` | 13.21 | 2.81 | 1 | 12 | 18 | 18 |
| `fsize` | 2.866 | 1.539 | 1 | 3 | 13 | 13 |
| `marr` | 0.605 | 0.489 | 0 | 1 | 1 | 2 |
| `twoearn` | 0.381 | 0.486 | 0 | 0 | 1 | 2 |
| `db` | 0.271 | 0.445 | 0 | 0 | 1 | 2 |
| `pira` | 0.242 | 0.428 | 0 | 0 | 1 | 2 |
| `hown` | 0.635 | 0.481 | 0 | 1 | 1 | 2 |

Counts (`data/prepare_metrics.json`): 0 missing values in every column; every 0/1
variable takes only the values 0 and 1; 3,682 rows have `e401` = 1; `net_tfa` is negative
in 2,902 rows and exactly 0 in 783; `inc` is zero or negative in 5 rows; all 9,915 rows
have `age` in 25-64. Rows dropped: 0.

## Comparison with the source

| Check | Source says | File / derived data | Match? |
|---|---|---|---|
| Row count | 9,915 households, 1991 SIPP [B]; also ddml and the DoubleML docs (`sources/notes.md` §2). The 2018 paper [C] does not state N. | 9,915 | Yes (against secondary sources; [C] gives no N) |
| Variable names | `net_tfa`, `e401`, `age inc educ fsize marr twoearn db pira hown` [R] | All 11 present | Yes |
| Nine controls | age, income, family size, years of education, married, two-earner, defined-benefit pension, IRA participation, home ownership [C], [B] | Same nine, matched to the file labels | Yes |
| Age range | Reference persons aged 25-64 [A] | 25-64 in all rows | Yes |
| Sample rules of Abadie (2003), which [R] says the sample follows | 9,275 rows; family income in $10,000-$200,000 [A] | 9,915 rows; exactly **9,275** rows have `inc` in [10,000, 200,000] | **No as a whole file; yes for the income-band subset** (see below) |
| Abadie Table I, "Entire Sample" column (mean (SD)) [A] | Net financial assets 19,071.68 (63,963.84); eligibility 0.39 (0.49); IRA participation 0.25 (0.44); family income 39,254.64 (24,090.00); age 41.08 (10.30); married 0.63 (0.48); family size 2.89 (1.53) | Within the 9,275-row income band: `net_tfa` 19,071.68 (63,963.84); `e401` 0.392 (0.488); `pira` 0.254 (0.436); `inc` 39,254.64 (24,090.00); `age` 41.08 (10.30); `marr` 0.629 (0.483); `fsize` 2.885 (1.526) | Yes, every value equal at the published precision |

## Discrepancies, stated plainly

1. **The file is not Abadie's (2003) sample.** The authors' code [R] says the sample
   selection follows Abadie (2003), whose sample has 9,275 rows with family income in
   $10,000-$200,000 [A]. The file has 9,915 rows. The 640 extra rows are exactly those
   outside Abadie's income band (including 5 rows with zero or negative income, minimum
   -$2,652, and a maximum income of $242,124). Inside the band the file reproduces
   Abadie's Table I entire-sample means and SDs exactly, so the file appears to be
   Abadie's extract **before** his income restriction. The 9,915-row count matches [B],
   which says it is the Chernozhukov & Hansen (2004) sample. As instructed, **no income
   restriction is applied** in the derived file; the design should state that the 2018
   replication uses all 9,915 rows (the authors' code does not subset).
2. **N is not in the 2018 paper.** 9,915 is confirmed only by secondary sources ([B],
   ddml, DoubleML docs), as already noted in `sources/notes.md`.
3. **Survey wave wording.** [A], [B], [C] and [R] all say "1991 SIPP". One later paper
   (arXiv:2411.08778, not in `refs.bib`, not verified against a primary source) describes
   the same 9,915-row data as "Wave 4 of the 1990 Survey of Income and Program
   Participation". The two descriptions may refer to the same interviews (a 1990-panel
   wave fielded in 1991), but no source read here says so. Use "the 1991 SIPP extract"
   in the paper unless the Scout verifies more.
4. **Household vs family; head vs reference person.** The file labels say "household" and
   "head of the household"; [A] says "family" and "household reference persons ... and
   spouse if present". These are labels, not a data difference; the codebook uses the
   file labels.
5. **Low education values.** `educ` ranges from 1 to 18 years (1st percentile 4). The
   low values are in the source file and are kept; no source read explains the coding
   (for example top-coding at 18 is not documented).
6. **Units and period.** No source read states whether `inc` is annual or the dollar
   year; they are recorded as US dollars as in the file.
7. **Reference not read.** Chernozhukov & Hansen (2004), which [B] and [C] name as the
   data's source, was not read (paywalled); its own description of N, wave and variable
   construction was not checked.

## Terms of use

No data license is stated by the source. The hosting repository's `LICENSE.Rmd` is an
MIT-style notice (copyright 2017, the six DML authors) for "this software and associated
documentation files"; it does not name the data file, and GitHub reports the license as
"Other" (NOASSERTION). The underlying survey is the public-use SIPP of the U.S. Census
Bureau. The file is distributed by its authors as replication material and is also
loaded by the MIT-licensed DoubleML package (`fetch_401K`); research use is consistent
with that, but redistribution rights for the data are not explicitly granted.
