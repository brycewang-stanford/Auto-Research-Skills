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
