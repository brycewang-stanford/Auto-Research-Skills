# X thread

> Status: final, ready to post. All six gallery papers have passed their submission gates; numbers per `gallery/scoreboard.json` and `gallery/usage.json`.

1/ I built a crew of AI research assistants that writes empirical ML and social-science papers in Claude Code. Six papers are done. The most useful member writes nothing: it only attacks the others' work. 🧵 github.com/brycewang-stanford/Free-Research-Crew

2/ The rule: the agent that does the work never judges it. A tool checks what happened (every result number in the paper is generated from a logged run; a clean rerun must reproduce every run). A Reviewer judges whether it's good. You decide whether to go on, at 4 gates.

3/ On a replication of the 401(k) double-ML estimates, the Reviewer found our Python lasso skipped a zero-threshold step in R's hdm. Porting it: R–Python gap $87 → $0.36. All 10 published cells then landed inside tolerances fixed before the analysis.

4/ On data with a true effect of exactly zero, it blocked a placebo test that a pre-program earnings dip would make "fail" either way. Final estimate: −$10 [−358, 338]. A secondary outcome with uncorrected p = 0.044 was not reported as a finding.

5/ On LaLonde's NSW-vs-CPS comparison, the 95% interval excluded zero by $9.6. The Reviewer pointed out that 3 of 5 cross-fitting repetitions alone did not, and the placebo failed. The paper calls it a statistical contrast, not a program effect.

6/ Across six papers: 68 review rounds, 12 critical and 210 major findings, no gate passed over an open critical one. Several hypotheses ended "inconclusive" or "contradicted". That's the honest answer, and it's in the gallery next to everything else.

7/ It runs on the Claude Code or Codex plan you already have: no server, no API bill. Each paper took 18–25 h of wall time, much of it waiting for me at gates. Time and usage per paper are measured from the transcripts and published.

8/ Free: plain role files + a stdlib tool, runs in the CLI you already have, CC0, v0.5 out now. Reviewer design learned from ARIS (github.com/wanshuiyin/Auto-claude-code-research-in-sleep). Every workspace, review and gate decision is public in gallery/.
