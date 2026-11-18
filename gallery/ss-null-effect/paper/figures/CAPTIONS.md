# Figure and table captions (ss-null-effect)

Each figure and table below was built by a script under `code/`. Each script ran through
`crew.py run --kind analysis`, and the run id is given for each item. The scripts read only
files written by logged runs, declared with `--input`, and no number was typed by hand.
Table cells the paper quotes are written as the claims' macros, so the fragments need
`\input{numbers.tex}`. They also need `\usepackage{booktabs,icomma}`: `icomma` keeps the
thousands comma inside math mode (`$1,716$`) without adding a space. Each fragment is a bare
`tabular`. The Writer adds the float, the caption below and the label. `tab_main` and
`tab_secondary` are wide and fit the text block with `\footnotesize` or `\resizebox`.
Where a caption below needs a number, it is written as the macro to use.

All three figures share one palette (Okabe-Ito) and one style. Every distinction that
matters also has a grayscale cue: position, marker fill, hatching or line style. All
figures are vector PDFs with embedded STIX fonts at 7 to 8.5 pt, and none crops an axis.
Earnings are in the file's nominal dollars, because the price year is not documented.

---

## Figure `fig_propensity.pdf`: run `fig-propensity`, script `code/fig_propensity.py`

**Caption.** Overlap of the cross-fitted propensity score. Bars count people per bin of
width 0.05 of $\bar m(X)$. $\bar m(X)$ is the out-of-fold propensity from the primary
specification (L2-penalized logit on $B(X)$, 5 folds $\times$ 5 repetitions), averaged
over the 5 repetitions and unclipped. Treated people (\PrimaryNTreated) are counted above
the axis (solid bars) and controls (\PrimaryNControl) below it (hatched bars). The dashed
lines at 0.1 and 0.9 mark the trimming bounds of the trimmed-overlap check and the overlap
rule O1, which allows no treated person above 0.9. No treated person lies above 0.9. A
share \OverlapShareOutside{} of all people lies outside $[0.1, 0.9]$, almost all of them
controls below 0.1 (Table `tab_balance`). The figure shows counts, not estimates, so it
has no error bars. The scores were computed outcome-blind, before the design gate.

Sources: `runs/diag-overlap/propensity_hist.json` (bin edges and counts) and
`runs/diag-overlap/metrics.json` (arm sizes). The script checks that the bins add up to
every unit in each arm.

## Figure `fig_forest.pdf`: run `fig-forest`, script `code/fig_forest.py`

**Caption.** Primary estimate and every planned robustness estimate, with the equivalence
margin. Each row is one specification in the order of the analysis plan, and all rows are
drawn alike. The dot is the point estimate, the thick bar the 90% confidence interval (the
interval used by the TOST equivalence test) and the thin bar the 95% confidence interval.
The OLS row has no thick bar, because rob-estimators logged no 90% interval for OLS. The
dashed lines and the gray band mark $\pm M$, $M = \$\EquivMargin$. $M$ is 10% of
participants' mean 1975 earnings and was fixed before any outcome was read. The solid gray
line marks zero. Filled dots are ATTs on 1978 earnings in the full sample of \PrimaryN.
Open dots are different estimands. The trimmed-overlap ATT is taken over the \TrimN{}
people with $\bar m \in [0.1, 0.9]$. The conditional difference-in-differences row
estimates the ATT on re78 $-$ re74 under conditional parallel trends from 1974 to 1978,
with time-invariant covariates only. This last estimate (\DiffSeventyFourEffect, 95% CI
[\DiffSeventyFourCILow, \DiffSeventyFourCIHigh]) rejects zero and lies outside $\pm M$.
Its bias is upward if enrolees' 1974 earnings were already transitorily depressed, and
downward if they were on a permanently lower growth path. The plan fixed both readings in
advance, and the runs cannot tell them apart. The right column prints each estimate and its
95% CI, rounded to dollars. The intervals use influence-function standard errors for the
AIPW rows (5 folds $\times$ 5 repetitions), HC2 standard errors for OLS, and a 999-draw
bootstrap standard error for the Hajek IPW. The x-axis covers every interval and $\pm M$.
The descriptive measure of selection on 1975 earnings (select-re75) is not an estimate of
this ATT, so it is not plotted; it is in Table `tab_main`, panel B.

Sources: `runs/{main-aipw,rob-trim,rob-covsets,rob-learners,rob-estimators,rob-diff74}/metrics.json`.

## Figure `fig_sensitivity.pdf`: run `fig-sensitivity`, script `code/fig_sensitivity.py`

**Caption.** Sensitivity of the primary estimate to an unobserved binary confounder $U$
(the model of Imbens 2003). The horizontal axis is $R^2_D$, the share of the residual
latent variance of enrolment explained by $U$. The vertical axis is $R^2_Y$, the share of
the residual variance of re78 explained by $U$. The shading and the contour lines show the
larger $|$bias$|$ of the two signs of $U$'s outcome effect. These values come from the 64
EM fits on the planned grid (gray dots), interpolated linearly between grid points. Three
contour lines mark the planned targets. The dotted line is $t_E = \$\SensTargetEquiv$, the
shift that would end equivalence. The dashed line is $t_0 = \$\SensTargetZero$, the shift
that would move the nearer 95% bound to zero. The solid line is $M = \$\SensTargetMargin$.
Orange diamonds on the dotted diagonal ($R^2_D = R^2_Y$) are the breakdown points of the
reading rule: \SensRsqEquiv, \SensRsqZero{} and \SensRsqMargin. Black dots are the nine
benchmark covariate groups. Each is placed at the strength that dropping the group from
$B(X)$ implies. Panel (a) shows the full grid. Panel (b) enlarges its lower-left corner,
where eight of the nine groups lie. The $|$bias$|$ printed next to each group is the EM fit
at that point, which is what the reading rule uses, not a reading of the interpolated
surface. A confounder as strong as earnings75 ($|$bias$|$ \$\SensBenchEarnSeventyFiveBias)
exceeds every target, so the conclusion is not robust to unobserved selection of that
strength. A confounder as strong as earnings74 (\$\SensBenchEarnSeventyFourBias) exceeds
$t_E$ only. The bias is computed within the parametric Imbens model and transferred
additively to the AIPW estimate as an approximation. That model's U-free estimate is
\SensTauZero, against the AIPW estimate of \PrimaryEffect. The earnings74 verdict for
$t_E$ holds by less than this gap. $n = \PrimaryN$. The figure plots point values from
the fits, so it has no error bars.

Sources: `runs/sens-imbens/metrics.json` (grid, diagonal $R^2_*$, targets, benchmark
points and their $|$bias$|$).

---

## Table `tab_balance.tex`: run `tab-balance`, script `code/tab_balance.py`

**Caption.** Covariate balance and overlap (outcome-blind; computed before the design
gate). The means are raw arm means. The standardized difference is the difference in means
divided by $\sqrt{(s_1^2 + s_0^2)/2}$, with unweighted group SDs, for every term of the
propensity basis $B(X)$. In the ATT-weighted column, controls are weighted by
$w = m/(1 - m)$. The design's balance rule B1 requires every weighted $|$difference$|$ to
be below 0.10, and it holds. The Imbens-Wooldridge normalized differences in the notes use
$\sqrt{s_1^2 + s_0^2}$, so they equal these unweighted values divided by $\sqrt 2$. Squared
terms have no mean column. $^{a}$ Midwest is the reference category, not a term of
$B(X)$; its difference is shown for information. $^{b}$ $w$ is formed from each
repetition's clipped propensity and averaged over the 5 repetitions. The overlap panel
uses $\bar m(X)$, as in Figure `fig_propensity`. $n = \PrimaryN$.

Sources: `data/derived/prep_metrics.json` (arm means, from the data-prep run
`prepare-covariates`), `runs/diag-overlap/metrics.json`, `claims.jsonl` (macros). The
script checks that both runs' unweighted differences agree.

## Table `tab_main.tex`: run `tab-main`, script `code/tab_main.py`

**Caption.** ATT of enrolment on 1978 earnings: the primary estimate and every planned
robustness estimate (panel A, the same rows as Figure `fig_forest`), and a descriptive
measure of pre-program selection (panel B). The primary estimator is cross-fitted AIPW for
the ATT, with gradient-boosted outcome and L2-logit propensity models, 5 folds $\times$ 5
repetitions, and influence-function standard errors. $p$ is the two-sided $p$-value for
ATT = 0 (H1). $p_{\mathrm{TOST}}$ is the equivalence $p$-value for $|$ATT$| < M$ (H1b). It
is below 0.05 exactly when the 90% CI lies within $\pm M$. "Rejects 0" and "Within
$\pm M$" are the run's own H1 and H1b decisions. "--" means that the run did not compute
the quantity. The OLS row has no 90% CI, TOST or equivalence decision, and the Hajek IPW
row has no $p$-values; its decisions come from its bootstrap-SE intervals. The H1b
decision holds under unconfoundedness given the eleven covariates. It is not robust to a
confounder as strong as earnings75 (Table `tab_sensitivity`). $^{a}$ A different
estimand: the ATT among the \TrimN{} people (\TrimNTreated{} treated) with
$\bar m \in [0.1, 0.9]$. $^{b}$ Set (a) conditions on age, educ, married, re74, re75,
unemp74 and unemp75. Set (b) conditions on all eleven covariates except re74 and unemp74.
$^{c}$ A different estimand and assumption: the ATT on re78 $-$ re74 under conditional
parallel trends from 1974 to 1978, given the time-invariant covariates (age, educ,
married, urban, region, children, health\_limit). Its bias is upward if enrolees' 1974
earnings were transitorily depressed, and downward if they were on a lower growth path.
The sign of the bias is not known. $^{d}$ The same estimator with re75 as the outcome,
conditioning on the 1974 covariates. It measures how far enrolees' 1975 earnings fell
below comparable non-enrolees'. The documented pre-program dip makes this nonzero whether
or not the identifying assumption holds, so it is neither a test of the assumption nor
support for the primary result, and no $p$-value is reported.

Sources: `runs/{main-aipw,rob-trim,rob-covsets,rob-learners,rob-estimators,rob-diff74,select-re75}/metrics.json`,
`claims.jsonl` (macros).

## Table `tab_secondary.tex`: run `tab-secondary`, script `code/tab_secondary.py`

**Caption.** Secondary outcome family (H2). Each outcome is estimated with the primary
estimator on the same folds and propensity fits, with $n = \PrimaryN$ and no missing or
inadmissible values. The Romano-Wolf step-down $p$-values and the single-step max-$t$
simultaneous 95% intervals come from one Gaussian multiplier bootstrap on the influence
functions, with the nuisance models not re-fitted. An outcome counts as "detected" if and
only if its Romano-Wolf $p < 0.05$. None is detected. The unadjusted $p$-values are shown
for reference only. No outcome with an unadjusted $p$ below 0.05 but a Romano-Wolf $p$
above it (benefits78) may be described as affected. The max-$t$ intervals are the
intervals reported for this family, and per-outcome unadjusted intervals are not shown. The
bootstrap uses the influence function averaged over repetitions, so its scale omits the
between-split variance in the standard errors. The Romano-Wolf $p$-values and max-$t$
intervals are therefore slightly anti-conservative, about 4% narrower, relative to the SE
column. $^{a}$ An integer scale assumed to be $[0, 10]$; the brief documents no scale.
$^{b}$ In units of the SD of wellbeing78 among controls (\SecWellbeingControlSD{} scale
points).

Sources: `runs/secondary-family/metrics.json`, `claims.jsonl` (macros).

## Table `tab_sensitivity.tex`: run `tab-sensitivity`, script `code/tab_sensitivity.py`

**Caption.** Imbens (2003) sensitivity analysis for the primary estimate. Panel A lists the
three planned targets and the diagonal breakdown point $R^2_*$, the smallest
$R^2_D = R^2_Y$ at which $|$bias$|$ reaches the target for either sign, interpolated
linearly between diagonal points. Panel B lists the nine benchmark covariate groups. For
each group, $R^2_D$ and $R^2_Y$ are the strengths implied by dropping the group from
$B(X)$. $|$bias$|$ is the larger of the two signs from the EM fit at that point. The
conclusion for a target is called robust to a group if $|$bias$|$ is below the target for
both signs. The conclusion is not robust to a confounder as strong as earnings75 for any
target, so unobserved selection of that strength could produce the result. For the
equivalence target $t_E$, it is also not robust to earnings74. That verdict
(\SensBenchEarnSeventyFourBias{} against \SensTargetEquiv) holds by less than the gap
between the Imbens model's U-free estimate and the AIPW estimate, so it lies within the
approximation error. Groups are ranked by $|$bias$|$ at their benchmark point. age and
educ nearly tie. $n = \PrimaryN$; the model and the grid are as fixed in the design.

Sources: `runs/sens-imbens/metrics.json`, `claims.jsonl` (macros).
