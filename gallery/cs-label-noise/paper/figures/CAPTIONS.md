# Figure and table captions (cs-label-noise)

Every figure and table below was built by a script under `code/`. Each script ran through
`crew.py run --kind analysis` (the run id is given for each item), and it reads only the
metrics files of logged runs, declared with `--input`. No number was typed by hand. Table
cells that the paper quotes are written as the claims' macros, so the fragments need
`\input{numbers.tex}` and `\usepackage{booktabs,array}`. Each fragment is a bare `tabular`.
The Writer adds the float, the caption below and the label.

Notation used throughout: m is the majority-class share of the test split (seed mean).
A(rho) is clean-test accuracy, averaged over the 10 seeds. h = A(0) - m is the headroom.
r = (A(0) - A(0.4)) / h is the share of headroom lost. D = r_GBDT - r_RF (H1), D1 = r_LR -
r_GBDT and D2 = r_LR - r_RF (H2). Delta = D_main - D_ablation. S is the per-seed SD of
the linearized difference. All three figures use one palette and one style. Methods are
told apart by colour and also by marker and line style, so they read in grayscale.

---

## Figure `fig_accuracy.pdf`: run `fig-accuracy`, script `code/fig_accuracy.py`

**Caption.** Clean-test accuracy against the training-label flip rate rho, for each
dataset and method. Each point is the mean over 10 seeds. The error bars are plus or minus
one standard deviation across those seeds (seed spread, not a confidence interval). Within
a seed, the split, the test set and the nested flip sets are shared across methods and
rates. Points are shifted slightly sideways so the error bars do not overlap. The dashed
gray line is the majority-class rate m. Test sets have 114 (breast_cancer), 200 (credit-g)
and 1,000 (adult, covtype) rows. credit-g is drawn with a dashed frame and labelled
"excluded". It was excluded before any noisy run, because at rho = 0 the headroom of at
least one method was below 0.05 (Table `tab_exclusion`). Its curves are descriptive only.
Each y-axis runs from just below the lowest of m and every mean minus SD, up to 1.0. No
axis is cut above the data.

Sources: `runs/main-rho0/metrics.json`, `runs/main-noisy/metrics.json` (seed means, SDs,
n_seeds = 10, m) and `runs/exclusion-check/metrics.json` (the exclusion flag).

## Figure `fig_contrasts.pdf`: run `fig-contrasts`, script `code/fig_contrasts.py`

**Caption.** Pre-registered contrasts in the share of headroom lost between rho = 0 and
rho = 0.4. Left: H1, D = r_GBDT - r_RF (H1 predicts D > 0). Middle and right: H2, D1 =
r_LR - r_GBDT and D2 = r_LR - r_RF (H2 predicts both < 0). The dark line is the 95%
decision interval: a paired t(9) interval over 10 seeds on the linearized ratio. It is
Nadeau-Bengio corrected on the datasets marked with a dagger (breast_cancer and credit-g,
where every seed re-splits the same rows) and uncorrected on adult and covtype. The light
line below it is the 95% seed-bootstrap percentile interval (10,000 resamples). It is
descriptive only and never decides an outcome. On breast_cancer it is narrower than the
decision interval because it has no Nadeau-Bengio correction. The gray band marks
|difference| < 0.05, the smallest meaningful difference. The marker gives the per-dataset
outcome under the pre-registered rule: filled for supported, open for no detectable
difference (inconclusive), and a cross for excluded. Under H2 the outcome is joint over D1
and D2, so both panels carry the same marker. credit-g was excluded at rho = 0 and is
drawn in its own row on its own x-scale, because its intervals are several times wider.
Overall, over the three informative datasets, both H1 and H2 are inconclusive under the
count rule (Table `tab_h1h2`).

Sources: `runs/h-tests/metrics.json` only.

## Figure `fig_ablations.pdf`: run `fig-ablations`, script `code/fig_ablations.py`

**Caption.** Ablation tests. Each row is Delta = D_main - D_ablation for one ablation and
dataset, with the dataset's 95% paired t(9) decision interval over the same 10 seeds
(Nadeau-Bengio corrected on breast_cancer and credit-g). A1 removes GBDT early stopping
and tests only the H1 contrast. A2 uses clean validation labels at rho = 0.4. A3 takes the
best of the first 10 of the same 20 candidates. The gray band marks |Delta| < 0.05. The
marker gives the pre-registered status: filled means attributed (the interval excludes 0
and |Delta| >= 0.05), open means not attributed, and a cross means excluded. One of the 21
tests on informative datasets is attributed: A2, H1 contrast, on adult. About one such
interval is expected by chance at 95% across 21 tests, and no multiplicity correction was
planned (claim `c-abl-count`). A2 changes two things at once: the labels used for model
selection and the labels GBDT's early stopping monitors. That result therefore cannot be
assigned to model selection. A1 compares GBDT and GBDT-noES, which use different random
candidate configurations. credit-g (excluded) is drawn on its own x-scale. Its A1
GBDT-noES headroom also failed the stability check.

Sources: `runs/abl-noes/metrics.json`, `runs/abl-cleanval/metrics.json`,
`runs/abl-budget/metrics.json`, `runs/h-tests/metrics.json` (the exclusion flags).

---

## Table `paper/tables/tab_exclusion.tex`: run `tab-exclusion`, script `code/tab_exclusion.py`

**Caption.** Exclusion check, decided from the rho = 0 cells only, before any noisy run.
For each dataset the table gives m, A(0) for each method (mean over 10 seeds) and the
headroom h = A(0) - m. A dataset is uninformative for a hypothesis if any method's
headroom is below 0.05 (asterisk). The whole dataset is excluded, never a seed.

Sources: `runs/exclusion-check/metrics.json` (h, m, the flags, the threshold) and
`runs/descriptives/metrics.json` (A(0), checked against `runs/main-rho0/metrics.json`).

## Table `paper/tables/tab_h1h2.tex`: run `tab-h1h2`, script `code/tab_h1h2.py`

**Caption.** Per-dataset tests of H1 (D) and H2 (D1, D2). For each contrast the table
gives the point estimate, the 95% decision interval (paired t(9) over 10 seeds;
Nadeau-Bengio corrected on the datasets marked with a dagger), S, the half-width, and the
difference in absolute accuracy drops between rho = 0 and 0.4. Supporting a hypothesis
needs the interval to exclude 0 in the predicted direction, |difference| >= 0.05 in r, and
a drop difference of at least 0.01. The outcome rows use the pre-registered reporting
words. Under H2 the outcome is joint over D1 and D2. credit-g was excluded at rho = 0, and
its rows are reported but not counted. The last rows give each hypothesis's overall verdict
under the count rule (support on at least max(2, ceil(0.75 n)) of the n informative
datasets and contradiction on none), with the counts behind it.

Sources: `runs/h-tests/metrics.json`.

## Table `paper/tables/tab_parts.tex`: run `tab-h1h2`, script `code/tab_h1h2.py`

**Caption.** Components of the H1 and H2 measures, per dataset and method: m, A(0) and
A(0.4) (means over 10 seeds), the absolute drop A(0) - A(0.4), the headroom h, the lower
end of the 95% interval of h (the denominator-stability check), and r. On credit-g
(excluded) every method falls below m at rho = 0.4, so r is above 1. Those values are
descriptive only.

Sources: `runs/h-tests/metrics.json` (A(0), A(0.4), m and drop matched to the descriptives
macros).

## Table `paper/tables/tab_ablations.tex`: run `tab-ablations`, script `code/tab_ablations.py`

**Caption.** Ablation tests, Delta = D_main - D_ablation, with the dataset's 95% paired
t(9) decision interval over 10 seeds. A1: GBDT without early stopping (H1 contrast only).
A2: model selection and GBDT early stopping on clean validation labels at rho = 0.4. A3:
the best of the first 10 of the same 20 candidates. Superscript a marks an attributed
result (the interval excludes 0 and |Delta| >= 0.05). Superscript x marks an excluded
dataset. The single attributed result (A2, adult, H1 contrast) is 1 of 21 tests on
informative datasets. It cannot be assigned to model selection, because A2 also changes
the labels GBDT's early stopping monitors.

Sources: `runs/abl-noes/metrics.json`, `runs/abl-cleanval/metrics.json`,
`runs/abl-budget/metrics.json`.

## Table `paper/tables/tab_accuracy.tex`: run `tab-accuracy`, script `code/tab_accuracy.py`

**Caption.** Clean-test accuracy, mean (SD) over 10 seeds, for each dataset, method and
flip rate rho, with the majority-class share m. The SD is the seed spread. credit-g was
excluded at rho = 0 and is reported descriptively. (Appendix table. At `\small` it is
wider than one column, so set it in a full-width float or scale it.)

Sources: `runs/descriptives/metrics.json`, `runs/exclusion-check/metrics.json` (the
exclusion flag).

---

## Notes for the Writer (from reviews/REVIEWER_MEMORY.md, paper stage)

- H1 and H2 are both **inconclusive** overall. covtype's H1 "supported" is one
  per-dataset outcome on 5,000-row subsamples. The figures give it the same colour and
  size as every other row; only the marker fill differs.
- Never cite the breast_cancer seed-bootstrap interval in `fig_contrasts` as support.
  It is descriptive (see the caption).
- A2 on adult: say "cannot be assigned to model selection" and cite `c-abl-count` next to it.
- The macro `\ATwoDeltaTwoCt` renders as `-0.000` (the value is a tiny negative). If the
  sign looks odd in `tab_ablations`, ask the Experimenter to change that claim's format.
  Do not edit the table by hand.
- `tab-h1h2`, `tab-exclusion`, `tab-ablations` and `tab-accuracy` declare `claims.jsonl`
  as an input. Any later edit to `claims.jsonl` (even to text) makes `crew.py validate`
  ask for these four runs to be repeated with `--replace`.
