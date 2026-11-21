# Figure `fig_select.pdf` (run `fig-select`, script `code/fig_select.py`)

Generated from `runs/select/metrics.json` and `runs/select/pseudo_atts.csv`; do not edit by
hand. Any number below that the text also quotes is written there as its claim macro.

**Caption.** Pre-period selection of the primary estimator. Each row is one of the 24
candidates (estimator, donor weighting where it applies, employment outcome E or P, donor pool
D20 or R50), in the design's order. At each of the 6 pseudo-dates (2016Q1, 2016Q2, 2016Q3, 2016Q4, 2017Q1, 2017Q2), California is
treated as if the law had started then, and the candidate's pseudo-ATT is its pooled estimate
over the eight quarters three to ten quarters after the pseudo-date. AB 1228 did not exist
then, so a pseudo-ATT measures how far the candidate's counterfactual misses California's path;
it also contains anything else specific to California in those quarters, such as the rises in
its general minimum wage (design threat T17). Panel (a): RMSE$_c$, the root mean square of the 6 pseudo-ATTs, in
100 × log points of employment (P candidates read on the log-employment scale); the bars start at
zero. Panel (b): the 6 pseudo-ATTs behind each RMSE and their range. The selection run read
data through 2019Q4 only. The selected candidate, `DDT-POPW-E-R50` (difference in differences with a linear trend (DDT), population-weighted donor mean, donor pool R50 (the other 49 states and DC)),
is the one with the smallest RMSE (black bar, filled markers). No other candidate has the same RMSE at four decimals, so the tie-break was not used.

**What the figure does not show.** The RMSEs are a pre-period placebo criterion, not estimates
with a sampling interval, so no confidence interval is drawn; panel (b) shows their spread. The
6 pseudo-dates are consecutive quarters whose eight-quarter windows overlap, so the
6 pseudo-ATTs are not 6 independent draws, and a small difference between two RMSEs is not
evidence that one estimator is better. The figure says nothing about any quarter after
2019Q4 and nothing about the effect of the law.
