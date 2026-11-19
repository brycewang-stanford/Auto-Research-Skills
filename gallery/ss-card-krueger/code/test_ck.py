"""check-synthetic (plan.json analysis_plan step 0c): test every estimator on synthetic data.

Runs every estimator in code/ck_analysis.py and the decision rules in code/verdict.py on a
synthetic stores file generated here with a fixed seed. It never reads
data/derived/stores.csv or any other study file, so no real outcome is computed.

Assertions (the four required by step 0c come first):
 1. s1-vs-hc2       S1 on a balanced sample equals the HC2 SE of the DFTE-on-NJ regression
                    (per state, S1 equals sd(DFTE)/sqrt(n)).
 2. stacked-did     The stacked store-wave regression FTE ~ NJ + POST + NJ*POST reproduces
                    the difference of state mean changes on an unbalanced sample, and both
                    equal an independent groupby computation.
 3. winsor          Winsorization caps exactly the stores strictly beyond
                    numpy.percentile(..., method='linear'), checked against a hand-written
                    linear-interpolation percentile, including ties at the cutoffs.
 4. t4-filter       The Table 4 sample equals a literal transcription of check.sas DATA C1
                    on hand-built cases and on the whole synthetic file.
 5. s1-monte-carlo  On an unbalanced design, the S1 variance matches the Monte Carlo
                    variance of the change estimator (and the independent-waves SE does
                    not, when waves are correlated).
 6. known-answer    A noise-free file (NJ +3, PA -1 FTE per store) gives every DiD = 4
                    exactly, zero balanced SEs, no capping and b_nj = 4 with controls.
 7. closures        The closure override sets permanent closures to 0 and temporary
                    closures / refusals to missing whatever the components say; the strict
                    build refuses a file whose raw coding differs; row 5 adds the temporary
                    closures at 0.
 8. entry-points    Every run id in ck_analysis.RUN_IDS runs on the synthetic file, with
                    its internal checks (stacked d = did, HC2 = S1, did_u = did_r4), writes
                    JSON-safe flat metrics and, for h2-winsor, a capped list keyed by ROW_ID.
 9. verdict         verdict.judge on hand-built metrics: the 0.05 tolerance is inclusive
                    after rounding to 6 decimals, N must match exactly, SE-only misses give
                    point_met = 1 and met = 0, and the H2 sign / half rules.
10. report-only     (code-r1 F3) Values of the report-only paths against plain-numpy
                    computations from the raw synthetic columns: row 5, placebo-hiwage
                    (rows 3 and 4), h2-closures-excl (cutoffs, caps by state and tail,
                    closures left uncapped) and h2-nw-rule (coefficient, conventional and
                    HC1 SEs, with controls that move the estimate).

Outputs: runs/check-synthetic/synthetic_stores.csv and runs/check-synthetic/metrics.json
(flat: pass flags and synthetic-only numbers). Exit code 1 if any assertion fails.

Usage, from the workspace root:
    .venv/bin/python -I code/test_ck.py
"""

from __future__ import annotations

import json
import math
import sys
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))  # -I drops the script dir
import ck_analysis as ck  # noqa: E402
import verdict  # noqa: E402

SEED = 20261119
OUT_DIR = Path("runs/check-synthetic")
SYN_CSV = OUT_DIR / "synthetic_stores.csv"
CSV_COLUMNS = ["ROW_ID", "SHEET", "CHAIN", "CO_OWNED", "STATE", "EMPFT", "EMPPT", "NMGRS",
               "WAGE_ST", "STATUS2", "EMPFT2", "EMPPT2", "NMGRS2", "WAGE_ST2", "FTE", "FTE2",
               "CLOSED_PERM", "CLOSED_TEMP", "REFUSED2"]


# ------------------------------------------------------------------ synthetic data
def add_derived(df: pd.DataFrame) -> pd.DataFrame:
    """FTE, FTE2 and status flags exactly as code/prepare_data.py builds them."""
    df = df.copy()
    df["FTE"] = df["EMPFT"] + df["NMGRS"] + 0.5 * df["EMPPT"]
    df["FTE2"] = df["EMPFT2"] + df["NMGRS2"] + 0.5 * df["EMPPT2"]
    df["CLOSED_PERM"] = (df["STATUS2"] == 3).astype(int)
    df["CLOSED_TEMP"] = df["STATUS2"].isin([2, 4, 5]).astype(int)
    df["REFUSED2"] = (df["STATUS2"] == 0).astype(int)
    return df[CSV_COLUMNS]


def synthetic_stores(seed: int = SEED) -> pd.DataFrame:
    """410 synthetic stores shaped like the public file (331 NJ, 79 PA; closures,
    refusal, item non-response, wage groups, a duplicated SHEET). Nothing is real."""
    rng = np.random.default_rng(seed)
    n_nj, n_pa = 331, 79
    n = n_nj + n_pa
    state = np.r_[np.ones(n_nj, int), np.zeros(n_pa, int)]
    df = pd.DataFrame({"ROW_ID": np.arange(1, n + 1), "STATE": state})
    df["SHEET"] = df["ROW_ID"] + 1000
    df.loc[[41, 167], "SHEET"] = 407                 # two different stores share a SHEET
    df["CHAIN"] = rng.integers(1, 5, n)
    df["CO_OWNED"] = rng.integers(0, 2, n)
    df["EMPFT"] = rng.poisson(8, n).astype(float)
    df["EMPPT"] = rng.poisson(18, n).astype(float)
    df["NMGRS"] = rng.poisson(3, n).astype(float) + rng.choice([0, 0.5], n)
    # wave 2: store-level persistence plus noise, a synthetic state shift, fat tails
    shift = np.where(state == 1, 1.0, -2.0)
    noise = rng.standard_t(3, n) * 3
    df["EMPFT2"] = np.maximum(0, np.round(df["EMPFT"] + shift + noise))
    df["EMPPT2"] = np.maximum(0, np.round(df["EMPPT"] + rng.normal(0, 4, n)))
    df["NMGRS2"] = np.maximum(0, df["NMGRS"] + rng.integers(-1, 2, n))
    df["WAGE_ST"] = rng.choice([4.25, 4.50, 4.75, 4.99, 5.00, 5.25], n)
    df["WAGE_ST2"] = np.where(state == 1, 5.05, rng.choice([4.25, 4.50, 4.75, 5.00], n))
    # second-wave status (indices are 0-based positions; ROW_ID = position + 1)
    df["STATUS2"] = 1
    perm = [3, 50, 120, 200, 300, 350]                # 5 NJ, 1 PA
    df.loc[perm, "STATUS2"] = 3
    df.loc[[10, 11], "STATUS2"] = 2
    df.loc[12, "STATUS2"] = 4
    df.loc[13, "STATUS2"] = 5
    df.loc[14, "STATUS2"] = 0
    df.loc[perm, ["EMPFT2", "EMPPT2", "NMGRS2"]] = 0.0
    df.loc[perm, "WAGE_ST2"] = np.nan
    df.loc[[10, 11, 12, 13, 14], ["EMPFT2", "EMPPT2", "NMGRS2", "WAGE_ST2"]] = np.nan
    df.loc[10, ["NMGRS2", "WAGE_ST2"]] = [3.0, 5.05]  # renovation store reports some items
    # item non-response: wave 1 (12 stores, 2 PA), wave 2 among answered (9, 2 PA)
    for i, col in zip([20, 21, 22, 60, 61, 62, 90, 91, 140, 141, 340, 360],
                      ["EMPFT", "EMPPT", "NMGRS"] * 4):
        df.loc[i, col] = np.nan
    for i, col in zip([30, 31, 70, 71, 100, 160, 250, 345, 370],
                      ["EMPFT2", "EMPPT2", "NMGRS2"] * 3):
        df.loc[i, col] = np.nan
    df.loc[rng.choice(n, 20, replace=False), "WAGE_ST"] = np.nan
    answered = np.flatnonzero(df["STATUS2"].to_numpy() == 1)
    df.loc[rng.choice(answered, 15, replace=False), "WAGE_ST2"] = np.nan
    return add_derived(df)


def known_answer_stores() -> pd.DataFrame:
    """Noise-free file: no closures, no missing values; every NJ store +3 FTE, PA -1."""
    n_nj, n_pa = 40, 20
    k = np.arange(n_nj + n_pa)
    state = np.r_[np.ones(n_nj, int), np.zeros(n_pa, int)]
    df = pd.DataFrame({"ROW_ID": k + 1, "SHEET": k + 1, "STATE": state,
                       "CHAIN": k % 4 + 1, "CO_OWNED": (k // 3) % 2,
                       "EMPFT": 5.0 + k % 7, "EMPPT": 10.0 + 2 * (k % 5), "NMGRS": 2.0 + k % 3,
                       "WAGE_ST": np.where(k % 3 == 0, 4.25, 5.00), "STATUS2": 1})
    df["EMPFT2"] = df["EMPFT"] + np.where(state == 1, 3.0, -1.0)
    df["EMPPT2"], df["NMGRS2"] = df["EMPPT"], df["NMGRS"]
    df["WAGE_ST2"] = 5.05
    return add_derived(df)


# ------------------------------------------------------------------- tests
def r(x: float, nd: int = 6) -> float:
    """Round for the metrics file, so a clean rerun compares stable numbers."""
    return float(round(float(x), nd)) + 0.0


def test_s1_vs_hc2(d: pd.DataFrame) -> dict:
    t3 = ck.table3(d)
    b = d[d["in_bal"]]
    hc2 = float(ck.ols(b["DFTE"], b[["NJ"]], cov="HC2").bse["NJ"])
    diff = abs(hc2 - t3["did_r4_se"])
    assert diff < 1e-10, f"S1 {t3['did_r4_se']} vs HC2 {hc2}"
    per_state = 0.0
    for s, tag in ((0, "pa"), (1, "nj")):
        v = b.loc[b["NJ"] == s, "DFTE"]
        per_state = max(per_state, abs(v.std(ddof=1) / math.sqrt(len(v)) - t3[f"chg_r4_{tag}_se"]))
        assert abs(v.mean() - t3[f"chg_r4_{tag}"]) < 1e-10
    assert per_state < 1e-10
    return {"s1_hc2_se": r(hc2), "s1_hc2_maxdiff_lt_1e10": 1}


def test_stacked(d: pd.DataFrame) -> dict:
    t3 = ck.table3(d)
    assert (d["in_w1"] != d["in_w2"]).sum() > 0, "synthetic row-3 sample must be unbalanced"
    fit, nobs, ncl = ck.stacked(d, "in_w1", "in_w2")
    dd = float(fit.params["NJ_POST"])
    # independent computation of the difference of state mean changes
    g1 = d[d["in_w1"]].groupby("NJ")["FTE1"].mean()
    g2 = d[d["in_w2"]].groupby("NJ")["FTE2"].mean()
    direct = (g2[1] - g1[1]) - (g2[0] - g1[0])
    assert abs(dd - t3["did_r3"]) < 1e-10 and abs(direct - t3["did_r3"]) < 1e-10, \
        f"stacked {dd}, direct {direct}, table3 {t3['did_r3']}"
    assert nobs == int(d["in_w1"].sum() + d["in_w2"].sum())
    assert ncl == int((d["in_w1"] | d["in_w2"]).sum())
    return {"stacked_did_r3": r(dd), "stacked_nobs": nobs, "stacked_nclusters": ncl,
            "stacked_unbalanced_stores": int((d["in_w1"] != d["in_w2"]).sum())}


def pct_linear(x: np.ndarray, p: float) -> float:
    """Hand-written linear-interpolation percentile (numpy 'linear' / type 7)."""
    s = np.sort(x)
    h = (len(s) - 1) * p / 100.0
    lo = math.floor(h)
    hi = min(lo + 1, len(s) - 1)
    return float(s[lo] + (h - lo) * (s[hi] - s[lo]))


def test_winsor(d: pd.DataFrame) -> dict:
    out = {}
    b = d[d["in_bal"]]
    x = b["DFTE"]
    wz = ck.winsorize(x)
    q05, q95 = pct_linear(x.to_numpy(), 5), pct_linear(x.to_numpy(), 95)
    assert abs(q05 - wz["q05"]) < 1e-12 and abs(q95 - wz["q95"]) < 1e-12
    exp_low, exp_high = x < q05, x > q95
    assert (exp_low == wz["low"]).all() and (exp_high == wz["high"]).all()
    assert (wz["w"] == np.minimum(np.maximum(x, q05), q95)).all()
    assert (wz["w"][~(exp_low | exp_high)] == x[~(exp_low | exp_high)]).all()
    out.update({"winsor_syn_q05": r(q05), "winsor_syn_q95": r(q95),
                "winsor_syn_n_low": int(exp_low.sum()), "winsor_syn_n_high": int(exp_high.sum())})
    # ties at the cutoffs: 0..20 -> q05 = 1, q95 = 19 exactly; 1 and 19 are not capped
    t = pd.Series(np.arange(21, dtype=float))
    wt = ck.winsorize(t)
    assert wt["q05"] == 1.0 and wt["q95"] == 19.0
    assert list(t[wt["low"]]) == [0.0] and list(t[wt["high"]]) == [20.0]
    # an interpolated cutoff: 0..9 -> q05 = 0.45, q95 = 8.55
    u = pd.Series(np.arange(10, dtype=float))
    wu = ck.winsorize(u)
    assert abs(wu["q05"] - 0.45) < 1e-12 and abs(wu["q95"] - 8.55) < 1e-12
    assert np.allclose(wu["w"], [0.45] + list(range(1, 9)) + [8.55], rtol=0, atol=1e-12)
    assert list(u[wu["low"]]) == [0.0] and list(u[wu["high"]]) == [9.0]
    # pooled cutoffs from a different pool (closures-excluded variant)
    pool = x[b["closed_perm"] == 0]
    wp = ck.winsorize(pool)
    assert abs(wp["q05"] - pct_linear(pool.to_numpy(), 5)) < 1e-12
    out["winsor_ties_ok"] = 1
    return out


def checksas_c1(df: pd.DataFrame) -> pd.Series:
    """Literal check.sas: EMPTOT, EMPTOT2, DEMP with missing propagation; CLOSED; DWAGE;
    DATA C1: IF DEMP NE . ; IF CLOSED=1 OR (CLOSED=0 AND DWAGE NE .)."""
    emptot = df["EMPPT"] * .5 + df["EMPFT"] + df["NMGRS"]
    emptot2 = df["EMPPT2"] * .5 + df["EMPFT2"] + df["NMGRS2"]
    demp = emptot2 - emptot
    closed = (df["STATUS2"] == 3).astype(int)
    dwage = df["WAGE_ST2"] - df["WAGE_ST"]
    keep = demp.notna() & ((closed == 1) | ((closed == 0) & dwage.notna()))
    return pd.Series(keep.to_numpy(), index=df["ROW_ID"].to_numpy())


def test_t4_filter(syn: pd.DataFrame) -> dict:
    base = dict(SHEET=1, CHAIN=1, CO_OWNED=0, STATE=1, EMPFT=10.0, EMPPT=10.0, NMGRS=2.0,
                WAGE_ST=4.50, STATUS2=1, EMPFT2=11.0, EMPPT2=8.0, NMGRS2=2.0, WAGE_ST2=5.05)
    cases = [  # (overrides, expected in T4)
        ({}, True),                                             # answered, both wages
        ({"WAGE_ST2": np.nan}, False),                          # wave-2 wage missing
        ({"WAGE_ST": np.nan}, False),                           # wave-1 wage missing
        ({"STATUS2": 3, "EMPFT2": 0.0, "EMPPT2": 0.0, "NMGRS2": 0.0,
          "WAGE_ST2": np.nan, "WAGE_ST": np.nan}, True),        # closed: wages not needed
        ({"STATUS2": 3, "EMPFT2": 0.0, "EMPPT2": 0.0, "NMGRS2": 0.0,
          "EMPPT": np.nan}, False),                             # closed but FTE1 missing
        ({"STATUS2": 2, "EMPFT2": np.nan, "EMPPT2": np.nan, "NMGRS2": 3.0}, False),  # temp
        ({"STATUS2": 0, "EMPFT2": np.nan, "EMPPT2": np.nan, "NMGRS2": np.nan,
          "WAGE_ST2": np.nan}, False),                          # refused
        ({"EMPPT2": np.nan}, False),                            # wave-2 item missing
        ({"STATE": 0, "WAGE_ST": 4.25, "WAGE_ST2": 4.25}, True),  # PA, wage unchanged
        ({"NMGRS": np.nan}, False),                             # wave-1 item missing
    ]
    rows = []
    for i, (over, _) in enumerate(cases):
        row = dict(base, ROW_ID=i + 1, SHEET=i + 1)
        row.update(over)
        rows.append(row)
    hand = add_derived(pd.DataFrame(rows))
    d = ck.build(hand)
    want = [w for _, w in cases]
    assert list(d["in_t4"]) == want, f"in_t4 {list(d['in_t4'])} != {want}"
    assert list(checksas_c1(hand)) == want
    # whole synthetic file
    ds = ck.build(syn)
    lit = checksas_c1(syn).reindex(ds.index)
    assert (lit == ds["in_t4"]).all()
    return {"t4_hand_cases": len(cases), "t4_syn_n": int(ds["in_t4"].sum())}


def test_s1_monte_carlo() -> dict:
    rng = np.random.default_rng(SEED + 1)
    n, reps = 300, 4000
    sd1, sd2, rho = 9.0, 10.0, 0.7
    cov = np.array([[sd1 ** 2, rho * sd1 * sd2], [rho * sd1 * sd2, sd2 ** 2]])
    a1 = rng.random(n) > 0.10           # fixed missingness pattern (conditioning on sets)
    a2 = rng.random(n) > 0.15
    n1, n2, n12 = a1.sum(), a2.sum(), (a1 & a2).sum()
    true_var = sd1 ** 2 / n1 + sd2 ** 2 / n2 - 2 * cov[0, 1] * n12 / (n1 * n2)
    chg = np.empty(reps)
    s1var = np.empty(reps)
    for k in range(reps):
        y = rng.multivariate_normal([20.0, 21.0], cov, n)
        res = ck.s1_change(pd.Series(y[:, 0]), pd.Series(y[:, 1]), pd.Series(a1), pd.Series(a2))
        chg[k], s1var[k] = res["chg"], res["se"] ** 2
    mc_var = chg.var(ddof=1)
    ratio_s1 = s1var.mean() / mc_var
    ratio_true = true_var / mc_var
    indep = sd1 ** 2 / n1 + sd2 ** 2 / n2
    # MC sd of a variance estimate with 4000 draws is about 2.2%; allow 6%
    assert abs(ratio_s1 - 1) < 0.06 and abs(ratio_true - 1) < 0.06, (ratio_s1, ratio_true)
    assert indep / mc_var > 1.5, "independent-waves variance should be far too large here"
    return {"mc_reps": reps, "mc_n1": int(n1), "mc_n2": int(n2), "mc_n12": int(n12),
            "mc_ratio_s1_var_to_mc_var": r(ratio_s1, 4), "mc_ratio_true_var_to_mc_var": r(ratio_true, 4),
            "mc_ratio_indep_var_to_mc_var": r(indep / mc_var, 4)}


def test_known_answer() -> dict:
    d = ck.build(known_answer_stores())
    t3, t4 = ck.table3(d), ck.table4(d)
    h2, _ = ck.h2_winsor(d)
    nw = ck.h2_nw_rule(d)
    s1x = ck.h2_closures_excl(d)
    for name, v in (("did_r3", t3["did_r3"]), ("did_r4", t3["did_r4"]), ("did_r5", t3["did_r5"]),
                    ("b_nj", t4["b_nj"]), ("did_u", h2["did_u"]), ("did_w", h2["did_w"]),
                    ("nw_b_nj", nw["b_nj"]), ("s1x_did_w", s1x["did_w"])):
        assert abs(v - 4.0) < 1e-9, f"{name} = {v}, expected 4"
    assert abs(t3["chg_r4_nj"] - 3.0) < 1e-12 and abs(t3["chg_r4_pa"] + 1.0) < 1e-12
    assert t3["did_r4_se"] < 1e-6 and t3["did_r3_se"] < 1e-6  # zero up to float noise
    assert h2["q05"] == -1.0 and h2["q95"] == 3.0
    assert sum(h2[f"capped_{t}_{s}"] for t in ("low", "high") for s in ("nj", "pa")) == 0
    assert t4["n"] == 60 and h2["ratio_w_u"] == 1.0
    return {"known_did_r3": r(t3["did_r3"]), "known_b_nj": r(t4["b_nj"]),
            "known_did_w": r(h2["did_w"]), "known_nw_b_nj": r(nw["b_nj"])}


def test_closures(syn: pd.DataFrame) -> dict:
    d = ck.build(syn)
    assert (d.loc[d["closed_perm"] == 1, "FTE2"] == 0).all()
    assert d.loc[(d["closed_temp"] == 1) | (d["refused"] == 1), "FTE2"].isna().all()
    assert (d.loc[d["closed_temp"] == 1, "FTE2_R5"] == 0).all()
    assert d.loc[d["refused"] == 1, "FTE2_R5"].isna().all()
    t3 = ck.table3(d)
    add = int(((d["closed_temp"] == 1) & d["in_w1"]).sum())
    assert t3["n_r5_nj"] + t3["n_r5_pa"] == t3["n_bal_nj"] + t3["n_bal_pa"] + add
    # a raw file whose components contradict the status: strict build refuses,
    # override sets FTE2 by status anyway
    bad = syn.copy()
    i_perm = bad.index[bad["STATUS2"] == 3][0]
    i_temp = bad.index[bad["STATUS2"] == 4][0]
    bad.loc[i_perm, ["EMPFT2", "EMPPT2", "NMGRS2"]] = [4.0, 6.0, 1.0]
    bad.loc[i_temp, ["EMPFT2", "EMPPT2", "NMGRS2"]] = [4.0, 6.0, 1.0]
    bad = add_derived(bad)
    try:
        ck.build(bad)
        raise AssertionError("strict build accepted contradictory closure coding")
    except ValueError:
        pass
    db = ck.build(bad, assert_raw_closure_coding=False)
    assert db.loc[bad.loc[i_perm, "ROW_ID"], "FTE2"] == 0.0
    assert math.isnan(db.loc[bad.loc[i_temp, "ROW_ID"], "FTE2"])
    # prepare-data's FTE column must agree with the components
    worse = syn.copy()
    worse.loc[worse.index[0], "FTE"] += 1
    try:
        ck.build(worse)
        raise AssertionError("build accepted an FTE that differs from its components")
    except ValueError:
        pass
    return {"closures_r5_added": add, "syn_n_bal": t3["n_bal_nj"] + t3["n_bal_pa"]}


def test_entry_points(syn: pd.DataFrame) -> dict:
    d = ck.build(syn)
    out: dict = {}
    results = {}
    for run_id in ck.RUN_IDS:
        m, extras = ck.compute(run_id, d)
        json.dumps(ck.flat(m), allow_nan=False)
        results[run_id] = m
        out[f"ep_{run_id.replace('-', '_')}_n_metrics"] = len(m)
    t3, t4, h2 = results["main-t3"], results["main-t4"], results["h2-winsor"]
    required = {
        "main-t3": ["n_w1_pa", "n_w1_nj", "n_w2_pa", "n_w2_nj", "n_both_pa", "n_both_nj",
                    "mean_w1_pa", "mean_w1_pa_se", "mean_w2_nj", "mean_w2_nj_se", "row1_diff",
                    "row1_diff_se", "row2_diff", "row2_diff_se", "chg_r3_pa", "chg_r3_pa_se",
                    "chg_r3_nj", "chg_r3_nj_se", "did_r3", "did_r3_se", "did_r3_pct",
                    "n_bal_pa", "n_bal_nj", "mean_w1_bal_nj", "chg_r4_pa", "chg_r4_pa_se",
                    "chg_r4_nj", "chg_r4_nj_se", "did_r4", "did_r4_se", "did_r4_pct",
                    "chg_r5_pa", "chg_r5_pa_se", "chg_r5_nj", "chg_r5_nj_se", "did_r5", "did_r5_se"],
        "main-t4": ["t4_n_fte_both_nj", "t4_n_fte_both_pa", "t4_n_nj", "t4_n_pa", "n", "n_nj",
                    "n_pa", "b_nj", "se_nj", "se_nj_hc1", "const", "root_mse", "dep_mean", "dep_sd"],
        "se-alt": ["did_r3_cr1_se", "did_r4_cr1_se", "did_r4_hc1_se", "did_r4_hc2_se",
                   "chg_r3_pa_indep_se", "chg_r3_nj_indep_se"],
        "placebo-hiwage": ["plac_r3", "plac_r3_se", "plac_r4", "plac_r4_se", "n_nj_hi_w1", "n_nj_hi_bal"],
        "h2-winsor": ["n", "n_nj", "n_pa", "n_closed_nj", "n_closed_pa", "q05", "q95", "did_u",
                      "did_u_se", "did_w", "did_w_se", "ratio_w_u", "capped_low_nj", "capped_low_pa",
                      "capped_high_nj", "capped_high_pa", "capped_low_closed", "capped_high_closed",
                      "fte1_mean_bal", "fte1_mean_capped_low", "fte1_mean_capped_high"],
        "h2-closures-excl": ["q05_nc", "q95_nc", "did_w", "did_w_se", "ratio_w_u", "capped_low_nj",
                             "capped_low_pa", "capped_high_nj", "capped_high_pa"],
        "h2-nw-rule": ["n", "n_nj", "n_pa", "b_nj", "se_nj", "se_nj_hc1", "chg_nj", "chg_pa"],
    }
    for run_id, keys in required.items():
        missing = [k for k in keys if k not in results[run_id]]
        assert not missing, f"{run_id} lacks planned metrics {missing}"
    # cross-run identities
    assert abs(h2["did_u"] - t3["did_r4"]) < 1e-12
    assert abs(results["se-alt"]["did_r4_hc2_se"] - t3["did_r4_se"]) < 1e-10
    assert t4["n"] == t4["t4_n_nj"] + t4["t4_n_pa"]
    assert results["h2-nw-rule"]["n"] == h2["n"] - h2["n_closed_nj"] - h2["n_closed_pa"]
    # the capped list is keyed by ROW_ID and matches the counts
    _, extras = ck.compute("h2-winsor", d)
    capped = extras["capped.csv"]
    assert capped["ROW_ID"].is_unique
    assert len(capped) == sum(h2[f"capped_{t}_{s}"] for t in ("low", "high") for s in ("nj", "pa"))
    # SHEET 407 is duplicated in the synthetic file and ROW_ID still keys the build
    assert (d["SHEET"] == 407).sum() == 2 and d.index.is_unique
    # the verdict runs on these synthetic metrics end to end
    v = verdict.judge(ck.flat(t3), ck.flat(t4), ck.flat(h2))
    for k in ("h1a_point_met", "h1a_se_met", "h1a_met", "h1b_met", "h1c_n_met",
              "h1c_point_met", "h1c_se_met", "h1c_met", "h2_sign_same", "h2_half_kept", "h2_holds"):
        assert v[k] in (0, 1), k
    out.update({"syn_did_r3": r(t3["did_r3"]), "syn_did_r3_se": r(t3["did_r3_se"]),
                "syn_did_r4": r(t3["did_r4"]), "syn_did_r4_se": r(t3["did_r4_se"]),
                "syn_t4_b_nj": r(t4["b_nj"]), "syn_t4_n": t4["n"],
                "syn_h2_did_w": r(h2["did_w"]), "syn_h2_capped": len(capped),
                "syn_did_r3_cr1_se": r(results["se-alt"]["did_r3_cr1_se"])})
    return out


def test_verdict() -> dict:
    def t3(**kw):
        base = {"did_r3": 2.76, "did_r3_se": 1.36, "chg_r3_pa": -2.16, "chg_r3_pa_se": 1.25,
                "chg_r3_nj": 0.59, "chg_r3_nj_se": 0.54, "did_r4": 2.75, "did_r4_se": 1.34,
                "chg_r4_pa": -2.28, "chg_r4_pa_se": 1.25, "chg_r4_nj": 0.47, "chg_r4_nj_se": 0.48}
        base.update(kw)
        return base
    t4 = {"n": 357, "b_nj": 2.33, "se_nj": 1.19}
    h2 = {"did_u": 2.75, "did_w": 2.0}
    v = verdict.judge(t3(), t4, h2)
    assert all(v[f"{p}_met"] == 1 for p in ("h1a", "h1b", "h1c")) and v["h2_holds"] == 1
    # inclusive tolerance at exactly 0.05 (floating point: 2.81 - 2.76 != 0.05 exactly)
    assert verdict.judge(t3(did_r3=2.81), t4, h2)["h1a_did_met"] == 1
    assert verdict.judge(t3(did_r3=2.71), t4, h2)["h1a_did_met"] == 1
    assert verdict.judge(t3(did_r3=2.8100011), t4, h2)["h1a_did_met"] == 0
    assert verdict.judge(t3(chg_r3_pa=-2.21), t4, h2)["h1a_pa_met"] == 1
    # an SE-only miss: point reproduced, part not reproduced
    v = verdict.judge(t3(chg_r3_nj_se=0.48), t4, h2)
    assert (v["h1a_point_met"], v["h1a_se_met"], v["h1a_met"]) == (1, 0, 0)
    # N must match exactly; an N miss fails the part but not the coefficient flag
    v = verdict.judge(t3(), {"n": 356, "b_nj": 2.33, "se_nj": 1.19}, h2)
    assert (v["h1c_n_met"], v["h1c_point_met"], v["h1c_met"]) == (0, 1, 0)
    # H2: half kept exactly (inclusive), below half, sign flip
    j = lambda w: verdict.judge(t3(did_r4=2.0), t4, {"did_u": 2.0, "did_w": w})  # noqa: E731
    assert j(1.0)["h2_holds"] == 1
    assert (j(0.99)["h2_half_kept"], j(0.99)["h2_holds"]) == (0, 0)
    assert (j(-3.0)["h2_sign_same"], j(-3.0)["h2_holds"]) == (0, 0)
    # did_u must equal did_r4
    try:
        verdict.judge(t3(did_r4=2.0), t4, {"did_u": 2.1, "did_w": 2.0})
        raise AssertionError("verdict accepted did_u != did_r4")
    except AssertionError as e:
        if "accepted" in str(e):
            raise
    return {"verdict_cases": 12}


# ------------------------------------------- report-only runs: plain-numpy values (code-r1 F3)
def raw_arrays(syn: pd.DataFrame) -> dict:
    """Variables rebuilt with numpy from the raw synthetic columns, without ck.build."""
    a = {c: syn[c].to_numpy(float) for c in ("EMPFT", "EMPPT", "NMGRS", "EMPFT2", "EMPPT2",
                                              "NMGRS2", "WAGE_ST", "STATE", "STATUS2",
                                              "CHAIN", "CO_OWNED")}
    st = a["STATUS2"]
    fte1 = a["EMPFT"] + a["NMGRS"] + 0.5 * a["EMPPT"]
    fte2 = a["EMPFT2"] + a["NMGRS2"] + 0.5 * a["EMPPT2"]
    fte2 = np.where(st == 3, 0.0, fte2)
    fte2 = np.where(np.isin(st, [0, 2, 4, 5]), np.nan, fte2)
    fte2_r5 = np.where(np.isin(st, [2, 4, 5]), 0.0, fte2)
    return {"fte1": fte1, "fte2": fte2, "fte2_r5": fte2_r5, "nj": a["STATE"] == 1,
            "perm": st == 3, "temp": np.isin(st, [2, 4, 5]), "chain": a["CHAIN"],
            "co": a["CO_OWNED"], "wage": a["WAGE_ST"]}


def np_s1(y1: np.ndarray, y2: np.ndarray, a1: np.ndarray, a2: np.ndarray) -> tuple[float, float]:
    """S1 written out with numpy sums (no np.var / np.cov)."""
    a12 = a1 & a2
    n1, n2, n12 = a1.sum(), a2.sum(), a12.sum()
    m1, m2 = y1[a1].sum() / n1, y2[a2].sum() / n2
    v1 = ((y1[a1] - m1) ** 2).sum() / (n1 - 1)
    v2 = ((y2[a2] - m2) ** 2).sum() / (n2 - 1)
    c = ((y1[a12] - y1[a12].mean()) * (y2[a12] - y2[a12].mean())).sum() / (n12 - 1)
    return m2 - m1, math.sqrt(v1 / n1 + v2 / n2 - 2 * c * n12 / (n1 * n2))


def np_did(nj_chg: tuple, pa_chg: tuple) -> tuple[float, float]:
    return nj_chg[0] - pa_chg[0], math.sqrt(nj_chg[1] ** 2 + pa_chg[1] ** 2)


def close(a: float, b: float, tol: float = 1e-10) -> bool:
    return abs(a - b) <= tol


def test_report_only_values(syn: pd.DataFrame) -> dict:
    v = raw_arrays(syn)
    d = ck.build(syn)
    w1, w2 = ~np.isnan(v["fte1"]), ~np.isnan(v["fte2"])
    bal = w1 & w2
    nj, pa = v["nj"], ~v["nj"]
    dfte = v["fte2"] - v["fte1"]
    out: dict = {}

    # row 5: B plus temporary closures (with FTE1) at FTE2 = 0, balanced-form S1
    r5 = w1 & ~np.isnan(v["fte2_r5"])
    d5 = v["fte2_r5"] - v["fte1"]
    chg = {}
    for tag, s in (("nj", nj), ("pa", pa)):
        x = d5[r5 & s]
        chg[tag] = (x.mean(), x.std(ddof=1) / math.sqrt(len(x)))
    did5, se5 = np_did(chg["nj"], chg["pa"])
    t3 = ck.table3(d)
    assert close(t3["did_r5"], did5) and close(t3["did_r5_se"], se5), (t3["did_r5"], did5)
    assert close(t3["chg_r5_nj"], chg["nj"][0]) and close(t3["chg_r5_pa_se"], chg["pa"][1])
    assert (r5 & v["temp"]).sum() > 0 and not close(did5, t3["did_r4"], 1e-6)
    out["f3_row5_did"] = r(did5)

    # placebo-hiwage: NJ stores with WAGE_ST >= 5.00 vs PA, rows 3 and 4
    hi = nj & (np.round(v["wage"], 2) >= 5.00)
    pl = ck.placebo_hiwage(d)
    for label, a1, a2 in (("r3", w1, w2), ("r4", bal, bal)):
        c_hi = np_s1(v["fte1"], v["fte2"], a1 & hi, a2 & hi)
        c_pa = np_s1(v["fte1"], v["fte2"], a1 & pa, a2 & pa)
        did, se = np_did(c_hi, c_pa)
        assert close(pl[f"plac_{label}"], did) and close(pl[f"plac_{label}_se"], se), label
    assert pl["n_nj_hi_w1"] == int((w1 & hi).sum()) and pl["n_nj_hi_bal"] == int((bal & hi).sum())
    out["f3_placebo_r3"] = r(pl["plac_r3"])

    # h2-closures-excl: pool and caps on B minus permanent closures; closures keep DFTE
    open_b = bal & ~v["perm"]
    q05, q95 = pct_linear(dfte[open_b], 5), pct_linear(dfte[open_b], 95)
    wv = dfte.copy()
    wv[open_b] = np.minimum(np.maximum(dfte[open_b], q05), q95)
    did_w = wv[bal & nj].mean() - wv[bal & pa].mean()
    se_w = math.sqrt(wv[bal & nj].var(ddof=1) / (bal & nj).sum()
                     + wv[bal & pa].var(ddof=1) / (bal & pa).sum())
    did_u = dfte[bal & nj].mean() - dfte[bal & pa].mean()
    cx = ck.h2_closures_excl(d)
    assert close(cx["q05_nc"], q05) and close(cx["q95_nc"], q95)
    assert close(cx["did_w"], did_w) and close(cx["did_w_se"], se_w) and close(cx["did_u"], did_u)
    assert close(cx["ratio_w_u"], did_w / did_u)
    for tail, mask in (("low", dfte < q05), ("high", dfte > q95)):
        for tag, s in (("nj", nj), ("pa", pa)):
            assert cx[f"capped_{tail}_{tag}"] == int((open_b & mask & s).sum()), (tail, tag)
    assert (bal & v["perm"]).sum() > 0 and (dfte[bal & v["perm"]] < q05).any(), \
        "test needs a closure below the open-store cutoff, left uncapped"
    # and differs from pooled winsorization, which does cap closures
    h2, _ = ck.h2_winsor(d)
    assert not close(h2["did_w"], cx["did_w"], 1e-6)
    out["f3_closures_excl_did_w"] = r(did_w)

    # h2-nw-rule: OLS of DFTE on NJ + BK + KFC + ROYS + CO_OWNED, B minus closures.
    # A variant file adds chain and ownership effects to wave-2 employment of answered
    # stores, so the controls move the estimate and the test can see them.
    syn_nw = syn.copy()
    ans = syn_nw["STATUS2"] == 1
    syn_nw.loc[ans, "EMPFT2"] = (syn_nw.loc[ans, "EMPFT2"] + 4.0 * (syn_nw.loc[ans, "CHAIN"] == 1)
                                 - 3.0 * (syn_nw.loc[ans, "CHAIN"] == 3)
                                 - 2.0 * syn_nw.loc[ans, "CO_OWNED"])
    syn_nw = add_derived(syn_nw)
    v = raw_arrays(syn_nw)
    d = ck.build(syn_nw)
    w1, w2 = ~np.isnan(v["fte1"]), ~np.isnan(v["fte2"])
    bal = w1 & w2
    nj = v["nj"]
    dfte = v["fte2"] - v["fte1"]
    open_b = bal & ~v["perm"]
    X = np.column_stack([np.ones(open_b.sum()), nj[open_b], v["chain"][open_b] == 1,
                         v["chain"][open_b] == 2, v["chain"][open_b] == 3,
                         v["co"][open_b]]).astype(float)
    y = dfte[open_b]
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    e = y - X @ beta
    n, k = X.shape
    se_conv = math.sqrt((e @ e) / (n - k) * xtx_inv[1, 1])
    meat = (X * e[:, None] ** 2).T @ X
    se_hc1 = math.sqrt((xtx_inv @ meat @ xtx_inv)[1, 1] * n / (n - k))
    nw = ck.h2_nw_rule(d)
    assert nw["n"] == n and close(nw["b_nj"], beta[1]) and close(nw["se_nj"], se_conv)
    assert close(nw["se_nj_hc1"], se_hc1)
    assert close(nw["chg_nj"], y[nj[open_b]].mean()) and close(nw["chg_pa"], y[~nj[open_b]].mean())
    # the controls must move the estimate on this file, so the test can see them
    assert abs(beta[1] - (nw["chg_nj"] - nw["chg_pa"])) > 1e-3
    out["f3_nw_b_nj"] = r(beta[1])
    out["f3_nw_controls_shift"] = r(beta[1] - (nw["chg_nj"] - nw["chg_pa"]))
    return out


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    syn = synthetic_stores()
    syn.to_csv(SYN_CSV, index=False)
    syn = ck.load(SYN_CSV)                      # exercise the CSV path the runs use
    d = ck.build(syn)
    tests = [("s1_vs_hc2", lambda: test_s1_vs_hc2(d)),
             ("stacked_did", lambda: test_stacked(d)),
             ("winsor", lambda: test_winsor(d)),
             ("t4_filter", lambda: test_t4_filter(syn)),
             ("s1_monte_carlo", test_s1_monte_carlo),
             ("known_answer", test_known_answer),
             ("closures", lambda: test_closures(syn)),
             ("entry_points", lambda: test_entry_points(syn)),
             ("verdict", test_verdict),
             ("report_only_values", lambda: test_report_only_values(syn))]
    metrics: dict = {"seed": SEED, "syn_rows": len(syn),
                     "syn_nj": int((syn["STATE"] == 1).sum()), "syn_pa": int((syn["STATE"] == 0).sum())}
    failed = 0
    for name, fn in tests:
        try:
            metrics.update(fn())
            metrics[f"pass_{name}"] = 1
            print(f"PASS {name}")
        except Exception:  # noqa: BLE001 - report every failure, then exit non-zero
            failed += 1
            metrics[f"pass_{name}"] = 0
            print(f"FAIL {name}", file=sys.stderr)
            traceback.print_exc()
    metrics["tests_run"] = len(tests)
    metrics["tests_failed"] = failed
    ck.write_metrics(metrics, OUT_DIR / "metrics.json")
    print(f"{len(tests) - failed}/{len(tests)} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
