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
