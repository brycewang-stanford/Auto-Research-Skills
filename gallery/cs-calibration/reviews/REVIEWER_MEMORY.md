# Reviewer memory: cs-calibration

## question-r1 (2026-11-18 UTC), verdict: revise (0 critical, 5 major, 4 minor)

Suspicions:
- H2 may be confirmed in binned ECE (which favours isotonic) and then presented as
  settling a dispute that is about proper scores. Watch which metric is labelled
  "primary" at design, and whether it changes after results.
- The choice of datasets and their calibration-split sizes can decide H2. Watch for
  OpenML datasets added or swapped after any pilot, and for load_breast_cancer-sized
  calibration splits.
- The novelty claims ("open", "clean test") are inflated relative to fonseca2017 (which
  ran Friedman GBC with isotonic on a held-out split and found it helped) and to
  manokhin2026 Appendix A (per-architecture results, unchecked).
- The Scout's summary of fonseca2017 left out the Sec. 3 sentence that RF/GBC beat LR
  on uncalibrated Brier.

Asked for:
- F1 a named metric per hypothesis (proper score for H2; calibration measure for H1).
- F2 a fixed dataset count and a per-dataset seed-noise decision rule.
- F3 named, pinned datasets and a minimum calibration n (or calibration n as a moderator).
- F4/F5 relabel H2b and narrow the contribution scope.
- F6 define "without recalibration" (defaults at the pinned version, or tuned).
- F7 Platt: descriptive or hypothesised, and one input scale for every model.
- F8 fix the fonseca2017 note.
- F9 use UTC for verified_on dates.

Check next time (question-r2 / design-r1):
- Is plan.json actually edited, not only the notes?
- Does design fix: ECE estimator (bins, equal-width/mass, P(y=1) vs top-label),
  log-loss clipping eps and clip counts, FrozenEstimator or manual calibrators (no
  ensemble=True), the same base model across none/Platt/isotonic, the seed redrawing
  both split and random_state, train-only preprocessing, an AUC control, the 60-min
  budget?
- If they claim manokhin2026 has no per-model HGB result, spot-check Appendix A.

Things I ran: none on study data. Fetched fonseca2017 PDF (arXiv) and the
manokhin2026 abs/html pages to check the novelty claims.

## question-r2 (2026-11-18 UTC), verdict: revise (0 critical, 3 major, 3 minor open)

Status of r1 findings: F1, F2, F3, F4, F5, F7, F8 and F9 are resolved. F6 stays open
(minor): "library defaults" leaves preprocessing unstated, meaning categorical encoding
and LR scaling/max_iter. plan.json was actually edited this time, not only the notes.

New:
- F10 (major): H2a/H2b have two co-primary metrics (log-loss and Brier) and no rule for
  combining them. In the Manokhin archive the two diverge for HGB and RF. The
  contribution's "proper scores primary" also contradicts H1, whose primary is ECE.
- F11 (major): the decision-rule categories overlap ("holds" and "no difference"), the
  "reference value" is undefined, and +/-1% of ECE is unreachably small. "Inconclusive"
  needs to be mapped to the task's "no difference".
- F12 (major): a naive paired t(9) over resplits of one pool is anti-conservative
  (Nadeau-Bengio). The cheapest fix is to scope verdicts to the sample. Also ask whether
  the 20k subsample is fixed or redrawn per seed.
- F13 (minor): the cap does not guarantee calibration n >= 1000; phoneme is about 5.4k
  rows. HGB early_stopping='auto' is on above 10k training rows, so it is on for 3
  datasets and off for phoneme.
- F14 (minor): the clipping eps decides H2a log-loss; equal-mass bin edges fall on ties
  for RF probabilities (multiples of 0.01).

Suspicions carried forward:
- When the metrics split (F10), watch which one ends up in the abstract.
- Nadeau and Bengio (2003) is cited from memory in F12 and is not in refs.bib. If the
  crew adopts the correction, the Scout must verify it.
- I did not re-read the Manokhin Appendix A figure values the Scout reported (RF
  67.69->59.19, HGB 38.76->57.37, GBC 30.38->62.85). Spot-check them at the literature
  review.

Check next time (question-r3 / design-r1):
- Does each hypothesis have exactly one confirmatory metric?
- Is the precedence in the decision rule stated, with an absolute ECE margin?
- Is the interval scoped to the sample, or corrected?
- Design: split fractions and calibration n per dataset; HGB early_stopping set
  explicitly; encoder and scaler fit on train only; clipping eps and clip counts;
  equal-mass tie handling; FrozenEstimator or manual calibration (no ensemble=True); the
  same base model across none/Platt/isotonic; AUC control; 60-minute budget.
- runs/ must still be empty before the design gate.

Things I ran: nothing on study data. I ran only crew.py status and validate, and read
workspace files.

## question-r3 (2026-11-18 UTC), verdict: pass (0 critical, 0 major, 7 minor open)

Status: F10, F11 and F12 are resolved. F12 is resolved by scoping the verdicts to the
sample. Conditional on the pool, the seeds are i.i.d. draws of the procedure, so a plain
paired t is valid for that target. F6, F13 and F14 stay open (minor) and are deferred to
design through plan.json design_stage_items. plan.json sha256 e7c5f641... matches log
line "question revised after question-r2". runs/ is empty.

New (all minor):
- F15: the difference is defined as T minus the comparator's seed mean, which is
  unpaired, yet the rule says "paired t(9)". It must be d_s = T_s - R_s on the same seed.
- F16: Nadeau-Bengio is used on phoneme only and plain variance on the other three,
  on a false "fresh subsample" premise. The pools are 48,842, 45,211, 45,312 and 5,404
  rows (OpenML qualities API), so 20k draws overlap by about 44%. This mixes inferential
  targets across the k-of-4 count. Nadeau-Bengio is not in refs.bib or sources.json.
- F17: the overall rule has no "no difference" outcome, so 4/4 equivalence reads as
  "inconclusive". This is likely for H2b.
- F18: electricity (151) is a time series and random splits leak temporally. It needs
  disclosure in design.threats and the limitations.

Suspicions carried forward:
- Watch whether F15, F16 and F17 are fixed in plan.json before the design gate, and not
  after results. A switch from Nadeau-Bengio to plain variance, or back, after runs
  would be a search over the decision rule.
- I did not check the ECE estimator bias. With 15 equal-mass bins and about 1,600 test
  rows on phoneme (about 100 per bin), binned ECE has a positive bias of roughly
  0.02-0.03 for a perfectly calibrated model. That is larger than the 0.005 margin. It
  mostly cancels in an RF-minus-LR difference, but not if RF's ties concentrate the bins.
  Raise this at design if the estimator is not debiased or the test n per bin is small.
- Manokhin Appendix A figure values are still unchecked; check them at the literature
  review.

Check next time (design-r1):
- Split fractions and calibration n per dataset (phoneme needs a calibration fraction
  of at least about 19%). State whether the subsample is redrawn per seed.
- One variance rule for all four datasets, matching the stated scope. If Nadeau-Bengio
  is kept, it must be verified in refs.bib.
- Paired d_s definition; an overall "no difference" category.
- Encoder, scaler and LR max_iter fitted on train only (F6). HGB early_stopping set
  explicitly (F13). ECE tie handling and log-loss eps with clip counts (F14).
- FrozenEstimator or manual calibrators (no ensemble=True); the same base model across
  none/Platt/isotonic; Platt on the logit of the clipped probability; an AUC control;
  the 60-minute budget; electricity listed in threats (F18).
- runs/ must still be empty before the design gate.

Things I ran: nothing on study data. I ran crew.py validate and status, and queried the
OpenML qualities API for row counts (metadata only).

## design-r1 (2026-11-19 UTC), verdict: revise (0 critical, 1 major, 3 minor open)

Deferred question findings: F6, F13, F14, F15, F16, F17 and F18 are all addressed in
plan.json design.method (preprocessing, HGB early_stopping=False, eps 1e-6 with clip
counts, tie rule, paired d_s, one variance rule, overall "no difference", electricity
threats). Confirmed in the pinned sklearn 1.9.1 source: HGB 'auto' early stopping is
n_samples > 10_000 (line 534); CalibratedClassifierCV with ensemble=False calls
cross_val_predict on the cloned FrozenEstimator and the binary predict_proba is 1 - p
with no renormalisation; is_categorical_ is None for ndarray input. sklearn 1.9.1 also
ships method='temperature' (not used; not required).

New:
- F1 (major): H1 margin 0.005 is below the resolution of plug-in ECE (floor about 0.01
  at 5,000 test rows, about 0.03-0.04 on phoneme). The bias is not additive (it shrinks
  as true miscalibration grows), so ece_adj = ece - floor over-corrects the
  miscalibrated model and is biased against H1. The Scout's D1 pointed to Kumar's
  debiased estimator or ECE_sweep; the design used floor subtraction instead.
  Remedies: narrow H1 to the plug-in estimator and state the bias directions, or swap
  sensitivity (a) to kumar2019's debiased estimator. Either must be fixed before any run.
- F2 (minor): sens-ncal equalises calibration n only; phoneme's train n and test n
  also differ.
- F3 (minor): run.json env.python records 3.14.6 (crew.py's interpreter), but .venv is
  3.12.11; Python is not pinned in requirements.txt.
- F4 (minor): format and git status of results/preds/ (about 2.2M probabilities) are
  unspecified.

Suspicions carried forward:
- If H1 comes back "holds" on 3 of 4 with phoneme deciding, check whether |dbar| on
  phoneme is below its mean ece_floor.
- Watch that the confirmatory ECE is not swapped for ece_adj (or a new debiased
  estimator) after results. Any change must have a log line timestamped before the
  main run.
- The timing script's seed streams (3 spawns, split.spawn) differ from method step 2
  (4 spawns, generate_state(2)). That does not matter for timing, but the code review
  must check that experiment.py follows step 2, not the timing script.

Check next time (design-r2 / code-r1):
- F1: a resolution, a debiased estimator, or narrowed H1 wording, with a plan.json
  sha256 logged.
- Code: the LogitScore decision_function path is used (not predict_proba); the
  bit-identity assertion exists and runs; electricity sort order is by original index
  carried through train_test_split; the ECE tie rule test covers a group that spans a
  bin edge; the manifest feature lists are used, not dtypes; floor Generators are in
  order (lr, rf, hgb) x (none, platt, isotonic).
- runs/ must contain only data-prep runs until the design gate is approved.

Things I ran: no model and no estimate on study data. I counted duplicate feature
vectors on data/raw CSVs with the target dropped (adult 57 excess, phoneme 9, others
0; negligible), read the sklearn 1.9.1 source, and ran crew.py validate (OK).

## design-r2 (2026-11-19 UTC), verdict: pass (0 critical, 0 major, 1 minor open)

Status of r1 findings: F1 conceded (H1 narrowed to the plug-in estimator, bias
directions stated, ece_adj replaced by Kumar Def. G.3 ece_db, amendment disclosed and
logged before any run; plan.json sha256 a697fbf6... matches the last designer log line).
F2, F3, F4 resolved. I checked Def. G.3 against the arXiv v2 PDF myself: the formula,
variance y_k(1-y_k)/(n p_k), and 'a heuristic approach' all match step 8 and claim
c-kumar-debiased-ece.

New:
- F5 (minor): contribution and H1 label still say "replication" of Niculescu-Mizil and
  Caruana, while the verdict is now about an estimator whose floor difference can decide
  it. Cheap fix: reword; call it a replication only where ece_db agrees in direction.

Suspicions carried forward:
- Results: if H1 is "supported" or "contradicted" where |dbar| is below the mean floor
  (about 0.01-0.02; phoneme 0.03-0.04), or where ece_db disagrees, check that the
  abstract states both (step 11) and does not say "replicates".
- Confirmatory ECE must not be swapped for ece_db after results.
- Ledger env.python records crew.py's interpreter (3.14.6), not .venv 3.12.11. At
  replication, check the clean environment uses .python-version / requirements header,
  and that the paper does not quote env.python.
- fit seconds must stay out of every runs/*/metrics.json (crew.py rerun compares every
  key at rtol 1e-6); step 8 says "not compared on rerun", which holds only if they live
  in cells.csv.

Check next time (code-r1):
- Everything listed under design-r1 "Check next time" for code.
- ece_db: one rng.normal(size=(1000, K)) call per cell, children 0..8 in (lr, rf, hgb) x
  (none, platt, isotonic) order, 9..11 for sens-ncal; no flooring; bins with y_k in
  {0,1} give zero correction; same bins/tie rule as ece.
- sens-elec-time uses SeedSequence([20261119, 2, s, 1]) and sorts by original row index.
- runs/ must contain only data-prep runs until the design gate is approved.

Things I ran: no model and no estimate on study data. crew.py validate (OK), sha256 of
plan.json, and fetched arXiv:1909.10155v2 into reviewer scratch to read Def. G.3.
