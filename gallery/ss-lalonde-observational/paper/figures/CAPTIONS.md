# Figure and table captions (ss-lalonde-observational)

Each figure and table below was built by a script under `code/`. Each script ran through
`crew.py run --kind analysis` with the role `figures-ra`; the run id is given for each item.
The scripts read only files that logged runs wrote, all declared with `--input`. They read no
claim file and nothing under `data/raw`, and they re-estimate nothing. No number was typed by
hand. Figure labels are printed from the run metrics, rounded as the claims' macros are
(`,.0f`; the primary lower bound `,.1f`, as `\PrimaryCiLow`). Every number in the table
fragment is a claim macro, so the fragment needs `\input{numbers.tex}` and
`\usepackage{booktabs,icomma}`. The fragment is a bare `tabular`; the Writer adds the float,
the caption below and the label. Where a caption needs a number, it is written as the macro
to use. Dollars are 1982 dollars, and every interval is a 95% confidence interval.

All three figures share one palette (Okabe-Ito) and one style. Every distinction that matters
also has a grayscale cue: position, marker shape or fill, hatching, line style or a text
column. All figures are vector PDFs with embedded STIX fonts at 6.6 to 8.5 pt. No axis is
cropped to exaggerate a difference; the two non-linear axes (log and square-root) are labelled
as such.

Wording rule for every caption and for the text around them: H3 failed, so the primary
estimate is a **statistical contrast between the treated men and comparable CPS men, not an
effect of the program**. Call it a "contrast", never an "effect" or an "impact".

---

## Figure `fig_overlap.pdf`: run `fig-overlap`, script `code/fig_overlap.py`

**Caption.** Overlap of the cross-fitted propensity score, NSW-treated men against CPS-1 men.
$\bar m(X)$ is the out-of-fold propensity of the primary specification (L2-penalized logit on
the 14-term basis $B(X)$, 5 folds $\times$ 5 repetitions), averaged over the repetitions and
unclipped. It was computed from covariates and treatment only, before the design gate. The
horizontal axis is $\log_{10} \bar m$, because almost every CPS man has a propensity far below
0.01. The bars show the percent of each group in each bin of width 0.25 on the log scale. The
\PrimaryNTreated{} treated men are drawn above the axis (solid bars) and the
\PrimaryNControl{} CPS men below it (hatched bars). Percents are shown instead of counts,
because counts would hide the treated men. The dashed lines mark the lowest and highest
treated $\bar m$, and the shaded region outside them is the trimming region of the robustness
check rob-trim. That check drops the \TrimNControlDropped{} CPS men in the region, all of them
below the lowest treated value, and keeps \TrimNControlKept{} CPS men and every treated man.
The bin edges are laid out from the lowest treated value, so no bin straddles the cutoff, and
the script checks that the region holds exactly rob-trim's count. The cutoff rests on a single
treated man's propensity, and the dropped men carry only \TrimDroppedWeightShare\% of the
control weight $\bar m/(1-\bar m)$. No treated man has $\bar m > 0.9$ and no unit is clipped
(rules O1 and O2). The weighted CPS men have a Kish effective sample size of
\OverlapKishEss{}. The figure shows shares of units, not estimates, so it has no error bars.

Sources: `runs/diag-overlap/propensity.csv` ($\bar m$ for every unit) and
`runs/diag-overlap/metrics.json` (arm sizes, treated $\bar m$ range, rob-trim counts).

## Figure `fig_forest.pdf`: run `fig-forest`, script `code/fig_forest.py`

**Caption.** The primary contrast, every planned robustness estimate and the H3 placebo, each
with its 95% confidence interval. Panel (a), outcome 1978 earnings: the primary estimate
(square) is the cross-fitted AIPW ATT contrast, \PrimaryEffect{} (SE \PrimarySe{}, 95% CI
[\PrimaryCiLow, \PrimaryCiHigh]), over all \PrimaryNTreated{} treated men. Because the
placebo failed (panel b), this is a statistical contrast between the treated men and
comparable CPS men, not an effect of the program. Its lower bound lies within cross-fitting
noise of zero. Taken alone, \PrimaryNRepsCiIncludeZero{} of the 5 cross-fitting repetitions
give 95% intervals that include zero (lower bounds \PrimaryRepZeroCiLow,
\PrimaryRepOneCiLow, \PrimaryRepTwoCiLow, \PrimaryRepThreeCiLow{} and
\PrimaryRepFourCiLow), so the contrast is never called significant without this caveat. The
rows below are in the order of the analysis plan. The two right-hand columns apply the
design's disagreement rule, which was fixed before any outcome was read. "Can trigger" says
whether the row can trigger the rule. "Did it?" is the run's own logged flag: a row triggers
when its H1 decision (95% CI entirely above zero or not) differs from the primary's. The rows
that trigger are control-only trimming, parametric nuisances, and covariate set (a), which
drops race, ethnicity and degree status, so the conclusion is not robust to these checks. The
random-forest row does not trigger. The Hajek IPW row (yes*) can trigger only if its point
estimate lies outside the primary's 95% CI; it does not, so it does not trigger. Filled dots
can trigger the rule. Open dots change the conditioning set, the estimator or the estimand,
and are reported but never trigger: covariate set (b), the OLS coefficient and the
conditional difference-in-differences contrast on re78 $-$ re74, which assumes conditional
parallel trends instead of unconfoundedness. The dashed blue line is the experimental
benchmark, \$\HTwoBenchmarkValue{} (Dehejia and Wahba 1999), drawn only for reference (H2,
descriptive). No row is compared with it, ranked by it or chosen by it. Panel (b), outcome
1975 earnings (the H3 placebo): the same estimator, conditioning on the covariates without
re75 and u75, gives \PlaceboEffect{} (SE \PlaceboSe{}, 95% CI [\PlaceboCiLow,
\PlaceboCiHigh]). The interval excludes zero, so H3 fails by the rule that takes precedence.
The gray band is the pass band of $\pm 900$, half the benchmark, fixed at the question gate.
Treated men earned less in 1975 than comparable CPS men. This is consistent with the
pre-program earnings dip and with re74 being measured over different months for the two
groups, so the failure is not proof that the primary contrast is biased. It does mean the
primary result may be worded only as a contrast. CPS re75 is top-coded
(\PlaceboCpsReSeventyfiveTopcoded{} men at the maximum) and NSW re75 is not. The intervals use
influence-function standard errors for the AIPW rows (5 folds $\times$ 5 repetitions), HC2
for OLS, and a 999-draw bootstrap for the Hajek IPW (SE \IpwSe). $n = \PrimaryN$ in every row
except control-only trimming, which keeps \TrimNControlKept{} CPS men and all treated men.

Sources: `runs/{main-aipw,rob-trim,rob-learners,rob-covsets,rob-estimators,rob-diff74,placebo-re75,h2-benchmark}/metrics.json`.

## Figure `fig_sensitivity.pdf`: run `fig-sensitivity`, script `code/fig_sensitivity.py`

**Caption.** Sensitivity of the primary contrast to an unobserved binary confounder $U$, in
the model of Imbens (2003), run sens-imbens. The horizontal axis is $R^2_D$, the share of the
residual latent variance of participation that $U$ explains. The vertical axis is $R^2_Y$, the
share of the residual variance of re78 that $U$ explains. Both axes use a square-root scale,
so that small values near the origin are visible; tick labels are $R^2$ values. The shading
and contour lines show the larger $|$bias$|$ of the two signs of $U$'s outcome effect. These
values come from the 64 EM fits on the planned grid (gray dots), interpolated linearly
between grid points. The dashed line is the planned target $t_0 = \$\SensTargetZero$, the
shift that moves the nearer 95% bound to zero and so flips the H1 decision. It is tiny because
the lower bound sits just above zero. The solid line is the point estimate, \PrimaryEffect: a
$|$bias$|$ that large would move the point estimate itself to zero. It is drawn for
orientation only and is not part of the reading rule. The orange diamond is the diagonal
breakdown point $R^2_{*,0} = \SensRsqZero$ on the diagonal $R^2_D = R^2_Y$: a confounder
that explains this share of the residual variance in both equations would flip the H1 decision.
The dots are the benchmark covariate groups, placed at the strengths that dropping each group
from $B(X)$ implies. The $|$bias$|$ printed next to each is the EM fit at that point, which is
what the reading rule uses. It is not a reading of the interpolated surface, which is coarse
near the axes: hispanic lies below the interpolated $t_0$ line, but its fitted $|$bias$|$,
\$\SensBenchHispBias, exceeds $t_0$. The conclusion is not robust to a confounder as strong as
earnings75 ($|$bias$|$ \$\SensBenchEarnSeventyfiveBias), so the positive contrast could be
produced by unobserved selection of that strength, for example a 1976 earnings shock. It is
also not robust to confounders as strong as age (\$\SensBenchAgeBias), education
(\$\SensBenchEducBias), hispanic or earnings74 (\$\SensBenchEarnSeventyfourBias; re74 is
measured over different months for the two groups). The open squares on the vertical axis are
black, married and no-degree. Their $R^2_D$ is floored at zero, which means that dropping the
group did not lower the variance of the fitted logit index. The rule's "robust" verdicts for
these three groups are therefore artifacts of the floor and carry no information about how
strong race, marital status or degree are as confounders. The conclusion is not described as
robust to any of them. age and earnings75 have $R^2_D$ above the grid's 0.30, so the
horizontal axis extends past the grid, and the hatched region has no surface. The bias is
computed within the parametric Imbens model and transferred additively to the AIPW estimate
as an approximation. That model's $U$-free estimate is \SensTauZerozero{}, against the AIPW
estimate of \PrimaryEffect. $n = \PrimaryN$. The figure plots point values from the fits, so
it has no error bars.

Sources: `runs/sens-imbens/metrics.json` (grid, diagonal, $t_0$, $R^2_{*,0}$, benchmark points
and their $|$bias$|$, the floored $R^2_D$ values).

---

## Table `tab_main.tex`: run `tab-main`, script `code/tab_main.py`

**Caption.** Primary contrast (H1), placebo (H3), robustness estimates and the descriptive
comparison with the experimental benchmark (H2). 1982 dollars; 95% confidence intervals. Panel
A: cross-fitted AIPW for the ATT on 1978 earnings, with an L2-logit propensity on $B(X)$ and a
gradient-boosted control outcome model, 5 folds $\times$ 5 repetitions and
influence-function standard errors (SE \PrimarySe{}); $n = \PrimaryN$. By the fixed rule H1
holds, because the interval lies above zero, but only just: \PrimaryNRepsCiIncludeZero{} of
the 5 single-repetition intervals include zero, so the decision lies within cross-fitting
noise. Because H3 failed, the estimate is a statistical contrast between the groups, not an
effect of the program. Panel B: the same estimator with outcome re75, conditioning on the
covariates without re75 and u75 (SE \PlaceboSe). The interval excludes zero, so H3 fails. The
failure is consistent with the pre-program earnings dip and with the different meaning of re74
in the two groups, so it is not proof of bias in panel A. Panel C: every planned robustness
estimate is reported; the primary estimate is never replaced. Panel D: the primary estimate
minus the benchmark of Dehejia and Wahba (1999, Table 3). This is descriptive: no test, and
closeness to the benchmark is never used to choose or rank estimators. $^{a}$ The design's
disagreement rule. A row that can trigger it triggers when its H1 decision differs from panel
A's. Each "Triggered" cell is the run's own logged flag; "--" marks rows that change the
assumption or the estimand and never trigger. Because the trimming, parametric-nuisance and
covariate-set (a) rows trigger, the abstract must say that the conclusion is not robust to control-only trimming, to dropping race, ethnicity and
degree status, or to parametric nuisance models. $^{b}$ Drops the \TrimNControlDropped{} CPS
men whose $\bar m$ lies outside the treated men's range and keeps \TrimNControlKept{} and
every treated man. It re-fits the nuisance models on the kept men. The dropped men carry
\TrimDroppedWeightShare\% of the control weight, so the check does not test reliance on them.
$^{c}$ Set (a) conditions on age, educ, married, re74, re75, u74 and u75, so it drops black,
hisp and nodegree. Set (b) drops re74 and u74, which are measured over different months for
treated and CPS men. $^{d}$ The Hajek IPW row (bootstrap SE \IpwSe) triggers only if its point
estimate lies outside panel A's 95% CI. $^{e}$ A different estimand and assumption: the ATT on
re78 $-$ re74 under conditional parallel trends given the time-invariant covariates. $^{f}$ The
difference $\pm 1.96$ times a combined SE of \HTwoSeCombined{},
$\sqrt{\mathrm{SE}^2 + \HTwoBenchmarkSe^2}$. This SE ignores the positive covariance that comes
from the \PrimaryNTreated{} treated men the two estimates share, so it overstates the
uncertainty and the band is too wide.

Sources: `runs/{main-aipw,placebo-re75,rob-trim,rob-learners,rob-covsets,rob-estimators,rob-diff74,h2-benchmark}/metrics.json`.
The macro names are fixed in the script by (run, metric), and the metric value behind each row
is written in the fragment as a comment. A separate check outside the run compared all 36
macros in the fragment with `claims.jsonl` and `paper/numbers.tex`: every one exists and
equals its run's metric.
