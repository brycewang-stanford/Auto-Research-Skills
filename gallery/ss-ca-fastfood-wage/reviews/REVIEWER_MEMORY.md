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
