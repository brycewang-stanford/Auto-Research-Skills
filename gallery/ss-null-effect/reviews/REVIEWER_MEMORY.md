# Reviewer memory: ss-null-effect

## question-r1 (2026-11-18T12:04Z), verdict: revise
Suspicions:
- The seed is called "null-effect" and the brief ships 20 survey items plus wellbeing78.
  Most likely trap: forking paths across outcomes (a survey item comes out "significant" and
  gets promoted). Watch for any of those outcomes entering the analysis without being in a
  declared family that has a correction.
- Survey-item timing is unknown. They could be pre-program confounders or post-program bad
  controls. Watch for them quietly entering the propensity or outcome models.
- H1 has no smallest effect of interest, so a non-rejection will be read as "no effect"
  after the fact.
- log.jsonl Scout entry is stamped 20:10Z, which is in the future relative to this review
  (12:04Z). The log is hand-written, so do not trust its times as proof that work was
  outcome-blind.

What I asked for: F1 (close the set of outcomes), F2 (name the conditioning set and the role
of the survey items), F3 (a smallest effect of interest, or narrow H1), F4 (fix the ATT
now), F5 (name the treatment column, enrolment vs participation), F6 (the percentage
denominator), F7 (simultaneous CIs for H2), F8 (the log timestamp).

Next time (round 2 or the design review):
- Check plan.json for the full list of outcomes and their families, and for the named
  conditioning set.
- Check whether anyone opened data.csv beyond the header before the design gate. Look at
  runs/ for analysis-kind runs and at code/ for reads of outcome columns.
- Check that the trimming rule, learners, folds and seed are fixed, and that the
  propensity specification is fixed before outcomes are seen.
- Check that the re75 placebo conditions on re74 and not on re75.
- I did not verify the literature sources against their originals (not in scope). Do it
  in the literature review: spot-check card2018 ("over 200"), lalonde1986 ($886, SE 476,
  Table 5) and crump2009 ([0.1, 0.9]).

## question-r2 (2026-11-18T12:08Z), verdict: revise
F1-F8 all resolved. New: F9 (major, the $1,000 margin's units and basis), F10 (minor,
Romano-Wolf stepdown vs max-t decision rule), F11 (minor, plan revision not logged, no
hash or commit of plan.json).

Suspicions:
- The $1,000 margin was fixed blind to re78's scale. If the crew later "discovers" the
  units and adjusts the margin after seeing re78, that is a forking path. Any change to
  the margin must be logged before the first analysis run and anchored to covariates
  only (re74/re75).
- No code/, runs/ or data/raw yet. data/manifest.json is empty. Nothing shows outcomes
  were opened. The workspace is untracked in git, so file mtimes are the only timeline
  (machine local time is UTC+8; plan.json mtime 20:06:38 local = 12:06:38Z).
- Survey items are excluded as covariates. If they turn out to be pre-program
  motivation measures, unconfoundedness is weak. That is a limitation now, but the design
  must carry a sensitivity analysis (Imbens 2003 style) fixed in advance.

Next time (design review):
- re78 - re75 difference outcome (notes section 9.6) would be an extra outcome-like
  specification. Check that it is pre-declared as robustness, not a rescue.
- Interval for the relative effect (estimated denominator): delta method or bootstrap,
  fixed in advance.
- Overlap assumption (p(X) < 1 for ATT) stated; trimming rule and the trimmed estimand
  named as secondary.
- Learners, folds, seed and propensity specification fixed; alternative propensity
  sets listed and all reported.
- re75 placebo conditions on re74, not re75.
- Region coding (number of categories) and the treatment column name confirmed
  outcome-blind at data-prep, with a data-prep run, not an analysis run.
- Whether F9 was fixed by an outcome-blind anchor and logged before the gate.
- Literature review: still spot-check card2018, lalonde1986 ($886, SE 476) and
  crump2009 ([0.1, 0.9]).

## question-r3 (2026-11-18T12:10Z), verdict: pass
F9, F10 and F11 resolved. I recomputed plan.json's SHA-256 (1ccb35da...0f4e9a2) and it
matches log.jsonl line 3. New minor findings: F12 (the '10% conventional' margin has no
source; participants' re75 may be depressed by a pre-entry dip, so H1b may be untestable;
no fallback stated) and F13 (a Romano-Wolf/max-t bootstrap with ML nuisances against the
30-minute laptop budget).

Suspicions:
- The current plan.json is NOT in git. Commit e8e27e2 has the old $1,000 version (sha
  9960b098...). The PI's response to F11 claimed it was committed. Check that it is
  committed before the design gate.
- sources/notes.md (section 3, Imbens 2004) suggests running the re75 placebo "as data
  preparation". That would be a result before the design gate that could shape the
  propensity specification. If it shows up as a data-prep run, flag it.
- The data-prep run that computes M will load the whole of data.csv, outcomes included.
  Read its code. It must touch only the treatment column, re75 and other covariates,
  and its metrics must contain no outcome summaries.
- If TOST fails after the gate, watch for M being re-anchored (to re74, to the non-
  participant mean, or for price-year adjustments).

Next time (design review):
- M logged by a data-prep run before the gate; its code is outcome-blind.
- F12: is 'conventional' removed or cited, is there a precision proxy, is the TOST-fail
  fallback stated?
- F13: bootstrap type, number of draws and seed fixed; runtime checked on covariates.
- Carry over from r2: the overlap/trimming rule and the trimmed estimand as secondary;
  learners, folds and seed; the re75 placebo conditions on re74, not re75; Imbens (2003)
  sensitivity fixed; re78 - re75 only as declared robustness; the interval for the
  relative effect.
- Literature review: still spot-check card2018, lalonde1986 ($886, SE 476) and crump2009.

## design-r1 (2026-11-18T12:41Z), verdict: block
Checked and held: no script or run reads an outcome (prepare_covariates usecols; every
run input is covariates.csv or the raw file read by usecols); margin.py uses treat and
re75 only, M = 483.47; plan.json sha 1a61bcc5... matches the last log entry;
diag-overlap is covariates-only, B1/O1/O2 pass, B+ not fired; the RW/max-t seed
20261119, B = 10,000, 5x5 cross-fit and seeds are fixed; the relative-effect CI is
delta-method; trimming is a named secondary estimand; the re75 placebo conditions on re74.
The previous worry about the placebo running as data-prep did not happen.

Findings: F1 critical (re75 placebo is read as evidence against the assumption, but the
documented 1975 dip makes rejection expected; no consequence rule), F2 major (rob-diff
uses the dip year as base: mean-reversion bias), F3 major (1976 shock unnamed;
sens-imbens R^2 definition, out-of-grid rule, benchmark grouping and reading not fixed),
F4 major (missing-outcome n/n_k rescaling wrong unless missingness equal by arm; MAR not
stated), F5 minor (IPW absent from disagreement rule), F6 minor (design not committed;
two data-prep runs repeated without a note; d-data still doing).

Suspicions:
- Seed is built around the dip: treated 6,713 -> 4,835, controls 8,885 -> 9,645. A naive
  difference will look negative, a re75-based DiD positive. Watch for whichever
  robustness check "agrees" with a preferred story being promoted after the gate.
- If the crew now runs the placebo as data-prep to "see" it before rewriting F1, that
  is a pre-gate result shaping the design. It reads only covariates, so it is allowed in
  principle, but it must be logged and the reading fixed in plan.json in the same step.
- If they switch rob-diff to re78 - re74, check it conditions only on time-invariant
  covariates and is still excluded from or included in the disagreement rule explicitly.
- M is small partly because of the dip (7.2% of enrolees' 1974 mean); question-r3 F12
  accepted that. Watch for M being re-anchored to re74 now that the dip is documented.

Next time (design-r2):
- F1: identifying_assumption and placebo text; consequence of a rejection fixed.
- F2: base year of rob-diff or its relabelling; threats[1] corrected.
- F3: 1976 shock named; R^2 formulas, grid-censoring rule, benchmark grouping, reading.
- F4: missing-outcome estimand, denominator, MAR assumption; whether a missing-count
  run was done before the gate and by whom (PI decision).
- F5, F6: IPW in the rule; commit hash of plan.json in git equal to the logged hash.
- Recompute plan.json sha256 and compare with the newest log entry.
- Literature review still pending: spot-check card2018, lalonde1986 ($886, SE 476),
  crump2009 ([0.1, 0.9]).

## design-r2 (2026-11-18T12:49Z), verdict: revise
F1-F6 all resolved. I checked them against plan.json, not against the authors' responses.
Timeline verified: the design was revised at 12:46:15Z (log line 21), missing-counts ran at
12:46:55Z, and commit 57f5b3f was made at 12:47:22Z. HEAD plan.json sha 837988cf... equals
the working copy. missing-counts: 0 missing anywhere, so rob-ipow does not fire.
New: F7 (major) has no validity rule for sentinel or impossible outcome values.
missing_counts.py sees only NA and non-numeric strings. F8 (minor) covers three things:
the log's last plan hash (5aab4b04) is stale relative to plan.json (837988cf), the PI ruling
on F4 is not logged by the PI, and "rob-ipow not triggered" is not recorded in
design.diagnostics.
Formulas checked and correct: the ATT score and IF, TOST p, the delta-method psi_r, and
the R2 -> alpha/delta inversions. R2_D(G) via V - V_-G is inflated by logit
non-collapsibility. It errs conservative, so I did not raise it.

Suspicions:
- If F7 is "fixed" by a data-prep run that inspects outcome ranges or prints min/max, that
  reveals outcome values before the gate. It may only count out-of-range entries by arm
  against ranges written in plan.json first, and the log must show the rule before the run.
- After the gate, watch for winsorizing or recoding of re78 that is not in the plan.
- The headline is near-foreordained: H1b is likely to fail (proxy |ATT| < ~67) and the
  conclusion is likely not robust to earnings75. Watch for M being re-anchored, or for the
  earnings75 sentence being softened in the paper.
- select-re75 will be negative. Watch that it never gets cited as support.

Next time (design-r3, or results):
- F7: the ranges in plan.json; any count run's code and the log order.
- F8: the PI's log entry, the diagnostics note, and the final hash logged equal to the
  committed plan.json.
- Results: the disagreement rule is applied mechanically, including the IPW point-outside-CI
  test; the sensitivity reading rule is followed verbatim; every claim id in
  design.claim_ids is present.
- Literature review still pending: spot-check card2018, lalonde1986 ($886, SE 476),
  crump2009 ([0.1, 0.9]).

## design-r3 (2026-11-18T12:53Z), verdict: pass
F7 and F8 are resolved, and no finding is open (F1-F8 all resolved). Order verified: F7 ruling
12:50:12Z, outcome_validity written 12:51:05Z, range-counts run 12:52:14Z, diagnostics
12:52:38Z, commit fe34a16 at 12:52:38Z. plan.json sha fa4433e0... equals the last log entry
and HEAD. range_counts.py writes counts only, and all are 0. Every run is data-prep. No outcome
value is exposed beyond the scale/format. The PI's F4 ruling is logged retroactively. It is
disclosed and must appear in the AI-use statement.

Strongest remaining objection (for results/paper): there is no informative falsification
test; the dip and the unobserved 1976 shock remain; the earnings75 benchmark will likely make
the conclusion "not robust"; H1b is likely untestable (proxy half-width about 416 vs M = 483).

Next time (results):
- main-aipw's data input is the raw extract read with usecols; it must use exactly B(X), the
  folds and the seeds in plan.json; M is read from margin_metrics.json and never re-anchored.
- No winsorizing or recoding of re78; invalid-<k> echoes equal 0.
- The disagreement rule (threats[12]) is applied mechanically, including the IPW
  point-outside-CI test; the sensitivity reading rule is followed verbatim, with earnings75 always
  stated; select-re75 is never cited as support.
- Every id in design.claim_ids is present, including primary-effect/ci-low/ci-high.
- Every analysed outcome is reported with Romano-Wolf; no survey item is read.
- Literature review still pending: spot-check card2018, lalonde1986 ($886, SE 476),
  crump2009 ([0.1, 0.9]).

## code-r1 (2026-11-18T13:59Z), verdict: pass (post hoc; analysis had already run)
Checked code/*.py against plan.json line by line. I re-implemented the primary estimator independently and reproduced
theta_rep0 and theta_rep4 exactly. The EM tau equals the direct observed-likelihood MLE within $0.6. My own RF
re-implementation gives -12.5 against the recorded -10.0, the gap from region column order. All analysis code mtimes
(13:03-13:06Z) are after the gate and before main-aipw (13:12Z). No leakage was found. Open, all minor: F1, the
sensitivity strongest/weakest ordering, chosen in code (age vs educ near-tie on equiv); F2, the relative-effect CI uses
psi_bar (4% narrower); F3, the Hajek IPW clipping is not in the plan (0 clipped); F4, the O1/O2-conditional H1b branch
is not coded (dormant).
Next time (results/paper): the paper must state the sensitivity ordering criterion and must not present the
additive bias transfer (OLS tau00 -126.5 vs AIPW -9.8) as exact. earn75 is not robust for any target, so the paper
must say unobserved selection of that strength could produce the result. rob-diff74 = -1,087 must be reported
prominently and not explained away.

## results-r1 (2026-11-18T14:00Z), verdict: revise
Checked and held:
- The design (plan.json without tasks and gates) is identical at commit 274c4d6 (gate), HEAD and the working copy.
- Every analysis run started after the gate (13:00:13Z), ran once, and ran in plan order.
- validate and --strict are OK.
- I re-executed the primary and RF AIPW in a scratch copy (scratchpad/ws). Both match the ledger exactly: -9.794 and -10.006. Their per-rep thetas differ, so the close agreement is a coincidence, not reused nuisances.
- Mixed nuisances give +11.9 (GBM g with RF m) and -68.9 (RF g with logit m).
- H1 and TOST formulas are correct. O1/O2 pass. The disagreement rule is applied mechanically, including the IPW point test (-191 inside [-358, 338]). The RW stepdown code is correct, with 0 detected.
- The sensitivity reading rule is applied, with earnings75 stated (NOT robust, all targets). tau00 equals the OLS coefficient.
- Every id in design.claim_ids is present. No survey item is read, and there is no recoding.
- NOTES table numbers equal the metrics.
- Raw group means: re78 treated 7,930 vs control 11,393. Naive -3,463, DiD74 -1,291, DiD75 +1,348.
Findings: F1 major (H1b claim lacks the scope from the sensitivity rule and diff74), F2 major (NOTES gives only the pro-primary reading of diff74), F3 minor (unplanned unadjusted secondary CIs; benefits78 [2.5, 171] excludes 0), F4 minor (psi_bar-based relative CI and RW/max-t omit the between-split variance, about 4% narrower; NOTES misstates the direction), F5 minor (figures todo; wellbeing max-t in SD units not claimed).
Suspicions:
- The memory prediction "H1b likely untestable" was wrong: SE 177.6, not ~253. H1b passes, so the danger has moved to overclaiming equivalence.
- Watch the paper: the abstract must not say "smaller than M" without the earnings75 sentence. Watch for diff74 being called "biased downward" or relegated to an appendix. Watch for benefits78 being described as an effect.
Next time (results-r2 or paper):
- Check that primary-h1b-decision is reworded; that a claim with the mandated earnings75 sentence and the earnings74 non-robustness for t_E exists; that diff74 decision claims exist; and that the NOTES diff74 sentence is fixed.
- Check that the sec-*-ci claims are dropped or relabelled; that the F4 caveat is stated; and that the figures exist.
- Literature review still pending: spot-check card2018, lalonde1986 ($886, SE 476), crump2009 ([0.1, 0.9]).

## results-r2 (2026-11-18T14:33Z), verdict: pass
Results-r1: F1-F4 resolved. F5 stays open (minor): the SD-unit max-t claims were added, but f-figures is still todo and
no figures exist. New F6 (minor): no claim or note states the plan-required 'approximation' for the additive bias
transfer. The earnings74 equivalence verdict holds by $22 (203.8 vs 181.5), inside the tau00-vs-AIPW gap of 117.
Code-r1: all four minor findings answered in the files. F1: sens-reading-* lists every group and states the
criterion and the age/educ near-tie. F2: the psi_bar caveat is in the rel-ci claims and NOTES. F3: the IPW clipping is
disclosed in NOTES item 5. F4: primary-h1b-decision cites rule_O1/O2_pass. All four are effectively resolved; I wrote
no code-r2 record.
Checked: commit 77a6b9c changed only claims, log, numbers.tex, NOTES and reviews (no code, run or metric changed); the
decision claim texts match their booleans; validate --strict is OK.
Next time (paper):
- Every statement of H1b, the abstract included, must carry the sens-mandated-sentence content, through macros
  (\SensBenchEarnSeventyFiveBias and similar), not typed numbers.
- The DiD -1,087 must appear in the main text with both readings, not in an appendix.
- benefits78 must never be called an effect.
- The additive approximation must be stated (F6).
- The figures must exist (F5).
- The sensitivity ordering criterion, the IPW clipping and the psi_bar ~4% narrowing must be disclosed.
- The PI's retroactive F4 ruling (design) must be in ai-use.tex.
- Literature spot-checks are still pending: card2018, lalonde1986 ($886, SE 476), crump2009 ([0.1, 0.9]).
