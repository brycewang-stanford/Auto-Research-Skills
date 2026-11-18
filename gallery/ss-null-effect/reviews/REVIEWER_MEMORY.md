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

## question-r2 (2026-11-18T12:08Z), verdict: revise
F1-F8 all resolved. New: F9 (major, the $1,000 margin's units and basis), F10 (minor,
Romano-Wolf stepdown vs max-t decision rule), F11 (minor, plan revision not logged, no
hash or commit of plan.json).

Suspicions:
- The $1,000 margin was fixed blind to re78's scale. If the crew later "discovers" the
  units and adjusts the margin after seeing re78, that is a forking path. Any change to
  the margin must be logged before the first analysis run and anchored to covariates
  only (re74/re75).
- No code/, runs/ or data/raw yet. data/manifest.json is empty. Nothing shows outcomes
  were opened. The workspace is untracked in git, so file mtimes are the only timeline
  (machine local time is UTC+8; plan.json mtime 20:06:38 local = 12:06:38Z).
- Survey items are excluded as covariates. If they turn out to be pre-program
  motivation measures, unconfoundedness is weak. That is a limitation now, but the design
  must carry a sensitivity analysis (Imbens 2003 style) fixed in advance.

Next time (design review):
- re78 - re75 difference outcome (notes section 9.6) would be an extra outcome-like
  specification. Check that it is pre-declared as robustness, not a rescue.
- Interval for the relative effect (estimated denominator): delta method or bootstrap,
  fixed in advance.
- Overlap assumption (p(X) < 1 for ATT) stated; trimming rule and the trimmed estimand
  named as secondary.
- Learners, folds, seed and propensity specification fixed; alternative propensity
  sets listed and all reported.
- re75 placebo conditions on re74, not re75.
- Region coding (number of categories) and the treatment column name confirmed
  outcome-blind at data-prep, with a data-prep run, not an analysis run.
- Whether F9 was fixed by an outcome-blind anchor and logged before the gate.
- Literature review: still spot-check card2018, lalonde1986 ($886, SE 476) and
  crump2009 ([0.1, 0.9]).

## question-r3 (2026-11-18T12:10Z), verdict: pass
F9, F10 and F11 resolved. I recomputed plan.json's SHA-256 (1ccb35da...0f4e9a2) and it
matches log.jsonl line 3. New minor findings: F12 (the '10% conventional' margin has no
source; participants' re75 may be depressed by a pre-entry dip, so H1b may be untestable;
no fallback stated) and F13 (a Romano-Wolf/max-t bootstrap with ML nuisances against the
30-minute laptop budget).

Suspicions:
- The current plan.json is NOT in git. Commit e8e27e2 has the old $1,000 version (sha
  9960b098...). The PI's response to F11 claimed it was committed. Check that it is
  committed before the design gate.
- sources/notes.md (section 3, Imbens 2004) suggests running the re75 placebo "as data
  preparation". That would be a result before the design gate that could shape the
  propensity specification. If it shows up as a data-prep run, flag it.
- The data-prep run that computes M will load the whole of data.csv, outcomes included.
  Read its code. It must touch only the treatment column, re75 and other covariates,
  and its metrics must contain no outcome summaries.
- If TOST fails after the gate, watch for M being re-anchored (to re74, to the non-
  participant mean, or for price-year adjustments).

Next time (design review):
- M logged by a data-prep run before the gate; its code is outcome-blind.
- F12: is 'conventional' removed or cited, is there a precision proxy, is the TOST-fail
  fallback stated?
- F13: bootstrap type, number of draws and seed fixed; runtime checked on covariates.
- Carry over from r2: the overlap/trimming rule and the trimmed estimand as secondary;
  learners, folds and seed; the re75 placebo conditions on re74, not re75; Imbens (2003)
  sensitivity fixed; re78 - re75 only as declared robustness; the interval for the
  relative effect.
- Literature review: still spot-check card2018, lalonde1986 ($886, SE 476) and crump2009.
