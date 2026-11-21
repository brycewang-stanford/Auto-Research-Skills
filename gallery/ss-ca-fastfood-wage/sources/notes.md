# Scout notes: ss-ca-fastfood-wage (task q-novelty)

Compiled by the Scout on 2026-11-21. Every fact below was read from a document fetched on
that day; its location follows it in brackets. "PDF p." is the page of the PDF file;
"p." alone is the printed page number. **[Scout]** marks my own reading or arithmetic,
not a claim made by any source. I downloaded no QCEW employment data and computed nothing
on outcomes.

Updated 2026-11-21 for finding F14 of `reviews/question-r3`: plan.json now has H1-H3 only
(H4, a specification grid, was deleted after `reviews/question-r2`). Passages that described
H4 or a grid as part of this study are rewritten or marked superseded below; the literature
facts are unchanged.

## 0. Read this first: three corrections to plan.json

1. **"No published estimate uses data past 2025Q3" is not quite true.** Clemens, Edwards,
   Meer and Nguyen, NBER w35931 (October 2026) `[clemens2026synthetic]` state "The QCEW and
   QWI currently end in 2025Q4" (p. 6) and analyse "the 2026Q1 data release from Friday,
   Aug. 28, 2026, covering data through 2025Q4" (p. 6, fn 3). Their 1,440 synthetic-control
   and SDID estimates on the "post-period-average estimand" use "QCEW and QWI fast-food
   (NAICS 722513) employment, 2015–2025" (appendix table note, p. 29, PDF p. 30), so they use 2025Q4.
   [Scout: the text never states the last post quarter of that average; 2025Q4 is implied
   by "currently end in 2025Q4" and "2015-2025".] Their fixed-horizon estimates stop at
   2025Q3. The revised Clemens et al. w34033 (October 2026) `[clemens2026employment]`
   uses the same data release but analyses only through September 2025 (p. 3).
   **What is still true:** no study I found uses any 2026 quarter of the QCEW, and none
   estimates a pooled effect over 2024Q2-2026Q1. Suggested wording: "no published estimate
   uses QCEW data for 2026; the latest use 2025Q4 (w35931) or 2025Q3 (Dube; Clemens et al.
   2026)."
2. **The Clemens et al. paper has been revised and renamed.** The NBER page for w34033 now
   serves "Employment Effects of California's Fast Food Minimum Wage: Evidence from the QCEW
   and QWI" (July 2025, revised October 2026), with a fourth author (Nguyen) and two-year
   estimates (median -3.45% in QCEW, -3.52% in QWI; Tables 3 and 7). The July 2025 original
   ("Did California's Fast Food Minimum Wage Reduce Employment?") is at
   `revisions/w34033.rev0.pdf`. Both share DOI 10.3386/w34033. I keep two keys:
   `clemens2025did` (original) and `clemens2026employment` (revision). The plan's "about a
   3% decline" is right for the one-year horizon; the revision gives about 3.5% at two years.
3. **Superseded: H4 was deleted from plan.json after `reviews/question-r2`; the study has
   no specification grid.** The literature facts in this item stay relevant because
   plan.json H2 uses this published map of specification choices (w35931; Dube Table D1)
   to fix its candidate set. Specification choices are already mapped in the literature:
   Dube (2026, Appendix D, Tables D1-D2) moves Clemens et al.'s specifications toward his
   own one choice at a time and reports
   how much each choice moves the elasticity; w35931 (Table A1) reports the median estimate
   by each choice across 1,440 synthetic specifications; Sosinskiy and Reich (2026,
   Appendix A and Table A3) list nine differences and test four. The paper must cite these
   and must not claim to be the first to compare specification choices. The base period and
   the anticipation window are also already varied or estimated: Dube Table 1 Panel B,
   Sosinskiy-Reich Table A3, w35931 fn 5 and CEMN Table A3 (Section 3.1).

Also for the design gate (now reflected in plan.json, whose H1 excludes standard errors
clustered by state): with one treated state, every paper here says cluster-robust
inference is invalid and uses something else (Section 6).

## 1. Studies of AB 1228's employment effects

### 1.1 Clemens, Edwards and Meer (2025), NBER w34033, original version `[clemens2025did]`

- **Data, last period:** monthly QCEW, state aggregates, September 2021 to December 2024
  (p. 3). Sectors: NAICS 722513 (fast food), 722511 (full service), and "non-minimum-wage-
  intensive" = total private excluding NAICS 44-45 and 72 (p. 3). All 50 states in the
  placebo pool (Table A1: 50 placebo states).
- **Estimator:** 12-month fixed-horizon difference of indexed employment (Sept 2023 = 100)
  between California and the comparison, September 2023 to September 2024 (eq. 1, p. 5);
  a triple difference netting out the same change in non-MW-intensive industries (eq. 2);
  "detrended" versions that subtract the 2021-2023 growth trend (pp. 3, 5); event studies
  on detrended, deseasoned monthly data (eqs. 3-4, pp. 5-6).
- **Comparison groups:** rest of the US (baseline), and states that did not raise their
  minimum wage after September 2023 ("Non-Increasers") (pp. 1-2, 8).
- **Outcome:** employment level indexed to September 2023 = 100 (fn 6, p. 4); differences
  are in index points, i.e. percent of the September 2023 level.
- **Treatment date / anticipation:** base month September 2023, the month of enactment;
  the post window includes the two quarters before the April 2024 effective date (p. 3).
  The event study shows the decline starting after enactment, read as anticipation
  (p. 10).
- **Headline estimate:** "employment in California's fast food sector declined by 2.7
  percent relative to ... elsewhere ... Adjusting for pre-AB 1228 trends increases this
  differential decline to 3.2 percent" (abstract). Table 1, Panel B (printed p. 18, PDF
  p. 20): FF, CA minus Rest of US: simple DD -2.74, detrended -3.20; CA minus
  Non-Increasers: -3.14, -3.49; DDD Rest of US: -2.28, -3.57; DDD Non-Increasers: -2.57,
  -3.93. Range -2.28 to -3.93, "median of just under -3.2 percent" (p. 9). Implied own-wage
  elasticities -0.29 to -0.49 (p. 11). **No standard errors.** Inference is placebo:
  Table A1 (PDF p. 23) lists the states with more negative placebo estimates; p-values
  0 (simple DD both groups; detrended DD non-increasers), 0.04 (detrended DD rest of US),
  0.0455, 0.06, 0.06, 0.0909 (DDD variants).
- **Uses QCEW past 2025Q3?** No (ends December 2024).

### 1.2 Clemens, Edwards, Meer and Nguyen (2026), NBER w34033 revised `[clemens2026employment]`

- **Data, last period:** monthly QCEW September 2021 to September 2025, and QWI
  beginning-of-quarter employment 2021Q3 to 2025Q3 (p. 3). "For the QCEW, we analyze the
  2026Q1 data release from Friday, Aug. 28, 2026, covering data through 2025Q4. QWI data
  are from ... release R2026Q2 (V4.14.0)" (fn 6, p. 4). Balanced panel without Alaska and
  Michigan (Table 1 note). [Scout: BLS's August 28, 2026 release is the 2026Q1 release
  `[bls2026cewq1]`, so the footnote's "covering data through 2025Q4" describes what the
  authors used, not what was available.]
- **Estimator:** as in 1.1, at 12- and 24-month (4- and 8-quarter) fixed horizons: simple
  and detrended DD, simple and detrended DDD (eqs. 1-2, pp. 5-6). Detrending for the
  two-year horizon subtracts twice the annual 2021-2023 trend (Table 3 note).
- **Comparison groups:** rest of US (48 placebo states) and the 22 Non-Increasers (Table 2).
- **Outcome:** indexed employment (Sept 2023 or 2023Q3 = 100).
- **Treatment date / anticipation:** base September 2023 / 2023Q3, "the last time periods
  ... that ensure that all post-enactment impacts on employment are appropriately
  categorized as post-treatment effects" (p. 6); they argue Dube's 2023Q4 base and
  2024Q1 exclusion "risk biasing estimates towards zero" (p. 13). They re-estimate the
  one-year QWI results on Dube's 2023Q4 base (fn 9, pp. 10-11; Table A3, p. 41, PDF
  p. 43): median -1.43 vs -1.38 on the 2023Q3 base, none significant at 0.10 (Section 3.1).
- **Headline estimates (percent):**
  - QCEW one year, Table 1 Panel B (p. 24, PDF p. 26): FF Rest of US simple -2.89,
    detrended -3.38; Non-Increasers -3.23, -3.58; DDD Rest of US -2.19, -3.52; DDD
    Non-Increasers -2.54, -3.90; median -3.3 (p. 10). Placebo p-values, Table 2 (p. 25):
    0.0204, 0.0435, 0.0816, 0.0870, 0.0612, 0.0435, 0.1224, 0.1304 (in the order DD all,
    DD non-inc., DDD all, DDD non-inc., detrended DD all, detrended DD non-inc., detrended
    DDD all, detrended DDD non-inc.).
  - **QCEW two years (Sept 2023 to Sept 2025), Table 3 Panel B (p. 26, PDF p. 28): FF Rest
    of US simple -2.74, detrended -3.72; Non-Increasers -3.18, -3.88; DDD Rest of US -2.02,
    -4.69; DDD Non-Increasers -2.31, -5.03; range -2.02 to -5.03, median -3.45** (p. 10).
    Placebo p-values, Table 4 (p. 27): 0.1020, 0.0435, 0.1633, 0.1739, 0.1224, 0.0870,
    0.1224, 0.1739 (same order).
  - QWI one year (2023Q3 base), Table 5 (p. 28): FF Rest of US -0.86, detrended -1.54;
    median -1.38 (p. 10). QWI two years, Table 7 (p. 30): FF Rest of US -2.63, detrended
    -4.00; Non-Increasers -3.04, -4.64; DDD -1.54, -4.69, -1.83, -5.55; median -3.52
    (p. 11).
  - Elasticities: QCEW one year -0.40; two years "just over -0.5" (p. 12). About 18,000
    and 20,000 jobs (p. 1).
- **Uses QCEW past 2025Q3?** Data file covers 2025Q4, analysis stops at September 2025.
- They also report they could replicate Dube's QCEW replication of their spec (-2.9) but
  not his QWI one (+1.5; they get -0.85) (pp. 10-11).

### 1.3 Dube (2026), NBER w35171 `[dube2026labor]`

- **Data, last period:** state-level quarterly QCEW 2015Q1-2025Q3 (quarterly employment
  = mean of the three months), and QWI R2026Q1 (January 2026) 2015Q1-2024Q4 (pp. 4-5).
  QCEW vintage not stated. No suppressed or missing fast-food cells in the 21-state sample
  in either source (fn 8, p. 5).
- **Estimators:** population-weighted event-study DD with state and quarter fixed effects
  on seasonally adjusted log outcomes (eq. 1, p. 6); three DDDs whose outcome is
  ln(FF) - ln(comparison sector) for (A) full-service restaurants 722511, (B) a low-wage
  non-FF composite (NAICS 72 - 722513, supersector 1021, NAICS 56), (C) all non-FF private
  (NAICS 10 - 722513) (p. 7); **preferred: synthetic DID (Arkhangelsky et al.) on the DD
  outcome**, with unit and time weights fitted on employment and reused for wages (pp. 7-8).
  Pre-period for SDID 2015Q1-2023Q4 excluding 2020Q1-2021Q4 (28 quarters) (p. 8). SDID
  weights: Idaho 61%, Utah 22%, Pennsylvania 7%, Texas 7%, Georgia 4% (p. 9).
- **Comparison group:** the 20 states whose binding fast-food minimum is the federal
  $7.25 (AL, GA, IA, ID, IN, KS, KY, LA, MS, NC, ND, NH, OK, PA, SC, TN, TX, UT, WI, WY);
  AR, MA, NM, WV excluded (p. 6).
- **Outcome:** log(employment / population), population interpolated to quarters,
  log-linear between July 1 anchors (p. 5). Wage: log average weekly wage.
- **Treatment date / anticipation:** base 2023Q4; 2024Q1 dropped as a "transition
  quarter" and excluded from both the pre- and the post-period; post 2024Q2-2025Q3 (six
  quarters); COVID quarters 2020Q1-2021Q4 excluded; Panel B uses the 2022Q1-2023Q3 average
  as base, which "is invariant to anticipation that may have leaked into 2023Q4 itself"
  (p. 6). Every Table 1 and Table 2 estimate is reported under both bases (Section 3.1).
- **Seasonal adjustment:** state-industry quarter factors from a 2x4 centered moving
  average over 2015Q1-2019Q4, subtracted from the whole series (p. 7).
- **Inference:** Ferman-Pinto permutation SEs: SD of the 20 placebo estimates scaled by
  sqrt(pop_j/pop_CA) (p. 8).
- **Headline estimates, Table 1 Panel A (p. 29, PDF p. 30), employment %, [FP SE]:**
  DD fast food -1.39 [0.44], OWE -0.19 (0.06); **SDID -0.26 [0.54], OWE -0.04 (0.08)**
  (preferred); DDD vs full-service -0.38 [0.58]; vs low-wage non-FF -1.50 [0.43]; vs all
  non-FF private -2.19 [0.39], OWE -0.29. Synthetic DDD: +0.07, -0.23, +0.04. Wage effects
  +7.50 (DD), +6.99 (SDID). Panel B (pre-average base): DD -1.28 [0.60]; SDID -0.02
  [0.66]. Text: "the preferred SDID yields -0.3 percent (p = 0.50, OWE = -0.04)" (p. 10).
- QWI, Table 2 (p. 30, PDF p. 31), post 2024Q2-2024Q4: DD employment -0.34 [0.49], SDID
  +0.74 [0.46]; separations -12.74 [1.17] (DD).
- **Decomposition, Table D1 (p. 43, PDF p. 44)** - starting from CEM (2025) Table 1, row by
  row (OWE in the DD-detrended column (3)): CEM reported -0.40; Dube's replication -0.42;
  drop detrending -0.36; log(emp/pop) -0.29; multi-quarter windows -0.22; pre-COVID
  seasonality -0.20; his 20 federal-MW controls -0.20; SDID -0.04. Text (p. 41): four of six
  changes matter (detrending, population normalisation, averaging window, SDID); seasonality
  (about 0.02) and donor pool (about 0) do not. On QWI (Table D2), CEM's specs give much
  smaller elasticities; "the data-source switch alone ... accounts for roughly half of the
  gap" (p. 42).
- **Uses QCEW past 2025Q3?** No.

### 1.4 Sosinskiy and Reich (2026), IRLE working paper, April 1, 2026 `[sosinskiy2026effects]`

(Earlier versions: Reich and Sosinskiy, "Sectoral Wage-Setting in California", September
2024 - not reached; May 2025 and September 2025 versions fetched, not relied on.)
- **Data, last period:** county-level quarterly QCEW "for years 2022-2024" (p. 13); event
  window k = -8 to 3; three post-policy quarters 2024Q2-2024Q4 (pp. 13-14; Table 1). Also
  CES, Glassdoor, Square payroll, Advan foot traffic (2023-2025) and scraped prices. Appendix
  A mentions "-1.3 percent using an additional quarter of data" (p. 42).
- **Estimator:** county event-study DD on ln(Y) with county and quarter FE and controls
  (employment outside restaurants, working-age population, state GSP growth), SEs clustered
  by state, weighted by 2010 county population (eq. 2, p. 13); **preferred: triple
  difference vs full-service restaurants (722511)** (eq. 3, p. 14); confidence intervals
  from Rambachan and Roth (2023) with M-bar = 1 using pre-periods from 2023 (p. 14).
- **Comparison group:** counties in states without a state minimum wage. For prices: "the
  95 most populous counties in states that do not have state-wide minimum wage policies"
  vs the 25 largest California counties (p. 11). [Scout: the QCEW section does not restate
  the county sample; N = 1,764 (DD) in Table 1.]
- **Outcome:** log county employment / working-age population (Figure 4 note, PDF p. 36).
- **Treatment date:** reference period 2024Q1, "the last quarter before treatment"
  (Figure 4 note); they reject enactment as reference (pp. 42-43) and "do not find
  anticipation effects" (p. 6). Appendix A.1 and Table A3 (p. 49) re-estimate with CEM's
  reference (2023Q3 / September 2023) and report the 2023Q4 and 2024Q1 coefficients
  directly (Section 3.1).
- **Seasonal adjustment:** state-industry quarter factors from 2010-2019 and 2023-2024
  (p. 13).
- **Headline estimate, Table 1 (p. 31):** DDD EPop 2024Q4 -0.009, 95% CI [-0.029, 0.009],
  OWE -0.117 [-0.903, 0.669]; DD EPop 2024Q4 -0.012 [-0.043, 0.023], OWE -0.198. Text:
  "-1.2 percent" vs CEM's -3.2 (p. 22).
- **Uses QCEW past 2025Q3?** No (2024Q4; possibly 2025Q1 in one robustness line).

### 1.5 Reich (2025), CWED policy brief, February 24, 2025 `[reich2025highlights]`

QCEW, seasonally adjusted; DD "very small (0.7 percent) negative employment effect"; the
preferred triple difference "does not find a significant negative employment effect"
(pp. 8-9). No point estimate or SE printed; superseded by 1.4. Data through mid-December
2024 for some sources (abstract); QCEW coverage not stated precisely.

### 1.6 Clemens, Edwards, Meer and Nguyen (2026), NBER w35931 `[clemens2026synthetic]`

- **Data:** state quarterly QCEW and QWI for 722513, through 2025Q4 (p. 6 and fn 3).
- **Design:** 1,440 specifications = SDID (900) and synthetic control (540) crossed with
  data source, donor pool (Dube's 20 federal-MW states or balanced 48), outcome (5 for
  SDID, 3 for SC), seasonal adjustment (none, Dube's CMA, CEM's quarter-of-year FE),
  detrending (none, CEM linear, 2021Q3-2023Q3 trend), match window (5 options) (Table 1,
  p. 6). Weights fitted with Dube's 2023Q4 base / 2024Q1 transition choice (fn 5); the
  fixed-horizon estimates are measured from 2023Q3 (eq. 1, p. 5), and fn 5 reports that the
  distribution is "slightly more negative, but not meaningfully changed" with a 2023Q3
  baseline and no transition quarter (Section 3.1).
- **Results:** SDID post-period average, QCEW: median -3.58, mean -3.87, SD 2.21; Dube's
  SDID estimate is at the 97th percentile (p. 7). Two-year fixed horizon (2023Q3-2025Q3):
  SDID QCEW median -5.01 (range -10.58 to -0.56); SC QCEW median -4.07 (p. 12). Largest
  single choice: detrending (pooled median -2.83 without, -5.67 with CEM's trend) (p. 12).
  They report that Dube's SDID omits the intercept and uses one penalty for unit and time
  weights (pp. 13-14).
- **Uses QCEW past 2025Q3?** Yes, 2025Q4 (see Section 0).

### 1.7 Melo, Neumark, Sigaud and Wagner (2026), NBER w35749 `[melo2026covered]`

- **Data:** Your Economy Time Series (YTS, from Data Axle) establishment-level annual
  employment, 2019-2025 (panel 2018-2025); chains matched by name to the 60-location
  threshold (pp. 20-22).
- **Estimator:** SDID at state level (California vs other states) and chain-by-state level;
  outcome IHS(employment); treatment = 1 for California in 2023-2025, i.e. dated to
  enactment (p. 22; Table 2 note); preferred start year 2021.
- **Headline:** state level, all chains, start 2021: -0.0137 (placebo SE 0.0240), implied
  elasticity -0.068 (Table 2, Panel A, col 2, PDF p. 48). Chain level: -0.20 to -0.23 for
  all/small chains (significant), -0.03 for the 20 largest (Table 3).
- **Uses QCEW past 2025Q3?** Not QCEW; YTS annual 2025.

### 1.8 Hamdi and Sovich (2025), working paper, March 2025 `[hamdi2025wage]`

Equifax payroll, July 2023 to January 2025; 1,097 fast-food establishments vs 22 control
states at the federal minimum; establishment DD with establishment and firm-by-month FE,
SEs clustered by state (Table 2 note, p. 27). log employment +0.0226 (0.0167); 95% CI
-1.01% to 5.53%; hourly wage +12.13%; OWE 0.19 (Table 2 col 1-2, p. 27; text p. 16).
Large chains only. Not QCEW.

### 1.9 Pandit (2026), Applied Economics Letters `[pandit2026simply]` - metadata only

DOI resolved (published online 4 March 2026). Abstract not reachable (403). Second-hand
only: Dube (2026, fn 3, p. 4) says it uses Advan mobility data and finds an 8 percent
staffing decline, restricted to California counties without local minimum wages and large
chains. Do not cite it for any finding.

### 1.10 Schneider, Harknett and Bruey (2024), Shift Project `[schneider2024early]`

Worker survey; wages rose, no evidence of reduced hours or understaffing (p. 1). Not an
employment-count study.

## 2. Does any study use QCEW data past 2025Q3?

| Study | QCEW last quarter used | Latest outcome window |
|---|---|---|
| CEM 2025 (rev0) | 2024Q4 (Dec 2024) | Sept 2023 to Sept 2024 |
| CEMN 2026 (w34033 rev) | 2025Q3 (Sept 2025); file through 2025Q4 | Sept 2023 to Sept 2025 |
| Dube 2026 | 2025Q3 | 2024Q2-2025Q3 average |
| Sosinskiy-Reich 2026 | 2024Q4 (one line mentions an extra quarter) | 2024Q2-2024Q4 |
| CEMN 2026 synthetic (w35931) | **2025Q4** | post-period average (2015-2025 data); fixed horizon to 2025Q3 |

None uses 2026Q1. QCEW 2026Q1 was released on August 28, 2026 (preliminary)
`[bls2026cewq1]`, so the data exist; the next release (2026Q2) is December 2, 2026.

## 3. Where Clemens et al. and Dube differ

| Choice | Clemens et al. (2025; rev. 2026) | Dube (2026) | Moves the estimate? (Dube D1 / w35931 A1) |
|---|---|---|---|
| Data source | Monthly QCEW (rev.: plus QWI) | Quarterly QCEW (3-month mean) plus QWI | QWI vs QCEW about half the gap (D2, p. 42); converges at 2 years per CEMN |
| Sample end | Dec 2024 (2025); Sept 2025 (rev.) | 2025Q3 (QCEW), 2024Q4 (QWI) | - |
| Base period | Sept 2023 / 2023Q3 (enactment) | 2023Q4; 2024Q1 dropped | Varied by all four, see 3.1: Dube Panel B (2022Q1-2023Q3 average) moves SDID -0.26 to -0.02, DD -1.39 to -1.28; SR Table A3; w35931 fn 5 ("not meaningfully changed"); CEMN Table A3 (QWI median -1.43 vs -1.38). In D1 it changes only jointly with the post window (row 5) |
| Post window | Single month, Sept 2024 (and Sept 2025) | Average 2024Q2-2025Q3 | Yes, jointly with the base: D1 row 5 replaces Sept-to-Sept with pre 2022Q1-2023Q3 / post 2024Q2-2025Q3 averages, DD OWE -0.29 to -0.22 |
| Outcome | Indexed employment level | log(emp / population) | Yes for DD: -0.36 to -0.29 (row 4) |
| Detrending | Linear, 2021-2023 growth | None | Yes: -0.42 to -0.36 (DD), -0.43 to -0.29 (DDD) (row 3); largest in w35931 |
| Seasonal adjustment | None needed for Sept-Sept; 2021-23 month FE for figures | Pre-COVID 2x4 CMA 2015-19 | About 0.02 (row 6) |
| Control states | Rest of US (49 or 48) or 22 non-increasers | 20 federal-$7.25 states | About 0 (row 7) |
| Estimator | Simple DD / DDD of indexes | Weighted TWFE DD / DDD; SDID preferred | SDID: -0.20 to -0.04 (row 8); w35931: Dube's SDID at 97th percentile |
| DDD comparison sector | All private excl. NAICS 44-45, 72 | Full-service; low-wage composite; NAICS 10 - 722513 | Full-service DDD -0.38 vs all-non-FF -2.19 (Table 1) |
| Weighting | Aggregated counts (Rest of US summed) | Population-weighted; SDID weights | Not decomposed |
| Pre-period / match window | Sept 2021-Sept 2023 | 2015Q1-2023Q4 excl. 2020-21 | w35931: match window matters |
| Inference | One-sided placebo rank p, (b+1)/(m+1) | Ferman-Pinto SE | Changes p-values, not points |

Published estimates for comparison (window ending 2025Q3; formerly listed as "H4 targets",
superseded since H4 was deleted; plan.json H2 names Dube 2026 Table 1 Panel B as the
published result closest to its timing): CEMN 2026 Table 3, Panel B
(QCEW two-year: simple DD rest of US -2.74; detrended -3.72; median -3.45) and Dube 2026
Table 1, Panel A (DD -1.39 [0.44]; SDID -0.26 [0.54]). The plan names "Clemens et al.
2025 about 3%"; that one-year number (Table 1 of `clemens2025did`) ends September 2024,
not 2025Q3. **[Scout] The PI should name the exact cells at the design gate.** The units
differ: CEM index points (percent of the Sept 2023 level), Dube log points times 100.

### 3.1 Base period and anticipation: what each study already does

Added for finding F7 of `reviews/question-r2`; each item re-read in the fetched PDF
(sha256 prefixes in `sources.json`). **Four studies vary the base period or estimate the
2023Q4-2024Q1 window directly; a statement that no published study does so is false.**

1. **Dube (2026) `[dube2026labor]`.** Panel A base 2023Q4. Panel B "subtracts the average
   of seven pre-period event-study coefficients (2022Q1-2023Q3) from the post-period
   average" and "is invariant to anticipation that may have leaked into 2023Q4 itself";
   both panels exclude 2024Q1 "from the post-period average as well as from the
   pre-treament period, treating it as a transition quarter" (p. 6). Table 1 (QCEW, p. 29,
   PDF p. 30), employment %, Panel A -> Panel B [FP SE]: DD -1.39 [0.44] -> -1.28 [0.60];
   SDID -0.26 [0.54] -> -0.02 [0.66]; DDD vs full-service -0.38 -> +0.28; vs low-wage
   non-FF -1.50 -> -0.44; vs all non-FF -2.19 -> -1.02; SDDD +0.07 -> +0.35, -0.23 -> +0.32,
   +0.04 -> +0.57. Panel B FP SEs "are approximate". Text: "Panel B pushes employment
   effects closer to zero across most specifications"; SDID OWE -0.04 -> -0.00 (p. 10).
   Table 2 (QWI, p. 30): main DD -0.34 [0.49] -> -0.62 [0.47]; SDID +0.74 [0.46] -> +0.87
   [0.49]. Table D1 row 5 (p. 43) switches CEM's Sept-to-Sept comparison to "pre =
   2022Q1-2023Q3, post = 2024Q2-2025Q3" in one step (DD col. 4: -2.3 -> -1.2, OWE -0.29 ->
   -0.22), so D1 does not separate the base from the post window. He reports no separate
   2023Q4 or 2024Q1 effect in Tables 1-2.
2. **Sosinskiy and Reich (2026) `[sosinskiy2026effects]`.** Main reference 2024Q1. Appendix
   A.1 (pp. 42-43): in their preferred specification "the point estimate is -1.2 when we use
   implementation as the reference date and -1.8 when we use the enactment date. For CEM,
   the comparable estimates are around -1.7 and -3.9" (the CEM pair deduced from CEM's
   Figure A3 Panel C, fn 37), so "almost 60 percent of CEM's estimated employment effect
   occurs during the anticipation phase"; "we interpret these results as suggesting the
   absence of any anticipatory effect" (p. 43). Table A3 (p. 49, PDF p. 49; PDF p. 48 is
   blank, the review cites p. 48): county event-study DD on the employment rate, reference
   2023Q3 (quarterly) or September 2023 (monthly), Rambachan-Roth 95% CI with M-bar = 1,
   SEs clustered by state, log points:

   | Quarter | (1) Preferred | (2) Emp. level, no controls | (3) SA 2021-23 | (4) Preferred, monthly | (5) Closest to CEM, monthly |
   |---|---|---|---|---|---|
   | 2023Q4 | -0.002 [-0.019, 0.017] | -0.004 [-0.019, 0.013] | -0.004 [-0.015, 0.007] | -0.001 [-0.029, 0.027] | -0.005 [-0.021, 0.009] |
   | 2024Q1 | -0.006 [-0.045, 0.027] | -0.010 [-0.045, 0.023] | -0.002 [-0.029, 0.019] | -0.008 [-0.065, 0.049] | -0.014 [-0.045, 0.019] |
   | 2024Q4 | -0.018 [-0.109, 0.069] | -0.027 [-0.113, 0.057] | -0.020 [-0.075, 0.031] | -0.020 [-0.159, 0.125] | -0.030 [-0.111, 0.051] |

   N = 1,764 (quarterly), 5,292 (monthly). [Scout: county level, data through 2024Q4, a
   TWFE event study; (3.9 - 1.7) / 3.9 = 56%.]
3. **Clemens, Edwards, Meer and Nguyen, w35931 `[clemens2026synthetic]`, fn 5 (p. 7, PDF
   p. 8).** Full text: "An additional choice that we do not consider here is the choice of
   baseline period. Dube (2026) uses 2023Q4 and excludes 2024Q1 as a 'transition' quarter.
   In Clemens et al. (2026b), we discuss this choice at length. For comparability, we use
   the choices made in Dube (2026) when creating the synthetic Californias. However, in the
   fixed-horizon estimates, ... we measure the change in the California-minus-synthetic
   employment gap from 2023Q3 to 2024Q3 or 2025Q3, retaining the synthetic weights estimated
   under the baseline and transition-quarter choices of Dube (2026). The distribution of
   estimates is slightly more negative, but not meaningfully changed, when using 2023Q3 as
   a baseline and not excluding any transition quarters." The fixed-horizon estimator
   (eq. 1, p. 5) sets t0 = 2023Q3; Figures 2-3 are "against a common 2023Q3 baseline". So
   the 1,440-specification grid does not include the base as a dimension, but the fixed-
   horizon estimates use a 2023Q3 base, and the post-period-average distribution was
   re-run on a 2023Q3 base. **No numbers are given for that re-run.**
4. **Clemens, Edwards, Meer and Nguyen, w34033 rev. `[clemens2026employment]`, fn 9 (pp.
   10-11, PDF pp. 12-13) and Table A3 (p. 41, PDF p. 43).** "Dube (2026)'s QWI estimates use
   changes relative to a baseline of 2023Q4 rather than 2023Q3. For the sake of direct
   comparison, we produce estimates that mirror this choice in Table A3 and differ only
   marginally from the estimates that use 2023Q3 as the baseline. The estimates range from
   -0.59 percent to -2.47 percent with a median of -1.43 percent. None of the eight
   estimates are significant at the 0.10 level." Table A3 (QWI, Q4 2023 to Q4 2024) vs
   Table 5 (QWI, Q3 2023 to Q3 2024, p. 28), simple / detrended: FF Rest of US -1.14 /
   -1.32 vs -0.86 / -1.54; FF Non-Increasers -1.56 / -1.53 vs -1.22 / -2.02; DDD Rest of US
   -0.59 / -1.93 vs -0.18 / -1.75; DDD Non-Increasers -1.15 / -2.47 vs -0.59 / -2.45.
   Placebo p-values, Table A4 (p. 42): 0.2245, 0.2174, 0.3061, 0.3043, 0.1837, 0.2174,
   0.1837, 0.1304. Figures A1 and A3 plot the QWI series indexed to 2023Q4. [Scout: QWI
   only and one-year only; no QCEW estimate on a 2023Q4 base; the comparison shifts the
   end quarter with the base (Q3-Q3 vs Q4-Q4), so it is not a pure base-period test.] On
   p. 13 they argue that both the 2024Q1 reference (SR) and the 2023Q4 base with 2024Q1
   dropped (Dube) "risk biasing estimates towards zero".

**[Scout] What is left:** none of these estimates the 2023Q4-2024Q1 window at state level
with SDID or synthetic control and reports it with a pre-specified test; SR's direct
estimate is a county TWFE event study ending 2024Q4. A 2023Q3 base with 2023Q4-2024Q1
reported separately repeats SR Table A3's design choice at another level and estimator; it
uses no post-2024Q1 data.

## 4. What AB 1228 covers (official sources)

- Signed September 28, 2023; $20 effective April 1, 2024 `[dir2026fastfoodcouncil]`;
  added Labor Code sections 1474-1476 `[dir2024fastfoodfaq]`.
- Covered "fast food restaurant": (1) a limited-service restaurant ("limited or no table
  service, where the customers order ... and pay ... before the items are consumed");
  (2) part of a chain of at least 60 establishments nationwide (off-site administrative
  or warehouse locations not counted); (3) primarily engaged (more than 50% of revenue) in
  selling food and beverages for immediate consumption. Franchisees covered. Coffee, ice
  cream, boba, donut shops can be covered `[dir2024fastfoodfaq]`.
- Exemptions: restaurants that produce and sell bread (at least half a pound, stand-alone)
  on site as of September 15, 2023; restaurants inside a grocery establishment over
  15,000 sq ft whose staff are employed by the grocer; restaurants in or with an airport,
  hotel, event centre (over 20,000 sq ft or 1,000 seats), theme park, museum, gambling
  establishment; concession restaurants on a single-company campus serving its staff, or
  on public beaches, parks, historic districts or port land `[dir2024fastfoodfaq]`.
- Fast Food Council may raise the wage annually by the lesser of 3.5% or CPI, not before
  January 1, 2025 `[dir2024fastfoodfaq]`. **No increase found:** the MW-2025 and MW-2026
  general orders still list only the fast-food rate "effective April 1, 2024"; no MW-2025
  fast-food supplement exists; the Council's meeting list ends February 26, 2025
  `[dir2026mw]`, `[dir2024mwffsupplement]`, `[dir2026fastfoodcouncil]`. [Scout: absence
  of evidence; not an official statement that no increase occurred.]
- General state minimum: $16.00 (2024), $16.50 (2025), $16.90 (2026) `[dir2026mw]`.
  [Scout arithmetic: the fast-food premium over the general minimum falls from $4.00 to
  $3.50 to $3.10.]
- Coverage share (Sosinskiy-Reich 2026, re-checked in the fetched PDF, sha256 prefix
  92fc2cac799f9c96): "We estimate that about 70 percent of the workers in the two
  industries are covered by the policy" (p. 6). The two industries are "fast food
  restaurants and snack and nonalcoholic beverage bars" (same paragraph), which the paper
  maps to NAICS 722513 and 722515 (p. 8). So the 70% is for **722513 and 722515
  combined**. The introduction words it as "roughly 70 percent of California's fast-food
  industry employees" (pp. 2-3). The only worked number is 71.8% (p. 7): 76.1% of chain
  fast-food restaurants (Dataessential counts) are in chains of 60+, times 94.4% of
  employees in chains, under employees-per-restaurant figures the authors give as an
  example ("If, for example ..."); it is stated for "fast food" restaurants, not a NAICS
  code, and is used to rescale the QCEW fast-food wage effect (p. 19). **No coverage
  share for NAICS 722513 alone is given.** Reich (2025) says about 72%.

## 5. QCEW documentation for county x industry quarterly files

- Open data: CSV slices for the most recent five years; older years from the downloadable
  data files `[blsqcewopendata]`. URL patterns:
  `https://data.bls.gov/cew/data/api/{year}/{qtr}/industry/{naics}.csv` and
  `.../area/{fips}.csv`. Fields include area_fips, own_code, industry_code, agglvl_code,
  size_code, year, qtr, disclosure_code (blank or "N" = not disclosed), qtrly_estabs,
  month1_emplvl-month3_emplvl, total_qtrly_wages, avg_wkly_wage, plus location quotients
  and over-the-year changes (42 fields).
- Aggregation levels: 78 county x NAICS 6-digit x ownership; 58 state; 18 national
  `[blsqcewagglvl]`. Private ownership own_code = 5 `[blsqcewowncodes]`.
- Disclosure: about 60% of the most detailed cells are suppressed; published higher-level
  totals include the suppressed lower-level data `[blsqcewfaq]` (Q6, Q13, Q14).
- Employment: workers who worked or received pay in the pay period including the 12th;
  multiple job holders counted by each employer `[blsqcewhom]`. Average weekly wage =
  total quarterly wages / mean monthly employment / 13 `[blsqcewtechnote]`.
- Revisions: data preliminary until finalized with the following year's first-quarter
  release; revisions usually minor `[blsqcewfaq]`, `[blsqcewtechnote]`.
- NAICS 2022 (pp. 562-563) `[naics2022]`: **722513 Limited-Service Restaurants** -
  "providing food services (except snack and nonalcoholic beverage bars) where patrons
  generally order or select items and pay before eating", e.g. fast-food, fast casual,
  pizza delivery, takeout sandwich shops. **722511 Full-Service Restaurants** - patrons
  "order and are served while seated ... and pay after eating". **722515 Snack and
  Nonalcoholic Beverage Bars** - coffee shops, doughnut, ice cream, juice bars.

## 6. What this implies for the design [Scout]

1. **Question status:** see verdict below. The new contribution is the window
   2024Q2-2026Q1 (2026Q1 data released August 28, 2026, preliminary) and the year-two
   effect (H3). (A fixed-in-advance specification grid was listed here earlier; it is
   superseded, since H4 was deleted from plan.json after `reviews/question-r2`.)
2. **Treated sector is wider than 722513.** DIR says coffee, donut and ice-cream chains can
   be covered; Sosinskiy-Reich describe the law as covering limited-service restaurants
   and snack and nonalcoholic beverage bars (Starbucks, Dunkin), i.e. NAICS 722515. So
   722515 must not be a control, and 722513+722515 is a natural secondary outcome. 722513
   also contains uncovered small chains and independents, so a 722513 effect is an
   intent-to-treat effect. The published share (about 70% covered) is for 722513 and
   722515 combined; the 722513-only share is unknown, so a dilution factor of about 0.7
   is an approximation, not a sourced number.
3. **Full-service DDD is contested:** CEMN say spillovers make 722511 invalid (p. 15);
   Dube shows the DDD comparison sector alone moves the estimate from -0.38 to -2.19.
   Any DDD sector must be fixed at the design gate and the alternatives reported.
4. **Anticipation is the biggest timing issue.** Enactment September 28, 2023; effect
   April 1, 2024. Bases in use: Sept 2023 (CEM), 2023Q4 (Dube), 2024Q1 (SR). A base of
   2023Q3 with 2023Q4-2024Q1 reported separately as an anticipation window keeps the
   pooled 2024Q2-2026Q1 effect from absorbing or hiding anticipation; report the 2024Q1
   base as a planned alternative. This is not new: SR Table A3 already uses a 2023Q3
   reference and reports 2023Q4 and 2024Q1 (-0.002 and -0.006 in the preferred
   specification), and Dube Panel B, w35931 fn 5 and CEMN Table A3 vary the base
   (Section 3.1); cite them.
5. **Inference with one treated state:** cluster-robust SEs are not valid (Dube p. 8;
   CEM p. 6; SR p. 14). Options in use: placebo-rank p-values (CEM), Ferman-Pinto SEs
   (Dube), Rambachan-Roth bounds (SR). plan.json H1 now excludes state-clustered SEs; the
   MDE should come from the placebo distribution.
6. **State level is the safer unit.** Dube found no suppressed 722513 cells at state level
   in his 21 states; county x 6-digit cells are often suppressed (about 60% of the most
   detailed cells overall), so a county design needs a pre-registered rule for suppressed
   cells. State totals include suppressed county data.
7. **Pre-period:** the CSV open-data API gives only the last five years; a 2015-start
   pre-period (Dube, w35931) needs the downloadable files. Detrending and the match window
   are the choices that move estimates most (w35931 Table A1).
8. **Population:** California's population grew about 1% less than the US, 2023-2025
   (CEMN p. 14); Dube/SR normalize by population. Fix level vs per-capita in advance.
9. **Year two:** the fast-food wage stayed at $20 while the general minimum rose to $16.50
   and $16.90, and CEMN find the wage effect fell from about 8% to just over 6% by 2025Q3
   (p. 11). H3 must be read with the year-two wage effect (H1 by year).
10. **Concurrent shocks:** SB 525 health-care minimum wage from October 2024 touches about
    3% of the non-MW-intensive control sector (CEMN fn 14).
11. **Data vintage:** 2025 quarters were finalized with the 2026Q1 release; 2026Q1 itself
    is preliminary until the 2027Q1 release. Record the download date and release.
12. **QCEW vs QWI:** QCEW counts anyone paid in the pay period with the 12th, so falling
    turnover can lower QCEW counts (Dube Appendix B); CEMN find QCEW and QWI agree at two
    years. QWI is a possible robustness source.

## 7. Novelty verdict

**Partly answered; still open for the 2024Q2-2026Q1 window.** Five studies estimate AB
1228's employment effect with administrative data (CEM 2025 / CEMN 2026, Dube 2026,
Sosinskiy-Reich 2026, w35931, Melo et al. 2026), plus payroll (Hamdi-Sovich) and survey
(Schneider et al.) evidence. Estimates run from about +2% (Hamdi-Sovich) and -0.3% (Dube
SDID) to -3.5% (CEMN two-year median) and -5% (CEMN detrended DDD, two years). No study
uses QCEW for any 2026 quarter, and none estimates the pooled eight-quarter effect
2024Q2-2026Q1, so H1-H3 on that window are new. The closest prior work is CEMN (2026,
two-year fixed horizon through September 2025) and w35931 (QCEW through 2025Q4). How
specification choices move the estimate is already mapped by Dube's Table D1, w35931's
Table A1 and SR's Appendix A; this study claims no contribution there (the former H4 grid
is superseded, deleted from plan.json after `reviews/question-r2`). The base
period and the anticipation window are not open either: Dube Table 1 Panel B, SR Table
A3, w35931 fn 5 and CEMN Table A3 vary or estimate them (Section 3.1).

## 8. Unverified or not reached

- AB 1228 statute text (leginfo.legislature.ca.gov blocked automated access) and its
  chapter number; coverage and dates are taken from DIR pages instead.
- Reich and Sosinskiy (2024), "Sectoral Wage-Setting in California", IRLE WP 104-24: its
  IRLE page now links the September 2025 revision.
- Pandit (2026): abstract and text unreachable (403); DOI metadata only.
- Hamdi and Sovich's SSRN number 5197571: from reference lists; SSRN blocked.
- A UC Santa Cruz report on automation and jobs (seen in search snippets only).
- Whether the Fast Food Council raised the wage after February 2025: no increase in DIR
  orders through MW-2026, but no explicit official statement found.
- The exact last post quarter in w35931's post-period-average estimand (inferred 2025Q4).
