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
