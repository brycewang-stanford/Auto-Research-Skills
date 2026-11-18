# Scout notes: cs-calibration (task `q-novelty`)

Scout, 2026-11-19. Bibliographic metadata comes from Crossref, OpenAlex, arXiv, PMLR,
NeurIPS, JMLR or ML Anthology pages fetched today, never from memory. `sources/sources.json`
gives the `method` for each entry and says what was read. Every number quoted below comes
from a fetched full text, and its location is given next to it. Where only the abstract
was read, nothing below goes beyond the abstract. I did not open the seed's `answer.json`
and downloaded no study data. Everything I say about the task comes from `task.json` and
`plan.json`.

**23 sources verified: 15 from full text, 6 from the abstract only, and 2 by DOI
resolution only.**

---

## 1. Novelty verdict: **largely answered; the remaining contribution is replication**

**Closest prior work**

- **Niculescu-Mizil & Caruana (2005)** [`niculescumizil2005`]. Same three ingredients:
  LR, RF and boosted trees (among 10 learners), calibrated with Platt scaling and
  isotonic regression on an independent calibration set, on 8 binary problems.
- **Fonseca & Lopes (2017)** [`fonseca2017`]. Almost exactly the crew's 3 × 3 grid: LR,
  RF and GBC × {none, sigmoid, isotonic}, with a separate 20% calibration split, on 18
  credit datasets. Brier score only, a chronological split, and no seeds.
- **Two 2026 benchmarks:**
  - **CalArena** [`berta2026`]: LR, RF, XGBoost, LightGBM and CatBoost on 104 binary
    TabRepo datasets.
  - **Manokhin & Grønhaug** [`manokhin2026`]: LR, RF, GBC, HGB and 17 others on 30 binary
    TabArena datasets.

  Both measure out-of-the-box calibration and Platt and isotonic calibration of these
  models with proper scoring rules, at far larger scale than this seed allows.

**What is already known**

- **The direction of H1.** On 8 problems, NM&C (2005, Sec. 4) found LR well calibrated
  out of the box. RF was "less clear cut": poorly or not well calibrated on 5 of 8
  problems, with predictions pushed toward the middle and sigmoid-shaped reliability
  plots. The scikit-learn user guide shows the same pattern [`sklearn_calibration_docs`,
  §1.16.1]. H1 is therefore a replication of a known result, not a new hypothesis.
  - Caveat: LR is well calibrated only when its model is roughly correct
    [`kull2017` §1; `sklearn_calibration_docs` §1.16.1, "well specified" and C "tuned
    to be appropriate"]. On a dataset with strong nonlinearity, H1 can fail.
- **H2 for exponential-loss boosting.** Platt and isotonic calibration strongly improve
  AdaBoost-style boosted trees [`niculescumizil2005boosting` Table 2: mean cross-entropy
  falls from 0.4836 to 0.3797 (Platt) and 0.3814 (isotonic)].
- **Calibration-set size.** Isotonic regression needs a large calibration set: Platt
  beats it below about 200–1000 cases [`niculescumizil2005` Sec. 5, Fig. 7].

**What is genuinely contested, and where this seed can add a careful data point**

- **H2 for random forests.** The evidence points both ways:
  - *Isotonic helps RF:* NM&C (2005, Sec. 5) say post-calibration helps RF "once the
    calibration sets are large enough". Fonseca & Lopes (2017, Sec. 4) find isotonic
    helps RF on credit data.
  - *Isotonic does not help, or hurts:* Boström (2008, Sec. 3) finds isotonic regression
    *slightly worsened* the Brier score of random forests of probability-estimation trees
    on 34 UCI datasets (the averaging RF in scikit-learn is of this kind). CalArena (2026,
    Sec. 6.1) finds no method consistently improves tuned TabRepo models, and binning
    methods degrade them. Manokhin & Grønhaug (2026, Sec. 2) find isotonic slightly
    *increases* log-loss in aggregate across models.
- **H2 for modern gradient-boosted trees.** Gradient-boosted trees fitted to log-loss with
  shrinkage (scikit-learn `HistGradientBoostingClassifier`) are not the
  exponential-loss boosted trees of 2005. The 2005 "boosting needs calibration" result
  does not carry over by default. The 2026 benchmarks report results pooled over models,
  so they give no clean, seed-resolved answer for HGB alone.

**Recommended framing.** The `contribution` line in `plan.json` ("small, controlled and
fully reproducible measurement … with uncertainty across seeds") is accurate. The paper
should present itself as:

- a pre-registered, seed-resolved *replication* of NM&C (2005) and Fonseca & Lopes
  (2017) on scikit-learn loader datasets, with current library defaults;
- a clean per-model test of H2 for RF and HGB, which the literature leaves contested.

It must not claim to discover that RF is under-confident or that recalibration helps.
Both are long known. The paper should also say its scale (≥3 datasets) is far smaller
than CalArena's 104 or TabArena's 30.

Nothing found makes the question pointless. The large benchmarks pool over models,
tune hyperparameters, and/or confound calibration with a smaller training set (see
D4). None reports per-model, per-dataset differences with seed uncertainty and a fixed
training set.

---

## 2. Design implications (for the PI and the design stage)

The Scout does not set the design. These points come from the sources and are listed
for the design author and the Reviewer.

- **D1. Primary metrics should be proper scores; binned ECE secondary, with its binning
  fixed in advance.**
  - *Binned ECE is unreliable.* Its value depends on the number and type of bins and is
    statistically biased [`roelofs2022` abstract and §1; `nixon2019` abstract]. The
    ranking of recalibration methods can flip with the choice of measure [`nixon2019`].
    Equal-mass bins have lower bias than equal-width bins [`roelofs2022`].
  - *Binned ECE tilts the Platt-vs-isotonic comparison toward isotonic.*
    - It underestimates the calibration error of continuous-output methods such as
      Platt scaling [`kumar2019` abstract, §1].
    - It favours binning-like calibrators, which includes isotonic's step functions
      [`berta2026` §5: "binned ECE estimators favor binning-based calibration functions
      and ignore refinement error"].
    - This bias cuts directly against the H2 comparison.
  - *Proper scores avoid the problem.* Log-loss and Brier score are strictly proper
    [`gneiting2007`; `brier1950`]. A post-hoc map cannot improve refinement, so the
    before/after change in a proper score is a clean measure of calibration gain
    [`berta2026` §5, "Post-Hoc Improvement"].
  - *Suggestion:* Brier and log-loss as primary, with the change relative to "none" as
    the effect. ECE as secondary, with the estimator fixed at the design gate: number of
    bins, equal-width or equal-mass, computed on P(y=1) and not on top-label confidence.
    Guo et al.'s ECE [`guo2017` §2] uses top-label confidence. For binary tasks the two
    differ, so the paper must say which it uses.
  - A debiased or equal-mass variant [`roelofs2022`] or CORP reliability diagrams
    [`dimitriadis2021`] could serve as a pre-declared sensitivity check.
- **D2. Isotonic regression can output exactly 0 or 1, which makes log-loss infinite.**
  NM&C kept predictions away from 0 and 1 [`niculescumizil2005boosting` fn. 1]. CalArena
  prefers Brier for this reason [`berta2026` §5]. The clipping epsilon must be fixed at
  the design gate, and the paper must report how often clipping was applied.
- **D3. Calibration-set size decides the Platt-vs-isotonic result.**
  - Isotonic needs about ≥1000 calibration cases to match or beat Platt
    [`niculescumizil2005` Fig. 7; `sklearn_calibration_docs` §1.16.3.2]. Below about
    200–1000 cases, Platt wins for all nine learners in NM&C.
  - A small built-in dataset (`load_breast_cancer` has 569 rows) gives a calibration
    split of roughly 100–200 cases. There isotonic is expected to lose for reasons of
    sample size, not model type.
  - The design should report the size of each calibration split and either choose
    datasets large enough or state this as a moderator.
- **D4. Hold the training set fixed across none, Platt and isotonic.**
  - Manokhin & Grønhaug carve the calibration set out of the training folds only for
    calibrated runs. They note this confounds the calibrator with "a reduced training
    set" [`manokhin2026` Sec. 2].
  - Fit each base model once per seed on the training split. Score "none" on the test
    split from that same model. Fit Platt and isotonic on the calibration split's
    predictions from that same model.
  - In scikit-learn, use `FrozenEstimator` (or fit the calibrators by hand), not the
    default `CalibratedClassifierCV(ensemble=True)`. The default refits one classifier
    per CV split and averages them, which changes the base model
    [`sklearn_calibration_docs` §1.16.3].
- **D5. Fix which score Platt scaling transforms.**
  - Logistic calibration on raw probability scores cannot represent the identity map, so
    it can uncalibrate an already calibrated model such as LR [`kull2017` abstract].
    CalArena finds "Platt-probs" degrades performance while Platt on logits is among the
    best binary methods [`berta2026` §6.1].
  - scikit-learn's sigmoid calibrator takes the classifier output "as given by
    decision_function or predict_proba" [`sklearn_calibration_docs` §1.16.2]. LR and HGB
    expose `decision_function`; RF does not. A default pipeline therefore applies Platt
    to logits for LR and HGB but to probabilities for RF.
  - The design should choose one input scale for all three models (logit of the clipped
    predicted probability is the natural choice) or report the difference. This is an
    inference from the docs text; the Engineer should confirm it in the pinned version.
- **D6. Report AUC as a control.** Isotonic introduces ties and can change ROC-AUC; Platt
  is strictly monotonic and preserves ranking [`sklearn_calibration_docs` §1.16.3.2].
  Report AUC alongside so readers can see whether a change in proper score comes from
  calibration or from lost discrimination [`berta2026` §5].
- **D7. Keep hyperparameter selection off the calibration and test splits.**
  - Caruana & Niculescu-Mizil (2006, Sec. 3) used the same 1000 cases both to calibrate
    and to select parameters. The seed task forbids the analogous shortcut: calibration
    data is "used neither for training nor for testing".
  - Either use fixed library defaults, stated at the design gate (simplest, and what
    Manokhin & Grønhaug did), or tune on a separate validation split. Do not tune on the
    calibration split.
  - Tuning changes calibration: CalArena tunes on validation ROC-AUC [`berta2026` §3],
    and Boström (2008, §3, citing his 2007 paper) notes pruning and smoothing settings
    change RF probability quality. "Out of the box" must be defined precisely.
- **D8. Seeds and splits.**
  - NM&C (2005) and Caruana (2006) used 5 trials. Manokhin & Grønhaug used 1×5-fold with
    no repetitions. The seed's ≥5 seeds already matches or exceeds this.
  - Each seed should redraw the train/calibration/test split *and* the model's random
    state, and the paper should say so. Report the mean and SD across seeds per dataset ×
    model × calibrator, plus paired differences relative to "none". Pairing on seed
    shares the split and model.
- **D9. Preprocessing.** Fit any scaling or encoding (LR needs standardised features to
  converge reliably) on the training split only. This is standard track practice
  (`tracks/cs.md`) rather than a source finding.

---

## 3. Source-by-source notes

### Recalibration methods

- **Platt (1999)** [`platt1999`, full text of the 1999 preprint]
  - *Finds:* passes SVM outputs through a sigmoid 1/(1+exp(Af+B)) with A and B fitted by
    maximum likelihood (§2.2, eq. 11–12). On p. 5, outputs on the training set are
    biased, so the sigmoid should be fitted on a hold-out set or by cross-validation. On
    three data-mining-style datasets, SVM + sigmoid gives probabilities "of comparable
    quality" to a regularized-likelihood kernel method (abstract).
  - *For us:* defines Platt scaling and justifies the held-out calibration split.
- **Zadrozny & Elkan (2001)** [`zadrozny2001`, full text]
  - *Finds:* binning makes naive Bayes probabilities better calibrated. For C4.5 trees,
    m-estimate smoothing plus "curtailment" works. All on one large dataset (KDD'98).
  - *For us:* histogram binning as an early calibrator; background only.
- **Zadrozny & Elkan (2002)** [`zadrozny2002`, abstract]
  - *Finds:* proposes a two-class calibration method that works for any classifier that
    produces a ranking (isotonic regression/PAV, as identified by NM&C 2005 §2.2). Also
    combines binary calibrations for multiclass. Tested with naive Bayes and SVMs.
  - *For us:* the citation for isotonic calibration.
- **Kull, Silva Filho & Flach (2017)** [`kull2017`, full text]
  - *Finds:* logistic calibration assumes normally distributed per-class scores with
    equal variance. Its family on raw scores lacks the identity, so it can uncalibrate a
    calibrated model. Isotonic overfits on smaller datasets. Beta calibration fixes this
    (better than logistic for naive Bayes and AdaBoost).
  - *For us:* D5. Beta calibration is out of scope, but the paper should mention it as
    the known improvement on Platt.

### Empirical studies of LR, RF and boosted trees

- **Niculescu-Mizil & Caruana (2005, ICML)** [`niculescumizil2005`, full text]
  - *Setup:* 10 learners on 8 binary problems (ADULT, COV_TYPE, LETTER.P1/P2, MEDIS, MG,
    SLAC, HS). 4000 training cases, independent 1000-case calibration sets, large test
    sets (Table 2).
  - *Out-of-the-box calibration (Sec. 4):*
    - LR and bagged trees are well calibrated, and post-calibration does not help them on
      most problems.
    - RF is "well calibrated on some problems, but … poorly calibrated on LETTER.P2, and
      not well calibrated on HS, COV_TYPE, MEDIS and LETTER.P1". It shows a milder
      version of the sigmoid distortion of max-margin methods, attributed to averaging
      high-variance trees.
    - Boosted trees show a sigmoid distortion on 7 of 8 problems.
  - *Calibration-set size (Sec. 5, Fig. 7):* calibration sets range from 32 to 8192
    cases. Platt beats isotonic for all nine learners below about 200–1000 cases. At
    ≥1000, isotonic is as good or better. For well-calibrated learners (neural nets,
    bagged trees, LR), neither method helps much, and small calibration sets hurt.
  - *After calibration (Sec. 6, Fig. 8; 5 trials × 8 problems):* before calibration the
    best are RF, bagged trees and neural nets; after it, boosted trees, RF and SVMs.
  - *For us:* the main precedent for H1, and the main source for D3. Their boosting is
    AdaBoost-style, not log-loss gradient boosting.
- **Niculescu-Mizil & Caruana (2005, UAI)** [`niculescumizil2005boosting`, full text]
  - *Finds:* AdaBoost shifts predictions away from 0 and 1. Platt and isotonic both fix
    this. Table 2, boosted trees, mean cross-entropy: raw 0.4836, Platt 0.3797, isotonic
    0.3814. Boosting full trees directly with log-loss does worse (0.4992). Footnote 1:
    predictions are kept off exactly 0 and 1 to avoid infinite cross-entropy.
  - *For us:* the H2 rationale for boosted trees, and D2. Modern regularised log-loss
    GBDT is a different model, which is why H2 for HGB is open.
- **Caruana & Niculescu-Mizil (2006)** [`caruana2006`, full text]
  - *Setup:* 10 learners, 11 binary problems, 8 metrics, 5 trials of 4000 train and
    1000 validation cases. The 1000 cases are used both to calibrate and to select
    parameters.
  - *Finds:* uncalibrated, the best probability metrics come from bagged trees, RF and
    neural nets. After Platt calibration, boosted trees lead. Calibration slightly hurts
    neural nets.
  - *For us:* corroborates NM&C 2005; D7.
- **Boström (2008)** [`bostrom2008`, full text]
  - *Setup:* RF of 100 unpruned trees, 34 UCI datasets, stratified 10-fold CV,
    out-of-bag examples as the calibration set.
  - *Finds (Brier score):* isotonic "slightly deteriorates" RF of probability-estimation
    trees; Platt gives "a limited improvement". A new RF-specific method is best. Both
    isotonic variants are significantly worse on AUC (Nemenyi test, 0.05).
  - *For us:* direct evidence *against* H2 for RF; supports D6.
- **Fonseca & Lopes (2017)** [`fonseca2017`, full text; arXiv preprint]
  - *Setup:* LR, RF, GBC × {none, sigmoid, isotonic}; 18 consumer-credit datasets;
    chronological 60/20/20 train/calibration/test split; Brier score only; one split per
    dataset.
  - *Finds (Sec. 3–4):*
    - Uncalibrated RF and GBC "do not perform much better" than LR and can be worse.
    - Sigmoid does almost nothing for LR, and harms RF and GBC in about 25% of cases.
    - Isotonic improves LR in over 75% of cases and helps RF and GBC.
    - RF "seems to require more calibration" than GBC.
  - *For us:* the closest design match. It confirms H2's direction on credit data but
    has no seed variation and a temporal split. A useful contrast for an i.i.d. design.
- **Manokhin & Grønhaug (2026)** [`manokhin2026`, full text; arXiv preprint]
  - *Setup:* 21 classifiers, including LR, RF, GBC and HGB, with default settings and no
    hyperparameter optimisation (§5.3). 30 binary TabArena-v0.1 datasets, 1×5-fold
    stratified CV, no repeats. Five calibrators (isotonic, Platt, beta, Venn-Abers,
    Pearsonify) on a calibration split carved from the training folds.
  - *Finds (Sec. 2):*
    - Aggregated over models, Platt lowers log-loss by 9.75% in expectation but improves
      it in only 49.8% of instances. Isotonic "is expected to slightly increase
      log-loss", but improves Brier by 3.74%.
    - Platt and isotonic "can systematically degrade proper scoring performance for
      strong modern tabular models".
    - Self-noted limitation: calibration is confounded with the smaller training set.
  - *For us:* the strongest recent evidence that H2 may fail. D4 and D7.
- **Berta, Holzmüller, Bach & Jordan (2026), CalArena** [`berta2026`, full text; arXiv v2]
  - *Setup:* TabRepo-binary covers 104 datasets and 832 experiments with LR, RF,
    ExtraTrees, XGBoost, LightGBM, CatBoost and two NNs, each tuned on validation
    ROC-AUC (§3). The main metric is the post-hoc improvement in Brier score; binned ECE
    is reported only as a diagnostic (§5).
  - *Finds (§6.1):* on TabRepo-binary "no method manages to consistently improve over
    the non-calibrated model". Platt on probabilities, XGBoost-as-calibrator and binning
    methods degrade it. Across benchmarks, logistic maps on log-probabilities (quadratic
    scaling, Platt on logits, beta) are best.
  - *For us:* the strongest evidence that the *answer* to H2 at scale is "often no",
    and the source for D1, D5 and D6.

### Calibration metrics

- **Brier (1950)** [`brier1950`, DOI only]: origin of the Brier score. Cite for the
  definition only.
- **DeGroot & Fienberg (1983)** [`degroot1983`, DOI only]: standard reference for
  evaluating forecasters' calibration. NM&C (2005) cite it for reliability diagrams. Cite
  for that only.
- **Gneiting & Raftery (2007)** [`gneiting2007`, abstract]: theory of proper scoring
  rules, including the logarithmic and quadratic scores. Justifies log-loss and Brier as
  primary metrics (D1).
- **Naeini, Cooper & Hauskrecht (2015)** [`naeini2015`, abstract]: proposes Bayesian
  Binning into Quantiles. Guo et al. (2017) and Roelofs et al. (2022) both credit it with
  the "ECE" acronym.
- **Guo, Pleiss, Sun & Weinberger (2017)** [`guo2017`, full text]: defines ECE with M
  equally spaced bins, weighted by bin size, on top-label confidence (§2). The standard
  definition the paper will be compared against (D1). Its neural-network findings are
  outside our scope.
- **Kumar, Liang & Ma (2019)** [`kumar2019`, full text]: Platt and temperature scaling
  are "less calibrated than reported". Binned estimates cannot measure the calibration
  error of continuous outputs. The plug-in estimator is less accurate than a debiased
  one. → D1.
- **Nixon et al. (2019)** [`nixon2019`, full text of arXiv v2]: ECE "has numerous
  flaws". The ranking of recalibration methods is "drastically impacted" by the choice of
  calibration measure. They recommend adaptive (equal-mass) bins and the L2 norm. → D1.
- **Roelofs, Cain, Shlens & Mozer (2022)** [`roelofs2022`, full text]: binned ECE is
  statistically biased. Equal-mass bins have lower bias than equal-width. They recommend
  the debiased estimator or ECE_sweep. → D1.
- **Dimitriadis, Gneiting & Jordan (2021)** [`dimitriadis2021`, abstract]: CORP
  reliability diagrams via PAV/isotonic regression are consistent, optimally binned and
  reproducible, and give a Brier-score decomposition. A candidate for the reliability
  figure (D1).
- **Silva Filho et al. (2023)** [`silvafilho2023`, abstract]: survey of calibration
  assessment and post-hoc methods. General background citation.

### Software

- **Pedregosa et al. (2011)** [`pedregosa2011`, abstract]: scikit-learn citation.
- **scikit-learn user guide §1.16** [`sklearn_calibration_docs`, page read; 1.9.1 at
  fetch time]
  - LR tends to be well calibrated when well specified and suitably regularised. RF
    shows a sigmoid curve (quoting NM&C 2005).
  - The calibrator should be fit on data independent of training.
  - `CalibratedClassifierCV(ensemble=True)` averages k classifier–calibrator pairs;
    `FrozenEstimator` calibrates a fitted model.
  - Isotonic is as good as or better than sigmoid with more than ~1000 samples.
    Isotonic ties can change AUC.
  - → D3, D4, D5, D6. The Writer should cite the docs version pinned in
    `code/requirements.txt`.

---

## 4. Unverified or not used

- **Platt (1999), publication details.** Pages 61–74 and the book's year are taken from
  the NM&C (2005) reference list and the preprint footnote ("to appear"), not from the
  book. Kull et al. (2017) cite it as 2000. The year in `refs.bib` (1999) may need to
  become 2000.
- **Zadrozny & Elkan (2002).** Full text not reachable: ACM returned 403, and the
  Cornell PDF is a slide deck. Only the abstract was read.
- **Brier (1950) and DeGroot & Fienberg (1983).** DOI-resolved only; the full texts were
  not read. Cite them only for definitions.
- **Nixon et al. (2019).** The CVPR-W 2019 version has 5 authors, while the arXiv v2
  that was read has 7. `refs.bib` cites the arXiv version.
- **CalArena (2026).** "Accepted at NeurIPS 2026" comes from the arXiv comment and was
  not checked in the proceedings. Manokhin & Grønhaug (2026) and Fonseca & Lopes (2017)
  are preprints.
- **Seen in search, not used:**
  - arXiv:2509.23665 ("Calibration Meets Reality"): abstract only, mainly theoretical.
  - arXiv:2202.12780 (Fissler et al., scoring-function user guide): abstract only.
  - Shaker & Hüllermeier (2025), "Random Forest Calibration": cited by
    `manokhin2026`, not fetched.
  - The earlier TabRepo calibration study by Berta et al. cited as [10] in `berta2026`:
    not fetched.

  If the Reviewer wants more on RF-specific calibration, Shaker & Hüllermeier is the
  next source to check.
