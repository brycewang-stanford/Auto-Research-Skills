# hdm source reading: the effective penalty constant c in the authors' lasso calls

Scout, 2026-11-18, task `s-hdm-source` (review design-r2, F10). Bibliography key: `[hdm_cran]`.

## 1. How the authors call hdm

Read from `https://github.com/VC2015/DMLonGitHub`. The workspace copy
`code/authors/ML_Functions.R` has sha256 `a04ac0a8…f49f2d`, identical to the repository's
master.

- `401K.R` line 73, unchanged since commit a8ef8ef (2017-06-01):
  `RLasso <- list(penalty = list(homoscedastic = FALSE, X.dependent.lambda =FALSE, lambda.start = NULL, c = 1.1), intercept = TRUE)`.
  The penalty list has no `gamma` and no `lambda`.
- `Moment_Functions.R` `cond_comp()`, the RLasso branch at about lines 679-682 on master:
  `post = FALSE; if(method=="PostRLasso"){ post=TRUE }`. Method "RLasso" therefore runs
  with **post = FALSE**. This branch is identical in commits a8ef8ef (2017-06-01) and
  ff35d21 (2018-01-22).
- `ML_Functions.R` `rlassoF()`, lines 43-67:
  - Y equation (line 49):
    `do.call(rlasso, append(list(formula=form, post = post, data=datause), arg))`
  - Binary D equation (line 54):
    `do.call(rlassologit, append(list(formula=form, post = post, data=datause), arg))`

  `rlassoF` is identical in a8ef8ef and master. The treatment `e401` is binary, so D
  goes through `rlassologit`.

## 2. hdm versions on CRAN

Dates are from `Date/Publication` in each DESCRIPTION. All tarballs were downloaded from
`https://cran.r-project.org/src/contrib/Archive/hdm/`, or from `src/contrib/` for 0.3.2.

| Version | On CRAN from | Superseded | License | Tarball sha256 |
|---|---|---|---|---|
| 0.1.0 | 2016-02-02 | 2016-06-17 | GPL-3 | b7553554d0759e3c7f353e74c7f25b5deab05c51c346ca40a7a1e2f9d2343e82 |
| 0.2.0 | 2016-06-17 | 2018-01-23 | GPL-3 | 14dd57d18e2eb2be79f4c47f9af981045306f8914f57d679e7360346c81aed07 |
| 0.2.3 | 2018-01-23 | 2019-01-18 | (not checked) | 942127e44cc723cce6fb002302810a11ca69d7d8f88e15b8ca71fde7e7ba475a |
| 0.3.1 | 2019-01-18 | 2024-02-14 | (not checked) | ba087565e9e0a8ea30a6095919141895fd76b7f3c05a03e60e9e24e602732bce |
| 0.3.2 | 2024-02-14 | current | MIT + file LICENSE | 3354b22752f0aa0c0d9c8c12b38810202b6380f2587e539be11d9a358412fe6a |

Versions 0.2.1 and 0.2.2 never appeared on CRAN; the archive lists none. hdm was built
on R-Forge (`Packaged: …; rforge` up to 0.3.1).

## 3. The lines that set c, by version (file `hdm/R/rlasso.R`)

All versions' `rlasso` formals default to
`penalty = list(homoscedastic = FALSE, X.dependent.lambda = FALSE, lambda.start = NULL, c = 1.1, gamma = .1/log(n))`.
The authors' list overrides that default as a whole. In every version, the fitting
function first fills a missing gamma
(`if (!exists("gamma", where = penalty)) penalty$gamma = 0.1/log(n)`).

**0.1.0.** The formula method is `rlasso()` (line 92); it calls `rlasso.fit()` with
`penalty=penalty` (lines 107-108). `rlasso.fit()` lines 145-147:
```r
if (post==FALSE & (!exists("c", where = penalty) | is.na(match("penalty", names(as.list(match.call)))))) {
  penalty$c = 0.5
}
```
`match.call` appears here without parentheses, so `as.list(match.call)` lists the formals
of the function `match.call` itself: `definition`, `call`, `expand.dots`, `envir`, and the
body. Checked in R 4.5.2: `names(as.list(match.call))` gives exactly those.
`"penalty"` never matches, so the second disjunct is always TRUE. **Every post = FALSE
call gets c = 0.5, whatever c is supplied.**

0.1.0 also uses a **different λ0 formula** for the heteroskedastic, X-independent case
(`lambdaCalculation`, line 359):
`lambda0 <- 2*penalty$c*sqrt(n)*sqrt(2*log(2*p*log(n)/penalty$gamma))`.
The qnorm version is commented out at lines 360-361. With c = 0.5, n ≈ 4,957 (2-fold) or
7,932 (5-fold) and p = 275, this λ0 equals the qnorm formula with c ≈ 0.62 (computed:
0.6205 and 0.6212).

**0.2.0.** `rlasso.formula()` (line 97) calls `rlasso(x, y, post = post, …, penalty=penalty, …)`
(line 121), which dispatches to `rlasso.default()` (line 131). Lines 158-160 contain the
same condition as 0.1.0, so **c = 0.5 for every post = FALSE call**. λ0 is computed at
lines 424-425 as `2 * penalty$c * sqrt(n) * qnorm(1 - penalty$gamma/(2 * p * 1))`; the
0.1.0 formula is commented out at line 423.

**0.2.3.** `rlasso.default()` lines 169-172:
```r
#if (post==FALSE & (!exists("c", where = penalty) | is.na(match("penalty", names(as.list(match.call)))))) {
if (post==FALSE & (!exists("c", where = penalty))) {
  penalty$c = 0.5
}
```
The authors supply `c`, so **c = 1.1 is honoured**. `exists("c", where = <list>)` is
TRUE only when the list has an element `c`: as.environment(list) has the empty
environment as parent. Checked in R: TRUE for the authors' list, FALSE for `list(a=1)`.

**0.3.1 and 0.3.2.** The lines from 0.2.3 are kept: 0.3.1 lines 181-184, 0.3.2 lines
188-191. A second reset is added (0.3.1 lines 186-189; 0.3.2 lines 193-196):
```r
default_pen <-  list(homoscedastic = FALSE, X.dependent.lambda = FALSE, lambda.start = NULL, c = 1.1, gamma = .1/log(n))
if (post==FALSE &  isTRUE(all.equal(penalty, default_pen))) {
  penalty$c = 0.5
}
```
Once gamma has been filled in, the authors' list equals `default_pen`: same names, same
order, `c = 1.1`, `gamma = 0.1/log(n)` with the same n. So **c = 0.5**. Checked in R:
`isTRUE(all.equal(...))` is TRUE for that list.

**rlassologit (D equation), all five versions.** `rlassologit.fit` in 0.1.0 (lines 90-120)
and `rlassologit.default` in 0.2.0-0.3.2 (e.g. 0.2.0 lines 100-131) reset c only when
c is missing:
`if (!exists("c", where = penalty)) { if (post==TRUE) penalty$c = 1.1 else penalty$c = 0.5 }`.
λ0 = `penalty$c/2 * sqrt(n) * qnorm(1 - penalty$gamma/(2 * p))`. The authors supply c, so
**c = 1.1 in every version**. The 0.1.0 code differs from 0.2.0 only in the function name
and line wrapping (diff checked).

## 4. Summary: effective c for the authors' call (post = FALSE, c = 1.1 supplied)

| hdm | Y equation (`rlasso`) | D equation (`rlassologit`) |
|---|---|---|
| 0.1.0 | 0.5, with the sqrt(2 log(2p log n/γ)) λ0, equivalent to c ≈ 0.62 in the qnorm formula | 1.1 |
| 0.2.0 | 0.5 | 1.1 |
| 0.2.3 | **1.1** | 1.1 |
| 0.3.1 | 0.5 | 1.1 |
| 0.3.2 | 0.5 | 1.1 |

Corroboration (not a logged crew run; do not cite in the paper). I installed each
archived tarball into a scratch library and ran the authors' `do.call` pattern on
400-row synthetic data, backing c out of the returned `lambda0`. Results: 0.1.0 0.6703
(= 0.5 × the formula ratio at n = 400, p = 10), 0.2.0 0.5000, 0.2.3 1.1000, 0.3.1 0.5000,
0.3.2 0.5000 for Y, and 1.1000 for D in all five. For 0.3.2 this agrees with the logged
run `check-learner-ports` (`lasso_c_eff_y = 0.5`, `lasso_c_eff_d = 1.1`,
`hdm_version = 0.3.2`).

## 5. Which hdm the authors used: known and not known

**Known:**
- The published Table 2 numbers (identical in the 2018 journal version and arXiv v7)
  first appear in **arXiv:1608.00060v5, 21 June 2017**. Checked: v5 and v6 (12 Dec 2017)
  Panel B match the journal table cell for cell, including both SE rows.
- **v4 (30 Dec 2016)** still shows the earlier numbers that also appear in the AER P&P
  preprint (e.g. 5-fold median PLR Forest 9252).
- So the Table 2 run was made between 30 Dec 2016 and 21 June 2017. Throughout that
  window the current CRAN release was **0.2.0** (2016-06-17 to 2018-01-23).
- The authors' public code was first committed on 2017-06-01. The RLasso call path
  (401K.R list, cond_comp branch, rlassoF) was the same then as on master.

**Not known:**
- The hdm version actually installed on the authors' machine. Neither the paper nor the
  repository records it: there is no sessionInfo or lockfile.
- It could have been an older 0.1.0 install, which also gives c = 0.5 but with the other
  λ0 formula (about c = 0.62 in qnorm terms).
- It could have been an R-Forge development build between 0.2.0 and 0.2.3. Those builds
  are not on CRAN; the condition changed by 0.2.3, and I could not date that change.
- 0.2.3, the only version that honours c = 1.1, was released on 2018-01-23. That is
  seven months after the numbers appeared, and one day after the repository's
  2018-01-22 "major update" commit.

**Conclusion:** if the authors used the CRAN release current at the time, the Y lasso ran
with **c = 0.5**. That is likely but not proven. c = 1.1 (hdm 0.2.3) is inconsistent with
the timeline, unless an R-Forge build already had the 0.2.3 condition. c ≈ 0.62 (stale
0.1.0) cannot be excluded.
