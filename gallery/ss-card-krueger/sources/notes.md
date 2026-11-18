# Scout notes: ss-card-krueger (task q-novelty)

Compiled by the Scout on 2026-11-19. Every number below was read from a fetched document,
and its location is given next to it. Arithmetic marked **[Scout arithmetic]** is my own
check on published numbers, not a claim made by any source. I did not open the seed's
`answer.json`, and I did not download `njmin.zip`.

## 1. Target: Card and Krueger (1994), AER 84(4): 772-793 `[card1994minimum]`

Source read: the author-hosted scan of the published article
(davidcard.berkeley.edu/papers/njmin-aer.pdf). The text was extracted with pdftotext. The
table cells are missing from the text layer, so Tables 3, 4 and 5 were read from page images
(journal pp. 780 and 783). The NBER working paper version (WP 4509, Oct 1993)
`[card1993nber]` reports the same headline numbers in its Table 3: 2.76, and 2.75 in the
balanced sample.

### Setting and sample (Section II, Table 1, p. 774-775)

- New Jersey's minimum wage rose from $4.25 to $5.05 on 1 April 1992. Pennsylvania's stayed
  at $4.25.
- Chains: Burger King, KFC, Wendy's, Roy Rogers. Area: New Jersey and eastern Pennsylvania.
- Wave 1: 15 Feb - 4 Mar 1992. 410 stores interviewed (331 NJ, 79 PA) out of 473 in the
  sample frame.
- Wave 2: 5 Nov - 31 Dec 1992, and only the 410 wave-1 respondents were contacted. 399 were
  interviewed (321 NJ, 78 PA). Six stores closed permanently (5 NJ, 1 PA). Two were under
  renovation and two were temporarily closed (all NJ), and one NJ store refused. The paper
  counts "four temporarily closed stores": the 2 under renovation plus the 2 temporarily
  closed.

### Definition of full-time-equivalent employment

- Text (p. 775): FTE = "the number of full-time workers [including managers] plus 0.5 times
  the number of part-time workers".
- Table 5 notes b-d (p. 783) make clear that the base measure counts managers and assistant
  managers in full. The 0.4 and 0.6 variants are "managers, assistant managers, and full-time
  nonmanagement workers, plus 0.4 [0.6] times the number of part-time nonmanagement workers".
- Treatment of closures (Table 3 notes): wave-2 employment at the six permanently closed
  stores is set to **0**. At the four temporarily closed stores it is **missing**. Row 5 is
  the only exception and sets them to 0.
- Mamula `[mamula2021replicating]` maps this to the public-file variables as
  `empft + nmgrs + 0.5*emppt`, with `empft2`, `nmgrs2` and `emppt2` for wave 2. I have not
  seen the codebook, so the Econometrician must check these names against `codebook` in the
  zip.

### Published headline: Table 3, "Average employment per store before and after the rise" (p. 780)

Standard errors are in parentheses. Rows 1-3 use "all stores with available data on
employment".

| Row | PA (i) | NJ (ii) | NJ-PA (iii) |
|---|---|---|---|
| 1. FTE before, all available obs | 23.33 (1.35) | 20.44 (0.51) | -2.89 (1.44) |
| 2. FTE after, all available obs | 21.17 (0.94) | 21.03 (0.52) | -0.14 (1.07) |
| 3. Change in mean FTE | -2.16 (1.25) | 0.59 (0.54) | **2.76 (1.36)** |
| 4. Change in mean FTE, balanced sample | -2.28 (1.25) | 0.47 (0.48) | **2.75 (1.34)** |
| 5. As row 4, temporarily closed set to 0 | -2.28 (1.25) | 0.23 (0.49) | 2.51 (1.35) |

- Text (p. 779): the relative gain "is 2.76 FTE employees (or 13 percent), with a t
  statistic of 2.03".
- Within NJ (cols iv-viii), by wave-1 starting wage: $4.25 (N=101), $4.26-4.99 (N=140),
  >= $5.00 (N=73). The changes in row 3 are 1.32 (0.95), 0.87 (0.84) and -2.04 (1.14).
  Low-minus-high is 3.36 (1.48) in row 3 and 3.36 (1.30) in row 4.
- The balanced sample (note c) is the "subset of stores with available employment data in
  wave 1 and wave 2".
- **[Scout arithmetic]** The SE in column (iii) equals sqrt(SE_PA^2 + SE_NJ^2), which treats
  the two states as independent: sqrt(1.25^2+0.54^2)=1.36, sqrt(1.25^2+0.48^2)=1.34 and
  sqrt(1.35^2+0.51^2)=1.44. The SE of the PA change, 1.25, is smaller than
  sqrt(1.35^2+0.94^2)=1.64. So the within-state change SEs allow for the correlation between
  waves at the same store, and do not treat the waves as independent samples.
- **[Scout arithmetic]** From the rounded entries, 0.59-(-2.16) = 2.75. The published 2.76
  therefore comes from unrounded means, so a replicated 2.75 or 2.76 is only a rounding
  difference.

### Published regressions: Table 4, "Reduced-form models for change in employment" (p. 780)

Sample: **357 stores** "with available data on employment and starting wages in waves 1
and 2". Dependent variable: change in FTE. Its mean is -0.237 and its SD is 8.825.

| | (i) | (ii) | (iii) | (iv) | (v) |
|---|---|---|---|---|---|
| NJ dummy | 2.33 (1.19) | 2.30 (1.20) | - | - | - |
| Initial wage gap | - | - | 15.65 (6.08) | 14.92 (6.21) | 11.91 (7.39) |
| Chain + ownership controls | no | yes | no | yes | yes |
| Region controls | no | no | no | no | yes |
| SE of regression | 8.79 | 8.78 | 8.76 | 8.76 | 8.75 |

- GAP = 0 in PA and in NJ stores with a wave-1 starting wage >= $5.05. Otherwise it is
  (5.05 - W1)/W1 (p. 779). The mean GAP in NJ is 0.11, so col (iii) implies +1.72 FTE (p. 781).
- p. 779: column (i) is "directly comparable" to Table 3, but it is smaller because of the
  restricted 357-store sample.

### The authors' own robustness checks: Table 5 (p. 783)

These are the NJ dummy in change-in-employment models, all with chain and ownership
controls. Base: 2.30 (1.19).

| Check | NJ dummy |
|---|---|
| Temporarily closed stores treated as closed | 2.20 (1.21) |
| Exclude managers | 2.34 (1.17) |
| Part-time weight 0.4 | 2.34 (1.20) |
| Part-time weight 0.6 | 2.27 (1.21) |
| Exclude 35 NJ shore stores | 2.58 (1.19) |
| Wave-2 interview-week dummies | 2.27 (1.20) |
| Exclude 70 stores called >2 times in wave 1 | 2.41 (1.28) |

The weighted proportional-change model gives 0.13 (0.05), a 13 percent relative increase.

## 2. Later critique: Neumark and Wascher, payroll data

### NBER WP 5224 (Aug 1995) `[neumark1995payroll]`, full text (OCR) read, abstract and pp. 1-6

- **What they did:** collected administrative payroll records (non-management hours,
  converted to FTE at 35 hours/week) from Burger King, KFC, Wendy's and Roy Rogers
  restaurants in the zip-code areas of CK's sample. The abstract counts 230 restaurants. The
  first 71 observations came from the Employment Policies Institute (EPI). NW took over
  collection later "to avoid conflicts of interest" (p. 5).
- **Finding 1, data quality (abstract, p. 1):** the standard deviation of employment change
  in CK's data is about three times that in the payroll data. The 90-10 range is 2.6 times as
  large. On p. 3 the largest changes in CK's data are -41.5 and +34 FTE. The SD of the change
  is 8.4 in NJ and 10.8 in PA.
- **Finding 2, effect (abstract, p. 2):** on the matched subset, CK's data imply a +17.6%
  relative NJ employment increase, an elasticity of 0.93. The payroll data give a **4.6%
  relative decrease**, significant at 5%, with an elasticity of **-0.24**. The range across
  sensitivity checks is -0.18 to -0.27.
- **Their CK baseline (p. 3, Table 1 panel A):** excluding closed stores, the DiD with chain
  and ownership controls is 2.78 FTE, an implied elasticity of 0.70. NJ +0.66 and PA -2.1.
  Footnote 2 says it differs slightly from CK Table 3 *because closed stores are excluded*.
- **Data facts relevant to us (p. 4 fn 6, p. 6):** "CK's data set does not include a unique
  restaurant identifier (such as an address)". It has only the first three digits of the zip
  code. Footnote 6 also says the public data set "does not include the date of the interview
  in the first wave of the survey".

### AER 2000 Comment `[neumark2000comment]`, metadata only

The published comment is AER 90(5): 1362-1396. I verified its DOI and bibliographic data,
but the full text is paywalled and neither AEA nor IDEAS shows an abstract. **I make no
claim about its content.** Anything said about the NW critique should cite the 1995 working
paper, and the paper should note that the published version used an expanded sample (CK's
reply says later versions added NW's own data collection).

## 3. Card and Krueger's reply: BLS ES-202 data

### NBER WP 6386 (Jan 1998) `[card1998reanalysis]`, full text (OCR) read, abstract, intro, Section I.A

nber.org says this is the working-paper version of the AER 2000 Reply
`[card2000reply]`. Card's website lists this PDF under the AER 2000 citation.

- **BLS ES-202 data (abstract, pp. 1-3):** UI payroll records for a set of large chains in NJ
  and eastern PA. The longitudinal file has 687 establishments (p. 6) and there are also
  repeated cross-sections for 1991-1996. Both show "similar or slightly faster employment
  growth in New Jersey relative to eastern Pennsylvania". In most specifications the
  difference is "small and statistically insignificant" (p. 3).
- **1996 federal increase (abstract):** this increase was binding in PA but not NJ. They find
  "no indication of relative employment losses in Pennsylvania".
- **On the NW/EPI sample (abstract, pp. 3-4):** the discrepancy comes from the Pennsylvania
  restaurants. Those are "a small set of restaurants owned by a single franchisee" who
  supplied the whole EPI PA sample. Employment trends also differ by reporting interval
  (weekly, biweekly or monthly). After controlling for reporting interval, the pooled sample
  "shows no difference in hours growth between New Jersey and Pennsylvania".
- **Data access:** the ES-202 data are confidential (title page). The NW payroll data are not
  in the public file either. **Neither payroll data set can be used to replicate from public
  data.**
- **Sample geography (p. 6):** CK's original PA sample covers 7 counties: Bucks, Chester,
  Lackawanna, Lehigh, Luzerne, Montgomery, Northampton.

### AER 2000 Reply `[card2000reply]`, metadata only

AER 90(5): 1397-1420, DOI verified. Full text is paywalled, so I make no claim about how it
differs from WP 6386.

## 4. Inference with one treated state `[conley2011inference]` (abstract only)

Conley and Taber (REStat 2011; NBER TWP 312, 2005). With a small number of policy changes,
the point estimator of the treatment effect "should not be thought of as being consistent".
They propose inference based on estimating the finite-sample distribution of the estimator,
and the abstract says that "in some cases the standard approach can give misleading
results". CK's design has exactly one treated state and one control state. Its published
SEs are cross-store sampling SEs, which ignore state-level shocks. The paper should say
this in its limitations and should not present the t-statistic of 2.03 as design-based
evidence.

## 5. Prior replications and reanalyses from the public data

- **Data documentation `[card_njmin_readme]`:** `njmin.zip` holds `public.dat` (410 obs), a
  `codebook`, a SAS program "to read the data and create some of the key tabulations", and
  the texts of the two survey instruments. The readme says the files pertain to "the surveys
  used in Card and Krueger's book Myth and Measurement, chapter 2". **The SAS program is
  the authors' own tabulation code. The Econometrician should read it before coding the FTE
  and sample rules.**
- **Mamula (2021) `[mamula2021replicating]`, an informal R replication from `njmin.zip`:**
  - Table 3 means reproduce exactly: PA 23.33 to 21.17, NJ 20.44 to 21.03.
  - The DiD is **2.75**. The author's SE is 1.59, against the published 1.36. The NJ-PA
    level SEs are also off (1.36 vs 1.44 and 1.21 vs 1.07), and the author "can't quite
    figure out" why. My arithmetic in §1 points to the cause: the published column-(iii) SEs
    are sqrt(SE_PA^2+SE_NJ^2), and the change SEs account for the panel correlation.
  - Store counts with non-missing FTE: PA 77 in both waves, NJ 321 before and 319 after.
  - Table 4 was not reproduced exactly. N was 351 or 370 against the published 357, and the
    NJ dummy was 2.28 or 2.16 against 2.33. The author could not reconstruct the "available
    employment and starting wage" sample and did not use the SAS file.
- **Morshed (2025) `[morshed2025replication]`, OSF preprint, 4 pp., full text read; not peer
  reviewed:**
  - The data file is "Card-Krueger-1994-data.dta", described as 410 stores. The preprint does
    not say where the file came from.
  - **It does not reproduce the published numbers**, and it does not note or explain the
    gaps. The reported DiD is 3.36 (SE "approximately 1.68") against 2.76 (1.36). The
    balanced-sample DiD is 3.44 against 2.75. Setting temporarily closed stores to zero gives
    3.28 against 2.51. The Table 4 NJ dummy is "approximately 2.94" against 2.33.
  - Its wave-1 FTE means are 7.72 (NJ) and 10.21 (PA), against 20.44 and 23.33 in CK
    Table 2/3. This points to a different employment measure or a different data file.
  - It reports **no N for Table 4**, so it says nothing about the 357-store sample.
  - It does no winsorization or trimming. Its extension is the within-NJ wage-group split:
    low-minus-high 1.90 against CK's 3.36.
  - **Bearing on the contribution:** it does not weaken the claim that no public replication
    reproduces the published SEs or N = 357. It is one more replication that misses them.
- **Ropponen (2010) `[ropponen2010cic]`, MPRA 25181 / HECER DP 289, full text read:**
  - **Data:** "the original Card and Krueger (1994) data", obtained from the Princeton IRS and
    MIT/Angrist (MHE) websites (fn 6). He keeps stores with complete employment data, as CK
    do. FTE = managers + full-time + 0.5 part-time (p. 4).
  - **Balanced sample (fn 8):** in his words, "the balanced sample in CK includes 309
    observations on fast-food restaurants in New Jersey and 75 in Pennsylvania", 384 in
    total. This is his count, not a number printed in CK.
  - **Replication:** the DiD on this sample is **2.72**, against CK's 2.75 in Table 3 row 4
    (p. 10).
  - **Changes-in-changes (Athey-Imbens 2006):** the average effect is **0.90** (bootstrap SE
    0.44) on 301 NJ + 75 PA stores. **Eight NJ stores are dropped** because their wave-1 FTE
    lies outside the support of PA wave-1 FTE (fn 15-16). This is a support restriction
    required by the estimator, not an outlier trim. With chain, ownership and location
    controls the effect is 1.58 (SE 0.44) (fn 17).
  - **Distribution and store size:** store-level effects are plotted against wave-1 FTE. A
    lowess curve of conditional average effects crosses zero at FTE 11.5 and 24 (Fig. 3; no
    controls). With controls it turns from positive to negative at FTE 20.8 (Fig. 4). The
    conclusion (p. 13) is that effects are "positive for small and negative for big fast-food
    restaurants", so the CK result is "overturned for big fast-food restaurants". He offers a
    demand-side explanation based on store location.
- **Ropponen (2011, JAE 26(6): 1051-1057) `[ropponen2011reconciling]`, abstract only:**
  - The abstract (on IDEAS, borrowed from VATT WP 24) says the paper uses the original CK
    **and** NW (2000) datasets with the CIC estimator.
  - It says the CK result "remains valid only for small fast-food restaurants" in both
    datasets, and that this reconciles the two studies.
  - I could not read the full text: Wiley is paywalled, and doria.fi and the ZBW JAE data
    archive returned 403 or bot checks. So I cannot say whether it trims or winsorizes, or
    what its sample sizes are.
- **Ropponen (2014, Empirical Economics 46(1): 307-316) `[ropponen2014note]`, abstract only:**
  - Uses Abadie's (2005) semiparametric DiD on "the original datasets" of CK and NW.
  - Concludes that "the original findings on the overall employment effect of a minimum wage
    are fairly robust". NW's results are slightly diluted once covariate distributions are
    balanced.
  - The abstract does not mention trimming, winsorizing or outliers. I did not read the full
    text.
- Other informal replications (blog posts, course pages, RPubs) were seen in search results.
  They report the same 2.75 vs 2.76. I did not verify them and do not cite them.

### Does any of these report a winsorization or trimming check?

**None that I could read.**
- CK 1994 Table 5 has no trimming or winsorizing rows. Its sample exclusions are by location,
  call-backs and closure status.
- NW 1995 documents the extreme changes (-41.5, +34 FTE) and the 3x SD ratio. I searched
  the full 38-page OCR text for trim, outlier, winsor, median, extreme and drop. It does not
  trim or winsorize CK's data. Its only exclusion is dropping closed restaurants. It also
  states (p. 9) that **"The greater variability in CK's data is not driven by one or two
  outliers."** In the combined sample, the SD of the change is 9.6 in CK's data against 3.2
  in the payroll data, and the 90-10 range is 21.0 against 7.9.
- Ropponen 2010 drops 8 NJ stores for CIC support. That is a support restriction, not a
  winsorization of changes, and he reports no winsorized DiD.
- Morshed 2025 and Mamula 2021 do neither.
- **Not checkable:** the full texts of Ropponen 2011 and 2014, NW 2000 and CK 2000. All are
  paywalled or blocked, and their abstracts say nothing on the point.

The defensible wording is: "we found no published winsorized or trimmed estimate on these
data; we could not read the full texts of [list]; Ropponen (2010, 2011) reports a
changes-in-changes reanalysis in which the effect is positive for small stores and negative
for large ones".

**What this implies for H2:** Ropponen's result makes the H2 outcome partly predictable. If
large stores carry negative effects and the extreme negative changes sit in large stores,
then capping the tails could move the NJ-PA difference either way. The paper should report
H2 next to Ropponen's CIC result, and should not present winsorization as untouched ground.

### Search log (prior robustness checks and distributional reanalyses)

The searches behind the novelty claim, with exact terms:

| Date | Tool | Exact query | What it found that was used |
|---|---|---|---|
| 2026-11-19 | WebSearch | `Neumark Wascher 2000 "Minimum Wages and Employment: A Case Study of the Fast-Food Industry in New Jersey and Pennsylvania: Comment" pdf` | NW 1995 WP 5224; NW 2000 metadata |
| 2026-11-19 | WebSearch | `replication Card Krueger 1994 New Jersey minimum wage public data difference-in-differences reproduce 2.76 FTE` | Mamula 2021 and other informal replications |
| 2026-11-19 | Crossref API | `query.bibliographic=Minimum Wages and Employment Case Study Fast-Food Industry New Jersey Pennsylvania` | CK 1993 WP, NW 2000, CK 2000, CK 1998 WP |
| 2026-11-19 | Crossref API | `Ropponen Reconciling the evidence of Card and Krueger Neumark Wascher`; `Ropponen A note on the robustness of Card and Krueger (1994) and Neumark and Wascher (2000) Empirical Economics` | Ropponen 2011 (JAE) and 2014 (Emp. Econ.) DOIs |
| 2026-11-19 | WebSearch | `Ropponen "Reconciling the evidence of Card and Krueger (1994) and Neumark and Wascher (2000)" pdf VATT` | VATT WP 24 (blocked), JAE data archive (blocked) |
| 2026-11-19 | WebSearch | `Card Krueger 1994 New Jersey fast food winsorized OR trimmed OR outliers employment change reanalysis` | Nothing on winsorizing or trimming; CK 1998 and NW 1995 only |
| 2026-11-19 | WebSearch | `Card Krueger 1994 quantile difference-in-differences OR "changes-in-changes" OR "median regression" fast-food employment distribution` | Nothing beyond course pages and informal replications |
| 2026-11-19 | WebSearch | `"Card and Krueger" minimum wage New Jersey robustness "measurement error" survey data outliers trimmed estimates Neumark Wascher comment` | Ropponen 2014 (Abadie semiparametric DiD); nothing on trimming |
| 2026-11-19 | Direct fetch | ideas.repec.org pages for MPRA 25181, JAE 26(6), VATT WP 24/25, Emp. Econ. 46(1); api.osf.io/v2/preprints/8ut4n_v1 | Ropponen 2010 PDF, Morshed 2025 PDF, abstracts |

The Reviewer's question-r2 search found Ropponen 2010 and Morshed 2025 before I did. My
first-round searches (rows 1-3) did not target distributional or trimmed reanalyses. That
gap is what F7 identified.

## 6. Novelty verdict (updated 2026-11-19 after question-r2 F7)

**The replication part is already answered as a finding, and its value is procedural. The
robustness part is partly answered.**

- **H1 (replication):** the published targets are in CK Tables 3-4. Three informal or
  working-paper replications from the public data come close on the point estimate:
  Mamula 2.75 and Ropponen 2.72 on the balanced sample. Morshed is far off at 3.36. **None
  of the four reproduces the published standard errors or N = 357.** H1's added value is
  doing that, or explaining why it cannot be done.
- **H2 (winsorization):** I found no published winsorized or trimmed estimate on these data.
  But the distributional question has been asked. Ropponen (2010; JAE 2011) uses
  changes-in-changes and reports a smaller average effect (0.90, or 1.58 with controls,
  against DiD 2.72) and a sign change with store size. Ropponen (2014) reports that the
  average effect is "fairly robust" under semiparametric DiD. **The paper must cite these
  and present H2 as a complement to them, not as the first distributional check.**
- The substantive dispute (NW payroll vs CK BLS ES-202) used non-public data and is outside
  the scope of this replication.
- The paper must not claim to settle the minimum-wage employment effect.

**Note for the PI:** `plan.json` `question` still ends with "a check with no published
result that we found". The F7 response says this qualifier was removed, but the wording is
still there. I have not edited `plan.json`, which is not my file.

## 7. Design implications, aligned with the revised hypotheses (plan.json, question-r2)

1. **H1(a), Table 3 row 3:** 2.76 (1.36), with PA -2.16 (1.25) and NJ 0.59 (0.54). All
   stores with available employment data are used. Permanently closed stores get wave-2
   FTE = 0, and the four temporarily closed stores are missing. Wave-1 interviews: 331 NJ,
   79 PA. Wave-2 interviews: 321 NJ, 78 PA (CK Table 1). The CK text gives no per-wave counts
   of stores with non-missing FTE. Mamula's counts (PA 77/77, NJ 321/319) are a secondary,
   unverified reference.
2. **H1(b), Table 3 row 4 (balanced):** 2.75 (1.34), PA -2.28 (1.25), NJ 0.47 (0.48).
   Ropponen (2010, fn 8) counts the CK balanced sample as 309 NJ + 75 PA = 384. That is a
   secondary source, not a CK number, but the replicated count can be checked against it.
3. **H1(c), Table 4 col (i):** N = 357, NJ coefficient 2.33 (1.19). Log the store count after
   each filter. Mamula's 2.28 sits exactly 0.05 away, so the |difference| <= 0.05 rule
   matters.
4. **FTE:** full-time (including managers and assistant managers) + 0.5 x part-time. Check
   the variable names and closure coding against `codebook` and the bundled SAS program.
5. **SEs (fixed at design):** the published column-(iii) SEs match sqrt(SE_PA^2+SE_NJ^2),
   with paired within-state change SEs (my arithmetic, §1). The alternative is a store-level
   regression with robust SEs. Report both.
6. **H2 (winsorization, an implementation of NW 1995's measurement-error critique):**
   - Sample: the H1(b) balanced sample, closures = 0.
   - Cap ΔFTE at the 5th and 95th percentiles of the pooled distribution, closures included.
   - Comparator: the unwinsorized estimate on the same sample.
   - Facts the design should record before running:
     - NW's extremes (-41.5, +34 FTE) and the per-state SDs of ΔFTE (NJ 8.4, PA 10.8; NW
       1995 p. 3, closed stores excluded).
     - PA has only about 75 balanced stores, so a pooled 5% tail in PA holds very few
       stores. Report how many stores are capped in each state and each tail.
     - Ropponen's finding that effects are negative for large stores. Report the wave-1 FTE
       of the capped stores, so readers can compare with Ropponen's Figs. 3-4.
   - NW (1995, p. 9) say the excess variability is "not driven by one or two outliers".
     So by NW's own account, measurement error is spread across the distribution. A 5/95
     winsorization tests only the tail part of that critique, and the paper should say so.
   - Secondaries (reported, not judged):
     - (i) the same check with the six permanently closed stores excluded from
       winsorization;
     - (ii) NW's rule (drop closed stores, add chain and ownership controls), published
       2.78 (NW 1995 p. 3).
7. **Discussion:** set H2 beside Ropponen's CIC averages (0.90 and 1.58, against DiD 2.72)
   and his store-size pattern. Set it beside Ropponen (2014) "fairly robust" as well. The CIC
   estimator could be offered as an optional, labelled extension. It is not pre-specified and
   must not be added after results are seen.
8. **Inference:** one treated and one control state (Conley-Taber). Report the conventional
   SEs only for comparison with the paper, and record the clustering limitation as a
   deviation at design.
9. **Data limits:** there is no store identifier and no wave-1 interview date (NW 1995 fn 6).
   Neither payroll data set (NW, BLS ES-202) is public.

## Unverified (not cited)

- The **published texts** of Neumark and Wascher (2000) and Card and Krueger (2000) are
  paywalled. Only their metadata is verified, and content claims use the working papers.
- Card and Krueger (1995), *Myth and Measurement* (Princeton UP). The readme names chapter 2
  as the use of the data. The book was not fetched.
- Lavin (1995), cited by NW for problems with CK's price data, was not fetched.
- The `njmin.zip` codebook and SAS program were not read, because I did not download the
  data archive.
- Other informal replications (anthonypuggs Substack and GitHub, RPubs, course pages) were
  seen in search results only. I read the Substack post's text via WebFetch, but its tables
  are images, so it is not recorded.
- **Ropponen (2011, JAE) and Ropponen (2014, Emp. Econ.):** full texts not read. Wiley and
  Springer are paywalled, and the VATT working papers on doria.fi and the ZBW JAE data
  archive returned 403 or bot checks. They are recorded as `fetched-abstract`. Nothing is
  claimed about their samples or about whether they trim.
- **Neumark and Wascher 1995:** the full OCR text (38 pp.) was keyword-searched for
  trimming. It was read closely only for pp. 1-10.
