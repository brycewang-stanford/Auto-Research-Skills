# Captions: figures and tables (ss-rd-senate)

Numbers in these captions are LaTeX macros from `paper/numbers.tex`, which is generated
from `claims.jsonl`. The paper must `\input{numbers.tex}` before the captions and tables.
The tables use `booktabs` commands (`\toprule`, `\midrule`, `\bottomrule`). No seeds are
involved: every estimate is deterministic given the recorded data and software versions
(rdrobust 2.1.1, rddensity 3.0, see `code/requirements.txt`).

---

## Figure 1. `paper/figures/fig_rd.pdf` (script `code/fig_rd.py`, run `fig-rd`)

**Figure 1. Democratic vote share at t+2 against the Democratic margin of victory at t, US Senate elections, 1914 to 2010.**
Sample: the H1 estimation sample, \RdN elections with an observed outcome (\RdNLeft left of the cutoff, \RdNRight at or above it). Points are means of the vote within evenly spaced bins; the bin edges are those chosen by rdrobust's `rdplot` (esmv rule, separately on each side, masspoints off). Bars are 95% confidence intervals from the within-bin standard deviation. Bins with one observation have no interval and are drawn as open circles. Solid lines are local-linear fits with triangular weights within the MSE-optimal bandwidth h = \RdBw (dashed vertical lines at the cutoff 0 and at +/- h; the shaded areas lie outside the bandwidth). The difference between the two fitted intercepts at 0 is the conventional H1 estimate, \RdEffect percentage points. The estimate is local to close elections, within about h points of the cutoff, conditional on the Democratic win at the threshold. It is not the incumbency advantage in all elections. The bandwidth uses masspoints = 'off', an assumption about the 2016 rdrobust release; under 'adjust' (the 2.1.1 default) h = \RdAdjBw. The plot shows the full support, margin from -100 to 100.

---

## Figure 2. `paper/figures/fig_density.pdf` (script `code/fig_density.py`, run `fig-density`)

**Figure 2. Density of the Democratic margin of victory around the cutoff (H2(a) falsification test).**
Sample: all \RdDensityN elections in the seed file (\RdDensityNLeft with margin below 0, \RdDensityNRight at or above 0); the outcome is not used. Bars are a histogram in 1-point bins over [-40, 40], scaled to a density over all elections. Curves are rddensity's local-polynomial density estimates on each side (p = 2, triangular kernel, jackknife variance, bandwidth selector 'comb', massPoints on), with 95% confidence regions; the estimates are evaluated on a grid of 60 points per side. The robust bias-corrected test of equal densities at 0 gives T_Q = \RdDensityT and p = \RdDensityP; the estimated difference in density (right minus left) is \RdDensityDiff, with a minimum detectable difference of \RdDensityMde (80% power, two-sided 5%). This is a single test with no correction. A large p-value is not proof of continuity of the running variable, and the test has limited power at this sample size, which is why the MDE is printed beside it.

---

## Table 1. `paper/tables/tab_main.tex` (script `code/tab_main.py`, run `tab-main`)

**Table 1. Replication of the default rdrobust output in Calonico, Cattaneo, Farrell and Titiunik (2017, Sec. 7.2) for the US Senate incumbency advantage.**
Specification: sharp regression discontinuity; local-linear fit (p = 1, bias order q = 2); triangular kernel; MSE-optimal common bandwidth (mserd); nearest-neighbour variance (3 matches); robust bias-corrected 95% confidence interval. Outcome: Democratic vote share at t+2 (percent). Running variable: Democratic margin at t (percentage points, cutoff 0). Sample: \RdN elections with an observed outcome. The printed column is the value stated in the article, as recorded by the Scout (`sources/notes.md`). The replicated columns use rdrobust 2.1.1 (pinned). Estimates and intervals are in percentage points; the bias bandwidth b is in margin points on the left side. The two replicated columns differ only in the masspoints option. `off` is the primary reading, on which the H1 decision is judged: the estimate and both interval endpoints must lie within 0.01 pp of the printed values, N must match exactly, and h must lie within 0.0005 of the printed value. b is recorded but is not part of the tolerance rule. `adjust` (the 2.1.1 default) is a secondary reading and is not judged. The check is a computational reproduction, not evidence about the incumbency advantage. Whether the 2016 release used no mass-point adjustment (`off`) is not verified.

---

## Table 2. `paper/tables/tab_falsification.tex` (script `code/tab_falsification.py`, run `tab-falsification`)

**Table 2. Falsification tests (H2) and descriptive sensitivity of the H1 estimate (H3).**
Samples: the H1 estimation sample (\RdN elections) for H3; all elections (\RdDensityN) for H2(a); all elections (\RdSelectionN) for H2(d); for H2(b), all elections (\RdCovClassN) for class and population and the complete cases (\RdCovTermshouseN) for termshouse and termssenate. Every test uses the H1 settings (masspoints off, p = 1, triangular kernel, mserd) except H2(a), which uses the rddensity defaults.

*Panel A.* H2(a): density test of margin at 0; the estimate is the difference in density, right minus left. H2(b): balance of four predetermined covariates at the cutoff, with Holm adjustment across these four only (adjusted p-values are shown in parentheses; none is below 0.05). Covariate estimates are in covariate units, and population is in persons. H2(c): one-sided placebo cutoffs c_L and c_R (medians of the margin on each side of 0), each estimated on its own side. These are reported only: they carry no test conclusion and no MDE, and the precision is the width of the interval. The bandwidth-cap flag is 0 on both placebos as recorded; the flag's positive branch has not been observed on real or synthetic output, so the flag does not show that the cap did not bind. H2(d): rdrobust of the observed-outcome indicator on margin, a single test. Its estimate and interval are on the proportion scale; multiply by 100 for percentage points (the estimate, \RdSelectionCoef, is -6.2 pp, and the interval runs from \RdSelectionCiLow to \RdSelectionCiHigh, or about -14.5 to +1.8 pp). Its MDE is in percentage points. For H2(a), H2(b) and H2(d), a non-rejection shows no evidence of a discontinuity larger than the MDE in the same row; it is not proof of continuity or of no selection. The H2(d) interval allows a lower observed-outcome share on the Democratic-win side of as much as about 14.5 pp, so H1 is not free of selection on this test. The MDE is (z_0.975 + z_0.80) times the robust standard error, fixed in the design; the MDEs of H2(a) and H2(b) were computed in run design-mde before the design gate, from the margin and covariates only (disclosed in plan.json).

*Panel B.* H3: descriptive sensitivity of the H1 estimate, with no decision rule. (i) printed 2014 bandwidths; (ii) and (iii) half and double the H1 bandwidth, with b scaled the same way; (iv) p = 2 and q = 3 with the mserd bandwidth; (v) the H1 specification with masspoints 'adjust'. Estimates and robust 95% intervals are in percentage points. Panel B has no MDE because these are not tests.
