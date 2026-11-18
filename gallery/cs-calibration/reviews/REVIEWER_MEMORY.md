# Reviewer memory: cs-calibration

## question-r1 (2026-11-18 UTC), verdict: revise (0 critical, 5 major, 4 minor)

Suspicions:
- H2 may be confirmed in binned ECE (which favours isotonic) and then presented as
  settling a dispute that is about proper scores. Watch which metric is labelled
  "primary" at design, and whether it changes after results.
- The choice of datasets and their calibration-split sizes can decide H2. Watch for
  OpenML datasets added or swapped after any pilot, and for load_breast_cancer-sized
  calibration splits.
- The novelty claims ("open", "clean test") are inflated relative to fonseca2017 (which
  ran Friedman GBC with isotonic on a held-out split and found it helped) and to
  manokhin2026 Appendix A (per-architecture results, unchecked).
- The Scout's summary of fonseca2017 left out the Sec. 3 sentence that RF/GBC beat LR
  on uncalibrated Brier.

Asked for:
- F1 a named metric per hypothesis (proper score for H2; calibration measure for H1).
- F2 a fixed dataset count and a per-dataset seed-noise decision rule.
- F3 named, pinned datasets and a minimum calibration n (or calibration n as a moderator).
- F4/F5 relabel H2b and narrow the contribution scope.
- F6 define "without recalibration" (defaults at the pinned version, or tuned).
- F7 Platt: descriptive or hypothesised, and one input scale for every model.
- F8 fix the fonseca2017 note.
- F9 use UTC for verified_on dates.

Check next time (question-r2 / design-r1):
- Is plan.json actually edited, not only the notes?
- Does design fix: ECE estimator (bins, equal-width/mass, P(y=1) vs top-label),
  log-loss clipping eps and clip counts, FrozenEstimator or manual calibrators (no
  ensemble=True), the same base model across none/Platt/isotonic, the seed redrawing
  both split and random_state, train-only preprocessing, an AUC control, the 60-min
  budget?
- If they claim manokhin2026 has no per-model HGB result, spot-check Appendix A.

Things I ran: none on study data. Fetched fonseca2017 PDF (arXiv) and the
manokhin2026 abs/html pages to check the novelty claims.
