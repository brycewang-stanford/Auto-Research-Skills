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
