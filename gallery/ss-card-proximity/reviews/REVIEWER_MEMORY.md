# Reviewer memory: ss-card-proximity

## question-r1 (2026-11-20, verdict revise)

Suspicions:
- The robustness layer (H2-H5) is fixed on Table 3 Panel A col 5 (no family background), while the headline basic spec is Panel B col 6. Watch for the paper describing the Panel A results as stressing "Card's IV estimate" (F1).
- Scout missed Cinelli & Hazlett (Biometrika 2025, iv.sensemakr): AR [0.025, 0.285] plus exclusion/confounding sensitivity (RV 0.67%) on exactly the Panel A col 5 spec. Also arXiv 2508.12474 (weak-IV-robust guide, Card example). The novelty sentence must change (F2).
- With one instrument, AR at 0 is the reduced-form t-test, and the AR-based CHR breakdown is the RF lower confidence bound (~0.007). Wald-based CHR is not weak-IV robust (F3).
- H5's "design-stage run from the first stage alone" is a pre-gate pilot and cannot produce an MDE without the outcome; the published SEs give MDE ~0.15 (F4).

Asked for: H2-H5 moved to Panel A col 6 (or col 6 primary) or narrowed wording; Cinelli-Hazlett fetched, recorded and compared; H4 interval type fixed (AR-based primary); MDE from published SEs, no pre-gate run; one primary IV-vs-OLS rule; H1 columns and seed-claim mapping explicit.

Check next time:
- plan.json H1-H5 text and contribution; sources.json has a cinelli/hazlett record; no runs/ dir entries before the design gate.
- At the design gate: does H4's code invert AR per gamma0? Is the Panel B 3-endogenous model stated as uncovered by H2-H4?
- At the results gate: SE formula used for the H1 comparison matches the pre-specified one (conventional); OLS SE .003 vs .004 knife-edge (Kling).

## question-r2 (2026-11-20, verdict pass)

F1-F6 all resolved in plan.json and sources (Steiner et al. spot-checked against arXiv 2511.16029: matches). New minors: F7 (question still says "the IV conclusion" though H2-H5 never touch Panel B col 6; contribution calls Panel A col 6 "Card's preferred"), F8 (H5 non-rejection read via MDE; should be the robust CI of the IV-OLS difference, ~[-0.04, 0.17] from published numbers).

Check next time:
- Design: F7/F8 wording carried into design and paper. H4 code inverts AR per gamma0 with robust SE of the reduced form; breakdown should equal RF lower bound (~0.010 col 6) to rounding, else a bug.
- Design: controls lists match notes sec. 5 item 6 (reg662-reg669 vs CH's reg661-reg668: same span, different omitted region); sample = non-missing lwage76, unweighted; conventional SE for H1, robust for H2-H5.
- Results: OLS SE four decimals (Kling .003 vs Card .004); H1 secondary target AR [0.025, 0.285] reproduced homoskedastically on col 5.
- Paper: no "Card's preferred" for Panel A col 6; no "average return".
