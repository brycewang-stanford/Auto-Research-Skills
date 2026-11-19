"""Card and Krueger (1994) replication: every planned analysis run, one entry point each.

Implements plan.json design.method and analysis_plan steps 1-7 exactly. The verdict
(step 8) is code/verdict.py; nothing here judges a hypothesis.

Entry points (run id = first argument):
    main-t3            Table 3 rows 1-5, method S1 SEs (H1(a), H1(b))
    main-t4            Table 4 column (i), OLS of DFTE on NJ, conventional SE (H1(c))
    se-alt             SE constructions not chosen (report only)
    placebo-hiwage     NJ stores with WAGE_ST >= 5.00 vs PA (descriptive only)
    h2-winsor          H2: pooled 5/95 winsorization on the balanced sample
    h2-closures-excl   H2 secondary s1 (report only)
    h2-nw-rule         H2 secondary s2, Neumark-Wascher rule (report only)

Usage, from the workspace root (through crew.py run; see runs/NOTES.md):
    .venv/bin/python -I code/ck_analysis.py <run-id> [--data data/derived/stores.csv]
                     [--out-dir runs/<run-id>]
Writes <out-dir>/metrics.json (flat JSON) and, for h2-winsor, <out-dir>/capped.csv.

Store key: ROW_ID (line number in public.dat). SHEET is a label only (SHEET 407 is two
stores) and is never used as a key, merge field or cluster variable.

All estimators are deterministic; no random numbers are drawn.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

RUN_IDS = ("main-t3", "main-t4", "se-alt", "placebo-hiwage",
           "h2-winsor", "h2-closures-excl", "h2-nw-rule")

# columns of data/derived/stores.csv that the analysis reads
REQUIRED = ["ROW_ID", "SHEET", "CHAIN", "CO_OWNED", "STATE", "EMPFT", "EMPPT", "NMGRS",
            "WAGE_ST", "STATUS2", "EMPFT2", "EMPPT2", "NMGRS2", "WAGE_ST2", "FTE", "FTE2",
            "CLOSED_PERM", "CLOSED_TEMP", "REFUSED2"]

STATUS_REFUSED, STATUS_ANSWERED, STATUS_PERM = 0, 1, 3
STATUS_TEMP = (2, 4, 5)          # renovation, highway construction, mall fire
TOL = 1e-9                       # internal consistency checks (identities, not estimates)


# ----------------------------------------------------------------------------- data
def load(path: str | Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"{path}: missing columns {missing}")
    return df


def build(raw: pd.DataFrame, assert_raw_closure_coding: bool = True) -> pd.DataFrame:
    """Construct every analysis variable from stores.csv (design.method VARIABLES/SAMPLES).

    Returns a frame indexed by ROW_ID with FTE1, FTE2 (closure override applied), FTE2_R5,
    DFTE, NJ, BK, KFC, ROYS, CO_OWNED, the wage group and the sample flags in_w1, in_w2,
    in_bal, in_r5, in_t4.
    """
    df = raw.copy()
    if df["ROW_ID"].duplicated().any() or df["ROW_ID"].isna().any():
        raise ValueError("ROW_ID must be unique and non-missing (it is the store key)")
    for col in ("STATE", "STATUS2", "CHAIN", "CO_OWNED"):
        if df[col].isna().any():
            raise ValueError(f"{col} has missing values")
    df = df.set_index("ROW_ID", drop=False).sort_index()
    df.index.name = None         # index = ROW_ID values; the column ROW_ID stays the key
    if not df["STATE"].isin([0, 1]).all():
        raise ValueError("STATE outside {0, 1}")
    if not df["STATUS2"].isin([0, 1, 2, 3, 4, 5]).all():
        raise ValueError("STATUS2 outside 0..5")

    status = df["STATUS2"].astype(int)
    perm = status == STATUS_PERM
    temp = status.isin(STATUS_TEMP)
    refused = status == STATUS_REFUSED
    # the prepare-data flags must agree with STATUS2
    for flag, mask in (("CLOSED_PERM", perm), ("CLOSED_TEMP", temp), ("REFUSED2", refused)):
        if not (df[flag].astype(int) == mask.astype(int)).all():
            raise ValueError(f"{flag} disagrees with STATUS2")

    # FTE from the components (NaN if any component is missing, as SAS arithmetic);
    # must equal prepare-data's FTE and FTE2 columns
    fte1 = df["EMPFT"] + df["NMGRS"] + 0.5 * df["EMPPT"]
    fte2_raw = df["EMPFT2"] + df["NMGRS2"] + 0.5 * df["EMPPT2"]
    for name, mine, theirs in (("FTE", fte1, df["FTE"]), ("FTE2", fte2_raw, df["FTE2"])):
        same_na = (mine.isna() == theirs.isna()).all()
        diff = (mine - theirs).abs().max(skipna=True)
        if not same_na or (not math.isnan(diff) and diff > TOL):
            raise ValueError(f"{name} in stores.csv differs from EMPFT + NMGRS + 0.5*EMPPT")

    # closure override, applied whatever the raw components say
    fte2 = fte2_raw.copy()
    fte2[perm] = 0.0
    fte2[temp | refused] = np.nan
    if assert_raw_closure_coding:
        # design.data: the raw file already codes closures this way; assert it
        if not ((fte2_raw[perm] == 0).all() and fte2_raw[temp | refused].isna().all()):
            raise ValueError("raw closure coding of FTE2 differs from the override")
    fte2_r5 = fte2.copy()
    fte2_r5[temp] = 0.0          # report-only row 5: temporarily closed stores at 0

    out = pd.DataFrame(index=df.index)
    out["ROW_ID"] = df["ROW_ID"].astype(int)
    out["SHEET"] = df["SHEET"]                       # label only
    out["NJ"] = df["STATE"].astype(int)
    out["STATUS2"] = status
    out["closed_perm"] = perm.astype(int)
    out["closed_temp"] = temp.astype(int)
    out["refused"] = refused.astype(int)
    out["FTE1"] = fte1.astype(float)
    out["FTE2"] = fte2.astype(float)
    out["FTE2_R5"] = fte2_r5.astype(float)
    out["DFTE"] = out["FTE2"] - out["FTE1"]
    out["DFTE_R5"] = out["FTE2_R5"] - out["FTE1"]
    chain = df["CHAIN"].astype(int)
    out["CHAIN"] = chain
    out["BK"] = (chain == 1).astype(int)
    out["KFC"] = (chain == 2).astype(int)
    out["ROYS"] = (chain == 3).astype(int)           # Wendy's (4) omitted
    out["CO_OWNED"] = df["CO_OWNED"].astype(int)
    w1 = df["WAGE_ST"].astype(float).round(2)
    w2 = df["WAGE_ST2"].astype(float).round(2)
    out["WAGE_ST"], out["WAGE_ST2"] = w1, w2
    # check.sas ICODE for NJ stores: low = 4.25, medium 4.25 < w < 5.00, high >= 5.00
    out["wage_low"] = (w1 == 4.25).astype(int)
    out["wage_med"] = ((w1 > 4.25) & (w1 < 5.00)).astype(int)
    out["wage_high"] = (w1 >= 5.00).astype(int)

    out["in_w1"] = out["FTE1"].notna()
    out["in_w2"] = out["FTE2"].notna()
    out["in_bal"] = out["in_w1"] & out["in_w2"]                       # sample B
    out["in_r5"] = out["in_w1"] & out["FTE2_R5"].notna()
    # check.sas DATA C1: DEMP non-missing and (CLOSED = 1 or (CLOSED = 0 and DWAGE non-missing))
    dwage_ok = out["WAGE_ST"].notna() & out["WAGE_ST2"].notna()
    out["in_t4"] = out["DFTE"].notna() & (perm | (~perm & dwage_ok))
    return out


# ------------------------------------------------------------------------ estimators
def mean_se(y: pd.Series) -> tuple[float, float, int]:
    """Mean and s/sqrt(n) (s with denominator n - 1) of the non-missing values."""
    y = y.dropna().to_numpy(float)
    n = len(y)
    return float(y.mean()), float(y.std(ddof=1) / math.sqrt(n)), n


def s1_change(y1: pd.Series, y2: pd.Series, a1: pd.Series, a2: pd.Series) -> dict:
    """Method S1: change in mean FTE between waves on possibly different store sets.

    change = mean_{A2}(y2) - mean_{A1}(y1)
    Var    = s1^2/n1 + s2^2/n2 - 2 * c12 * n12 / (n1 * n2)
    s1^2, s2^2: sample variances (ddof 1) of y1 on A1 and y2 on A2; c12: sample covariance
    (ddof 1) of y1 and y2 on the overlap A12. On a balanced sample this is var(y2 - y1)/n.
    """
    a1, a2 = a1.astype(bool), a2.astype(bool)
    if y1[a1].isna().any() or y2[a2].isna().any():
        raise ValueError("S1: sample set contains missing values")
    a12 = a1 & a2
    v1, v2 = y1[a1].to_numpy(float), y2[a2].to_numpy(float)
    n1, n2, n12 = len(v1), len(v2), int(a12.sum())
    s1sq, s2sq = v1.var(ddof=1), v2.var(ddof=1)
    c12 = float(np.cov(y1[a12].to_numpy(float), y2[a12].to_numpy(float), ddof=1)[0, 1]) \
        if n12 >= 2 else 0.0
    var = s1sq / n1 + s2sq / n2 - 2.0 * c12 * n12 / (n1 * n2)
    if -1e-12 < var < 0:         # floating-point noise when every change is identical
        var = 0.0
    return {"chg": float(v2.mean() - v1.mean()), "se": float(math.sqrt(var)),
            "n1": n1, "n2": n2, "n12": n12, "indep_se": float(math.sqrt(s1sq / n1 + s2sq / n2))}


def did_from(nj: dict, pa: dict) -> tuple[float, float]:
    """Column (iii): NJ change minus PA change, SE = sqrt(SE_PA^2 + SE_NJ^2)."""
    return nj["chg"] - pa["chg"], math.sqrt(nj["se"] ** 2 + pa["se"] ** 2)


def ols(y: pd.Series, X: pd.DataFrame, cov: str = "nonrobust", groups=None):
    Xc = sm.add_constant(X.astype(float), has_constant="add")
    model = sm.OLS(y.astype(float), Xc)
    if cov == "cluster":
        return model.fit(cov_type="cluster", cov_kwds={"groups": np.asarray(groups)})
    return model.fit(cov_type=cov)


def winsorize(x: pd.Series, pool: pd.Series | None = None) -> dict:
    """Winsorize x at the 5th/95th percentiles of `pool` (default x itself).

    Percentiles: numpy.percentile(method='linear'). A value is capped only if strictly
    below q05 (low) or strictly above q95 (high).
    """
    pool = x if pool is None else pool
    q05, q95 = (float(v) for v in np.percentile(pool.to_numpy(float), [5, 95], method="linear"))
    low, high = x < q05, x > q95
    w = x.clip(lower=q05, upper=q95)
    return {"q05": q05, "q95": q95, "w": w, "low": low, "high": high}


# ---------------------------------------------------------------------- run bodies
def _state(d: pd.DataFrame, s: int) -> pd.DataFrame:
    return d[d["NJ"] == s]


def table3(d: pd.DataFrame) -> dict:
    """main-t3: Table 3 rows 1-5 (design.method TABLE 3 ESTIMATES AND SEs)."""
    m: dict = {}
    for s, tag in ((0, "pa"), (1, "nj")):
        g = _state(d, s)
        m[f"n_w1_{tag}"] = int(g["in_w1"].sum())
        m[f"n_w2_{tag}"] = int(g["in_w2"].sum())
        m[f"n_both_{tag}"] = int(g["in_bal"].sum())
        m[f"mean_w1_{tag}"], m[f"mean_w1_{tag}_se"], _ = mean_se(g.loc[g["in_w1"], "FTE1"])
        m[f"mean_w2_{tag}"], m[f"mean_w2_{tag}_se"], _ = mean_se(g.loc[g["in_w2"], "FTE2"])
    for row, w in (("row1", "w1"), ("row2", "w2")):
        m[f"{row}_diff"] = m[f"mean_{w}_nj"] - m[f"mean_{w}_pa"]
        m[f"{row}_diff_se"] = math.sqrt(m[f"mean_{w}_nj_se"] ** 2 + m[f"mean_{w}_pa_se"] ** 2)

    def rows(label, y2col, a1col, a2col):
        res = {}
        for s, tag in ((0, "pa"), (1, "nj")):
            g = _state(d, s)
            res[tag] = s1_change(g["FTE1"], g[y2col], g[a1col], g[a2col])
            m[f"chg_{label}_{tag}"] = res[tag]["chg"]
            m[f"chg_{label}_{tag}_se"] = res[tag]["se"]
        m[f"did_{label}"], m[f"did_{label}_se"] = did_from(res["nj"], res["pa"])
        return res

    rows("r3", "FTE2", "in_w1", "in_w2")                      # unbalanced
    r4 = rows("r4", "FTE2", "in_bal", "in_bal")               # balanced, sample B
    r5 = rows("r5", "FTE2_R5", "in_r5", "in_r5")              # B + temporary closures at 0
    nj = _state(d, 1)
    m["did_r3_pct"] = 100.0 * m["did_r3"] / m["mean_w1_nj"]
    m["n_bal_pa"], m["n_bal_nj"] = r4["pa"]["n1"], r4["nj"]["n1"]
    m["mean_w1_bal_nj"] = float(nj.loc[nj["in_bal"], "FTE1"].mean())
    m["did_r4_pct"] = 100.0 * m["did_r4"] / m["mean_w1_bal_nj"]
    m["n_r5_pa"], m["n_r5_nj"] = r5["pa"]["n1"], r5["nj"]["n1"]
    return m


def table4(d: pd.DataFrame) -> dict:
    """main-t4: OLS of DFTE on NJ on check.sas sample C1, conventional SE judged."""
    m: dict = {}
    for s, tag in ((0, "pa"), (1, "nj")):
        g = _state(d, s)
        m[f"t4_n_all_{tag}"] = int(len(g))                              # step 0
        m[f"t4_n_fte_both_{tag}"] = int(g["in_bal"].sum())              # step 1
        m[f"t4_n_{tag}"] = int(g["in_t4"].sum())                        # step 2
        m[f"t4_n_closed_{tag}"] = int((g["in_t4"] & (g["closed_perm"] == 1)).sum())
    s = d[d["in_t4"]]
    fit = ols(s["DFTE"], s[["NJ"]])
    fit_hc1 = ols(s["DFTE"], s[["NJ"]], cov="HC1")
    m["n"] = int(fit.nobs)
    m["n_nj"], m["n_pa"] = int((s["NJ"] == 1).sum()), int((s["NJ"] == 0).sum())
    m["b_nj"] = float(fit.params["NJ"])
    m["se_nj"] = float(fit.bse["NJ"])
    m["se_nj_hc1"] = float(fit_hc1.bse["NJ"])
    m["const"] = float(fit.params["const"])
    m["root_mse"] = float(math.sqrt(fit.mse_resid))
    m["dep_mean"] = float(s["DFTE"].mean())
    m["dep_sd"] = float(s["DFTE"].std(ddof=1))
    return m


def stacked(d: pd.DataFrame, a1col: str, a2col: str):
    """Store-wave regression FTE = a + b*NJ + c*POST + d*NJ*POST, CR1 clustered on ROW_ID."""
    w1 = d.loc[d[a1col], ["ROW_ID", "NJ", "FTE1"]].rename(columns={"FTE1": "FTE"}).assign(POST=0)
    w2 = d.loc[d[a2col], ["ROW_ID", "NJ", "FTE2"]].rename(columns={"FTE2": "FTE"}).assign(POST=1)
    long = pd.concat([w1, w2], ignore_index=True)
    long["NJ_POST"] = long["NJ"] * long["POST"]
    fit = ols(long["FTE"], long[["NJ", "POST", "NJ_POST"]], cov="cluster", groups=long["ROW_ID"])
    return fit, len(long), int(long["ROW_ID"].nunique())


def se_alt(d: pd.DataFrame) -> dict:
    """se-alt: SE constructions not chosen, beside S1 (report only)."""
    t3 = table3(d)
    m: dict = {"did_r3": t3["did_r3"], "did_r3_se_s1": t3["did_r3_se"],
               "did_r4": t3["did_r4"], "did_r4_se_s1": t3["did_r4_se"]}
    for label, a1, a2 in (("r3", "in_w1", "in_w2"), ("r4", "in_bal", "in_bal")):
        fit, nobs, nclus = stacked(d, a1, a2)
        dd = float(fit.params["NJ_POST"])
        if abs(dd - t3[f"did_{label}"]) > TOL:
            raise AssertionError(f"stacked d ({dd}) != did_{label} ({t3[f'did_{label}']})")
        m[f"did_{label}_stacked"] = dd
        m[f"did_{label}_cr1_se"] = float(fit.bse["NJ_POST"])
        m[f"stacked_{label}_nobs"] = nobs
        m[f"stacked_{label}_nclusters"] = nclus
    b = d[d["in_bal"]]
    for cov in ("HC1", "HC2"):
        fit = ols(b["DFTE"], b[["NJ"]], cov=cov)
        m[f"did_r4_{cov.lower()}_se"] = float(fit.bse["NJ"])
    if abs(m["did_r4_hc2_se"] - t3["did_r4_se"]) > TOL:
        raise AssertionError("HC2 SE on B differs from the S1 SE of did_r4")
    for s, tag in ((0, "pa"), (1, "nj")):
        g = _state(d, s)
        r = s1_change(g["FTE1"], g["FTE2"], g["in_w1"], g["in_w2"])
        m[f"chg_r3_{tag}_indep_se"] = r["indep_se"]
    return m


def placebo_hiwage(d: pd.DataFrame) -> dict:
    """placebo-hiwage: NJ stores with WAGE_ST >= 5.00 vs PA (descriptive only)."""
    m: dict = {}
    pa = _state(d, 0)
    hi = d[(d["NJ"] == 1) & (d["wage_high"] == 1)]
    for label, a1, a2 in (("r3", "in_w1", "in_w2"), ("r4", "in_bal", "in_bal")):
        r_hi = s1_change(hi["FTE1"], hi["FTE2"], hi[a1], hi[a2])
        r_pa = s1_change(pa["FTE1"], pa["FTE2"], pa[a1], pa[a2])
        m[f"plac_{label}"], m[f"plac_{label}_se"] = did_from(r_hi, r_pa)
        m[f"chg_{label}_nj_hi"], m[f"chg_{label}_nj_hi_se"] = r_hi["chg"], r_hi["se"]
        m[f"chg_{label}_pa"] = r_pa["chg"]
    m["n_nj_hi"] = int(len(hi))
    m["n_nj_hi_w1"] = int(hi["in_w1"].sum())
    m["n_nj_hi_w2"] = int(hi["in_w2"].sum())
    m["n_nj_hi_bal"] = int(hi["in_bal"].sum())
    return m


def _did_bal(b: pd.DataFrame, col: str) -> tuple[float, float]:
    """NJ-minus-PA difference in mean `col` on a balanced sample, S1 balanced-form SE."""
    out = {}
    for s, tag in ((0, "pa"), (1, "nj")):
        v = b.loc[b["NJ"] == s, col].to_numpy(float)
        out[tag] = {"chg": float(v.mean()), "se": float(v.std(ddof=1) / math.sqrt(len(v)))}
    return did_from(out["nj"], out["pa"])


def h2_winsor(d: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """h2-winsor: pooled 5/95 winsorization of DFTE on sample B, closures included."""
    b = d[d["in_bal"]].copy()
    if not (b.loc[b["closed_perm"] == 1, "DFTE"] == -b.loc[b["closed_perm"] == 1, "FTE1"]).all():
        raise AssertionError("permanent closures must have DFTE = -FTE1")
    wz = winsorize(b["DFTE"])
    b["W"], b["low"], b["high"] = wz["w"], wz["low"], wz["high"]
    m: dict = {"n": int(len(b)), "n_nj": int((b["NJ"] == 1).sum()),
               "n_pa": int((b["NJ"] == 0).sum()),
               "n_closed_nj": int(((b["NJ"] == 1) & (b["closed_perm"] == 1)).sum()),
               "n_closed_pa": int(((b["NJ"] == 0) & (b["closed_perm"] == 1)).sum()),
               "q05": wz["q05"], "q95": wz["q95"]}
    m["did_u"], m["did_u_se"] = _did_bal(b, "DFTE")
    m["did_w"], m["did_w_se"] = _did_bal(b, "W")
    t3 = table3(d)
    if abs(m["did_u"] - t3["did_r4"]) > TOL:
        raise AssertionError("did_u differs from main-t3 did_r4")
    m["ratio_w_u"] = m["did_w"] / m["did_u"] if m["did_u"] != 0 else None
    for tail in ("low", "high"):
        for s, tag in ((1, "nj"), (0, "pa")):
            m[f"capped_{tail}_{tag}"] = int((b[tail] & (b["NJ"] == s)).sum())
        m[f"capped_{tail}_closed"] = int((b[tail] & (b["closed_perm"] == 1)).sum())
    m["fte1_mean_bal"] = float(b["FTE1"].mean())
    for tail in ("low", "high"):
        sel = b.loc[b[tail], "FTE1"]
        m[f"fte1_mean_capped_{tail}"] = float(sel.mean()) if len(sel) else None
    capped = b[b["low"] | b["high"]].copy()
    capped["state"] = np.where(capped["NJ"] == 1, "NJ", "PA")
    capped["tail"] = np.where(capped["low"], "low", "high")
    capped = capped[["ROW_ID", "SHEET", "state", "tail", "DFTE", "W", "FTE1", "closed_perm"]]
    return m, capped.sort_values(["tail", "DFTE", "ROW_ID"]).reset_index(drop=True)


def h2_closures_excl(d: pd.DataFrame) -> dict:
    """h2-closures-excl: closures out of the percentile pool and never capped (s1)."""
    b = d[d["in_bal"]].copy()
    open_ = b["closed_perm"] == 0
    wz = winsorize(b.loc[open_, "DFTE"])
    b["W"] = b["DFTE"]
    b.loc[open_, "W"] = wz["w"]
    b["low"], b["high"] = False, False
    b.loc[open_, "low"], b.loc[open_, "high"] = wz["low"], wz["high"]
    m: dict = {"n": int(len(b)), "n_pool": int(open_.sum()), "q05_nc": wz["q05"], "q95_nc": wz["q95"]}
    m["did_u"], _ = _did_bal(b, "DFTE")
    m["did_w"], m["did_w_se"] = _did_bal(b, "W")
    m["ratio_w_u"] = m["did_w"] / m["did_u"] if m["did_u"] != 0 else None
    for tail in ("low", "high"):
        for s, tag in ((1, "nj"), (0, "pa")):
            m[f"capped_{tail}_{tag}"] = int((b[tail].astype(bool) & (b["NJ"] == s)).sum())
    return m


def h2_nw_rule(d: pd.DataFrame) -> dict:
    """h2-nw-rule: B minus permanent closures; DFTE on NJ + chain dummies + CO_OWNED."""
    s = d[d["in_bal"] & (d["closed_perm"] == 0)]
    X = s[["NJ", "BK", "KFC", "ROYS", "CO_OWNED"]]
    fit = ols(s["DFTE"], X)
    fit_hc1 = ols(s["DFTE"], X, cov="HC1")
    return {"n": int(fit.nobs), "n_nj": int((s["NJ"] == 1).sum()), "n_pa": int((s["NJ"] == 0).sum()),
            "b_nj": float(fit.params["NJ"]), "se_nj": float(fit.bse["NJ"]),
            "se_nj_hc1": float(fit_hc1.bse["NJ"]),
            "chg_nj": float(s.loc[s["NJ"] == 1, "DFTE"].mean()),
            "chg_pa": float(s.loc[s["NJ"] == 0, "DFTE"].mean())}


def compute(run_id: str, d: pd.DataFrame) -> tuple[dict, dict[str, pd.DataFrame]]:
    """Return (metrics, extra output tables) for one planned run on a built frame."""
    if run_id == "main-t3":
        return table3(d), {}
    if run_id == "main-t4":
        return table4(d), {}
    if run_id == "se-alt":
        return se_alt(d), {}
    if run_id == "placebo-hiwage":
        return placebo_hiwage(d), {}
    if run_id == "h2-winsor":
        m, capped = h2_winsor(d)
        return m, {"capped.csv": capped}
    if run_id == "h2-closures-excl":
        return h2_closures_excl(d), {}
    if run_id == "h2-nw-rule":
        return h2_nw_rule(d), {}
    raise ValueError(f"unknown run id {run_id!r}; expected one of {RUN_IDS}")


# ------------------------------------------------------------------------- output
def flat(m: dict) -> dict:
    """JSON-safe flat metrics: numpy scalars to Python, NaN/inf to None."""
    out = {}
    for k, v in m.items():
        if isinstance(v, (bool, np.bool_)):
            out[k] = bool(v)
        elif isinstance(v, (int, np.integer)):
            out[k] = int(v)
        elif isinstance(v, (float, np.floating)):
            out[k] = float(v) if math.isfinite(v) else None
        elif v is None or isinstance(v, str):
            out[k] = v
        else:
            raise TypeError(f"metric {k} is not a scalar: {type(v)}")
    return out


def write_metrics(m: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(flat(m), indent=2, allow_nan=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("run_id", choices=RUN_IDS)
    p.add_argument("--data", default="data/derived/stores.csv")
    p.add_argument("--out-dir", default=None)
    a = p.parse_args(argv)
    out_dir = Path(a.out_dir or f"runs/{a.run_id}")
    d = build(load(a.data))
    m, extras = compute(a.run_id, d)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, table in extras.items():
        table.to_csv(out_dir / name, index=False)
    write_metrics(m, out_dir / "metrics.json")
    print(f"{a.run_id}: wrote {len(m)} metrics to {out_dir / 'metrics.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
