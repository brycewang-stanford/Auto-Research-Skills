# Figure captions (ss-card-proximity)

The script `code/fig_chr.py` built the figure below. The script ran as run `fig-chr` through
`crew.py run --kind analysis`. Code review `code-r1` covered the script; the current run was
repeated at the paper stage after a label-only change (axis units, "log points" -> log wage) with
`--unreviewed` and the human's consent (deviation D8). It reads only files that logged runs
wrote, each declared with `--input`:

- `runs/h4-chr/chr_grid.csv` and `runs/h4-chr/metrics.json`
- `runs/h3b-subvector/profile.csv` and `runs/h3b-subvector/metrics.json`

It estimates nothing new. Before drawing, it checks that the plotted sets agree with the
logged bounds and with the breakdown points.

Every result number in the caption is a claim macro from `paper/numbers.tex`. The claim id
is given after each macro. The critical values 7.815 (chi-square(3)) and 1.96 are the
planned critical values that the claims' texts state. They are not results.

## Figure `chr` (paper/figures/chr.pdf)

**Suggested caption (LaTeX; needs `\input{numbers.tex}`):**

> **(a) Sensitivity of the Panel A coefficient on schooling to a direct effect of college
> proximity; (b) weak-instrument-robust inference on the return to schooling in Card's basic
> specification.** $\delta$ and $\delta^*$ are in log-wage units (0.01 is one log point). All men in the analysis sample,
> $N = \NSample$ [n-sample]. All sets are 95% sets.
> *(a) Panel A specifications, which treat experience as exogenous. The quantity is the
> Panel A coefficient on schooling, not the return to schooling.* For each bound $\delta$
> on the direct effect of college proximity on log wages, the lines show the bounds of
> the Conley–Hansen–Rossi union. The union is taken over the direct effect
> $\gamma_0 \in [0, \delta]$ of the heteroskedasticity-robust (HC1) Anderson–Rubin
> sets, shown as solid lines through the full $\delta$ grid, with markers at
> $\delta = 0, 0.005, \ldots, 0.020$. The
> Wald-based union is shown as dashed lines; it is secondary and not robust to a weak
> instrument. Panel A column 6, with family background, is in blue with circles. Panel A
> column 5 is in orange with squares.
> At $\delta = 0$ the union is the H3(a) robust AR set: $[\ASixArLo, \ASixArHi]$
> [a6-ar-lo, a6-ar-hi] for column 6, and $[\AFiveArLo, \AFiveArHi]$ [a5-ar-lo, a5-ar-hi]
> for column 5. Dotted vertical lines mark the breakdown points, the smallest $\delta$ at
> which the robust union first includes 0:
> $\delta^* = \ASixPacoefChrBreakdown$ [a6-pacoef-chr-breakdown] for column 6, which is
> $\ASixPacoefChrShare$ [a6-pacoef-chr-share] of its reduced-form coefficient; and
> $\delta^* = \AFivePacoefChrBreakdown$ [a5-pacoef-chr-breakdown], or
> $\AFivePacoefChrShare$ [a5-pacoef-chr-share], for column 5. The Wald-based unions break
> down at $\ASixPacoefChrWaldBreakdown$ and $\AFivePacoefChrWaldBreakdown$
> [a6-pacoef-chr-wald-breakdown, a5-pacoef-chr-wald-breakdown].
> *(b) Card's basic specification, Panel B column 6, which treats schooling, experience
> and its square as endogenous. The quantity is the return to schooling.* The curve is the
> profile robust Anderson–Rubin statistic $m(b_0)$, the minimum over the two experience
> coefficients of the HC1 full-vector AR statistic. The dashed line is the chi-square(3)
> 95% critical value, 7.815. The bars below show the 95% sets on the evaluated point list:
> - The robust projection set is the primary set, in blue:
>   $[\BSixArRobLo, \BSixArRobHi]$ [b6-ar-rob-lo, b6-ar-rob-hi], one piece
>   [b6-ar-rob-npieces]. It is valid under heteroskedasticity whatever the strength of the
>   instruments, but it is conservative, so it is wider than an exact-size test's set. It
>   contains 0, so this set does not establish a positive return
>   [h3b-b6-return-positive]; it does not show that the return is zero.
> - The three homoskedastic subvector AR sets are shown alongside and do not decide H3(b):
>   - GKMC: $[\BSixArGkmcLo, \BSixArGkmcHi]$ [b6-ar-gkmc-lo, b6-ar-gkmc-hi].
>   - GKM19 with Table 3 critical values, the reported GKM19 set:
>     $[\BSixArGkmOneNineLo, \BSixArGkmOneNineHi]$ [b6-ar-gkm19-lo, b6-ar-gkm19-hi].
>   - GKM19 with the eq. (2.12) quantile from ivmodels:
>     $[\BSixArGkmOneNineqLo, \BSixArGkmOneNineqHi]$ [b6-ar-gkm19q-lo, b6-ar-gkm19q-hi].
>
>   Their critical values are close to the chi-square(1) value because $\kappa_1$ is
>   large everywhere on the point list (minimum $\BSixKappaOneMin$ [b6-kappa1-min]).
>
> The plotted window of $b_0$ is the span of the sets and 0, padded by 10%. The statistic
> and the sets were evaluated on $[-1, 1]$ and beyond, up to $|b_0| = 10^5$; on that evaluated
> point list no set has a piece outside the window (pieces narrower than the outer-grid
> spacing outside $[-1, 1]$ could be missed).

**Wording the Writer must keep.**

- In panel (a) the quantity is "the Panel A coefficient on schooling", not "the return to
  schooling".
- H3(b) is the only result in this figure about the return. Its set is conservative, and a
  set that contains 0 is "positive not established", not evidence of a zero return.
- The Wald unions and the homoskedastic GKMC and GKM19 sets are secondary.

**Reading notes for the Writer, not for the caption.**

- In panel (a), the upper bound of each robust union stays at its $\delta = 0$ value.
  Larger $\gamma_0$ only moves the set down, so the union widens only at its lower end.
- The $\delta$ grid in `chr_grid.csv` is dense: 201 values per specification, step
  $10^{-4}$. The lines pass through every grid point. Markers are drawn only at the five
  planned values of $\delta$, and the two specifications share the same $\delta$ positions
  (no horizontal offset).
