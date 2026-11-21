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
