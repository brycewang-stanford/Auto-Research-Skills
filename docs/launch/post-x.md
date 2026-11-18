# X thread draft

> Status: draft. Post after the gallery papers pass submission; numbers per `gallery/scoreboard.json`.

1/ I built a crew of AI research assistants that writes empirical ML and social-science papers in Claude Code. The most useful member writes nothing. It only attacks the others' work. 🧵 github.com/brycewang-stanford/Free-Research-Crew

2/ The rule: the agent that does the work never judges it. A tool checks what happened (every number in the paper is generated from a logged run). A Reviewer judges whether it's good. You decide whether to go on, at 4 gates.

3/ On a replication of the 401(k) double-ML estimates, the Reviewer found our Python lasso skipped a zero-threshold step in R's hdm. Porting it: R–Python gap $87 → $0.36.

4/ On data with a true effect of exactly zero, it blocked a placebo test that a pre-program earnings dip would make "fail" either way. Final estimate: −$10 [−358, 338]. A secondary outcome with uncorrected p = 0.044 was not reported as a finding.

5/ On a label-noise study, it found the small-dataset intervals were ~40% as wide as honest ones. Both hypotheses ended "inconclusive". That's the honest answer, and it's in the gallery with everything else.

6/ Free: plain role files + a stdlib tool, runs in the CLI you already have, CC0. Reviewer design learned from ARIS (@ the ARIS authors). Every workspace, review and gate decision is public in gallery/.
