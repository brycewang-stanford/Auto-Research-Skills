# Figure and table captions (ss-dml-401k)

Each figure and table below was built by a script under `code/`. Each script ran through
`crew.py run --kind analysis` after the results gate, and the run id is given for each item.
The scripts read only files written by logged runs, declared with `--input`. No number was
typed by hand.

Table cells that the paper quotes are written as the claims' macros, so the fragments need
`\input{numbers.tex}`. They also need `\usepackage{booktabs,icomma}`. `icomma` keeps the
thousands comma inside math mode (`$7,701$`) without adding a space. Each fragment is a bare
`tabular`. The Writer adds the float, the caption below and the label. Both tables are wide
and fit the text block with `\footnotesize` inside `\resizebox{\textwidth}{!}{...}`.

Where a caption below needs a number, it is written as the macro to use. The constants
1.4826, 1.96 and 2.81, the true synthetic theta and the split counts S are design constants
(`plan.json` design), not results.

Both figures share one palette (Okabe-Ito) and one style. Every distinction that matters also
has a grayscale cue: marker fill, marker shape, line style or position. Both are vector PDFs
with embedded STIX fonts at 6.6 to 8.5 pt, and neither crops an axis. All real-data amounts
are in 1991 US dollars.

**Wording rule.** No caption, table or figure says that a replicated estimate is "identical"
to the published one or "reproduces" it. Under design.decision_rules.H2, a pass means only
that no shift larger than the cell's 80%-power detectable shift was detected. Shifts below that
size are not ruled out.

**Macro check.** Neither table script reads `claims.jsonl`. It is not a run output, and any
later edit to the claims would invalidate the run. Instead, each script names the macro for
the (run, metric) pair it reads by the claims' convention `<Quantity><Learner><Two|Five>`. It
lists every macro it used, with that source, in comments at the end of the fragment. An
unlogged check on 2026-11-19 parsed both fragments (110 macros: 90 in `tab_side_by_side` and
20 in `tab_port_check`) and confirmed three things for each macro:

- the macro is defined in `paper/numbers.tex`;
- its claim's first support is exactly the listed (run, metric);
- the claim's value equals that metric.

There were no failures. If a claim is renamed, LaTeX fails on the undefined macro instead of
printing a stale number.

**Determinism.** Each script was also run twice in a scratch copy. The outputs were
byte-identical to each other and to the logged outputs.

---

## Table `tab_side_by_side.tex`: run `tab-side-by-side`, script `code/tab_side_by_side.py`

**Caption.** Published and replicated estimates of the effect of 401(k) eligibility on net
financial assets, for all ten cells. The model is the DML2 partially linear model with the
partialling-out score, run on all \NoctrlN{} households of the 1991 SIPP extract.

- **Replicated estimate.** The median over $S$ random sample splits (eq. 3.14). $S = 100$ for
  the lasso, regression tree and neural network, 40 for the random forest and 30 for boosted
  trees.
- **Published estimate.** Chernozhukov et al. (2018), Table 2, Panel B.
- **Bracketed SE.** The median-based SE.
- **Adjusted SE.** The parenthesized SE, which adds the split-to-split variation (eq. 3.14).
  It is shown for the published and the replicated estimate.
- **Repl. − publ.** The replicated minus the published estimate.
- **Tolerance.** The pre-registered H2 acceptance half-width,
  $2.81\sqrt{se_{rep}^2 + se_{pub}^2}$ (design.tolerance_table).
- **MDS$_{80}$.** The shift that a cell detects with 80% power.

No cell lies outside its tolerance (\HTwoNOutside{} of 10), and \HTwoNTestableInside{} of
\HTwoNTestable{} testable cells are inside.

Footnotes:

- **(a)** The two lasso cells are inside their tolerance but not testable at this resolution.
  Their detectable shifts (\MdsLassoTwo, \MdsLassoFive) exceed half the published bracketed SE,
  so they are not counted as passes. The replicated lasso split-to-split spread is also several
  times narrower than the published one (Figure `fig_split_spread`; claim
  lasso-spread-discrepancy). The lasso agreement is read only as "inside, not testable", never
  as a reproduction.
- **(b)** Pass means $|\text{difference}| \le$ tolerance in a testable cell: no shift larger
  than the cell's MDS$_{80}$ was detected. It does not mean the estimates are identical, and a
  shift below MDS$_{80}$ is not ruled out.
- **(c)** The random-forest port failed the pre-gate port check (Table `tab_port_check`). On
  synthetic outcomes the Python forest's estimate was \PortShiftForest{} (SE
  \PortShiftSeForest) in synthetic-outcome dollars, relative to R's randomForest. This was
  measured at the 2-fold training size only.
  - The 5-fold forest difference (\DiffForestFive) lies close to that shift, and the 2-fold
    difference (\DiffForestTwo) does not show it.
  - Both differences lie below the cells' detectable shifts (\MdsForestTwo, \MdsForestFive).
    So the forest passes do not show that the port reproduces randomForest, and neither cell
    can tell a zero shift from the measured one.

The table shows estimates and SEs, not intervals. The 95% lower bounds
($\theta - 1.96 \times$ adjusted SE) are the `CiLow*` macros (claims plr-*-ci-low).

Sources:

- `runs/main-<learner>/metrics.json`: replicated estimate, bracketed and adjusted SE, MDS$_{80}$;
- `runs/verdict/metrics.json`: published estimate and SEs, difference, tolerance, testability,
  H2 status, port-check result.

The script asserts that the verdict's copies of the replicated values equal the main runs'.

## Figure `fig_h2_diff.pdf`: run `fig-h2-diff`, script `code/fig_h2_diff.py`

**Caption.** The replicated minus the published estimate for each of the ten cells, against
the H2 acceptance interval. Each row is one learner and fold count $K$.

- **Dot.** The difference between the replicated median-over-splits estimate and the published
  estimate, in 1991 US dollars. Filled dots are testable cells. Open dots are the two lasso
  cells, which are not testable at this resolution.
- **Gray band.** The pre-registered tolerance $\pm 2.81\sqrt{se_{rep}^2 + se_{pub}^2}$. It is
  built from the split-sampling standard errors of both medians, so it is the uncertainty
  display for each difference. No other interval is drawn.
- **Dashed ticks.** $\pm$MDS$_{80}$, the shift detected with 80% power.
- **Right column.** The difference, the tolerance and the H2 reading.

Every cell lies inside its band (\HTwoNOutside{} of 10 outside). A dot inside the band means no
shift larger than MDS$_{80}$ was detected, not that the two estimates are identical.

The arrows mark the random-forest rows: that port failed the pre-gate check, with a shift of
\PortShiftForest{} (SE \PortShiftSeForest) in synthetic-outcome dollars at the 2-fold training
size. That shift was measured on a synthetic outcome, so it is printed as text and not plotted
on this real-data axis (design.check_learner_ports.scale_limitation).

The x-axis is symmetric and covers every MDS$_{80}$ tick.

Sources: `runs/verdict/metrics.json` (difference, tolerance, testability, H2 status, port-check
result and shift) and `runs/main-<learner>/metrics.json` (MDS$_{80}$).

## Table `tab_port_check.tex`: run `tab-port-check`, script `code/tab_port_check.py`

**Caption.** Pre-gate port check: each scikit-learn learner against the authors' R function,
called as in their code (analysis plan 0, design.check_learner_ports).

**All amounts are in synthetic-outcome dollars.** They come from a synthetic outcome and
treatment built on the nine real covariates (true $\theta$ = 9,000, ten units, one 2-fold
partition). They are not real-data dollars and not tolerances. This check ran before the
design gate, and it never read net_tfa or e401.

Columns:

- **Mean $\hat\theta$.** The mean over units for the Python port and for R seed A.
- **(a) Shift (SE).** The mean Python-minus-R difference in $\hat\theta$, with its SE across
  units.
- **(c) RMS of $\hat\theta$ gap.** The RMS Python-minus-R difference across units ("Port"),
  next to the RMS difference between two R seeds ("Seed"), which is the yardstick. The R lasso
  is deterministic, so its seed RMS is \PortRmsSeedLasso.
- **Max $|$gap$|$.** The largest absolute Python-minus-R difference over units.
- **(b) Min. correlation.** The smallest correlation, over units, of the out-of-fold
  predictions $\hat\ell$ (outcome) and $\hat m$ (treatment) between Python and R seed A. The R
  seed B versus seed A value is in parentheses.

Pass rules, fixed before the check ran:

- **Tree, forest, boosting and neural network.** $|$shift$| \le \max(2.262\,\text{SE}, \$25)$
  and port RMS $\le \max(1.75 \times$ seed RMS$, \$25)$.
- **Lasso.** Max $|$gap$| \le \$25$, and both minimum correlations $\ge 0.999$.

**(d)** The random-forest port fails both rules: shift \PortShiftForest{} (SE
\PortShiftSeForest), and port RMS \PortRmsForest{} against a seed RMS of \PortRmsSeedForest.
The deviation sits in the treatment forest: its $\hat m$ correlation with R is below the
correlation between two R seeds (column (b)). It is a measured deviation, disclosed and not re-tuned. Table
`tab_side_by_side`, note (c), and Figure `fig_h2_diff` mark it next to the forest cells.

A correlation that rounds to 1 is printed as $>$0.9999. The lasso values are given to two
decimals, matching the lasso port claims, so that the Python and R means (which differ by
\PortShiftLasso) do not print alike.

Sources:

- `runs/check-learner-ports/metrics.json`: the data-prep run, with 10 units, the mean
  $\hat\theta$, the maximum gap and the correlations;
- `runs/verdict/metrics.json`: the shift, SE, RMS, seed RMS and pass flag, copied from the
  port check and backing the `Port*` macros. The script asserts that each copy equals the
  original.

## Figure `fig_split_spread.pdf`: run `fig-split-spread`, script `code/fig_split_spread.py`

**Caption.** Split-to-split spread of the replicated estimates against the spread implied by
the published SEs (analysis plan 9(a)). Each row is one learner and fold count. The number of
splits $S$ is in the row label.

**Panel (a)** plots every per-split estimate $\theta_s$ minus the published estimate, as one
gray tick per split.

- **Blue diamond and solid bar.** The replicated median (the cell's estimate) $\pm$ 1.4826
  times the MAD of the $\theta_s$.
- **Vermillion square and dashed bar.** The published estimate (zero on this axis) $\pm$ the
  split-to-split SD that the published SEs imply, $1.4826\sqrt{\text{adj}^2 - \text{med}^2}$.
- **Gray band.** The H2 tolerance, as in Figure `fig_h2_diff`.

**Panel (b)** compares the two spreads directly, on an axis that starts at zero: the replicated
spread (filled circle) and the published-implied spread (open square).

For every learner the replicated spread is narrower than the published-implied one. The
lasso gap is by far the largest: \SplitSdObsLassoTwo{} against \SplitSdPubLassoTwo{} at
$K = 2$, and \SplitSdObsLassoFive{} against \SplitSdPubLassoFive{} at $K = 5$ (claim
lasso-spread-discrepancy). No run tests why the replicated lasso spread is narrower. The
diagnostic changes no tolerance, S or claim.

The bars are spreads of the split distribution, not confidence intervals for the median.

Sources:

- `runs/main-<learner>/splits.csv`: $\theta_s$ for every split;
- `runs/main-<learner>/metrics.json`: S and the replicated median;
- `runs/verdict/metrics.json`: published estimate, difference, tolerance, and the two spreads.

The script asserts that each file's median of $\theta_s$ equals the logged estimate, and that
the verdict's replicated spread equals the main run's.
