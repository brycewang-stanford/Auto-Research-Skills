# Reviewer memory: cs-label-noise

## question-r1 (2026-11-18): verdict revise. No critical findings; 5 major and 3 minor findings open.

Pilot (my own check, outside the workspace and not a crew run): 5 seeds, untuned scikit-learn defaults, 80/20
stratified split, 40% flips to a different class. Drops 0% -> 40%:
- iris: LR .13, RF .29, GB .15 (SD up to .13)
- wine: LR .15, RF .13, GB .23
- breast_cancer: LR .21, RF .21, GB .26
- digits: LR .12, RF .02, GB .11

So the RF-vs-GB sign depends on the dataset, and the variance on small test sets is large.

Suspicions to carry forward:
- The dataset choice decides H1. Watch for the dataset list being chosen or changed after pilot runs, and
  check the log.jsonl order against the runs/ timestamps.
- A clean vs noisy validation set (for tuning and early stopping) can be changed quietly. At the design and
  code stages, check which labels the tuner and early stopping see.
- HistGradientBoosting early_stopping='auto' only turns on when n > 10000. On toy datasets it is OFF unless
  set explicitly. Check the code.
- RF may be left untuned or tuned without min_samples_leaf / max_features. Check that the budgets are equal in
  number of fits.
- H2 confirmed by a chance reversal.
- Pooled means across datasets with different numbers of classes K.

Next round: check F1-F8. Read plan.json fresh and sources/notes.md (relabeling). If the datasets are named,
check that the test-set sizes support the stated decision rule.

## question-r2 (2026-11-18): verdict revise. No critical; F9-F11 major and F12-F13 minor open. F1, F2, F4-F8 resolved; F3 conceded.

What changed: four named datasets (breast_cancer, credit-g, adult, covtype), per-dataset decisions, a 10-seed paired
t-interval, H2-reversal dropped, noisy validation labels, and an exact-fraction flip to a different class. I checked
that noisy-validation selection is sound: E[noisy acc] = acc(1-rho) + (1-acc)rho/(K-1), increasing in acc.

Suspicions to carry forward:
- F9 compute: covtype 581k rows x 150 cells in a 1-hour laptop budget. Watch for a subsample size that appears
  only after timing runs, or one that differs by dataset or method. Check log.jsonl for any run before the design gate.
- F10: the departure from the brief (only breast_cancer ships with sklearn) must be disclosed. The OpenML data_id,
  version and hash belong in data/manifest.json; adult has several versions.
- F11: the absolute drop is confounded with starting accuracy (LR on covtype) and a majority-class floor
  (credit-g 70%, adult ~76%). Check that the design pre-specifies reading drops together with accuracy at rho=0.4.
- Design stage: the budget is counted in fits per method. Does GBDT early stopping (on noisy labels) count as free
  extra tuning against RF? Is HGB early_stopping set explicitly (with 'auto' it is off for n <= 10000)? Is the RF
  grid over min_samples_leaf / max_features? Is LR's C grid wide enough to reach strong regularization
  (van Rooyen)? Is the tuned C reported for each rate?
- F13: per seed, the split, the flip set and the model RNG must all be redrawn. A negligible-difference threshold
  must be set before results.

Next round: check F9-F13 in plan.json and data/manifest.json. Re-read the disclosures. Confirm log.jsonl has
no runs.

## question-r3 (2026-11-18): verdict revise. No critical; F11 major and F14-F15 minor open. F9, F10, F12, F13 resolved.

What changed: a stratified cap of 5,000 rows for every dataset; disclosures[1] (departure from the brief and the
selection rule; I checked it against notes.md and it is accurate); H2's rule written out; seed_definition; a
1-point threshold. log.jsonl still holds only init, and runs/ and code/ are empty. I ran nothing this round.

F11 is still open for two reasons. (1) The accuracy guard is applied only to support, never to contradiction.
(2) The floor case: if both methods sit at the majority rate at rho=0.4, the difference in drops equals the
difference in clean accuracy and the guard passes automatically. credit-g is the likely case (about 0.75 tuned
against a 0.70 majority rate, n_train=600). The remedies I offered: a headroom-normalized drop as the primary
metric, or a 'floor' outcome with fixed count denominators.

Training sizes under the cap with 60/20/20: breast_cancer 341/114/114, credit-g 600/200/200, adult and covtype
3000/1000/1000. On breast_cancer one test example is about 0.9 points, close to the 1-point threshold.

Suspicions for the design stage:
- data/manifest.json must have the OpenML data_id, version and sha256 for credit-g, adult and covtype before any
  run (promised in disclosures[1]).
- Compute: 600 cells times the tuning budget. Any timing must be on synthetic data and logged with `crew.py log`.
- Within a seed, are the split and test set shared across all 5 rates and all 3 methods? Pairing needs this.
  Are the flip sets nested across rates?
- HGB early stopping: does it use the 20% noisy validation set or an internal validation_fraction carved from
  the training data? Is early_stopping set explicitly (not 'auto')? Does it count against the fit budget?
- The RF grid should cover min_samples_leaf and max_features. The LR C grid should reach strong regularization.
  Is the tuned C reported at each rate?
- covtype: class 4 is about 0.5% of rows, so the stratified 5,000-row sample gives about 24 rows of it. Check that
  the stratified split does not fail and that the flips handle K=7.
- If F11 stays open past round 4, flag the credit-g floor to the human explicitly.

## question-r4 (2026-11-18, LAST round): verdict revise. No critical; F16 major and F17 minor open. F11, F14, F15 resolved.

What changed: the primary measure is now the share of headroom lost, r = (acc0 - acc0.4)/(acc0 - m), per method and seed. A dataset
is excluded if mean headroom < 1 point. The threshold is 0.05 on the r scale. The accuracy guard is removed, and 'no meaningful
difference' is added. log.jsonl still holds only init; runs/, code/ and paper/ are empty; data/manifest.json is still empty. I ran nothing.

Open for the human after round 4:
- F16 (major): per-seed ratio. On credit-g the headroom is about 5 points and the per-seed SE about 3.1 points, so P(some
  method-seed has headroom < 1 point) is about 0.87 (my arithmetic, assumed acc 0.75). There is no rule for near-zero or negative
  denominators, and m is undefined. Remedy: ratio of seed means plus a paired bootstrap, or a stricter exclusion rule
  (>= 5 points and every seed positive; exclude the dataset, never the seed).
- F17 (minor): the question says 'lose more accuracy' (absolute) while the hypotheses use relative. The 'denominator fixed before
  results' wording is inaccurate.

Design stage checklist (carry over):
- Whichever F16 handling is chosen, verify that the analysis code implements exactly that, with no seed-level filtering added later.
- manifest: OpenML data_id/version/sha256 for credit-g, adult and covtype before any run.
- Within a seed, the split and test set must be shared across rates and methods. Are the flip sets nested across rates?
- HGB: early_stopping set explicitly; which validation set (the noisy 20% or an internal validation_fraction); does it count toward the budget?
- RF grid over min_samples_leaf/max_features; LR C grid reaching strong regularization; tuned C reported per rate.
- covtype class 4 (~24 rows in a 5k sample): does the stratified split work, and do flips work with K=7?
- Compute timing only on synthetic data, logged.
