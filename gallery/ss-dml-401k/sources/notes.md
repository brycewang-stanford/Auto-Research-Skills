# Scout notes: ss-dml-401k (task q-novelty)

Compiled by the Scout on 2026-11-18. Every number below was read from a fetched document;
where it comes from is given next to it. I did not open the seed's `answer.json`.

## 1. Target: Chernozhukov et al. (2018), 401(k) eligibility application

Source read: arXiv:1608.00060v7 (3 Nov 2024), full PDF, Section 6.2 (pp. 41-44 of the
preprint). Metadata (journal, volume 21(1), pages C1-C68, DOI 10.1111/ectj.12097) from
Crossref. I also compared Table 2 with the journal's HTML (academic.oup.com, article
5056401) and every Table 2 value in both panels (estimates and both SE rows) matches the arXiv text. Table number and panel are the
same in both versions. `[chernozhukov2018dml]`

### Published partially linear (PLR) estimates: Table 2, Panel B

"Estimated Effect of 401(k) Eligibility on Net Financial Assets", Panel B "Partially
Linear Regression Model". DML2 estimator, 100 sample splits, point estimate is the
median over splits. `[brackets]` give the median SE across splits; `(parentheses)` give
the SE adjusted for variation across splits by the median method (eq. 3.14). US dollars.

| Cross-fitting | Lasso | Reg. Tree | Forest | Boosting | Neural Net | Ensemble | Best |
|---|---|---|---|---|---|---|---|
| 2-fold estimate | 7717 | 8709 | 9116 | 8759 | 8950 | 9010 | 9125 |
| 2-fold [median SE] | [1346] | [1363] | [1302] | [1339] | [1335] | [1309] | [1304] |
| 2-fold (adjusted SE) | (1749) | (1427) | (1377) | (1382) | (1408) | (1344) | (1357) |
| 5-fold estimate | 8187 | 8871 | 9247 | 9110 | 9038 | 9166 | 9215 |
| 5-fold [median SE] | [1298] | [1358] | [1295] | [1314] | [1322] | [1299] | [1294] |
| 5-fold (adjusted SE) | (1558) | (1418) | (1328) | (1328) | (1355) | (1310) | (1312) |

For context, the same table's Panel A (interactive model, ATE, propensity trimmed at
0.01/0.99) reports 5-fold estimates of 7170 (Lasso), 7993, 8105, 7713, 7788, 7839 and
7753 (Best). Table 3 reports the LATE of participation (5-fold Forest 11764). The
estimate with no controls is $19,559 (SE 1,413) (text, p. 43).

### Specification as stated in the paper

- **Outcome Y:** net financial assets: IRA balances + 401(k) balances + checking
  accounts + U.S. saving bonds + other interest-earning accounts + other interest-earning
  assets + stocks + mutual funds, minus non-mortgage debt.
- **Treatment D:** indicator for eligibility to enroll in a 401(k) plan.
- **Controls X (raw):** age, income, family size, years of education, married indicator,
  two-earner indicator, defined-benefit pension indicator, IRA participation indicator,
  home ownership indicator (9 variables).
- **Model:** PLR, Y = D·θ0 + g0(X) + U, D = m0(X) + V (eqs. 1.1-1.2 / 4.1-4.2).
- **Data:** "the same data as in Chernozhukov and Hansen (2004)"; the identification
  argument is attributed to Poterba et al. (1994a, 1994b), who the paper says use the
  1991 SIPP.
- **Learners:** same as the Bonus example (Section 6.1) with one change. Reg. Tree is
  one CART tree, penalty chosen by 10-fold CV. Forest has 1000 trees. Boosting uses
  boosted regression trees with parameters chosen by 10-fold CV. The neural net has
  **8 neurons and decay 0.01** in the 401(k) example. Lasso uses the Belloni et al. (2012)
  data-driven penalty on an expanded dictionary; the other learners use the raw
  covariates. Ensemble is a weighted average of Lasso, Boosting, Forest and Neural Net,
  with weights summing to one, chosen by 5-fold CV MSE. Best picks, separately for each
  nuisance function, the method with the best out-of-sample prediction.
- **Cross-fitting:** DML2 (Definition 3.2): one pooled solution of the averaged score
  over K folds. K = 2 and K = 5 are reported separately.
- **Repeated splits and aggregation:** S = 100 random partitions. Point estimate =
  median of the 100 estimates. SE in parentheses = sqrt of median{σ̂²_s + (θ̂_s −
  θ̃_median)²} (Definition 3.3, eq. 3.14). SE in brackets = median of the per-split SEs.

### Details the paper text does NOT state (taken from the authors' public code instead)

From `https://github.com/VC2015/DMLonGitHub`, files `401K.R` and `Moment_Functions.R`,
read on 2026-11-18. The repository was last pushed 2018-05-07. `[dmlongithub]`

- **Sample size:** the paper text does not give N. The seed brief, ddml (Ahrens et al.
  2024, Sec. 6.1: "n = 9915 households from the 1991 SIPP") and the DoubleML 401(k)
  example (9,915 observations) all agree. Treat **N = 9,915** as confirmed by two
  secondary sources, not by the 2018 paper itself.
- **Variable names in `sipp1991.dta`:** `net_tfa` (Y), `e401` (D), `age inc educ fsize
  marr twoearn db pira hown` (X). `p401` (participation) is used for the LATE.
- **Data provenance stated in code:** "Data source: SIPP 1991 (Abadie, 2003)"; "the
  sample selection and variable construction follow Abadie (2003)". `[abadie2003]`
- **PLR score:** the code estimates θ by an OLS regression without intercept of the
  outcome residual on the treatment residual (`lm(ry ~ rz - 1)`), pooled across folds,
  with HC standard errors (`vcovHC(type='HC')`). This is the Robinson partialling-out
  score (paper eq. 4.4), not the score in eq. 4.3. DoubleML's `score='partialling out'`
  matches it.
- **Lasso dictionary in code:** `(poly(age,6) + poly(inc,8) + poly(educ,4) +
  poly(fsize,2) + marr + twoearn + db + pira + hown)^2`, i.e. raw polynomials plus all
  pairwise interactions, fitted with `hdm::rlasso(post = FALSE)`, heteroskedastic penalty. 401K.R *passes*
  c = 1.1, but the *effective* c depends on the hdm version (see `sources/hdm_penalty.md`).
  It is 0.5 for the Y lasso in hdm 0.2.0, the CRAN release current when the Table 2 numbers
  were produced (Dec 2016 to Jun 2017), and in 0.3.1 and 0.3.2. It is 1.1 only in 0.2.3
  (released 2018-01-23). It is 0.5 with a different λ0 formula, about 0.62 in qnorm terms,
  in 0.1.0. The D logistic lasso (`rlassologit`) uses c = 1.1 in every version. The
  authors' installed hdm version is not recorded anywhere.
  The paper text does not give this dictionary for the 401(k) example.
- **Other tuning in code:** Boosting is gbm with 1000 trees, shrinkage 0.01,
  interaction depth 2, bag fraction 0.5 and 5-fold CV. Forest is randomForest with 1000
  trees and node size 5 (regression) or 1 (classification). The neural net is nnet with
  size 8, decay 0.01 and maxit 1000. The trees are rpart. Seed `set.seed(1211)`. The
  public `401K.R` runs `nfold=2`; the 5-fold column needs `nfold=5`.

### Where the data can be downloaded, and terms

- `https://github.com/VC2015/DMLonGitHub/raw/master/sipp1991.dta` (260,726 bytes per the
  GitHub API listing). This is the URL that DoubleML's `fetch_401K()` reads
  (`doubleml/datasets/fetch_401K.py` on the `main` branch). I did not download the data;
  that is the Econometrician's job.
- **License/terms:** the repository's `LICENSE.Rmd` is an MIT-style permission notice,
  "Copyright 2017 Victor Chernozhukov, Denis Chetverikov, Mert Demirer, Esther Duflo,
  Whitney Newey, James Robins", granted for "this software and associated documentation
  files". GitHub reports the license as "Other" (NOASSERTION). No separate data license
  is stated. The underlying SIPP is a U.S. Census Bureau public-use survey. Record the
  license in the manifest as "MIT-style notice on the replication repository; no
  explicit data license; derived from public-use SIPP 1991".

## 2. Other verified sources

- **Chernozhukov & Hansen (2004)**, REStat 86(3):735-751. `[chernozhukov2004]` Read:
  Crossref metadata and the IDEAS abstract; the full text is paywalled. The paper
  instruments 401(k) participation with eligibility in SIPP data and estimates quantile
  treatment effects on wealth measures. Effects on net financial assets are positive and
  significant across the distribution, with evidence of substitution in the upper tail.
  The 2018 paper names this as the source of its data. I could not confirm N or the
  SIPP wave from its own text.
- **Poterba, Venti & Wise (1994)**, "401(k) Plans and Tax-Deferred Saving", in Wise
  (ed.), *Studies in the Economics of Aging*, pp. 105-142. `[poterba1994]` Read: full
  NBER chapter PDF. It uses the **1984, 1985 and 1986 SIPP panels** (covering 1984 and
  1987), not the 1991 SIPP.
- **Poterba, Venti & Wise (1995)**, JPubE 58(1):1-32. `[poterba1995]` Read: Crossref
  metadata and the IDEAS abstract. The 2018 paper cites it as "1994b", but Crossref dates
  the issue to September 1995. It uses the 1984, 1987 and 1991 SIPP and finds little
  evidence that 401(k) contributions crowd out other personal saving.
- **Abadie (2003)**, J. Econometrics 113(2):231-263. `[abadie2003]` Crossref metadata
  only. It is cited only because the authors' code names it as the sample's origin.
- **Bach, Chernozhukov, Kurz & Spindler (2022)**, JMLR 23(53):1-6, DoubleML for Python.
  `[bach2022doubleml]` Full text read. It implements DML, is MIT-licensed, and is built
  on scikit-learn.
- **Bach, Kurz, Chernozhukov, Spindler & Klaassen (2024)**, JSS 108(3), DoubleML for R.
  `[bach2024doublemlr]` Full text read. It presents 401(k) as the motivating PLR example
  and points to an online 401(k) vignette. Its worked code example uses the Bonus data.
- **Chernozhukov et al. (2017)**, AER P&P 107(5):261-265. `[chernozhukov2017aerpp]`
  Crossref metadata; the appendix was read from arXiv:1701.08687v1. It is an earlier run
  of the same 401(k) exercise by the same authors, with Table 1 (mean over splits) and
  Table 2 (median over splits). Its Table 2, Panel B (PLR, median), 5-fold row is
  8202 (1581), 8894 (1440), 9252 (1400), 9089 (1378), 9065 (1393), 9199 (1379) and 9232
  (1359). Its 2-fold row is 7707, 8770, 9204, 8746, 9104, 9061 and 9129. Compared with the 2018
  Table 2, Panel B, the gaps for the five in-scope learners are $5-27 in the 5-fold row
  (lasso +15, tree +23, forest +5, boosting −21, nnet +27) and $10-154 in the 2-fold row
  (lasso −10, tree +61, forest +88, boosting −13, nnet +154). Their RMS over the ten cells
  is $61.15. *Corrected 2026-11-19 (paper-r2 F9):* earlier versions of these notes said
  "at most $33" for 5 folds. $33 is the out-of-scope Ensemble column (9199 vs 9166). The
  earlier run's code and splits are not public; the repository history starts on
  2017-06-01. So whether these gaps are split noise, code or version changes, or both is
  unknown. Only the preprint arXiv:1701.08687v1 was read, not the appendix of the
  published AER P&P article.
- **Ahrens, Hansen, Schaffer & Wiemann (2024)**, Stata Journal 24(1):3-45, ddml.
  `[ahrens2024ddml]` Text from arXiv:2301.09397v3. In Sec. 6.1 the 401(k) PLR on
  `sipp1991.dta` has n = 9915, 4 folds and 1 resample, with robust SEs. The short-stacked
  estimate is 9748.788 (1331.364). Across 9 learner pairs the estimates range from
  5986.657 (OLS/OLS) to 10103.630. The paper does not compare with the 2018 Table 2.
- **Chernozhukov, Hansen, Kallus, Spindler & Syrgkanis (2024)**, *Applied Causal
  Inference Powered by ML and AI* (arXiv:2403.02467 v0.1.1). `[chernozhukov2024causalml]`
  Ch. 10, Table 10.4, reprints the 2018 5-fold results. **Discrepancy:** its "Lasso"
  column shows 8871 (PLR) and 7993 (IRM), which are the 2018 *Reg. Tree* values. The 2018
  Lasso values (8187 PLR, 7170 IRM) are missing. Use the 2018 paper, not the book, as
  the benchmark.
- **Chernozhukov, Cinelli, Newey, Sharma & Syrgkanis (2026)**, "Long Story Short",
  REStat (advance article, DOI 10.1162/REST.a.1705). `[chernozhukov2026lss]` Text from
  arXiv:2112.13398v6. Table 1 gives a PLM DML random-forest estimate of 9,002 (1,394) and
  an NPM estimate of 7,949 (1,245), plus sensitivity bounds. The covariate list in the
  text omits the defined-benefit indicator.
- **DoubleML documentation, "Python: Impact of 401(k) on Financial Wealth"**.
  `[doubleml401kdocs]` Read through a fetch tool. Data from `fetch_401K`, N = 9,915. PLR
  uses 3-fold cross-fitting, with n_rep not set. Results: Lasso basic 5,722.46
  (1,380.58), Lasso flexible 8,974.79 (1,324.32), Random forest 8,909.63 (1,321.82),
  Tree 8,260.06 (1,348.62), XGBoost 8,336.66 (1,391.03). The page does not compare with
  the 2018 Table 2. These values come from a summarizing fetch, so the Econometrician
  should not treat them as authoritative.

### Added 2026-11-19 (review paper-r1)

- **Earlier run's SEs.** In arXiv:1701.08687v1 (appendix Table 2, PDF p. 17) and
  arXiv:1608.00060v4 (Table 2, PDF p. 28), the numbers are the same. The parenthesized
  SE is σ̂_Median, the median over splits of sqrt(σ̂_s² + (θ̂_s − θ̂_median)²). This is the
  **split-adjusted** SE, the same concept as the 2018 parenthesized row (eq. 3.14). No
  bracketed per-split median SE is reported, so the 2017 split spread cannot be backed
  out on its own.
  - Lasso 5-fold: 8,202 (1,581) in 2017 vs 8,187 (1,558) in 2018.
  - Lasso 2-fold: 7,707 (1,785) vs 7,717 (1,749).
- **Which source to cite for the earlier run.** Cite `[chernozhukov2017aerpp]` (whose
  appendix table was read) and/or the new `[chernozhukov2016dmlv4]` (arXiv v4), not
  `[chernozhukov2018dml]`. The 2018 article does not contain those numbers; cite it only
  for the 2018 values. The statement that the Table 2 numbers first appear in v5 rests on
  `[chernozhukov2018dml]` (arXiv versions read), and the v4 contents on
  `[chernozhukov2016dmlv4]`.
- **Abadie's income band.** It is sourced to `[abadie2000]`, NBER Technical Working Paper
  260, which I read in full. Section 6 and the Table I note give 9,275 SIPP 1991
  observations with family income in $10,000-$200,000.
- **Pages read through a summarising fetch tool.** `doubleml401kdocs`,
  `doubleml401krdocs` and `mendez2026` are marked in `sources.json` (`fulltext_via`). They
  were read through a model summary, not as raw text.

## 3. Discrepancies to carry forward

1. **SIPP year of Poterba et al.** The 2018 paper says Poterba et al. (1994a, 1994b) "use
   data from the 1991 SIPP". The 1994 chapter actually uses the 1984-86 SIPP panels; the
   1995 JPubE article uses 1984, 1987 and 1991. Do not repeat the 2018 sentence as fact.
2. **Citation year.** The JPubE article is 1995 (Crossref), although the 2018 paper calls
   it 1994b.
3. **Data lineage.** The 2018 paper says the data are those of Chernozhukov & Hansen
   (2004). The authors' code says the sample follows Abadie (2003). Both are consistent
   with the single public file `sipp1991.dta`.
4. **N is not in the 2018 text.** 9,915 is stated by Belloni et al. (2017, Sec. 7: "9,915
   observations at the household level drawn from the 1991 SIPP", same data as
   Chernozhukov & Hansen 2004). Two of the 2018 authors are co-authors there. ddml,
   DoubleML docs and the seed brief agree.
5. **PLR score and Lasso dictionary** are only in the code, not the paper (see above).
6. **Version drift.** The published numbers match arXiv v7 exactly. The 2017 AER P&P run
   differs by $5-27 (5-fold) and $10-154 (2-fold) on the five in-scope learners. The CausalML book reprint has a column error.

## 4. Unverified / not added

- Chernozhukov & Hansen (2004) full text (paywalled): N, SIPP wave and variable
  construction were not checked against it directly. Belloni et al. (2017) restates them.
- Poterba, Venti & Wise (1995) full text: ScienceDirect returned 403. NBER WP 4391 was
  downloaded but is a scanned PDF with no text layer.
- Abadie (2003): metadata only; its sample description was not read.
- Christian Hansen's 2004 MIT PhD thesis (DSpace 1721.1/29431): metadata only, not
  added.
- The AER P&P published PDF itself: aeaweb returned HTML. Numbers come from the arXiv
  preprint.
- The supplementary appendices of Belloni et al. (2017) and of the 2018 paper were not
  read.

## 4a. Sources read for review finding F9 (2026-11-18)

I read each item below to test the claim that no cell-by-cell replication of Table 2,
Panel B exists.

| Source | Read | What it does with the 401(k) data | Cell-by-cell Table 2 replication? |
|---|---|---|---|
| Belloni et al. (2017) `[belloni2017]` | arXiv v8 full text, Sec. 7 | N = 9,915 (1991 SIPP), Y = net financial assets. Estimates ATE/LATE/QTE with post-lasso on 35/311/1756-term dictionaries, without cross-fitting. Predates the 2018 paper. | No. Different estimator; it is not a replication. |
| Wüthrich & Zhu (2023) `[wuthrich2023]` | arXiv v9 full text, Sec. 5.2.1 | N = 9,915. Y = **total wealth**. Post double lasso on 167/272 controls, plus subsampling to study omitted-variable bias. | No. Different outcome and estimator. |
| DoubleML R vignette `[doubleml401krdocs]` | fetched page | PLR with 3 folds (n_rep not stated). glmnet basic 6133 (1465), glmnet flexible 9580 (1325), ranger 9127 (1313), rpart 8210 (1324), xgboost 8700 (1360). Says the `polynomial_features` option "can be used to replicate the models" of the 2018 paper but reports no comparison. | No |
| Mendez (2026) online tutorial `[mendez2026]` | fetched page | DoubleML Python with 3 folds in code, although the text says 5. PLR: Lasso 9,370.81 (1,326.47), RF 8,835.46 (1,309.07), Tree 7,822.51 (1,321.78), XGBoost 8,892.39 (1,398.65). Cites the 2018 paper only in the references. | No |
| Ahrens et al. (2025, JAE) `[ahrens2025modelavg]` | arXiv v2 full text | Uses the 401(k) data to calibrate a Monte Carlo study of stacking, and replicates a Wüthrich & Zhu figure. | No |
| Ahrens et al. (2026) DML introduction `[ahrens2025intro]` | arXiv v2 full text | 401(k)-calibrated simulation on the 9,915 observations. | No |
| Raina, Erasmus BSc thesis (thesis.eur.nl/pub/73637) | full PDF | Simulation study replicating Belloni et al. (2011). It never uses the 401(k) data: the only "401" in the text is a page number. Not added to `refs.bib`. | No |
| The carlos-mendez.rbind.io "web_app" page from the first search | not read separately | It is the interactive companion of the Mendez tutorial above. | n/a |

I also ran an extended web search for replications of Table 2 with 2-/5-fold, 100-split
median aggregation. It returned only the original papers and the items above. This is a
search of the open web, arXiv and documentation sites, not of GitHub code or
unpublished course materials. **The claim therefore stands, but only as "none of the
sources we found and read".**

## 5. Novelty / replication-status verdict

Revised 2026-11-18 after review question-r1, against the current `plan.json` question
and hypotheses.

**Partly answered: the effect is known; the cell-by-cell reproduction is not.**

- The PLR coefficient on eligibility is well established. The authors themselves ran
  the exercise twice (AER P&P 2017; Econometrics Journal 2018). DML re-estimates of the
  same 401(k) PLR on the same `sipp1991.dta` exist in:
  - ddml (Ahrens et al. 2024): 9,749
  - Long Story Short (Chernozhukov et al. 2026): 9,002
  - the DoubleML Python and R documentation: 8,910 and 9,127 with random forests
  - an online tutorial (Mendez 2026): 8,835 with random forests
  - the CausalML textbook, which reprints the 2018 table

  All of these are positive and significant, at roughly $8-10k. **H1 is a sanity check
  whose answer is already known**, which is how the current plan labels it.
- **None of the sources we found and read** reproduces Table 2, Panel B cell by cell
  under its protocol: K = 2 and 5, S = 100 splits with median aggregation, and the
  eq. 3.14 SE, compared side by side with the published cells. ddml uses 4 folds and 1
  resample. DoubleML Python/R and Mendez use 3 folds with no stated repetitions. Long
  Story Short reports one forest estimate. Belloni et al. (2017) and Wüthrich & Zhu
  (2023) use other estimators, and Wüthrich & Zhu use another outcome. Ahrens et al.
  (2025, 2026) use the data only to calibrate simulations. See §4a. Code-only replications
  on GitHub or in course materials were not searched systematically, so the absence claim
  is limited to the literature and documentation we read.
- So the current question is not done yet: an implementation written by the crew with
  scikit-learn learners, checked cell by cell for 5 learners x 2 fold counts. It is
  incremental, not new knowledge about 401(k) plans.
- **Closest prior work:**
  - Chernozhukov et al. (2017, AER P&P), a second run by the same authors. Compared with
    2018, its PLR median estimates differ by $5-27 at 5 folds and by $10-154 at 2 folds
    (five in-scope learners; read from the preprint arXiv:1701.08687v1 only).
  - Ahrens et al. (2024, ddml): same data and model, but not the published protocol.
- **Implications for the current hypotheses:**
  - **H2** (re-done 2026-11-18 for review question-r3, F14). This follows `plan.json`
    hypotheses[1], which is authoritative; this section only illustrates it.
    - MAD = sqrt(SE_adj^2 − SE_med^2) from the published Panel B (parenthesized and
      bracketed rows).
    - sd_split = 1.4826·MAD.
    - SE of a median over S splits = 1.2533·sd_split/sqrt(S).
    - Tolerance = **2.81**·sqrt(se_rep^2 + se_pub^2), with S = 100 on the published side.
    - A tolerance above **$1,000** means "not testable at this resolution" (NT).
    - The replication's S is fixed per learner at the design gate; the plan puts lasso
      and tree at 100.

    The table shows the replication side at S = 10, 20 and 100.

    | Learner | K | Published | [med SE] | (adj SE) | MAD | sd_split | se_pub (S=100) | tol S=10 | tol S=20 | tol S=100 |
    |---|---|---|---|---|---|---|---|---|---|---|
    | lasso | 2 | 7717 | 1346 | 1749 | 1117 | 1656 | 207.5 | 1934 (NT) | 1428 (NT) | 825 |
    | tree | 2 | 8709 | 1363 | 1427 | 423 | 626 | 78.5 | 732 | 540 | 312 |
    | forest | 2 | 9116 | 1302 | 1377 | 448 | 665 | 83.3 | 776 | 573 | 331 |
    | boosting | 2 | 8759 | 1339 | 1382 | 342 | 507 | 63.6 | 592 | 437 | 253 |
    | nnet | 2 | 8950 | 1335 | 1408 | 447 | 663 | 83.1 | 775 | 572 | 330 |
    | lasso | 5 | 8187 | 1298 | 1558 | 862 | 1278 | 160.1 | 1492 (NT) | 1102 (NT) | 636 |
    | tree | 5 | 8871 | 1358 | 1418 | 408 | 605 | 75.8 | 707 | 522 | 301 |
    | forest | 5 | 9247 | 1295 | 1328 | 294 | 436 | 54.7 | 509 | 376 | 217 |
    | boosting | 5 | 9110 | 1314 | 1328 | 192 | 285 | 35.7 | 333 | 246 | 142 |
    | nnet | 5 | 9038 | 1322 | 1355 | 297 | 441 | 55.2 | 515 | 380 | 219 |

    **2017 vs 2018 runs by the authors** (both use S = 100, so the S = 100 column
    applies). Every gap is well inside its tolerance:

    | Cell | Gap | Tolerance |
    |---|---|---|
    | lasso, K=2 | −10 | 825 |
    | tree, K=2 | +61 | 312 |
    | forest, K=2 | +88 | 331 |
    | boosting, K=2 | −13 | 253 |
    | nnet, K=2 | +154 | 330 |
    | lasso, K=5 | +15 | 636 |
    | tree, K=5 | +23 | 301 |
    | forest, K=5 | +5 | 217 |
    | boosting, K=5 | −21 | 142 |
    | nnet, K=5 | +27 | 219 |

    The nnet 2-fold gap of 154 is less than half its corrected tolerance of 330. This
    replaces the earlier, wrong figure of 159.

    **Prior off-protocol estimates against the 5-fold cells.** These are illustrative
    only. Those runs used 3 or 4 folds, a single split or an unstated number, and their
    own dictionaries, so they are not real H2 tests.

    | Estimate | Cell | Difference | S = 10 | S = 20 | S = 100 |
    |---|---|---|---|---|---|
    | DoubleML Python RF | forest | −337 | pass | pass | fail |
    | Long Story Short RF | forest | −245 | pass | pass | fail |
    | ddml rforest/rforest | forest | +281 | pass | pass | fail |
    | DoubleML R ranger | forest | −120 | pass | pass | pass |
    | Mendez RF | forest | −412 | pass | fail | fail |
    | DoubleML Python tree | tree | −611 | pass | fail | fail |
    | DoubleML R rpart | tree | −661 | pass | fail | fail |
    | Mendez tree | tree | −1,048 | fail | fail | fail |
    | Mendez XGB | boosting | −218 | pass | pass | fail |
    | DoubleML R xgboost | boosting | −410 | fail | fail | fail |
    | DoubleML Python XGB | boosting | −773 | fail | fail | fail |
    | DoubleML Python lasso (flexible) | lasso | +788 | NT | NT | fail |
    | DoubleML R lasso (flexible) | lasso | +1,393 | NT | NT | fail |
    | Mendez lasso | lasso | +1,184 | NT | NT | fail |
    | DoubleML lasso (basic), both | lasso | −2,465 / −2,054 | NT | NT | fail |

    So at the S the budget allows for forest and boosting (about 10-20), most
    off-protocol forest estimates **would pass**, including DoubleML Python 3-fold RF at
    −337, inside 376-509. The earlier statement that they "would not all pass" was
    wrong. Most boosting and some tree estimates would still fail. At 2 folds the forest
    and tree estimates pass more often, because the bands there are wider (forest
    573-776, tree 540-732 at S = 20/10). H2 can tell such implementations apart from the
    published cells mainly where S is near 100: lasso, tree and possibly nnet under the
    plan.
  - **H3** now requires, at each fold count, lasso < each of the four flexible learners.
    It holds in the published table at both K: 2-fold 7717 < 8709, 8759, 8950, 9116;
    5-fold 8187 < 8871, 9038, 9110, 9247.
- **Seed requirement (updated seed task):** the seed now asks for one result claim
  **per learner and fold count**, with id `plr-<learner>-<k>fold`, learner in {lasso,
  tree, forest, boosting, nnet} and k in {2, 5}. That makes 10 claims, each valued as the
  PLR coefficient on eligibility in 1991 US dollars. Each maps one-to-one to a cell of
  the table above. Ensemble and Best are not part of the seed or the plan.
