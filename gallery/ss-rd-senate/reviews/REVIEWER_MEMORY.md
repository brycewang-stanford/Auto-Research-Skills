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
