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
