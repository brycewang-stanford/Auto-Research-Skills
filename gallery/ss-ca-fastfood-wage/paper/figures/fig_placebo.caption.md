# Figure `fig_placebo.pdf` (run `fig-placebo`, script `code/fig_placebo.py`)

Generated from `runs/h2-emp/placebos.csv`, `runs/h2-emp/metrics.json` and `runs/level-mde/metrics.json`; do not edit by hand.
Any number below that the text also quotes is written there as its claim macro.

**Caption.** California's pooled estimate for H2 against the placebo estimates of its 50
donors. Outcome: seasonally adjusted log employment, NAICS 722513; estimator `DDT-POPW-E-R50`
(difference in differences with a linear trend (DDT), population-weighted donor mean, donor pool R50 (the other 49 states and DC)); base quarter 2023Q3, post window 2024Q2-2026Q1;
values in 100 × log points. Each donor's placebo is the same estimate with that donor treated and
the other 49 donors as its pool. Open markers: the placebo estimate; filled markers: the
same estimate times sqrt(pop_j / pop_CA), with populations at the base quarter. SE_n is the
root mean square of the unscaled placebos and SE_s that of the scaled ones; the inference uses
SE = max(SE_s, SE_n), here SE_n (unscaled), and the dashed lines mark ± SE. California's 90% interval
(thick) and 95% interval (thin) are estimate − c × SE with the critical values of run
level-mde's H2 statistic (t at ν = 14.1 with the decision-set quantile as a floor),
as in run h2-emp. Donors are sorted by their scaled placebo.

**What the figure does not show.** The donors' placebo estimates are not effects of any
policy; they show how large an estimate this procedure gives where no fast-food law applies.
The figure is not a permutation test: California's rank among the placebos is not the
inference the design uses, and no p-value is read from it. The H2 label comes from the 95% and
90% intervals by the rule of hypotheses[1] (run h2-emp), not from this figure.
