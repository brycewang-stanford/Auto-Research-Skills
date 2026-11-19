# Run notes (econometrician)

## diag-overlap (data-prep, before the design gate), 2026-11-19

- Script: `code/diag_overlap.py`, adopted from `gallery/ss-null-effect/code/diag_overlap.py`
  (sha256 235d2ecb...acf5) with only DEV-1, DEV-2, DEV-4, DEV-5, DEV-6 applied (ten covariates,
  14-term B(X), 56-term B+(X), upper clip 0.99 only, control-only trimming count).
- Input: `data/derived/analysis_noRE78.csv` only (no re78 column; refuses to run if one exists).
  Nothing was built or fitted on X- (covariates without re75/u75).
- Seeds: 20261118 + s, s = 0..4 (outer 5-fold StratifiedKFold and inner CV). 37 treated per test fold.
- Only addition to the learner code: FutureWarnings from scikit-learn 1.9.1 are silenced with a
  warnings filter (no learner argument changed); ConvergenceWarnings are counted (0).
- Outcome: B1 pass (max weighted |SMD| 0.059, age^2), O1 pass (0 of 185 treated with m_bar > 0.9),
  O2 pass (0 clipped units). Final basis B(X); diag-overlap-ext not run. Kish ESS of weighted
  controls 126.4; largest control weight 6.41. rob-trim would drop 8,125 CPS men (all below the
  treated minimum m_bar 1.03e-4), keeping 7,867.
- Worth noting: the trimmed set is large (about half the CPS men) because the lowest treated
  m_bar (1.03e-4) sits just above the CPS median m_bar (9.5e-5).
