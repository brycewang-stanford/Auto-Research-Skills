# Figure and table captions (cs-calibration)

Every figure and table below was built by a script under `code/`. Each script ran through
`crew.py run --kind analysis` (run ids below) after the results gate, and reads only files that
logged runs wrote, declared with `--input`: the `runs/<id>/metrics.json` of `h-tests`, `describe`,
`sens-ncal` and `sens-elec-time`, and, for the reliability diagrams, the test-split predictions that
run `main` wrote under `results/preds/main/` (git-ignored; `main` rebuilds them). No script reads
`claims.jsonl`, and no number was typed by hand. Design constants (the margins 0.005 and 0.001,
the predicted signs, the category words, the 15-bin equal-mass rule with its tie rule) are imported
from `code/analyze.py` and `code/experiment.py`, the code that runs `h-tests` and `main` executed.

Table cells that the paper quotes are the claims' macros, so the fragments need
`\input{numbers.tex}` and `\usepackage{booktabs}`. Each fragment is a bare `tabular`; the Writer
adds the float, the caption below and the label. Numbers no claim quotes (Platt's log-loss and AUC
in `tab_levels`, the category counts in `tab_decision`, the 1,351 in `tab_sensitivity`) are printed
from the run metric with the same format as the matching macros, and listed as plain numbers at the
end of each fragment. Category codes are printed as words (0 no difference, 1 holds,
2 contradicted, 3 no detectable difference (inconclusive); overall 0 no difference, 1 supported,
2 contradicted, 3 inconclusive), the same words the claims' texts give.

Notation. Seeds s = 0..9; each seed redraws the subsample, both splits and the models'
random_state, and every comparison is paired by seed. "Mean (SD)" is the mean over the 10 seeds
and, in parentheses, the SD across seeds (ddof = 1): a seed spread, not a confidence interval.
The 95% interval of a difference is the plain paired t(9) interval over the 10 per-seed differences
(treatment minus comparison). Because the seeds resample overlapping rows of the same pool (about
44% shared between two 20,000-row draws; phoneme reuses all rows), these intervals measure
variability over resplits of these samples, not population sampling variance, and every category is
scoped to these samples. ECE is the plug-in estimator with 15 equal-mass bins on P(y=1), tied
predictions never split across bins. Log-loss clips at 1e-6. Test splits have 5,000 rows on adult,
bank-marketing and electricity and 1,351 on phoneme; calibration splits have 5,000 and 1,351.

---

## Table `tab_decision.tex`: run `tab-decision`, script `code/tab_decision.py`

**Caption.** Pre-registered tests of H1, H2a and H2b. For each dataset: the mean over 10 seeds of
the paired per-seed difference, its 95% paired t(9) interval, and the category under the rule fixed
at the question gate, applied in order: *no difference* if the whole interval lies within plus or
minus the margin (0.005 for ECE, 0.001 for Brier); *holds* if it lies wholly on the predicted side;
*contradicted* if wholly on the other side; otherwise *inconclusive* (no detectable difference).
Overall (k-of-4): supported if it holds on at least 3 datasets and is contradicted on none;
contradicted if contradicted on at least 2; no difference if no difference on at least 3 and holds
or is contradicted on none; otherwise inconclusive. H1 compares uncalibrated RF with uncalibrated LR
on the plug-in ECE; H2a and H2b compare isotonic regression with no recalibration on the same frozen
RF or HGB, on the Brier score. Intervals are not adjusted for the three hypotheses on four datasets.
H1 is a test of the published direction on this estimator, not a replication: the plug-in ECE sits
at a noise floor of roughly 0.01 to 0.04 for a well-calibrated model, above H1's 0.005 margin, and
the bins it averages over differ between models (uncalibrated RF scores on \AdultRfNoneEceBins,
\BankRfNoneEceBins and \PhonemeRfNoneEceBins non-empty bins on adult, bank-marketing and phoneme,
against \AdultLrNoneEceBins, \BankLrNoneEceBins and \PhonemeLrNoneEceBins for LR; Table
`tab_levels`). H1's *contradicted* reflects LR's own miscalibration on bank-marketing and phoneme;
it does not show that RF is well calibrated. H2b's *no difference* means each interval lies inside
plus or minus 0.001 Brier, not that isotonic had no effect.
**Electricity dependence** (dagger): electricity's random splits put neighbouring half-hours on both
sides, and whether that leakage drives its results is open (the chronological sensitivity measures
drift instead; Table `tab_elec_time`). The dagger marks the hypotheses whose overall verdict would
change if electricity's category were any other category, as computed by the script with the
k-of-4 rule of `analyze.py`: H2a (electricity's *holds* is its only one; with *no difference* there
H2a would be *no difference*) and H2b (*no difference* needs electricity as one of its three).
H1's *contradicted* does not depend on electricity.

Sources: `runs/h-tests/metrics.json` only. 36 macro cells, 12 plain counts.

## Figure `fig_reliability.pdf`: run `fig-reliability`, script `code/fig_reliability.py`

**Caption.** Reliability diagrams of LR, RF and HGB (columns) on each dataset (rows), without
recalibration (filled circles, solid line) and with isotonic regression fitted on the calibration
split (open squares, dashed line). Predictions on the test split are pooled over the 10 seeds
(50,000 rows per curve on adult, bank-marketing and electricity; 13,510 on phoneme) and grouped by
the ECE's own rule: 15 equal-mass bins on P(y=1), tied predictions never split. Each point is one
non-empty pooled bin, at its mean prediction and observed positive rate; marker area is
proportional to the bin's share of rows (1/15 unless ties merge bins). Error bars are plus or minus
one SD across seeds of the positive rate among that seed's rows in the bin (a seed spread; a bin
holding rows from few seeds has a noisy bar: every uncalibrated bin holds rows from all 10 seeds,
but some isotonic bins hold rows from as few as 2, because isotonic's step outputs tie). The dotted
diagonal is perfect calibration. The box in each panel gives, for each calibrator, the plug-in ECE
as mean (SD) over the 10 per-seed values and the mean number of non-empty bins per seed, the
quantities the tests and Table `tab_levels` use. **Bin counts.** These per-seed counts are not the
number of pooled points: pooling over seeds breaks most of isotonic's ties, so isotonic curves show
13 to 15 pooled bins, more than the per-seed mean in the box, while uncalibrated RF shows 11
(bank-marketing) or 13 (adult, phoneme) pooled bins because its outputs tie at multiples of 0.01
(pooled counts are the `*_pooled_bins` metrics of run `fig-reliability`).
ECE values computed on different numbers of bins are not on an identical footing; this is part of
why H1 is read as a statement about the estimator. The bank-marketing panels crowd below 0.2
because 11.7% of its rows are positive. **Electricity**: random splits, possibly leaky across
neighbouring half-hours (see Table `tab_decision`); the curves describe these samples only.
As a check, the script recomputes each seed's plug-in ECE from the prediction files and confirms
that their seed mean equals `describe`'s to within 1e-12 for all 24 curves.

Sources: `results/preds/main/<dataset>_s<seed>.npz` (40 files written by run `main`) and
`runs/describe/metrics.json` (`*_ece_mean`, `*_ece_sd`, `*_ece_bins_mean`).

## Table `tab_levels.tex`: run `tab-levels`, script `code/tab_levels.py`

**Caption.** Metric levels on the test split for every dataset, model and calibrator: plug-in ECE,
Brier score, log-loss (clipped at 1e-6) and ROC-AUC, each as mean (SD) over 10 seeds, and the mean
number of non-empty ECE bins out of 15 ("Bins"). Platt scaling is fitted on the logit of the
clipped probability and is descriptive only. AUC is reported as a control: isotonic regression ties
predictions and can lower AUC, so a Brier change may partly come from lost discrimination.
Bins below 15 mean tied predictions merged bins (uncalibrated RF's outputs near multiples of 0.01,
isotonic's step function); ECE values on fewer bins average over coarser groups, which is one
reason ECE levels are compared across models with care. Phoneme's splits are smaller (training
2,702, calibration and test 1,351), so its ECE noise floor is higher (about 0.03 to 0.04 for a
well-calibrated model, against 0.01 to 0.02 at 5,000 test rows). Electricity's levels come from
random splits of a time series (see Tables `tab_decision` and `tab_elec_time`).

Sources: `runs/describe/metrics.json` only. 276 macro cells; 48 plain cells (Platt's log-loss and
AUC means and SDs, which no claim quotes).

## Table `tab_sensitivity.tex`: run `tab-sensitivity`, script `code/tab_sensitivity.py`

**Caption.** Pre-specified sensitivity analyses; none changes a verdict. Columns as in Table
`tab_decision`. *Panel A*: H1 recomputed on the debiased ECE of Kumar et al. (2019, Def. G.3) on
the same bins, with the same margin and rule, reported descriptively. It removes only about 41% of a
well-calibrated bin's noise floor and close to none of a miscalibrated bin's, so a floor difference
between RF and LR reappears at about 0.6 times its size with the same sign; its agreement with the
plug-in result is not confirmation. *Panel B*: H2a and H2b with isotonic regression refitted on a
stratified 1,351-row subset of each seed's calibration split on adult, bank-marketing and
electricity, with the same frozen base model and test split; phoneme's rows are its main rows,
since its calibration split already has 1,351 rows. Per-dataset categories only; the plan defines no
overall verdict for this sensitivity. It equalises calibration n only, not training n (2,702 against
10,000) or test n (1,351 against 5,000), so a pattern that survives is not attributed to the
dataset. Adult's and bank-marketing's H2a *contradicted* rest on mean Brier rises below 0.001 whose
intervals cross the margin only at their upper ends.

Sources: `runs/h-tests/metrics.json` (Panel A; phoneme rows of Panel B) and
`runs/sens-ncal/metrics.json` (Panel B; `n_cal_sub`).

## Table `tab_elec_time.tex`: run `tab-sensitivity`, script `code/tab_sensitivity.py`

**Caption.** Electricity under a chronological split, **a measure of drift, not a test of
random-split leakage**. Each seed's 20,000-row subsample is sorted by original file row (the time
order) and split 50/25/25 into train, calibration and test; the three models are refitted and the
calibrators fitted on the calibration quarter. Left: plug-in ECE, Brier score and ROC-AUC as mean
(SD) over 10 seeds. Right, for comparison: ECE and Brier under the main random splits (Table
`tab_levels`). Under the chronological split all three uncalibrated models are badly miscalibrated
on the test quarter, and recalibration fitted on the calibration quarter can make the test quarter
worse (for LR, Brier rises from \ElecTimeLrNoneBrier with no recalibration to \ElecTimeLrPlattBrier
with Platt and \ElecTimeLrIsoBrier with isotonic). The run therefore measures drift from the
calibration quarter to the test quarter, mixed with the Victoria fill regime (vicprice, vicdemand
and transfer are constant fill values in the first 17,424 file rows; every seed's training split
holds \TimeVicfillTrainMin to \TimeVicfillTrainMax such rows, the calibration and test splits
\TimeVicfillCalMax and \TimeVicfillTestMax) and with test-quarter dates beyond most of the training
range. It does not show whether random-split leakage drives the main electricity results; that
question remains open. Descriptive; not counted in any k-of-4 verdict.

Sources: `runs/sens-elec-time/metrics.json` (chronological columns) and `runs/describe/metrics.json`
(random-split columns). 126 macro cells across `tab_sensitivity` and `tab_elec_time`.

---

## Macro check

No table script reads `claims.jsonl`: it is not a run output, and any later claim edit would
invalidate the run. Instead, `code/figlib.py` names the macro for each (run, metric) pair by the
claims' convention (`macro_for`), and each fragment lists, in comments at its end, every macro it
used with that source, every plain number with its source and format, and every code it printed
as a word. An unlogged check on 2026-11-19 parsed the four fragments and confirmed, with no
failures, that:

- every macro in a tabular body is listed in the footer, and every listed macro is used;
- each of the 438 macros has a claim whose first support is exactly the listed (run, metric) and
  whose value equals that metric, and is defined in `paper/numbers.tex`;
- none of the 61 plain numbers has a claim backed by its (run, metric).

If a claim is renamed, LaTeX fails on the undefined macro instead of printing a stale number. The
figure prints numbers in its panel boxes from `runs/describe/metrics.json` with the claims' formats
(ECE `.4f`, bins `.1f`), so they read the same as the macros `\<Dataset><Model><Cal>Ece`,
`...EceSd` and `...EceBins`.
