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

## design-r3 (2026-11-18): pass, 0 critical / 0 major / 2 minor open

Status: F7-F11 are resolved. F7: the per-cell p_outside values and the combined 33% are in
plan.json; I recomputed them (forest K=5 0.243, K=2 0.077, combined 0.331). New: F12 (plan
says hdm 0.1.0 behaves like c = 0.5, but sources/hdm_penalty.md shows 0.1.0 is about
c = 0.62) and F13 (no fixed reading of a failed lasso cell against sens-lasso-c11). Both minor.

Verified: the re-run of check-learner-ports. Lasso shift +0.04, max 0.36, cor_l 0.99999997.
The other four learners are identical to the first run, which is kept in git b57c415. The
rlasso_fit_predict threshold (coef/sd_keep after division by psi) matches
design.learners.lasso. No analysis run exists (only data-prep runs). crew.py validate is OK.
The re-run's Python phase took 110 s, which is inside the timing model's range, so the
254 s of the first run was a load outlier.

Suspicions (results stage):
- Forest K=5 is the likely H2 failure (p about 0.24). Check that the reading is applied exactly
  (same sign, |diff - shift| <= tol), and that 'consistent with the port deviation' is not
  stretched into 'reproduced'.
- Lasso: any failure reads 'not explained'. Watch for sens-lasso-c11 being used as an excuse
  ('the authors used c = 1.1') against the timeline in sources/hdm_penalty.md section 5 (F13).
- Check that every pass is worded 'no shift above MDS80 detected', with the tolerance shown
  next to each cell.
- K=5 ports were never checked. The paper must carry that caveat on every K=5 reading.
- crew.json title still says "raise" (paper stage).
- The code reviewer (code-r2) owns the rulings on code-r1 F1-F3. Do not double-count them.

## code-r2 (2026-11-18): pass, 0 critical / 0 major / 0 minor open

Status: F1 (zero threshold), F2 (NOTES mechanism) and F3 (verdict exports port metrics) are resolved.
No new findings. The amendment and the re-run of check-learner-ports (13:49:54Z) come before any
analysis run. validate is OK.

Verified myself (unlogged, scratchpad, synthetic Y/D only):
- The lasso port against the authors' rlassoF in hdm 0.3.2 on 4 heavy-tailed units (Y SD ~$100k,
  skew up to 2.9; 2 units at K = 2, 2 at K = 5): theta differs by $0.2-0.7. So the scale concern
  (design-r2 F9) and the unchecked K = 5 size are closed for the lasso.
- verdict.py on fabricated metrics: every reading branch is correct.

Suspicions:
- Forest: -$216 on the D side, cause unidentified (F8). Expect a low-side forest K=5 failure read
  as 'consistent with the measured port deviation'. At results, check that the paper adds the
  synthetic-scale and K = 2-only caveat next to it.
- The lasso reading uses the run's shift +0.045, not the table's 0.0. The difference is immaterial.

Check at results:
- S unchanged and the overrun disclosed. Claim values come from main-* only. Port metrics are
  cited through verdict macros, not typed.

## results-r1 (2026-11-19): revise, 0 critical / 2 major / 3 minor open

Rulings: H1 supported. H2 supported as pre-registered (0 of 10 outside, 8 of 8 testable inside, lasso
inside but not testable). H3 supported (margins $1,066 and $761, both against the tree). sens-lasso-c11
is descriptive only, as required.

Findings:
- F1 (major): the H2 claims say "pass" without the pre-registered scope ("no shift > MDS80 detected").
  hypotheses[1] (tolerance) and decision_rules.H2 (MDS80) also disagree on what a pass means. The
  forest K=5 diff of -$206 is about the measured -$216 port shift, yet it passes because MDS80 is $373.
- F2 (major): no claims back the 30 published numbers of the side-by-side table (the pub_* verdict
  metrics are unclaimed), the 33% / per-cell p_outside, or the wall-time overrun.
- F3 (minor): the lasso adjusted SEs are not reproduced (0.79/0.84), and the split spread is 4.7-6.7x
  smaller than published. No claim states this.
- F4 (minor): the port-shift claims are labelled "1991 US dollars" but are synthetic dollars.
- F5 (minor): the c-hdm-c citation still says hdm 0.1.0 means c = 0.5 (it is about 0.62; design-r3 F12
  was fixed in the plan only).

Verified myself:
- Recomputed all 12 (run, K) aggregates, tolerances, MDS80, testability, tol_obs and the H3 margins
  from splits.csv.
- Re-executed 16 (split, K) cells over all six runs (relative difference 1e-11).
- validate and validate --strict pass. The run order and gate timing are correct.
- The NOTES numbers match the ledger.
- The interrupted first main-lasso attempt produced no outputs, and its seeds were fixed.

Check at round 2 / paper:
- F1: the forest h2 claims carry the port-FAIL and MDS80 caveat, and one pass definition is used.
- F2: claims exist for pub_theta and pub_se_*, the 33% figure and the wall time.
- The paper must not say "reproduced" or "replicates" for H2 without "no shift > MDS80 detected".
- The paper must not use the lasso's $16/$14 as proof that the port matches.
- The K = 5 port caveat must appear.
- The crew.json title still says "raise" (paper stage). The estimand is the PLR coefficient, not the ATE.

## results-r2 (2026-11-19): pass, 0 critical / 0 major / 1 minor open

Status: F1-F5 resolved. F2(b)(c) accepted under the PI ruling (33% and p_outside are plan.json design
facts fixed before the gate; wall time cited from NOTES, and it agrees with run.json times 16:10:03-
17:41:56). I checked the timeline rather than taking the ruling on trust. New: F6 (minor): the forest
port caveat is one-sided. The 5-fold claim says the cell "sits where the port deviation predicts" without
saying the shift was measured at 2-fold only. The 2-fold cell (diff -$52, $164 from -$216) carries no
port-FAIL note. Pooled forest diff is about -$160 +/- $85, so neither zero nor -$216 is excluded.

Verified: every typed number in the reworded H2 claims and lasso-spread-discrepancy against the metrics;
30 pub constants against sources/notes.md Table 2 Panel B; c-hdm-c against hdm_penalty.md; commit
d9a78ee touched only claims, numbers.tex, NOTES (no code, run or plan). validate and --strict OK.
Ran no model this round.

Check at paper:
- 33% and p_outside are labelled pre-analysis design figures from plan.json, never findings. They will
  be typed literals (no macro); the paper review must check that they match plan.json exactly.
- Derived numbers typed only in claim text (4.7x/6.7x spread ratio, $164, 1.30 x tolerance) have no
  macro. The Writer must not type them unless backed by a macro or plan.json.
- MDS80 next to every pass; "no shift > MDS80 detected", never "reproduced"/"replicates" for H2.
- Forest: both cells need the port-FAIL caveat; K = 5 needs the "2-fold only" caveat (F6).
- The lasso $16/$14 must not be called a reproduction (lasso-spread-discrepancy).
- crew.json title still says "raise". The estimand is the PLR coefficient, not the ATE.

## paper-r1 (2026-11-19): revise, 0 critical / 1 major / 7 minor open

Findings:
- F1 (major): Section 2 quotes only the $5 forest-5 gap from the authors' AER P&P 2017 run (c-aerpp-rerun).
  The other gaps are omitted: $5-33 at 5-fold and up to $154 at 2-fold (nnet 9,104 vs 8,950), all inside
  the tolerances (notes.md section 5). This run validates the tolerances and calibrates our +$157 nnet-2
  gap. Its lasso-5 SE of 1,581 bears on the lasso spread discrepancy, but the Scout must say which SE
  type it is.
- F2: the "forest has the highest m-hat RMSE, the direction the port check found" sentence. R's own
  forest is also last on synthetic data (0.4715 vs 0.4598-0.4646).
- F3: the 92 min excludes the interrupted first main-lasso attempt (duration unrecorded, 14:39-16:09).
- F4: the abstract calls the published split spread observed (it is inferred). Limitations ties the
  independence assumption to Bonferroni instead of the 33% figure.
- F5: the Abadie income band comes from NBER TWP 260 (CODEBOOK [A]), which is not in refs.bib.
  abadie2003 is DOI-only.
- F6: AI-use says "17 full text", but 3 of those are summarized web fetches. The review and
  replication items are stale.
- F7: the conclusion generalises "an independent implementation"; the crew.json title still says "raise".
- F8: bib casing ({N}eyman) and the DoubleML entries have no year.

Verified myself (no model run; arithmetic and file reads only):
- validate OK. A scratch compile of paper/ gives 18 pp, no undefined refs, and bibtex warns only on
  the 2 empty years.
- Every typed design-fact literal matches plan.json: 0.24 (0.19-0.31), 0.08, 0.005-0.006, 33%,
  x4.5, $673/$649, 2.262/1.75/$25/0.999, 7e-5, 34-43 and 70-100 min, -$87 (SE $16), $14,300.
- Source literals match notes.md: $19,559 (1,413), $9,252 (1,400), and the $7,717-$9,247 range over
  7 learners.
- Process literals match NOTES and run.json: 92 min, load 46-90, lasso 52 min, c11 11 min.
- Writer-derived statements are true: all adj-SE ratios outside 15% are lasso only; bracketed SE ratios
  0.95-1.05; tol_obs < tol everywhere with all diffs inside; nnet-2 is the largest of six; RMSE
  ranges; m-hat out zero for lasso/tree/boosting; H3 margins vs tree; CI low; pct/SD units.
- Every memory checklist item holds: MDS80 next to each pass; no "reproduced"; the forest caveat
  on both cells plus "2-fold only"; lasso "inside, not testable"; estimand PLR not ATE; c = 1.1 a
  conjecture citing the timeline; both H2 amendments and the restart disclosed.
- AI-use: the gate times and review counts match the log and reviews. No --accept-findings anywhere.
  The repo is PUBLIC.
- Oddity (not filed): design-r3 created 14:33:00Z, but the designer logged its F12/F13 answer at
  14:32:20Z.

Check at round 2:
- F1: the full gap range and the "all inside tolerance" statement, with a claim; whether the lasso
  SE type was confirmed before it is used.
- F2-F8 wording. The AI-use now names paper-r1 and the replication.json result. The Replicator's
  verdict: BLAS-dependent lasso/nnet reruns may differ.

## paper-r2 (2026-11-19): revise, 0 critical / 1 major / 2 minor open

Status: F1-F5, F7 and F8 are resolved. F6(b) stays open: the AI-use replication and review
items are stale and can only be closed after replication.json and the final paper round exist.
New: F9 (minor) and F10 (major).

- F9: "$5 to $33 at 5 folds" is wrong; the largest of the five in-scope gaps is $27, and $33
  is probably the Ensemble column. The error started in notes.md and in MY paper-r1 F1 text.
  The paper says the AER P&P appendix, but only the arXiv preprint was read. The dmlv4 bib
  entry prints the year twice.
- F10: the earlier run is misread. On independent splits, under the published-implied spread,
  the gaps are jointly too small: sum z^2 = 2.95 on 10 df (p about 0.02). The lasso gaps of
  -10/+15 against a run-to-run SD of $293/$227 have joint p of about 0.0014. Under our observed
  spreads, sum z^2 = 5.8 (p about 0.17). So "wide lasso spread is a feature of the authors'
  procedure" is backwards, or else it is mechanical if the splits were shared. The max-vs-max
  comparison (+157 vs +154) hides that ours is larger in 7 of 10 cells (RMS about $99 vs $61).
  My paper-r1 F1 ruling ("out-of-sample check that the tolerances are not too tight") partly
  invited this. Question-r2 memory had warned against it.

Verified myself (no model run; published-table arithmetic and file reads only):
- The ten 2017-vs-2018 gaps match the notes.md rows.
- A scratch compile of paper/ gives 19 pp with the same text as the committed main.pdf, and
  no undefined refs or BibTeX warnings. validate is OK.
- sources.json counts 16 + 3 + 2 + 1 = 22, matching ai-use. The abadie2000 record exists.
- DMLonGitHub history starts with a8ef8ef on 2017-06-01, after the v4 run (Dec 2016). 401K.R
  uses set.seed(1211), then foreach %dopar% on makeCluster(12) PSOCK, with no doRNG or
  clusterSetRNGStream. So even the public code's splits are not fixed by the seed.

Check at round 3:
- F10: the lasso "feature of the procedure" sentence is deleted or neutralised; "run-to-run" /
  "original code" is replaced; the max-vs-max sentence is dropped or made cell by cell (abstract,
  Sec. 6, conclusion). Any new z/p/RMS figure needs a claim, not a typed literal.
- F9: $27 in main.tex, c-aerpp-rerun and notes.md; "preprint" wording; bib year.
- F6: ai-use review count, replication item, "Replicator has not yet run", and the Limitations
  replication line, all against the Replicator's replication.json and REPLICATION.md.
- Check that the Replicator's result, if it fails on lasso/nnet BLAS, is reported per run with
  its magnitude, not just "differs".

## paper-r3 (2026-11-19): revise, 0 critical / 1 major / 3 minor open

Status: F9 and F10 are resolved. F6(b) is resolved for the replication part, but the AI-use
review count still says 2 paper rounds. New: F11 (major), F12 and F13 (minor).

- F11 corrects MY OWN paper-r2 error. 401K.R never calls registerDoParallel. makeCluster(12)
  is created but never registered, so %dopar% runs sequentially, and the warning is hidden
  by options(warn=-1). set.seed(1211) therefore fixes the splits (runif inside DoubleML,
  Moment_Functions.R line 53), given the package versions. The paper now prints my false claim
  ('does not fix the splits it draws on parallel workers'), attributed to 'the review'. Also:
  the repository starts at 91e7d6c on 2017-05-31T18:06Z (Readme only); the code comes in
  a8ef8ef on 2017-06-01T00:54Z. My earlier memory had both wrong.
  Lesson: check for backend registration before claiming anything about foreach RNG.
- F12: the abstract and conclusion still infer that the tolerances are 'if anything, wide'
  from the earlier-run gaps, which Sec. 2 says are not split noise. Better evidence is
  already in the paper: tol_obs < tol in all 10 cells.
- F13: replication.json has 15 'match' and 1 'ran' (timing-synthetic). The paper says
  'all 16 reproduced'.

Verified myself (no model run; file reads, arithmetic, GitHub API reads of public code):
- Every min/max or ordering statement against numbers.tex: Tol and MDS ranges, CiLow, Pct and
  SD ranges, RMSE ranges, SE-ratio ranges, the 15% statement, tol_obs, nnet-2 largest, H3
  margins vs tree.
- Ours larger than the earlier-run gap in 7/10 cells. RMS $61.2.
- Gate times and code-r2 (14:33:17Z) before check-noctrl (14:38:52Z).
- The replication facts against replication.json, REPLICATION.md and the run.json env.
  Every record has the same platform string; "same machine" cannot be proved beyond that.
- plan.json is unchanged since paper-r2. validate and --strict OK. A scratch compile gives
  20 pp, and its text equals the committed main.pdf.

Check at round 4 (last):
- F11: the clause is deleted or corrected with a dmlongithub claim; the date wording is fixed.
- F12: 'if anything, wide' is dropped or tied to tol_obs. F13: '15 matched + 1 ran'.
- F6: the AI-use names paper-r3/r4 and their verdicts. After round 4, the open items go to the
  human.
- Do not let a new sentence about the authors' code appear without a claim.
