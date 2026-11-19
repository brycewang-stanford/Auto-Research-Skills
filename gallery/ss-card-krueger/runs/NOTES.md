# Econometrician notes: ss-card-krueger

This file lists what ran, in order, the exact commands, and anything that surprised us.
code-r1 passed with three minor findings, which were fixed before any analysis run (see
0d). The eight planned analysis runs then ran once each, in the planned order, on
2026-11-19. None has been replaced.

## Code (written 2026-11-19, after the design gate)

| File | Purpose |
|---|---|
| `code/ck_analysis.py` | `build()` constructs every analysis variable from `stores.csv`, keyed by ROW_ID: FTE1, FTE2 with the closure override, FTE2_R5, DFTE, NJ, the chain dummies, the wage groups, and the sample flags in_w1, in_w2, in_bal, in_r5 and in_t4. There is one entry point for each analysis run: `main-t3`, `main-t4`, `se-alt`, `placebo-hiwage`, `h2-winsor`, `h2-closures-excl` and `h2-nw-rule`. Each writes `runs/<id>/metrics.json` |
| `code/verdict.py` | Step 8, the only place a hypothesis is judged. It reads the metrics of main-t3, main-t4 and h2-winsor. For every H1 target it writes the published value, the absolute difference and a met flag. It also writes the H2 flags |
| `code/test_ck.py` | Step 0c, check-synthetic. It runs the tests on synthetic data only and never reads `stores.csv` |
| `code/run_analysis.sh` | Runs 1-8 in order through `crew.py run`. It refuses to start unless all of the following hold: the latest `reviews/code-r*/review.json` has no open critical or major finding; `ck_analysis.py` and `verdict.py` hash to the values recorded in code-r1; `test_ck.py` hashes to its post-F3 value; and check-synthetic passed on exactly those files (code-r1 F1). It has no replace path (code-r1 F2) |

### Implementation choices the design leaves implicit

None of these changes a sample rule, the FTE definition, an SE method or a decision rule.

1. **Checks in `build()`.** FTE and FTE2 are recomputed from EMPFT, NMGRS and EMPPT, and
   must equal prepare-data's columns. The CLOSED_PERM, CLOSED_TEMP and REFUSED2 flags must
   agree with STATUS2. The closure override is then applied: STATUS2 = 3 sets FTE2 to 0,
   and STATUS2 in {0, 2, 4, 5} sets FTE2 to missing. design.data also says the analysis
   code asserts that the raw file already codes closures this way. So the run stops if the
   raw coding differs from the override, rather than overriding silently.
2. **Wage groups.** WAGE_ST and WAGE_ST2 are rounded to 2 decimals before the
   check.sas comparisons (= 4.25, 4.25 < w < 5.00, >= 5.00). This guards against
   float noise from the CSV. A store with no wave-1 wage is in no NJ wage group, as in
   check.sas's 'BAD WAGE'.
3. **S1 variance.** A variance in (-1e-12, 0) is set to 0. This happens only through
   float noise, when every store in a state has the same change, as in the known-answer
   test. It cannot arise on the study data unless all changes in a state are equal.
4. **Row 5.** The sample is FTE1 non-missing and FTE2_R5 non-missing: sample B plus the
   temporarily closed stores that have FTE1, at FTE2 = 0. The SE uses the balanced form of
   S1.
5. **Percent effects.** `did_r3_pct` divides by the NJ wave-1 mean on the row-3 wave-1
   sample (`mean_w1_nj`). `did_r4_pct` divides by the NJ wave-1 mean on B
   (`mean_w1_bal_nj`).
6. **CR1 in se-alt.** This is statsmodels' `cov_type='cluster'` on ROW_ID with its
   default small-sample factor G/(G-1) x (N-1)/(N-K), the same as Stata's CR1.
7. **Extra report-only metrics.** Some metrics go beyond the lists in analysis_plan, and
   none is judged:
   - counts: `n_r5_*`, `t4_n_all_*` and `t4_n_closed_*`;
   - se-alt: `did_r*_stacked` (the stacked d, which is asserted equal to did_r3 and
     did_r4), `did_r*_se_s1`, and the stacked observation and cluster counts;
   - placebo-hiwage: the within-group changes `chg_*`, plus `n_nj_hi` and `n_nj_hi_w2`;
   - h2-closures-excl: `n_pool` and `did_u`;
   - verdict: `*_rep`, `*_pub` and `*_absdiff` for every target.
8. **Edge cases.** `ratio_w_u` is null if did_u = 0. For H2's sign rule, 0 counts as its own
   sign.
9. **H1(c) flags.** `h1c_point_met` covers the coefficient only. `h1c_n_met` is the N =
   357 data check. `h1c_met` needs N, the coefficient and the SE all met.
10. **Consistency checks inside the runs.** These are identities, with tolerance 1e-9:
    - se-alt fails if the stacked d differs from did_r3 or did_r4, or if the HC2 SE on B
      differs from the S1 SE of did_r4;
    - h2-winsor fails if did_u differs from did_r4;
    - verdict fails if h2-winsor's did_u differs from main-t3's did_r4.

## Runs

### 0c. `check-synthetic` (data-prep, 2026-11-19): 9/9 tests passed; rerun after code-r1 F3: 10/10 passed

The first record is archived by crew.py under `runs/.superseded/check-synthetic-20261119T070120Z/`.

The run used synthetic data only. `code/test_ck.py` generates 410 synthetic stores (331 NJ,
79 PA; seed 20261119) shaped like the public file:

- 6 permanent closures with zero wave-2 components;
- 4 temporary closures, one of which reports NMGRS2 and WAGE_ST2 like ROW_ID 198;
- 1 refusal;
- item non-response in both waves and missing wages;
- SHEET 407 on two stores.

The file is written to `runs/check-synthetic/synthetic_stores.csv` and read back through
`ck.load`. The run does not read `data/derived/stores.csv`.

| Test | What it showed |
|---|---|
| 1. S1 vs HC2 | On the balanced synthetic sample (384 stores), the S1 SE of the DiD equals the HC2 SE of DFTE on NJ to within 1e-10 (0.634782). Each state's S1 SE equals sd(DFTE)/sqrt(n) |
| 2. Stacked regression | On the unbalanced row-3 sample (26 stores in only one wave; 794 store-waves, 410 clusters), the NJ x POST coefficient equals did_r3 and an independent groupby difference of state mean changes (3.927658) |
| 3. Winsorization | The cutoffs equal a hand-written linear-interpolation percentile. The capped set is exactly the stores strictly beyond the cutoffs (16 low, 19 high). On 0..20, the values at the cutoffs (1 and 19) are not capped. On 0..9 the interpolated cutoffs are 0.45 and 8.55 |
| 4. T4 filter | `in_t4` equals a literal transcription of check.sas DATA C1 on 10 hand-built cases (answered with both wages; a missing wave-1 or wave-2 wage; closed with no wages; closed with FTE1 missing; temporary closure; refusal; a missing wave-1 or wave-2 item; PA) and on the whole synthetic file (350 stores) |
| 5. S1 Monte Carlo (extra) | Unbalanced sets (n1 266, n2 251, overlap 224), wave correlation 0.7, 4,000 replications. The mean S1 variance divided by the Monte Carlo variance of the change is 1.035; the population formula gives 1.036 (Monte Carlo SD about 2%). The independent-waves variance is 2.60 times too large |
| 6. Known answer (extra) | Noise-free file (NJ +3, PA -1 per store). did_r3, did_r4, did_r5, b_nj, did_u, did_w, NW-rule b_nj and the closures-excluded did_w all equal 4. Balanced SEs are 0, q05 = -1, q95 = 3, and no store is capped |
| 7. Closures (extra) | Permanent closures get FTE2 = 0 and temporary closures and the refusal get missing; row 5 adds the 4 temporary closures at 0. A file whose components contradict STATUS2, or whose FTE disagrees with its components, is refused by `build()`. With the assertion switched off, the override still codes FTE2 by status |
| 8. Entry points | All seven run ids run on the synthetic file and write every metric that analysis_plan names, as JSON-safe flat output. The internal identities hold, and the capped list is keyed by ROW_ID |
| 9. Verdict (extra) | The 0.05 tolerance is inclusive after rounding to 6 decimals: 2.81 and 2.71 are met against 2.76, and 2.8100011 is not. An SE-only miss gives point_met = 1 and met = 0. N = 356 fails h1c_met but not h1c_point_met. On H2, half the magnitude kept exactly holds, 0.99 of half fails, and a sign flip fails. A did_u that differs from did_r4 is refused |

| 10. Report-only values (code-r1 F3) | Each report-only path is checked against plain-numpy computations from the raw synthetic columns, to 1e-10: row 5; placebo-hiwage, rows 3 and 4; h2-closures-excl (cutoffs, caps by state and tail, closures left uncapped although one lies below the cutoff, and a result different from pooled capping); h2-nw-rule (coefficient, conventional and HC1 SEs, and the within-state means). The h2-nw-rule check uses a variant file with chain and ownership effects, so the controls move the estimate by -0.071. Four deliberate mutations of a scratch copy of `ck_analysis.py` were each caught: row 5 without temporary closures; the high-wage group at > 5.00; the closures-excluded pool taken over all of B; CO_OWNED dropped from the NW rule |

The synthetic numbers in the metrics file describe the generator only, not the study.
Running the test twice gave byte-identical metrics.

Pinned hashes (sha256) that the guard in `run_analysis.sh` checks:

| File | sha256 | Status |
|---|---|---|
| `code/ck_analysis.py` | `632d22031ff807d4cac23bbe985ac5023de6ec872641087391b233b3b8b9ff9a` | as reviewed in code-r1 |
| `code/verdict.py` | `65599671fb46d8580abfaa4ed43850f4d8a4ec70c188130da05a2d66f89d53bd` | as reviewed in code-r1 |
| `code/test_ck.py` | `f53561d8e61e7e3edd39b97ae3abbb73ad7379144266976827d4516a5c879729` | after the F3 edit; code-r1 reviewed `9d065575...` |

The F3 edit added only value tests; the estimators are unchanged.

check-synthetic was rerun with this command after the F3 edit. Its record hashes all
three files:

```bash
cd /Users/brycewang/Auto-Research-Skills
python3 crew/scripts/crew.py run gallery/ss-card-krueger --id check-synthetic \
  --role econometrician --kind data-prep --replace \
  --code code/test_ck.py --code code/ck_analysis.py --code code/verdict.py \
  --output runs/check-synthetic/synthetic_stores.csv \
  --metrics runs/check-synthetic/metrics.json -- .venv/bin/python -I code/test_ck.py
```

### 0d. Code review `reviews/code-r1`: pass, minor F1-F3, fixed

Responses are recorded in the review file.

- **F1.** The guard now pins the code hashes.
- **F2.** The replace path was removed. **Analysis runs are never replaced.** Rerunning one
  needs a deviation that the PI has approved and recorded in this file. crew.py would then
  archive the old record under `runs/.superseded/`.
- **F3.** Test 10 was added, and check-synthetic was rerun.

## Analysis runs 1-8 (2026-11-19, once each, in this order)

Before the runs, `crew.py validate --strict` passed. Then the eight runs ran with `bash
gallery/ss-card-krueger/code/run_analysis.sh`: the guard passed and every run exited 0
with an empty stderr. The script is equivalent to the commands below, from the repository
root. Each command uses `.venv/bin/python -I` relative to the workspace, which is the
working directory crew.py uses.

```bash
cd /Users/brycewang/Auto-Research-Skills
CREW=crew/scripts/crew.py
WS=gallery/ss-card-krueger

# 1. main-t3: Table 3 rows 1-5, S1 SEs (H1(a), H1(b))
python3 $CREW run $WS --id main-t3 --role econometrician --kind analysis \
  --code code/ck_analysis.py --input data/derived/stores.csv \
  --metrics runs/main-t3/metrics.json -- .venv/bin/python -I code/ck_analysis.py main-t3

# 2. main-t4: Table 4 column (i), conventional OLS SE (H1(c))
python3 $CREW run $WS --id main-t4 --role econometrician --kind analysis \
  --code code/ck_analysis.py --input data/derived/stores.csv \
  --metrics runs/main-t4/metrics.json -- .venv/bin/python -I code/ck_analysis.py main-t4

# 3. se-alt: SE constructions not chosen (report only)
python3 $CREW run $WS --id se-alt --role econometrician --kind analysis \
  --code code/ck_analysis.py --input data/derived/stores.csv \
  --metrics runs/se-alt/metrics.json -- .venv/bin/python -I code/ck_analysis.py se-alt

# 4. placebo-hiwage: NJ WAGE_ST >= 5.00 vs PA (descriptive only)
python3 $CREW run $WS --id placebo-hiwage --role econometrician --kind analysis \
  --code code/ck_analysis.py --input data/derived/stores.csv \
  --metrics runs/placebo-hiwage/metrics.json -- .venv/bin/python -I code/ck_analysis.py placebo-hiwage

# 5. h2-winsor: H2, pooled 5/95 winsorization on sample B, capped-store list
python3 $CREW run $WS --id h2-winsor --role econometrician --kind analysis \
  --code code/ck_analysis.py --input data/derived/stores.csv \
  --output runs/h2-winsor/capped.csv \
  --metrics runs/h2-winsor/metrics.json -- .venv/bin/python -I code/ck_analysis.py h2-winsor

# 6. h2-closures-excl: H2 secondary s1 (report only)
python3 $CREW run $WS --id h2-closures-excl --role econometrician --kind analysis \
  --code code/ck_analysis.py --input data/derived/stores.csv \
  --metrics runs/h2-closures-excl/metrics.json -- .venv/bin/python -I code/ck_analysis.py h2-closures-excl

# 7. h2-nw-rule: H2 secondary s2, Neumark-Wascher rule (report only)
python3 $CREW run $WS --id h2-nw-rule --role econometrician --kind analysis \
  --code code/ck_analysis.py --input data/derived/stores.csv \
  --metrics runs/h2-nw-rule/metrics.json -- .venv/bin/python -I code/ck_analysis.py h2-nw-rule

# 8. verdict: H1(a)-(c) target flags, H2 flags
python3 $CREW run $WS --id verdict --role econometrician --kind analysis \
  --code code/verdict.py \
  --input runs/main-t3/metrics.json --input runs/main-t4/metrics.json \
  --input runs/h2-winsor/metrics.json \
  --metrics runs/verdict/metrics.json -- .venv/bin/python -I code/verdict.py
```

### What the runs gave

Numbers are rounded here; the claims carry the unrounded values.

| Target | Replicated | Published | Absolute difference | Met |
|---|---|---|---|---|
| H1(a) DiD row 3 | 2.7536 | 2.76 | 0.0064 | yes |
| H1(a) SE | 1.3100 | 1.36 | **0.04997** | yes, by 0.00003 |
| H1(a) PA change | -2.1656 | -2.16 | 0.0056 | yes |
| H1(a) PA SE | 1.2220 | 1.25 | 0.0280 | yes |
| H1(a) NJ change | 0.5880 | 0.59 | 0.0020 | yes |
| H1(a) NJ SE | 0.4721 | 0.54 | 0.0679 | **no** |
| H1(b) DiD row 4 | 2.7500 | 2.75 | 0.0000 | yes |
| H1(b) SE | 1.3423 | 1.34 | 0.0023 | yes |
| H1(b) PA change | -2.2833 | -2.28 | 0.0033 | yes |
| H1(b) PA SE | 1.2533 | 1.25 | 0.0033 | yes |
| H1(b) NJ change | 0.4667 | 0.47 | 0.0033 | yes |
| H1(b) NJ SE | 0.4808 | 0.48 | 0.0008 | yes |
| H1(c) N | 357 | 357 | 0 | yes (a data check) |
| H1(c) NJ coefficient | 2.3258 | 2.33 | 0.0042 | yes |
| H1(c) SE | 1.1916 | 1.19 | 0.0016 | yes |

- **H1(a): point reproduced within tolerance, but not at published precision; SE
  construction not identified.** (Corrected after results-r1 F1 and F2.)
  - *Points.* All three point targets are within the pre-registered 0.05. At the paper's
    two decimals, though, the replicated row 3 reads 2.75 / -2.17 / 0.59 (DiD / PA / NJ)
    against the published 2.76 / -2.16 / 0.59. The published entries themselves imply
    narrow intervals: since 0.59 - (-2.16) = 2.75 while the DiD prints 2.76, the
    unrounded NJ change must lie in (0.590, 0.595) and the PA change in (-2.165,
    -2.160). The replicated NJ 0.5880 and PA -2.1656 lie outside both. So the 0.0064
    DiD gap is **not rounding**. Its source is unidentified: it could be the data vintage
    (threat T1) or an inconsistency in the published table.

    **Where the gap is** (results-r2 F4). Rows 1-3 use the same wave samples (n_w1 77/321,
    n_w2 77/319). The replicated row 3 is exactly row 2 minus row 1, to machine
    precision, both for the state changes and for the DiD. So the gap is in the unbalanced
    wave means themselves. The published row 3 implies that CK's unrounded wave means
    differ from ours by amounts below the printed precision: enough to raise the NJ
    change by at least 0.0020 and the PA change by at least 0.0006. Rows 1-2 match only
    at their two printed decimals. That test is too coarse to detect differences this
    small, so it is not a contrast with row 3. The balanced row 4 matches.

    This pattern is consistent with a difference among the 26 stores observed in one wave
    only (PA 2 + 2, NJ 12 + 10). It is equally consistent with a sub-rounding data
    difference. Both are conjectures; the data cannot tell them apart. Row 5 matches. In
    Table 4 column (i), the coefficient, SE, N, root MSE and SD match; the dependent mean
    misses by a hair (see H1(c)).
    `sources/notes.md` (Scout, lines 70-72) still calls a 2.75-or-2.76 result "only a
    rounding difference". That is wrong for these values and must not be used in the
    paper.
  - *SEs.* All three row-3 S1 SEs are below the published ones: DiD 1.310 vs 1.36, PA
    1.222 vs 1.25 and NJ 0.472 vs 0.54. The NJ miss is the one design-r1 F1 predicted
    (about 0.48 under S1). Every row-4 SE matches. The DiD SE target sits at the
    boundary (0.04997, met by 0.00003) because all three row-3 SEs are low. The low NJ SE
    does **not** help it pass: it pushes the DiD SE away from 1.36. With the published
    0.54 in place of 0.472, sqrt(1.222^2 + 0.54^2) = 1.336, a difference of only 0.024.
    "Point reproduced; SE construction not identified" therefore applies to the whole
    row-3 SE column. h1a_did_se_met = 1 and h1a_pa_se_met = 1 must not be cited as the
    headline SE being reproduced. The paper should say "within tolerance (by 0.00003);
    row-3 SE construction not identified".
- **H1(b): reproduced.** Every target, points and SEs, is met.
- **H1(c): reproduced.** N = 357 was already known from data prep. These match the
  published values at every printed digit: the coefficient, its SE, N, the root MSE
  (8.79) and the SD of DFTE (8.825).
  - The mean of DFTE does not match exactly (results-r2 F5). It is -0.2375 (unrounded
    -0.237535, so it prints -0.238), against the published -0.237. That is just outside
    the rounding interval [-0.2375, -0.2365), by 0.00004: the DFTE sum over the 357
    stores is -84.800, against at most -84.7875 implied by the published figure.
  - The cause could be a printing convention (truncation) or a sub-rounding data
    difference.
  - It is not a pre-registered target, so H1(c) is unaffected. Claim `reg-dep-mean` now
    prints 4 decimals.
- **H2 holds.** On the 384 balanced stores, the pooled 5/95 cutoffs are -17.425 and
  13.7125. The winsorized DiD is 2.34 (SE 1.10), against 2.75 unwinsorized, a ratio of
  0.851. The sign is the same and more than half the magnitude is kept.
  - Capped stores, low tail: NJ 12, PA 8. One of them is a closure (PA).
  - Capped stores, high tail: NJ 16, PA 4. None is a closure.
  - Low-tail stores were large in wave 1 (mean FTE1 46.0, against 21.0 on B). High-tail
    stores had mean FTE1 19.5.
- **H2 secondaries, report only.**
  - With closures excluded from winsorization, the DiD is 2.33 (ratio 0.849).
  - Under the Neumark-Wascher rule (378 stores), the coefficient is 2.78 (SE 1.16;
    HC1 1.34), with unadjusted NJ +0.66 and PA -2.06. NW report 2.78, NJ +0.66 and
    PA -2.1, so their sample and ours appear to coincide. NW's N is not recorded, so this
    is not established.
- **Other report-only runs.**
  - se-alt: the store-clustered CR1 SEs are 1.31 (row 3) and 1.34 (row 4). The HC2 SE
    on B equals S1 (1.3423). The independent-waves SEs of the row-3 changes are PA 1.65
    and NJ 0.73.
  - Row 5 gives 2.51 (SE 1.35); the published value is 2.51 (1.35).
  - placebo-hiwage, descriptive only: 0.13 (row 3) and 0.13 (row 4). The NJ high-wage
    row-3 change is -2.04, the same as the published -2.04 (Table 3 column vi). But its
    S1 SE is 0.98, against the published 1.14. This is the same under-statement as the
    other row-3 S1 SEs. (This comparison with the published SE was not planned; it is
    reported for completeness.)

### Surprises

1. **Store-clustered SE close to the published one.** The store-clustered CR1 SE of the
   row-3 DiD (1.307) is about as close to the published 1.36 as S1 is (1.310). Neither
   reproduces the NJ within-state SE. This is reported only. The judged method was not
   changed.
2. **H1(a) DiD SE on the boundary.** It passes the 0.05 tolerance by 0.00003, because every
   row-3 S1 SE is low (see H1(a) above). The verdict applies the pre-registered rule
   exactly, but the paper should say how close it is.
3. **Row-3 points not at published precision** (results-r1 F1). The row-3 DiD and PA
   change differ from the published values by more than rounding allows. The gap is in
   the unbalanced wave means (rows 1-3 share the wave samples; rows 1-2 match only at
   printed precision). The balanced row 4, row 5, and the Table 4 coefficient, SE, N,
   root MSE and SD match. Its source is unidentified. A difference among the 26
   single-wave stores is a conjecture.
4. **Table 4 dependent mean** (results-r2 F5): -0.2375 against the published -0.237, just
   outside rounding. Not a target.

## Claims

There are 127 result claims (`claims.jsonl`), all generated from the run metrics and
listed in `paper/numbers.tex`:

- the seed-required `did-fte`, `did-fte-se` and `did-fte-balanced`;
- Table 3 levels and counts;
- every H1 target, with its absolute difference and met flag, plus the point, SE and part
  flags;
- Table 4;
- se-alt and placebo-hiwage;
- H2: estimates, cutoffs, capped counts by state and tail with closures, and the wave-1
  size of capped stores;
- both H2 secondaries.

The absolute differences use 5 decimals, so the H1(a) SE boundary is visible; the other
numbers use 2 decimals, as in the paper. After results-r1, the texts of the H1(a) claims
add two statements. Row 3 is reproduced within tolerance, but not at published precision,
and the gap is not rounding. The row-3 SE met flags must not be read as the headline SE
being reproduced. The values did not change; numbers.tex was regenerated and is identical.
After results-r2, the H1(a) point-claim texts locate the gap in the unbalanced wave means
(F4). They limit the exact Table 4 match to the coefficient, SE, N, root MSE and SD (F5).
`reg-dep-mean` now uses format `.4f`, which changes only how \RegDepMean prints
(-0.2375).

## Deviations

None in the analysis. D1 and D2 are design-level deviations approved at the design gate
(plan.json design.deviations). Two code-review fixes are not deviations from the plan: the
F1-F3 changes before the runs (guard, no replace path, extra tests), and the rerun of the
data-prep run check-synthetic.
