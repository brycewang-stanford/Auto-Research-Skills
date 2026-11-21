# Figure `fig_event.pdf` (run `fig-event`, script `code/fig_event.py`)

Generated from `runs/event-path/event_path.csv`, `runs/event-path/metrics.json`, `runs/level-mde/metrics.json` and `runs/h1-wage/metrics.json`; do not edit
by hand. Any number below that the text also quotes is written there as its claim macro.

**Caption.** Quarterly gap between California and its estimated counterfactual,
2014Q1–2026Q1, for the primary candidate `DDT-POPW-E-R50`:
difference in differences with a linear trend (DDT), population-weighted donor mean, donor pool R50 (the other 49 states and DC). Panel (a) is the candidate's employment outcome
(seasonally adjusted log employment, NAICS 722513); panel (b) is the seasonally adjusted log average weekly wage, NAICS 722513, with the same estimator,
weighting and pool, its trend fitted on the wage. Each point is California's outcome minus
the counterfactual the estimator builds from the donors, fitted with the base quarter 2023Q3, in 100 × log points (close to percent for small values). The shaded band
is a pointwise 95% interval, gap − c_hi(0.975) SE to gap − c_lo(0.025) SE, where SE =
max(SE_s, SE_n) comes from the donors' placebo gaps at that quarter and the critical values are
those of the selected candidate's H2 statistic from run level-mde (t at ν = 14.1
with the decision-set quantile as a floor; c_hi(0.975) = 2.14, c_lo(0.025) =
−2.14); both panels use these critical values, as the run does. Hatched: COVID
quarters (2020Q1–2021Q4), excluded from every fit window. Light shading: the post window
(2024Q2–2026Q1). Dashed line: 2022Q3, the quarter AB 257 was enacted
(September 2022). Dotted line: 2023Q4, the first quarter after AB 1228 was
signed (28 September 2023). The quarters after the last fit-window quarter (2023Q3)
and before the post window (2023Q4, 2024Q1) are in neither window.

**Panel (b) and the H1 test.** H1 is decided by run h1-wage's one-sided 5% test of the pooled
wage estimate, which rejects when t exceeds H1's own c_hi(0.95) = 3.45 (t at
ν = 14.4 with the decision-set quantile as a floor; its c_hi(0.975) = 4.32).
Panel (b)'s bands do not use these values: they use the H2 critical values above, as analysis
plan item 16 specifies, so a band's lower edge lies above zero when gap / SE exceeds
c_hi(0.975) = 2.14. That threshold is below H1's c_hi(0.95), so on the upper side the wage bands are narrower than the H1 test: a quarter's band can exclude zero at a t value the H1 test would not reject. A band in panel (b) that excludes zero is therefore
not evidence against the H1 verdict, which comes from run h1-wage alone.

**Reading (estimator case DDT).** 2022Q1-2023Q3 gaps are residuals around the fitted trend (curvature only); the 2014-2019 segment is outside the trend's fit.

**What the figure does not show.** The bands are pointwise, not simultaneous, so a quarter
whose band excludes zero is not a test that the path is zero, and no pre-period part of the figure is a pre-trend test. The figure is report-only: no hypothesis label is read from
it. The pooled post-window estimates, their intervals and the hypothesis labels come
from runs h2-emp (employment) and h1-wage (wage); the per-quarter bands here use per-quarter
standard errors and are not those intervals.
