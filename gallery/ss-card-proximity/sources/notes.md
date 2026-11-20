# Scout notes: ss-card-proximity (task q-novelty)

Compiled by the Scout on 2026-11-20. Every number below was read from a fetched document,
and its location is given next to it. Arithmetic marked **[Scout arithmetic]** is my own
check on published numbers, not a claim made by any source. I did not open any answer key
of the bench. I downloaded `proximity.zip` and read only `readme`, `code_bk.txt` and
`read1.sas`; I did not open `nls.dat`, and opened `read1.lst` only far enough to see that it
is the SAS listing of `read1.sas`.

## 0. Citation correction (read this first)

- The seed brief and Card's own codebook (`code_bk.txt`, lines 3-6) cite the paper as
  "NBER Working Paper 4832, August 1994". **That is wrong.** NBER WP 4832 (August 1994) is
  Card, "Earnings, Schooling, and Ability Revisited" `[card1994earnings]` (title page and
  abstract page fetched and OCR'd; Crossref agrees).
- The college-proximity paper is **NBER WP 4483, October 1993** `[card1993nber]`
  (DOI 10.3386/w4483; title page fetched; Crossref agrees). The published version is a
  chapter in *Aspects of Labour Market Behaviour: Essays in Honour of John Vanderkamp*, ed.
  L. N. Christofides, E. K. Grant and R. Swidinsky, University of Toronto Press, 1995,
  pp. 201-222, as listed in Card's own reference list in `[card2000estimating]` (NBER WP
  7769, printed p. 40). Kling's reference list gives pp. 201-221.
- **(literature-r1 L2) The chapter is no longer in refs.bib.** Its text is unreachable, and
  a library catalogue record is not one of the three verification methods PROTOCOL.md
  defines, so the `card1995chapter` record was dropped (2026-11-21). The paper should cite
  `card1993nber` for every number and may say in prose that the paper was published in
  1995 as a book chapter, citing `card2000estimating` for that fact.
- What is known about the chapter's tables:
  - Card's codebook says the chapter has "the same title and identical tables".
  - Card (2000, Table 2 row 4, PDF p. 48) quotes "Card (1995b)" as OLS 0.073 (0.004), IV
    0.132 (0.049), and 0.097 (0.048) with proximity x family background. These equal WP 4483
    Table 4 row 1 and Table 5 col 4, so the chapter's headline numbers match the WP.
  - Kling (2001, Table 1) labels his replicated columns "Card (1995b): T2-c2" (OLS .073
    (.003)) and "T3-c5B" (IV .132 (.049)). In WP 4483, Table 2 col 2 prints 0.075 (0.003)
    and Table 3 Panel B col 5 prints 0.122 (0.046); the matching WP columns are T2 col 5
    (0.073 (0.004)) and T3 Panel B col 6. So either the chapter numbers its columns
    differently from the WP, or Kling mislabelled them; the files cannot settle which.
    Kling's OLS SE (.003) also differs from the WP's (0.004).
  - Neither source covers the Panel A columns.
- **All numbers below are from WP 4483.** Page numbers are WP 4483's printed page numbers
  (text) or its PDF page numbers (tables, which are unnumbered). The paper should label every
  target as "WP 4483 Table x, Panel y, column z", say that the chapter's tables were not
  seen, and use the WP's printed values (e.g. OLS SE 0.004) as targets.

## 1. Target: Card (1993, NBER WP 4483) `[card1993nber]`

Source read: NBER scan (37 pp., no text layer). Text OCR'd with tesseract at 300 dpi; every
table number below was read from the page images (PDF pp. 33-37), not from OCR.

### Data and sample (pp. 3-7, Table 1 on PDF p. 33)

- NLS Young Men (NLSYM): began 1966 with men aged 14-24, follow-ups through 1981. Men from
  neighbourhoods with many non-white residents were over-sampled (p. 4).
- Cross-section: the **1976** interview. Card chooses 1976 because the youngest respondents
  are 24 and all were asked their education then (p. 6).
- Table 1 sample sizes (row 12): overall NLSYM **5225**; interviewed in 1976 with valid
  education **3613** (col 2); valid wage and education **3010** (col 3).
  - Inconsistencies inside the paper: the text (p. 3) says the NLSYM "began in 1966 with
    5525 men" (Table 1 and the codebook's `id` range 1-5225 say 5225); and p. 6 says the
    1976 sample is "3694 observations or 71 percent of the original sample" while Table 1
    gives 3613 with valid education. 3613 is the number of rows in `nls.dat` (readme).
- Sample rule: "Eighty-three percent of men interviewed in 1976 report a valid wage
  observation" (p. 7). Kling (2001) `[kling2001interpreting]`, who replicated Card exactly
  (section 3; Table 1 note, WP p. 20), states the rule precisely: "Replicating Card's sample
  exactly requires including only observations with wages between $1 and $30 per hour. 49
  additional observations were excluded for whom the interview month was missing in 1966
  (D. Card, personal communication, April 20, 1995)."
- The codebook says `lwage76` is "log wage (outliers trimmed) 1976" with **N = 3010**
  non-missing, while raw `wage76` (cents/hour) has N = 3017. The codebook's minimum of
  `lwage76` is 4.6051702 and its maximum 7.7848893.
  - **[Scout arithmetic]** ln(100 cents) = 4.60517, so the trim at $1 is already applied; the
    maximum is ln(2404) = $24.04, below the $30 cap. The 3010 non-missing `lwage76` values
    equal Card's N, so the sample is "rows of `nls.dat` with non-missing `lwage76`". The
    Econometrician should confirm that count, not re-apply the $1-$30 rule (which could
    drop or keep different rows), and report how many of the 3017 `wage76` values lie
    outside the trimmed sample.
- Mean of the dependent variable in the 3010 sample: log hourly wage 6.262 (s.d. 0.444)
  (Table 2 note); years of education 13.263 (s.d. 2.677) (Table 3 note). The codebook gives
  6.2618319 (0.4437977) for `lwage76`.
- Weighting: the file has a `weight` variable (NLS 1976 cross-section weight). Nothing in
  Card's text or table notes says the regressions are weighted, and `read1.sas` runs them
  unweighted. Treat unweighted as the published specification.

### Variable construction

- **Experience** = age - education - 6: "a quadratic function of potential experience
  (age-education-6)" (p. 7). `read1.sas`: `exp76=age76-ed76-6; exp762=exp76*exp76;`.
  Table 2 reports the square divided by 100 (row 3, "Experience-Squared /100"), which only
  rescales its coefficient.
- **Instrument**: an indicator for "the presence of an accredited 4-year college in the local
  labor market" in 1966 (p. 5), based on county of residence in 1966 (p. 5, fn 7). In the
  codebook: `nearc4` "grew up near 4-yr college" (mean 0.678 in 3613 rows); Table 1 row 4
  gives 68.2% in the 3010 sample. Also in the file: `nearc2` (2-year), `nearc4a` (public),
  `nearc4b` (private).
- **Parental education**: missing values are set to the overall mean, with dummies for
  imputation (p. 4): `daded`, `momed` ("missing=avg"), `nodaded`, `nomomed`.
- **Base control set** (Table 3 note, PDF p. 35; Table 4 note, PDF p. 36): black indicator;
  southern residence and SMSA residence in 1976; region in 1966 (8 indicators, Table 2 row
  7, i.e. 9 regions with one omitted); SMSA in 1966; experience and its square.
  `read1.sas` variables: `black smsa76r reg76r smsa66r reg662-reg669 exp76 exp762`.
- **Family background**: "14 variables representing mother's and father's education,
  indicators for missing father's or mother's education, interactions of mother's and
  father's education, and dummies for family structure at age 14" (Table 3 note a; Table 4
  note). Table 2 notes a-c break it down: years of mother's and father's education plus two
  missing indicators; 8 indicators for classes of mother's and father's education; two
  family-structure indicators (both parents at 14; single mother at 14).
  `read1.sas`: `daded momed nodaded nomomed f1-f8 momdad14 sinmom14` = 2+2+8+2 = 14, with
  `f1`-`f8` = indicators for `famed` = 1..8 (famed = 9 omitted). Kling's Table 1 note lists
  the same 14.
- **Standard errors**: Card writes only "standard errors in parentheses" (Tables 2-5). The
  formula is not stated. Evidence that they are conventional (homoskedastic) SEs:
  - Blandhol et al. `[blandhol2025tsls]` reproduce Table 3 Panel A column 5 with
    heteroskedasticity-robust SEs and get 0.132 **(0.054)** (their Table 3 col 1, Table
    SA.3), against Card's printed (0.055).
  - Bi, Kang and Taylor `[bi2020inferring]` reproduce Panel A columns 5 and 6 as 0.132
    (0.055) and 0.140 (0.055) (their Table 1); they do not say which SE they use.
  - This is suggestive, not proof. **Design implication:** H1 should compare the published
    SE with the conventional 2SLS SE and report the robust SE next to it, and state this
    choice before running.

### Published estimates

**Table 2, "Estimated Regression Models for Log Hourly Earnings" (OLS; PDF p. 34; N = 3010)**

| Row 1, Education | (1) | (2) | (3) | (4) | (5) |
|---|---|---|---|---|---|
| coefficient | 0.074 | 0.075 | 0.073 | 0.074 | **0.073** |
| SE | (0.004) | (0.003) | (0.004) | (0.004) | **(0.004)** |
| Region 1966 + SMSA 1966 | no | yes | yes | yes | yes |
| Parental educ main effects | no | no | yes | yes | yes |
| Parental educ classes | no | no | no | yes | yes |
| Family structure | no | no | no | no | yes |
| R-squared | 0.291 | 0.300 | 0.301 | 0.303 | 0.304 |

- Column (2) has the controls of Table 3 Panel A without family background; column (5) has
  the full set and is the "basic specification" OLS of Table 4 row 1.
- Other column (5) coefficients: experience 0.085 (0.007); experience-squared/100 -0.229
  (0.032); black -0.189 (0.019); south 1976 -0.146 (0.026); SMSA 1976 0.138 (0.020).
- P-value for the family-background variables (row 13): 0.235, 0.462, 0.165 in cols 3-5.

**Table 3, "Reduced Form and Structural Estimates of Education and Earnings Models" (PDF p. 35; N = 3010)**

Coefficient of "Live near college in 1966" (rows 1, 4) and of education (rows 2, 5):

| | (1) Educ RF | (2) Educ RF | (3) Earn RF | (4) Earn RF | (5) IV | (6) IV |
|---|---|---|---|---|---|---|
| Family background | no | yes | no | yes | no | yes |
| **A: experience exogenous** | 0.320 (0.088) | 0.322 (0.083) | 0.042 (0.018) | 0.045 (0.018) | 0.132 (0.055) | 0.140 (0.055) |
| **B: experience endogenous** | 0.382 (0.114) | 0.365 (0.105) | 0.047 (0.019) | 0.048 (0.019) | 0.122 (0.046) | **0.132 (0.049)** |

- Panel B note b: "experience is treated as endogenous. Instruments for experience and
  experience squared are age and age squared." So Panel B is 2SLS with three endogenous
  regressors (education, experience, experience squared) and three excluded instruments
  (nearc4, age, age squared). Its "reduced form" columns replace experience by age and age
  squared.
- The IV estimates "are simply the ratios of the corresponding reduced form coefficients"
  (p. 12). **[Scout arithmetic]** 0.042/0.320 = 0.131; 0.045/0.322 = 0.140; 0.047/0.382 =
  0.123; 0.048/0.365 = 0.132; all agree with columns 5-6 to rounding.

**Column-by-column specification of Table 3 and Table 2 (added 2026-11-20 after question-r1
F1/F6; re-read from the page images PDF pp. 34-35).** "Base controls" below means exactly
what the Table 3 note lists for *all* models: a black indicator; indicators for southern
residence and SMSA residence in 1976; indicators for region in 1966 (Table 2 row 7: 8
indicators); an SMSA-in-1966 indicator; experience and experience squared. "Family
background" means the 14 variables of Table 3 note a.

| Column | Dependent var. | Regressors on the right | Experience | Printed coefficient (SE) |
|---|---|---|---|---|
| T3 A(1) | education | nearc4 + base controls | exogenous regressor | nearc4 0.320 (0.088) |
| T3 A(2) | education | nearc4 + base + family background | exogenous regressor | nearc4 **0.322 (0.083)** |
| T3 A(3) | log wage | nearc4 + base controls | exogenous regressor | nearc4 0.042 (0.018) |
| T3 A(4) | log wage | nearc4 + base + family background | exogenous regressor | nearc4 **0.045 (0.018)** |
| T3 A(5) | log wage, 2SLS | education (instr. nearc4) + base | exogenous | education 0.132 (0.055) |
| T3 A(6) | log wage, 2SLS | education (instr. nearc4) + base + family background | exogenous | education **0.140 (0.055)** |
| T3 B(1)-(4) | as A(1)-(4) | as A(1)-(4) | endogenous; instruments age, age^2 | 0.382 (0.114); 0.365 (0.105); 0.047 (0.019); 0.048 (0.019) |
| T3 B(5) | log wage, 2SLS | education, exp, exp^2 (instr. nearc4, age, age^2) + base minus exp terms | endogenous | education 0.122 (0.046) |
| T3 B(6) | log wage, 2SLS | as B(5) + family background | endogenous | education 0.132 (0.049) |
| T2 (2) | log wage, OLS | education + base controls | exogenous | education 0.075 (0.003) |
| T2 (5) | log wage, OLS | education + base + family background (rows 9-11 all "yes") | exogenous | education 0.073 (0.004) |

- **Panel A column 6** (the experience-exogenous analogue of the basic specification, one
  endogenous regressor, family background included): 2SLS return **0.140 (0.055)**; first
  stage on nearc4 **0.322 (0.083)** (col 2); reduced form on nearc4 **0.045 (0.018)**
  (col 4); N = 3010. Family background is "yes" in cols 2, 4, 6 of both panels (rows 3 and 6).
- **Its OLS counterpart is Table 2 column 5, 0.073 (0.004)**: Table 2 col 5 has the same
  regressors (base controls plus parental-education main effects, the 8 interacted classes
  and the 2 family-structure indicators = the 14 family-background variables), with
  education treated as exogenous. Table 2 column 2 (0.075 (0.003)), which has base controls
  only, is the OLS counterpart of Panel A column 5. Card's Table 4 row 1 also pairs Table 2
  col 5 with Panel B col 6.
- What the Panel B reduced-form columns contain is my reading, not a printed statement:
  note b says only that experience and its square are "endogenous" with "age and age
  squared" as instruments, and the text (p. 13) that Panel B models "instrument experience
  and experience-squared with age and age-squared". In a reduced form this means age and
  age squared take the place of experience and its square.
- **[Scout arithmetic]** Implied conventional first-stage F for Panel A col 6 (from col 2):
  (0.322/0.083)^2 = 15.05; reduced-form t for col 4 = 0.045/0.018 = 2.50, so a
  (homoskedastic) AR test of a zero return in Panel A col 6 is this t-test (with one
  instrument, the AR statistic at beta0 = 0 is the reduced-form statistic; see
  `[cinelli2025omitted]`, whose IV and reduced-form t-values are both 2.33 for col 5).

**Table 4, "OLS and IV Estimates of the Return to Education: Alternative Specifications" (PDF p. 36)**

| Row | OLS | IV |
|---|---|---|
| 1. Basic specification (N=3010) | **0.073 (0.004)** | **0.132 (0.049)** |
| 2. 1978 wages and education (N=2639) | 0.066 (0.006) | 0.117 (0.061) |
| 3. Include KWW score (N=2963) | 0.055 (0.004) | 0.136 (0.078) |
| 4. KWW instrumented with IQ (N=2040) | 0.061 (0.005) | 0.089 (0.085) |
| 5. Proximity to public college as instrument | as row 1 | 0.194 (0.059) |
| 6. 2-year and 4-year proximity as instruments | as row 1 | 0.117 (0.047) |
| 7. Subsample age 14-19 in 1966 (N=2037) | 0.076 (0.006) | 0.094 (0.064) |

- Text (p. 14): row 1 is "OLS from column (5) of Table 2; IV from the lower panel of column
  (6) in Table 3". **So Card's own "basic specification" is Table 3 Panel B column 6 =
  0.132 (0.049), with OLS 0.073 (0.004), first stage 0.365 (0.105), reduced form 0.048
  (0.019), N = 3010.**
- **Ambiguity the design must resolve:** Table 3 Panel A column 5 (no family background,
  experience exogenous) also prints 0.132, with SE 0.055 and first stage 0.320 (0.088).
  Blandhol et al. treat Panel A column 5 as Card's "main results" (their section 6.1;
  Table SA.4); Kling and Card's Table 4 use Panel B column 6. The plan must name which
  column H1's targets come from (I recommend Card's own basic specification, Panel B col 6,
  as primary, and Panel A cols 5-6 as secondary targets), and report all of them.

**Table 5, interaction instruments (PDF p. 37; N = 3010; experience endogenous; family background included)**

Specification of every Table 5 column (note): dependent variable log hourly wage 1976 in all
columns (the note says so, although col 1 is headed "Education", which is the education
reduced form); all models include the base controls; experience and its square "are treated
as endogenous, with age and age squared used as instruments"; family background (14
variables, note c) is "yes" in all four columns. In cols 3-4, nearc4 enters the earnings
equation directly and the excluded instruments are, col 3: nearc4 x an indicator for both
parents having less than high-school education (note a); col 4: nearc4 x the 8
parental-education class indicators (note b). So the direct-effect estimates come from
**Panel-B-type models with family background** (experience endogenous), not from Panel A.

- Column 3 (instrument: nearc4 x both parents below high school, with nearc4 in the earnings
  equation): education 0.093 (0.065); direct effect of nearc4 0.015 (0.029).
- Column 4 (instruments: nearc4 x 8 parental-education classes): education 0.097 (0.048);
  direct nearc4 effect 0.013 (0.024).
- Reduced forms (cols 1-2): nearc4 0.154 (0.135) and nearc4 x low parental education
  0.462 (0.186) for education; 0.029 (0.024) and 0.043 (0.032) for earnings.
- Text p. 21: over-identification test p = 0.28 (col 4); interaction of predicted
  education with proximity gives 0.122 (0.075); p. 22: with 9 interactions as instruments
  and nearc4 excluded, 0.115 (0.034), over-identification p = 0.38 (fn 24), Hausman-Wu
  statistic 1.24.

### What Card claims, and two checks

- Card's reading: the IV estimates are imprecise; "one cannot reject the hypothesis that
  differences between the IV and OLS estimates are due to sampling error" (p. 13). Footnote
  17: under the null that OLS is consistent, the variance of the IV-OLS difference is the
  difference of the variances, approximately the IV variance.
  - **[Scout arithmetic]** For the basic specification, (0.132 - 0.073) /
    sqrt(0.049^2 - 0.004^2) = 0.059/0.0488 = 1.21, so the Hausman t is about 1.2.
- Card says the IV estimates are "50-60 percent higher than the corresponding OLS
  estimates" (p. 13) and "25-60%" (abstract). **[Scout arithmetic]** From his tables,
  0.132/0.073 = 1.81 (Table 4 row 1), 0.132/0.075 = 1.76 (Panel A col 5 vs Table 2 col 2),
  0.117/0.066 = 1.77 (row 2), 0.094/0.076 = 1.24 (row 7). Only row 7 is in his stated
  range; the main ratios are about 75-80%. The paper should quote the numbers, not the
  "50-60%" sentence.
- **Interpretation.** Card's footnotes 10 and 12 (pp. 8, 10): with heterogeneous returns, IV
  estimates a return "for some subset of the population" (citing Angrist and Imbens 1993);
  pp. 23-24 argue the high IV estimate reflects high marginal returns among men from poor
  family backgrounds. The paper must not call the IV estimate the average return for all
  men (seed requirement).
- **Threats Card names** (p. 18): families who value education may live near colleges;
  colleges may come with better local schools; unobserved geographic wage premia; and
  (p. 16-17) some older respondents may have moved near a college by 1966 (Table 4 row 7
  restricts to ages 14-19 in 1966).

## 2. Data source and codebook `[cardproximitydata]`

- `https://davidcard.berkeley.edu/data_sets/proximity.zip`, downloaded 2026-11-20; zip
  sha256 `0e9b2ad4182ea631ca3dd8a5fff6c1b0ab86b56c6a3fa868870f716e8d82691f` (the Data steward
  should record its own hash in `data/manifest.json`). Files dated 2002-05-30:
  `code_bk.txt`, `nls.dat` (3613 rows, ASCII, missing = "."), `read1.sas`, `read1.lst`,
  `readme`. No licence is stated anywhere in the zip.
- The codebook gives fixed column positions for 52 variables, but `read1.sas` reads the
  file in list (space-delimited) mode in the same order; the file is named `nls.flt` in the
  SAS `infile` line. Key variables: `nearc4` (cols 10), `ed76` (18-19), `age76` (24-25),
  `daded` (27-31), `nodaded` (33), `momed` (35-39), `nomomed` (41), `weight` (43-54),
  `momdad14` (56), `sinmom14` (58), `reg661`-`reg669` (62-78), `lwage76` (86-97),
  `famed` (112), `black` (114), `smsa76r` (116), `reg76r` (120, "in south in 1976"),
  `smsa66r` (126), `wage76` (128-132), `kww`, `iq`.
- `read1.sas` constructs `exp76`, `exp762` and `f1`-`f8`, and its last two `proc reg`
  models are the OLS of Table 2 column 2 and column 5. `read1.lst` holds that program's
  output; I did not read its regressions. The PI can decide whether the Econometrician may
  use it as a check.
- The R package `wooldridge` ships a derived `card` data set (3010 obs, 34 variables,
  `exper = age - educ - 6`) `[wooldridgecarddata]`. It lacks `famed` and the imputation
  flags, so it cannot build Card's 14 family-background variables. **Use `nls.dat`.**

## 3. Prior replications and reanalyses of these data

| Source | What it does with Card's data | What it implies here |
|---|---|---|
| Kling (2001) `[kling2001interpreting]` (WP 7989, Table 1, p. 20) | Replicates Card "exactly": OLS .073 (.003); IV .132 (.049); age 14-19 IV .094 (.064), N=2037; dropping the experience quadratic gives .133 (.049). Gives the sample rule ($1-$30 wages; 49 obs with missing 1966 interview month). Then characterises the men whose schooling responds to proximity. | H1 has been done before and the specification is reproducible. Kling's OLS SE (.003) differs from Card's (.004). His column labels "Card (1995b): T2-c2" and "T3-c5B" refer to the 1995 chapter (his reference list: pp. 201-221). They do not match the WP 4483 columns with those numbers; whether the chapter numbers its columns differently is unknown (section 0). His sec. 2 (WP printed p. 4) states the interpretation: with Z independent of the unobservables conditional on X, "the 2SLS point estimate ... is a weighted average of the heterogeneous marginal benefits for those whose schooling choice are affected by the instrument, conditional on X", and "the monotonicity implied in (3)" allows the average-causal-response reading, which Kling attributes to Angrist and Imbens (1995). The monotonicity, covariate and complier conditions are Kling's; the Angrist-Imbens abstract read here states none of them. |
| Blandhol, Bonney, Mogstad, Torgovitsky (2025) `[blandhol2025tsls]` (sec. 6.1, Table 3, Tables SA.3-SA.4) | Reproduce Panel A col 5: OLS 0.075 (0.004); IV without covariates 0.188 (0.026); IV with covariates 0.132 (0.054), robust SEs; N = 3,010. RESET test of "rich covariates" p = 0.000; DDML estimate of the rich-covariates estimand 0.122 (0.053); LATE/ACR 0.067 (0.046) (DDML) and 0.085 (0.049) (IPSW). | With additive covariates, TSLS here need not be a weighted average of LATEs. Supports the seed requirement not to call the IV the average return, and suggests a note that it is not even guaranteed to be a positively weighted LATE. (Their text says proximity is measured "when the respondent was 14 years old" and calls the survey "NLSY"; Card says 1966 and NLSYM.) |
| Bi, Kang, Taylor (2020) `[bi2020inferring]` (sec. 6.1, Table 1) | Reproduce Panel A cols 5-6: 0.132 (0.055), 95% CI [0.024, 0.239], F = 13.322; 0.140 (0.055), CI [0.033, 0.248], F = 15.081. Conditional on passing an F > 10 pre-test, CIs become [-0.094, 0.357] and [-0.072, 0.327]. | First-stage F in the Panel A specifications is below 16.38 and well below 23.1; conventional significance is fragile. They attribute an "F around 14" to Card; Card's paper reports no F (it is implied by his t). |
| Kang, Jiang, Zhao, Small (2021) `[kang2021ivmodel]` (arXiv v2 sec. 7) | Card example with Wooldridge's `card` data and a reduced control set (exper, expersq, black, south, smsa; no region 1966, SMSA 1966 or family background): first-stage F = 16.72; TSLS 0.132289 (0.049233); homoskedastic AR 95% CI [0.0384, 0.2612]; CLR the same. | The closest published AR result, but not Card's specification and not heteroskedasticity-robust. That the TSLS point estimate and SE coincide with Card's Panel B col 6 is a coincidence of a different model; it is not a replication target. |
| ivmodels documentation `[ivmodelscard]`; Londschien (2025) `[londschien2025guide]` (arXiv v1, sec. 2.1, 3.1, 4, 6; same numbers in both) | Card's `proximity.zip` data, n = 3010; ed76, exp76, exp762 endogenous; instruments nearc4a, nearc4b, nearc2, age76, age76^2 (over-identified, not nearc4 alone); family background, region and race as exogenous controls. OLS 0.072634; TSLS 0.144954; LIML 0.172352. Subvector tests of beta = 0 for education: AR 5.07 (p 0.0016), CLR 10.93 (p 0.0024). 95% sets: Wald (TSLS) [0.058, 0.232], AR [0.083, 0.352], CLR [0.073, 0.396], LM [-0.594, -0.059] U [0.061, 0.467]. Cragg-Donald rank statistic 15.613. Homoskedastic methods throughout (no mention of heteroskedasticity). | A published weak-IV-robust (subvector AR/CLR) analysis of a Panel-B-type model with family background, but with different instruments and non-robust errors. Shows subvector inference with experience endogenous is feasible. The documentation page has no author; the guide shows it is Londschien's package and example. |
| Kitagawa (2015) `[kitagawa2015test]`; Carr and Kitagawa (2021) `[carr2021testing]` (sec. 5.1) | Testable-implication tests of instrument validity in a **binary-treatment** model: education binarised at 16+ years. Per Carr and Kitagawa (the only source here for Kitagawa's Card result): Kitagawa (2015) rejects validity without covariates and conditioned on at most five binary covariates; earlier tests (Huber and Mellace 2015, Mourifie and Wan 2017, Sun 2021) used at most three; with Card's full covariate set Carr and Kitagawa do not reject. Carr and Kitagawa note that binarising can itself violate exclusion through coarsening bias (citing Angrist and Imbens 1995 and Marshall 2016; neither checked by me for this point), and report a check that the binarised treatment captures the instrument-induced change. | Validity of the binarised-treatment model is conditional on covariates, which is weak, indirect support for using the full control set. It does not test the multi-valued-schooling model Card estimates. Kitagawa (2015) is abstract-only here; attribute its Card result to Carr and Kitagawa. |
| **Cinelli and Hazlett (2025)** `[cinelli2025omitted]` (Biometrika accepted manuscript, sec. 2 and sec. 5, Table 2, Fig. 1); package vignette `[ivsensemakr]` | Running example: Card's data, n = 3,010; outcome log hourly wage, treatment education, instrument nearc4; covariates (vignette code) exper, expersq, black, south, smsa, reg661-reg668, smsa66 = **Card Table 3 Panel A column 5** (no family background); classical (homoskedastic) standard errors (manuscript p. 6); df = 2994. Table 2 ("Minimal sensitivity reporting", manuscript p. 16): IV 0.132, **Anderson-Rubin 95% CI [0.025, 0.285]**, t = 2.33, XRV 0.05%, RV 0.67%; first stage 0.320, CI [0.148, 0.492], t = 3.64, XRV 0.31%, RV 3.02%; reduced form 0.042, CI [0.007, 0.078], t = 2.33, XRV 0.05%, RV 0.67%. OLS 7.5% (vignette 0.07469326, CI [0.0678, 0.0816]). Bound "1x SMSA": partial R2 with outcome 2%, with instrument 0.6%, bias-adjusted critical value 2.55 > 2.33. Text (p. 16): confounding as strong as SMSA or black gives an interval of [-0.02, 0.40]. Vignette bounds: 1x black R2zw.x 0.00221, R2y0w.zx 0.0750, CI [-0.0212, 0.402], critical 2.59; 1x smsa 0.00639, 0.0202, CI [-0.0192, 0.396], critical 2.57. The method covers exclusion violations ("side-effects") and instrument confounding with the same algebra (sec. 5, p. 15). | **Answers the substance of H3 and H4 on Panel A column 5**: a weak-IV-robust (homoskedastic AR) interval that excludes 0, and a sensitivity analysis showing the sign is not robust to a confounder or side-effect as strong as SMSA or black. The robustness value of the IV equals that of the reduced form: the IV conclusion hinges on the reduced form. The paper (2.55) and the 2026 vignette (2.57) give slightly different SMSA critical values; quote the version you cite. |
| Steiner, Houssineau and Steel (2025/2026) `[steiner2025possibilistic]` (arXiv v3, sec. 5.3, Table 5, Fig. 2b) | Card's data; outcome log hourly wage, treatment years of schooling, instrument nearc4; covariates partialled out "including experience, experience squared, family background, marital status, race, region, and parents' education" (imputed by the mean with missingness indicators): **not Card's exact column** (adds marital status). Direct effect of proximity alpha restricted to A = [0, a]. With A = {0} the posterior mode is "just below 0.15" and the effect is significant; with A = [0, 0.02] and [0, 0.04] the uncertainty intervals include zero. Lower/upper probabilities of beta > 0 (Table 5): a = 0, 0.01, 0.02, 0.03, 0.04 give lower 1, 1, 0.887, 0.748, 0.517; upper 1 throughout. | A published exclusion-restriction sensitivity analysis in the direct-effect (gamma) parametrisation that H4 uses, on a near-Card specification with family background: the positive return survives a 1-point direct effect and not 2 points. Not frequentist CHR, and covariates differ. |
| Delbianco (2026) `[delbianco2026testing]` (arXiv v2, sec. 5, Table 2) | n = 3010, data "from Wooldridge, 2010"; "Card's covariates" = experience and its square, race, South, SMSA, SMSA in 1966, region dummies (Panel A col 5). First stage 0.320, first-stage F 13.3, OLS 0.075, IV 0.132 (0.055). A fourth-cumulant test of exclusion: p = 0.970 with Card's covariates, but the identification diagnostic shows the test is uninformative ("consistent with exclusion and equally with sizeable violations"). | Another reproduction of Panel A col 5 (F 13.3). No usable bound on the direct effect. |
| Słoczyński, Uysal and Wooldridge (2024) `[sloczynski2024abadie]` (arXiv v4, sec. 4.2, Table 3) | Binarised treatment (13+ or 16+ years); Card's covariates without family background (quadratic experience, nine regional indicators, black, SMSA 1966 and 1976, South 1976). 2SLS (robust SE): some college 0.661 (0.294); college completion 1.392 (0.798). | Reanalysis of a different (binary) estimand; says many estimates are "too large", possibly because of failures of exclusion and monotonicity. Context only. |
| Tübbicke (2023) `[tubbicke2023when]` (Empirical Economics 65; sec. 3, Table 3, journal p. 2989) | Card's data restricted to cells with at least five observations (n = 2,988); treatment "some college" (more than 12 years); baseline = Card's covariates without family background (experience and its square, 1966 region, black, South 1976, urban 1966 and 1976). Table 3 Panel A: OLS 0.238 (0.017); 2SLS 0.603 (0.289); kernel matching 0.279 (0.228); IPW 0.323 (0.219); ECB 0.289 (0.212). First stage 0.065 (2SLS) vs 0.098-0.102 (PS-based). Saturated specification: 2SLS 0.570 (0.350) vs 0.266; with Słoczyński's reordered instrument 0.289 (0.195) vs 0.192. "2SLS estimates are somewhere between 50 and 100% larger than more flexible PS-based estimates", attributed to the "implicit conditional-variance weighting of 2SLS". | Further evidence, on a binary-treatment version of these data, that linear-in-covariates 2SLS does not estimate a LATE-type average here (Słoczyński 2021 is the theory and was not fetched). Supports narrowing the interpretation (section 5 item 9). **Monotonicity is also in doubt (literature-r2 L5):** Tübbicke (journal p. 2990) reports that Słoczyński (2021) attributes the large 2SLS estimate to defiers; with his reordered instrument the saturated 2SLS falls from 0.570 to 0.289 (Table 3 Panel C); Słoczyński, Uysal and Wooldridge also name failures of monotonicity. Słoczyński (2021) is the source for both the weighting and the defier arguments and was not fetched. All of this is for a binary "some college" treatment on n = 2,988 without family background: evidence by analogy for Card's per-year 2SLS, not a direct test. |
| Card (2000) `[card2000estimating]` (NBER WP 7769; Econometrica 2001; Table 2 row 4, PDF p. 48) | Card's survey of supply-side IV estimates: "Card (1995b)", NLS Young Men; OLS 0.073 (0.004), IV 0.132 (0.049); proximity x family background 0.097 (0.048). Abstract: IV estimates from such instruments are "typically as big or bigger" than OLS; one interpretation is high marginal returns among low-education subgroups affected by the instrument. | Confirms the chapter's headline numbers equal WP 4483's. The standard place where the proximity estimate is set against other IV estimates of the return to schooling. |
| Jiang, Yang and Ding (2022) `[jiang2022multiply]` (arXiv v2 sec. 6.1, Table 3) | Principal stratification without the exclusion restriction, under principal ignorability: Z = nearc4, intermediate S = education beyond high school, Y = log wage 1976, n = 3010; covariates race, age and its square, family structure, past living areas. Strata shares: compliers (u = 10) 7% (3%, 10%), never (00) 48%, always (11) 45%. Triply robust estimates: tau_10 0.10 (-0.01, 0.23); tau_00 0.02 (-0.03, 0.07); tau_11 0.01 (-0.05, 0.07). Other estimators give tau_10 between 0.09 and 0.15 (one weighting estimator -0.87). "No significant evidence of violating the ER." | A test-like check of exclusion for always- and never-takers on these data, under principal ignorability and a binary intermediate variable. Not a sensitivity bound on Card's specification. **(literature-r2 L6)** The authors' text calls tau_10 "positive and statistically significant", but their triply robust interval (-0.01, 0.23) includes 0 and the unstabilised weighting estimator gives -0.87 (-1.69, -0.05); only the regression and stabilised-weighting estimators exclude 0. Cite the table, not the sentence. |
| Luo, Li, Miao and He (2024) `[luo2024identification]` (Statistics in Medicine; arXiv v2 sec. 6, Table 2) | Same set-up with negative controls (average parental education as negative-control exposure, IQ as negative-control intermediate) instead of principal ignorability, n = 3,010; covariates race, age, KWW, family structure, geography; missing covariates imputed by kNN. Preferred cases (iii)-(iv): Delta_ss -0.18 (-0.55, 0.80) / (-0.56, 0.78); Delta_ss-bar 0.87 (0.05, 1.93) / 0.85 (0.00, 1.88); Delta_s-bar-s-bar -0.07 (-0.91, 0.23) / (-0.89, 0.26). "No significant evidence of violating the exclusion restriction"; cites Tan (2006), Jiang et al. (2022), Kédagni (2021) as consistent. | As above, with different identifying assumptions. Intervals are wide, so "no significant evidence" is weak evidence. **(literature-r2 L6)** The preferred-case complier effect 0.85 (0.00, 1.88) has its lower bound at 0, and is for a binary "beyond high school" treatment, not per year. Cases (i)-(ii), which the authors treat as misspecified (no IQ proxy in the outcome model), differ: case (i) gives significantly negative complier (-0.68 (-1.85, -0.25)) and never-taker (-0.86 (-2.83, -0.32)) effects, the latter a direct effect of proximity; case (ii) intervals include 0. |

**This table is a selection of reanalyses of these data, not a complete list** (literature-r1
L4). Not verified (named by the sources above, not fetched by me): Huber and Mellace (2015),
Mourifie and Wan (2017), Sun (2021), Andresen and Huber (2021), Słoczyński (2021; now Review
of Economic Studies, doi 10.1093/restud/rdag116 per Crossref), Tan (2006, JASA), Kédagni
(2021, J. Econometrics), Marshall (2016), Cameron and Taber (2004), Carneiro, Heckman and
Vytlacil (2011), Heckman et al. (2018), Cinelli and Hazlett (2020). Do not cite them without
fetching them.

Searched and found **not** to use Card's data (so not prior work on this question): Masten
and Poirier, "Salvaging Falsified IV Models" (arXiv 1812.11598; mentions Card only via
Card 2001); Dorn and Yap, "Sensitivity Analysis for Linear Estimators" (arXiv 2309.06305);
Conley, Hansen and Rossi (2012) (quarter of birth); Clarke and Matta (2018). Search of
2026-11-20 (second round): web searches for Anderson-Rubin and exclusion-restriction
sensitivity on Card's college-proximity data; candidates fetched and searched for "Card".
A course-lab GitHub repository reporting a CHR-style result was not used (not a citable
source).

## 4. Later-literature methods named in H2-H5

**Stock and Yogo critical value (H2)** `[stock2002testing]`, `[stock2005testing]`
- Table 2 ("Critical Values for the Weak Instrument Test Based on TSLS Size", printed p. 59
  of NBER TWP 284): for n = 1 endogenous regressor and K2 = 1 instrument, maximal size
  r = 0.10 of a nominal 5% Wald test: **16.38** (r = 0.15: 8.96; 0.20: 6.66; 0.25: 5.53).
  The table has entries only for n = 1 and n = 2.
- The bias-based Table 1 starts at K2 = 3, so no bias criterion exists for one instrument.
- The test statistic is the first-stage F, or Cragg-Donald with several endogenous
  regressors, and assumes homoskedastic errors (abstract; MOP p. 2).

**Montiel Olea and Pflueger effective F (H2)** `[montielolea2013robust]`
- Page numbers are the PDF pages of the April 2013 manuscript. Robust to
  heteroskedasticity, autocorrelation and clustering; for **one endogenous regressor** (p. 5: "a linear IV model ... with one endogenous regressor and K
  instruments").
- "In the just identified case" the effective F equals the robust F (p. 3); with
  homoskedastic errors it equals the non-robust F (also `[andrews2019weak]`, eq. 9).
- Baseline: null that the Nagar bias exceeds 10% of a "worst-case" benchmark, 5% size.
  Simplified-test critical values (Table 1, upper 5% quantile of chi2_Keff(x Keff)/Keff):
  for K_eff = 1 and x = 10 (tau = 10%), **23.11**; tau = 20% (x = 5) 15.06; tau = 30%
  (x = 3.33) 12.05; tau = 5% (x = 20) 37.42. Rule of thumb: "rejects when the effective F
  is greater than 23.1" (p. 3).
- The generalized test computes its critical value numerically from the estimated
  covariance matrices (four steps, manuscript p. 7); the simplified test uses the bound in
  Table 1 and is conservative ("strictly larger than the TSLS critical value for all K
  shown", p. 11, for K >= 3). The plan's "10% worst-case-bias critical value at 5% size"
  should say which one it uses; 23.11 (simplified) is the simple pre-specifiable choice.

**Andrews, Stock and Sun (2019)** `[andrews2019weak]`
- Recommendations (manuscript p. 3): with one endogenous regressor, judge strength by the MOP effective
  F; with a single instrument, report identification-robust AR confidence sets, "efficient
  regardless of the strength of the instruments, and so should be reported regardless of
  the value of the first stage F".
- Section 5.1 (manuscript pp. 22-23): AR(beta0) = g(beta0)' Omega(beta0)^-1 g(beta0), with g = delta_hat -
  pi_hat beta0 (reduced form minus first stage times beta0) and Omega the robust variance;
  chi2_k under the null whatever pi. This is the heteroskedasticity-robust generalisation of
  Anderson and Rubin `[anderson1949estimation]`, who assumed homoskedastic normal errors.
  With one instrument the set's bounds are analytical (a quadratic inequality); it can be
  bounded, the union of two half-lines, or the whole line.

**Lee, McCrary, Moreira and Porter (2022)** `[lee2022valid]` (arXiv v1 abstract; Results
2b-2c)
- In the single-IV model a true 5% t-test needs F > 104.7; keeping F > 10 needs critical
  value 3.43 instead of 1.96; their tF procedure gives F-dependent critical values.
- **[Scout arithmetic]** Card's basic t = 0.132/0.049 = 2.69 < 3.43, and the implied
  first-stage F values (below) are far below 104.7. This is context for H3, not a
  pre-registered test.

**Conley, Hansen and Rossi (2012), union of confidence intervals (H4)** `[conley2012plausibly]`
(2008 draft, sec. 4.1)
- Model Y = X beta + Z gamma + e. With support G for gamma: for each gamma0 in G, run 2SLS of
  (Y - Z gamma0) on X with instruments Z, form the usual (1-alpha) interval, and take the
  union over G (eq. 6), approximated on a grid. Coverage is at least 1-alpha asymptotically.
  A slightly shorter version allows asymmetric intervals (appendix).
- Their returns-to-schooling example uses Angrist-Krueger quarter of birth (sec. 6.3), not
  Card's data.
- Stata implementation: `plausexog` `[clarke2018practical]`.

## 4b. Weak-IV-robust subvector inference for Panel B column 6 (added 2026-11-21, design-r1 F1)

Setting. Card's basic specification (WP 4483 Table 3 Panel B col 6) has three endogenous
regressors, ed76 (coefficient beta, under test) and exp76, exp762 (coefficients gamma,
nuisance), and three excluded instruments, nearc4, age76 and age76^2, plus the exogenous
controls. So k = 3, m_W = 2, and the model is just identified. For a hypothesis
H0: beta = b0, define Y0 = lwage76 - b0 * ed76 and W = (exp76, exp762), after partialling
out the exogenous controls (GKM19 Algorithm 1, step 1).

**(a) GKMC subvector AR** `[guggenberger2012asymptotic]` (abstract only;
statistic and critical value as stated in `[guggenberger2019more]` pp. 488, 491 and
`[andrews2019weak]` manuscript p. 31)
- Statistic (GKM19 eq. 2.5-2.8): AR_n(b0) = min over gamma of
  (Y0 - W gamma)' P_Z (Y0 - W gamma) / ((1, -gamma') Omega(b0) (1, -gamma')'), which equals
  the smallest root kappa_p of |kappa Omega(b0) - (Y0, W)' P_Z (Y0, W)| = 0. The minimiser is
  the LIML estimate of gamma, so the statistic is the LIML over-identification
  (Anderson-Rubin/Sargan-type) statistic of the model Y0 = W gamma + error with
  instruments Z. In practice Omega is estimated by (n - k)^-1 (Y0, W)' M_Z (Y0, W) (GKM19
  Algorithm 1: the eigenvalues of ESS * (n - k) RSS^-1).
- Critical value: chi-square(k - m_W) quantile. **For Panel B col 6, k - m_W = 1: reject at
  5% if AR_n(b0) > 3.841** (**[Scout arithmetic]**: the standard chi-square(1) 95% quantile;
  GKM19 Table 3 prints 3.841 for kappa_1 = infinity). Projection would use chi-square(3),
  7.815.
- Assumptions: conditional homoskedasticity (GKMC abstract: "under homoskedasticity").
  No assumption on the strength of identification of beta or gamma. Asymptotic size equals
  nominal size. Andrews, Stock and Sun (manuscript p. 31) say Lee (2015, not fetched) shows
  the result "does not extend to the general non-homoskedastic case".
- This is the test the design-r1 F1 remedy describes ("the over-identification statistic of
  (lwage76 - b0 ed76) on exp76, exp762 instrumented by nearc4, age76, age762, 1 df").

**(b) GKM19 conditional subvector AR** `[guggenberger2019more]` (Quantitative Economics,
full text)
- Same statistic, AR_n(b0) = kappa_p (smallest root), but a data-dependent critical value
  c_{1-alpha}(kappa_1, k - m_W) that depends on the largest root kappa_1, "a measure of the
  strength of identification" of gamma (comparable to a first-stage F for gamma when m_W = 1;
  p. 494). Reject if kappa_p > c_{1-alpha}(kappa_1, k - m_W) (eq. 2.14-2.15).
- Critical values are tabulated for alpha = 10%, 5%, 1% and k - m_W = 1 to 5 in Appendix B;
  6 to 20 are in the online supplement. Linear interpolation between grid points (eq.
  2.13). **For k - m_W = 1 at 5% (Table 3, journal p. 519, read from the page image):**
  kappa_1 = 0.5 -> 0.4; 1.0 -> 0.8; 2.0 -> 1.4; 3.1 -> 2.0; 4.8 -> 2.6; 7.8 -> 3.2;
  9.8 -> 3.4; 18.5 -> 3.7; 29.7 -> 3.8; 1000 -> 3.838; infinity -> 3.841. So when gamma
  (experience) is strongly identified, kappa_1 is large and the test coincides with GKMC.
- **Full transcription (task s-gkm19-table): GKM19 Appendix B, Table 3, k - m_W = 1,
  alpha = 5%, journal p. 519 (PDF p. 34 of the UvA-DARE file).** Read from the page image
  (rendered at 220 dpi and checked by eye). The text layer has the same digits but drops the
  decimal points (e.g. "05 04 13 10 ... ∞ 3841"), so it was used only as a cross-check. The
  printed table has seven (kappa_1, cv) column pairs; they are listed below in reading order,
  down each column pair and then left to right. Every value is exactly as printed
  (37 rows; "inf" = the printed ∞):

  | kappa_1 | cv |
  |---|---|
  | 0.5 | 0.4 |
  | 0.6 | 0.5 |
  | 0.7 | 0.6 |
  | 0.9 | 0.7 |
  | 1.0 | 0.8 |
  | 1.2 | 0.9 |
  | 1.3 | 1.0 |
  | 1.5 | 1.1 |
  | 1.6 | 1.2 |
  | 1.8 | 1.3 |
  | 2.0 | 1.4 |
  | 2.1 | 1.5 |
  | 2.3 | 1.6 |
  | 2.5 | 1.7 |
  | 2.7 | 1.8 |
  | 2.9 | 1.9 |
  | 3.1 | 2.0 |
  | 3.4 | 2.1 |
  | 3.6 | 2.2 |
  | 3.9 | 2.3 |
  | 4.1 | 2.4 |
  | 4.4 | 2.5 |
  | 4.8 | 2.6 |
  | 5.1 | 2.7 |
  | 5.5 | 2.8 |
  | 6.0 | 2.9 |
  | 6.5 | 3.0 |
  | 7.0 | 3.1 |
  | 7.8 | 3.2 |
  | 8.6 | 3.3 |
  | 9.8 | 3.4 |
  | 11.4 | 3.5 |
  | 13.9 | 3.6 |
  | 18.5 | 3.7 |
  | 29.7 | 3.8 |
  | 1000 | 3.838 |
  | inf | 3.841 |

  Use as GKM19 prescribe (eq. 2.13, journal p. 494): linear interpolation between grid
  points, with kappa_1,0 = 0 and q_0 = 0 for values below the first grid point. Above
  kappa_1 = 1000 the paper's footnote 4 suggests a nonlinear interpolation towards the
  chi-square(1) value 3.841. GKM19 say (p. 494) the printed values "have been rounded up to
  one decimal" to offset interpolation error; that sentence refers to Table 1 (k - 1 = 4).
  Whether the same rounding applies to Table 3 is not stated in what I read.
- Assumptions: Gaussian errors with known covariance for the finite-sample results, and
  conditional homoskedasticity for the asymptotic results. Size equals nominal size, shown
  for alpha in {1, 5, 10}% and k - m_W in {1, ..., 20} (Corollary 4). The GKMC test is
  inadmissible relative to it. The authors: "The analysis in this paper relies critically on
  the assumption of homoskedasticity", and both this test and GKMC "must have asymptotic
  size exceeding the nominal size if one allows for arbitrary forms of heteroskedasticity"
  (pp. 489-490).
- Code: the online supplement provides code for computing further critical values (fn. 6).

**(c) Heteroskedasticity-robust options**
- *Projection of the robust full-vector AR (conservative fallback).* `[andrews2019weak]`
  manuscript pp. 30-31: form the joint AR confidence set for (beta, gamma), then keep each
  b0 for which some gamma is in the set. Equivalently, reject H0 if min over gamma of
  AR(b0, gamma) > chi-square(k) quantile (k = 3 here: 7.815, **[Scout arithmetic]**). With
  the heteroskedasticity-robust AR statistic HAR_n(b0, gamma) = n g_bar' Sigma_hat^-1 g_bar,
  g_i = Z_i (y_i - Y_i b0 - W_i gamma) (definition as in `[guggenberger2024powerful]` eq.
  3.11-3.13), the full-vector test is size-correct under heteroskedasticity whatever the
  instrument strength (ASS sec. 5.1), so its projection is valid but "often conservative".
  Projection was advocated by Dufour and Taamouti (2005, not fetched).
- *GKM (2024), Econometric Theory* `[guggenberger2024powerful]` (arXiv v3, full text):
  robustifies GKM19 to arbitrary conditional heteroskedasticity. It uses an adapted
  conditional subvector AR test when a covariance matrix is close to Kronecker-product form,
  as chosen by a model-selection step, and otherwise Andrews's (2017) AR/AR test, which is
  fully heteroskedasticity-robust. Asymptotic size is at most nominal size. AR/AR test (sec.
  3.2): step 1 builds a first-stage confidence set for gamma from HAR_n(b0, gamma) <
  chi-square(k, 1 - alpha1) plus an "estimator set"; step 2 rejects if the infimum over that
  set of a C(alpha)-type statistic HAR_beta,n(b0, gamma) exceeds a chi-square(k - m_W)
  quantile at an adjusted level alpha2. Its power gains are largest when k - m_W is small,
  especially k - m_W = 1 (arXiv v3 PDF p. 11), which is Card's case. No public code is mentioned in the
  paper; the authors thank Andrews for his Gauss code of Andrews (2017). Andrews (2017) itself
  was not fetched.
- *twostepweakiv (Stata)* `[sun2018implementing]`: VCEs are heteroskedasticity-robust by
  default (cluster() and kernel() also available). project(varlist) gives confidence sets
  for one endogenous coefficient that treat the other endogenous coefficients as nuisance
  parameters, using the "refined projection method" (Chaudhuri and Zivot 2011) with K or LC
  tests (Table 2 of the article; AR is not in that list). strong(varlist) instead plugs in
  estimates for coefficients assumed strongly identified.

**(d) Public implementations**
- ivmodels (Python) `[ivmodelsapi]`, `[londschien2026weak]`, `[londschien2025guide]`:
  `anderson_rubin_test(Z, X, y, beta, W=..., C=..., critical_values=...)` with W the nuisance
  endogenous regressors; critical values 'chi2' (chi-square(k - m_W), the GKMC test,
  default), 'f', or 'guggenberger'/'GKM' (the GKM19 conditional test).
  `inverse_anderson_rubin_test` returns the confidence set in closed form (a quadric;
  Londschien and Bühlmann). **No heteroskedasticity-robust option**; Londschien and Bühlmann
  (arXiv v4 p. 4): "our results do not allow for general forms of heteroskedasticity. For
  inference that is robust to heteroskedasticity, see (Guggenberger et al., 2024)". The
  documentation's AR statistic is scaled by 1/k (AR = (n-k)/k * ...), and its confidence set
  uses (k - m_W) * AR against chi-square(k - m_W) (Londschien 2025, Definition 42). The
  Econometrician should check which scaling the p-value uses.
- twostepweakiv (Stata, SSC) for robust refined-projection sets, as above.
- No Python implementation of the heteroskedasticity-robust GKM (2024) or AR/AR test was
  found.

**Implication for the design (my reading, for the PI).** A homoskedastic subvector AR set
for Panel B col 6 with chi-square(1) (GKMC) or GKM19 critical values is directly available in
ivmodels. Because nearc4 is the only instrument for education and age, age^2 identify
experience, kappa_1 is likely large, so GKM19 and GKMC should give nearly the same set.
If the design wants heteroskedasticity robustness for Panel B, the citable choices are the
conservative projection of the robust full-vector AR (chi-square(3)), twostepweakiv's
refined projection, or GKM (2024) without public code. A robust minimum-AR statistic
compared with chi-square(1) is **not** supported by these sources (Lee 2015 via ASS;
GKM19 pp. 489-490).

## 5. Implications for the design

1. **Name the target column.** Card's "basic specification" is Table 3 Panel B column 6 /
   Table 4 row 1: IV 0.132 (0.049), OLS 0.073 (0.004) (Table 2 col 5), first stage on
   nearc4 0.365 (0.105), reduced form 0.048 (0.019), N 3010. Panel A column 5 also prints
   0.132 but with SE 0.055 and first stage 0.320 (0.088); its OLS counterpart is Table 2
   col 2, 0.075 (0.003). H1's targets must name table, panel and column.
2. **(F1) Which column for H2-H5.** Panel A column 6 (0.140 (0.055); first stage 0.322
   (0.083); reduced form 0.045 (0.018); OLS counterpart Table 2 col 5, 0.073 (0.004)) has one
   endogenous regressor *and* keeps the 14 family-background controls. Of Card's columns it
   is the closest single-endogenous analogue of the basic specification. Panel A col 5 is
   the column Cinelli and Hazlett, Bi et al., Delbianco and Blandhol et al. use, so running
   both, with col 6 primary, allows a direct comparison with published numbers. Carr and
   Kitagawa do not reject validity only with the full covariate set. That is weak, indirect
   support for col 6, because their test concerns a model with education binarised at 16+
   years, not Card's multi-valued schooling.
2b. **Panel B has three endogenous regressors.** Stock-Yogo (n = 1, 16.38) and the MOP
   effective F (one endogenous regressor) do not apply directly to Panel B, and Stock-Yogo
   tabulates nothing for n = 3. Options to fix before results: (a) run H2-H3 on the Panel A
   specifications (single endogenous regressor) and say so; (b) for Panel B, partial out or
   use a conditional first-stage statistic and subvector AR (methods I have not verified;
   the Scout would need to fetch e.g. Sanderson-Windmeijer before they are cited); or
   (c) follow Kling's column 4, which drops the experience quadratic, and check whether that
   still leaves more than one endogenous regressor (it does: linear experience instrumented
   by age). Option (a) is the simplest defensible choice.
3. **Expected strength.** **[Scout arithmetic]** from printed t-ratios (non-robust): Panel A
   col 1 F = (0.320/0.088)^2 = 13.2; col 2 (0.322/0.083)^2 = 15.1; Panel B col 1
   (0.382/0.114)^2 = 11.2; col 2 (0.365/0.105)^2 = 12.1. Bi et al. report 13.322 and 15.081
   for Panel A. All are below 16.38 and 23.11. H2's decision rule is fixed already; this is
   only to warn that "below threshold" is the likely outcome, which makes H3 the main
   inferential result.
4. **SE formula.** Pre-specify conventional SEs for the H1 comparison (the evidence in
   section 1 points that way) and robust SEs for H2-H5.
5. **Sample.** Non-missing `lwage76` (3010) in `nls.dat`; unweighted; do not re-trim.
6. **Controls.** Panel A without family background: `black reg76r smsa76r smsa66r
   reg662-reg669 exp76 exp762`; with family background add `daded momed nodaded nomomed
   f1-f8 momdad14 sinmom14`. Panel B swaps `exp76 exp762` into the endogenous list with
   `age76` and `age76^2` as instruments.
7. **H4 anchors (revised after question-r1 F1).** The reduced form of the *same* column is the
   denominator for "delta as a share of the reduced form": 0.045 (0.018) for Panel A col 6,
   0.042 (0.018) for Panel A col 5, 0.048 (0.019) for Panel B col 6. Card's Table 5
   direct-effect estimates (0.015 (0.029) col 3; 0.013 (0.024) col 4) come from
   experience-endogenous models with family background and nearc4 x parental-education
   instruments, i.e. Panel-B-type models; they are a reference scale only for a Panel B
   analysis, and should not be presented as belonging to a Panel A analysis.
   - **[Scout arithmetic] What H4 can find.** With one instrument, subtracting Z gamma0 from Y
     moves the reduced-form coefficient to (lambda_hat - gamma0) and leaves the first stage
     unchanged. The AR test of beta = 0 for outcome Y - Z gamma0 is the t-test of
     lambda_hat - gamma0 = 0. So an AR-based union over gamma0 in [0, delta] first includes
     0 at delta* = lambda_hat - z_{0.975} se(lambda_hat), the lower 95% limit of the reduced
     form. From the printed (conventional) numbers: Panel A col 6, 0.045 - 1.96 x 0.018 =
     0.0097; col 5, 0.042 - 1.96 x 0.018 = 0.0067 (Cinelli and Hazlett print the reduced-form
     lower limit 0.007); Panel B col 6, 0.048 - 1.96 x 0.019 = 0.0108. The Wald-based CHR
     union the plan names gives a different number and is not weak-IV robust. This agrees
     with Steiner et al.: the sign survives a = 0.01 and not a = 0.02. H4's breakdown point
     is therefore close to a function of numbers already printed. The rerun adds the robust
     standard error and the exact column.
8. **H5.** Card already reports non-rejection (fn 17; Hausman-Wu 1.24 for the over-identified
   model). The robust control-function test plus MDE adds a power statement.
9. **Interpretation (revised after literature-r1 L1).** What the sources support, with their
   conditions:
   - Angrist and Imbens (1995; abstract of NBER TP 127): under IV independence assumptions
     and "mild regularity", 2SLS with a variable treatment estimates "a weighted average of
     per-unit causal effects" (the average causal response). The abstract names no
     monotonicity, covariate or complier condition. Cite it only for the general ACR
     reading.
   - Kling (2001, WP p. 4): with proximity independent of the unobservables *conditional on
     X*, the 2SLS coefficient is "a weighted average of the heterogeneous marginal benefits
     for those whose schooling choice are affected by the instrument, conditional on X";
     monotonicity gives the ACR reading. The conditional, complier-weighted wording rests on
     Kling alone.
   - But Card's covariates enter linearly. Blandhol et al. show that linear 2SLS has that
     weakly causal reading only under "rich covariates", and their RESET test rejects it for
     Panel A col 5 (p = 0.000). Their LATE/ACR estimates (0.067 DDML, 0.085 IPSW) are well
     below 0.132. Tübbicke (2023) finds 2SLS 50-100% above propensity-score IV estimators on
     a binarised ("some college") version of these data and attributes the gap to
     conditional-variance weighting. Monotonicity is questioned too: Tübbicke, reporting
     Słoczyński (2021), shows that accounting for defiers lowers the saturated 2SLS from
     0.570 to 0.289, and Słoczyński, Uysal and Wooldridge name failures of monotonicity.
   - Wording the sources support: "under monotonicity and a correctly specified (rich)
     covariate adjustment, a positively weighted average of returns for men whose schooling
     responds to proximity; Blandhol et al. reject rich covariates for Card's Panel A
     column 5, and monotonicity is questioned on these data (Tübbicke reporting Słoczyński;
     Słoczyński et al.), so even this reading is not guaranteed here". Attribute the
     conditions to Kling (2001) and the general ACR reading to Angrist and Imbens (1995).
     Never "the average return".
     Whether Blandhol et al.'s test also rejects for col 6 (with family background) is not
     reported.
10. **Citations.** Cite WP 4483 for numbers; mention the 1995 chapter in prose via Card
    (2000) (section 0); say the codebook's "WP 4832" citation is an error.

## 6. Novelty verdict (revised 2026-11-20 after question-r1 F2)

**Already answered as a replication. The robustness layer is also largely answered on
Panel A column 5. What remains is narrow: the heteroskedasticity-robust versions, the
specification with family background (Panel A col 6), and a logged rerun.**

- **Replication (H1): answered.** The estimates have been reproduced from these data by
  Kling (2001; Panel B col 6 and Table 2 col 5, "exactly"), Bi, Kang and Taylor (2020;
  Panel A cols 5-6), Blandhol et al. (2025; Panel A col 5, robust SE 0.054) and Delbianco
  (2026; Panel A col 5, F 13.3).
- **Weak-IV-robust inference (H2-H3): answered for Panel A col 5 with homoskedastic errors.**
  Cinelli and Hazlett (Biometrika 2025) report the AR 95% interval **[0.025, 0.285]**
  (t = 2.33) on exactly that column. It excludes 0, and its lower end lies below Card's OLS
  (0.075), so by H3(b) the "IV exceeds OLS" claim would not survive in col 5 (my reading of
  their interval, not their statement). Kang et al. give a homoskedastic AR set for a reduced
  control set; Londschien (2025) gives subvector AR/CLR sets for an over-identified
  Panel-B-type model with family background. Implied conventional first-stage F values of
  13.3 (col 5) and 15.1 (col 6) are published (Bi et al.; Delbianco).
- **Exclusion sensitivity (H4): answered in two parametrisations, neither of them CHR on
  Card's exact column.** Cinelli and Hazlett: partial-R2 parametrisation on col 5, RV 0.67%,
  XRV 0.05%; a side-effect or confounder as strong as SMSA or black gives [-0.02, 0.40].
  Steiner et al.: direct-effect parametrisation (alpha in [0, a]) on a near-Card
  specification with family background and marital status; the sign holds at a = 0.01 and
  not at a = 0.02.
  Other work on exclusion in these data (a selection, section 3): principal-stratification
  analyses that drop exclusion (Jiang, Yang and Ding 2022; Luo et al. 2024) find no
  significant direct effect for always- and never-takers, with the intermediate variable
  "education beyond high school" and wide intervals; testable-implication tests (Carr and Kitagawa 2021) do not
  reject with full covariates. None of these bounds the return on Card's specification.
- **Not found in either search round** (absence in a limited search, not proof): (i) a
  heteroskedasticity-robust AR set; (ii) the MOP effective F against 23.11; (iii) a
  frequentist CHR union-of-intervals breakdown point; (iv) any of the above on Panel A
  column 6, the single-endogenous specification with family background; (v) a robust
  control-function test with an MDE (H5).
- **What the contribution sentence in plan.json should say** (the PI's call; I change
  nothing in plan.json): the replication and the homoskedastic AR set and partial-R2
  sensitivity for Panel A col 5 are published (Cinelli and Hazlett 2025). This paper adds
  the heteroskedasticity-robust AR set and effective F, a CHR delta breakdown point (which
  with one instrument equals the lower limit of the reduced-form interval when done with
  AR, section 5 item 7), both on Panel A col 6 as well as col 5, in a logged rerun that
  sets its numbers next to Cinelli and Hazlett's. The current sentence ("none of the three
  was reported on Card's own specification") is literally true only for the robust and CHR
  versions and would mislead readers. It should be rewritten.

## 7. Unverified or not reached

- The 1995 chapter's text, its table and column numbering, and the claim that its tables
  are identical to WP 4483. Card (2000) confirms only the headline numbers; Kling's column
  labels suggest the numbering may differ. The chapter was dropped from refs.bib.
- Angrist and Imbens (1995): only the abstract of the 1992 NBER version was read (OCR); the
  JASA text, including its exact monotonicity condition, was not.
- Słoczyński (2021/2026), Tan (2006), Kédagni (2021): not fetched.
- The journal versions of Kling (2001), Montiel Olea and Pflueger (2013), Conley, Hansen
  and Rossi (2012), Lee et al. (2022) and Andrews, Stock and Sun (2019): I read working-paper
  or accepted-manuscript versions (noted per key in sources.json).
- The published Stock and Yogo (2005) chapter text and its table numbering ("Table 5.2");
  16.38 is from the 2002 NBER version.
- Kitagawa (2015) full text; its result on Card's data is second-hand from Carr and Kitagawa.
- Anderson and Rubin (1949): DOI resolved only.
- Subvector inference: GKMC (2012) abstract only (its chi-square(k - m_W) result is quoted
  from GKM19 and ASS); Dufour and Taamouti (2005), Andrews (2017/2018), Chaudhuri and Zivot
  (2011), Lee (2015) and Kleibergen (2021) not fetched; GKM (2024) read in arXiv v3 only;
  Sanderson-Windmeijer and Kleibergen-Paap rank statistics not fetched.
- Cinelli and Hazlett (2025): the typeset Biometrika version and its Supplementary Material
  (separate reduced-form and first-stage analyses) were not read; the numbers come from the
  NSF PAR accepted manuscript and the 2026-02-09 vignette, read through WebFetch (first
  100,000 of 217,129 characters; the bounds table is in that part).
- Steiner et al. and Delbianco: arXiv versions only (v3 July 2026; v2 September 2026); no
  peer-reviewed version found on Crossref.
