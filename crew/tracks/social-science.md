# Social-science track

An empirical paper that answers a causal or descriptive question with real, public data.

## What a finished paper contains

1. A question about a population, and why the answer matters.
2. Data: source, sample, variable definitions, summary statistics.
3. Empirical strategy: the estimand, the identifying assumption in plain words, and the
   estimating equation.
4. Main result with its uncertainty and its magnitude in real units.
5. Robustness: the checks planned in the design, all reported, including those that
   weaken the result.
6. Limitations, and every deviation from the approved design.

## Design rules

- Choose the estimand before the estimator. Say what comparison identifies it.
- Fix outcome, treatment, controls, sample and standard errors at the design gate. The
  space of defensible specifications is large; searching it after seeing results is how
  false findings are made.
- Plan checks that could fail: placebo outcomes, pre-trends, alternative samples,
  alternative learners or functional forms.
- Cluster standard errors at the level treatment varies.
- Report effect sizes relative to a meaningful baseline (the control mean, a standard
  deviation), not only coefficients.

## Methods and tools

Difference-in-differences, instrumental variables, regression discontinuity, matching and
weighting, double machine learning, synthetic control. Free tooling: StatsPAI,
statsmodels, linearmodels, DoubleML, scikit-learn; Stata through the `stata-code` MCP
server if the user has it.

Skills in this repository the roles can draw on:
[`skills/empirical-research-skills`](../../skills/empirical-research-skills),
[`skills/stata-code`](../../skills/stata-code), and the analysis and writing
[starter kits](../../catalog/STARTER-KITS.md).

## Data

Public sources only, unless the user supplies data: FRED, World Bank, IMF, census and
survey microdata, replication archives. Record the license. Do not commit raw data; the
manifest and its hash let anyone fetch the same file.

## Replication tasks

When the task is to replicate a published estimate, the Scout records the published
number, its standard error, the sample and the specification, with the table number. The
Econometrician follows the published specification as closely as the data allow, reports
the difference, and explains it. Matching the published number is not the goal;
an honest comparison is.
