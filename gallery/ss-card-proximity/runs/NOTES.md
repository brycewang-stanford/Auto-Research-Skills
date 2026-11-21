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

## Analysis runs (2026-11-20, after code-r1 passed; all `--kind analysis`, covered by code-r1)

Every run executed `.venv/bin/python code/<script>.py` from the workspace root through
`crew.py run`, with `--input data/derived/card_analysis.csv` (verdict: the ten
`runs/<id>/metrics.json` files) and `--metrics runs/<id>/metrics.json`. `--code` named the
script and `code/ivlib.py`; h1-a5 also named `code/h1_a6.py` and verdict `code/ivlib.py`
(code-r1 F3). Each ran once, in the order of design.analysis_plan; none was replaced, and
no reviewed script was edited.

| # | Run | Started (UTC) | Wall | Extra outputs |
|---|---|---|---|---|
| 1 | h1-b6 | 18:47:11 | <1 s | |
| 2 | h1-a6 | 18:47:14 | <1 s | |
| 3 | h1-a5 | 18:47:16 | <1 s | |
| 4 | h2h3-weakiv | 18:47:18 | <1 s | |
| 5 | h3b-subvector | 18:47:24 | 331 s | runs/h3b-subvector/profile.csv |
| 6 | h4-chr | 18:53:12 | <1 s | runs/h4-chr/chr_grid.csv |
| 7 | h5-cf | 18:53:14 | <1 s | |
| 8 | r-age1419 | 18:53:15 | <1 s | |
| 9 | r-balance | 18:53:17 | <1 s | |
| 10 | r-cluster | 18:53:18 | <1 s | |
| 11 | verdict | 18:53:20 | <1 s | |

Measured wall time of the whole analysis plan: about 6 minutes (h3b-subvector 331 s),
inside the seed's 15-minute budget. Every in-run identity and agreement check passed
(A5/A6 2SLS = RF/FS; AR(0) = robust RF t^2; H3(a) grid check 0 mismatches; stacked HAR =
direct regression, 4e-12; kappa_p, kappa_1 = ivmodels at 13 points in [-1, 1], 1e-12;
GKMC quadric = ivmodels = procedure, 3e-7; (3Q) = ivmodels 'gkm', 3e-7; CHR grid within
one step; IF variances = HC1; D = -rho g; CR1 = own formula). No reported H3(b) bound lies
beyond |b0| = 1, so the D3(a) "outer" comparison was not needed (metrics 0).

### What surprised us

1. **Card's Panel B first-stage and reduced-form columns are not reproduced; his Panel B
   2SLS columns are.** B6 2SLS 0.1324 (0.0493) and B5 0.1224 (0.0465) round to the
   published 0.132 (0.049) and 0.122 (0.046), but B4 is 0.0346 (0.0173) against 0.048
   (0.019), B3 0.0325 (0.0174) against 0.047 (0.019), B2 0.3639 (0.1024) against 0.365
   (0.105), B1 0.3924 against 0.382. N, the sample, Panel A (all twelve numbers), both OLS
   columns and the Cinelli-Hazlett AR set reproduce, so the data reading and sample rule
   are not the cause. Diagnosis (arithmetic only, nothing re-estimated): Card says the IV
   estimates are the ratios of the reduced-form coefficients, and his printed Panel B
   ratios are (0.048/0.365 = 0.132, 0.047/0.382 = 0.123), whereas ours are not
   (0.0346/0.3639 = 0.095, 0.0325/0.3924 = 0.083). That is expected for the regression
   the design specified (lwage76 or ed76 on nearc4, age76, age762 and controls): since
   exp76 = age76 - ed76 - 6, the nearc4 coefficient of that reduced form is not beta x pi.
   So Card's Panel B "reduced form" columns must be a different regression; the design
   adopted the Scout's reading, which sources/notes.md flags as not printed. One
   regression whose ratio is beta by construction is the nearc4 coefficient with experience
   and its square kept in the equation as endogenous regressors instrumented by age and
   age squared; this is a hypothesis only. Testing it would be a new, unplanned diagnostic
   run (new script, code round, PI approval); it was not run and nothing was tuned.
2. **H3(b): the robust projection set is far wider than the homoskedastic sets.**
   Robust [-0.0068, 0.4983] (contains 0; m(0) = 7.30 against 7.815) against GKMC
   [0.0401, 0.2811] and GKM19 [0.0401, 0.2811]. kappa_1 is about 6,000 at the estimate
   (minimum 5,320 over the point list), so GKM19 = GKMC to four decimals, as the Scout
   expected. The robust set's width is the projection's conservativeness (chi-square(3)
   instead of chi-square(1)), as plan.json H3 anticipated.
3. **r-age1419**: N = 2,037 and IV 0.0944 (0.0645) match Card's 0.094 (0.064), but OLS is
   0.0745 (0.0061) against the published 0.076 (0.006).
4. **H4** breakdowns (0.0114 A6, 0.0077 A5) are a little above the values predicted from
   the published conventional numbers (0.0097, 0.0067), because the HC1 SE of the reduced
   form is smaller than the conventional one.
5. **r-cluster**: the CR1 SE of the reduced form is smaller than HC1 (ratio 0.82 A6, 0.86
   A5; G = 18, smallest cell 25 men, one cell under 30), so clustered t = 3.18 / 2.78 >
   t(0.975, 17) = 2.11. By the fixed reading this is not reported as robustness to
   county-level dependence.
6. **Warnings in runs/h3b-subvector/stderr.log** (not errors): a ComplexWarning when
   ivmodels' inverse returns a quadric boundary as a complex number with zero imaginary
   part (we take the real part; the set agrees with ours to 3e-7), and an IntegrationWarning
   / invalid-power warning from ivmodels' p-value integrand at z near 0. All in-run
   agreement checks passed.

### Metrics not turned into claims, and why

Check and diagnostic metrics (grid mismatch counts, max relative differences, k, the
sum(e^2)/n SEs, `*_minus_ratio`, ivmodels comparisons, kappa and critical values at each
bound, `*_pieces` strings, shapes, CI-excludes-0 flags that duplicate the reported
coefficient and SE) are the evidence that the run is internally consistent, not findings.
The h2h3 flags and h3b flag duplicate the verdict flags, which are claimed. The CHR union
bounds at the five fixed deltas are drawn in the figure from chr_grid.csv and can be
claimed if the Writer quotes one. HC1 SEs of the H1 first stages and reduced forms, the
Panel B experience coefficients and the young-men HC1 SE are available in the metrics but
not planned for the paper. After results-r1 (F3, F5, F6), the r-cluster first-stage
results, the young-men interval and the Table 2 col 5 HC1 and n-denominator SEs became
claims (see the section below).

## Claims (task e-claims)

115 result claims were appended to claims.jsonl (all ids of design.claims_plan, plus
iv-return-pct, young-ols-se, b6-rob-m-at-zero, the a6/a5 conventional Hausman t,
balance coefficients in SD units, and t-crit-cl), each with `value` copied from its run's
metric and a letters-only macro; `crew.py numbers` wrote paper/numbers.tex. No H3(a) or
H4/H5 claim is worded as a statement about the return to schooling; only
h3b-b6-return-positive is. check-sas-listing (e-sas-code) has not been started, and
read1.lst has not been opened.

## D4 (post hoc): diag-panelb

Written for task e-diag-panelb after the PI recorded deviation D4. It re-estimates
Panel B columns 1-4 as just-identified 2SLS regressions with exp76 and exp762 endogenous
(instrumented by age76, age762) and nearc4 and the controls exogenous. It reports the
nearc4 coefficient with conventional and HC1 SEs and the H1 rounding-rule match against
Card's printed values. It fails the run unless B4*/B2* equals the B6 2SLS coefficient
and B3*/B1* equals the B5 2SLS coefficient to 1e-10. It imports only ivlib.py, and no
reviewed script was edited. The script was tested outside the ledger in the scratch
directory on runs/check-synthetic/synthetic_card.csv, where both identities held to 2e-12.
It waits for code-r2 before its run (`--code code/diag_panelb.py --code code/ivlib.py
--input data/derived/card_analysis.csv --metrics runs/diag-panelb/metrics.json`).

### Run diag-panelb (2026-11-20T19:02Z, analysis, covered by code-r2, exit 0)

`crew.py run . --id diag-panelb --role econometrician --kind analysis --code
code/diag_panelb.py --code code/ivlib.py --input data/derived/card_analysis.csv --metrics
runs/diag-panelb/metrics.json -- .venv/bin/python code/diag_panelb.py`

With exp76 and exp762 kept as endogenous regressors instrumented by age76 and age762, all
8 printed Panel B column 1-4 numbers round to Card's values:

| Column | Re-estimate (conv. SE) | Card |
|---|---|---|
| B1 | 0.3815 (0.1138) | 0.382 (0.114) |
| B2 | 0.3654 (0.1053) | 0.365 (0.105) |
| B3 | 0.0467 (0.0189) | 0.047 (0.019) |
| B4 | 0.0484 (0.0185) | 0.048 (0.019) |

Following code-r2 F5, the 9 post hoc claims (diag-b1 ... diag-b4-se,
diag-targets-reproduced) rest only on the diag_b*_reproduced and diag_b*_se_reproduced
flags. They say the match is consistent with Card having estimated the columns this way,
not that it proves it. The approved B1-B4 targets stay counted as misses in the verdict.
The ratio metrics (B4*/B2* - B6 = -1.6e-11, B3*/B1* - B5 = 8e-12) are an algebraic
identity, used as a code check and not claimed as evidence. Since the conventional SEs
match too, the narrowing F5 prescribes for coefficient-only matches was not needed. No
variant was run. HC1 SEs are in the metrics, not claimed.

## e-sas-code: code/check_sas_listing.py (written 2026-11-20, not yet run; awaits code-r3)

Written after every planned claim was in claims.jsonl. It reads read1.lst from
data/raw/proximity.zip in memory and never extracts, writes or prints it. Nobody on the
crew has opened it: the parser was written from the PROC REG output format, using
read1.sas (four models under `proc reg s`; the two LWAGE76 models are Table 2 columns 2
and 5) to know what to expect.

The parser finds the two LWAGE76 model blocks and identifies them by parameter count
(16 and 30; anything else fails the run). N comes from "Number of Observations Used",
or, in SAS 6 listings, which print no N, from the corrected-total df + 1; it is
cross-checked against the error df. The ED76 estimate and SE are compared with h1-a5
(a5_ols, a5_ols_se, a5_n) and h1-b6 (ols_beta, ols_se, n_sample) at the printed precision
with the H1 rule. The run writes sas_ols_match (all 6 items) for the planned claim
sas-ols-match.

The parser was tested outside the ledger on two synthetic listings written in the scratch
directory, 15 checks in all:
- a SAS 6 layout with form feeds, page headers, the `s` descriptive-statistics block, two
  ED76 models first, and a parameter table continued on a new page with a repeated model
  header. This case led to the one change made during testing: a repeated header now
  continues the current block.
- a SAS 9 layout.
- detection of coefficient, SE and N mismatches.
- failure when a LWAGE76 model is missing.

Planned command (after code-r3): `crew.py run . --id check-sas-listing --role econometrician
--kind analysis --code code/check_sas_listing.py --code code/ivlib.py --input
data/raw/proximity.zip --input runs/h1-a5/metrics.json --input runs/h1-b6/metrics.json
--metrics runs/check-sas-listing/metrics.json -- .venv/bin/python code/check_sas_listing.py`

### Run check-sas-listing (2026-11-20, analysis, covered by code-r3, exit 0)

The run used the planned command above. It parsed four PROC REG models and identified the
two LWAGE76 models as MODEL3 (16 parameters, Table 2 col 2) and MODEL4 (30, Table 2
col 5). The listing is in the SAS 6 layout: it prints no N, so N is the corrected-total
df + 1. All 6 items match at the printed precision:

| Item | Listing | Ours | Difference |
|---|---|---|---|
| T2 col 2 N | 3010 | 3010 | 0 |
| T2 col 2 ED76 | 0.074693 | 0.074693259 | +2.6e-7 |
| T2 col 2 SE | 0.00349835 | 0.00349834572 | -4.3e-9 |
| T2 col 5 N | 3010 | 3010 | 0 |
| T2 col 5 ED76 | 0.072634 | 0.072634472 | +4.7e-7 |
| T2 col 5 SE | 0.00369843 | 0.00369843054 | +5.4e-10 |

D5's failure path was not needed. As code-r3 F7 and D5 require, the claim sas-ols-match
speaks only of these two OLS regressions and N. It says nothing about the instrument, the
age variables, any IV estimate or the B1-B4 misses. No tolerance was changed. The
listing's text was not printed, and nothing was extracted to disk. Every planned run and
claim is now complete.

## Claims revised after results-r1 (2026-11-20; no run, no value changed)

- **Changed texts**: iv-return (F1); first-stage, first-stage-se, reduced-form,
  reduced-form-se, b1-fs, b3-rf, b3-rf-se, h1-primary-reproduced,
  h1-secondary-reproduced (F2); a5-ols-se, ols-return-se (F3); young-ols (F4);
  b6-kappa1, b6-kappa1-min (F7).
- **New claims**: ols-return-se-robust and ols-return-se-n (F3); young-iv-lo and
  young-iv-hi (F5); a6-fs-se-cl, a6-fs-cl-ratio, a6-fs-t-cl, a6-rf-cl-ratio,
  a5-fs-se-cl, a5-fs-cl-ratio, a5-fs-t-cl, a5-rf-cl-ratio and n-clusters-under30 (F6).
- **Clustered first-stage F (squared clustered t)**: A5 is about 11.4, below both H2
  thresholds. A6 is about 19.0, above 16.38 but below 23.11.

## Claims added after paper-r1 (2026-11-20; no run, no value changed)

- **F3**: bal-kww-all-n. The iq-obs-diff and iq-obs-diff-se texts now say the row is
  unadjusted.
- **F6**: h1-primary-targets, h1-secondary-targets, diag-targets, sas-items,
  sas-items-matched. No run metric gives the number of H1 misses (7) or the number of
  Panel A targets (12) directly. Each is a sum of verdict flags, so the Writer must
  derive it from macros (for example with `\numexpr`) or reword.
- **F9**: b6-hom-stat-at-zero (kappa_p at b0 = 0 = 6.84, next to m(0) = 7.30). It is
  descriptive and post hoc, and changes neither the H3(b) rule nor its primary set.
