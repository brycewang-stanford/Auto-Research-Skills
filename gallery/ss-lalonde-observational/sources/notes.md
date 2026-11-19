# Scout notes: ss-lalonde-observational (task q-novelty)

Compiled by the Scout on 2026-11-18 (UTC). Every number below was read from a fetched document,
and the source is named next to it. I did not open the seed's `answer.json`, and I did
not download the study data. All dollar figures are 1982 dollars unless stated.

Scope (task title): the literature on recovering the NSW benchmark from observational
comparison groups; the benchmark itself and its source.

## Novelty verdict

**Partly answered: the substantive question has been answered, and only the procedure is new.**

The CPS-1 versus NSW-treated (Dehejia-Wahba subsample) comparison is the most studied
benchmark-recovery exercise in program evaluation. Point estimates of the ATT on 1978
earnings, with standard errors and their distance from the $1,794 benchmark, have been
published for propensity-score stratification and matching (Dehejia and Wahba 1999,
2002), cross-sectional and DID matching (Smith and Todd 2005), blocking and bias-corrected
matching after outcome-free trimming (Imbens 2015), and ten modern estimators with and
without trimming (Imbens and Xu 2025). Most of these land within one standard error of the
benchmark. So H1 (positive, CI excludes zero) and H2 (CI covers the benchmark) are close
to predictable from the literature. An estimate on its own adds little.

The closest prior work is **Imbens and Xu (2025, JEP)**, which runs nearly this exact
exercise on LDW-CPS. It finds that once overlap is enforced the estimators agree, and many
of them sit near $1,794. It also finds that placebo tests on 1975 earnings reject
unconfoundedness, so the agreement "may have given researchers a false sense of
confidence". **Imbens (2015)** already sets out and applies an outcome-free design stage
(trimming, propensity model and a pseudo-outcome check, all without Y) on the same data,
and proposes "no specification searches" at the analysis stage.

**Pre-commitment in benchmark comparisons is not new in general** (revised after
question-r1 F6). The within-study-comparison (WSC) literature already lists it as a
quality criterion. Cook, Shadish and Wong (2008) require that "Analysts of the
experimental and observational data should be blind to each other's results" (criterion
4). They also describe Shadish, Clark and Steiner's study, in which the propensity-score
analysis was done by an author blind to how the scores affected bias reduction.
Weidmann and Miratrix (2021) specified their matching method "before we began generating
results". Keller et al. (2024) preregistered the analysis plan of a four-arm WSC on OSF.

What remains is narrow. **In the searches listed below I found no example on the
NSW-CPS (LaLonde/Dehejia-Wahba) benchmark** that commits to one estimator, covariate set
and overlap rule in a timestamped record before outcomes are examined. This is a claim
about those searches, not proof that no such example exists. The contribution as written
in `plan.json` is therefore defensible, but it is procedural, and it applies a known WSC
standard to the best-known benchmark. The paper should say so: it is a pre-committed
replication of a known result, not a new estimate, and it should cite cook2008 for the
standard.

The NSW-CPS setting cannot meet Cook-Shadish-Wong criterion 4 in full. The benchmark is
public and the crew knows it. Its value also depends on the commitment being credible even though the crew,
like any analyst, already knows from this literature which estimators "work" on LDW-CPS
(see design implication D1).

## 1. The benchmark and its source

### LaLonde (1986) `[lalonde1986]`
Read: full text, a scan of the published AER article (third-party host), Table 5 and
Sections I-II.
- NSW men, LaLonde sample: 297 treated and 425 controls (sizes from dehejia1999 Table 1 and imbens2025 Table 1).
  Experimental impact on 1978 earnings: **$886 (SE 476)**, Table 5 col. (4). Unadjusted
  difference in means, 1982 dollars.
- CPS-SSA-1 versus NSW treated, the same column: **-$8,870 (SE 562)**. The regression
  estimates vary widely across specifications and comparison groups (Table 5). LaLonde's
  conclusion (abstract) is that "many of the econometric procedures do not replicate the
  experimentally determined results".
- CPS-SSA file (footnote, pp. 611-612): March 1976 CPS matched to Social Security
  earnings. Only people in the labor force in March 1976 with nominal income < $20,000 and
  household income < $30,000. "In 1976 ... 21 percent of the males had earnings at the
  Social Security maximum." Males over 55 are excluded.
- **Implication:** the outcome for CPS men is administrative SSA earnings, which are top-coded at the
  SS maximum. For NSW men it is survey earnings. The CPS sample is also pre-screened on
  income and labor-force status. All of this is fixed by the data, so the paper should
  list it as a threat, not try to fix it.

### Dehejia and Wahba (1999) `[dehejia1999]`: source of the $1,794 benchmark
Read: full text of NBER WP 6586 (June 1998) on 2026-11-18, and on 2026-11-19 (paper-r1 F2a)
the **published JASA article** itself: a JSTOR page scan of JASA 94(448):1053-1062 hosted on
the first author's site (https://users.nber.org/~rdehejia/papers/dehejia_wahba_jasa.pdf),
read by OCR, with the Table 3 rows checked against the page image. Tandfonline still
returns 403. The benchmark is also corroborated by smith2005 Table 1, dehejia2002 and imbens2025.
- **Checked in the JASA text (2026-11-19), all identical to the WP:** the RE74 subset is
  selected on month of assignment and employment history, 185 treated and 260 controls
  (p. 1054); CPS-1 has 15,992 men (Table 1, p. 1055); NSW benchmark **1,794 (633)** in
  Table 2, panels B and C, col. (1) (p. 1056) and Table 3, col. (1) (p. 1059), and 1,672
  (638) adjusted (Table 3, col. (2)); Table 2 note: the NSW-control estimates are unbiased
  estimates of the impact for the original sample ($886) and the RE74 sample ($1,794);
  CPS-1 row of Table 3: -8,498 (712), 972 (550), stratification **1,713 (1,115)** and
  **1,774 (1,152)**, matching **1,582 (1,069)** and **1,616 (751)**; 12,611 of 15,992 CPS-1
  units discarded (p. 1058 and Figure 2); the balance-driven specification search, "we add
  higher-order terms and interactions of the covariates until this condition is
  satisfied" (p. 1058); with RE74 dropped, matching estimates range from $861 to $1,941
  (p. 1061). So the paper may cite the JASA article, with these table numbers, for
  every DW (1999) number it uses. Section numbers in the bullets below are the WP's.
- **Sample:** the "RE74 subset" of LaLonde's men, defined by month of assignment so that 1974
  earnings are available: **185 treated, 260 controls** (Sec. 2.1; Table 1).
- **Benchmark:** **$1,794 (SE 633)**. This is the unadjusted experimental difference in mean
  1978 earnings (Table 2, Panel B col. (1) and Table 3 col. (1), NSW row). With
  covariate adjustment it is $1,672 (SE 638) (Table 3, col. (2)). The paper calls $1,794
  "an unbiased estimate of the impact of training" (Table 2 note b). It is more than twice LaLonde's $886
  because of the "cohort phenomenon" (Sec. 2.2).
- **Derived (Scout arithmetic, not in the paper):** a normal 95% interval for the benchmark
  is 1,794 ± 1.96×633, roughly **[$553, $3,035]**. The benchmark has its own sampling
  error, and H2 should be read with that in mind.
- **CPS-1:** 15,992 men (Table 1). Means: age 33.22, educ 12.02, black 0.07, married 0.71,
  RE74 $14,016, RE75 $13,650. NSW treated: age 25.81, black 0.84, married 0.19, RE74
  $2,096, RE75 $1,532.
- **Results with CPS-1** (Table 3): difference in means -$8,498 (712); OLS on all
  covariates $972 (550). Propensity-score stratification gives **$1,713 (1,115)** unadjusted
  and **$1,774 (1,152)** adjusted. Matching with replacement gives **$1,582 (1,069)** unadjusted and
  **$1,616 (751)** adjusted. Of the 15,992 CPS units, 12,611 are discarded because their score
  is below the treated minimum (Sec. 4).
- **Propensity-score specification for CPS** (Table 3, note e): logit on age, age²,
  educ, educ², nodegree, married, black, hisp, RE74, RE75, u74, u75, educ·RE74, age³.
  It was **chosen by a balance-driven specification search**, which "adds higher-order and
  interaction terms until within-stratum balance is achieved" (Sec. 5.1). Dropping RE74
  moves the CPS estimates to $861-$1,941 (Sec. 5.2).

### Dehejia (data page) `[dehejiadata]`
Read: https://users.nber.org/~rdehejia/data/.nswdata2.html and the directory index.
- **Year (paper-r1 F6, 2026-11-19):** the page text states no date. The server's HTTP
  Last-Modified header is 8 Oct 2012, but that is server metadata, not a date stated on
  the page. refs.bib therefore has `year = {2026}` (year of access) and a note saying so.
- `nswre74_treated.txt` has 185 rows, `nswre74_control.txt` 260 and `cps_controls.txt` **15,992**.
- Column order for the DW and CPS files: treat, age, educ, black, hisp, married, nodegree,
  RE74, RE75, RE78. The binary variables are coded 1/0. **There are no u74/u75 columns.**
  Unemployment indicators have to be built from RE74 = 0 and RE75 = 0.
- There is no explicit licence. The page says LaLonde gave permission to publish the data.
  The page also notes that CPS2/CPS3 do not exactly match LaLonde's subsets, which does
  not matter here because CPS-1 is used.

## 2. Prior attempts to recover the benchmark from CPS-1

### Dehejia and Wahba (2002) `[dehejia2002]`
Read: NBER WP 6829 (Dec 1998). Published metadata and abstract from Crossref and IDEAS.
- WP Table 2, CPS: the full-CPS regression gives $1,066 (554). Nearest-neighbour matching
  without replacement gives $1,559-$1,605. Matching with replacement gives $1,360 (974),
  using 119 controls. Radius matching gives $1,119-$1,158, and its bias grows as more
  controls enter.
- The propensity logit uses age, age², age³, educ, educ², married, nodegree, black, hisp, RE74, RE75,
  u74, u75, educ·RE74.
- **Implication:** with this many controls, estimates still move by about $500 depending
  on the matching variant. This is the kind of researcher choice that a pre-specification
  has to fix.

### Smith and Todd (2005) `[smith2005]` and Dehejia (2005) reply `[dehejia2005]`
Read: full text of both (article-in-press PDFs).
- Smith and Todd find that DW's low bias "is highly sensitive to their choice of a
  particular subsample of LaLonde's (1986) data" and to the variables in the score
  (abstract; Sec. 1). Table 5, CPS, the DW sample with the DW score: nearest-neighbour
  biases are $5-$407. On LaLonde's full sample and on the "Early RA" subsample (108 T /
  142 C, experimental impact $2,748) the biases are far larger (e.g. $7,781 for one
  nearest neighbour on Early RA).
- **What "Re74" measures (Sec. 5, pp. 321-323; checked by the Scout 2026-11-19 against the
  fetched article-in-press text, claim `c-smith-re74`):** "Real Earnings in 1974" for the
  NSW samples "consists of real earnings in months 13-24 prior to the month of random
  assignment"; for persons assigned early these months largely overlap calendar 1974, for
  persons assigned later they largely overlap 1975, and this is "the variable denoted
  'Re74' in DW (1999, 2002)" (pp. 321-322). The DW inclusion rule that Smith and Todd
  reconstructed "partly through trial and error", accounting for all but one observation
  (p. 323, Table 2): everyone randomly assigned January-April 1976, plus, of those
  assigned after April 1976, only persons with zero earnings in months 13-24. They say
  this rule "corresponds fairly closely to the verbal statement in DW (1999)". The
  after-April rule is therefore Smith and Todd's reconstruction, not a rule DW state.
- **Mechanisms they name:** comparison units come from national samples, so they are mostly
  from different local labour markets. Earnings are also measured differently for the two groups:
  SSA administrative records for CPS, survey data for NSW (Sec. 5). They find that
  DID matching performs best because it removes these time-invariant biases.
- Dehejia (2005) replies that each treatment-comparison pairing needs its own propensity
  specification, and that sensitivity to small specification changes is a diagnostic
  (abstract).
- **Implication:** the result is known to depend on the DW subsample. The paper should
  state that its target is the DW-subsample ATT and should not claim the finding
  generalises to NSW men.

### Imbens (2015) `[imbens2015]`
Read: NBER WP 19959 (March 2014). Sec. 4 and Sec. 6.3, Tables 20-22.
- He proposes a **three-stage strategy**. The design stage trims on the propensity score
  "without using the outcome data". The supplementary stage runs pseudo-outcome tests,
  again without Y. The analysis stage uses blocking or bias-corrected matching, with
  "no specification searches at this stage" (Sec. 4.3).
- **LDW-CPS** (Table 22, thousands of $): the full sample with no covariates gives -8.50
  (0.58). After matching 185 treated to 185 controls without replacement, estimates are
  **1.72-2.10**. One example is 1.90 (0.67) with 2 blocks and all covariates.
- Pseudo-outcome tests (Table 20): earn'75 gives -1.22 (0.25) blocking and -1.24 (0.30)
  matching. (earn'74+earn'75)/2 gives -6.13 (0.49). He concludes "we cannot be confident
  here that unconfoundedness holds" (Sec. 6.3.4, 6.3.7).
- **Implication:** an outcome-free design on these data has already been published. The
  crew's addition is the **timestamped, single-estimator commitment**, not the idea of an
  outcome-free design.

### Imbens and Xu (2025) `[imbens2025]` and replication tutorial `[xu2024tutorial]`
Read: full text of arXiv v3 (JEP forthcoming version), the AEA abstract page and the
tutorial page.
- **Tutorial year (paper-r1 F6, 2026-11-19):** neither the 02-LDW page nor the tutorial
  index page states a date, and the server sends no Last-Modified header. refs.bib
  therefore has `year = {2026}` (year of access) and a note saying so. The index page says
  the tutorial condenses the analysis of "Imbens & Xu (2024)", the arXiv version.
- This is the **closest prior work**. On LDW-CPS (185 treated) they use ten estimators: regression,
  regression with interactions, GRF, 1:5 NN matching with bias correction, IPW with GRF
  scores, CBPS, entropy balancing, DML-ElasticNet and AIPW-GRF. All give positive
  ATTs, and "nearest neighbor matching aligns most closely with the experimental benchmark of $1,794".
  After trimming (164 treated, 1:1 matched controls) the trimmed benchmark is **$1,911**.
- Tutorial Table B1 (robust SEs), LDW-CPS1 full sample: the benchmark is 1794.34 (670.82).
  Estimates range from **$1,066 (regression) to $1,729 (NN matching)**, e.g. IPW 1,236.84
  (687.14), entropy balancing 1,406.27 (654.93), AIPW-GRF 1,571.17 (703.86).
- **Placebo (RE75 as outcome, without conditioning on RE75/u75):** every nonexperimental
  estimate is negative and significant. In the tutorial Table B2 they run from about
  -$1,097 to -$1,579, against an experimental placebo of 265 (305). Their conclusion:
  "With sufficient overlap, modern methods can robustly estimate the statistical
  estimands, but not necessarily the causal estimands." LDW-CPS "appears to be an outlier
  in its ability to recover experimental benchmarks".
- **Discrepancy noted:** their Table 1 reports 15,922 CPS-SSA-1 observations, while their
  Figure 1, the data page, DW (1999) and athey2024 all report 15,992. This looks like a
  typo in their Table 1.
- **Implication:** trimming that drops treated units changes the estimand. The benchmark
  then moves from $1,794 to $1,911 in their trimmed sample. A design that wants to be
  compared with $1,794 must keep all 185 treated and trim **only controls**. If it trims
  treated units, it must say that the target is no longer the DW-subsample ATT.

## 3. Estimator selection and the "forking paths" problem on this benchmark

### Advani, Kitagawa and Słoczyński (2019) `[advani2019]`
Read: arXiv v2 full text.
- They treat NSW-treated plus trimmed CPS-1 as a population: 185 treated and 7,660 CPS
  units, with the CPS trimmed to the min/max score of the experimental units (fn 9). They ask
  whether empirical Monte Carlo can pick the estimator. Both approaches they study "are
  worse than random at selecting estimators which minimise absolute bias". They advise
  "use a range of estimators and compare estimates for robustness" (Summary).
- They also use the Smith-Todd placebo design (NSW **controls** versus CPS, true effect 0).
- **Implication:** the benchmark has already been mined for estimator-selection studies. No
  data-driven selection rule is known to pick the right estimator here. This supports
  choosing the estimator on a priori grounds and committing to it. It also means the
  paper should report a small set of secondary estimators as sensitivity analysis, not
  for selection.

### Athey, Imbens, Metzger and Munro (2024) `[athey2024]`
Read: arXiv v3 full text (abstract, Sec. 3).
- They use LDW-CPS (185 treated plus 15,992 CPS = 16,177) to generate WGAN data and
  compare ATT estimators. Finding: "there is not a single estimator that outperforms the
  others in all three settings".
- **Implication:** this supports an a priori choice. It does not hand the crew a "best"
  estimator.

### Abadie and Imbens (2011) `[abadie2011]`
Read: abstract only.
- Their bias-corrected matching is applied to the NSW data of LaLonde (1986), with an
  NSW-based simulation in which it performs well on bias, RMSE and coverage relative to
  simple matching and regression.
- **Implication:** this is a candidate primary estimator that comes with a published
  rationale, and it is the "NN matching with bias correction" used in imbens2025.

## 4. Overlap and outcome-free design

### Crump, Hotz, Imbens and Mitnik (2009) `[crump2009]`
Read: abstract of NBER TWP 330 (2006, earlier title) on 2026-11-18, and on 2026-11-19
(paper-r1 F2b) the **abstract of the published Biometrika article** (IDEAS/RePEc record
https://ideas.repec.org/a/oup/biomet/v96y2009i1p187-199.html, "Copyright 2009, Oxford
University Press"). The Biometrika abstract states the rule: "a good approximation to the
optimal rule is provided by the simple rule of thumb to discard all units with estimated
propensity scores outside the range [0.1,0.9]". The rule as cited (claim `c-crump-rule`)
is thus verified against the published article's abstract; the body of the Biometrika
article was not read (academic.oup.com returned 403).
- They characterise optimal subsamples. As an approximation they recommend dropping units with
  estimated scores outside **[0.1, 0.9]**.
- **Implication:** that rule targets ATE-type estimands and drops **treated** units, so it
  changes the estimand away from the $1,794 benchmark. For the ATT, DW's rule (drop controls
  below the minimum treated score) or a rule that trims controls only fits better.

### Rubin (2008) `[rubin2008]`
Read: arXiv full text (abstract, Sec. 1-2).
- Observational studies "have to be carefully designed to approximate randomized
  experiments, in particular, without examining any final outcome data". Outcome-free
  design is "absolutely critical for objectivity".
- **Implication:** this is the methodological basis for the plan's contribution. Cite it
  for the principle, and imbens2015 for its application to these data.

### Chernozhukov et al. (2018) `[chernozhukov2018]` (added 2026-11-19 for paper-r1)
Read: full text, arXiv:1608.00060v7; published metadata (Econometrics Journal 21(1):C1-C68)
from Crossref.
- DML combines Neyman-orthogonal scores with cross-fitting; together they remove the bias
  that regularization and overfitting in machine-learned nuisance estimates would otherwise
  cause, so the estimator is root-N consistent and approximately normal (Summary; Sec. 3.1,
  Definitions 3.1-3.2, K-fold cross-fitting, DML1/DML2).
- Sec. 5.1 gives the orthogonal (doubly robust, AIPW-type) score for the ATE (eq. 5.3) and
  for the ATT, "ATTE" (eq. 5.4), under unconfoundedness, with Theorem 5.1 for inference.
- Sec. 3.4, Definition 3.3: repeat the estimator over S random splits and report the mean
  or the median; "We recommend using medians".
- **Use:** the reference for cross-fitted AIPW for the ATT (claim `c-dml-crossfit`). It
  is a methods reference, not prior work on this benchmark.

## 5. Within-study comparisons and blinding or pre-specification (added for F6)

### Cook, Shadish and Wong (2008) `[cook2008]`
Read: full text (a copy of the JPAM article, pp. 724-750).
- They review 12 recent within-study comparisons. The RD designs, the cases of intact-group matching on the pretest
  (especially local matches), and the cases with a known selection process reproduce the
  experimental estimates. This is "more promising than what was achieved in past
  within-study comparisons, most involving job training" (abstract).
- They list seven criteria for a good WSC. The ones that bear on this study:
  - (2) The experiment and the observational study must estimate the same causal quantity.
  - (3) The groups must be measured the same way and should come from the same place.
  - (4) The analysts must be blind to each other's results.
- They fault Aiken et al. (1998) because "the analysts were not blind" (p. 739). They describe
  Shadish, Clark and Steiner's propensity-score analysis as "carried by an author blind to how the
  propensity scores he computed affected the bias reduction" (p. 740).
- **Implication:** NSW-CPS fails (3) by construction: survey versus SSA earnings, and
  national comparison units (see smith2005). It can meet (4) only partly. Criterion (2)
  supports D2: the same ATT and the same 185 treated men.

### Weidmann and Miratrix (2021) `[weidmann2021]`
Read: arXiv preprint full text (abstract and introduction).
- This study has 14 WSCs in English primary schools. Their 1-1 school-level matching "was specified
  before we began generating results". The mean absolute bias is 0.03σ.
- **Implication:** this is prior art for pre-specifying the observational method in a
  benchmark comparison.

### Keller et al. (2024) `[keller2024]`
Read: abstract (EconPapers record of the OSF preprint).
- This is a four-arm WSC (N = 2,200) whose eligibility, recruitment, allocation and **analysis plan
  were preregistered on OSF**. The abstract reports no results yet.
- **Implication:** preregistered benchmark comparisons exist. The crew's novelty is limited
  to applying one to the NSW-CPS benchmark.

## Design implications for the Econometrician and PI

- **D1, honest framing of the pre-commitment.** The benchmark ($1,794) and the behaviour
  of the main estimators on LDW-CPS are public, and this crew has now read them. The
  commitment removes outcome-driven selection *within this study*. It cannot remove
  selection driven by the literature. Disclose this in the paper. Choose the estimator by
  a rule that a reader can check against an a priori rationale (e.g. imbens2015's recipe,
  or AIPW/bias-corrected matching as the doubly robust default), not by its published
  closeness to $1,794. Note that imbens2025 show NN matching lands closest, so picking it
  invites the suspicion D1 describes.
- **D2, estimand.** Use the ATT for the 185 DW-treated men. Use an overlap rule that trims
  **controls only**, e.g. drop CPS units with a score below the treated minimum (dehejia1999)
  or outside the treated score range (advani2019 fn 9). If any treated unit is dropped,
  the target is no longer the one the $1,794 benchmark estimates (imbens2025: the trimmed
  benchmark is $1,911). The experimental controls cannot be used to re-benchmark under the
  task rules.
- **D3, covariates.** Use the ten standard covariates: age, educ, black, hisp, married, nodegree, RE74,
  RE75, u74, u75 (imbens2025; dehejia2002). u74 and u75 are not in the files and must be
  built as RE=0 indicators (dehejiadata). Fix any higher-order terms in the propensity
  model in advance. DW's own model came from a balance-driven search (dehejia1999 Sec. 5.1).
- **D4, a check that can fail (placebo).** Pre-register a placebo: the effect on RE75 without
  conditioning on RE75/u75, using the same estimator. The literature predicts it will fail:
  about -$1,100 to -$1,600, significant (imbens2025/xu2024tutorial; imbens2015 Table 20).
  The paper must report this whatever the main result is. It is the most informative
  check on H1.
- **D5, standard errors.** The benchmark SE is 633 (conventional; dehejia1999) or 670.82
  (robust; xu2024tutorial). Fix the SE method for the primary estimate at the design
  gate (e.g. the Abadie-Imbens analytic SE for matching, or influence-function SEs for
  AIPW). The H2 comparison ignores the benchmark's own sampling error unless the paper
  says how it handles it.
- **D6, threats to list.** These cannot be fixed with these files: outcome measurement
  differs (SSA administrative earnings, top-coded at the SS maximum for 21% of CPS men in
  1976, versus NSW survey earnings); comparison units are geographically mismatched
  (smith2005); the CPS sample is pre-screened on income (lalonde1986 fn); results depend
  on the DW subsample (smith2005); and the placebo is expected to fail (imbens2015,
  imbens2025).
- **D7, reporting.** Report the estimate against the benchmark *and* against the range of
  published LDW-CPS estimates ($972-$1,774 in dehejia1999 Table 3; $1,066-$1,729 in the
  tutorial Table B1), so readers can see whether the pre-committed choice is typical.

## Revision log

- **2026-11-19, paper-r1 (F2, F6).** (a) dehejia1999 verified against the JASA article
  (JSTOR scan on the author's site); every number and table number used matches the WP;
  sources.json updated; no WP entry needed. (b) crump2009 rule verified against the
  Biometrika abstract (IDEAS); sources.json updated. (c) Added claim `c-smith-re74`,
  verified by the Scout against smith2005 Sec. 5, pp. 321-323. F6: `year = {2026}` plus a
  note added to dehejiadata and xu2024tutorial (no date stated on either page). Optional:
  added chernozhukov2018 (full text) with claim `c-dml-crossfit`; Imbens (2003) could not
  be read and was not added. Searches: "Dehejia Wahba 1999 Causal Effects in
  Nonexperimental Studies JASA pdf" (led to the author's papers/ directory); "Crump Hotz
  Imbens Mitnik Dealing with limited overlap Biometrika pdf"; "Imbens 2003 Sensitivity to
  Exogeneity Assumptions in Program Evaluation pdf" (standard and extended).

## Search log (2026-11-18)

- Crossref API: DOIs resolved for all journal entries above. A bibliographic query found
  the JEP 2025 DOI of Imbens-Xu and its earlier SSRN version.
- Web searches: "LaLonde NSW CPS benchmark pre-registered OR blinded estimator choice";
  "LaLonde pre-analysis plan / preregistered nonexperimental estimator NSW CPS". Neither
  found any preregistered or blinded recovery exercise on this benchmark. The results were
  the papers above, plus Calónico and Smith (2017) on NSW women.
- Added for question-r1 F6 (same date, UTC):
  - "Cook Shadish Wong 2008 Three conditions ... pdf" found the full text, which I read.
  - "within-study comparison prospective design blinded analyst nonexperimental estimates
    before experimental results known" (extended search) led me to weidmann2021. It also
    surfaced Ferraro and Miranda (2014, JEBO, 10.1016/j.jebo.2014.03.008); a search
    snippet says that paper discusses the Glazerman et al. (2008) blinding standard.
  - "within-study comparison preregistered OR pre-registered OR pre-analysis plan" led me
    to keller2024. It also surfaced an MDRC post recommending preregistered matching plans
    (not read).
  - None of these searches found a pre-committed analysis on NSW-CPS.
- Full texts were downloaded to the session scratchpad and read with pdftotext:
  NBER w6586, w6829, w19959, t0330; arXiv 2406.00827, 1809.09527, 1909.02210, 0811.1640;
  the Smith-Todd and Dehejia (2005) article-in-press PDFs; and the LaLonde (1986) scan.

## Unverified or not used

- **Published REStat (2002) typeset tables.** Not accessible (paywall); dehejia2002 numbers
  come from NBER WP 6829. (The JASA 1999 article *was* read on 2026-11-19; see above.)
- **Crump et al. (2009), Biometrika body text.** Not read (403). The published abstract,
  which states the [0.1, 0.9] rule, was read on 2026-11-19.
- **Imbens (2003), "Sensitivity to Exogeneity Assumptions in Program Evaluation", AER
  93(2):126-132, DOI 10.1257/000282803321946921** (metadata from Crossref and IDEAS).
  Not added. The author's copy on scholar.harvard.edu returned 403 to curl, WebFetch and
  a browser; the AEA page is paywalled and shows no abstract; IDEAS has no abstract;
  OpenAlex and Semantic Scholar list no open copy. Nothing about the model it proposes
  could be checked against the source, so there is no entry and no citation claim. The
  plan's sensitivity model (plan.json design.method.sensitivity) is attributed to it
  without a verified source.
- **Abadie and Imbens (2011).** Only the abstract was read. No numbers are cited from it.
- **Hainmueller (2012), entropy balancing.** The publisher page did not show a LaLonde
  application, so it was not added.
- **Diamond and Sekhon (2013), Heckman and Hotz (1989), Calónico and Smith (2017).**
  These are relevant context but were not fetched and read, so they were not added.
  Cook, Shadish and Wong (2008) has since been read and added.
- **Ferraro and Miranda (2014, JEBO)** and **Glazerman, Levy and Myers (2003/2008).** The
  blinding standard is attributed to them in search snippets only. The ScienceDirect
  page returned 403, so they were not added. Shadish, Clark and Steiner (2008) is
  described only through cook2008 and was not read directly.
- **keller2024.** Only the abstract was read. Whether the preregistered plan fixed a
  single estimator was not checked.
- **LaLonde (1984) Princeton WP.** The DataSpace copy is behind a bot challenge.
- The full text of the LaLonde (1986) article came from a third-party host (gwern.net), not
  JSTOR. Its text matches the IDEAS metadata and the abstract quoted in imbens2025.
