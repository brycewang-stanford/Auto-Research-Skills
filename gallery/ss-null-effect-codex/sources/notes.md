# Question-stage literature check

Scope: quick novelty and positioning check, 2026-11-21. Read plan.json, crew.json, seed task.json, PROTOCOL.md and social-science track. No outcome data, answer keys, estimates or analysis were inspected. This is not a systematic review or a replication of a published estimate.

## Novelty verdict

Already answered as a general methodological question: evaluating training effects with observational earnings data and diagnosing its limitations are established topics. The exact synthetic cohort has no verified published evaluation in this targeted search; that does not create substantive or methodological novelty. Closest prior work: LaLonde (1986), Dehejia and Wahba (1999), and Imbens and Xu (2025 version). The proposed distinction between nonsignificance and practical equivalence is also established (Lakens 2017).

What this exercise can add is a reproducible, prospectively specified application to the supplied synthetic cohort, with transparent uncertainty, reporting of all examined outcomes and multiplicity handling. It cannot estimate the actual historical NSW effect or demonstrate that a causal method generally works. Similar calendar years and variable names do not establish that this is NSW data.

## Verified sources

### lalonde1986
Primary text fetched from the author-hosted NBER teaching copy of the AER article; title page verifies author, year, venue, volume, issue and pages. Opening abstract (p. 604): compares nonexperimental earnings estimates with an experimental training benchmark and finds many procedures fail to reproduce it. Relevant as the foundational warning about specification dependence. No numerical estimate is attributed here. Princeton's institutional working-paper abstract was also opened; it is dated 1984, so its date was not substituted for the 1986 journal article.

### dehejiawahba1999
Primary text fetched from Dehejia's NBER page; first page verifies authors, title, 1999 JASA volume/issue and start page, with the document running through p. 1062. Abstract (p. 1053): propensity-score comparisons approach the experimental benchmark more closely in their application, conditional on observed assignment variables and overlap. Sensitivity to selection-on-observables remains. Relevant as the closest established observational training example; it does not validate ignorability in this synthetic cohort. DOI omitted rather than inferred.

### imbensxu2025
Author-submitted arXiv abstract and version history fetched; version 3 revised May 27, 2025. Listed as preprint, not an asserted journal publication. Abstract: revisits LaLonde; modern methods with overlap can deliver stable adjusted differences without ensuring causal interpretation. Assignment-process scrutiny and validation exercises remain necessary. This directly weakens any claim that a modern estimator alone makes the exercise novel or causal. No full-text-specific claims made.

### lakens2017
Publisher PDF fetched from the author's university repository; cover and first article page verify metadata and DOI. Abstract and discussion of confidence intervals (article pp. 355–357): nonsignificance does not demonstrate absence of a meaningful effect; TOST uses prespecified meaningful bounds, and significance and equivalence answer distinct questions. Relevant for framing H1/H2. It supplies no justification for this project's 1000-unit threshold or its causal standard error.

## Concerns for question/design review

- Retain explicit synthetic status in title, abstract and conclusions. The track normally describes real public data; the seed explicitly authorizes synthetic data, so describe this as an evaluation exercise.
- Explain whether “enrolled adults” means the whole supplied cohort or program participants; ATT targets participants, not all adults. Define eligibility and treatment separately.
- Voluntary enrollment requires an explicit conditional counterfactual comparability assumption, overlap and a treatment definition with timing. Covariate balance cannot establish absence of unobserved selection.
- Justify equivalence bounds in the documented earnings units before outcomes are examined. A convenient 1000-unit choice is a sensitivity benchmark until substantively defended; do not claim it is historically meaningful dollars without metadata.
- Prespecify outcome families, multiplicity handling and inference for both superiority and equivalence. Applying a t-test primer to an adjusted ATT requires appropriate estimator-specific uncertainty.
- Failure to establish equivalence is inconclusive; even established equivalence is conditional on identifying assumptions and chosen bounds.

## Search and verification provenance

Used web search for primary training-evaluation and equivalence papers, then opened each recorded source. Searches included LaLonde evaluating econometric training evaluations, Dehejia/Wahba causal effects nonexperimental training, and Lakens equivalence primer. The search also returned the recent Imbens/Xu revisit, whose current arXiv version was opened. Bibliography records contain permanent public URLs and verification methods. Sources are linked by BibTeX key to claims.jsonl.

Unverified: no additional bibliography entries. NBER's working-paper landing page for Dehejia/Wahba returned HTTP 403 on open; the accessible author-hosted journal PDF independently verified the recorded source. PubMed's Lakens page returned only a site footer; the university-hosted publisher PDF independently verified the recorded source. No exhaustive novelty claim is warranted by this quick search.

# Design-stage supplement (2026-11-21)

Read the current plan, question-r1 review, protocol, social-science track and seed task metadata. No CSV, outcome data, answer keys or outcome estimates were read. The question-stage novelty verdict above remains: general methodology already answered; this is an application exercise, not a novel historical finding. Eight verified bibliography entries now cover identification, training-evaluation positioning, ATT estimation/inference, overlap, multiplicity and equivalence.

### rosenbaumrubin1983
Fetched the McGill-hosted scan of the original Biometrika article. Cover verifies title, authors, volume, issue, pages; publisher abstract listing independently verifies 1983. Method: propensity-score theory and observational adjustment. Finds that the score balances observed assignment covariates. The conditional-independence requirement remains substantive, not a conclusion from balance. For this design the ATT requires an untreated counterfactual for participants, consistency/no interference and adequate control support at participant covariate values. A sufficient condition is conditional ignorability; untreated-potential-outcome mean independence is enough for the ATT. This last distinction is design interpretation, not a claim that the paper validates this cohort.

### chernozhukov2017
Fetched MIT author manuscript in full and AEA article page for final journal metadata and DOI. Author manuscript PDF pp. 1–3: ATTE definition, orthogonal score equation (6), K-fold algorithm, score variance/normal interval, Assumption II.1 and Theorem II.1. Supplies direct support for an augmented ATT score using control outcome regression and propensity odds, with cross-fitting and score-based inference. Validity requires independent sampling, overlap, sufficient moments and nuisance convergence rates. Cross-fitting does not make these assumptions automatically true; flexible learners do not solve hidden selection. Do not cite this as a theorem validating arbitrary fixed logistic/linear working models, clustering by an arbitrary region label, or a finite-sample guarantee. Standard errors must reflect the actual estimator and sampling unit. This source is the six-author 2017 AER note, not the seven-author 2018 Econometrics Journal paper.

### crump2009
Fetched author-hosted accepted manuscript from Hotz's Duke page, title and four authors on PDF p. 1; journal year/volume/issue/pages/DOI verified against primary OUP abstract search listing. Manuscript explicitly says forthcoming in Biometrika; manuscript pagination differs from final article. PDF pp. 1–3 establish limited-overlap precision/specification concerns and that selecting an overlap subpopulation changes the target. Its symmetric trimming recommendation concerns an ATE precision problem; it is not a universal ATT prescription. For full-cohort participants' ATT, removing treated people changes the estimand. Clipping control odds can change the estimating equation and its bias; report this transparently as sensitivity, not a silent cure. Fix diagnostics and any restricted-target fallback prospectively. No outcome-dependent trimming is justified.

### holm1979
Fetched original six-page scan from University of Granada; rendered first page locally because text extraction is empty. Page 65 verifies author, title, year, journal, volume and pages, and abstract states familywise protection across configurations of true nulls. Method: sequentially rejective multiple testing. Supports strong familywise error control with valid individual p-values; dependence among this cohort's outcomes need not motivate pretending tests are independent. Prespecify the tested family and include every analyzed outcome; adjusted p-values do not make ordinary marginal confidence intervals simultaneous. The seed's twenty survey items should either remain unanalyzed or join an explicitly reported testing family. H1 and H2 address different propositions about the same estimand: any separate-family decision and joint-discovery interpretation must be explicit before outcomes are seen.

## Earnings scale and equivalence-bound evidence

The seed task calls re78 earnings and dates it to 1978, but specifies no currency, price base, hours conversion or program cost. Historical NSW papers are context, not calibration data for this synthetic cohort. LaLonde's Table 3 note b and footnote 9 (article p. 608) explicitly state 1982 dollars and discuss converting experimental-time earnings to annual earnings. That is evidence that metadata matter; it does not establish the seed's scale. No historical effect number is imported as a target or equivalence bound. This is not a replication task.

Lakens supplies the rationale for a prospectively justified smallest effect of interest, not an external justification for ±1000 here. With available metadata, ±1000 can honestly be a declared benchmark in supplied earnings units, with equivalence conditional on that convention. Describe it as benchmark equivalence, not absence of economically meaningful effects or an established policy threshold. A baseline-relative scale comparison can use only preprogram earnings summaries prepared without reading outcomes; such summaries characterize scale but cannot establish welfare relevance. No baseline summary or power calculation was performed by the Scout. The Designer should either supply independent substantive justification or explicitly retain this benchmark interpretation and a prospective precision calculation over declared hypothetical variances. Do not tune bounds to observed outcome variance, estimates or confidence intervals.

For a normal asymptotic ATT interval, TOST at 5% corresponds to the 90% interval lying strictly inside the fixed bounds. This adaptation needs the estimator-specific valid standard error, not an unadjusted two-sample t-test. Report the 95% interval in original units regardless of either decision; its endpoints describe compatibility conditional on identification and inference assumptions, not an unconditional guarantee about hidden bias.

## Verification limits and search record

Targeted searches covered propensity-score identification, ATTE orthogonal inference, limited overlap and Holm testing, including work challenging nonexperimental training evaluation. Failed accesses: Rutgers Hahn PDF redirected to an inaccessible page; no Hahn entry added. Harvard Crump PDF and OUP open/DOI redirects failed, so the full accepted manuscript was verified at Duke. The USP Holm PDF returned 403; the Granada scan was fetched and visually inspected instead. These access failures do not leave an unverified bibliography entry. The retained Imbens/Xu record remains abstract-only, so no fulltext numerical claims may be attributed to it. No source found independently validates synthetic earnings units, the ±1000 welfare threshold, or ignorability for the seed. Bibliography completeness is targeted rather than systematic.
