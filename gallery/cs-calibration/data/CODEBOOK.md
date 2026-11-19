# Codebook: cs-calibration data

Data RA, 2026-11-19 (UTC). All four datasets were fetched by the data-prep run `fetch-data`
(`code/fetch_data.py`). It calls `sklearn.datasets.fetch_openml` (scikit-learn 1.9.1,
pandas 3.1.1) pinned by `data_id`, with `data_home=data/raw/sklearn_home`. The run checks
the OpenML name, version, file id and md5 it receives, then re-checks the md5 of the cached
ARFF itself. It also checks rows, minority-class size and missing cells against OpenML's
published qualities. Provenance, licences and hashes are in `data/manifest.json`, and the
per-column profile is in `runs/fetch-data/profile.json`. The run was executed twice
(`--replace`), and both runs wrote byte-identical CSVs (same sha256).

Every `data/raw/<name>.csv` has the features in OpenML column order, followed by an integer
`target` column (0/1). Rows are in the order of the OpenML ARFF file. Missing values are
empty cells. No rows or columns were dropped, and nothing was recoded except the target.
The only label statistic computed is the marginal class count of each dataset. No feature
was related to the label, and no model was trained.

## Summary

| Dataset | OpenML id / version / file id | ARFF md5 | CSV sha256 | Rows | Numeric / categorical features | Missing cells (rows) | `target = 1` means | Positive share |
|---|---|---|---|---|---|---|---|---|
| adult | 1590 / v2 / 1595261 | `bb6510925e5d4b23d136715febb2cdf5` | `0626dc27…2dd4b754` | 48,842 | 6 / 8 | 6,465 (3,620 rows, 7.4%) | `class = '>50K'` | 11,687 / 48,842 = 0.2393 |
| bank-marketing | 1461 / v1 / 1586218 | `b29d2eb78e508569fd41172c97bda00e` | `0e933553…51f27f8bc` | 45,211 | 7 / 9 | 0 | `Class = '2'` (subscribed, UCI y = yes) | 5,289 / 45,211 = 0.1170 |
| electricity | 151 / v1 / 2419 | `8ca97867d960ae029ae3a9ac2c923d34` | `a882e1fb…ca4add0ec79a90f70eb05c8b` | 45,312 | 7 / 1 | 0 | `class = 'UP'` | 19,237 / 45,312 = 0.4245 |
| phoneme | 1489 / v1 / 1592281 | `902ff27649dbfb512f3fb01fc05c6b24` | `4f8eecda…e7e695fd3e` | 5,404 | 5 / 0 | 0 | `Class = '2'` (oral vowel) | 1,586 / 5,404 = 0.2935 |

`data/manifest.json` holds the full hashes, including the sha256 of each decompressed ARFF.

**Checks against the source.** For every dataset, the row count, minority-class size and
number of missing cells equal OpenML's published qualities (`NumberOfInstances`,
`MinorityClassSize`, `NumberOfMissingValues`, read from `api/v1/json/data/qualities/<id>`
on 2026-11-19). The feature names, types and nominal levels match OpenML's feature list
(`api/v1/json/data/features/<id>`).

**Licences.** OpenML's licence field reads "Public" for all four datasets. For adult and
bank-marketing, the UCI ML Repository pages state CC BY 4.0 (both pages fetched 2026-11-19). The original sources of
electricity (J. Gama's ELEC2 page) and phoneme (ELENA project, KEEL) state no licence.
These two are widely used benchmark data, and we use them for research only.

**Parser.** The run uses `parser='liac-arff'`. scikit-learn 1.9.1's `'pandas'` ARFF parser
fails under pandas 3.1.1 on nominal attributes whose values look like integers
(bank-marketing and phoneme `Class {1,2}`, electricity `day {1..7}`). pandas infers
integer categories, and scikit-learn's quote stripping then raises `TypeError`. With
LIAC-ARFF, every numeric column arrives as float64, so integer-valued columns such as
adult `age` are written as `25.0`. Their values are unchanged.

## adult (OpenML 1590, v2)

These are UCI Adult records (1994 US Census extract, Kohavi 1996), with the UCI training
and test files merged. The OpenML labels are exactly `<=50K` and `>50K`, so the trailing
period of the UCI test file is not present. Coding: `target = 1` if `class == '>50K'`.

| Column | Type | Missing | Notes |
|---|---|---|---|
| age | numeric (integer-valued) | 0 | 17–90 |
| workclass | categorical, 8 levels | 2,799 | UCI `?` arrives as missing |
| fnlwgt | numeric (integer-valued) | 0 | CPS sampling weight, 12,285–1,490,400 |
| education | categorical, 16 levels | 0 | |
| education-num | numeric (integer-valued) | 0 | 1–16; a numeric coding of `education` |
| marital-status | categorical, 7 levels | 0 | |
| occupation | categorical, 14 levels | 2,809 | UCI `?` arrives as missing |
| relationship | categorical, 6 levels | 0 | |
| race | categorical, 5 levels | 0 | |
| sex | categorical, 2 levels | 0 | |
| capital-gain | numeric (integer-valued) | 0 | 0–99,999 (99,999 is a top code) |
| capital-loss | numeric (integer-valued) | 0 | 0–4,356 |
| hours-per-week | numeric (integer-valued) | 0 | 1–99 |
| native-country | categorical, 41 levels | 857 | UCI `?` arrives as missing |
| target | 0/1 | 0 | 1 = `>50K` |

## bank-marketing (OpenML 1461, v1)

This is the UCI Bank Marketing data (`bank-full`, 45,211 calls; Moro et al. 2011).
OpenML renames the attributes to V1–V16. The names below come from the attribute list in
the OpenML description, and the levels and ranges match it. Coding: `target = 1` if
`Class == '2'`. The OpenML description lists the output as `y` (yes/no) and does not state
the 1/2 mapping. We infer it from the class sizes: label `2` has 5,289 rows (11.7%), which
matches the known share of "yes" in `bank-full`.

| Column | UCI name | Type | Notes |
|---|---|---|---|
| V1 | age | numeric (integer-valued) | 18–95 |
| V2 | job | categorical, 12 levels | includes an `unknown` level |
| V3 | marital | categorical, 3 levels | |
| V4 | education | categorical, 4 levels | includes `unknown` |
| V5 | default | categorical, 2 levels | |
| V6 | balance | numeric (integer-valued) | average yearly balance in euros, −8,019 to 102,127 |
| V7 | housing | categorical, 2 levels | |
| V8 | loan | categorical, 2 levels | |
| V9 | contact | categorical, 3 levels | includes `unknown` |
| V10 | day | numeric (integer-valued) | last contact day of month, 1–31 |
| V11 | month | categorical, 12 levels | last contact month |
| V12 | duration | numeric (integer-valued) | last call duration in seconds, 0–4,918 |
| V13 | campaign | numeric (integer-valued) | contacts in this campaign, 1–63 |
| V14 | pdays | numeric (integer-valued) | days since previous campaign contact; −1 = not contacted |
| V15 | previous | numeric (integer-valued) | contacts before this campaign, 0–275 |
| V16 | poutcome | categorical, 4 levels | includes `unknown` |
| target | | 0/1 | 1 = subscribed a term deposit |

There are no missing cells. `unknown` is a level of four categorical columns, not a
missing value.

## electricity (OpenML 151, v1)

This is ELEC2 from the New South Wales electricity market (Harries 1999), in the version
normalised to [0, 1] by A. Bifet. Coding: `target = 1` if `class == 'UP'`, meaning the NSW
price went up relative to its moving average over the last 24 hours.

| Column | Type | Notes |
|---|---|---|
| date | numeric | normalised date, 0–1; **not monotone in file order** (see below) |
| day | categorical, levels `1`–`7` | day of week |
| period | numeric | half-hour of the day, normalised: 48 values from 0 to 1 in steps of 1/47 |
| nswprice | numeric | NSW price, normalised |
| nswdemand | numeric | NSW demand, normalised |
| vicprice | numeric | Victoria price, normalised; constant over the first 17,424 rows |
| vicdemand | numeric | Victoria demand, normalised; constant over the first 17,424 rows |
| transfer | numeric | scheduled NSW–Victoria transfer, normalised; constant over the first 17,424 rows |
| target | 0/1 | 1 = `UP` |

**Time ordering columns: `date`, `period`, `day`, and the row order itself.** These checks
use features only (`runs/fetch-data/profile.json`, `time_checks`):

- **The file is 944 whole days of 48 rows.** Each 48-row block has one `date` value and one
  `day` value, and `period` rises from 0 to 1 within the block. From one block to the next,
  `day` advances by exactly one (mod 7) with no gaps. The first block has `day = 2`, and
  7 May 1996, the stated start date, was a Tuesday. **The file row order is therefore
  chronological.** `row // 48` gives the day index (0–943), and `row % 48` gives the
  half-hour.
- **The normalised `date` column cannot serve as a time key.** In file order it drops five
  times, each time at a day boundary (rows 25,488, 34,896, 35,232, 36,240 and 40,704). Its
  maximum (1.0) is at row 40,656, and the last row has 0.9158. It takes 933 distinct values
  across 944 days, so 22 day-blocks share a value with another block. The likely cause is
  how the raw date was encoded before normalisation. In any case, anyone who needs time
  order should use the row order, not `date`.
- **Day count.** The OpenML description gives the span as 7 May 1996 to 5 December 1998,
  which is 943 days. The file holds 944 contiguous days (45,312 = 944 × 48 rows, which is
  the instance count OpenML states). That is a one-day discrepancy with the stated end
  date.
- **Constant Victoria columns.** `vicprice`, `vicdemand` and `transfer` are constant over
  the first 17,424 rows, which is 363 days to early May 1997. These look like fill values
  for a period without Victorian data, not measurements.

The plan (item F18) already notes that random splits put neighbouring half-hours on both
sides of a split.

## phoneme (OpenML 1489, v1)

The ELENA / KEEL phoneme data (ROARS project, 1993) has 5 harmonic amplitudes per vowel.
The OpenML description says the patterns are in random order.

| Column | Type | Notes |
|---|---|---|
| V1–V5 | numeric | amplitudes of the first five harmonics AHi/Ene, signed; standardised in this version (each mean ≈ 0, range about −3.0 to 4.6) |
| target | 0/1 | 1 = oral vowel |

Coding: `target = 1` if `Class == '2'`. The OpenML description text says "Class 0: Nasals,
Class 1: Orals", but the ARFF labels are `1` and `2`. We read `2` as oral because label `2`
has 1,586 rows (29.35%) and label `1` has 3,818, which matches the class sizes of the
ELENA phoneme data (3,818 nasal, 1,586 oral).

## Points for the design

- **phoneme is small.** It has 5,404 rows, so the 20,000-row cap does not bind. A
  calibration split of at least 1,000 cases needs a calibration fraction of at least
  1,000 / 5,404 = 18.5% of the full dataset, and more if the fraction applies after a test
  split is taken out.
- **bank-marketing V12 (`duration`)** is known only after the call ends. The UCI page (fetched
  2026-11-19) says it "should be discarded if the intention is to have a realistic
  predictive model". Keeping it or dropping it is a
  design decision. Nothing has been dropped here.
- **adult** has 3,620 rows with missing values in three categorical columns. How they are
  handled (a separate category, imputation or dropping) is a design decision.
- **electricity** row order is time order. Its `date` column is not monotone, and its
  Victoria columns are constant over the first 363 days (see above).
