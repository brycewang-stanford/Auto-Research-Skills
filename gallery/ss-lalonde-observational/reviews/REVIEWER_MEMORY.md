# Reviewer memory: ss-lalonde-observational

## question-r1 (2026-11-18T16:39Z), verdict: block

Core suspicion: the "pre-commitment" contribution can't be outcome-blind, because the crew
has read per-estimator results on this exact LDW-CPS sample (notes.md sec. 2-3). H1/H2
outcomes can be read off per estimator before choosing:
- CI includes 0 (H1 fails): regression 1,066 (554); IPW 1,237 (687); DW stratification 1,713 (1,115)
- CI excludes 0: entropy balancing 1,406 (655); AIPW-GRF 1,571 (704); DW matching adj. 1,616 (751)
- Every published CPS-1 CI covers 1,794, so H2 is near-certain.

Asked for: a narrowed contribution (F1); an H2 that can fail, e.g. an equivalence/difference
test with the combined SE (F2); an estimand fixed as ATT on all 185 treated, with the
benchmark named as $1,794 (SE 633) (F3); a placebo H3 with a stated consequence (F4);
a rule that keeps RE78 out of data-prep before the design gate (F5); a broader novelty
search (F6); and corrected verified_on dates (F7).

## Check next time
- plan.json contribution: is the claim "closeness cannot have guided the choice" gone?
- At design: is the estimator justified by an external rule, not by published closeness?
  Does it happen to be the one closest to 1,794 (NN bias-corrected matching)? Is SE method fixed?
- Overlap rule trims controls only? Was the u74/u75 construction fixed in advance?
- Data-prep code in code/: does it read, print or summarise RE78 before the design gate?
  Check run.json outputs and logs for outcome moments.
- The placebo spec must not condition on RE75/u75.
- Before the results gate, no benchmark comparison may appear in the files (task.json brief).

## question-r2 (2026-11-18T16:52Z), verdict: revise

Round 1 F1-F7 are all closed: F1, F3, F4, F5, F6 and F7 resolved, F2 conceded.
New findings, all open:
- F8 (major): "rule from outside this literature" is false. ss-null-effect refs.bib cites
  LaLonde, DW 1999/2002, Smith-Todd and Dehejia 2005. The real protection is timing: the
  ss-null-effect design gate was 13:00Z, this workspace was created 16:28Z. Also, the
  published AIPW-GRF result on LDW-CPS ($1,571, SE 704) was known and is not disclosed.
- F9 (major): "unchanged" cannot hold. Clipping at [0.01, 0.99] binds with 1.1% treated,
  and the covariate bases must be rebuilt. Every adaptation is a literature-aware choice.
- F10 (major): an H3 pass licenses a causal reading, but a pass can come from imprecision,
  and the ss-null-effect design itself says a RE75 placebo is uninformative under a dip.
  H3 was my own r1 remedy, so I said so in the review.
- F11 (minor): no guard on RE75 diagnostics under the placebo conditioning set.

## Check next time
- Are "outside this literature" and "unchanged" gone from plan.json question and contribution?
- Design: are the clipping or trimming rule and covariate bases listed as deviations, with
  reasons that never cite LDW-CPS published estimates? Is the clip count reported?
- H3: is there a precision condition, and is a pass worded as "did not reject"?
- Earlier items still apply: SE method fixed; u74/u75 built as RE = 0; no RE78 in data-prep
  outputs or run logs; no benchmark comparison in the files before the results gate.

## question-r3 (2026-11-18T16:48Z), verdict: revise

F8, F9, F10 and F11 resolved (timing re-checked: ss-null-effect design gate 13:00:13Z, its
design hash unchanged afterwards per its log line 42; this workspace init 16:28:21Z).
New, all open:
- F12 (major): H3 is predicted to fail by the crew's own notes (D4; xu2024tutorial Table B2
  -1,097 to -1,579; imbens2015 Table 20) and claims.jsonl c-imbens-xu-placebo, so H1 is
  expected to end as a "statistical contrast". plan.json does not disclose this; the
  question still asks for "the effect". Remedy: one disclosure sentence + conditional wording.
- F13 (minor): H3 pass rule bounds CI width, not effect size (a pass allows ~+/-$1,800).
  Asked for CI within [-900, 900]; and a rule for H1 when H3 is "inconclusive".
  This corrects my own r2 remedy (b).
- F14 (minor): $1,571 (SE 704) attributed to Imbens-Xu 2025 but comes from xu2024tutorial B1.

## Check next time (round 4 is the last)
- Contribution discloses the expected H3 failure; question's causal wording is conditional.
- H3 pass = CI inside [-900, 900]; inconclusive -> H1 handling stated.
- $1,571 cited to xu2024tutorial.
- Design stage: deviations list for clipping/basis/trimming with reasons free of LDW-CPS
  estimates; clip count; SE method fixed; u74/u75 = 1[RE = 0]; no RE78 in data-prep outputs
  or logs; no placebo-set diagnostics; no benchmark comparison before the results gate.

## question-r4 (2026-11-18T16:49Z), verdict: pass (last round)

F12, F13 and F14 resolved. All of F1-F14 closed. Two new minor findings, open for the human:
- F15 (minor): question says "effect only if the placebo does not reject"; H3 calls a wide,
  non-rejecting CI "inconclusive" -> contrast. Also "under selection on observables" twice.
- F16 (minor): H3 pass (CI within +/-900) and fail (CI excludes zero) can both hold, e.g.
  [-700, -150]. Precedence must be fixed before the design gate.
Kill argument: outcome predictable from the notes (H1 holds, H3 fails -> contrast); value
is procedural only. Disclosed in plan.json, so it is the human's call.

## Check at design
- F15/F16 wording fixed in plan.json before the design gate (hash in log.jsonl).
- Deviations list for clipping/basis/trimming, reasons free of LDW-CPS estimates; clip count.
- SE method fixed; u74/u75 = 1[RE = 0]; overlap rule trims controls only.
- No RE78 in data-prep outputs or run logs; no placebo-set diagnostics; no benchmark
  comparison in the files before the results gate.
- H2 combined SE: plan uses 633 (DW); the tutorial gives 670.82. Check which is used.

## design-r1 (2026-11-19T06:57Z), verdict: block

Question-stage F15/F16 are fixed in plan.json (question wording now says "passes (as defined
in H3)"; H3 fail-takes-precedence rule). Held: RE78 never parsed pre-gate (prepare_data.py
parses fields 1-9 only; derived header has no re78); timing-synthetic fits X- only with a
permuted treatment; trimming drops controls only; u74/u75 = 1[RE = 0] checked in code; SE
method fixed (IF, mean aggregation); H2 uses 633; no benchmark comparison in runs/ (the 1794
grep hits in diag outputs are float digits).
Findings, all open:
- F1 (critical): DEV-9/DEV-11 drop sens-imbens, rob-covsets, rob-estimators, rob-diff74 and the
  matching disagreement triggers. These are exactly the checks the notes say are fragile on
  LDW-CPS: OLS 1,066 (554), IPW 1,237 (687) CIs cover 0; covariate-set fragility per Smith-Todd
  and DW Sec. 5.2. The adopted design said sens-imbens + rob-diff74 are its only assumption
  probes. DEV-9's reason ("hypotheses this question does not have") is false.
- F2 (major): NSW re74 = months 13-24 before RA (largely 1975 for later assignees; smith2005
  Sec. 5). The DW rule admits men assigned after April 1976 only if re74 = 0. This hits the main
  X and the H3 placebo (re75 outcome given re74/u74). Not in the threats; CODEBOOK says "1974".
- F3 (minor): rob-trim drops 8,125 CPS men carrying 0.09% of the m_bar-weight (my arithmetic
  on propensity.csv). The cutoff hinges on one treated man (9,218 / 11,193 at the 2nd / 3rd
  lowest). The disagreement rule rests in practice on rob-learners.
- F4 (minor): pre-diagnostic plan (sha 320cc2..., 01:29Z) never committed; plan edited after
  diag-overlap (05:47Z) -> 20b2f5... at 06:52Z. Rebuild by deleting diagnostics did not
  match, so other text changed too.
- F5 (minor): all four run.json record python 3.14.6, but the .venv is 3.12.11 (tool fix
  047c99f came later). Rerun the data-prep runs.

## Check next round
- F1: restored components with mechanical mappings (rob-covsets (a) "earnings-history core"
  mapping; sens-imbens benchmark groups) and the adopted disagreement rule; or DEV-9 reason
  replaced with the true one plus a "never call H1 robust" rule. Was sens-imbens timed?
- F2: threats + h3_placebo wording + CODEBOOK corrected; H3 spec itself unchanged (a change
  would need the question gate).
- F4: change list 320cc2 -> 20b2f5 logged.
- F5: data-prep runs re-run; diag-overlap metrics identical.
- At code review: placebo_re75.py must not read re78 and must not use re75/u75 in X-;
  no benchmark in any script but h2_benchmark.py; the "unchanged" learner settings match
  ss-null-effect aipw_lib.py@716b6c3.

## design-r2 (2026-11-19T07:19Z), verdict: pass

F1-F5 all resolved. Checked: restored components vs ss-null-effect@716b6c3 (mechanical changes
only; 166 sens points vs 168 adopted is right; t_M/t_E dropped for lack of M); the F4 proof
(reconstructed_320cc2.json hashes to the logged pre-diag hash; key diff vs 95ae728 = diagnostics
+ d-diag status only); question/hypotheses/contribution/constraints byte-identical to the
question-gate commit bcf8e10; run.json envs 3.12.11 with diag metrics/propensity hashes
unchanged; timing_synthetic fits X- only with a permuted treatment, covsets timed with real
treatment but only timings kept; rob-diff74 set (subset of X-) not fitted pre-gate.
New, open:
- F6 (minor): DEV-13's literal mapping makes rob-covsets (a), a disagreement-rule trigger, drop
  black/hisp/nodegree; black has the largest raw imbalance (nd 1.72). The check then measures
  omitted-race bias (foreseeably downward), and the abstract sentence would call it covariate-set
  fragility. Asked for: wording in DEV-13/threats[14]; the abstract sentence names the dropped
  covariates. Mapping unchanged.
Kill argument: outcome predictable from the notes (H1 likely holds, H3 likely fails or cannot
pass; SE_p < 459 needed); value procedural; disclosed and accepted at the question gate.

## Check at code review
- placebo_re75.py: no re78 read; X- excludes re75/u75; propensity re-fitted on B(X-).
- Learner settings and the score match ss-null-effect aipw_lib.py@716b6c3 (sha 86435b8f...).
- rob_covsets.py uses exactly the DEV-13 sets; rob_estimators.py C from LogisticRegressionCV with
  inner seed 20261118, upper clip 0.99 only, bootstrap seed 20261120, 999 draws.
- sens_imbens.py: 8 groups, 128+22+16 points, t_0 from main-aipw, reading rule as fixed.
- Only h2_benchmark.py contains 1794 / 633; join_rule checks fields 1-9.
- F6 wording, if adopted, appears in the claims/abstract logic, not as a changed covariate set.

## code-r1 (2026-11-19T08:36Z), verdict: pass

Held (checked line by line against ss-null-effect@716b6c3 and 9f3133a): AIPW score, per-repetition SE,
mean aggregation + between-repetition variance, HGB settings, the LRCV propensity (now diag_overlap.crossfit,
only warning handling added), folds/seeds; DEV-1..17 coded as written (B 14, B(X-) 11 / T 8, covsets a/b
11/7 and 11/8, diff74 8/6, upper-only clip everywhere incl. Hajek and RF, HC2 OLS 16 regressors, C from
LRCV seed 20261118, bootstrap 999 seed 20261120 unstratified, 8 sens groups partition B(X), 166 points);
join rule (fields 1-9 exact, u74/u75 rebuilt, both-way match, NA -> missing); only main_aipw touches
data/raw; placebo reads only analysis_noRE78.csv; benchmark only in h2_benchmark.py; disagreement rule
(h1 flag for trim/covset-a/linear/rf; IPW by point outside CI). Pre-existing workspace not otherwise changed
(plan.json diff = a-code status only).
My synthetic checks (scratch lalonde-reviewer3/, no study file read): (1) HGB 1/3/8 OpenMP threads ->
bit-identical predictions; 4.8 s vs 96.6 s per fit under load 70-105. (2) every script end to end on a
16,177-row synthetic file with 210 treated (true ATT 1,500): main 1,662 (SE 347); all runs rc 0, 8.5 min
single-threaded; m_bar diff vs diag 0.0; EM all converged. (A first, more extreme synthetic file failed B1
and load_covariates correctly refused to run.) Side observation, design-level and already disclosed:
when selection depends on re75/u75, unconfoundedness given X can hold while the placebo fails hugely
(-4,873, SE 416 on my synthetic data). A placebo failure on the real data says little.
Open (all minor): F1 OMP threads unlimited (fix: env OMP_NUM_THREADS=1, result-neutral); F2 convergence
counts not written (4 scripts) + sens-imbens Logit convergence unchecked; F3 no stop when refit m_bar !=
diag-overlap's; F4 h2-benchmark has no gate guard.

## Check at results review
- Run records: OMP setting in the command; n_convergence_warnings present; main-aipw
  max_abs_diff_mbar_vs_diag_overlap ~0 and rob-trim n_control_dropped == 8,125.
- No code change after this review without unit-tests --replace and a re-review (sha256 in unit-tests run.json).
- h2-benchmark run time after the results gate approval time; no benchmark in claims before it.
- Claims: wording follows the placebo verdict (contrast unless pass); every robustness run reported; the
  covset-a sentence names race/ethnicity/degree if it triggers; sens earn75 sentence present.

## results-r1 (2026-11-19T12:52Z), verdict: revise

Held: claim values = run metrics (validate and --strict OK); code diff 866903c..1d4682e = code-r1 F1-F4 only
(code-r1 F1-F4 fixed in files); unit-tests rerun before main-aipw; each analysis run once, in order, OMP=1 in
command; m_bar diff 5e-13, trim count 8,125; rob-ipow correctly not run (0 unobserved); no benchmark in
claims/numbers/runs; h2-benchmark not run; lalonde-econ scratch has only synthetic copies + logs matching ledger.
Wording follows H3 FAIL (-1,543 [-2,699, -387]) and the disagreement rule (trim, covset-a, linear trigger).
Open:
- F1 (major): H1 lower bound 9.6; per-rep lower bounds +55, +57, -20, -26, -3 (3/5 include 0); between-rep SD 52,
  MC SD of bound ~23. threats[9] promised per-rep estimates; no claim has them. Rel CI [-5.1, 71.0] includes 0.
  Remedy: theta_rep/se_rep claims + sentence in h1-decision. No change of aggregation (median would give 48;
  do NOT let anyone switch).
- F2 (major): sens R2_D floor. My covariate-only check (lalonde-reviewer4/vcheck.py): V 13.0 (controls 12.3,
  treated 4.2); V-V_-G black -1.45, nodegree -0.83, married -0.04; but dLL black 179.3 (McFadden 0.30) vs age 51,
  earn74 22, married 20, earn75 19, educ 13, hisp 7, nodegree 3. "Strongest robust group is black" inverts.
- F3 (minor): disagree-trim needs the design's meaning (0.09% weight; trim reps 1,265-1,624); placebo claim needs
  the CPS re75 top-code (3,007) sentence.
- F4 (minor): no re-review after code-r1 fixes (PI brief skipped it); diff checked here; disclose as deviation.
- F5 (minor): plan.json tasks stale.

## Check next round / at paper
- h1-decision text has the 3-of-5 sentence; theta_rep/se_rep claims exist; paper never says "significant" bare.
- sens-reading no longer reads "robust to race"; any V/V_-G number comes from a logged, labelled diagnostic run.
- Aggregation, seeds, rules unchanged (no new main-aipw run; runs/.superseded holds only unit-tests).
- h2-benchmark run time after results gate approval; no estimator chosen or ranked by closeness to 1,794.
- Paper: deviations list includes F4; abstract carries the three non-robust statements + earn75 sentence.

## results-r2 (2026-11-19T12:58Z), verdict: pass

results-r1 F1-F5 all resolved. Checked: rep lower bounds recomputed (+55.2, +56.5, -20.1, -26.0, -2.6); no code change
after 1d4682e, no run after 12:41Z, .superseded = unit-tests only; h2-benchmark not run; trim between-rep SD 138 vs main
52 (trim SE w/o between term ~801 vs 813), so the "noise" reading in disagree-trim holds; placebo reps each exclude 0
(H3 fail seed-stable); sens benchmark_r2 would give R2_D > 1 if V - V_-G < -pi^2/3, but none > 1, so zeros = x in [-3.29, 0].
code-r1/review.json F1-F4 still say "open" although fixed. Only a code-r2 round could close them; the PI decides.
New, open (both minor):
- F6: claim texts have numbers no macro/metric holds: "$9.6" (\PrimaryCiLow, \SensTargetZero print "10"), "+55"/"three of
  five" (no rep-bound metric; rep1 is +56.5), "0.09% (0.169 of 188.9)", and sens-reading's "CPS men far outside the treated
  range" clause (my own r1 scratch, not logged; I corrected my own remedy). Fix: ',.1f' format; logged derived run or words only.
- F7: runs/NOTES.md table row 8 still says "robust only to black, married, nodegree" unqualified; Surprises mechanism differs.

## Check at paper
- Abstract: the three fixed non-robust sentences (trim; race, ethnicity and degree; parametric) + earn75 sentence; "contrast" not "effect".
- "significant" never without the cross-fitting-noise sentence; lower bound shown with a .1f macro, not "$10" as if a clean margin.
- No hand-typed 55/57/-20/-26/-3, 0.09%, V, V_-G unless from a logged run.
- No "robust to race/married/degree"; deviations list has the code re-review skip (results-r1 F4) + AI-use statement.
- h2-benchmark run time after the results gate approval; H2 descriptive only, combined SE 633, no ranking by closeness.
