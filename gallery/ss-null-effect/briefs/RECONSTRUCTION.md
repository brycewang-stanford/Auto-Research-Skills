# Briefs: reconstruction by the PI

The PI did not archive its briefs to the agents of this paper as they were sent; the
crew's playbook now requires it (`crew/PI.md`, "Archive every brief"). This file is a
reconstruction written by the PI session after the fact, from its own conversation record,
on 2026-11-18. It cannot be independently verified, and it says so.

The PI session also wrote this seed (`crew/bench/seeds/ss-null-effect/`: the data
generator and the hidden answer key). It therefore knew that the true effect is zero.

## What every brief contained

- The workspace path, the role file to follow, the protocol file, the track playbook.
- "Never open answer.json or anything under answer/ in the seed directory."
- Before the design gate: "outcomes are sealed"; no statistic involving any outcome column.

## Instructions with substance, by stage

| Stage | To | Substantive instruction from the PI |
|---|---|---|
| Question | PI's own draft | Neutral question and hypotheses written in the form of a program evaluation: H1 "participation raised 1978 earnings", H2 "raised employment". The PI chose not to state any expectation about the sign or size. |
| Question | Scout | Literature list to cover: LaLonde; Dehejia & Wahba; Smith & Todd; doubly robust estimation; Imbens reviews; overlap and trimming; multiple-testing corrections; pre-analysis plans. |
| Question r1→r2 | PI's own revision | Answered the Reviewer: named covariates, closed outcome list, survey items excluded, ATT, a $1,000 equivalence margin. |
| Question r2→r3 | PI's own revision | Replaced the $1,000 margin with 10% of participants' mean re75, at the Reviewer's suggestion (F9), because the $1,000 figure leaned on a benchmark the Scout had ruled out. |
| Design | Designer | Fix estimator, diagnostics, robustness, secondary family, sensitivity, claim ids; time on covariates with a synthetic outcome only. |
| Design | Data RA | Copy and hash the extract; covariates file without outcomes; compute M and the precision proxy from treat and re75 only. |
| Design r1 | Designer | PI ruling: a pre-gate run may count missing outcome values by arm, counts only. Preferences: relabel the re75 placebo as descriptive; re78 − re74 for the DiD check; specify the sensitivity analysis fully. |
| Design r2 | Designer, Data RA | PI ruling: a pre-gate run may count out-of-range outcome values by arm, counts only. Admissible ranges suggested by the PI (re78/re79 ≥ 0; employed78 ∈ {0,1}; hours78 ∈ [0, 8784]; benefits78 ≥ 0; wellbeing78 integer 0–10), to be checked by the Designer against the brief. |
| Results | Econometrician | Run every planned run exactly as specified; never change the plan because of results; report every flag the plan requires. |
| Results r1 | Econometrician | Answer the Reviewer without new estimation: scope H1b to unconfoundedness; add the mandated sentence; give both pre-registered readings of rob-diff74; drop unadjusted secondary intervals. |
| Paper | Writer | Required content: never "no effect"; H1b only under unconfoundedness with the mandated sentence; benefits78 not a finding; disclose the post-hoc code review, the retroactive F4 ruling, and seed authorship. |

## What the PI did not do

The PI did not tell any agent the true effect, the generator's structure, or the answer
key, and did not suggest any estimate. The reader has only the PI's word for this.
