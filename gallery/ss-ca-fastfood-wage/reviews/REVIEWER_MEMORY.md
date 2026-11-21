# Reviewer memory: ss-ca-fastfood-wage

## question-r1 (2026-11-21, verdict block)

Suspicions:
- H4 is the weak point. w35931 already runs a 1,440-specification grid on one QCEW vintage (Aug 2026 release) that brackets both published targets. A "range contains both targets" criterion is tautological. The only choices nobody has varied are the base period / anticipation handling (w35931 fn 5 says it is not varied) and the DDD comparison sector.
- H2 novelty is one preliminary quarter (2026Q1) beyond w35931's post-period average through 2025Q4. QCEW 2026Q2 is released 2026-12-02; watch whether the PI waits for it or still claims "first" after that date.
- The PI and Scout know which choices move estimates (Dube D1, w35931 A1). Any "pre-registered" grid or primary spec is chosen with that knowledge. Check that the design-stage primary spec is not tilted toward one camp without stated reasons.

Asked for: H4 narrowed to untested choices with a falsifiable quantity (or dropped); honest contribution wording; H2 decision categories made exclusive; the coverage-share attribution fixed (70% is for 722513+722515 combined); H3 relabelled as a reduced-form contrast with an MDE rule; inference resolution checked against the donor pool.

Check next round:
- Run `crew.py changes`; re-read plan.json H2-H4 and contribution in full.
- Confirm c-coverage-share is reworded in claims.jsonl.
- At the design stage: base period, donor pool, DDD sector, detrending and the inference method are fixed before any post-2023Q3 outcome is computed; there are no runs of kind analysis before the design gate; the MDE comes from pre-period placebo data only.
- Verified myself: w35931 pp. 6-7 (data end 2025Q4, fn 3 vintage, fn 5 base period not varied, percentiles of CEMN and Dube); Sosinskiy-Reich 70% quote. Copies are in my scratch folder rv-q1.

## question-r2 (2026-11-21, verdict block)

F1-F6 resolved. New: F7 critical, F8 major, F9 and F10 minor.

Correction to my own round 1: I proposed the base period as "the choice nobody varies" from the first sentence of w35931 fn 5 and notes.md section 3. That was wrong. fn 5 ends by saying a 2023Q3 base is "not meaningfully changed". Dube Table 1 Panel B (base 2022Q1-2023Q3, "invariant to anticipation ... in 2023Q4") moves SDID from -0.26 to -0.02. SR Table A3 (p. 48) gives the 2023Q4 and 2024Q1 effects on a Sept 2023 reference (-0.002, -0.006). CEMN rev. fn 9 / Table A3 re-estimate on a 2023Q4 base. The PI took my remedy, so a false novelty claim now carries the question. Lesson: verify the literature myself before suggesting a remedy.

Suspicions:
- With H4 pre-empted, the question's only remaining new element is H2 (one preliminary quarter plus a pre-specified test). Watch for a new "first" or "no study" claim taking H4's place without a check.
- The base period for H2 and H3 is still unfixed (F10). This is the choice with the most room to search, and the PI has seen its effect in the published numbers.

Check next round:
- `crew.py changes`; grep plan.json for "no published", "no study", "first", "the one".
- If H4 survives: it uses the 2023Q4 effect alone for Dube's base, gives its own bound with a rationale and an MDE rule, and concludes as a share of the gap.
- The H2 table has the (sign undetermined, at least b) cell.
- No analysis runs yet (only fetch-data and prepare-data, both data-prep, as of r2).
- My PDFs are in scratch rv-q2/dl (w35171, w34033 rev.; hashes match the Scout's copies) and rv-q1 (w35931, SR).

## question-r3 (2026-11-21, verdict revise)

F7, F9 and F10 resolved; F8 conceded (H4 deleted). New: F11 major, F12, F13 and F14 minor. No critical finding is open.

Re-verified: SR Table A3 is on PDF p. 49, not p. 48 as I wrote in r2 (the Scout's correction is right); the 2023Q4/2024Q1 numbers and the "almost 60 percent" passage are correct; w35931 fn 5 verbatim; CEMN rev. fn 9 and Table A3 Panel B are correct. w35931 p. 12: the detrending medians -2.83 / -5.67 / -4.98.

Suspicions:
- F11 is the real risk now: the label H2 gets is close to determined by the estimator and detrending choice, and the PI knows the published map. At the design gate, check that the selection rule uses only pre-2023Q3 data, is stated before the choice is made, and does not cite which camp it matches; that both camps' specifications are named secondaries; and that "pre-registered" is either backed or narrowed.
- The 2023Q3 base may itself contain anticipation (SR p. 42: as early as July-August 2023). This should appear among the design threats.

Check next round (r4 is the last):
- `crew.py changes`; read plan.json H2 and the contribution in full; check that the F12 label split is symmetric for the positive cases.
- F13: Dube Panel B no longer credited with reporting 2023Q4/2024Q1 separately.
- F14: notes.md sections 0.3, 3 (end), 6.1 and 7 marked as superseded or reworded.
- Still only data-prep runs (fetch-data and prepare-data).

## question-r4 (2026-11-21, verdict pass; last question round)

F11-F14 resolved. New: F15 and F16, both minor and open; they go to the design stage and the human.

Checked: the placebo exercises in w34033 rev. (Tables 2, 4), w35171 and w35931 are placebo-in-space over states; none reports placebo-in-time fit, so the selection rule's winner is not already in print. Notes grep for H4/grid finds only superseded or literature passages. Still only data-prep runs (fetch-data, prepare-data). validate passes.

Suspicions for the design review:
- F15: the room to search now sits in the rule's pseudo-dates, windows (COVID inside every eight-quarter pseudo-window from about 2018Q3 to 2021Q3), tie-break and pools. Check they are fixed in plan.json before any placebo is computed, and that the selection is one logged analysis run on an input truncated at one stated cutoff (the plan says pre-2023Q3 for the rule and pre-2023Q4 for the MDE), before any post-period run. Look in runs/.superseded and log.jsonl for repeated selection runs.
- F16: which outcome the RMSE uses, and whether H1 inherits the employment-selected estimator.
- 2023Q3 base may contain anticipation (SR p. 42, July-August 2023); it should be in design.threats.
- The H2 bound uses Dube's pooled ~7% wage effect from a window ending 2025Q3 as "the same pooled post-period estimand"; it is close but not the same window. Check the paper does not overstate this.

## literature-r1 (2026-11-21, verdict revise)

New: L1-L4 major, L5-L7 minor. No critical finding. After recording I fixed one typo in L1's text (review.json only; no stamped file changed).

Verified myself (PDFs in scratch rv-lit1/dl; every sha256 prefix matches sources.json): c-cem2025, c-cemn2026, c-dube2026, c-dube-decomp, c-sr2026, c-synth2026, c-melo2026, c-hamdi2025, the DIR claims, the BLS release (USDL-26-1424) and QCEW HOM/Q&A. All numbers correct. BLS pages block curl; WebFetch works.

Suspicions:
- L1: AB 257 (Sept 2022, up to $22, stayed Jan 2023) puts 2022Q3-2023Q3 under a pending sectoral wage law. The selection rule, the MDE and Dube Panel B's base all use those quarters. At the design review, check the threats list and whether the pseudo-dates avoid that window or report the rule both ways.
- L2: Melo et al. find QCEW misclassification (LA: 7.9% of chain locations in 722511, 9.2% in 722515) and covered-chain employment 33% below QCEW 722513 in CA in 2025 (p. 19). Watch for a 722511 DDD treated as clean and for "share not known" left standing.
- L4: Recording Law data page (6 Nov 2026) publishes a raw CA-vs-US 722513 index through March 2026. The post-period for the one new quarter is public; the not-blind disclosure should say so.
- L3: no methods sources yet; Ferman-Pinto-Possebom (2020, cherry picking) bears directly on the RMSE selection rule.

Check next round:
- `crew.py changes <ws> literature`; new claims for AB 257, Melo misclassification/coverage, methods sources; c-no-2026-qcew reworded to "no causal estimate"; c-ab1228-no-increase reworded; H2 bound wording (L5).
- Spot-check every new sources.json entry against the fetched document (methods papers: title, journal, year).
- Still only data-prep runs (fetch-data, prepare-data) as of literature-r1.

## design-r1 (2026-11-21, verdict block)

New: D1 critical; D2, D3, D4 major; D5, D6, D7 minor. question-r4 F15(a)(c) and F16 are settled in the design; F15(b) remains only as wording (D7). literature-r1 L1 (T4, rob-pre-ab257) and L2 (T9, plc-722511) are folded in.

Verified myself: Ferman-Pinto MPRA 81988 (sha256 8d2afec9..., same as sources.json; copy in scratch rv-d1/dl): var = A + B/M (p. 9), A > 0 dominates as M grows (p. 10), A and B estimated by regressing squared residuals on 1/M (pp. 12-13). Dube w35171 p. 8 scales by sqrt(pop_j/pop_CA), which imposes A = 0. Arkhangelsky Table 1 Prop 99: -15.6 / -19.6 / -27.3 (w25532 text). Runs as of design-r1: fetch-data, prepare-data, fetch-pop, fetch-prop99, prepare-state, all data-prep; no analysis run, no runs/.superseded. The Designer's scratch holds only a Census population xlsx and a text-writing script, with no outcome computation.

Suspicions:
- D1 is the crux. The H2 label is a CI label, and California is the largest unit, so 1/pop scaling shrinks its SE. Illustration (pure state shocks): SE about 0.4 of the truth, a nominal 5% test rejecting about 40%. The pooled level check averages small units that under-reject with large ones that over-reject. Watch for a fix that only adds the k diagnostic or more wording.
- D3: California's general minimum wage ramp 2016-2019 sits inside every pseudo-window, and many R50 states raised minimum wages then too. An R50 or DDT winner may reflect this.
- D4: S1 and S2 are outside the verdict's not-robust rule; the headline can hinge on a nearly uninformative selection.

Check next round:
- `crew.py changes <ws> design`; read plan.json design.method INFERENCE, LEVEL CHECK, MDE and the verdict step in full.
- D1: an A + B/pop fit, or a conservative max(scaled, unscaled) SE, and a level decision based on large units, all fixed before level-mde runs; an A > 0 design in the Monte Carlo (check-methods iv).
- D2: the threshold tied to nominal, or calibrated/conservative always.
- D3: a threat entry; level-check treated units restricted to states with no minimum-wage change in 2014-2019, or rates reported for them.
- Still no analysis runs before the gate; select reads only state_panel_pre.csv.

## literature-r2 (2026-11-21, verdict pass)

L1-L4, L6, L7 resolved. L5 still open (minor). New, all minor and open: L8 (stale notes.md 1.4 and 3), L9 (bound cites the superseded one-year Clemens range; the revised two-year range starts at -2.02, on the bound), L10 (disclosure omits Steier's public 2026Q1 weekly-pay index 114.8 vs 104.3, H1's outcome), L11 (Melo's argument that QCEW 722513 tracks covered employment poorly across donor states, -8 to +17 points, missing from the limits and T9-T10).

Correction to my own round 1: my L5 remedy ('the least negative of Clemens et al.'s estimates') was imprecise. The PI wrote 'the least negative of the elasticities Clemens et al. report', which is false: w34033 rev. p. 12 gives -0.17 (QWI, one year). Lesson again: check the remedy's wording against the full source before proposing it.

Verified myself (scratch rv-lit2/dl; every sha256 prefix matches sources.json): FPP 14.3% (PDF p. 17), ADH 1/39 = 0.026 and in-time placebos, Abadie 2021 pages 406/409/410/414, Ballotpedia AB 257 dates, Steier values and datePublished, DIR $20.00 page, EPI quote, Wiltshire, NRL, Thornberg, Card-Krueger, RS 2024. Crossref for 11 DOIs matches refs.bib. Web search: no causal 2026Q1 study.

Check next time (paper stage):
- The related-work and H2 text use the revised Clemens et al. range and the corrected elasticity wording (L5, L9); 'separates the two readings' narrowed to the medians.
- Disclosure covers the wage index (L10); limits carry Melo's measurement objection (L11).
- Still only data-prep runs as of literature-r2 (fetch-data replaced once; .superseded/fetch-data-20261121T044556Z).

## design-r2 (2026-11-21, verdict pass)

D1-D7 resolved. New, all minor and open: D8 (California in every L unit's donor and placebo sets, so L carries its MW ramp and is weak at detecting size-related over-rejection; it can only widen intervals), D9 (H1 still says level-mde 'shows ... attain the stated level'; the design says California's level is argued, not measured), D10 (rob-pre-ab257 '9 quarters' lists 10; S1's 2021Q3 trend endpoint contradicts 'COVID never used in any trend'; I missed both in r1), D11 (check (ii) on 2022Q1-2023Q3 is in-sample for DDT/SC/SDID), D12 (Monte Carlo has homogeneous sigma_A; heterogeneous donor variances cut the effective df below J).

Verified myself: the max-SE expectation algebra; numpy quantile indices for 60 values; the DOL WHD history table (Internet Archive copy, sha256 6e8c87edc35ab245 matches sources.json; copy in scratch rv-d2/dl): all 20 D20 states constant 2014-2024, WV changes 2015, VA constant to 2020, NV unchanged 2014-2019. Local MWs (Iowa counties, Louisville and Lexington) not in the table; IA and KY are not in L. Runs: still only data-prep (fetch-data, prepare-data, fetch-pop, fetch-prop99, prepare-state); one superseded fetch-data (04:45Z), and its replacement has identical data hashes (197 of 198 outputs match; the 198th is the metrics file).

Check next time (code review):
- level_mde.py: whether D8 was taken (California excluded from L units' donors) and how T is computed for L (SE = max); quantile methods 'higher' and 'lower'.
- select.py and level_mde.py refuse any quarter after 2019Q4; check-methods (iv) pass condition fixed in the script before it runs; scaled-only rates reported.
- rob-pre-ab257 trend points match whatever D10 fixes; sec-cemn's 2021Q3 endpoint.
- The elasticity denominator reuses the employment fit (D5); verdict.py's 'not robust' uses sign category only (paper review: watch size-label differences).
- Paper stage: the event-path figure is not called a pre-trend test for a DDT, SC or SDID winner (D11); H1 wording (D9).

## design-r3 (2026-11-21, verdict pass)

D8-D12 resolved. New: D13 minor, open. hetero-A is under the Monte Carlo pass condition although the plan predicts t_J over-rejects there. In my synthetic illustration (scratch rv-d3/mc.py, approximate populations, no study data) the two-sided rate is 0.054-0.057 against a bound of 0.0646 at R = 2,000, so pass or fail is close to chance, and the plan does not say what a fail leads to. hetero-A-CA2 in the same illustration: two-sided about 0.15, one-sided about 0.12.

Checked: the stamped plan (git f907556~1, sha 96505a63...) against the current one, field by field. No stale 'plus California' or 'stays J' text. rob-pre-ab257 now lists 9 trend points. Pseudo-dates 2016Q1-2017Q2, so B'-8 is 2014Q1-2015Q2 (no COVID quarter). Satterthwaite df 12.9. Runs: still the same five data-prep runs, none of kind analysis; validate passes. The Econometrician was briefed in parallel for e-code and e-check; code/ has only the five data-prep scripts so far.

Check next time (code review):
- check-methods output: hetero-A rates next to pure-A; whether any fail was answered by a change chosen after the fact (D13); hetero-A-CA2 rates recorded for T6.
- level_mde.py: L units use pool minus u (J-1) with California out of donors and placebos; t_{J-1} for their rates; c_hi floor t_J; SE_n divisor equals the size of u's own donor set.
- rob-pre-ab257 DDT trend points are 2018Q2-2019Q4 plus 2022Q1-2022Q2; sec-cemn alone touches 2021Q3.
- Paper: event-path figure note per D11; H1 wording per D9; hetero-A-CA2 size reported in the limits.

## design-r4 (2026-11-21, verdict pass; last design round)

D13 resolved (every label at t_nu, nu = min(J, nu_hat); every outcome of check-methods (iv) fixed before it runs). New, both minor and open, for the human: D14 (the df penalty also applies when donor variances differ because of size, where SE_n is already conservative for California, so the intervals widen twice; in my synthetic illustration rv-d4/nu.py, pure B with D20 gives true df 9.1, nu_hat median 6.6, 5th percentile 3.2, MDE factor 1.12 at the median and 1.37 at the 5th percentile; remedy: wording plus a t_J MDE/h90 shown next to it), and D15 (hetero-A-CA2 rate for T6 not tied to t_{nu_MC}).

Checked: plan diff against the design-r3 stamp (git 01c0fa3, sha 18eb7860...) field by field; 1 - F_13(t_20,0.95) = 0.0541 and 2(1 - F_13(t_20,0.975)) = 0.0573; grep shows no t_J left in a label rule. Runs: the same five data-prep runs, none of kind analysis; validate passes. code/sclib.py now exists (Econometrician, 801 lines, mtime 06:51Z) with a fresh __pycache__ (06:51:20Z): an import, not a logged run. Not read in full; it is for the code review.

Check next time (code review):
- sclib.py satterthwaite_df / nu_from_s2 / nu_for_donors: s_j^2 = mean over the six B' of tau_j(B')^2 from California's level-check placebos; rob-7225 over its own donors; t from scipy at non-integer df.
- check-methods: hetero-A judged against r at nu_MC; hetero-A-CA2 rates at t_{nu_MC} as well as t_J (D15); no change chosen after the Monte Carlo is seen.
- Whether D14 got the wording and the t_J MDE/h90 comparison before level-mde runs; if the PI adds a floor on nu, it must be logged before level-mde.
- That nothing ran sclib.py on data/derived before the gate (the __pycache__ is from an import).

## code-r1 (2026-11-21, verdict pass)

New, all minor and open: C1 (h1-wage's yearly one-sided tests use the pooled h1 critical values and nu, undisclosed; they gate owe_y1/owe_y2), C2 (requirements.txt wrapt 2.5.2 vs approved design text 2.6.0.dev1), C3 (fig_event/fig_placebo captions omit the SDID floor if SDID is selected; stale select.py prologue comments). D14 and D15 are in the code (level-mde mde_h2_tJ/h90_h2_tJ; hetero-A-CA2 at t_nu echoed as cm_).

Read all 24 files in code/ (hashes stamped by crew.py review), plan.json design, runs/NOTES.md, runs/check-methods/run.json (its code hashes equal the current files). No study data read or run. Synthetic-only checks in scratch rv-c1 (tools/build.py, recover.py, infer_check.py, misc_check.py, pipeline.sh): every run script and the three figure scripts execute end to end for a DDT-POPW-P-D20 and an SDID-E-D20 primary (level-mde about 190 s for SDID); all 24 candidates recover a noise-free -0.03 exactly; run path = mc_dd/mc_T to 0 for DD/DDT; label probabilities = simulation; SA full vs pre identical; rob-7225 drops NH and WY (J = 18) and uses nu over its own donors. Pitfall I hit: test_sclib.synthetic_panel_df treats unit 0 as treated, so California must be first.

Suspicions / check next time (results stage):
- runs/select run once: one record, no runs/.superseded/select-*; select names code/test_sclib.py with --code (select_rule imports it); input state_panel_pre.csv only.
- level-mde ran before any run reading post-2023Q3 data (compare started times in run.json); every post run's --input includes runs/select and runs/level-mde metrics.
- Whether C1 was disclosed before h1-wage ran; whether yearly elasticities are reported as gated by the pooled critical values.
- sc_solver_gap only covers California's six pseudo-ATTs; if SC wins with R50, ask for the real-window solver gap too (non-unique weights, T16).
- Paper: S1/S2 labels next to the primary; 'not robust to' and the plc-nonff qualifier exactly as verdict wrote them; figure captions vs SDID floor (C3).

## code-r2 (2026-11-21, verdict revise)

C1, C2 (D5, D6 in design.deviations; D5 logged 11:53:27Z, before h1-wage at 11:55:50Z) and C3 (figlib.sdid_floor; formula matches sclib.critical_values; synthetic SDID input checked; stale prologues gone) resolved. New: C4 major, C5 minor, both open.

C4: fig_event panel (b) (wage) uses H2's critical values (c_hi(0.975) 2.14) per analysis_plan 16, but the wage test H1 uses c_hi(0.95) 3.45 / c_hi(0.975) 4.32 from L (Lq_h1). On the real event_path.csv the wage band excludes zero in 6 of 8 post quarters under H2's c and in none under H1's; the caption does not say so. I missed this at design time, when the wage L quantile was not yet known. C5: the caption's 'Generated from' line omits runs/level-mde/metrics.json.

Ran (scratch rv-c2, outputs only there): fig_event, fig_placebo, fig_select on the real run outputs; all exit 0, every internal check passes. No estimate run. crew.py validate passes (2 paper warnings: a typed 0.0240 in literature.tex, main.pdf older than numbers.tex). Post-period runs all name code_review code-r1; select and level-mde ran once, before any post run; no runs/.superseded for select.

Check next round:
- `crew.py changes <ws> code`; fig_event.py caption gives H1's critical values for panel (b), or panel (b) is redrawn with them and a deviation is logged before fig-event runs; runs/h1-wage/metrics.json is declared as an input if read.
- C5: provenance line lists every input.
- Paper/results stage: the text does not read panel (b) as evidence of a wage effect beyond H1's label; S2's reused-weights wage effect (+0.075, excludes 0 under S2's c) is not presented as overturning H1; the typed 0.0240 in literature.tex becomes \SelBestDDRmse.

## code-r3 (2026-11-21, verdict pass)

C4 and C5 resolved (first remedy; bands not redrawn, analysis_plan 16 unchanged). No new finding; C1-C5 all resolved.

Checked: fig_event.py reads runs/h1-wage/metrics.json (selected, nu 14.41, h1_c_hi95 3.45, h1_c_hi975 4.32) and refuses a mismatched candidate; the comparison branch is computed. Ran fig_event and fig_placebo on the real run outputs into scratch rv-c3 only (no estimate); captions print the run values; Generated-from lines list every argparse input. Post-window wage gap/SE: 6 of 8 above 2.14, one (2024Q3, 3.71) above 3.45, none above 4.32. For SDID, H1 carries the same pool floor (sclib.crit_for), so FLOOR['phrase'] fits H1. validate passes (3 paper warnings: process.tex stale, typed 0.0240 in literature.tex, main.pdf older). No runs/fig-* yet.

Check next time (results/paper):
- fig-event, fig-placebo, fig-select runs name code-r3 and --input every file in CAPTIONS.md (fig-event includes runs/h1-wage/metrics.json); captions used unchanged.
- The paper does not read panel (b) as a wage effect; the strongest remaining objection is that the picture still shows bands at H2's 2.14, so a referee may ask for H1's values.
- The caption's comparison sets per-quarter gap/SE against the pooled-test threshold; the text should not repeat it as a per-quarter test.
- Still open from code-r2: S2's reused-weights wage effect not presented as overturning H1; \SelBestDDRmse for the typed 0.0240.

## results-r1 (2026-11-21, verdict revise)

New: R1-R3 major; R4-R8 minor. No critical finding. code-r1 process items checked: select ran once (no runs/.superseded/select-*), on state_panel_pre.csv only, with test_sclib.py in --code. level-mde (11:54:05Z) preceded every post run (11:55:50Z onward). Every post run read select and level-mde metrics and ran once. D5 was recorded (11:53:27Z) before h1-wage. Validate passes with 2 warnings. One of them is literature.tex:44, where 0.0240 is Melo's SE, written before select ran: a coincidence that needs `% crew:literal`.

What I did (report-only, from run outputs and data/derived; no new estimator runs): read tests.csv by unit; computed the L quantiles without GA; took yoy aww deviations from the cross-state median; fitted OLS slopes of the event-path 2014-2019 segment. Script in scratch rv-r1/write_review.py.

Suspicions:
- R1 is the big one. Georgia's 722513 aww drops about 15 log points in 2014→2015 (yoy deviation -0.15 to -0.17; the next largest in the panel is FL at -0.078). It produces all four top L wage t-values (2016Q1-Q4), so it alone sets crit_h1 at 3.45/4.32. Watch for two opposite errors: (a) the paper reading 'H1 not supported' as 'no first stage'; (b) someone dropping GA or changing the rule after seeing this. The verdict must stay as pre-specified; only disclosure and a report-only check are legitimate.
- In other statistics, one state drives the L tails too (TN for S1/op/H3 lower, IN for S2 lower). No label changes there. "20 effective draws in L" is really about ten states with correlated windows.
- S2's California pseudo-ATTs average +0.029 (k 1.86, 4/6 upper rejections). Do not let S2's narrow interval or its wage interval [0.035, 0.116] be used as independent support.
- The design's own named DDT out-of-fit evidence (the 2014-2019 event-path segment) drifts: emp slope 0.0023/q, wage 0.0085/q. Only the in-fit RMS is claimed.
- Brief inconsistency: the archived brief (20261121T120101Z-reviewer.md) says the parallel Reviewer reviews 'results'; the PI's message says code. code-r2's brief was archived at the same second. Check which target that review has.

Check next round:
- `crew.py changes <ws> results`. Look for new text claims for R1 (GA sets crit_h1; h1_p_upper_tnu next to the verdict), R3 (2014-2019 segment), R5 (sign) and R6 (ca_h1_* claimed).
- Any new metric (event_path.py, level_mde.py) needs a passing code review that read the changed script before it runs. Check run.json code_review and that no post run was --replace'd to change a label.
- plan.json contribution no longer says the bound 'separates the two published readings' (R2).
- f-figs is still todo. The figure scripts changed after code-r1 (C3, 11:56Z), so fig runs need code-r2.
- Paper stage: the abstract shows S1/S2 labels with the R4 caveat; no 'no first stage' wording; no 'robust' wording (all checks inconclusive, n_not_robust 0 because every sign category is 'undetermined', not because estimates agree).

## code-r4 (2026-11-21, verdict pass; last code round)

Target: code/posthoc.py (D7, post hoc, report-only). C1-C5 still resolved. New: C6-C9, all minor and open; they go to the human.

- C6: part (b) 'without Georgia' removes only Georgia's six L tests. Georgia stays in nu_h1 (s2_h1_13 = 0.0105, the largest of 50, 17.8% of the sum; nu without it 17.92 against 14.41), in California's h1 SE_n (R50 donor) and in the other nine L units' SE_n. The direction probably favours rejection, so the qualitative flip should survive. This was my own results-r1 framing, computed the same partial way. Lesson: say 'own tests removed' when I mean that.
- C7: Georgia-only deletion; asked for leave-one-L-state-out c_hi and decisions.
- C8: 722511/7225/10 comparison series are in georgia.csv only, not in metrics; D7(a) 'whether ... artifact' wording; county_sum emp includes suppressed zeros.
- C9: claim r-h1-crit-georgia states the posthoc result with level-mde support only.

Ran (scratch rv-c4/ws, copies of the seven declared inputs; nothing written to the workspace): posthoc.py exits 0 in about 1 s. Results: GA 722513 aww 304 -> 255 (2014Q4 -> 2015Q1), level shift, yoy dev -0.139 to -0.170; emp dev within ±0.012; estabs +3.8%; 0 suppressed quarters; 722511 aww not down. Largest other |dev| is FL 2018Q4 at -0.078. Part (b): 54 values, others' max T 1.13, c_hi95 = t_nu 1.758, all three decisions reject (pre-specified 0). Part (c): emp slope 0.00229/q (implied +0.0149), wage 0.00847/q (implied +0.055, against an h1 ATT of 0.092), wage RMS 0.141.

Check next time (results r2 / paper):
- runs/posthoc ran once, names code-r4 as its code review, with --code posthoc.py and sclib.py and the seven inputs in runs/NOTES.md. If posthoc.py changes for C6-C8 it needs a new code review; code is capped at r4, so it would have to run --unreviewed with a reason.
- The paper never presents b_*_reject_noga as a verdict or as 'H1 supported'. Georgia's removal is described as partial (C6) and as post hoc.
- The wage drift implied over the post window (about 0.055) is large next to the h1 ATT; the limits section should say so, because the DDT wage counterfactual itself drifts.
- r-h1-crit-georgia is re-supported by posthoc metrics (C9).
