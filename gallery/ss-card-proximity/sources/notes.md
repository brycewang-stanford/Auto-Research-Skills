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
  (DOI 10.3386/w4483; title page fetched; Crossref agrees). The published version is the
  chapter in *Aspects of Labour Market Behaviour: Essays in Honour of John Vanderkamp*, ed.
  L. N. Christofides, E. K. Grant and R. Swidinsky, University of Toronto Press, 1995,
  pp. 201-222 `[card1995chapter]`.
- I could not reach the 1995 chapter's text. Its existence and bibliographic details come
  from a library catalogue record and two secondary reference lists; the claim that it has
  "the same title and identical tables" is Card's own (codebook). **All numbers below are
  from WP 4483.** Page numbers are WP 4483's printed page numbers (text) or its PDF page
  numbers (tables, which are unnumbered); the chapter's page numbers are unknown.
- The paper should cite `card1993nber` for every number and `card1995chapter` as the
  published version, and say that the tables were read from the working paper.

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
| Kling (2001) `[kling2001interpreting]` (WP 7989, Table 1, p. 20) | Replicates Card "exactly": OLS .073 (.003); IV .132 (.049); age 14-19 IV .094 (.064), N=2037; dropping the experience quadratic gives .133 (.049). Gives the sample rule ($1-$30 wages; 49 obs with missing 1966 interview month). Then characterises the men whose schooling responds to proximity. | H1 has been done before and the specification is reproducible. Kling's OLS SE (.003) differs from Card's (.004). His column labels "T2-c2" and "T3-c5B" do not match his own specification (which includes family background, i.e. Card's T2 col 5 and T3 Panel B col 6). |
| Blandhol, Bonney, Mogstad, Torgovitsky (2025) `[blandhol2025tsls]` (sec. 6.1, Table 3, Tables SA.3-SA.4) | Reproduce Panel A col 5: OLS 0.075 (0.004); IV without covariates 0.188 (0.026); IV with covariates 0.132 (0.054), robust SEs; N = 3,010. RESET test of "rich covariates" p = 0.000; DDML estimate of the rich-covariates estimand 0.122 (0.053); LATE/ACR 0.067 (0.046) (DDML) and 0.085 (0.049) (IPSW). | With additive covariates, TSLS here need not be a weighted average of LATEs. Supports the seed requirement not to call the IV the average return, and suggests a note that it is not even guaranteed to be a positively weighted LATE. (Their text says proximity is measured "when the respondent was 14 years old" and calls the survey "NLSY"; Card says 1966 and NLSYM.) |
| Bi, Kang, Taylor (2020) `[bi2020inferring]` (sec. 6.1, Table 1) | Reproduce Panel A cols 5-6: 0.132 (0.055), 95% CI [0.024, 0.239], F = 13.322; 0.140 (0.055), CI [0.033, 0.248], F = 15.081. Conditional on passing an F > 10 pre-test, CIs become [-0.094, 0.357] and [-0.072, 0.327]. | First-stage F in the Panel A specifications is below 16.38 and well below 23.1; conventional significance is fragile. They attribute an "F around 14" to Card; Card's paper reports no F (it is implied by his t). |
| Kang, Jiang, Zhao, Small (2021) `[kang2021ivmodel]` (arXiv v2 sec. 7) | Card example with Wooldridge's `card` data and a reduced control set (exper, expersq, black, south, smsa; no region 1966, SMSA 1966 or family background): first-stage F = 16.72; TSLS 0.132289 (0.049233); homoskedastic AR 95% CI [0.0384, 0.2612]; CLR the same. | The closest published AR result, but not Card's specification and not heteroskedasticity-robust. That the TSLS point estimate and SE coincide with Card's Panel B col 6 is a coincidence of a different model; it is not a replication target. |
| ivmodels documentation `[ivmodelscard]`; Londschien (2025) `[londschien2025guide]` (arXiv v1, sec. 2.1, 3.1, 4, 6; same numbers in both) | Card's `proximity.zip` data, n = 3010; ed76, exp76, exp762 endogenous; instruments nearc4a, nearc4b, nearc2, age76, age76^2 (over-identified, not nearc4 alone); family background, region and race as exogenous controls. OLS 0.072634; TSLS 0.144954; LIML 0.172352. Subvector tests of beta = 0 for education: AR 5.07 (p 0.0016), CLR 10.93 (p 0.0024). 95% sets: Wald (TSLS) [0.058, 0.232], AR [0.083, 0.352], CLR [0.073, 0.396], LM [-0.594, -0.059] U [0.061, 0.467]. Cragg-Donald rank statistic 15.613. Homoskedastic methods throughout (no mention of heteroskedasticity). | A published weak-IV-robust (subvector AR/CLR) analysis of a Panel-B-type model with family background, but with different instruments and non-robust errors. Shows subvector inference with experience endogenous is feasible. The documentation page has no author; the guide shows it is Londschien's package and example. |
| Kitagawa (2015) `[kitagawa2015test]`; Carr and Kitagawa (2021) `[carr2021testing]` (sec. 5.1) | Testable-implication tests of instrument validity with education binarised at 16+ years. Per Carr and Kitagawa: Kitagawa (2015) rejects validity without covariates; earlier tests (Huber and Mellace 2015, Mourifie and Wan 2017, Sun 2021) used at most five covariates; with Card's full covariate set Carr and Kitagawa do not reject. | Validity is conditional on covariates, so the control set matters for H3-H4. The Kitagawa (2015) result is cited second-hand (abstract page only). |
| **Cinelli and Hazlett (2025)** `[cinelli2025omitted]` (Biometrika accepted manuscript, sec. 2 and sec. 5, Table 2, Fig. 1); package vignette `[ivsensemakr]` | Running example: Card's data, n = 3,010; outcome log hourly wage, treatment education, instrument nearc4; covariates (vignette code) exper, expersq, black, south, smsa, reg661-reg668, smsa66 = **Card Table 3 Panel A column 5** (no family background); classical (homoskedastic) standard errors (manuscript p. 6); df = 2994. Table 2 ("Minimal sensitivity reporting", manuscript p. 16): IV 0.132, **Anderson-Rubin 95% CI [0.025, 0.285]**, t = 2.33, XRV 0.05%, RV 0.67%; first stage 0.320, CI [0.148, 0.492], t = 3.64, XRV 0.31%, RV 3.02%; reduced form 0.042, CI [0.007, 0.078], t = 2.33, XRV 0.05%, RV 0.67%. OLS 7.5% (vignette 0.07469326, CI [0.0678, 0.0816]). Bound "1x SMSA": partial R2 with outcome 2%, with instrument 0.6%, bias-adjusted critical value 2.55 > 2.33. Text (p. 16): confounding as strong as SMSA or black gives an interval of [-0.02, 0.40]. Vignette bounds: 1x black R2zw.x 0.00221, R2y0w.zx 0.0750, CI [-0.0212, 0.402], critical 2.59; 1x smsa 0.00639, 0.0202, CI [-0.0192, 0.396], critical 2.57. The method covers exclusion violations ("side-effects") and instrument confounding with the same algebra (sec. 5, p. 15). | **Answers the substance of H3 and H4 on Panel A column 5**: a weak-IV-robust (homoskedastic AR) interval that excludes 0, and a sensitivity analysis showing the sign is not robust to a confounder or side-effect as strong as SMSA or black. The robustness value of the IV equals that of the reduced form: the IV conclusion hinges on the reduced form. The paper (2.55) and the 2026 vignette (2.57) give slightly different SMSA critical values; quote the version you cite. |
| Steiner, Houssineau and Steel (2025/2026) `[steiner2025possibilistic]` (arXiv v3, sec. 5.3, Table 5, Fig. 2b) | Card's data; outcome log hourly wage, treatment years of schooling, instrument nearc4; covariates partialled out "including experience, experience squared, family background, marital status, race, region, and parents' education" (imputed by the mean with missingness indicators): **not Card's exact column** (adds marital status). Direct effect of proximity alpha restricted to A = [0, a]. With A = {0} the posterior mode is "just below 0.15" and the effect is significant; with A = [0, 0.02] and [0, 0.04] the uncertainty intervals include zero. Lower/upper probabilities of beta > 0 (Table 5): a = 0, 0.01, 0.02, 0.03, 0.04 give lower 1, 1, 0.887, 0.748, 0.517; upper 1 throughout. | A published exclusion-restriction sensitivity analysis in the direct-effect (gamma) parametrisation that H4 uses, on a near-Card specification with family background: the positive return survives a 1-point direct effect and not 2 points. Not frequentist CHR, and covariates differ. |
| Delbianco (2026) `[delbianco2026testing]` (arXiv v2, sec. 5, Table 2) | n = 3010, data "from Wooldridge, 2010"; "Card's covariates" = experience and its square, race, South, SMSA, SMSA in 1966, region dummies (Panel A col 5). First stage 0.320, first-stage F 13.3, OLS 0.075, IV 0.132 (0.055). A fourth-cumulant test of exclusion: p = 0.970 with Card's covariates, but the identification diagnostic shows the test is uninformative ("consistent with exclusion and equally with sizeable violations"). | Another reproduction of Panel A col 5 (F 13.3). No usable bound on the direct effect. |
| Słoczyński, Uysal and Wooldridge (2024) `[sloczynski2024abadie]` (arXiv v4, sec. 4.2, Table 3) | Binarised treatment (13+ or 16+ years); Card's covariates without family background (quadratic experience, nine regional indicators, black, SMSA 1966 and 1976, South 1976). 2SLS (robust SE): some college 0.661 (0.294); college completion 1.392 (0.798). | Reanalysis of a different (binary) estimand; says many estimates are "too large", possibly because of failures of exclusion and monotonicity. Context only. |

Not verified (named by the sources above, not fetched by me): Huber and Mellace (2015),
Mourifie and Wan (2017), Sun (2021), Andresen and Huber (2021), Słoczyński (2021), Tan
(2006), Cameron and Taber (2004), Carneiro, Heckman and Vytlacil (2011), Heckman et al.
(2018), Angrist and Imbens (1993/1995), Cinelli and Hazlett (2020). Do not cite them without
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
   Kitagawa do not reject validity only with the full covariate set, which also favours
   col 6.
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
9. **Interpretation.** IV is a weighted average of returns for men whose schooling responds
   to proximity (Card fn 10, 12; Kling), and with additive covariates may not even be a
   positively weighted LATE (Blandhol et al.). Use "return for men whose schooling responds
   to proximity", never "the average return".
10. **Citations.** Cite WP 4483 for numbers, with the 1995 chapter as the published version;
    say the codebook's "WP 4832" citation is an error.

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

- The 1995 chapter's text, page numbers of its tables, and the claim that its tables are
  identical to WP 4483 (only Card's codebook says so).
- The journal versions of Kling (2001), Montiel Olea and Pflueger (2013), Conley, Hansen
  and Rossi (2012), Lee et al. (2022) and Andrews, Stock and Sun (2019): I read working-paper
  or accepted-manuscript versions (noted per key in sources.json).
- The published Stock and Yogo (2005) chapter text and its table numbering ("Table 5.2");
  16.38 is from the 2002 NBER version.
- Kitagawa (2015) full text; its result on Card's data is second-hand from Carr and Kitagawa.
- Anderson and Rubin (1949): DOI resolved only.
- Methods for weak-IV-robust inference with several endogenous regressors
  (Sanderson-Windmeijer, Kleibergen-Paap, Guggenberger et al. 2012 subvector AR) were not
  fetched. Londschien (2025) describes them but is not the primary source.
- Cinelli and Hazlett (2025): the typeset Biometrika version and its Supplementary Material
  (separate reduced-form and first-stage analyses) were not read; the numbers come from the
  NSF PAR accepted manuscript and the 2026-02-09 vignette, read through WebFetch (first
  100,000 of 217,129 characters; the bounds table is in that part).
- Steiner et al. and Delbianco: arXiv versions only (v3 July 2026; v2 September 2026); no
  peer-reviewed version found on Crossref.
