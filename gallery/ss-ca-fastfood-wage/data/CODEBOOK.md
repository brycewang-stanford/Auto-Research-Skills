# Codebook: QCEW county panel, NAICS 722513 / 722511 / 7225 / 10, 2014Q1-2026Q1

Prepared by the Data RA on 2026-11-21 (task `dr-fetch`). The design gate is not approved:
this file documents data only. It contains counts of rows, counties and suppressed cells; it
contains no statistic of employment or wages that compares areas or periods.

## Source

- **U.S. Bureau of Labor Statistics, Quarterly Census of Employment and Wages (QCEW)**, Open
  Data Access CSV "data slices by industry":
  `https://data.bls.gov/cew/data/api/<year>/<qtr>/industry/<code>.csv`
  (documentation: https://data.bls.gov/cew/doc/access/csv_data_slices.htm).
- Field layout: "QCEW Field Layouts for NAICS-Based, Quarterly CSV Files",
  https://data.bls.gov/cew/doc/layouts/csv_quarterly_layout.htm (checked 2026-11-21).
- Aggregation-level codes: https://data.bls.gov/cew/doc/titles/agglevel/agglevel_titles.csv;
  ownership codes: https://data.bls.gov/cew/doc/titles/ownership/ownership_titles.csv
  (both checked 2026-11-21).
- License: public domain. BLS: "everything that we publish ... is in the public domain"
  (except previously copyrighted photographs and illustrations); cite BLS as the source
  (https://www.bls.gov/opub/copyright-information.htm, checked 2026-11-21).

## Files fetched (run `fetch-data`, `code/fetch_data.py`)

- 4 industries x 49 quarters (2014Q1-2026Q1) = **196 CSV files**, 288,941,864 bytes,
  1,503,889 data rows, in `data/raw/qcew/<year>q<qtr>_<code>.csv` (git-ignored). Each file has
  its own entry in `data/manifest.json` (URL, sha256, size, rows, server Last-Modified, ETag);
  `data/fetch_index.json` holds the same list.
- **Latest quarter available: 2026Q1.** On 2026-11-21 the 2026Q2 URLs returned HTTP 404 for
  all four industries (recorded in `data/fetch_index.json`, `next_quarter_probe`).
- Requests sent a generic User-Agent (`Mozilla/5.0 (compatible; research-data-fetch/1.0)`).
- No checksum is published. The fetch script compares a rerun's bytes with the manifest
  hashes. BLS revises recent quarters: the 2025Q1-2026Q1 files carry Last-Modified
  21 Aug 2026, so a rerun after the 2026Q2 release (and later annual revisions) may fetch
  different bytes for 2025-2026. That would be a new data vintage, not a broken download.

## Row selection (run `prepare-data`, `code/prepare_data.py`)

| Industry | Ownership kept | National / state / county agglvl_code | BLS title of the county level |
|---|---|---|---|
| 722513 limited-service restaurants | 5 Private | 18 / 58 / 78 | County, NAICS 6-digit -- by ownership sector |
| 722511 full-service restaurants | 5 Private | 18 / 58 / 78 | County, NAICS 6-digit -- by ownership sector |
| 7225 restaurants and other eating places | 5 Private | 16 / 56 / 76 | County, NAICS 4-digit -- by ownership sector |
| 10 total, all industries | 0 Total Covered | 10 / 50 / 70 | County, Total Covered |

All files have `size_code` 0 (all sizes). States are the 50 states, DC, Puerto Rico (72) and
the U.S. Virgin Islands (78): 53 state rows per industry-quarter. County rows include each
state's "XX999" unknown/undefined-county record, flagged `area_level = county_unknown`.
The national row (`US000`) covers the 50 states and DC only (see the checks below).

### Rows kept and dropped

Rows read: **1,503,889**. Kept: **640,423**. Dropped: **863,466**.

| Industry | national | state | county | county_unknown | total kept |
|---|---|---|---|---|---|
| 722513 | 49 | 2,597 | 151,126 | 2,314 | 156,086 |
| 722511 | 49 | 2,597 | 154,952 | 2,171 | 159,769 |
| 7225 | 49 | 2,597 | 156,499 | 2,382 | 161,527 |
| 10 | 49 | 2,597 | 157,920 | 2,475 | 163,041 |

Dropped, by reason (exact counts in `data/prepare_metrics.json`, keys `dropped_*`):

- MSA / CSA rows (agglvl 30, 40-48): 18,664 each for 722513, 722511 and 7225; 102,089 for 10.
- Government ownership (own_code 1 federal, 2 state, 3 local) of the restaurant industries:
  722513: 1,904 rows; 722511: 8,465; 7225: 18,169 (national, state and county levels).
- Industry 10, rows other than Total Covered: county by ownership (agglvl 71) 636,952; state
  by ownership (51) 10,339; national by ownership (11) 196; MicroSA (80) 26,518; U.S. summary
  levels (91-96) 2,842.

No area-industry-quarter key is duplicated.

### Counties

Distinct named counties (excluding XX999) that appear at least once: 722513: 3,173;
722511: 3,217; 7225: 3,225; 10: 3,235. Present in all 49 quarters: 722513: 2,983;
722511: 3,072; 7225: 3,152; 10: 3,211. A county-industry row is **absent** (not suppressed)
when the county has no establishment in that industry. Within each year the panel is balanced
(cells = 4 x counties). Across years it is not. For example, in California two small counties
leave the 722513 file: Alpine (06003, last present 2021Q4) and Sierra (06091, last present
2024Q4). California has 58 counties in 722511, 7225 and 10 in every year.

## Variables (`data/derived/qcew_panel.csv`)

| Variable | Type | Definition | Units / values |
|---|---|---|---|
| area_fips | text(5) | QCEW area code: county FIPS (SSCCC), state SS000, unknown county SS999, nation US000 | |
| state_fips | text(2) | First two characters of area_fips; "US" for the national row | |
| area_level | text | national, state, county, county_unknown (derived from agglvl_code and area_fips) | |
| industry | text | QCEW `industry_code`: 722513, 722511, 7225, 10 | NAICS codes |
| own_code | text | Ownership: 5 Private (restaurants), 0 Total Covered (industry 10) | |
| agglvl_code | text | QCEW aggregation level (table above) | |
| year, qtr | int | Reference year and quarter | |
| disclosure_code | text | blank = disclosed; `N` = not disclosed (suppressed); `-` = see below | |
| suppressed | int | 1 if disclosure_code is `N`, else 0 | 0/1 |
| establishments | int | `qtrly_estabs`: count of establishments in the quarter (published even when suppressed) | count |
| month1_emplvl, month2_emplvl, month3_emplvl | float | Employment level in the first, second and third month of the quarter (pay period including the 12th) | jobs; missing if suppressed |
| total_qtrly_wages | float | Total wages paid in the quarter | US dollars, nominal; missing if suppressed |
| avg_wkly_wage | float | Average weekly wage, as published by BLS | US dollars, nominal; missing if suppressed |

Columns of the raw files not kept: size_code, taxable_qtrly_wages, qtrly_contributions, and
all location-quotient (`lq_*`) and over-the-year (`oty_*`) fields.

## Suppression

**Rule.** BLS withholds employment and wages for a cell when publishing them could identify an
employer (confidentiality under its pledge to respondents). Such rows have
`disclosure_code = N`. The raw files still give the establishment count and write 0 for
every employment and wage field. `prepare_data.py` checks that all such values are 0 and sets
them to missing. **These zeros are not zero employment.** The layout documents only blank and
`N`. The files also contain `-` on 993 kept rows (722513: 427, 722511: 355, 7225: 198,
10: 13). Every such row has 0 establishments and 0 in every field. They are kept as reported
(not set to missing). They look like cells with no active establishment in that quarter, but
BLS does not define the code.

Suppressed county-quarter cells (named counties, not XX999), all states. 2026 has one quarter:

| Year | 722513 counties | cells | suppressed | % | 722511 suppressed | % | 7225 suppressed | % | 10 suppressed |
|---|---|---|---|---|---|---|---|---|---|
| 2014 | 3,081 | 12,324 | 2,535 | 20.6 | 3,399 | 26.8 | 3,113 | 24.3 | 0 |
| 2015 | 3,081 | 12,324 | 2,518 | 20.4 | 3,338 | 26.3 | 3,112 | 24.3 | 1 |
| 2016 | 3,073 | 12,292 | 2,535 | 20.6 | 3,342 | 26.4 | 3,086 | 24.2 | 0 |
| 2017 | 3,072 | 12,288 | 2,453 | 20.0 | 3,296 | 26.0 | 3,100 | 24.3 | 0 |
| 2018 | 3,078 | 12,312 | 2,423 | 19.7 | 3,208 | 25.4 | 3,073 | 24.1 | 4 |
| 2019 | 3,084 | 12,336 | 2,381 | 19.3 | 3,178 | 25.1 | 3,072 | 24.1 | 0 |
| 2020 | 3,080 | 12,320 | 2,331 | 18.9 | 3,355 | 26.5 | 3,131 | 24.5 | 0 |
| 2021 | 3,086 | 12,344 | 2,307 | 18.7 | 3,137 | 24.8 | 2,896 | 22.7 | 0 |
| 2022 | 3,093 | 12,372 | 2,372 | 19.2 | 2,963 | 23.5 | 2,908 | 22.8 | 2 |
| 2023 | 3,093 | 12,372 | 2,325 | 18.8 | 2,908 | 23.0 | 2,748 | 21.5 | 1 |
| 2024 | 3,096 | 12,384 | 2,324 | 18.8 | 2,848 | 22.5 | 2,719 | 21.3 | 0 |
| 2025 | 3,094 | 12,376 | 2,584 | 20.9 | 3,296 | 26.1 | 3,748 | 29.4 | 0 |
| 2026Q1 | 3,082 | 3,082 | 640 | 20.8 | 804 | 25.6 | 931 | 29.2 | 0 |

(722511 cells per year: 12,684 to 12,612; 7225: 12,796 to 12,764; 10: 12,888 to 12,896. Exact
numbers are in `data/prepare_metrics.json`, keys `county_cells_*`, `county_suppressed_*`,
`county_n_*`.)

**Suppression rises in 2025, in every state together.** The share of suppressed county cells
rises in 2025Q1 for all three restaurant industries and stays there through 2026Q1. For 7225
it goes from 23.2% (2024Q4) to 29.6% (2025Q1). The rise is broad: from 2024 to 2025 the
count of suppressed county cells rises in 45 of 53 states for 7225 (falls in 2), in 39 for
722513 (falls in 11), and in 31 for 722511 (falls in 16). The files do not say why. It may be
a change in BLS disclosure processing for that vintage; this is not verified. For the
treatment period this means county-level restaurant panels lose more cells after 2024 than
before, and a balanced county panel would be selected partly on post-period disclosure.

Suppression at other levels: no national or state row of 722513 or 722511 is suppressed. Four
state-quarter rows of 7225 are suppressed: one each in Alaska, New Hampshire, Vermont and
Wyoming. For industry 10, 18 rows are suppressed: 8 named-county and 10 unknown-county
cells. XX999 unknown-county rows suppressed: 722513: 799 of 2,314; 722511: 1,007 of 2,171;
7225: 876 of 2,382.

By state and year: `data/derived/suppression_by_state_year.csv` (columns state_fips, industry,
year, county_quarter_cells, suppressed_cells, dash_cells, counties). California (06),
suppressed county-quarter cells / county-quarter cells:

| Year | 722513 | 722511 | 7225 | 10 |
|---|---|---|---|---|
| 2014 | 21 / 232 | 8 / 232 | 15 / 232 | 0 / 232 |
| 2015 | 18 / 232 | 16 / 232 | 16 / 232 | 0 / 232 |
| 2016 | 20 / 232 | 13 / 232 | 15 / 232 | 0 / 232 |
| 2017 | 18 / 232 | 16 / 232 | 12 / 232 | 0 / 232 |
| 2018 | 18 / 232 | 14 / 232 | 12 / 232 | 0 / 232 |
| 2019 | 17 / 232 | 12 / 232 | 6 / 232 | 0 / 232 |
| 2020 | 16 / 232 | 18 / 232 | 11 / 232 | 0 / 232 |
| 2021 | 8 / 228 | 14 / 232 | 6 / 232 | 0 / 232 |
| 2022 | 3 / 224 | 12 / 232 | 15 / 232 | 0 / 232 |
| 2023 | 7 / 228 | 9 / 232 | 17 / 232 | 0 / 232 |
| 2024 | 13 / 228 | 13 / 232 | 12 / 232 | 0 / 232 |
| 2025 | 14 / 224 | 15 / 232 | 14 / 232 | 0 / 232 |
| 2026Q1 | 4 / 56 | 4 / 58 | 3 / 58 | 0 / 58 |

## Checks against the source

- Rows: the prepare run read 1,503,889 rows, equal to the line count the fetch run recorded
  for the 196 files. Every file starts with the documented header. Every file's
  `industry_code`, `year` and `qtr` match its URL.
- 53 state rows per industry-quarter in every quarter. One national row per industry-quarter.
- Identity checks, industry 10 Total Covered, third-month employment:
  - Counties (including XX999) sum exactly to the state row in 2,588 of 2,597 state-quarters.
    All 9 that do not match contain a suppressed county cell (DC 2018Q1; Iowa 2015Q3 and
    2018Q1-Q4; Nevada 2023Q4; Washington 2022Q2-Q3). Every state-quarter without a
    suppressed county cell matches exactly.
  - The 50 states plus DC sum exactly to `US000` in all 49 quarters. Adding Puerto Rico and the
    Virgin Islands matches in none. So `US000` excludes PR and VI. An analysis that uses the
    national row as a "rest of the U.S." benchmark must account for that.
- No published row count is available to compare against. BLS does not publish the number of
  rows per slice.

## Problems and cautions for the design

1. **The 2025 jump in suppression** (above) coincides with the post-policy period and occurs
   in most states. County-cell samples are not stable across the policy date.
2. **Absent rows are not zeros.** A county drops out of an industry file when it has no
   establishment. Two California counties leave 722513 during the sample.
3. **Undocumented `-` disclosure code** on 993 rows, all with 0 establishments.
4. **Vintage.** The 2025-2026 quarters are preliminary/revised as of 21 Aug 2026 and will be
   revised again. The manifest hashes pin the vintage used here.
5. **Coverage of 722513.** QCEW 722513 includes establishments AB 1228 does not cover (chains
   below 60 national locations, independents). The QCEW does not identify chain size.
6. **Wages are nominal**, and `avg_wkly_wage` is kept as BLS publishes it. The panel does not
   recompute it.

---

# Addendum (2026-11-21): state panel, population series, Prop 99 test data

Prepared by the Data RA (tasks `dr-pop`, `dr-prop99`, `dr-state`; analysis_plan steps 0c-0e).
The design gate is not approved. This addendum reports counts and pass/fail checks only; it
contains no statistic of employment or wages that compares California with other states or one
period with another.

## Population sources (run `fetch-pop`, `code/fetch_pop.py`)

- **U.S. Census Bureau, Population Estimates Program**, files in
  `https://www2.census.gov/programs-surveys/popest/datasets/`. Public domain (works of the U.S.
  Government, 17 U.S.C. 105); cite the Census Bureau, Population Division.
  - `2010-2020/intercensal/state/asrh/sc-est2020int-alldata6.csv` -> `data/raw/census/`:
    annual intercensal state estimates by 6 race groups, age, sex and Hispanic origin (release
    September 2025; Last-Modified 30 Sep 2025). 18,292,193 bytes, 236,844 rows = 51 states x 3
    SEX x 3 ORIGIN x 6 RACE x 86 AGE, 21 columns, header equal to the layout
    (`.../technical-documentation/file-layouts/2010-2020/intercensal/state/SC-EST2020INT-ALLDATA6.pdf`).
    The file has no RACE total and no national row.
  - `2020-2025/state/totals/NST-EST2025-ALLDATA.csv` -> `data/raw/census/`: Vintage 2025
    (release January 2026; Last-Modified 27 Jan 2026). 53,555 bytes, 66 rows (nation, regions,
    divisions, 50 states, DC, Puerto Rico), 97 columns; the leading 12 fields equal the layout
    (`.../file-layouts/2020-2025/NST-EST2025-ALLDATA.pdf`).
- No checksum is published. The sha256 of each file is in `data/manifest.json` and in the run's
  metrics (`data/fetch_pop_metrics.json`), so a clean rerun that fetches other bytes fails.
- Requests sent the generic User-Agent `Mozilla/5.0 (compatible; research-data-fetch/1.0)`.

## Prop 99 test data (run `fetch-prop99`, `code/fetch_prop99.py`)

- `california_prop99.csv` from the synthdid R package, pinned to commit
  `70c1ce3eac58e28c30b67435ca377bb48baa9b8a` (repository HEAD on 2026-11-21; the file last
  changed in `eaf905d`, 2021-03-13) -> `data/raw/synthdid/california_prop99.csv`. License: package
  DESCRIPTION "GPL (>= 2) | BSD_3_clause + file LICENSE". The data are Abadie, Diamond and
  Hainmueller's (2010) replication data (package `data/README.md`).
- Integrity: GitHub's git blob SHA-1 at the pinned commit (`4ff21c81...`) is recomputed from the
  downloaded bytes; it matches.
- Structure (counts only; no statistic of PacksPerCapita computed): 32,687 bytes, `;`-delimited,
  columns State, Year, PacksPerCapita, treated; 1,209 rows = 39 states x 31 years (1970-2000),
  balanced, no missing value; `treated` is 0/1, equal to 1 on exactly 12 rows, California
  1989-2000. Used only by check-methods, never in a study run.

## State panel (run `prepare-state`, `code/prepare_state.py`)

Files: `data/derived/state_panel.csv` (2,499 rows = 51 units x 49 quarters, 2014Q1-2026Q1) and
`data/derived/state_panel_pre.csv` (1,224 rows = 51 x 24 quarters, 2014Q1-2019Q4; the only
input of `select` and `level-mde`). Units: the 50 states and DC. Puerto Rico (72) and the
Virgin Islands (78) are dropped: 392 QCEW state rows. Rows are sorted by state_fips, year, qtr.

| Variable | Definition | Units / source |
|---|---|---|
| state_fips | State FIPS code (2 characters) | QCEW `area_fips` SS000 |
| state_abbr | USPS abbreviation | |
| year, qtr, quarter | Reference year, quarter, label `YYYYQq` | |
| emp_722513 | mean(month1, month2, month3 `emplvl`), private NAICS 722513, state row (agglvl 58) | jobs, QCEW |
| emp_722511 | same, private NAICS 722511 (agglvl 58) | jobs, QCEW |
| emp_7225 | same, private NAICS 7225 (agglvl 56); missing when `sup_7225` = 1 | jobs, QCEW |
| emp_10 | same, industry 10 Total Covered, own_code 0 (agglvl 50; includes government) | jobs, QCEW |
| emp_nonff | emp_10 - emp_722513 | jobs |
| sep_722513 | `month3_emplvl` of 722513 (third month of the quarter; for the CEM cross-check) | jobs, QCEW |
| wages_722513 | `total_qtrly_wages` of 722513 | US dollars, nominal |
| aww_722513 | `avg_wkly_wage` of 722513 as BLS publishes it | US dollars per week, nominal |
| pop | July 1 resident population interpolated to the quarter (below) | persons, Census PEP |
| pop_extrap | 1 if pop is extrapolated (quarter time after 2025.5), else 0 | 0/1 |
| sup_7225 | 1 if the state 7225 row has disclosure code `N` | 0/1 |

Population construction (design.data, source 2): July 1 anchors 2013-2019 = intercensal file,
SEX 0, ORIGIN 0, summed over RACE 1-6 and AGE 0-85; 2020-2025 = Vintage 2025 POPESTIMATE2020-2025
(SUMLEV 040). Anchor of year y at y + 0.5; quarter q of year y at y + (q - 0.5)/4; ln pop is
linear between adjacent anchors; after 2025.5, ln pop(2025) + (x - 2025.5)[ln pop(2025) -
ln pop(2024)]. 2014Q1 (2014.125) uses the 2013 and 2014 anchors; 2019Q4 (2019.875) uses the
2019 intercensal and the 2020 Vintage 2025 anchors.

Seasonal adjustment, logs, pools and aggregates are not computed here; the estimator code builds
them from these columns.

## Checks (analysis_plan 0e; exact values in `data/prepare_state_metrics.json`)

| Check | Result |
|---|---|
| 51 units x 49 quarters, no duplicate key | pass (2,499 rows; 51 units; 49 quarters) |
| QCEW state rows matched to the grid, each industry | 2,499 of 2,499 for 722513, 722511, 7225 and 10 |
| No missing 722513 / 722511 / 10 state value (employment, wages, avg weekly wage) | pass (0 missing) |
| 7225 state rows suppressed | 4 rows; `emp_7225` missing on exactly those rows (pass) |
| aww identity, \|avg_wkly_wage - total_qtrly_wages / (13 x emp_722513)\| <= $1, row by row | pass (0 of 2,499 rows outside) |
| Splice: states whose V2025 July 2020 / intercensal July 2019 ratio lies outside 0.97-1.03 | 0 of 51 (pass) |
| Intercensal SEX 1 + 2 and ORIGIN 1 + 2 add up to the SEX 0 / ORIGIN 0 totals (2013-2019) | 357 of 357 state-years each |
| Vintage 2025: 50 states + DC add up to the U.S. row | 6 of 6 years (2020-2025) |
| Population missing | 0 |
| Extrapolated quarters (`pop_extrap` = 1) | 2025Q3, 2025Q4, 2026Q1 (153 rows) |
| `state_panel_pre.csv` = header + the 2014Q1-2019Q4 lines of `state_panel.csv`, byte for byte | pass; last quarter 2019Q4, max year 2019 |
| D20 states present / California present | 20 of 20 / yes |

## Discrepancies and cautions

1. **Extrapolated quarters: three, not two.** design.data says "extrapolated after 2025.5 ...
   (2025Q4, 2026Q1 flagged)". Under the design's own placement rule, 2025Q3 sits at 2025.625,
   which is also after the last anchor (2025.5), so 2025Q3 is extrapolated and flagged as well.
   The script follows the formula; the parenthetical in the design omits 2025Q3. This matters
   only if a per-capita (P) candidate wins.
2. **The four suppressed 7225 state rows are all in 2024Q4**: Alaska, New Hampshire, Vermont and
   Wyoming. 2024Q4 is inside the post window (2024Q2-2026Q1), so rob-7225's rule drops these four
   donors; New Hampshire and Wyoming are D20 states (D20 would have 18 donors in rob-7225).
3. Population for 2019Q4 uses the 2020 Vintage 2025 anchor, i.e. the pre-2020 file
   `state_panel_pre.csv` contains a population value informed by a July 2020 estimate. It
   contains no QCEW value after 2019Q4.
4. `emp_10` is Total Covered (private and government), as the design specifies, so `emp_nonff`
   includes government employment.
