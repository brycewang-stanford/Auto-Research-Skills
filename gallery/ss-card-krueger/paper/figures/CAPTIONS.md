# Figure and table captions (ss-card-krueger)

Each table and figure below was built by a script under `code/`. Each script ran through
`crew.py run --kind analysis` after the results gate, and the run id is given for each
item. The table and figure scripts read only files written by logged runs, declared with
`--input`. No number was typed by hand.

Table cells that the paper quotes are written as the claims' macros, so the fragments need
`\input{numbers.tex}` and `\usepackage{booktabs}`. Each fragment is a bare `tabular`. The
Writer adds the float, the caption below and the label. Both tables are wide and fit the
text block with `\footnotesize` inside `\resizebox{\textwidth}{!}{...}` (checked with
pdflatex on 2026-11-19, no errors or overfull boxes).

Where a caption below needs a result, it is written as the macro to use. The 0.05
tolerance is the pre-registered H1 constant (`verdict.TOLERANCE` in `code/verdict.py`), and
1.96 is the normal 97.5% quantile; neither is a result.

**Published values.** The published numbers in Table `tab_replication` come from run
`pub-values` (`code/pub_values.py`). It parses the Scout's transcription of Card and Krueger
(1994) Tables 3 and 4 in `sources/notes.md` (section 1, read from the page images, p. 780),
declared as `--input`. It fails unless each of the 15 published H1 targets it parses equals
the value the verdict run judged with (`runs/verdict/metrics.json`, `*_pub`). Rows 1, 2
and 5 and the Table 4 SE of regression, mean and SD of the dependent variable come only
from that transcription. If `sources/notes.md` is edited, `crew.py validate` will report
that the input changed. Then `pub-values` and `tab-replication` must be rerun with
`--replace`.

**Wording rules.** Row 3's labels follow runs/NOTES.md after results-r1 and results-r2:

- The row-3 points are "within tolerance, not at published precision". The 0.0064 DiD gap
  is not rounding. Its source is unidentified.
- The row-3 SE column is "SE construction not identified". The NJ-PA SE is within the
  tolerance by 0.00003 only, and this must not be read as the headline SE being reproduced.
- Only H1 targets carry a verdict. No tolerance is applied to rows 1, 2 and 5 or to the
  other Table 4 rows (plan.json analysis_plan step 8: no judgment outside the verdict run).

**Macro check.** Neither table script reads `claims.jsonl`. Each one names the macro for the
(run, metric) pair it reads and lists every macro used, with that source, in comments at the
end of the fragment. An unlogged check on 2026-11-19 parsed both fragments (79 macros: 46 in
`tab_replication` and 33 in `tab_h2`). It confirmed three things for each macro:

- the macro is defined in `paper/numbers.tex`;
- its claim's first support is exactly the listed (run, metric);
- the claim's value equals that metric.

There were no failures. The set of macros used in each fragment equals the set listed in its
footer.

**Determinism.** All four scripts were run again in a scratch copy of the workspace. The
outputs and metrics were byte-identical to the logged ones.

**Style.** The figure uses the Okabe-Ito palette. Every distinction also has a grayscale
cue: hatching, line style or shading. It is a vector PDF with embedded STIX fonts at 7 to
8.5 pt. Both y-axes start at zero, and no axis is cropped.

---

## Table `tab_replication.tex`: run `tab-replication`, script `code/tab_replication.py`

**Caption.** Published and replicated estimates of Card and Krueger (1994), Table 3, rows
1-5, and Table 4, column (i). The replication uses the authors' public file (njmin.zip, 410
stores) and the sample and variable rules of their check.sas.

- **Publ.** The published value, printed to the published precision.
- **Repl.** The replicated value, unrounded in the comparison and printed to two decimals
  (four for the mean of $\Delta$FTE).
- **$|\Delta|$.** The absolute difference between the unrounded replicated value and the
  published value.
- **Tol.** The pre-registered H1 tolerance: a target is met if $|\Delta| \le 0.05$ after
  rounding $|\Delta|$ to six decimals. $N$ must match exactly.
- **Status.** The verdict run's reading of each H1 target: rows 3 and 4 (H1(a), H1(b)) and
  the Table 4 $N$, NJ coefficient and SE (H1(c)). "Report only" marks a published value that
  is not a target. Its $|\Delta|$ is shown for comparison, but no tolerance is applied.

Samples:

- Rows 1-3 use all stores with employment data in a wave: wave 1 \NWOnePa{} PA and
  \NWOneNj{} NJ stores; wave 2 \NWTwoPa{} PA and \NWTwoNj{} NJ stores.
- Row 4 uses the balanced sample of \NBalPa{} PA and \NBalNj{} NJ stores with employment
  data in both waves. Permanently closed stores are in it with wave-2 employment 0.
- Row 5 adds the temporarily closed stores with wave-2 employment 0.
- Table 4 column (i) is an OLS regression of the change in FTE employment on an NJ dummy,
  on \RegN{} stores (\RegNNj{} NJ, \RegNPa{} PA).

Standard errors:

- Table 3: the within-state SEs allow for the correlation between the two waves at the same
  store (method S1, fixed at the design gate). The NJ $-$ PA SE is
  $\sqrt{SE_{PA}^2 + SE_{NJ}^2}$.
- Table 4: the conventional OLS SE.

Notes:

- **(a)** Row 3's three points are within the tolerance, but not at published precision. At
  two decimals the replicated row 3 reads $-2.17$ / 0.59 / 2.75 (PA / NJ / NJ $-$ PA)
  against the published $-2.16$ / 0.59 / 2.76. The published entries imply unrounded NJ and
  PA changes that the replicated values lie outside, so the DiD gap (\HOneADidAbsdiff) is
  not rounding. Its source is not identified. Rows 1-3 share the same wave samples, and the
  replicated row 3 equals row 2 minus row 1, so the gap lies in the unbalanced wave means.
- **(b)** SE construction not identified. All three row-3 SEs are below the published
  ones. The NJ SE misses the tolerance (\HOneANjSeAbsdiff). The NJ $-$ PA SE is within it
  by 0.00003 only (\HOneADidSeAbsdiff), because the low NJ SE lowers it. Every row-4 SE
  matches. H1(a) as a whole is therefore not reproduced (\HOneAMet{} = 0), while its points
  are (\HOneAPointMet{} = 1).
- **(c)** $N = 357$ is a data check, not a blind test: the count was observed at data prep
  with the check.sas rule.
- The published mean of $\Delta$FTE, $-0.237$, is just outside the rounding interval of
  the replicated $-0.2375$ (unrounded $-0.237535$). It is not a target.
- Report-only cells are compared at the published precision only. One of them, the row-2
  NJ $-$ PA SE, prints as 1.08 against the published 1.07: the replicated value
  (\LevelGapWTwoSe, unrounded 1.0772) is more than half a unit of the last printed digit
  from 1.07. The two state SEs of row 2 each round to the published value.

Sources:

- `runs/main-t3/metrics.json`: replicated Table 3;
- `runs/main-t4/metrics.json`: replicated Table 4;
- `runs/verdict/metrics.json`: $|\Delta|$ and met flag of every H1 target;
- `runs/pub-values/metrics.json`: published values.

The script asserts that the verdict judged exactly the replicated and published values
shown. It also asserts that each met flag equals the tolerance rule applied to the logged
$|\Delta|$.

## Table `tab_h2.tex`: run `tab-h2`, script `code/tab_h2.py`

**Caption.** H2: the NJ $-$ PA difference in the mean change in FTE employment on the
balanced sample, unwinsorized and winsorized at the 5th and 95th percentiles of the pooled
distribution of store-level changes, with two report-only secondaries.

- **(1)** The unwinsorized difference on the balanced sample of \HTwoN{} stores (\NBalNj{}
  NJ, \NBalPa{} PA). It is the replicated row 4. The six permanently closed stores are in
  it with a change of $-$FTE$_1$.
- **(2)** The H2 estimate. Each store's change is capped at the pooled cutoffs
  (\HTwoQZeroFive{}, \HTwoQNineFive{}), computed over all \HTwoN{} stores of both states
  with closures included. A store is counted as capped only if it lies strictly beyond a
  cutoff. H2 holds if (2) keeps the sign of (1) and at least half its magnitude, judged on
  point estimates (verdict run). The ratio (2)/(1) is \HTwoRatio.
- **(3) Secondary s1, report only.** The six permanently closed stores are left out of the
  percentile pool and are never capped. The other stores are winsorized at the cutoffs of
  the remaining 378.
- **(4) Secondary s2, report only.** The Neumark-Wascher sample rule: the balanced sample
  minus the permanently closed stores, \NwRuleN{} stores. OLS of the change on an NJ dummy,
  chain dummies and a company-ownership dummy. The mean changes in (4) are unadjusted.
  Neumark and Wascher (1995) report 2.78 for this rule (claim c-nw-ckbaseline). Their $N$ is
  not recorded, so the samples are not established to be the same.

Standard errors are in parentheses. Columns (1)-(3) use the balanced-sample S1 SE,
$\sqrt{sd_{NJ}^2/n_{NJ} + sd_{PA}^2/n_{PA}}$ of the (winsorized) changes. Column (4) uses
the conventional OLS SE, with the HC1 SE in brackets. With one treated and one control
state these are cross-store sampling SEs. They cannot be clustered at the level of
treatment (design deviation D1), and H2 is not judged on significance.

Among the capped stores, the low tail held 1 permanent closure (PA) and the high tail none.
The low-tail stores were large in wave 1: mean FTE$_1$ \HTwoFteOneCappedLow, against
\HTwoFteOneBal{} on the balanced sample. The high-tail stores had mean FTE$_1$
\HTwoFteOneCappedHigh.

Sources:

- `runs/h2-winsor/metrics.json` and `runs/h2-winsor/capped.csv`: H2;
- `runs/h2-closures-excl/metrics.json`: secondary s1;
- `runs/h2-nw-rule/metrics.json`: secondary s2;
- `runs/main-t3/metrics.json`: the row-4 state changes and sample sizes;
- `runs/verdict/metrics.json`: the H2 flags.

The script asserts that (1) equals main-t3's row 4, that the three H2 flags follow from the
logged estimates, and that the capped-store counts by state, tail and closure equal the rows
of `capped.csv`.

## Figure `fig_dfte_dist.pdf`: run `fig-dfte-dist`, script `code/fig_dfte_dist.py`

**Caption.** Distribution of the store-level change in FTE employment between wave 1
(February-March 1992) and wave 2 (November-December 1992) on the balanced sample, by
state: New Jersey (top, \NBalNj{} stores) and Pennsylvania (bottom, \NBalPa{} stores).

- **Bars.** The number of stores in each 2.5-FTE bin. Hatched segments are permanently
  closed stores (5 NJ, 1 PA), whose change is $-$FTE$_1$ because wave-2 employment is 0.
- **Dashed lines.** The pooled 5th and 95th percentiles used by H2 (\HTwoQZeroFive{} and
  \HTwoQNineFive), computed over both states together, closures included.
- **Shaded regions.** The tails beyond the cutoffs. Stores there are capped at the cutoff in
  the H2 estimate. The counts printed in each tail are the capped stores in that state:
  NJ \HTwoCappedLowNj{} below and \HTwoCappedHighNj{} above; PA \HTwoCappedLowPa{} below and
  \HTwoCappedHighPa{} above.
- **Diamond and bar.** The state's mean change, unwinsorized (row 4: NJ
  \DidFteBalancedNj, PA \DidFteBalancedPa), with a 95% interval of $\pm 1.96$ times its S1
  standard error. It is a sampling interval for the mean, not a spread of the stores.

A bin that straddles a cutoff is drawn whole. Only the shading shows which side each store
lies on, and `capped.csv` lists the capped stores. The two panels have their own y-axes,
both starting at zero, and share the x-axis.

Sources:

- `data/derived/stores.csv`: store-level FTE, written by run `prepare-data`. The analysis
  variables are built with `build()` from `code/ck_analysis.py`, the same code the analysis
  runs used.
- `runs/h2-winsor/metrics.json` and `runs/h2-winsor/capped.csv`: the cutoffs drawn, the
  capped counts and the capped stores;
- `runs/main-t3/metrics.json`: the row-4 state means and SEs.

The script asserts several things:

- the plotted stores are the logged sample (\HTwoN{} stores, with closures by state);
- `numpy.percentile` on them gives the logged cutoffs;
- the stores beyond the cutoffs are exactly those listed in `capped.csv`;
- the state means and SEs equal the logged row-4 values.
