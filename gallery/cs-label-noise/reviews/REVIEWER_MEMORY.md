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

## design-r1 (2026-11-18): verdict revise. No critical; F1-F2 major, F3-F6 minor open.

State at review: runs are fetch-data, prepare-data (label/feature counts only; no model imports) and timing-synthetic
(make_classification only). No analysis run. crew.py validate OK. Question-stage F16 is handled in hypotheses: ratio of
seed means, joint paired bootstrap, 5-point exclusion from rho=0 only, unstable-resample count. F17 wording fixed
("lose a larger share ... above the majority-class rate"). Checklist from question-r4 all satisfied in design.method
(explicit early_stopping=True with X_val = noisy 20% split; nested exact flips; shared split/candidates/random_state;
RF grid over min_samples_leaf/max_features/max_samples; LR C down to 1e-4; tuned C reported per rho; covtype class asserts).

I checked sklearn 1.9.1 source (.venv): HGB uses the supplied X_val; _should_stop compares to the score
n_iter_no_change+1 back and the fit loop never truncates predictors -> no rollback to best iteration (F3).
Arithmetic only (no data): percentile bootstrap at n=10 ~ 90% coverage; Nadeau-Bengio SE factor sqrt(1+10*114/341)=2.08,
sqrt(1+10*200/600)=2.08.

Open:
- F1 (major): seed intervals on breast_cancer/credit-g are re-splits of fixed rows -> too narrow; plus percentile
  undercoverage. Remedy: corrected t/BCa interval, or narrow claims to "over re-splits of these rows" and fix threats[3].
- F2 (major): ablations attribute mechanism from category changes. Remedy: paired interval for D_main - D_ablation from the
  shared index matrix, or descriptive only.
- F3 HGB no-rollback + one-hot scope; F4 undisclosed reinterpretation of task requirements (noisy val labels; "inconclusive"
  vs "no difference"); F5 compute assumes 8 cores, synthetic may understate covtype GBDT; F6 adult duplicates unstated.

Next round / code stage:
- Verify analyze.py implements whatever F1/F2 remedy is chosen, exactly, with the shared rng(20261119) index matrix.
- Verify exclusion-check run precedes main-noisy in runs/ timestamps and log.jsonl; analyze.py reads exclusion.json only.
- Verify experiment.py: fit(X_tr, y_tr_noisy, X_val=X_va, y_val=y_va_noisy); selection scored on noisy val; test predicted
  once (plus test_acc_half); preprocessing fit on train features only; flip asserts; SeedSequence([20261118,d,s]).spawn(5)
  order; candidates per method via spawn(4); no clean-val use outside A2.
- Watch for any change to seeds, N, datasets, thresholds after main-rho0 exists.

## design-r2 (2026-11-18): verdict revise. No critical; F7 major, F8-F10 minor open. F1-F6 resolved.

State at review: runs are fetch-data, prepare-data, timing-synthetic and timing-covtype-stress (all data-prep; the
stress run uses make_classification only). No analysis run. Manifest pins credit-g (OpenML 31 v1), adult (1590 v2),
covtype (archive sha256) and breast_cancer with sha256. crew.py validate OK. I ran nothing; arithmetic only.

Checked and held: delta-method influence l_ks = [(a0-a4) - r(a0-m)]/h is the right linearization of a ratio of seed
means; Delta tests for ablations on shared seeds; A2 reuses main rho=0 (correct); HGB no-rollback stated; 4 new
disclosures accurate; contingency 7 x W0 (rho=0 is the costliest cell); adult duplicate arithmetic (0.13 pairs/seed).

Open:
- F7 (major): N-B factor applied to adult/covtype where seeds draw near-independent 5k samples (overlap 184 / 15
  training rows), so SE doubled needlessly; n_te/n_tr term gives a J-independent floor (half-width >= 1.13 S; 1.49 S at
  J=10); 'no meaningful difference' needs S < 0.034, effectively unreachable. Remedy: N-B only on breast_cancer/credit-g
  (or overlap-scaled), or disclose the over-conservatism and the floor.
- F8: stress run made the problem harder -> earlier stopping; it cannot show the estimate is not optimistic. Wording.
- F9: ablation denominators (GBDT-noES rho=0 headroom, half-budget headroom) not covered by stability rule.
- F10: stale task titles (bootstrap / "recompute H1"); Nadeau & Bengio 2003 not in refs.bib/sources.json.

Next round / code stage:
- Whichever F7 choice: check analyze.py uses exactly the stated factor per dataset, n_tr/n_te as in method
  (341/114, 600/200, 3000/1000), t.ppf(0.975, 9), and that the bootstrap never decides an outcome.
- Unstable-denominator check uses the corrected interval of h; check it is computed from rho=0 values only.
- Check log order: main-rho0 -> exclusion-check -> main-noisy; W0 contingency decision logged before ablations.
- Prior code-stage checklist from design-r1 still applies (noisy X_val in HGB fit, flip asserts, SeedSequence order,
  candidate spawn(4) order lr/rf/gbdt/gbdt_noes, single test prediction plus test_acc_half).

## design-r3 (2026-11-18): verdict pass. No critical or major open; F10 (part b) and F11 minor open. F7, F8, F9 resolved.

State at review: runs are still only fetch-data, prepare-data, timing-synthetic, timing-covtype-stress. No analysis run.
plan.json sha256 4cfb882b... matches the designer's logged hash. question, hypotheses, contribution, seed_definition unchanged
from HEAD; only the design sections changed. validate OK. I ran nothing on any data; arithmetic only (t(0.975,9)=2.262;
0.72 S and 1.49 S; S < 0.070 and S < 0.034).

Open:
- F10b: nadeau2003 cited in design.method and disclosures[2] but no refs.bib entry and no sources.json record. dt-pin still 'doing'.
- F11: the ranking 'within noise' rule (SD > mean gap) is looser than the 1.49 S corrected interval on breast_cancer/credit-g and
  stricter than 0.72 S on adult/covtype. Remedy: use the dataset's paired t(9) interval with the same c.

Strongest remaining objection (power, not bias): credit-g will likely be excluded or 'unstable denominator', so H1 overall needs
all three of breast_cancer/adult/covtype, and breast_cancer is judged at 1.49 S. Expect 'inconclusive' overall; the paper must
lead with per-dataset D, S and half-width and must not dress up an inconclusive result.

Code stage checklist:
- analyze.py: c = 0.1 + n_te/n_tr only for breast_cancer (114/341) and credit-g (200/600); c = 0.1 for adult/covtype; t.ppf(0.975, 9);
  the same c in the h-stability check (lower bound < 0.01) and the Delta intervals; the bootstrap never decides an outcome; outcome order
  supported, contradicted, no meaningful difference, inconclusive; the overall rule max(2, ceil(0.75 n)).
- Stability rule applied to GBDT-noES rho=0 (A1) and to half-budget rho=0 (A3); ablations use the main exclusion.json unchanged.
- Ledger order main-rho0 -> exclusion-check -> main-noisy; W0 contingency decision logged before the ablations.
- Prior checklist: noisy X_val in the HGB fit; flip asserts; SeedSequence([20261118,d,s]).spawn(5) order; candidate spawn(4) order
  lr/rf/gbdt/gbdt_noes; a single test prediction plus test_acc_half; preprocessing fit on training features only.
- Whatever the ranking rule becomes (F11), check that analyze.py implements it as written.

## code-r1 (2026-11-18): verdict pass. No critical or major open; F1 and F2 minor open.

State at review: code/common.py, experiment.py, exclusion.py, analyze.py are new and untracked. The runs are fetch-data, prepare-data,
two timing runs and smoke (data-prep, seed 100, N=2, all variants; it writes structure only plus GBDT n_iter). No analysis run and no
results/ directory. validate OK.

What I ran (no study seeds, no study results): sklearn 1.9.1 checks (LR l1_ratio=0.0 gives the same coefficients as the default L2, no warning;
HGB.fit accepts X_val/y_val, and noisy y_val changes n_iter_); experiment.prepare/flip/run_cell on make_classification data with the name
"adult" (prep deterministic across calls, val flips nested, scaler fitted on train only, cleanval GBDT stopped much later than main);
exclusion.py and every analyze.py mode on synthetic cell tables in the scratchpad (D matched an independent recompute, half-width/S =
1.491/1.489/0.715/0.715, delta-method SE within 1% of a jackknife except credit-g with a tiny h, outcomes and the overall count rule
behaved as written). Float-boundary probe: F1.

Checked and held: noisy y_val in the HGB fit and in selection (main); clean y_va only in cleanval and in diagnostics; one test predict
plus the half-budget predict; ties go to the earlier candidate; cand.spawn(4) order lr/rf/gbdt/gbdt_noes; split second integer =
generate_state(2)[1]; draw order perm_tr, shift_tr, perm_va, shift_va; the outcome order; H2 any/all logic; excluded overrides
unstable; unstable counts in n; bootstrap BOOT_IDX from default_rng(20261119) shared and never deciding; A2 reuses main rho0 and hc_main;
A1/A3 own-denominator checks; the ranking 'within noise' rule uses the t(9) interval with c.

Results-stage checklist:
- Ledger order: main-rho0 -> exclusion-check -> main-noisy -> h-tests; exclusion.json hash as output of exclusion-check equals input hash of
  h-tests (F2). common.py is listed as --code on every run.
- Was F1 fixed before main-rho0? If it was fixed after, it must be disclosed. Check whether any credit-g/adult headroom or ddrop sits on a cutoff.
- W0 from runs/main-rho0/timing.json; any contingency (dropping A1/A2) logged before the ablations, and 7 x W0 arithmetic.
- The h-tests metrics' {d}.H1.informative must equal exclusion-check's {d}.informative_h1.
- A1 compares two different candidate streams (gbdt vs gbdt_noes), as designed. An 'attributed' A1 result mixes early stopping with
  different random configurations; the paper should say so.
- Claims: 'inconclusive' is never written 'no difference'; S and the half-width are next to every D.
