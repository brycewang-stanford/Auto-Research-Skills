# Reviewer memory: ss-card-krueger

## Round question-r1 (2026-11-18): verdict block

Suspicions:
- The hypotheses are framed to pass. H2 is a sign test whose answer is already published for every
  candidate check (NW 2.78, within-NJ 3.36, Table 5 2.20-2.58). The pre-specification claim in the
  contribution is hollow (F1, critical).
- H1 leaves out the SE and the balanced sample, the only parts not already replicated (Mamula 2.75,
  SE 1.59 vs 1.36) (F2).
- The tolerance for H1 is undefined: 2.75 vs 2.76 invites a post-hoc tolerance or a choice of the
  nearest published cell (F3).
- The public file is the release for *Myth and Measurement* ch. 2, so its vintage may differ from
  the AER data (F4).
- Inference with 2 states: clustering at the treatment level is impossible (F5).

Next round, check:
- plan.json: does H1 name Table 3 row 3 col (iii), include the SE and the balanced estimate, and
  state a numeric tolerance fixed now?
- Does H2 have a criterion that can fail, and is the contribution narrowed to "no within-study
  search", with prior knowledge of the published checks disclosed?
- If the crew claims a robustness check has "no published result", verify that against CK 2000
  Reply / NW 2000 Comment (both only metadata-verified so far).
- At the design stage: SE construction (paired within-state SEs combined as independent vs robust
  regression SE), the closure rule (perm. closed = 0, temp. closed = missing), the FTE formula
  checked against the codebook and the SAS program, and whether the pilot tabulation stayed
  data-prep only.

## Round question-r2 (2026-11-18): verdict revise

Ruled: F1-F5 resolved (contribution narrowed, H1 targets and 0.05 tolerance fixed, vintage stated,
H2 judged on the point estimate). New findings, all open:
- F6 (major): H2's sample, closure handling and comparator are unfixed. Six permanent closures (5 NJ)
  have change = -FTE1. A pooled 5th-percentile cap lifts the NJ mean. Comparator should be the
  unwinsorized estimate on the same sample (row 4), not row 3.
- F7 (major): missed Ropponen 2010 (MPRA 25181, CIC on CK data: effect only for small stores) and
  Ropponen 2011 JAE 26(6):1051-1057; also Morshed 2025 OSF preprint. The "no published result found"
  claim has no logged search.
- F8 (minor): winsorization is not a check "from the later literature" (seed brief) unless it is
  framed as NW 1995's measurement-error critique.
- F9 (minor): H1(a)/(b) targets lie within tolerance of each other; add the within-state change
  targets (row 3 NJ 0.59 vs row 4 NJ 0.47); make the tolerance inclusive; the SE construction is
  still unstated.

Next round / design, check:
- plan.json H2: sample = row 4 balanced? closures in the pool? comparator = same-sample estimate?
- Are Ropponen entries in sources.json with fetched content, and does notes.md say what they found
  about distribution and store size? Does the H2 qualifier disclose it?
- Design: SE construction fixed; clustering deviation recorded; FTE and closure rule checked against
  the SAS program; the pilot stays data-prep only; the percentile computation order is fixed.

## Round question-r3 (2026-11-18): verdict pass

Ruled: F6-F9 resolved (H2 sample/closures/pool/comparator fixed; Ropponen 2010/2011/2014 and
Morshed 2025 recorded, search logged, qualifier narrowed; NW sample rule added as secondary;
within-state targets added, tolerance inclusive). Spot-checked Ropponen 2010 full text: 309+75,
0.90 (0.44), 8 NJ dropped for support, 1.58 with controls all confirmed. New, all minor and open:
- F10: H2 labelled "an implementation of NW 1995's critique", but NW p. 9 say the variability is
  not outlier-driven; 5/95 winsorization tests tails only. Watch for "survives NW" in the paper.
- F11: question says "headline estimate"; H2 comparator is the balanced row 4.
- F12: Ropponen's 2.72 is attributed to the 384-store balanced sample; fn 15 puts the figure that
  carries it on 301+75 = 376 stores. Do not let it serve as a 384-sample replication check.

At design, check:
- SE construction fixed, and the robust store-level regression SE reported beside the
  independent-states combination of paired SEs (the crew knows which one matches 1.36).
- Percentile interpolation rule for H2 fixed; capped-store counts per state and tail reported;
  wave-1 FTE of capped stores reported (Ropponen comparison).
- Clustering / Conley-Taber limitation recorded as a deviation in design.threats.
- FTE formula and closure coding checked against the codebook and SAS program; the 357 filter
  steps logged; the pilot tabulation stays data-prep only.
- NW secondary: "drop closed stores" means permanent closures (temporary are already missing);
  chain + ownership controls specified exactly.
- Whether F10-F12 were fixed or carried forward.

## Round design-r1 (2026-11-19): verdict pass

No critical or major findings; six minor, all open:
- F1: S1 is supported only by the PA arithmetic. On the published entries alone (no study data),
  S1 gives about 0.48 for the row-3 NJ change SE against the published 0.54, if wave variances are
  equal inside and outside the balanced panel. A match must not be called "CK's method". A miss
  should be reported as "SE construction not identified".
- F2: SHEET is not unique (407 = PA KFC ROW_ID 42 and NJ Wendy's ROW_ID 168). The design calls it
  the unique id and uses it in capped.csv and, by implication, as the se-alt cluster variable.
  ROW_ID must be used.
- F3: design.data and analysis_plan 0b describe prepare-data outputs that do not exist (FTE1, DFTE,
  in_* flags, sample_counts.json). The design was written in parallel with prepare-data.
- F4: N = 357 was already observed at data-prep (prepare_metrics checksas_table4_subset_n), so
  H1(c)'s N target is not blind; the design should say so.
- F5: placebo-hiwage has no decision rule ("clearly non-zero"), its answer is published (-2.04 vs
  -2.16), and the stores at $5.00-5.04 are bound. It must not be cited as support for parallel trends.
- F6: the sample behind NW's 2.78 is not recorded. Ask for the within-state changes (+0.66 and
  -2.1) as comparators.
Feasibility arithmetic done (recorded in F1): S1 on published Table 3 SEs only. No study data used.

At code review, check:
- ROW_ID as the key and cluster; DFTE built in analysis code; the closure override is explicit.
- S1 implements the n12 covariance term with denominator n12-1 on A1 and A2 intersected; the balanced
  case equals HC2.
- The T4 filter is C1 verbatim; GAP is not needed. pandas 3 nullable Int64 / NA arithmetic: missing FTE
  must propagate as in SAS.
- Winsorization: numpy.percentile method='linear' on the pooled B including the closures; caps strict
  (< q05, > q95). Ties at the cutoffs are likely, because DFTE values come in multiples of 0.5.
- check-synthetic never reads stores.csv. verdict.py takes its inputs only from metrics.
- Any SE-method switch after main-t3 is a red flag. The design fixes S1.

## Round code-r1 (2026-11-19): verdict pass

Reviewed code hashes (sha256): ck_analysis.py 632d2203..., verdict.py 65599671..., test_ck.py
9d065575... (equal to runs/check-synthetic/run.json). Synthetic data only. The 9 shipped tests pass
on rerun in scratch. My own numpy re-implementation (no ck functions) matched every estimator to
1e-10 on the synthetic file: S1 rows 3-4, the C1 filter from raw components, the conventional OLS
SE and root MSE, pooled 5/95 winsorization (strict caps, per-tail counts, closures counted), the
closures-excluded variant, the NW rule, row 5 and the placebo. On synthetic data all 6 closures land
in the pooled low tail, so the bias toward passing H2 is real; it is a design-level issue that was
already disclosed. Open findings, all minor:
- F1: run_analysis.sh's guard does not check that the code is the reviewed version (no hash binding).
- F2: REPLACE=1 / --replace overwrites run.json and metrics with no archive, so a run can be
  re-done after a miss and leave no trace.
- F3: test_ck.py only checks that the report-only paths run (NW controls, closures-excl capping,
  placebo, row 5); it never checks their values.

At results review, check:
- Do the hashes of ck_analysis.py and verdict.py recorded in each analysis run.json equal the
  hashes above? If not, find what changed and why.
- In log.jsonl, was any analysis run executed more than once (a sign of REPLACE)?
- verdict metrics: every flag must come from the verdict run. If a point target is met and an SE
  target missed, the paper must say "point reproduced; SE construction not identified".
- h2-winsor: capped_low_closed (expect up to 6), and the capped counts by state. Whether H2 passes
  only because closures were lifted: compare against h2-closures-excl.
- se-alt: whichever SE construction matches the published SEs must not become the judged one.

## Round results-r1 (2026-11-19): verdict revise

What I checked, and it held:
- Code hashes in all 8 analysis run.json files equal the code-r1 pins: ck_analysis 632d2203..., verdict 65599671....
  check-synthetic was rerun on test_ck f53561d8... before the runs (10/10). log.jsonl shows each analysis run executed
  once; only check-synthetic is under .superseded. code-r1 F1-F3 are fixed in the files: the guard pins the hashes, there
  is no replace path, and test 10 exists. They are still marked 'open' in code-r1 because there is no code-r2. Rule them
  resolved if a code round is ever reopened.
- My own numpy code (scratch ck-reviewer2/indep.py and cr1.py), run from raw public.dat without ck_analysis, reproduces
  every metric to 1e-12. That covers rows 1-5, T4 (357, 2.3258, 1.1916, RMSE 8.79), the CR1 SEs, H2 (q05 -17.425,
  q95 13.7125, did_w 2.3395, caps 12/8/16/4, one closure capped and it is in PA), closures-excluded 2.3345, the NW rule
  (378 stores, 2.7803) and the placebo (0.129).
- verdict.py applies the 0.05 inclusive rule after round(.,6), the SE-only-miss flags, N as a data check and the H2 rule
  exactly. Claims are labelled report-only and descriptive as the plan requires.

Open:
- F1 (major): the row-3 point gap is not rounding. The published entries force NJ in (0.590, 0.595) and PA in
  (-2.165, -2.160); the replicated 0.5880 and -2.1656 are outside both. Rows 1-2, 4 and 5 and Table 4 match every digit.
  sources/notes.md lines 70-72 still say "only a rounding difference".
- F2 (minor): NOTES says the DiD SE pass "follows from the low NJ SE". The direction is wrong: the low NJ SE pushes it
  toward failing. All three row-3 S1 SEs are low. NOTES cites the placebo's -2.04 match but leaves out its SE (0.98
  against 1.14).
- F3 (minor): the plan.json tasks rv-code and pi-design-gate are still 'todo'.

At results-r2 or the paper, check:
- notes.md and NOTES are corrected. The paper calls row 3 "within the pre-registered tolerance, not at published
  precision; gap not rounding, source unidentified", and never "reproduced" without that qualifier.
- The paper never says S1 reproduces the row-3 SEs, and never cites h1a_did_se_met as the headline SE being reproduced.
- NW rule: matching 2.78/+0.66/-2.06 must not become "same sample as NW" (NW's N is unknown).
- H2 wording: tails only, no "survives NW" (question-r3 F10). The low-tail capped stores are large (mean FTE1 46 vs
  21), so watch that the Ropponen comparison is not overstated.
- Placebo: descriptive only, and never offered as support for parallel trends.

## Round results-r2 (2026-11-19): verdict pass

Checked, and it held:
- The code hashes are unchanged: ck_analysis 632d2203..., verdict 65599671..., test_ck f53561d8.... `validate --strict` is OK. I re-executed all 7
  ck_analysis entry points and verdict.py in scratch (ck-reviewer3/ws) from stores.csv, and every metrics.json and capped.csv is byte-identical.
  The ledger matches NOTES: each analysis run executed once, and the only superseded run is check-synthetic.
- results-r1 F1-F3 are resolved. NOTES, the H1(a) claim texts and sources/notes.md now say "within tolerance, not at published precision, not
  rounding, source unidentified". The SE direction is fixed, the placebo SE 0.98 vs 1.14 is reported and labelled unplanned, and the tasks are done.
- The pre-registered labels are intact: the N=357 data check; H2's secondaries report-only; placebo-hiwage "Not evidence for parallel trends";
  "SE construction not identified" covers the whole row-3 column.

New, both minor and open:
- F4: replicated row 3 == row2 - row1 exactly (same wave samples). "Rows 1-2 match every printed digit, so the gap is specific to row 3" is
  a false contrast. The row-3 gap implies sub-rounding differences in the wave means; the location among the 26 single-wave stores is a conjecture.
- F5: Table 4 dep mean -0.237535 prints as -0.238 vs the published -0.237 (sum -84.80 vs <= -84.7875). NOTES line 233 says it matches.

At the paper stage, check:
- No "rows 1-2 match exactly / gap specific to row 3" contrast. No "Table 4 matches every digit" unless the dependent mean is qualified.
- No placebo SE 0.98 is typed by hand: there is no claim for chg_r3_nj_hi_se, so the Writer needs one or must omit it.
- NW rule: NOTES says "appear to coincide". The paper must not say "same sample as NW".
- The H2 wording covers tails only, with no "survives NW". The Ropponen comparison is not overstated (low-tail capped mean FTE1 46 vs 21).
- The headline is "within the 0.05 tolerance", never a bare "reproduced". The DiD SE is "within tolerance by 0.00003; SE construction not identified".
- code-r1 F1-F3 are still marked open in the code-r1 file, although they are fixed. Rule them resolved if a code round reopens.
