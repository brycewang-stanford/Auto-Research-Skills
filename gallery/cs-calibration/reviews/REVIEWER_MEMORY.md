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

## code-r1 (2026-11-19 UTC), verdict: revise (0 critical, 2 major, 1 minor open)

Checked against the design-r1/r2 "Check next time" lists, and all of it held: LogitScore
decision_function routing, bit-identity assertion, electricity sort by original file row,
tie-edge test, manifest feature lists, debias child order (0..8 main, 9..11 sens-ncal),
one rng.normal((1000, K)) per cell, no flooring, pure bins give zero correction,
SeedSequence([20261119, 2, s, 1]), fit seconds kept out of metrics.json, runs/ holds
data-prep runs only, and no results/ dir. crew.py rerun compares metrics only, so
main_timing.json as an --output is harmless.

Findings:
- F1 (major): experiment.main() asserts that one-hot width is constant across seeds. The
  adult native-country level 'Holand-Netherlands' (one row in UCI) puts P(crash) at
  about 0.90. The assertion fires after cells.csv is written. describe.py reports seed 0's
  width. Synthetic demo reproduced the varying width.
- F2 (major): NOTES item 2 is not just wording. ece_db keeps about 59% of the floor, so
  it keeps the sign of a floor-only RF-minus-LR difference (synthetic: 86-88% per seed,
  mean sign always). The "replication only where ece_db agrees" licence (hypotheses[0],
  contribution) and threats[0]'s disagreement fallback are therefore close to vacuous.
  Cheapest fix: reword before main and drop the replication licence.
- F3 (minor): NOTES item 1 is wording only (step 7 parenthetical); the code matches step 7.

Suspicions carried forward:
- If F2 is fixed by adding an analytic-floor metric, it must be logged before main. Check
  the plan.json sha256 against the log, and that the H1 metric, margin and rule are
  unchanged.
- If main crashes on F1 before the fix, cells.csv will exist before the code edit. Check
  that the rerun main is byte-identical and that nothing in the plan changed between
  them.
- Results: if H1 holds or is contradicted while |dbar| is below the floor difference,
  and ece_db "agrees", the paper must not say "replicates".

Check next time (code-r2 / results-r1):
- F1: width min/max instead of the assertion; a unit test with a single-row level;
  unit-tests rerun with --replace; crew.py validate OK.
- F2/F3: plan.json wording edits logged, with the sha256 matching the last log line.
- Results: main exit 0; cpu_minutes <= 30; lr_nonconverged_cells; hgb_n_iter 100/100;
  ece_bins on RF none (ties); the clip counts.

Things I ran: no model and no estimate on study data, and data/raw was not opened. I
reran code/test_metrics.py with cwd in reviewer scratch (32/32 pass; the workspace runs/
was untouched). I ran a synthetic width demo and a synthetic ece_db sign simulation
(calib-reviewer2/width_demo.py, ecedb_sign.py) and crew.py validate (OK).

## results-r1 (2026-11-19 UTC), verdict: revise (0 critical, 1 major, 4 minor open)

Status of code-r1 findings: F1 resolved (width min/max; unit-tests --replace at 07:42:47Z
before main at 07:43:43Z; adult width 106-107). F2 conceded (narrowing logged at 07:41:34Z,
sha256 bee7499f, before main; the current plan cff3831b = bee7499f + five task statuses,
verified by reconstruction). F3 resolved (step 7 wording).

What I checked and found sound: all 16 per-dataset categories and 4 overall verdicts
recomputed independently from cells.csv (precedence, paired t(9), margins and k-of-4 exact).
main, analyze, describe, sens_ncal and sens_elec_time re-executed in
calib-reviewer3/rerun; every CSV and metrics file is byte-identical. ece and brier
recomputed from the .npz files equal cells.csv exactly. lr_nonconverged 0, hgb n_iter
100/100, 2.55 CPU-min. No claim says replication. h1db is labelled descriptive everywhere.
H1 floor check (calib-reviewer3/floor.py, analytic floor sum_k p_k sqrt(2/pi)
sqrt(y_k(1-y_k)/n_k)): the floor difference is -0.0009 on bank-marketing and -0.0121 on
phoneme. The floor-adjusted intervals stay contradicted (bank-marketing -0.0139
[-0.0153, -0.0124], phoneme -0.0142 [-0.0222, -0.0062]), so H1 is not a floor artefact.
LR is genuinely miscalibrated there (ece_db close to ece).

New:
- F1 (major): sens-elec-time is degenerate. The chronological split gives ECE 0.17-0.33
  for every model, and recalibration makes LR worse (Brier 0.202 to 0.253), so it
  measures drift from the calibration quarter to the test quarter (plus the fill regime
  and date extrapolation), not leakage. Its H2a 'contradicted' and H2b 'holds' (-0.078)
  are claimed, but the absolute levels are not. Electricity carries the only H1 'holds'
  and the only H2a 'holds'. Remedy: narrow the claims and add the level claims.
- F2 (minor): the sens-ncal overall k-of-4 verdicts are not in the plan.
- F3 (minor): no SD claims and no ece_bins claims (RF none 11-13 bins against LR 15).
- F4 (minor): H1 contradicted reflects LR's miscalibration (phoneme AUC 0.81), not RF
  being well calibrated. H2b 'no difference' covers intervals that exclude 0 on both
  sides.
- F5 (minor): no log line for the plan sha; stale task titles and statuses
  (ece_adj; rv-*); a NOTES sentence says 'none was repeated'.

Suspicions carried forward:
- At the paper stage, watch whether electricity's 'holds' or the sens (c) H2b -0.078 is
  used as evidence that isotonic helps gradient boosting under drift.
- Watch that the abstract does not say 'RF is well calibrated' or 'isotonic has no
  effect on HGB'.
- Watch that the floor-adjusted H1 numbers in this memory do not enter the paper as
  findings. They are my post hoc check; if the crew wants them, they must be a logged,
  labelled post hoc run.
- Replication: main_timing.json is an output but not a metric, so a rerun is unaffected.
  results/preds is git-ignored and is rebuilt by main.

Check next time (results-r2):
- F1: new claims for the chronological per-model levels, reworded r-h*_time-* texts and
  NOTES, crew.py validate OK, and no new run needed (the metrics already exist).
- F2-F5: the claims and plan bookkeeping, with a log line holding the plan sha256.

Things I ran: crew.py validate (OK, also --strict) and status. I recomputed the decision
rule from results/cells.csv. I re-executed all five analysis scripts in reviewer
scratch, a copy of code/ plus data/raw CSVs and the manifest; the workspace was not
touched. I ran a post hoc analytic-floor check on results/preds/main (calib-reviewer3/floor.py).

## results-r2 (2026-11-19 UTC), verdict: pass (0 critical, 0 major, 3 minor open)

Status of results-r1 findings: F1-F5 are all resolved, with no new run. runs/, results/ and code/
are unchanged since e0b9816; only NOTES, claims texts, new claims and numbers.tex changed. plan.json
c3ebd78c is logged and differs from cff3831b only in tasks. All 222 new claims (156 SD, 54
chronological levels, 12 bins) match their metric keys and values. The 21 changed claims changed
only their text.

My own error: in results-r1 (F1 text and kill argument) I wrote that the overall verdicts do not
depend on electricity. That is wrong for H2b and incomplete for H2a, and the PI's experimenter brief
repeated it. The experimenter got H2b right.

New (all minor):
- F6: H2a's 'inconclusive' becomes 'no difference' if electricity is 'no difference'. The claim
  and NOTES say only 'not supported without electricity'. So two of the three overall verdicts
  (H2a, H2b) depend on electricity.
- F7: NOTES says both 576 and 354 result claims (stale paragraph at line 64).
- F8: isotonic cells are scored on 10-14 ECE bins; only the 'none' ece_bins are claimed.
  Descriptive isotonic ECE reductions partly reflect bin count.

Suspicions carried forward (paper stage):
- The abstract or results must say that the H2a and H2b overall verdicts depend on electricity
  and that its leakage question is open. Watch for 'H2a inconclusive regardless'.
- Watch that sens (c)'s HGB -0.078 is not used as evidence that isotonic helps under drift, and
  that the paper does not say 'RF is well calibrated' or 'isotonic has no effect on HGB'.
- Watch that 'isotonic lowers ECE on all four datasets' is not stated without the bin caveat (F8).
- The floor-adjusted H1 numbers from calib-reviewer3 must not enter the paper.
- Watch that ece_db is never a replication licence; no claim says 'replicat' now.
- The sens-ncal overall must be quoted only with its UNPLANNED AGGREGATION label.

Check next time (paper-r1):
- Every abstract and intro statement traces to a claim macro; no typed numbers, including the
  0.063, 0.81 and 0.95 that appear inside claim texts.
- The limitations section covers electricity's time ordering and its open leakage question, the
  ECE estimator bias and bins, the defaults-only scope, and the sample-scoped intervals.
- The ai-use statement discloses the plan amendments (disclosures[]).

Things I ran: crew.py validate (OK, also --strict) and status. I recomputed the decision rule and
the electricity-dependency counterfactuals from results/cells.csv and sens_elec_time_cells.csv
(calib-reviewer4/recompute.py, 0 mismatches). I checked claim text against metric key for the new
claims (calib-reviewer4/check_claims.py). No model was refitted; the workspace was not modified
except for my review and this memory.

## paper-r1 (2026-11-19 UTC), verdict: revise (0 critical, 3 major, 9 minor open)

What I checked and found sound: all 197 macros used in main.tex map to the intended run metric
(name-to-key dump); every per-dataset category (h1, h2a, h2b, h1db, ncal, time; 25 in all)
recomputes from the run metrics (0 mismatches); the 48 plain (non-macro) numbers in tab_levels (the
Platt log-loss and AUC cells) match describe metrics; plan.json has changed only in tasks and gates
since e0b9816 (cff3831b); crew.py validate --strict is OK. The paper does not use my calib-reviewer3
floor-adjusted numbers, does not call H1 a replication, states the electricity dependence of H2a/H2b
in the abstract, intro, results and conclusion, labels sens (c) as drift, gives the bin caveat for
isotonic ECE, and does not say 'RF is well calibrated' or 'isotonic has no effect'. The noise-floor
arithmetic (0.8 sqrt(p(1-p)/n_b); 41%; logit(1e-6) = -13.8) checks out.

Findings:
- F1 (major): the abstract's 'debiased estimator ... points the same way on every dataset' is
  presented as reassurance; the body says that agreement is not confirmation (code-r1 F2).
- F2 (major): related work line 156-159 credits manokhin2026 with 18/30 and 4/30 per-dataset log-loss
  counts. Those are the Scout's unlogged scratchpad tabulation of their archive, not the paper. It is
  also selective: the Brier counts (RF 13/30, HGB 14/30) remove the RF/HGB contrast.
- F3 (major): ai-use.tex says the code review 'passed' and lists code-r1 among stages that 'passed
  with minor findings'. code-r1 was revise with 2 major. main ran under two minutes later with no
  code-r2, and the fixes were verified first at results-r1.
- F4-F12 (minor): Sec. 6 lead overstates the plan.json disclosures (items 4-6 are absent); the
  machine-eps log-loss sensitivity was suppressed while the clipping dependence is asserted; the
  abstract's H1 sentence omits electricity 'holds'; 'Platt changed little' contradicts RF/electricity
  -0.0029; stale ai-use placeholders (replication.json now exists, passed); brier1950 (DOI-only) is
  cited for propriety; the intro's 1,000-case misattribution; typed '15' and '0.00005' and the Fig. 1
  dagger caption; the title promises more than the tests deliver.

Suspicions carried forward:
- If F2 is fixed by keeping the counts with a logged run, check that the run hashes the archive
  (sha256 7d33f9cd...) and that Brier is reported beside log-loss.
- When ai-use.tex is updated after this round and the replication, check the review counts (paper
  rounds), the replication.json timestamp against every run (the tab/fig runs finished 12:35-12:39Z;
  replication created 12:52:00Z), and the replicator's env (.venv 3.12.11, not crew.py's 3.14.6).
- Watch that a fix for F1 does not swap in another reassurance (for example 'robust to the
  estimator').

Check next time (paper-r2):
- Each F1-F12 against the files; numbers.tex regenerated and validate OK; main.pdf rebuilt after the
  tex; no new runs unless F2/F5 add a logged one (then check its kind and hashes).

Things I ran: crew.py validate (also --strict) and status; pdftotext of main.pdf; rendered both
figures to PNG; macro-to-metric dump; category recompute; plain-number check of tab_levels against
describe metrics (calib-reviewer5/plain.py); plan.json hash history via git show. No model was fitted,
and nothing in the workspace was modified except reviews/paper-r1/review.json and this memory.

## paper-r2 (2026-11-19 UTC), verdict: pass (0 critical, 0 major, 4 minor open)

Status of paper-r1 findings: F1-F12 are all resolved in the files. No run, code or result file
changed since the results gate. The last run is fig-intervals (12:39:14Z), and replication.json
(12:52:00Z) is newer. The current plan.json sha256 is 20c41f3c, which equals the 12:57:23Z
disclosure-added log line. Each Sec. 6 'Recorded' pointer matches a log line with a hash (06:55
afd41598, 07:03 c1d03097, 07:41 bee7499f, 07:43:18 code fix). Disclosure 5(c) matches the Figures
RA brief 20261119T122759Z. All 72 new LoglossMach macros map to the right describe keys. main.pdf
was rebuilt from the current tex (numbers.tex mtime is later but unchanged in content). I finally
checked Manokhin Appendix A on arXiv 2601.19944v1 p. 61 at 300 dpi: rf 67.69 -> iso 59.19,
hgb 38.76 -> 57.37, gbc 30.38 -> 62.85, and Platt ahead of isotonic for all three (rf.platt
43.45, hgb.platt 42.88, gbc.platt 45.57), so c-manokhin-appendix holds.

New (all minor):
- F13: 'Platt changed little except tree models on electricity' leaves out RF on phoneme. There
  Platt was -0.0009 [-0.0017, -0.0001], larger than isotonic's H2a -0.0007, which was
  inconclusive. HGB Platt on bank and phoneme was -0.0005, excluding 0. My r1 F7 remedy was too
  narrow.
- F14: AI-use and Sec. 3.7 say the rerun 'downloaded the data again'. REPLICATION.md says the
  rerun rebuilt from the copied sklearn_home cache. The cold download was a separate, unlogged run.
- F15: the machine-epsilon summary names adult (larger) and phoneme (equal) but leaves out
  electricity, where isotonic's log-loss advantage halves (0.010 -> 0.005), and bank (grows).
- F16: main.tex line 179 still says 'quadratic (Brier)' under gneiting2007. The Scout dropped
  '(Brier)' from c-proper-scores because the abstract does not name Brier.

Suspicions carried forward (submission):
- If the Writer edits for F13-F16, check that main.pdf is rebuilt, validate --strict is OK, and
  no new run is added (a run would make replication.json stale for the submission gate).
- The H2 verdicts' dependence on electricity and its open leakage question must stay in the
  abstract, results and conclusion through any further edit.

Things I ran: crew.py validate (also --strict) and status; pdftotext of main.pdf; a macro-to-key
check for the 72 LoglossMach claims; log/hash cross-checks; and a download of the Manokhin arXiv
PDF into calib-reviewer6/dl, with p. 61 rendered and read. No model was fitted, and nothing in the
workspace was modified except reviews/paper-r2/review.json and this memory.
