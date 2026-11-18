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
