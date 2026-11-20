# Reviewer memory: ss-rd-senate

## question-r1 (2026-11-20, verdict block)

Findings open: F1 (critical, already answered: CCFT 2017 Sec 7.2 and CFT 2015 on the same file); F2 (H1 names an unprinted bias-corrected point estimate); F3 (H1 true by construction; rdrobust release unpinned; tolerance rule missing); F4 (H2 tests unnamed, sample unspecified, no power or equivalence bound); F5 (data not in manifest, no hash or license); F6 (covariate set is four, not the eight in CFT 2015).

Suspicions and checks for later rounds:
- Literature: confirm the CCFT 2017 Section 7.2 numbers (7.416, [4.09441, 10.9255]) and the CFT 2015 p = 0.39 footnote against the full text. Eggers et al. (2015) was checked by abstract only; do not accept any Senate-specific claim from it.
- Literature: check whether any independent replication of the Senate RD exists that the scout missed.
- Design: when the design is proposed, check that the density test, covariates, placebo cutoffs and multiplicity correction are named, and that a non-rejection has a power or equivalence bound.
- Design: check that the tolerance rule and rdrobust release are fixed before any analysis run.
- Data: check the manifest entry (origin, license, sha256) once the data-prep run exists.
- I did not run any model or estimate on the data, and I did not open the seed task or any answer key.

## question-r2 (2026-11-20, verdict revise)

Status of round-1 findings: F1 conceded (question narrowed to a replication, no new finding claimed); F2 resolved (H1 names 7.416 and [4.094, 10.926]; checked against the fetched CCFT 2017 text); F3 resolved (rdrobust==2.1.1 pinned, tolerance 0.01 pp, N exact); F4 open (H2 names the tests, but no equivalence margin or MDE, and N and density statistic unstated); F5 resolved (manifest entry; hash recomputed and matches); F6 resolved (H2(b) uses the four seed covariates and disclaims one-to-one comparison).

New open findings: F7 (major, rdrobust 2.1.1 defaults vs the 2016 release, ties and masspoints); F8 (major, CSV vs .dta fidelity not checked on any printed moment); F9 (major, H2(c) placebo cutoffs not restricted to one side of zero); F10 (minor, covariate-test samples); F11 (minor, H3 names a selector the sources do not contain); F12 (minor, contribution lists the Haiku trial).

Suspicions and checks for later rounds:
- Design: check that H2(c) restricts each placebo to one side of 0, and that the MDE or equivalence bound is stated for every test.
- Code and design: check whether the design states which rdrobust 2.1.1 defaults were used, and whether margin ties were counted (a running-variable count, not an outcome).
- Data: check whether the CSV's margin, class and population moments match CCFT Sec. 7.2 (margin mean 7.171159, sd 34.32488; class mean 2.023022; population mean 3827919). Do not accept a vote statistic before the design gate.
- Data: the 'matches seed' claim rests on a constant in code/fetch_data.py; I did not open the seed, so I did not verify that constant.
- Checks run this round, none on outcome data: sha256 of the raw CSV; printed the header and the first three raw rows to confirm column layout (no statistic computed); read rdrobust 2.1.1 defaults from the installed source; downloaded CCFT 2017 and CFT 2015 full texts to the scratchpad and grepped the printed numbers. I did not run any model or estimate, and I did not open the seed task or any answer key.

## design-r1 (2026-11-20, verdict revise)

Findings open: F1 (major, carried from question-r2 F4: H2(c) equivalence bound is a multiple of vote's SD, not a fixed number); F2 (major, carried from question-r2 F7: masspoints 'off' justified by an unsourced claim that the 2016 release predates the option; 'adjust' changes the selector's N from 1,390 to M = 1,352, so the H1 h check decides the option; bwcheck trigger is 20 percent mass, not reached); F3 (major, no test of selection into the outcome: 93 missing vote; vote_observed RD needs no outcome values); F4 (major, design-mde is data-prep but fits rddensity on margin and four covariate rdrobust models before the gate; PI to accept or rerun as analysis); F5 (minor, codebook overclaims file fidelity, outcome moments unchecked); F6 (minor, no family rule across H2); F7 (minor, placebo windows truncated at 0, bandwidth edge rule not stated).

Carried findings resolved in the design: question-r2 F8 (dr-checks compare printed non-outcome moments; 32 comparisons match), F9 (placebo restricted to one side of 0), F10 (N = 1,108 stated), F11 (H3 uses printed 2014 bandwidths and base h = 17.708, b = 27.984), F12 (contribution no longer lists the trial).

Suspicions and checks for later rounds:
- H1 option: when the results exist, check whether h1-rdrobust was run with masspoints 'off' only, and whether 'adjust' was tried after a failure (that would be tuning). Check the H3(v) row.
- H2(c): check whether the placebo fixes a bound in vote units or still uses the SD; check the bandwidth edge rule.
- H2(d) (if added): check that vote_observed is the only input and that its MDE is fixed.
- Covariate fits: check whether the h2-covariates SEs reproduce design-mde's SEs exactly; if not, the MDEs fixed in design text are wrong.
- Claims: check that rd-cov-*-p are compared with CCFT Sec. 7.4 printed p-values (0.897, 0.561, 0.901, 0.634). The printed block uses plain rdrobust z margin (line ~1190 of the fetched text, no cluster option), so the comparison is like-for-like only if the option matches the 2016 algorithm (see F2).
- I ran no model or estimate on the study data. I read code and run metrics, and read rdrobust/rddensity source and the fetched CCFT text by grep. I did not open the seed task or any answer key. crew.py validate passed.

## design-r2 (2026-11-20, verdict revise)

Status of round-1 findings: F1 conceded (H2(c) report-only in method; hypothesis text not updated, see F8); F2 resolved (assumption labelled, both settings, bwcheck sentence matches rdrobust 2.1.1 lines 609-615 and 721); F3 resolved (H2(d) in method, but missing from hypotheses, see F8); F4 withdrawn on the PI's ruling (disclosure present in plan.json; paper must carry it); F5 resolved (codebook Result narrowed); F6 resolved in method (hypothesis text disagrees, see F8).

Open: F7 (minor, placebo cap is rdrobust bw_max = max distance to sample range, not |c_L| or c_R; response disputed); F8 (major, plan.json hypotheses[2] still says H2(c) Holm over two and non-rejection claims, and omits H2(d)); F9 (minor, massPoints True for density vs 'off' for rdrobust tests, unexplained); F10 (minor, 2016 masspoints history still unverified; CRAN and GitHub NEWS fetch returned 404).

Suspicions and checks for later rounds:
- Run h2-placebo: check that bw_capped uses the software's bw_max on the one-sided sample, and that the metrics record bw_max, h, b, N_h.
- Run h1-rdrobust: check that 'off' was the only setting tried before the report, and that the H3(v) row was not used to choose.
- Paper stage: check that the pre-gate design-mde computations are disclosed in the paper's AI-use statement and text.
- Scout/Data RA: check the 2016 masspoints history if a source becomes available.
- I ran no model or estimate on the study data. I read code, run metrics and installed rdrobust source, and ran crew.py validate (passed). I did not open the seed task or any answer key.

## design-r3 (2026-11-20, verdict pass)

Status of round-2 findings: F1 conceded (report-only H2(c)); F2 resolved (masspoints 'off' labelled an assumption, both settings reported); F3 resolved (H2(d) added); F4 withdrawn (PI ruling, disclosed); F5 resolved; F6 resolved; F7 resolved (checked: rdbwselect.py mserd branch caps h and b at bw_max, computed on the sample passed in); F8 resolved (hypothesis block matches method); F9 resolved (massPoints rationale and p_Q_nomass); F10 conceded (2016 history left as an assumption; paper must disclose).

New in round 3: F11 (c_L and c_R never recorded; task t-design-mde says they are; stale log wording), F12 (H1 'adjust' and bwcheck counts quoted from the full file, not the 1,297-row H1 sample), F13 (H2(b) compares to CCFT default-option p-values but is run only at masspoints 'off').

Open at round 3: F11, F12, F13, all minor. No critical or major open. The kill argument stands: the falsification battery is report-only or underpowered, so it cannot show absence of a discontinuity; H1 is a computational check.

Suspicions and checks for round 4 (the last round):
- Paper stage: the paper must carry the pre-gate disclosure (F4), the unverified 2016 masspoints history (F10), the local-estimand caveat, and the absence of state clustering (CCFT 2017 Sec. 7.4).
- Confirm that numbers in claims.jsonl for H2(c) are report-only and carry no non-rejection wording.
- Check that h2-placebo records c_L, c_R, bw_max, h, b and N_h (F11), and that H2(b) is reported at the setting the comparison supports (F13).
- Check the H1 'adjust' M value on the 1,297-row sample (F12).
- I ran no model or estimate on the study data and did not open the seed task or any answer key.

## code-r1 (2026-11-20, verdict pass)

Findings open, all minor: F1 (the H2(b) printed-value comparator is the 'adjust' reading, per the PI ruling on design-r3 F13, but plan.json still says 2016 = 'off' and names no setting; record the rationale), F2 (literal metrics: design_mde `outcome_loaded` 0 and fetch_data `sha256_matches_seed` 1), F3 (h2_covariates does not compare SEs/MDEs with the design-mde values fixed in the plan), F4 (unit tests do not exercise the H1 tolerance flags; the H1 estimate check accepts any value in (0, 6)), F5 (plan text still quotes full-file counts for the H1 'adjust' M and bwcheck figures).

Status of design-r3 findings in the code: F11 resolved (h2_placebo.py records c_L and c_R at the top level of its metrics); F12 resolved in code (h1_replication.py records the 1,297-row counts), plan text still open as code-r1 F5; F13 answered by the PI ruling, rationale still open as code-r1 F1.

Checks run this round, none on outcome data: sha256 of data/raw/rdrobust_senate.csv matches data/manifest.json and the constant in fetch_data.py; read runs/design-mde/metrics.json (values match the plan's fixed MDEs and density MDE); read rddensity 3.0 source (the `test` robust statistic is computed from the same fit in the useall and non-useall branches, so p_Q_useall equals p_Q by construction); grepped rdrobust 2.1.1 rdbwselect.py for the bw_max cap; reran code/test_analysis.py on synthetic data in the scratch directory (31 of 31 passed). I ran no analysis script on the study data and did not compute any statistic of vote. I did not open the seed task or any answer key.

Suspicions and checks for next round or the results stage:
- H1 run: check that masspoints 'off' is the only reading used for the pass or fail decision, and that a failure is reported and diagnosed, not re-run under 'adjust'.
- H2(c): check that bw_capped and bw_max are reported for each side, and that no result sentence states a non-rejection.
- H2(d): check that the run happens after the gate and that vote_observed is the only input.
- Paper: the printed-value comparison must state its setting (F1); the pre-gate design-mde disclosure must appear in the text; the local-estimand and no-state-clustering caveats must appear.

## code-r2 (2026-11-20, verdict revise)

Status of code-r1 findings: F1 open, raised from minor to major (the printed-value comparator is tied to 'adjust' under a rationale that contradicts the design's own 2016 assumption, 'off'); F2 withdrawn (literal fields disclosed in NOTES, not cited); F3 resolved (SE and MDE checked against design-mde metrics, with match and mismatch tests); F4 resolved (tolerance_flags and estimate tests; 43 of 43 on synthetic data in scratch); F5 withdrawn (disclosure in plan.json; run records use the 1,297-row sample).

New open findings: F6 (minor, NOTES.md says the Reviewer verified the raw hash against the seed task; no reviewer did, and I did not open the seed this round); F7 (minor, the bw_capped flag's positive branch has no test and never fired in 60 random one-sided synthetic samples).

Suspicions and checks for the results stage:
- H1 run: check that the pass or fail is judged on 'off' only, that 'adjust' was not run after a failure, and that the H3 (v) row was not used to choose; check that the h1 M and side counts cited are the 1,297-row ones.
- H2(b): check which reading the paper's comparison uses (F1). If it is 'adjust', the paper must say the comparison is not evidence for 'off' or 'adjust'.
- H2(c): check that the paper reports bw_capped only as recorded, that no non-rejection wording appears, and that c_L and c_R come from h2-placebo metrics (design-r3 F11 resolved).
- H2(d): check that h2-selection ran after the gate and that vote_observed was the only input.
- Paper: the pre-gate design-mde computations (density p = 0.381, covariate SEs) must be disclosed in the text; the local-estimand and no-state-clustering caveats must appear.
- I ran no analysis script on the study data and computed no statistic of vote. I ran code/test_analysis.py on synthetic data in the scratch directory (43 of 43). I did not open the seed task or any answer key. I read the raw CSV only for its sha256.

## code-r3 (2026-11-20, verdict pass)

Status of code-r2 findings: F1 resolved (code records 'off' as primary and 'adjust' as secondary; paper must name the setting in any match statement; plan step 4 still names no setting); F2 withdrawn; F3 resolved; F4 resolved (49 of 49 on synthetic data); F5 withdrawn (bwcheck trigger re-derived from rdrobust.py 609-615: about 0.002 left, 0.053 right, below 0.20); F6 resolved (NOTES corrected); F7 open, minor (the positive cap branch is tested only on forced inputs; NOTES overstates it).

New in round 3: F8 (minor, H3 rows ii and iii use the printed b = 27.984 as baseline; H1 'off' b is not checked); F9 (minor, the static no-vote guard is a substring match on the double-quoted token in three files).

Checks run this round, none on study outcome data: read all code/*.py against plan.json design.method and analysis_plan; read rddensity useall branches, rdbwselect.py mserd cap (final h and b capped at bw_max, so the flag logic is right in principle), rdrobust.py masspoints and bwcheck trigger; confirmed the installed rdrobust 2.1.1 and rddensity 3.0 match code/requirements.txt; reran code/test_analysis.py on synthetic data in the scratch directory (49 of 49); searched for a cap-binding synthetic sample (240 + 40 fits, none capped). crew.py validate passed. I did not run any analysis script on the real data, computed no statistic of vote, and did not open the seed task or any answer key.

Suspicions and checks for the results stage:
- H1: judge the pass or fail on 'off' only; check that 'adjust' was not run after a failure; check the H3 b baseline against off_b_left (F8).
- H2(c): check that bw_capped is reported only as recorded (F7) and that no non-rejection wording appears.
- H2(d): check that h2-selection ran after the gate and used vote_observed as its only input.
- Paper: the pre-gate design-mde disclosure, the local-estimand and no-state-clustering caveats, and the H2(b) setting statement must appear in the text.

## results-r1 (2026-11-20, verdict revise)

Open findings: F1 (major, rd-density-diff labelled 'left minus right' but the value is right minus left; rddensity diff = b[3]-b[2]; hat_right minus hat_left = -0.00355); F2 (major, H2(a) density MDE 0.01136 is in a data-prep run only and in no claim; N and side counts unclaimed); F3 (major, H2(d) robust interval -14.5 to 1.8 pp not claimed and not linked to H1; point estimate about 53 percent of its 11.6 pp MDE); F4 (minor, H2(c) bandwidths, bw_max and CI widths not claimed); F5 (minor, density robust p 0.381 vs conventional 0.099, both to be reported with equal weight); F6 (minor, the 0.0005 printed-match rule is in code, not in the plan; 'adjust' fails for class and termssenate); F7 (minor, bw_capped claims rest on a flag whose positive branch is untested; code-r3 F7 still open).

Checks run this round, none that estimate anything new: crew.py validate (passed); read claims.jsonl, paper/numbers.tex, all run metrics and run records, the analysis scripts, and the rddensity diff construction in the installed source; confirmed the h2-selection run (05:44:42Z) came after the design gate (05:23:23Z); confirmed the claim values equal their runs. Pre-gate design-mde computations are disclosed in plan.json and are not counted as results. I did not run any model or estimate, and I did not open the seed task or any answer key.

Suspicions and checks for round 2 (after the author responds):
- F1: the claim text and paper/numbers.tex must say right minus left; check that the H2(a) sentence in the paper matches the sign.
- F2: check whether an analysis run records the density MDE (or a claim carries it); a value typed in the paper is not acceptable.
- F3: check that the H1 discussion carries the H2(d) interval and does not call H1 selection-free; check whether the interval is claimed.
- F5: check that the paper gives robust and conventional density p-values together.
- F6: check that the paper states the printed-match rule and the two 'adjust' mismatches.
- F7: check that the paper says bw_capped reads 0 and that the positive branch was not observed.
- Paper stage (later): the pre-gate disclosure, the local-estimand caveat and the no-state-clustering caveat must appear in the text.

## results-r2 (2026-11-20, verdict revise)

Status of round-1 findings: F1 resolved (density diff sign right minus left in claim, run and macro); F2 open (density MDE 0.01136 in no analysis run; rebuttal that it is a design constant is wrong under PROTOCOL; cheapest fix is an MDE metric in h2-density); F3 resolved (selection CI claimed; H1 discussion is a paper-stage check); F4 resolved (placebo bw, bw_max and CI width claimed; p-values still unclaimed, see F9); F5 resolved (both density p-values with equal weight); F6 resolved in files (0.0005 rule in plan disclosures; adjust mismatches in NOTES; paper must state them); F7 resolved in claim text (no claim says the cap did not bind).

New open findings: F8 (major, H2(d) claims are on the proportion scale with .3f macros while the text is in pp: \RdSelectionCiLow{-0.145} reads 100 times too small if used in a pp sentence); F9 (minor, placebo p-values recorded but not claimed); F10 (minor, the printed h and b discriminate: 'off' matches both, 'adjust' misses h by 0.046 and b by 0.044; no claim says so; tolerance rule never tests b); F11 (minor, H2(d) claim text omits the sign convention).

Checks run this round, none on new data: crew.py validate (passes); read claims, numbers.tex, all six analysis metrics, NOTES, and code/h2_placebo.py, h2_selection.py, h2_density.py in full or by range; re-derived the MDEs (0.01136, 11.61 pp), the 'off' and 'adjust' printed-match flags, the placebo bw_max values (85.66, 79.56) and the H1 'adjust' deviations from the printed values from the metrics. I ran no model or estimate and computed no statistic of vote. I did not open the seed task or any answer key.

Suspicions and checks for the paper stage or the next round:
- The paper must print the H2(a) MDE through a macro once F2 is fixed, and must state both 'adjust' printed mismatches.
- The paper must print both density p-values in one sentence, with the McCrary p = 0.39 distinction.
- The paper must not use \RdSelection* macros in pp sentences unless F8 is fixed.
- The paper's H1 discussion must carry the H2(d) interval and the local-estimand and no-state-clustering caveats (CCFT 2017 Sec. 7.4 not replicated).
- The 2016 masspoints history is still unverified; the paper must say so.
- t-rerun (crew.py rerun) is still todo; submission needs replication.json newer than every run.
- Watch for any h1 rerun under 'adjust' after a change: that would be tuning.

## results-r3 (2026-11-20, verdict pass)

Status of round-2 findings: F1 resolved (sign); F2 resolved (mde_density is now an analysis-run metric and claim, value 0.01136; earlier h2-density metrics unchanged); F3 resolved in the files (interval claimed; H1 discussion is a paper condition); F4 to F7 resolved; F8 conceded (claim text now says proportion scale; macros unchanged; paper must not put a \RdSelection macro in a pp sentence; pp metrics would be the cleaner fix and may be rerun after the gate); F9, F10, F11 resolved.

New in round 3: F12 (minor, open: no claims for the 'adjust' M counts (595, 665, total 1,260) or for the H2(d) N and placebo N_h; no rerun needed); F13 (minor, open: H1 claim texts omit the local-estimand scope and the conditioning on a Democratic win); F14 (minor, open: NOTES says 95 result claims; there are 113).

Carried from the code target, still open and not results-blocking: code-r3 F7 (the bw_capped positive branch is tested only on forced inputs; NOTES now says so), F8 (H3 b baseline is the printed 27.984; H1 off b is claimed as 27.98412, a 0.0001 difference), F9 (static no-vote guard is a substring match).

Checks run this round, none on new data: crew.py validate (passes); every result claim checked against its run metric (113 claims, zero mismatches); h2_density.py re-run metrics compared key by key with the superseded run; read code/h1, h2_density, h2_covariates, h2_placebo, h2_selection, h3_sensitivity and design_mde; read rddensity useall (test vs test_p, lines 381-396); confirmed rdrobust 2.1.1 and rddensity 3.0 are installed and match requirements.txt. I did not run any analysis script or compute any statistic of vote, and I did not open the seed task or any answer key.

Paper-stage conditions (must appear in the text, not just in the files):
- Pre-gate design-mde computations (density p = 0.381, covariate SEs and MDEs) disclosed as pre-gate.
- Both density p-values in one sentence (robust 0.381 and conventional 0.099), neither read as the McCrary p = 0.39.
- H2(b) match statement names 'off' and reports the two 'adjust' mismatches (class, termssenate).
- H1 discussion carries the H2(d) interval (-14.5 to 1.8 pp, proportion scale converted), and says H1 is not free of selection.
- Local estimand (about 17.7 points, close elections), no state clustering (CCFT 2017 Sec. 7.4 not replicated), and the 'incumbency advantage in all elections' wording removed.
- 2016 masspoints history unverified; 'off' is an assumption that the printed h supports as evidence only.
- bw_capped reported as recorded; positive branch never observed.
- Every number through a macro; no typed results.

Open for the human after round 4 (results target has one round left): F12, F13, F14 (minor), and the paper conditions above. Also outstanding: t-rerun (crew.py rerun) is still todo; the submission gate needs replication.json newer than every run.

## paper-r1 (2026-11-20, verdict revise)

Open findings: F1 (major, Section 6 item 1 and ai-use say the Reviewer kept design-r1 F4 open at design-r2 and design-r3; the records show it withdrawn on the PI's ruling at both rounds); F2 (major, Section 3 'fixed at the design gate' and the abstract's 'fixed in advance' omit that the H2(a) statistic and the H2(b) SEs/MDEs were computed in design-mde before the gate at 05:23Z); F3 (major, 'the choice of primary setting was not made by reference to the printed numbers' is unverifiable and sits against the paper's own use of the printed h as evidence for 'off'; under 'adjust' H1 fails); F4 (major, the H2(d) 'cannot rule out a selection shift large enough to produce the whole H1 effect' compares a share change with a vote-share effect with no bound; the -6.2 pp point estimate is not discussed; Section 6 item 7 says the text converts units explicitly, which it does not); F5 (major, title 'Replicating the Senate Incumbency Advantage' names a broader estimand than the local Democratic-win effect within 17.7 points); F6 (major, replication.json env python 3.14.6 contradicts the 3.12.11 stated in the paper and REPLICATION.md); F7 (minor, the rerun-tool fix was made by the PI session after the 7/15 failure, per log.jsonl 07:08:12Z; the paper does not say who changed the tool); F8 (minor, post-gate edits in commit 48f9767 and results-r3 F12-F14 were never re-reviewed; Section 6 item 10 does not list them); F9 (minor, abstract non-rejection sentence covers the report-only H2(c)); F10 (minor, typed 1,390 and 1,297 in Section 6 item 3 where macros exist).

Checks that held: all 122 result claims equal their run metrics (script over runs/*/metrics.json, zero mismatches); the H1 numbers match the printed values to within the stated tolerance; all analysis runs are after the 05:23Z design gate; the PDF is newer than main.tex and numbers.tex and has no undefined references; the four full-text sources and the Eggers abstract-only record match the claims in sources/notes.md (CCFT p. 392, 393, 397, 398; CFT footnote 13; Caughey and Sekhon's House findings; Eggers et al. abstract); the design-mde SEs and MDEs in the paper match plan.json.

Suspicions and checks for round 2 (after the Writer responds):
- F1: confirm the disclosure states the withdrawal at design-r2 and does not say 'kept open'.
- F2: check that Section 3 and the abstract name the pre-gate computations, not only Section 6.
- F3: check that the 'not made by reference to the printed numbers' sentence is gone or qualified, and that the 'adjust' H1 failure is stated where the pass is reported.
- F4: check for pp values in the text, the -6.2 point estimate, and whether the 'whole H1 effect' sentence survives without a bound.
- F6: check whether replication.json's env field was corrected by the tool, not edited by hand.
- Paper-stage claim count: AI-use says 11 review rounds; with this review it is 12, and the statement must be updated.
- I ran no model or estimate on the study data and did not open the seed task or any answer key. I ran only scripts that read the run metrics and the claims file.

## paper-r2 (2026-11-20, verdict revise)

Status of paper-r1 findings: F2, F3, F4, F5, F7, F8, F9, F10 resolved in the files (checked against the PDF, main.tex, ai-use.tex, numbers.tex, plan.json and the log). F1 open: the ai-use bullet still says the Reviewer 'kept it open at design-r2', although the response says it was fixed; design-r2 F4 is withdrawn. F6 open: Section 6 item 9 and ai-use describe the second rerun and the 3.14.6 env field, but replication.json is now the third run (07:16:07Z, commit 87890ae), with env.crew_python and per-run python 3.12.11. The paper does not mention that third run.

New open findings (all minor): F11 (Section 2 names the wrong two covariates as incomplete; termshouse and termssenate are the ones at N 1,108); F12 (0.053 is 37/702, while 38 observations sit at +100; 0.0001 should read 0.00012); F13 (H2(c) medians use all 1,390 margins, not the 1,297 estimation sample, and the paper does not say so); F14 (the bw_capped caveat reads as if the cap could have bound, but the reported bandwidths are far below the caps); F15 ('default-option output' for the printed p-values sits badly beside the adjust default and the off primary); F16 (ai-use says 11 rounds and 'paper stage not yet reviewed'; with paper-r2 it is 12); F17 (Eggers 'hold' should be 'likely to hold'; the CFT full text came from a third-party mirror, and the provenance is not recorded).

Suspicions and checks for paper-r3 or the human:
- F1 and F6 are the blocking items; check whether ai-use and Section 6 item 9 now describe the third run, commit 87890ae, and the env.crew_python field, and whether the paper recompiles with the current replication.json.
- Check that the H2(c) sample wording (F13) and the cap sentence (F14) are fixed without changing any number.
- Check that the macro-free numbers in the text (0.053, 0.0001, 28.02809) are corrected or macro-based.
- If the paper is revised again, check that no number changed. The claims were 133 lines and the NOTES count is stale; that is not in the paper.
- I ran no model or estimate on the study data and computed no statistic of vote. I read run metrics, code, the log, the git history and the rendered PDF pages. I did not open the seed task or any answer key.

## paper-r3 (2026-11-20, verdict revise)

Status of paper-r2 findings: F1 resolved for the phrase cited ('kept it open' is gone), but the bullet heading now reads 'None', which is new F18; F6 resolved (three runs, commits 2dce826, c1c9549, 0a72b72, 87890ae all exist; replication.json fields match); F11 to F15 and F17 resolved; F12 resolved (text counts repeats beyond the first, 0.053; the response's '0.0527' is not what the paper prints, which is fine at three decimals); F16 resolved as of paper-r2 (13 rounds). After this round the ai-use count must become 14 rounds, with paper 3; the Writer must update it.

New open in round 3: F18 (major, ai-use heading 'None' contradicts the PI's design-r1 F4 ruling and the writer's log at 07:07:10Z); F19 (minor, 'within tolerance' applied to b, which the tolerance rule does not test); F20 (minor, H2(a) called primary and also 'equal weight'); F21 (minor, massPoints=False p-value identical to all 16 digits, reported as 'same to three decimals' with no reason); F22 (minor, the pre-gate design-mde also produced the density-difference MDE 0.01136 and the density difference and SE, and Section 6 item 1 does not name the MDE); F23 (minor, Section 6 item 2 omits the code-stage comparator rulings at 05:31Z and 05:37Z, both before the first analysis run at 05:44Z); F24 (minor, REPLICATION.md says 'the result above is attempt 2' while its table is the third run).

Checks run this round, none on outcome data: crew.py validate (passes); all 122 result claims equal their first supporting run's metric (script over claims.jsonl and runs/*/metrics.json, zero mismatches); Holm values recomputed (all 1.000 is correct for those p-values); pp conversions (-6.2, [-14.5, 1.8], 84 percent) recomputed; run timestamps against the log (all analysis runs after the 05:23:23Z design gate; design-mde before it); commit hashes; margin tie counts on data/derived/senate_rd.csv (margin column only: -100 has 2 rows, +100 has 38; no outcome read). I did not run any model or estimate on the study data, computed no statistic of vote, and did not open the seed task or any answer key.

Suspicions and checks for round 4 (the last round):
- F18: the heading must say one finding was accepted over the Reviewer's objection; check that the bullet and the log agree.
- F21: check whether the writer gives a reason for the identical massPoints p-value, and whether the reason was checked in the rddensity path, not asserted.
- F22: check that the MDE (0.01136) and the density-difference SE are disclosed as pre-gate values.
- F23: check the two comparator rulings and their times in Section 6 item 2.
- Carried from code and design targets, still minor and open: code-r3 F7 (bw_capped positive branch tested only on forced inputs), F8 (H3 b baseline is the printed 27.984), F9 (static no-vote guard is a substring match). Design-r3 F12/F13 resolved by PI ruling or disclosure.
- Round 4 is the last. Open after it, for the human: any of F18 to F24 the Writer does not fix; the paper's core limits stay: H1 pass conditional on 'off', the 2016 masspoints setting unverified, falsification tests report-only or underpowered, no state clustering.
