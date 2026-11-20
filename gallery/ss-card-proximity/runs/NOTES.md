# Econometrician notes: ss-card-proximity

What ran, in order, with the exact commands, and anything that surprised us. Data
preparation (fetch-data, prepare-data) was run by the Data RA; see data/CODEBOOK.md.

## Environment

- `.venv` inside the workspace (git-ignored), built with Homebrew Python 3.14.6:
  `python3.14 -m venv .venv && .venv/bin/pip install numpy==2.5.3 pandas==3.0.5
  scipy==1.18.1 statsmodels==0.15.0 linearmodels==7.1 ivmodels==0.10.0 glum==3.5.0
  tabmat==4.3.1 numba==0.68.1 llvmlite==0.50.0 scikit-learn==1.9.1 matplotlib`, then
  `pip freeze > code/requirements.txt`. Every version named in design.method resolved as
  named (pandas 3.0.5 included); matplotlib 3.11.2 was added at the PI's request for the
  fig-chr run.
- The resolver first pulled `wrapt==2.6.0.dev1` (a pre-release, dependency of formulaic,
  which linearmodels needs). It was replaced by the latest stable release, 2.5.2, before
  the freeze; `pip check` is clean.
- A fresh venv built from `code/requirements.txt` alone (in a scratch directory, not used
  by any run) freezes to the identical list.

## Code (written 2026-11-21, after the design gate, before any analysis run)

| File | Run | Purpose |
|---|---|---|
| `code/ivlib.py` | all | Column sets, specifications A1-A6, B1-B6, T2C2, T2C5 (k asserted against design.method), OLS (statsmodels) and 2SLS (linearmodels IV2SLS, debiased) with conventional and HC1 SEs, the one-instrument AR set, CHR, H5 influence functions, the Panel B robust projection (`PanelB`), GKMC / GKM19 statistics and critical values, the SET COMPUTATION procedure (`invert_on_grid`), ivmodels wrappers, CR1 |
| `code/h1_b6.py` | h1-b6 | Primary H1 targets (B6, B2, B4, T2 col 5, N) and B5, B1, B3 |
| `code/h1_a6.py` | h1-a6 | A6, A2, A4 |
| `code/h1_a5.py` | h1-a5 | A5, A1, A3, T2 col 2, homoskedastic AR set for A5 |
| `code/h2h3_weakiv.py` | h2h3-weakiv | H2 F statistics, H3(a) robust AR sets with the grid check |
| `code/h3b_subvector.py` | h3b-subvector | H3(b) robust projection, GKMC, GKM19 (3T, 3Q) sets; `profile.csv` |
| `code/h4_chr.py` | h4-chr | H4 breakdown, union sets, Wald secondary; `chr_grid.csv` |
| `code/h5_cf.py` | h5-cf | H5 control-function test and stacked-IF interval |
| `code/r_age1419.py` | r-age1419 | Card Table 4 row 7 |
| `code/r_balance.py` | r-balance | KWW / IQ balance checks |
| `code/r_cluster.py` | r-cluster | CR1 SEs on region-1966 x SMSA-1966 cells |
| `code/verdict.py` | verdict | H1 counts and misses, H2, H3, H5 flags, H4 next to the published-number prediction |
| `code/test_ivlib.py` | check-synthetic | Step 0c on synthetic data only |

Column names shared with `code/fig_chr.py` (Figures RA's input contract): chr_grid.csv has
`spec, delta, ar_lo, ar_hi, ar_npieces, wald_lo, wald_hi` (delta = 0, 1e-4, ..., 0.02);
profile.csv has `b0, m, kappa_p, kappa_1, c_gkm19, c_gkm19q, acc_rob, acc_gkmc,
acc_gkm19, acc_gkm19q`; metrics keys `a6_pacoef_chr_breakdown`,
`a5_pacoef_chr_breakdown`, `b6_ar_{rob,gkmc,gkm19,gkm19q}_{lo,hi}`, `b6_ar_rob_npieces`.

### Implementation choices the design leaves implicit

None of these changes a sample, specification, SE formula or decision rule.

1. **H3(b) random starts.** The 20 draws are standard-normal 2-vectors drawn once with
   `default_rng(4483)`; at each b0 the starts are g_2sls(b0) + 5 x HC1 SE(B6 g) x draw,
   i.e. N(start (a), diag(25 x SE^2)) with the same offsets at every b0, so each m(b0)
   depends only on b0 (bisection and reruns are reproducible).
2. **H3(b) HAR check points.** design.method asks for "20 random (b0, g)" and also says the
   only randomness is the 20 starting draws. The real-data check therefore uses
   b0 = 20 evenly spaced points on [-0.5, 0.8] and g = B6 g + 5 x HC1 SE x the same 20
   draws (no new random numbers). The synthetic check uses fresh random points.
3. **BFGS** is given the analytic gradient of HAR in g (checked against central
   differences in check-synthetic); m(b0) is the smallest value reached over the 23 starts,
   whatever scipy's convergence flag (with gtol 1e-10 many starts end with "precision
   loss").
4. **Outer grid.** `logspace(0, 5, 401)[1:]`: 400 points per side beyond |b0| = 1 up to
   1e5 (|b0| = 1 itself is on the fine grid). The point list has 4,801 points.
5. **Bisection** stops when the bracket is within 1e-6 (absolute for |b0| <= 1, relative
   beyond); the reported bound is the bracket midpoint.
6. **(3Q) acceptance** is kappa_p <= q(kappa_1), q found by Brent's method on the ivmodels
   p-value function on (0, min(kappa_1, 20)); the cap 20 keeps scipy's quad on a short
   range (for k - m_W = 1 the 95% quantile is below 3.842, and the tail above 20 is below
   1e-5). Without the cap quad returned p = 1 at kappa_1 = 1e5.
7. **Unbounded sides** are written to metrics.json as null, with `*_lo_unbounded` /
   `*_hi_unbounded` flags and a `*_pieces` string; CSV files write -inf / inf.
8. **Full-rank check.** `fit_ols` refuses a rank-deficient regressor matrix
   (statsmodels would otherwise fall back to a pseudo-inverse silently).
9. **kappa_1 at large |b0|.** Because exp76 + ed76 = age76 - 6 and age76 is an
   instrument, P_Z(Y0, W) has a component of order b0 that M_Z(Y0, W) lacks, so kappa_1(b0)
   grows like b0^2 on the outer grid (about 1.8e15 at |b0| = 1e5 on the synthetic Card
   file). Two consequences, found in the check-synthetic dry run: the (3Q) quantile search
   keeps its lower bracket near 0 (item 6), and `PanelB.kappas` equilibrates the 3 x 3
   generalized eigenproblem by the diagonal of the M-matrix (roots unchanged).
10. **ivmodels agreement checks (h3b-subvector).** The failing checks (kappa_p, kappa_1 to
    1e-6; GKM p-value to 1e-3) are made at |b0| <= 1: the 2SLS estimate, 0, -0.5, 0.5, 1
    and every finite reported bound inside [-1, 1]. The tolerance is relative with an
    absolute floor, |a - b| <= 1e-6 max(|a|, |b|, 1), because B6 is just-identified and
    kappa_p = 0 at the 2SLS estimate (about -7e-13 numerically, where ivmodels' p-value is
    NaN); p-values are compared only where kappa_p > 1e-8, and a NaN difference fails. At
    a reported bound beyond |b0| = 1 the differences are written as metrics
    (`*_outer`) but do not fail the run: on the synthetic Card file ivmodels' own root
    solver gives kappa_1 = 964 at b0 = 1e5 where the b0^2 law (and our equilibrated
    3 x 3 solve) gives 1.8e15, while kappa_p still agrees to 1e-7. The set agreement
    checks (GKMC quadric, ivmodels 'chi2' and 'gkm' inverses, to 1e-4) are unchanged.
11. **Wall time** is printed to each run's stdout.log, not written as a metric, so a clean
   rerun can compare metrics exactly.

## Runs

### 0c. check-synthetic (data-prep, synthetic data only), 2026-11-20T18:29Z, exit 0

```bash
python3 crew/scripts/crew.py run gallery/ss-card-proximity --id check-synthetic \
  --role econometrician --kind data-prep \
  --code code/test_ivlib.py --code code/ivlib.py --code code/h1_b6.py --code code/h1_a6.py \
  --code code/h1_a5.py --code code/h2h3_weakiv.py --code code/h3b_subvector.py \
  --code code/h4_chr.py --code code/h5_cf.py --code code/r_age1419.py \
  --code code/r_balance.py --code code/r_cluster.py --code code/verdict.py \
  --code code/requirements.txt \
  --output runs/check-synthetic/synthetic_card.csv \
  --output runs/check-synthetic/entry/h3b-subvector/profile.csv \
  --output runs/check-synthetic/entry/h4-chr/chr_grid.csv \
  --metrics runs/check-synthetic/metrics.json -- .venv/bin/python code/test_ivlib.py
```

All 10 checks pass (`checks_failed` = 0; wall time 433 s, of which 287 s is the H3(b)
entry point on the synthetic Card file). Highlights, all synthetic:

- SEs: OLS and 2SLS (one and three endogenous) conventional and HC1 SEs equal the hand
  formulas to 1e-10; one-instrument 2SLS = RF/FS to 3e-15.
- H3(a) closed form = grid inversion in all three shapes (bounded, two half-lines, whole
  line); AR(0) = robust RF t^2.
- CHR breakdown = RF lower bound and the 1e-5 grid; Wald CHR SE = linearmodels.
- H5: IF variances = HC1; pairs-bootstrap Var(D) / IF Var(D) = 1.010 (tolerance 0.15).
- Panel B, S (concentration for W 313, population kappa_1 591) and WN (population
  kappa_1 5.08): stacked HAR = direct regression (< 1e-10), BFGS profile never above the
  401 x 401 brute-force grid (largest ratio 0.99999), robust projection coverage 0.996 (S)
  and 1.000 (WN) of 500 (bound 0.921); GKMC coverage 0.976 / 1.000 and GKM19 (3T) 0.974 /
  1.000 (reported only); own kappa_p, kappa_1 = ivmodels (< 1e-13), GKMC quadric =
  ivmodels (< 1e-8), (3Q) procedure set = ivmodels 'gkm' (< 2e-7). In WN the GKMC and GKM19
  sets are the whole line, so the bounded-set agreement is exercised by S and by the
  entry-point file.
- GKM19 critical values: every check of design step 0c passes; the eq. (2.12) quantile
  lies 0.0004-0.03 below each tabulated value (consistent with upward rounding).
- Set computation returns the four known shapes to 1e-6.
- Entry points: every run script and verdict.judge ran on the synthetic Card file.

Surprises found by the dry runs (scratch copy, before this run), all fixed in the code
this run covers: (1) kappa_1 grows like b0^2 on the outer grid, which broke the first
(3Q) bracket and exposed ivmodels' loss of precision at |b0| >= 1e3 (items 6, 9, 10
above); (2) the 2SLS-vs-linearmodels consistency check in h4-chr needed QR solves
instead of normal equations (difference 1.4e-10 -> 3e-12); (3) the conv-vs-robust 2SLS
coefficient check now uses a scale-aware tolerance.

Next: code review (rv-code) of every script above plus `code/fig_chr.py`; no analysis
run before it passes.
