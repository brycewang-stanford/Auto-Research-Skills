# Scout notes: label-noise sensitivity of tabular classifiers (task `q-novelty`)

Scout, 2026-11-18. Every source below was fetched and checked: metadata from Crossref,
arXiv, JMLR or NeurIPS proceedings, and content from the abstract or full text as stated in
`sources/sources.json`. Where only the abstract was read, nothing below goes beyond it.

## Novelty verdict: **partly answered**

**Closest prior work:** Le Baher, Lemaire & Trinquart, arXiv:2010.13570 (v5, formatted for
the DQAML@SIGKDD '21 workshop) [`lebaher2020`]. The study compared logistic regression,
random forests (two implementations) and XGBoost, plus linear SVC and Khiops, on 14 binary
tabular datasets with labels flipped completely at random. Training labels only were
flipped, with 5×5-fold CV.

Hypothesis numbers below follow the **current** `plan.json`, which has two hypotheses,
each decided per dataset with a count rule:

- **H1:** HistGradientBoosting loses more than RandomForest.
- **H2:** logistic regression has the smallest drop.

Earlier versions of these notes used other numberings and are superseded. The general fact
that accuracy falls as label noise rises is **already answered**: every empirical source
below reports it, though Breiman (2001, Table 4) shows random-forest error sometimes falls
at 5% noise. It is not a hypothesis in the plan.

- **H1 (main): per dataset, the 0 → 0.4 drop is larger for log-loss GBDT with early
  stopping than for RF. Verdict: open/contested.** This is where a careful study can add
  something.
  - *Evidence that boosting degrades more than bagging or random forests:*
    - Dietterich (2000, Table 3): AdaBoost compared with bagging, on noise up to 20%.
    - Breiman (2001, Table 4): AdaBoost compared with random forests, at 5% noise.
    - Nawaz et al. (2025, abstract): boosting models (XGBoost, LightGBM, CatBoost) were
      the most sensitive and RF moderately robust, on noise up to 30%.
    - Long & Servedio (2010) give a theoretical worst case for convex-potential boosters.
  - *Evidence for random forests degrading badly:* Le Baher et al. find RF's drop
    significant and RF among the worst methods once noise is added. They explicitly
    disagree with Folleco et al. (2008), who recommend random forests for noisy data.
    Their XGBoost used hinge or squared-error loss, not log-loss, and was untuned.
  - *Context, not evidence on the ordering:* Eisenbürger et al. (2024) study **XGBoost
    alone**. They find it robust to symmetric noise in absolute terms, especially with
    early stopping. They make **no comparison with random forests or any other model
    family**, so their result neither supports nor disputes an RF-versus-GBDT ordering
    (finding F6). It does show that early stopping matters for the GBDT curve.
  - *Why the evidence conflicts:* the classic "boosting is fragile" comparisons concern
    AdaBoost (exponential loss, no shrinkage), not log-loss gradient boosting with
    shrinkage and early stopping. Long & Servedio is a worst-case construction, not an
    average-case prediction. Nawaz et al. compare modern GBDT libraries with RF, but only
    up to 30%. From the abstract we cannot tell their noise model, their tuning, or
    whether test folds were clean.
  - **Gap:** we found no study comparing HistGradientBoosting-style log-loss GBDT with RF
    under exact symmetric flips up to 40%, with an equal tuning budget, clean test labels
    and per-dataset seed intervals. Not finding one does not prove that none exists.
- **H2: per dataset, tuned L2-regularized LR has the smallest drop of the three. Verdict:
  partly answered.**
  - *Empirical:* Le Baher et al. bear on this directly. In their Section 4.3 and
    Conclusion, logistic regression and linear SVC "show surprisingly good results
    overall and a 'small' sensibility to labels corruption", while RF becomes one of the
    worst methods under noise. In Section 4.1 they also say that LR, LinearSVC and the
    two Khiops models "know a really small decrease even at ρ = 1.00". The text does not
    make clear which dataset that sentence refers to. It follows the Trucks paragraph, so
    it should not be cited as a Breast Cancer result.
  - This supports H2 qualitatively, with four limits:
    1. In Le Baher et al., LR was not the single least-sensitive method; Khiops was
       comparably stable.
    2. Their metrics were AUC, balanced accuracy and kappa, not accuracy.
    3. Noise was scaled by minority-class share, and the data were binary only.
    4. LR used fixed C = 1, not a tuned C, and XGBoost used non-default losses.

    We found no other empirical source comparing LR's drop with RF and GBDT. Nawaz et al.
    omit LR.
  - *Theory:* there is a mechanism, with a qualification. Van Rooyen et al. (2015) show
    that strong l2 regularisation makes most standard learners robust to symmetric label
    noise. Ghosh et al. (2015) show, by contrast, that no standard convex loss, logistic
    loss included, meets their sufficient condition for tolerance to uniform noise. So a
    small LR drop is expected when the tuned C is small. If tuning on noisy validation
    labels picks a large C, the theory does not guarantee it.
  - *Confound to report:* LR's clean accuracy may be lower on some datasets, for example
    covtype, where a linear model is far from the trees. A model that starts lower can
    lose less. The drop should be read together with absolute accuracy at each rate.
  - **Gap:** we found no study with tuned C, an equal budget, accuracy on clean test
    labels and per-dataset seed intervals.

**Descriptive, not tested: ranking reversals.** `plan.json` no longer tests whether the
ordering of the methods changes with noise; rankings are reported descriptively. Prior
work the paper can cite for that description:

- Dietterich (2000, Table 3): AdaBoost beats bagging 5-0-4 at 0% noise and loses 0-6-3 at
  20%.
- Le Baher et al.: RF is near the top without noise and near the bottom with it.
- Morampudi et al. (2026): rankings among GBDT libraries appear only from 20% symmetric
  noise.

Because these reversals are well documented, a reversal on its own would not have been a
new finding.

**Prior work on the four named datasets** (breast_cancer, credit-g, adult, covtype):

- **breast_cancer** (scikit-learn: Wisconsin Diagnostic, 569 × 30)
  - Le Baher et al. used a different Breast Cancer: 699 rows, 9 features (Table 1), i.e.
    the original Wisconsin data. On it, "performances decrease along with noise on all
    models" (Section 4.1, Figure 1; AUC, kappa and balanced accuracy, with values only in
    the figure).
  - Breiman (2001) also used the 699-row version. At 5% noise, AdaBoost error rose 43.2%,
    against 1.8% for Forest-RI (Table 4).
  - Eisenbürger et al. used the same 569 × 30 version as scikit-learn, with XGBoost only.
    Their reported classification table for it uses 30% pair noise (Table 7), not
    symmetric noise.
- **adult**
  - Le Baher et al. (Figure 6: AUC against ρ for all models, values only in the figure).
  - Eisenbürger et al. (XGBoost only; noise-detection and pair-noise tables).
- **covtype**: Eisenbürger et al. use it as their main dataset (XGBoost only; Figure 2,
  Tables 3 and 6, with pair noise in the tables).
- **credit-g**: no fetched source ran a noise experiment on it.
  - Dietterich (2000) and Breiman (2001) list German credit among their datasets but
    leave it out of their noise experiments.
  - Nawaz et al. and Morampudi et al. use OpenML suites, but their abstracts do not name
    the datasets, so overlap is unverified.

No source we found reports LR vs RF vs log-loss GBDT accuracy under symmetric noise on any
of these four datasets.

**What remains novel:** the controlled protocol, not the question. Le Baher et al. differ
from the crew's design on every point that matters for H1 and H2:

- XGBoost used hinge and squared-error objectives, not the default logistic loss.
- Hyperparameters were fixed, with no per-method tuning budget.
- Binary tasks only.
- The noise rate was scaled by the minority-class share (effective rate = ρ × minority
  proportion), so "ρ = 0.4" is not 40% flipped labels.
- Metrics were AUC, balanced accuracy and Cohen's kappa, not accuracy.

Nawaz et al. omit logistic regression. Eisenbürger et al. study XGBoost only, and
Morampudi et al. study GBDT libraries only. Neither includes RF or LR. The contribution as
now worded in `plan.json` ("in the work we found, has not been made") matches what the
search supports.

**Notes for the design stage** (for the PI / Methodologist; the Scout does not edit
plan.json):

1. Early stopping is now in the plan. Eisenbürger et al. show, for XGBoost, that it
   changes the result.
2. Clean test labels are now in the plan. Contrast this with Dietterich (2000), who
   flipped labels before CV, so his test labels were noisy too.
3. The exact-flip definition differs from Le Baher's minority-scaled ρ. Say so when
   comparing with them.
4. Van Rooyen et al. (2015) tie LR's robustness to regularisation strength. Report the
   tuned C at each noise rate for H2.

## Sources

### Surveys

- **frenay2014**: Frénay & Verleysen, "Classification in the Presence of Label Noise: A
  Survey", IEEE TNNLS 25(5):845-869, 2014. *Abstract read.* A taxonomy of label-noise types
  (including noise completely at random, used by Le Baher et al.). It reviews the consequences
  of label noise: lower accuracy, more complex models, more training samples needed. It also
  covers noise-robust, noise-cleansing and noise-tolerant algorithms, and experiment design.
  Relation: the standard framing reference for the related-work section. Supports only the
  general fact that noise degrades accuracy (no longer a plan hypothesis).

### Empirical comparisons (closest to the question)

- **lebaher2020**: Le Baher, Lemaire & Trinquart, arXiv:2010.13570v5. *Full text read.*
  - Setup: 14 binary tabular datasets (NASA software defects, UCI: Adult, Breast Cancer,
    Spambase, Mushroom, Bank, etc.; Table 1). NCAR noise with ρ₋₁ = ρ₊₁ (Section 2.3),
    applied to training splits only. Noise rates are scaled by minority-class share, with 12
    levels from 0 to 1.25 (Section 3.5). 5×5-fold CV; AUC, balanced accuracy, Cohen's kappa.
  - Models: LinearSVC, logistic regression (lbfgs, C = 1), sklearn and Weka random forests
    (100 trees), Khiops, and XGBoost with hinge, squared, unhinged or ramp losses. No
    hyperparameter tuning is described.
  - Findings (Section 4 and Conclusion):
    - Performance falls with noise for all models on balanced datasets (Breast Cancer,
      Spambase) and is stable on the largest, most imbalanced dataset (Trucks).
    - Random forests are very good without noise but among the worst once noise is added.
    - Logistic regression and linear SVC show only "small" sensitivity.
    - Symmetric losses in XGBoost are stable but beaten by standard losses except at very
      high noise.
  - Relation: closest prior work. It bears on H1 and H2 and on the descriptive rankings, but with a
    different noise scale, different metrics, untuned models and a non-default XGBoost loss.
- **dietterich2000**: Dietterich, Machine Learning 40(2):139-157, 2000. *Full text read
  (author preprint).*
  - Setup: C4.5, bagged C4.5, AdaBoost C4.5 and randomized C4.5 on 9 UCI domains with 0%,
    5%, 10% and 20% random class noise. Each noisy label is drawn uniformly from the
    incorrect classes. The noise was added *before* the stratified 10-fold CV, so test
    labels were noisy too.
  - Finding (Table 3): AdaBoost beats bagging 5-0-4 at 0% noise but loses 0-6-3 at 20%.
    "Classification noise destroys the effectiveness of Adaboost."
  - Relation: classic evidence for H1 in its AdaBoost form; cited descriptively for rank
    reversal (no longer a tested hypothesis).
- **breiman2001**: Breiman, Machine Learning 45(1):5-32, 2001. *Full text read (author's
  January 2001 version).* Defines random forests (cited for the method). Section 8: 5% of
  training labels are flipped to a uniformly chosen other class, with 50 repetitions on 9
  small datasets.
  - Table 4: AdaBoost error rises by 1.6-48.9%. Forest-RI changes by -6.6 to +7.9%
    (sonar: -6.6, liver: -0.2). Forest-RC changes by -0.4 to +11.1%.
  - Relation: supports H1 against AdaBoost (not log-loss GBDT) at 5% noise. It also shows
    random forests may not degrade at low noise.
- **folleco2008**: Folleco, Khoshgoftaar, Van Hulse & Bullard, IEEE IRI 2008, pp. 190-195.
  *Abstract read.* Injects noise into five class-imbalanced software-engineering datasets,
  varying the learner, the noise level and the share of noisy minority instances.
  Recommends random forests for noisy data. Relation: the pro-RF position that Le Baher et
  al. dispute. Its noise model (label and/or attribute) cannot be confirmed from the
  abstract.
- **nawaz2025**: Nawaz, Ahmad & Khan, ICML 2025 FMSD workshop. *Abstract read.* 15 OpenML
  binary tabular datasets with label noise at 0, 1, 5, 10, 20, 25 and 30%. TabPFN against
  RF, XGBoost, LightGBM, CatBoost, SVM, kNN and decision tree, with 2×5-fold stratified CV
  (accuracy, AUC). Boosting models are most sensitive; RF is moderately robust; TabPFN is
  most resilient. Relation: recent support for H1 (modern GBDT libraries vs RF). It has no logistic
  regression, so it is silent on H2, and from
  the abstract we cannot tell whether the noise is symmetric or whether test folds are
  clean.
- **eisenburger2024**: Eisenbürger, Otten, Hudde & Hopfgartner, arXiv:2409.08647 (preprint).
  *Full text read.* XGBoost on Covertype, Dry Bean, Adult and Breast Cancer, with symmetric
  (NCAR) and pair (NAR) noise and a clean test set. The contributions list (p. 2) states
  that GBDTs are naturally robust to label noise, particularly symmetric noise, and that
  early stopping helps. The only model trained is XGBoost: the paper contains no random
  forest, logistic regression, LightGBM or CatBoost (its "baseline" is XGBoost without
  noise detection). Figure 4: without early stopping, clean-test accuracy falls as
  boosting continues on noisy labels, much more slowly under symmetric noise than under
  pair noise. Relation: shows XGBoost is robust in absolute terms and that early stopping
  matters. Because it makes no RF comparison, it is **not** evidence for or against H1's
  RF-vs-GBDT ordering (corrected per review finding F6).
  It does not compare with RF or LR.
- **morampudi2026**: Morampudi, Padi, Kakitapelli & Surapani, Algorithms 19(9):730, 2026.
  *Abstract read.* XGBoost, LightGBM and CatBoost on 15 OpenML-CC18 datasets, under
  symmetric, pair-flip and instance-dependent noise. Four rates, three seeds, clean test
  set, macro-F1. Hyperparameters were tuned on clean data and then fixed.
  - No library separates at 10%. Separation appears from 20% symmetric noise.
  - At 40% symmetric noise, CatBoost degrades least and LightGBM most.
  Relation: shows that GBDT robustness conclusions depend on the noise model and the
  implementation. Supports the threat that "GBDT" in H1 is not one method, so the crew
  should name the implementation.

### Theory on noise-robust losses

- **manwani2013**: Manwani & Sastry, IEEE Trans. Cybernetics 43(3):1146-1151, 2013.
  *Abstract read.* Risk minimization under 0-1 loss is noise tolerant; under squared loss it
  is tolerant only to uniform noise; under other losses it is not. Relation: the
  population-level reason symmetric noise need not change the optimal classifier.
  Degradation in practice comes from using surrogate losses with finite samples.
- **ghosh2015**: Ghosh, Manwani & Sastry, Neurocomputing 160:93-107, 2015. *Abstract read.*
  Gives a sufficient condition for a loss to be tolerant to uniform noise. 0-1, sigmoid,
  ramp and probit losses satisfy it; no standard convex loss does. Relation: logistic loss
  (used by LR and log-loss GBDT) is not covered by the tolerance guarantee.
- **long2010**: Long & Servedio, Machine Learning 78(3):287-304, 2010. *Full text read
  (author manuscript).* Any convex-potential booster (AdaBoost, LogitBoost, ...) can be made
  to fail by random classification noise at any rate η > 0. On a constructed data set it
  reaches no better than 1/2 accuracy, even with early stopping or an L1 bound. Relation:
  theoretical motivation for H1. It is a worst-case construction, so it does not predict
  average behaviour on real datasets.
- **vanrooyen2015**: van Rooyen, Menon & Williamson, NIPS 28, 2015. *Abstract read.*
  Proposes the "unhinged" loss, which is robust to symmetric label noise, and shows that
  strong l2 regularisation makes most standard learners robust to it. Relation: predicts
  that a strongly regularised logistic regression should degrade little. Relevant to H2
  (the LR curve) and to how C is tuned.
- **natarajan2013**: Natarajan, Dhillon, Ravikumar & Tewari, NIPS 26, 2013. *Abstract
  read.* Loss corrections (unbiased estimator; weighted surrogate) for class-conditional
  random label noise; weighted logistic regression is provably noise tolerant. Synthetic
  data: over 88% accuracy with 40% of labels corrupted. Relation: background on correcting
  noise; out of scope for an uncorrected comparison, but a natural "future work" pointer.

### Methods and software (cited for what the crew uses)

- **pedregosa2011**: Pedregosa et al., "Scikit-learn: Machine Learning in Python", JMLR
  12(85):2825-2830, 2011. *Abstract page read.* Cite for the implementations.
- **breiman2001**: see above (random forests).
- **friedman2001**: Friedman, "Greedy Function Approximation: A Gradient Boosting Machine",
  Annals of Statistics 29(5):1189-1232, 2001. *Abstract read.* Defines gradient boosting
  of regression trees, including the multiclass logistic likelihood. The abstract calls
  gradient-boosted trees "highly robust" and "especially appropriate for mining less than
  clean data". That statement concerns robust losses (LAD, Huber) for regression, not label
  noise, so it must not be cited as evidence about H1.

## Not used / unverified

- Zhu & Wu (2004), "Class Noise vs. Attribute Noise: A Quantitative Study", Artificial
  Intelligence Review 22(3):177-210, DOI 10.1007/s10462-004-0751-8: DOI resolved via
  Crossref, but the abstract and full text could not be reached (Springer blocked automated
  access; no abstract in OpenAlex or Semantic Scholar). Not added.
- Nettleton, Orriols-Puig & Fornells (2010), Artificial Intelligence Review 33(4):275-306,
  DOI 10.1007/s10462-010-9156-z: same situation. Not added.
- Angluin & Laird (1988), "Learning from Noisy Examples", Machine Learning 2(4):343-370,
  DOI 10.1007/BF00116829 (origin of the random-classification-noise model): DOI resolved
  only, content not read. Not added. Add it if the paper needs a citation for the model's
  origin and someone can read it.
- Bootkrajang & Kabán, "Boosting in the presence of label noise" (arXiv:1309.6818) and
  "Label-noise robust logistic regression" (ECML PKDD 2012): metadata seen; judged
  peripheral (noise-aware variants, not standard classifiers). Not added.
- Folleco et al. (2009), Informatica 33:245-259, cited by Le Baher et al. as their [15]:
  not fetched.
- The full text of Nawaz et al. (2025) is behind an OpenReview browser check. Their noise
  model and whether test folds were kept clean are unverified.

## Added for the design stage (design-r2 F10)

- **nadeau2003**: Nadeau & Bengio, "Inference for the Generalization Error", Machine
  Learning 52(3):239-281, 2003, DOI 10.1023/A:1024068626366. *Abstract read* (metadata from
  Crossref and the Springer landing page; abstract from mlanthology.org).
  - The abstract says tests should account for the variability due to the choice of
    training set, not only test examples. Ignoring it can grossly underestimate the
    variance of the CV estimator.
  - It also says that all variance estimators based only on the CV results must be biased,
    and that the proposed estimators give tests with correct size and good power in
    simulations.
  - **Unverified:** the specific correction factor (1/J + n_test/n_train) behind the
    "corrected resampled t-test" is not in the abstract, and the full text could not be
    fetched (Springer blocked automated access). Claim `c-nadeau` is therefore worded at
    abstract level and does not state the factor. Before the paper states the formula with
    this citation, someone with access must check the full text and record the section or
    equation number.
