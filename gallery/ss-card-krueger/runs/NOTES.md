# Econometrician notes: ss-card-krueger

This file lists what ran, in order, and the exact commands for every planned run. Nothing in
it is a result on the study data. As of 2026-11-19 no analysis run has touched
`data/derived/stores.csv`. The plan (analysis_plan 0d) blocks analysis runs until the
Reviewer's code review (`reviews/code-r1`) has no open critical or major finding.

## Code (written 2026-11-19, after the design gate)

| File | Purpose |
|---|---|
| `code/ck_analysis.py` | `build()` constructs every analysis variable from `stores.csv`, keyed by ROW_ID: FTE1, FTE2 with the closure override, FTE2_R5, DFTE, NJ, the chain dummies, the wage groups, and the sample flags in_w1, in_w2, in_bal, in_r5 and in_t4. There is one entry point for each analysis run: `main-t3`, `main-t4`, `se-alt`, `placebo-hiwage`, `h2-winsor`, `h2-closures-excl` and `h2-nw-rule`. Each writes `runs/<id>/metrics.json` |
| `code/verdict.py` | Step 8, the only place a hypothesis is judged. It reads the metrics of main-t3, main-t4 and h2-winsor. For every H1 target it writes the published value, the absolute difference and a met flag. It also writes the H2 flags |
| `code/test_ck.py` | Step 0c, check-synthetic. It runs the tests on synthetic data only and never reads `stores.csv` |
| `code/run_analysis.sh` | Runs 1-8 in order through `crew.py run`. It refuses to start unless the latest `reviews/code-r*/review.json` has no open critical or major finding |

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

### 0c. `check-synthetic` (data-prep, 2026-11-19): 9/9 tests passed

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

The synthetic numbers in the metrics file describe the generator only, not the study.
Running the test twice gave byte-identical metrics.

If the code review changes `ck_analysis.py`, `verdict.py` or `test_ck.py`, check-synthetic
must be rerun first. Its record hashes all three files.

```bash
cd /Users/brycewang/Auto-Research-Skills
python3 crew/scripts/crew.py run gallery/ss-card-krueger --id check-synthetic \
  --role econometrician --kind data-prep --replace \
  --code code/test_ck.py --code code/ck_analysis.py --code code/verdict.py \
  --output runs/check-synthetic/synthetic_stores.csv \
  --metrics runs/check-synthetic/metrics.json -- .venv/bin/python -I code/test_ck.py
```

(This is the command that ran, without `--replace`.)

### 0d. Code review: pending (Reviewer, `reviews/code-r1`)

No analysis run is started until it has no open critical or major finding.

## Planned analysis runs (not run yet)

Run these in this order, from the repository root, only after 0d. `bash
gallery/ss-card-krueger/code/run_analysis.sh` runs all eight, with the same guard. Each
command uses `.venv/bin/python -I` relative to the workspace, the working directory that
crew.py uses.

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

Then write the result claims in `design.claims_plan` and run `crew.py numbers` and
`crew.py validate`.

## Deviations

None so far. D1 and D2 are design-level deviations that were approved at the design gate
(see plan.json design.deviations).
