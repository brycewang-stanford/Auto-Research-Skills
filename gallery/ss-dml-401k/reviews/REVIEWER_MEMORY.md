# Reviewer memory: ss-dml-401k

## question-r1 (2026-11-18): revise, 0 critical / 5 major / 4 minor

Suspicions:
- H2's $650 tolerance is about 12-27x the Monte Carlo error implied by the published table
  (sqrt(adjSE^2-medSE^2)*1.25/sqrt(S)). Watch for the tolerance being widened, or the
  cells being chosen, after results are in.
- Lasso is excluded from H2. It is the cell most sensitive to implementation (dictionary,
  rlasso penalty) and the noisiest (split spread about $860-1,120).
- The plr-<learner> claim does not say which K it reports. Watch for the closer of 2-fold
  and 5-fold being reported.
- The budget (60 min on a laptop) cannot fit S=100 x 7 learners. Expect S to be reduced;
  it must be disclosed as a deviation.
- Estimand wording: PLR coefficient vs "average effect" (IRM ATE is about $1,000-1,400 lower).

Verified myself:
- Table 2 Panels A and B in arXiv:1608.00060v7 p.42 match notes.md.
- The 401(k) neural net has 8 neurons and decay 0.01 (p.~44).
- The DoubleML pension page PLR numbers match notes.md (3 folds, n_rep unset).
- Timing (sklearn, 8 cores, n=7,932): RF reg 3.5 s, RF clf 0.9 s, GBM (1000 trees) 4.2 s
  per fit.

Check next round:
- F1-F9 status. Is a numeric per-cell tolerance fixed in plan.json, and is S stated?
- Was the stale "one SE ($1,300)" line in notes.md fixed?
- At the design stage: the lasso dictionary and penalty are fixed; there is an R reference
  arm or the decomposition claim is dropped; the SE type (HC) and the eq. 3.14 aggregation
  are fixed in advance.

## question-r2 (2026-11-18): revise, 0 critical / 1 major / 3 minor open

Status: F1, F3, F5, F6, F7 and F9 resolved. F2 and F4 conceded. F8(b) still open (which
SE row is used for "units of the published SE"). New: F10 (major), F11 and F12 (minor).

Suspicions:
- F10: the H2 tolerance treats sqrt(adj^2 - med^2) as an SD. It is roughly a MAD (x1.4826),
  and H2 is an "all 10 cells" conjunction at 2 SE. A faithful run fails about 37% of the
  time (correct scale) to 86% (plan's scale). Watch for the fix being chosen after results.
  It must be in plan.json before the design gate.
- The 2017-vs-2018 gaps give z^2 summing to 6.5 under the plan's formula (max 1.94, nnet
  K=2). They are probably the same seed and code, so they are not a null draw. Do not let
  the authors cite them as validating the calibration.
- se_rep uses the published sd_split with the crew's S (notes.md section 5). If the crew
  later switches to its own observed split SD, a noisier implementation earns a wider
  tolerance. Flag that if it happens.
- The response to F3 promised descriptive SE comparisons. They are not in plan.json. Check
  that they appear at results, and that they are not used selectively.

Arithmetic I ran (published table only; no data, no models): MAD factor, coverage
probabilities, corrected tolerances at S = 10 and 20, and z-scores for the 2017-vs-2018
gaps.

Check next round / at design:
- Has F10's rule been fixed, and is S stated with a per-cell tolerance table and a timing
  estimate (F11)?
- Lasso dictionary and penalty: is the 401K.R formula used? sklearn has no rlasso; check
  how the c = 1.1 heteroskedastic penalty is approximated.
- SE type (HC as in the authors' code, lm(ry ~ rz - 1)), the score (partialling out), and
  the eq. 3.14 aggregation are fixed.
- nnet: MLPRegressor vs nnet (8 units, decay 0.01, maxit 1000). Is input scaling stated?
  For a binary D, the classifier m(X) needs probabilities: check what nnet/tree/forest
  return for D.
- Same splits across learners within a split index? This affects the cross-cell
  correlation that F10's joint rule assumes.
- crew.json title still says "raise". Check the paper title and abstract at the paper stage.

## question-r3 (2026-11-18): revise, 0 critical / 1 major / 3 minor open

Status: F10, F12 and F8 are resolved. F11 stays open (minor, carried to the design
review). New: F13 (major), F14 and F15 (minor).

Suspicions:
- F13: the F10 fix (which I proposed) made every tolerance 2.08 times wider. At budget S
  the tolerances are $330-1,930, so H2 is close to a guaranteed pass. Watch for "all 10
  cells reproduced" in the results or the paper without the tolerance and the minimum
  detectable shift next to each cell. The floor at crew S = infinity is lasso 583/450 and
  flexible learners 100-234, because the published median's own Monte Carlo error sets
  it.
- 1.4826 is the upper bound. If sigma_s varies across splits, the right factor is
  between 1 and 1.4826, so H2 is conservative. Do not let the authors use their own run's
  observed SD to *change* the tolerance after results are in. Using it only as a
  descriptive diagnostic is fine.
- Watch for a per-learner S being chosen after any pilot. It must be in plan.json before
  any analysis run.
- notes.md section 5 is stale again (no 1.4826, z = 2). It has been stale twice now, so
  check it every round.

Arithmetic I ran (published table only; no data, no models): tolerances at S = 10, 20, 50,
100 and infinity; detection probability against a $300 shift; H3 failure rate under a
faithful replication (0.215 at S = 10, 0.072 at S = 20; independent-cell simulation).

Check at design:
- S per learner, the tolerance table and timing (F11, F13). Is there a "not testable at
  this resolution" threshold, fixed in advance?
- The lasso dictionary is the 401K.R formula. How is rlasso c = 1.1 approximated in
  sklearn? The SE type is HC; the score is partialling out; aggregation follows eq. 3.14.
- nnet scaling; probability outputs for binary D; whether splits are shared across
  learners within a split index.
- H3 is stated as a comparison of point estimates, with its expected failure rate (F15).

## question-r4 (2026-11-18, last round): pass, 0 critical / 0 major / 3 minor open

Status: F13 conceded (claim narrowed, not powered up). F14 and F15 resolved. F11 stays
open as a design item. New: F16 and F17 (minor). Open findings go to the human.

Suspicions:
- The power problem from F13 has not gone away. At the planned S (lasso and tree at 100,
  forest and boosting at about 10), every cell's tolerance is below $1,000, so the NT rule
  excludes nothing. Expect the headline "all testable cells reproduced". The 80%-power
  minimum detectable shift is 1.30 times the tolerance: forest K=2 $1,008 at S = 10,
  lasso K=2 $1,071 at S = 100.
- F17: after a cell fails, the crew may re-tune the learner until it passes. The claim value
  must come from the configuration fixed at the design gate.
- crew.json title still says "raise" (paper stage).

Verified myself: notes.md section 5 table against Panel B, to within $2 of rounding; the
off-protocol pass/fail entries; H3 false-fail rate below 1% with lasso at S = 100 (smallest
margin is nnet K=5, about 3.6 SE). Arithmetic on the published table only; no data, no models.

Check at design:
- S for every learner, the tolerance table with MDS80 next to it, and a timing estimate
  (F11, F16). Was the NT threshold or the word "resolution" changed?
- A rule that claim values come from the design-gate configuration only, plus a deviation
  list per learner (F17).
- How the lasso approximates rlasso c = 1.1 (the 401K.R dictionary has about 275 columns),
  the HC SE, the partialling-out score, eq. 3.14 aggregation, nnet scaling, probability
  outputs for binary D, and whether splits are shared across learners and across K.

## design-r1 (2026-11-18): revise, 0 critical / 2 major / 4 minor open

Question-stage carry-overs: F11 (S not fixed) is resolved. S is lasso/tree/nnet 100, forest 40 and
boosting 30, fixed from timing-synthetic (synthetic Y/D only). F17 is resolved by design_constraints.
F16: NT is now re-tied to MDS80 > half the bracketed SE, which makes both lasso cells NT at any S.
That is principled, but it applies in both directions. Filed as D-F1.

Findings: F1 (major): NT discards rejections. F2 (major): no port check for tree, forest, boosting
or nnet against R, which is installed. F3: the c = 0.5 check is unrecorded, and check-lasso-port
must use the authors' exact rlassoF call path. F4: the check-noctrl fork has no switching rule.
F5: no reading rule for a failure driven by higher split noise. F6: no baseline effect size.

Verified myself against the authors' code (fetched 401K.R, ML_Functions.R and Moment_Functions.R):
- DML2 pools ry/rz over folds, then lm(ry ~ rz - 1) with vcovHC 'HC' (HC0).
- trim is passed but unused for plinear. All 9,915 rows are used. cvgroup is shared across methods
  within a call.
- Forest: D uses clas_nodesize 1 with reg = TRUE (a regression forest); Y uses nodesize 5.
- Tree: rpart method is never passed (D is anova); prune at the which.min xerror CP.
- gbm: adaboost for D, predicted with type = "response"; n.cv = 5.
- nnet: linout = FALSE for both nuisances.
- RLasso: penalty list has c = 1.1 and no gamma; post = FALSE.
Recomputed every tolerance_table row exactly. H3 false-fail union bound is 6.6e-5.
Ran no model and did not open the study data.

Suspicions:
- After the design gate, check that the remaining port check(s) run before any analysis run. Check
  that a failed port is recorded as a deviation and not "fixed" after main runs.
- nnet: the iteration counts (nnet_iter_med_y/d) should appear. Y stops around 88 iterations, while
  the D fits hit max_iter 1000 every time.
- Budget: the 34-43 min estimate excludes the R port checks and BLAS oversubscription under
  n_jobs = -1. Watch for a silent cut in S.
- crew.json title still says "raise" (paper stage).

Check next round:
- F1: is NT made one-sided in hypotheses[1] and decision_rules.H2?
- F2: is check-learner-ports added, with thresholds and an R-versus-R yardstick?
- F3-F6: wording or plan changes.
- Code stage: dml_plr.py should match design.method. Check the SeedSequence-to-int conversion, the
  LogisticRegression l1_ratio/liblinear call, and that numpy.median is used on splits.

## design-r2 (2026-11-18): revise, 0 critical / 1 major / 4 minor open

Status: F1-F6 are resolved. F1: the one-sided NT rule is in hypotheses[1], decision_rules and
verdict.py h2_holds. F3: lasso_c_eff_y = 0.5 and c_eff_d = 1.1 are logged under hdm 0.3.2.
New: F7 (major), F8-F11 (minor).

The check-learner-ports results: tree, boosting and nnet pass. Lasso fails (-$87, Y side).
Forest fails (-$216, SE 9, D side, m_hat RMSE 0.480 vs 0.472). The design was not revised
after the check.

Suspicions:
- F7: the forest shift looks like attenuation from a noisier m_hat. It is proportional to theta,
  so it should carry over to net_tfa. My arithmetic: the forest K=5 cell fails H2 with p of
  about 0.24 and K=2 with about 0.08. Expect H2 to fail on forest. Watch for the explanation
  being chosen after the results, and for "consistent with the port deviation" used without
  the sign and magnitude check.
- F8: I think the cause is sklearn continuing the split search beyond max_features, whereas
  randomForest makes the node terminal. NOTES blames the nodesize mapping instead. This is
  not verified.
- F9: the synthetic Y scale is about 1/4.5 of net_tfa's SD, with light tails. The Y-side lasso
  deviation may be several times larger on real data. Watch for "-$87 = 11% of tolerance"
  in the paper.
- F11: the Python phase was 2.0-2.4x slower than the timing model. Expect a 70-100 minute
  main analysis. Check that S is unchanged and that the overrun is disclosed.
- NOTES "21x" is arithmetic for 13x. Check the numbers in NOTES every round.

What I ran: arithmetic only (forest failure probabilities from the tolerance_table SEs and
the synthetic shifts; a crude lasso rescaling). I read the marginal net_tfa summary only.
No models were fitted. No e401-net_tfa relationship was computed or seen.

Check next round / at code:
- F7: a per-cell failure probability and a fixed reading rule in plan.json; the hypotheses[1]
  5% sentence amended; an explicit PI decision on the forest port.
- F8 candidate added. F9 wording. F10: s-hdm-source done, the KKT diagnostic logged or
  dropped, the sources/notes.md c = 1.1 line fixed. F11: re-timing or an accepted overrun.
- Code stage: dml_plr.py vs design.method; SeedSequence-to-int; liblinear l1_ratio; the median
  over splits; that verdict.py uses the measured-deviation reading rule exactly as fixed.

## code-r1 (2026-11-18): revise, 0 critical / 1 major / 2 minor open

The code matches design.method:
- DML2 pooled score and HC0 SE (equal to statsmodels).
- eq. 3.14 aggregation; np.median over splits.
- SeedSequence to int through generate_state.
- liblinear with l1_ratio = 1 applies L1.
- The S guard on main-* runs works.
- The verdict reading wording is verbatim from the plan.
- H1-H3 logic checked on fabricated synthetic metrics.
- No leakage: scaling is done per training fold, and the dictionary is a fixed map.
- The R driver is faithful to cond_comp (re-checked against 401K.R and Moment_Functions.R).

Findings:
- F1 (major): hdm LassoShooting.fit zeroThreshold = 1e-6 on raw-scale coefficients is in every
  hdm version since 0.1.0. It is absent from design.learners.lasso and from the port. Turning it
  off in hdm makes R equal to Python within $0.1-0.2 RMS on 4 synthetic folds, so it explains the
  whole -$87 lasso deviation. The threshold is in absolute units, so its effect on net_tfa is
  unknown in size and sign.
- F2: NOTES blames non-convergence (wrong).
- F3: verdict.py does not re-export the port-check deviations. check-learner-ports is data-prep,
  so its numbers cannot become claims or macros.

What I ran: hdm variants and the port on synthetic units only. dml_plr, check_noctrl and
verdict ran on a synthetic net_tfa/e401 in the scratchpad. No real e401-net_tfa quantity was
computed.

Check next round:
- F1: was the design amended (threshold) and check-learner-ports re-run with --replace, both
  results kept? Or was the deviation stated as identified?
- That any amendment predates every analysis run (log.jsonl and run timestamps).
- F3: verdict --input includes runs/check-learner-ports/metrics.json.
- Forest: still unexplained (design-r2 F8 suspicion: sklearn keeps searching beyond
  max_features). The code matches the design, so this is not a code finding.
