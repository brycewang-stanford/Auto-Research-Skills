# Experimenter notes: cs-label-noise

What ran, in order, with wall times and anything surprising. Timing is kept here and in
`runs/<id>/timing.json`, never in metrics, so `crew.py rerun` compares only reproducible numbers.

## Code (written 2026-11-18, after the design gate)

| File | Purpose |
|---|---|
| `code/common.py` | constants fixed by design.method (datasets and their index d, seeds 0..9, rates, N = 20, N_half = 10, root seed 20261118, bootstrap seed 20261119, split sizes, which datasets get the Nadeau-Bengio factor) and the flat-metrics writer |
| `code/experiment.py` | design.method steps 1-8: SeedSequence([20261118, d, s]).spawn(5) streams, stratified cap and 60/20/20 split, exact nested flips with assertions, train-only preprocessing, the three estimators and GBDT-noES, 20-candidate random search scored on noisy (or, for `cleanval`, clean) validation labels, one test prediction per cell plus the A3 best-of-first-10, 8 joblib workers with one BLAS/OpenMP thread each |
| `code/exclusion.py` | reads `results/cells_rho0.csv` only (asserts rho = 0), writes `results/exclusion.json` |
| `code/analyze.py` | `--test main` (H1, H2), `--test noes/cleanval/half` (A1, A2, A3 Delta tests), `--describe` |

Implementation choices that the design leaves implicit (none changes a decision rule):

1. **Label encoding.** The prepared tables keep the original labels; `experiment.py` encodes
   them as the index in `data/derived/schema.json` `classes` (breast_cancer 0/1; credit-g
   bad=0, good=1; adult <=50K=0, >50K=1; covtype 1..7 -> 0..6). The flip `(y + shift) mod K`
   is uniform over the other K-1 classes under any encoding.
2. **Nadeau-Bengio factor.** c = 1/J + n_te/n_tr with the exact sizes, so 0.1 + 114/341 =
   0.4343 on breast_cancer (the method text rounds this to 0.1 + 1/3) and 0.1 + 200/600 on
   credit-g. The half-width is 1.49 S on both either way.
3. **Ablation denominators.** A Delta is reported 'inconclusive (unstable denominator)' if the
   h-interval check fails for any denominator that enters D_main or D_ablation (the ablation's
   own rho=0 headroom, as design.method requires, and also the main ones). The two components
   are recorded separately (`*.abl_denominator(s)_stable` and the main `*.h_stable` metrics).
4. **A3 test prediction.** When the best of the first 10 candidates is the overall winner, its
   test prediction is reused instead of predicting twice (same model, same numbers).
5. **Bootstrap.** Resamples whose headroom is 0 give non-finite r. They are counted
   (`*.boot_nonfinite`) and left out of the descriptive percentiles. The bootstrap never
   decides an outcome.
6. **n_flip.** floor(rho n + 0.5) is computed exactly from the decimal rate (`Fraction`). No
   split size gives a .5 tie at these rates.

The statistics code was unit-tested on synthetic cell tables in a scratch directory outside
the workspace (no study data). The half-widths matched design.method: 0.72 S on adult and
covtype, 1.49 S on breast_cancer and credit-g.

## Runs

### 1. `smoke` (data-prep, 2026-11-18): about 27 s wall; rerun with `--replace` after the code-r1 fixes (about 40 s)

A tiny configuration to check the pipeline before any study cell: **seed 100 (not a study
seed), 2 candidates per method, rho 0 and 0.4**, with the variants `main`, `gbdt_noes` and
`cleanval`, on all four datasets. The smoke run writes no accuracy, validation score or
selected configuration. Its cell tables do record one learning outcome on the study
datasets: the GBDT and GBDT-noES `n_iter` of the selected model at rho 0 and 0.4 (seed 100,
N = 2), used here only to confirm that early stopping triggers (code-r1 F2 corrected the
earlier wording, which said no learning outcome was recorded). The rest is structural.

- Split sizes 341/114/114, 600/200/200, 3000/1000/1000 and 3000/1000/1000, as designed. Every
  class is present in every split, including covtype's class 4.
- Feature counts after one-hot encoding: breast_cancer 30, credit-g 61, adult 103 (the design
  estimated about 108; the count depends on which levels occur in the 3,000 training rows),
  covtype 54.
- Flip counts equal floor(rho n + 0.5) in every cell, flips are nested, and no flipped label
  equals its clean label.
- 0 LogisticRegression convergence warnings.
- GBDT early stopping triggers (n_iter_ from 22 to 164 in the first smoke run's cells), so it is active.

### Code review (code-r1, verdict pass, two minor findings), fixed before main-rho0

- **F1. Exact thresholds.** Every accuracy is a count out of n_test, so the seed means of
  test accuracy and majority rate are computed as exact Fractions (`common.exact_mean`,
  which also asserts that each value is k/n). These comparisons are now exact: the exclusion
  cutoff (A(0) - m >= 0.05), the drop-difference threshold (>= 0.01), the |D| and |Delta|
  thresholds (>= 0.05), and the 'within noise' gap estimates. Reported values are floats of
  those Fractions. The interval bounds (which involve a square root) and the h-interval floor
  stay floating point. No rule changed. On synthetic credit-g vectors whose exact headroom is
  0.05, the float comparison misread 284 of 2,000; the exact one misread none.
- **F2. Chain of custody.** Every run from here on passes `code/common.py` as `--code`. Each
  `results/*.csv` and `results/*.json` file is an `--output` of the run that writes it and an
  `--input` of every run that reads it. `experiment.py` exits with an error for noisy `main`
  cells while `results/exclusion.json` is missing. The smoke-run sentence above is corrected.

## Analysis runs (2026-11-18), in planned order

| # | Run | Started (UTC) | Wall | What |
|---|---|---|---:|---|
| 2 | `main-rho0` | 13:18:31 | 306 s | 120 clean-label cells; 37.7 CPU-min of fits |
| - | contingency | 13:23 | - | W0 = 306 s; projected total 7 x W0 = 35.7 min <= 45 min, so **no contingency**: A1 and A2 both run (logged before exclusion-check) |
| 3 | `exclusion-check` | 13:23:48 | <1 s | read `results/cells_rho0.csv` only; wrote `results/exclusion.json` |
| 4 | `main-noisy` | 13:23:54 | 701 s | 480 cells at rho 0.1-0.4; 88.6 CPU-min; refused to start without `exclusion.json` |
| 5 | `h-tests` | 13:35:48 | 1 s | H1, H2 |
| 6 | `descriptives` | 13:35:49 | 1 s | accuracy table, rankings, hyperparameters, diagnostics |
| 7 | `abl-noes` (A1) | 13:36:00 | 164 s | 80 GBDT-noES cells + Delta test; 19.8 CPU-min |
| 8 | `abl-cleanval` (A2) | 13:38:44 | 291 s | 120 clean-validation cells at rho 0.4 + Delta tests; 35.6 CPU-min |
| 9 | `abl-budget` (A3) | 13:43:35 | 1 s | half-budget Delta tests (no fits) |

Total analysis wall time is **24.4 min** (main runs 16.8 min), against the design estimate of
about 20 min and the 60-min budget. The smoke run took another 49 s. Two crew.py invocations
failed at argument parsing, before anything ran (a zsh word-splitting slip in my shell); no
run directory was created and nothing executed.

### Exclusion (from rho = 0 only)

credit-g is uninformative for both H1 and H2: headroom A(0) - m is 0.035 for GBDT and 0.0485
for RF (and 0.0505 for LR), all against m = 0.700. breast_cancer, adult and covtype are
informative for both hypotheses, so n = 3 for H1 and n = 3 for H2. Overall support needs
max(2, ceil(0.75 x 3)) = 3 of 3.

### Main results (decision interval: paired t(9), NB-corrected on breast_cancer)

| Dataset | H1: D = r_GB - r_RF [95% CI] | H1 | H2: D1 = r_LR - r_GB | D2 = r_LR - r_RF | H2 |
|---|---|---|---|---|---|
| breast_cancer | +0.264 [-0.014, +0.543] | inconclusive | -0.034 [-0.497, +0.428] | +0.230 [-0.189, +0.648] | inconclusive |
| credit-g | (+0.236 [-1.253, +1.725]) | excluded | (-1.009) | (-0.773) | excluded |
| adult | +0.112 [-0.217, +0.440] | inconclusive | -0.167 [-0.481, +0.147] | -0.055 [-0.184, +0.073] | inconclusive |
| covtype | +0.073 [+0.022, +0.124] | **supported** | -0.090 [-0.138, -0.041] | -0.016 [-0.059, +0.026] | inconclusive |

Overall: **H1 inconclusive** (1 supported, 2 inconclusive, 0 contradicted of 3); **H2
inconclusive** (0 supported, 3 inconclusive, 0 contradicted of 3). No headroom interval fell
below 1 point on the informative datasets, so no outcome was set by the unstable-denominator
rule. Reporting words, per design.method: 'inconclusive' is written 'no detectable
difference (inconclusive)'. The claim texts and metrics use the short label.

### Ablations (attribute only if the Delta interval excludes 0 and |Delta| >= 0.05)

- **A1 (no early stopping):** not attributed on breast_cancer (Delta -0.143 [-0.461, +0.176]),
  adult (-0.135 [-0.341, +0.072]) or covtype (+0.013 [-0.024, +0.050]). On credit-g (excluded)
  the GBDT-noES headroom also failed the stability check.
- **A2 (clean-validation selection at rho 0.4):** **attributed on adult for the H1 contrast:
  Delta = -0.370 [-0.709, -0.030].** With clean-validation selection, D_abl = +0.481
  [+0.302, +0.661], larger than D_main = +0.112. So on adult, noisy model selection shrinks
  GBDT's excess loss relative to RF; it does not create it. Every other A2 Delta was not
  attributed (adult Delta1/Delta2, all of breast_cancer and covtype).
- **A3 (half budget):** not attributed anywhere. The largest is covtype Delta = +0.032
  [-0.018, +0.083].

## Surprises and things the paper should say

1. **breast_cancer H1:** the decision interval [-0.014, +0.543] only just includes 0. The
   descriptive seed bootstrap gives [0.173, 0.390]. The Nadeau-Bengio correction is what makes
   this outcome inconclusive (this power limit was stated in advance in design-r3). It cannot
   be reported as support.
2. **Results against H2:** on breast_cancer, LR loses a larger share than RF (r 0.560 vs 0.330;
   D2 = +0.230, absolute drop 0.190 vs 0.105), the opposite of H2. The interval includes 0. On
   adult and covtype, LR's point estimates are in H2's direction against GBDT but not
   separable from RF.
3. **credit-g:** r exceeds 1 for every method (1.5 to 2.5). At rho = 0.4 all three fall
   below the 0.700 majority rate (A(0.4) 0.638 to 0.675). The dataset is excluded, so this is
   descriptive only.
4. **covtype rankings:** GBDT and RF tie at rho = 0 (0.7555 vs 0.7554; within noise). At every
   rho >= 0.1, RF > GBDT > LR, and each gap's paired interval excludes 0.
5. **Tuned hyperparameters move with noise as expected:** the median LR C falls from 0.28 to 0.04
   (breast_cancer), 0.27 to 0.007 (credit-g) and 0.38 to 0.006 (adult) between rho 0 and 0.4,
   but not on covtype (2.25 to 0.62). The median RF min_samples_leaf rises (for example adult
   3 to 23), and the median GBDT n_iter_ falls on breast_cancer (167 to 31).
6. **Diagnostics:** 0 flip-count failures in 600 cells; 0 logistic-regression convergence
   warnings.
7. **Determinism, cross-run check inside the ledger:** in A2 the LR and RF fits equal main's.
   In all 17 cells where both runs selected the same configuration (LR 10, RF 7), test and
   training accuracies match exactly across the two processes. The full clean rerun is the
   Replicator's task (`r-rerun`).

## Deviations from the approved design

None. The contingency was evaluated as written and did not trigger. The code-r1 fixes (exact
threshold comparisons, input/output hashing, the exclusion guard) were made before main-rho0
and change no rule. The implementation choices listed under "Code" fill gaps the design left
open; none was chosen after seeing results.

## Claims

`claims.jsonl` holds 1,193 result claims generated by `code/make_claims.py`. That script runs
no computation: it copies each `value` from `runs/<id>/run.json` metrics. The claims cover the
accuracy table (mean and SD at every rate), the majority rates, headrooms, drops and r, every D
and Delta with its decision interval, S, half-width and bootstrap interval, the outcomes and
verdicts (as text claims tied to the outcome metrics, including the inconclusive and adverse
ones), the ablation accuracies, the tuned hyperparameters, the validation and training
diagnostics, and the rankings. `paper/numbers.tex` was regenerated with `crew.py numbers`.
