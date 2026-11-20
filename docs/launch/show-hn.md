# Show HN draft

> Status: final, ready to post: all six gallery papers have passed their submission gates. Check numbers against `gallery/scoreboard.json`.

**Title:** Show HN: Free-Research-Crew – AI research assistants with a reviewer that never lets up

**URL:** https://github.com/brycewang-stanford/Free-Research-Crew

**First comment:**

I built a crew of research-assistant agents that takes a question to a compiled paper in empirical ML or empirical social science, inside Claude Code (it also installs into Codex). The part I think is interesting is not the writing; it is keeping the agents from grading their own work.

Three kinds of judgment are kept apart:

- *What happened* is checked by a small stdlib Python tool: analysis can't run before a human approves the design, every number in the paper is a LaTeX macro generated from a logged run, editing code after a run invalidates it, and every citation needs a verification record.
- *Whether it is good* is decided by a Reviewer agent that never wrote any of it, reads the files rather than the authors' summary, and opens every review with the single strongest argument for rejection (design borrowed from ARIS).
- *Whether to go on* is decided by a human at four gates.

I ran it on six seed tasks: four social-science (three replications and a null-effect test) and two ML. Every workspace, review and gate decision is in `gallery/`. Some things the Reviewer caught:

- A replication tolerance sized to sampling error, which a sloppy replication would pass; then, after the fix, one so tight that a faithful replication would fail; then the right formula.
- A Python port of R's `hdm::rlasso` that skipped a zero-threshold step; porting it moved the R–Python gap from $87 to $0.36.
- A placebo test that a pre-program earnings dip would make "fail" whether or not the identifying assumption held.
- Confidence intervals on small datasets that were ~40% as wide as honest ones, because every seed re-split the same rows.
- A related-work sentence that credited a published paper with a count the crew had made itself, from the authors' released archive, with an unlogged script.
- On the LaLonde comparison, a primary estimate whose 95% interval excluded zero by $9.6, when three of its five cross-fitting repetitions alone did not; the paper now says the decision is within seed noise.

On a synthetic dataset with a true effect of exactly zero, the crew reported −$10 [−358, 338] and did not report a secondary outcome with an uncorrected p = 0.044.

Cost: it runs on the Claude Code or Codex plan you already have, with no server and no separate API bill. Each paper took 18–25 hours of wall time, much of it waiting for me at gates; time and model usage per paper are measured from the transcripts (`gallery/usage.json`).

Limits: gate approval is guarded by a hook that refuses an approve command unless my latest answer approved that gate, but a determined agent could still work around it; the Reviewer runs on the same model family unless you opt into cross-family review via Codex; the papers are demos and are not submitted anywhere. CC0.
