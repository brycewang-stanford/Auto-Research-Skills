# Scout notes: ss-null-effect (task q-novelty)

Compiled by the Scout on 2026-11-18. Bibliographic metadata comes from the Crossref API
record for each DOI (or from IDEAS/RePEc where there is no DOI), never from memory.
`method` in `sources.json` says what was read. Every number quoted below comes from a
fetched full text, and the location is given next to it. I did not open the seed's
`answer.json`, the `answer/` directory or `data.csv`. Everything I say about the data
comes from `task.json`.

23 sources verified: 9 from full text and 14 from the abstract only.

---

## 1. Novelty verdict

**Verdict: the methods are not new. The answer for this dataset is not yet known.
Calling the paper "new" is justified only in a narrow sense.**

- **What is not new.** Two questions are already well studied. The first is whether a
  voluntary job-training program raises earnings. The second is whether
  selection-on-observables estimators can recover such an effect from non-randomized
  data. The standard references are LaLonde (1986), Dehejia & Wahba (1999, 2002),
  Smith & Todd (2005), Dehejia (2005), the reviews by Imbens (2004) and Imbens &
  Wooldridge (2009), and the meta-analysis by Card, Kluve & Weber (2018). The estimators
  are also standard: propensity score, IPW, doubly robust/AIPW, DML, and trimming.
  Pre-specifying the analysis and adjusting for multiple outcomes is established
  practice too (Casey et al. 2012; Anderson 2008; Olken 2015; Burlig 2018 for
  observational data). The contribution line in `plan.json` ("estimand, primary outcome
  and estimator fixed before any outcome is examined, with every analysed outcome
  reported") describes good practice. It is not a methodological contribution, and the
  paper should not present it as one.
- **What is new.**
  - No published analysis of this 4,000-person extract exists. Its license is
    "CC0-1.0 (synthetic data distributed with this repository)", so any estimate from
    it is new by construction.
  - The analysis is pre-specified while the outcomes are still sealed. The crew's
    design gate keeps the outcomes closed until the plan is fixed, which is the
    "data not yet accessed" condition that Burlig (2018) says makes an observational
    pre-analysis plan credible.
  - The paper will say what effect size the data can rule out, in the way Abadie
    (2020) recommends.
- **What must be said plainly in the paper.**
  1. The data are synthetic. The brief calls the file an "administrative extract", but
     the license says it is synthetic. Results describe this dataset, not a real
     program, and no policy claims about real training programs should be made.
  2. The variable names re74, re75 and re78 match those of the LaLonde/NSW files used by
     Dehejia & Wahba. The population, however, is different:
     - 4,000 adults, about 40% treated, with covariates such as married, urban, region,
       children and health_limit.
     - By contrast, the Dehejia-Wahba NSW sample has 185 treated men and a PSID
       comparison group of 2,490.
     - The NSW experimental estimates ($886 in LaLonde's full male sample; $1,794 in
       the Dehejia-Wahba subsample) are therefore not a benchmark or "true value" for
       this extract. They can be used only as a reference for an economically
       meaningful effect size, and the dollar year must be stated.
- **Closest prior work:**
  - Dehejia & Wahba (1999) and Smith & Todd (2005): the same estimand, the same kind
    of covariates (two lags of earnings plus unemployment indicators), and the same
    identifying assumption.
  - Burlig (2018): pre-analysis plans for observational data.
  - Anderson (2008): multiple-outcome inference with a summary index.

No source was found that makes the question pointless.

---

## 2. Experimental-vs-observational benchmark

### LaLonde (1986) `[lalonde1986]`, full text read
- **What it shows.** It compares estimates from the NSW field experiment with
  non-experimental estimates that use comparison groups drawn from the PSID and
  CPS-SSA. The experimental estimates of the effect on 1978 earnings are:
  - men: $886 (SE $476)
  - AFDC women: $851 (SE $317)

  Both are in 1982 dollars (Table 5 and Table 4 notes, p. 616). The non-experimental
  estimates for men are "negative and smaller" than the experimental ones. Even
  estimates that pass conventional specification tests "still fail to replicate the
  experimentally determined results". Policymakers "should be aware that the available
  nonexperimental evaluations ... may contain large and unknown biases resulting from
  specification errors" (Section IV, p. 617). Longitudinal data reduce the potential
  for specification error relative to cross-sectional data (p. 617).
- **Implications for the design.**
  - Expect self-selection bias.
  - Do not trust a single specification.
  - Use the pre-program earnings history (re74, re75, unemp74, unemp75) as
    conditioning variables.
  - Passing specification tests is not proof of validity.

### Dehejia & Wahba (1999) `[dehejia1999]`, full text (NBER WP 6586)
- **What it shows.**
  - Their subsample of LaLonde's men has 185 treated and 260 controls. The
    experimental benchmark rises from $886 to $1,794 because of a cohort effect
    (Section 2.2).
  - Propensity-score stratification and matching give $1,608 and $1,691 with the PSID
    comparison group. With the CPS comparison group they give $1,713 and $1,582. On the
    full comparison samples, a difference in means gives -$15,205 (PSID) and -$8,498
    (CPS) (Table 3 discussion).
  - A researcher using their method would obtain estimates "ranging from $1,473 to
    $1,774". The method works because it "use[s] only the subset of the comparison
    group that is comparable to the treatment group" (Conclusion).
  - Adding 1974 earnings (a second lag) brings the regression estimates closer to the
    benchmark.
  - The authors warn that "there may be important unobservable covariates, for which
    the propensity score method cannot account."
- **Implications for the design.**
  - Make overlap and balance diagnostics central.
  - Use both lags of earnings.
  - Report how many comparison units are comparable.

### Dehejia & Wahba (2002) `[dehejia2002]`, full text (NBER WP 6829)
- **What it shows.**
  - Nearest-neighbour propensity-score matching brings the CPS estimates to $1,559 to
    $1,605, against the $1,794 benchmark.
  - With the PSID comparison group only 56 of 2,490 controls are comparable, and
    estimates become sensitive to the matching method.
  - The method "is able to pare the large pool of potential controls down to the
    relevant comparisons without using information on outcomes".
  - "It is extremely valuable to check the comparability of the treatment and control
    units in terms of pre-treatment characteristics" (Sections 5 and 6).
- **Implications for the design.** Choose the propensity model, check balance and set
  the trimming rule using covariates and treatment only. This is outcome-blind and can
  be done before the design gate.

### Smith & Todd (2005) `[smith2005]`, published abstract plus full text (PIER WP 01-035)
- **What it shows.** Applied to the same NSW data, propensity-score matching estimates
  are "highly sensitive to the set of variables included in the scores and to the
  analysis sample". Difference-in-differences matching performs best, because it
  removes time-invariant bias such as geographic mismatch and differences in how
  outcomes are measured. Matching is "not a general solution to the evaluation
  problem".
- **Implications for the design.**
  - Fix the propensity covariate set before outcomes are opened.
  - Report sensitivity to alternative covariate sets.
  - Consider a pre-specified secondary estimator that uses the earnings change, such as
    re78 minus re75 or a DiD-style AIPW.
  - region and urban can stand in for local labour markets.

### Dehejia (2005) `[dehejia2005]`, full text
- **What it shows.** It replies to Smith & Todd. A separate propensity-score
  specification must be estimated for each pairing of treatment and comparison group,
  and researchers should "examine the sensitivity of the estimated treatment effect to
  small changes in the propensity score specification", which works as a diagnostic of
  comparison-group quality (Abstract; Section 5).
- **Implications for the design.** Pre-specify a small, fixed set of alternative
  propensity specifications as a robustness check, and report all of them.

---

## 3. Estimation under unconfoundedness

### Rosenbaum & Rubin (1983) `[rosenbaum1983]`, abstract
- **What it shows.** Adjusting for the scalar propensity score is enough to remove bias
  from all observed covariates.
- **Implications for the design.** This underpins using the propensity score both for
  balancing and for weighting.

### Imbens (2004) `[imbens2004]`, full text (NBER TWP 294)
- **What it shows.**
  - It reviews regression, matching, propensity-score and mixed methods under
    unconfoundedness and overlap.
  - Section 3.4 explains double robustness: combining weighting with regression gives a
    consistent estimator if either model is correctly specified.
  - Section 5.1 describes indirect tests of unconfoundedness. The most useful one
    estimates the "effect" of treatment on a lagged outcome that the treatment cannot
    have affected. "For these tests it is clearly helpful to have a number of lagged
    outcomes."
- **Implications for the design.** A placebo test that treats re75 as a pseudo-outcome
  and conditions on re74, unemp74 and the other covariates (not on re75 itself) is
  feasible here. It uses no post-program outcome, so it can be pre-specified and even
  run as data preparation.

### Imbens & Wooldridge (2009) `[imbens2009]`, full text (NBER WP 14251)
- **What it shows.**
  - It recommends reporting the normalized difference (mean difference divided by
    sqrt(S0² + S1²)) rather than t-statistics. As a rule of thumb, a normalized
    difference above one quarter means linear regression is sensitive to
    specification.
  - In LaLonde's data, four of the ten covariates differ by more than one standard
    deviation.
  - It recommends propensity-score histograms by treatment status to judge overlap.
  - It warns that trimming "change[s] what is being estimated".
- **Implications for the design.**
  - Pre-specify a balance table with normalized differences and a propensity
    histogram, both outcome-blind.
  - Pre-specify the trimming rule and say which estimand it targets.

### Hirano, Imbens & Ridder (2003) `[hirano2003]`, abstract
- **What it shows.** Weighting by the inverse of a nonparametrically estimated
  propensity score gives an efficient estimator of the average treatment effect.
- **Implications for the design.** This supports IPW as a secondary estimator.

### Imbens (2003) `[imbens2003]`, opening text
- **What it shows.** It examines how robust treatment-effect estimates are to
  departures from unconfoundedness, as a middle path between assuming unconfoundedness
  and Manski-style bounds.
- **Implications for the design.** Pre-specify a sensitivity analysis for unobserved
  confounding.

---

## 4. Doubly robust / augmented IPW

### Robins, Rotnitzky & Zhao (1994) `[robins1994]`, abstract
- **What it shows.** It introduces augmented inverse-probability-weighted estimating
  equations, which reach the semiparametric efficiency bound when data are missing at
  random.
- **Implications for the design.** This is the origin of the AIPW estimator.

### Bang & Robins (2005) `[bang2005]`, abstract
- **What it shows.** A doubly robust estimator is consistent if either the
  treatment-assignment model or the outcome model is correctly specified, which gives
  the analyst "two chances, instead of only one". Simulations show good finite-sample
  performance.
- **Implications for the design.** AIPW is a good candidate for the primary estimator.

### Chernozhukov et al. (2018) `[chernozhukov2018dml]`, abstract
- **What it shows.** Neyman-orthogonal scores combined with cross-fitting remove the
  bias that regularization and overfitting introduce when nuisance functions are
  estimated with machine learning.
- **Implications for the design.** If the nuisance models are flexible learners, use
  cross-fitted AIPW (the DML form of the doubly robust score). Fix the learners and the
  number of folds and the seed at the design gate.

---

## 5. Overlap and trimming

### Crump, Hotz, Imbens & Mitnik (2009) `[crump2009]`, published abstract plus full text (NBER TWP 330)
- **What it shows.**
  - Limited overlap makes estimates imprecise and sensitive to specification.
  - The optimal subsample depends only on the propensity score, and dropping units with
    estimated scores outside [0.1, 0.9] is a good approximation to the optimal rule.
  - In the working paper's application to the Dehejia-Wahba PSID sample (2,490
    controls and 185 treated), only 312 units are kept under the optimal rule, and the
    standard error of the ATT estimate falls from 2.58 to 1.82 (thousands of dollars)
    with the 0.10 cutoff (Section 7).
- **Implications for the design.**
  - Pre-specify the trimming rule, for example [0.1, 0.9] or the optimal rule.
  - Report the untrimmed estimate alongside it, and name the estimand for each.
  - With about 40% treated, overlap may be much better than in NSW-PSID, but this has
    to be checked outcome-blind.

---

## 6. Multiple outcomes

The data contain six post-program outcomes (re78, re79, employed78, hours78,
benefits78, wellbeing78) and twenty survey items. Without adjustment for multiple tests,
false positives are likely.

### Benjamini & Hochberg (1995) `[benjamini1995]`, abstract
- **What it shows.** It controls the false discovery rate (the expected share of false
  rejections). This is equivalent to the familywise error rate (FWER) when all nulls
  are true and gives more power otherwise. The step-up procedure is proved for
  independent test statistics.

### Romano & Wolf (2005) `[romano2005]`, abstract
- **What it shows.** It is a stepwise procedure that controls the FWER asymptotically.
  It captures the joint dependence of the test statistics and so has more power than
  single-step methods.
- **Implications for the design.** It suits correlated labour-market outcomes, such as
  earnings, employment and hours.

### Anderson (2008) `[anderson2008]`, abstract
- **What it shows.** It combines summary-index tests with FWER and FDR corrections.
  Results that looked significant without adjustment became clearer once multiple
  inference was accounted for. In complex studies "it can be important to declare the
  family of tests under consideration and to either consolidate measures or report
  adjusted and unadjusted p values."
- **Implications for the design.**
  - Declare test families at the design gate:
    - primary: re78
    - secondary labour-market family: re79, employed78, hours78, benefits78
    - well-being/survey family: wellbeing78 and survey_q01-q20, or a pre-specified
      summary index of them
  - Report both adjusted p-values (Romano-Wolf FWER within each family, or BH FDR for
    the survey items) and unadjusted p-values.

---

## 7. Pre-registration and pre-analysis plans

### Casey, Glennerster & Miguel (2012) `[casey2012]`, abstract
- **What it shows.** The authors used a pre-analysis plan "to bind our hands against
  data mining" across many outcome indicators. Without it they "could have generated
  two divergent, equally erroneous interpretations of program impacts".

### Olken (2015) `[olken2015]`, abstract
- **What it shows.** A pre-analysis plan specifies variables, data cleaning and
  regression specifications before the data are examined. When all pre-specified
  results are reported, data-mining problems are "greatly reduced". It also discusses
  costs and limits.

### Coffman & Niederle (2015) `[coffman2015]`, abstract
- **What it shows.** It argues that enthusiasm for pre-analysis plans should be
  tempered and that replications can be a strong corrective.
- **Implications for the design.** This is the counterpoint the paper should
  acknowledge. Pre-specification does not replace a clean rerun or robustness checks.

### Burlig (2018) `[burlig2018]`, full text
- **What it shows.** Transparency efforts have centred on randomized trials. Burlig
  names three observational settings in which preregistration is credible: researchers
  collecting their own data, prospective studies, and restricted-access data. In each,
  the plan is registered before the researcher can access the data.
- **Implications for the design.** The crew's setup, with outcomes sealed until the
  design gate, is close to this "before access" condition. The paper should say
  explicitly that covariates and treatment were seen before the plan was fixed, but
  outcomes were not.

---

## 8. Interpreting a null and setting a prior on effect size

### Abadie (2020) `[abadie2020]`, abstract
- **What it shows.** Rejecting a point null often carries little information, whereas
  failing to reject can be highly informative. Non-significant results should be
  reported and discussed visibly.
- **Implications for the design.** The task asks for "the size of effect the data can
  rule out". Report the 95% CI bounds in dollars and as a percentage of the control
  mean. Pre-specify a smallest effect of interest so that a null can be read as
  informative.

### Card, Kluve & Weber (2018) `[card2018]`, abstract
- **What it shows.** Across more than 200 recent evaluations of active labour market
  programs, average impacts are "close to zero in the short run" and become more
  positive 2-3 years after the program. Programs that emphasize human capital show
  larger gains.
- **Implications for the design.** A small or zero effect on 1978 earnings, one year
  after a 1976-77 program, is a priori plausible. re79 gives a slightly longer horizon,
  and the plan should state in advance how re78 and re79 relate (primary versus
  secondary).

---

## 9. Design implications (summary for the Econometrician and PI)

1. **Estimand.** The question and H1 ask about earnings "relative to what participants
   would have earned without the program", which is the ATT.
   - Fix the ATT on re78 as primary, with the outcome in the file's dollar units.
   - If trimming is used, name the trimmed estimand (Crump et al. 2009; Imbens &
     Wooldridge 2009).
2. **Identifying assumption.** Unconfoundedness given the pre-program covariates:
   - age, educ, married, urban, region, children, health_limit
   - re74, re75, unemp74, unemp75

   The two earnings lags matter (LaLonde 1986; Dehejia & Wahba 1999). The survey items
   are not clearly pre-program, so do not condition on them unless the data team
   confirms when they were measured.
3. **Primary estimator.** Doubly robust AIPW for the ATT (Robins et al. 1994; Bang &
   Robins 2005), optionally cross-fitted with flexible learners (Chernozhukov et al.
   2018).
   - Fix the propensity and outcome models, learners, folds and seed at the design
     gate.
   - Secondary estimators: IPW, propensity-score matching and OLS with covariates. All
     are reported, none is chosen afterwards.
4. **Outcome-blind diagnostics, before the gate.**
   - Normalized differences, flagging any above 0.25.
   - Propensity histograms by treatment status.
   - Counts of units outside [0.1, 0.9].

   (Imbens & Wooldridge 2009; Dehejia & Wahba 2002.)
5. **Falsification.** A pseudo-outcome test on re75, conditioning on re74 and the
   static covariates (Imbens 2004 §5.1).
6. **Robustness, fixed in advance and all reported.**
   - Trimming at [0.1, 0.9].
   - Alternative propensity covariate sets (Smith & Todd 2005; Dehejia 2005).
   - A difference-style outcome, re78 minus re75 (Smith & Todd 2005).
   - A sensitivity analysis for unobserved confounding (Imbens 2003).
7. **Multiple testing.** Declare the families. Use Romano-Wolf FWER for the
   labour-market family and BH FDR or a summary index for wellbeing78 and the 20 survey
   items. Report adjusted and unadjusted p-values (Anderson 2008; Romano & Wolf 2005;
   Benjamini & Hochberg 1995).
8. **Inference.** Treatment varies at the individual level, so use
   heteroskedasticity-robust (or influence-function) standard errors. Clustering is not
   needed unless assignment is shown to vary by region.
9. **Reporting a possible null.** Give the 95% CI in dollars and as a percentage of
   the control-group mean, and state the largest effect it rules out (Abadie 2020).
   Compare it with the NSW magnitudes only as context, never as ground truth.
10. **Pre-registration framing.** Cite Burlig (2018) and Olken (2015) for fixing the
    plan before outcomes are opened, and Coffman & Niederle (2015) for its limits.
    Disclose that the data are synthetic.

---

## 10. Unverified / not used

- **Heckman, Ichimura & Todd (1997, 1998); Heckman, LaLonde & Smith (1999 Handbook
  chapter).** Relevant, but not fetched, so not cited.
- **Rosenbaum-style sensitivity analysis and Oster (2019).** Not fetched. Imbens (2003)
  is cited for sensitivity instead.
- **Westfall-Young resampling and Benjamini, Krieger & Yekutieli (2006) sharpened
  q-values.** Not fetched. If the design uses sharpened q-values, the Scout must verify
  this source first.
- **Smith & Todd (2005).** The journal full text is paywalled, so specific numbers are
  taken only from the working paper (none are quoted here). The findings are cited from
  the published abstract.
- **LaLonde (1986).** Full text was read from a third-party scan (gwern.net), not from
  JSTOR. Metadata comes from IDEAS. The article has no DOI.
- **Dehejia & Wahba (1999, 2002), Imbens (2004), Imbens & Wooldridge (2009) and Crump et
  al. (2009).** Read in their NBER working-paper versions. Numbers may differ slightly
  from the journal versions, and the journal title of Crump et al. differs from the
  working-paper title.
