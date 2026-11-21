"""Run posthoc (design deviation D7; added after results-r1; report-only, changes no label).

Every number here is post hoc: chosen after the post-period results and results-r1 were seen.
None enters a decision; the pre-specified verdict stands.

Inputs  data/derived/qcew_panel.csv          (a) Georgia's QCEW rows, 2014Q1-2016Q4 only
        data/derived/state_panel_pre.csv     (a) state 722513 wage and employment, 2014-2019
        runs/level-mde/tests.csv             (b) the H1 level-check tests
        runs/level-mde/metrics.json          (b) nu_h1, the pre-specified H1 critical values
        runs/h1-wage/metrics.json            (b) the H1 pooled and yearly estimates
        runs/event-path/event_path.csv       (c) the selected candidate's event path
        runs/select/metrics.json             the selected candidate (checked against the others)
Output  runs/posthoc/metrics.json, runs/posthoc/georgia.csv

(a) Facts bearing on whether Georgia's 2014-2015 NAICS 722513 weekly-wage drop is a data
    artifact (results-r1 R1; code-r4 C8). State facts only; the script draws no conclusion. For
    Georgia (13), NAICS 722513, 722511, 7225 and industry 10 (state rows), and the 722513 county
    rows, by quarter 2014Q1-2016Q4: disclosure code, establishments, mean monthly employment,
    average weekly wage (georgia.csv; the county_sum rows give the establishments of all counties
    and the employment of the non-suppressed counties only). In metrics.json, for 2015Q1-2015Q4
    and each of the four industries: the year-over-year log change (quarter t against t-4) of
    Georgia's weekly wage, employment and establishments, and the wage and employment changes
    minus the median over the 51 units of the same change (state rows); Georgia's weekly wage
    in 2014Q4 and 2015Q1; the number of suppressed quarters; the number of Georgia counties with
    a 722513 row and with a suppressed one; and, for scale, the largest absolute 722513 wage
    deviation over every state and quarter 2015Q1-2019Q4 other than Georgia's 2015.
(b) The H1 decision-set quantiles with Georgia's own six L tests removed (results-r1 R1; code-r4
    C6, C7). Only Georgia's six T values in L are removed: Georgia remains a donor and a placebo,
    in California's SE and in the other L states' SEs. From runs/level-mde/tests.csv, the
    T = tau / SE values (SE = max) of statistic h1 in L; q95 and q975 with numpy method 'higher',
    q05 and q025 with 'lower', as level-mde computes them; c_hi(p) = max(t_{nu,p}, q) and c_lo(p) =
    min(-t_{nu,1-p}, q). Reported for (i) Georgia's L tests removed at level-mde's nu_h1; (ii) the
    same with nu recomputed from the 49 non-Georgia donors' s_j^2 (Georgia's placebo variance
    removed from nu only); (iii) leave one L state out, for each of the ten L states in turn, at
    nu_h1, with whether the removal changes c_hi(0.95) or c_hi(0.975). For each: whether the
    pooled, year-1 and year-2 H1 t-statistics of h1-wage exceed c_hi(0.95), and for (i) and (ii)
    the 95% and 90% intervals. None of these is a decision: the pre-specified H1 verdict stands.
(c) DDT's out-of-fit pre-period evidence (results-r1 R3; identifying_assumption (ii)): the OLS
    slope per calendar quarter of the event-path gap on the quarter index over 2014Q1-2019Q4, for
    employment and wages, its RMS over those quarters, and the implied size over the post window:
    slope x the mean horizon of P = 2024Q2-2026Q1 relative to the base 2023Q3 (6.5 quarters).
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import sclib as S

QCEW = Path("data/derived/qcew_panel.csv")
PRE = Path("data/derived/state_panel_pre.csv")
TESTS = Path("runs/level-mde/tests.csv")
LEVEL = Path("runs/level-mde/metrics.json")
H1 = Path("runs/h1-wage/metrics.json")
EVENT = Path("runs/event-path/event_path.csv")
SELECT = Path("runs/select/metrics.json")
OUT_DIR = Path("runs/posthoc")
GA = "13"
IND = ["722513", "722511", "7225", "10"]
Q_FIRST, Q_LAST = S.qidx(2014, 1), S.qidx(2016, 4)


def qcew_rows(path=QCEW):
    """State rows of the 51 units (four industries) and Georgia's 722513 county rows,
    2014Q1-2016Q4."""
    cols = ["area_fips", "state_fips", "area_level", "industry", "own_code", "year", "qtr",
            "disclosure_code", "suppressed", "establishments", "month1_emplvl", "month2_emplvl",
            "month3_emplvl", "avg_wkly_wage"]
    q = pd.read_csv(path, dtype={"area_fips": str, "state_fips": str, "industry": str,
                                 "own_code": str, "disclosure_code": str}, usecols=cols)
    q["qi"] = 4 * q["year"] + q["qtr"] - 1
    keep_state = (q.area_level == "state") & q.state_fips.isin(S.ALL51)
    keep_cty = (q.area_level == "county") & (q.state_fips == GA) & (q.industry == "722513")
    q = q[(keep_state | keep_cty) & q.qi.between(Q_FIRST, Q_LAST) & q.industry.isin(IND)].copy()
    q["emp"] = q[["month1_emplvl", "month2_emplvl", "month3_emplvl"]].mean(axis=1)
    q["disclosure_code"] = q["disclosure_code"].fillna("")
    return q


def part_a(q, pre):
    m, rows = {}, []
    st_all = q[q.area_level == "state"]
    st = st_all[st_all.state_fips == GA]
    for ind in IND:
        d = st[st.industry == ind].sort_values("qi")
        for _, r in d.iterrows():
            rows.append({"industry": ind, "level": "state", "quarter": S.qlabel(int(r.qi)),
                         "disclosure_code": r.disclosure_code, "establishments": r.establishments,
                         "emp": r.emp, "avg_wkly_wage": r.avg_wkly_wage, "note": ""})
        m[f"a_ga_{ind}_rows"] = int(len(d))
        m[f"a_ga_{ind}_suppressed_quarters"] = int(d.suppressed.sum())
    cty = q[(q.area_level == "county") & (q.industry == "722513")]
    for qi, d in cty.groupby("qi"):
        lab = S.qlabel(int(qi))
        ok = d[d.suppressed == 0]
        rows.append({"industry": "722513", "level": "county_sum", "quarter": lab,
                     "disclosure_code": f"{int(d.suppressed.sum())} of {len(d)} counties suppressed",
                     "establishments": d.establishments.sum(), "emp": ok.emp.sum(),
                     "avg_wkly_wage": np.nan,
                     "note": "establishments: all counties; emp: non-suppressed counties only"})
        m[f"a_ga_722513_counties_{lab}"] = int(len(d))
        m[f"a_ga_722513_counties_suppressed_{lab}"] = int(d.suppressed.sum())
    # year-over-year log changes (t against t-4), Georgia and minus the 51-unit median
    for ind in IND:
        d = st_all[st_all.industry == ind]
        ww = d.pivot(index="qi", columns="state_fips", values="avg_wkly_wage").astype(float)
        we = d.pivot(index="qi", columns="state_fips", values="emp").astype(float)
        wn = d.pivot(index="qi", columns="state_fips", values="establishments").astype(float)
        dw = np.log(ww) - np.log(ww.shift(4))
        de = np.log(we) - np.log(we.shift(4))
        dn = np.log(wn) - np.log(wn.shift(4))
        for k in (1, 2, 3, 4):
            qi = S.qidx(2015, k)
            lab = S.qlabel(qi)
            m[f"a_ga_{ind}_aww_yoy_{lab}"] = float(dw.loc[qi, GA])
            m[f"a_ga_{ind}_aww_yoy_dev_{lab}"] = float(dw.loc[qi, GA] - dw.loc[qi].median())
            m[f"a_ga_{ind}_emp_yoy_{lab}"] = float(de.loc[qi, GA])
            m[f"a_ga_{ind}_emp_yoy_dev_{lab}"] = float(de.loc[qi, GA] - de.loc[qi].median())
            m[f"a_ga_{ind}_estabs_yoy_{lab}"] = float(dn.loc[qi, GA])
        for qi in (S.qidx(2014, 4), S.qidx(2015, 1)):
            m[f"a_ga_{ind}_aww_{S.qlabel(qi)}"] = float(ww.loc[qi, GA])
    # scale: the largest other |722513 wage deviation| over 2015Q1-2019Q4 (state_panel_pre)
    p = pre.copy()
    p["qi"] = 4 * p["year"] + p["qtr"] - 1
    wide_w = p.pivot(index="qi", columns="state_fips", values="aww_722513")
    dw = np.log(wide_w) - np.log(wide_w.shift(4))
    dev_w = dw.sub(dw.median(axis=1), axis=0)
    win = dev_w.loc[S.qidx(2015, 1):S.qidx(2019, 4)].stack()
    ga15 = [(S.qidx(2015, k), GA) for k in (1, 2, 3, 4)]
    m["a_ga_722513_aww_yoy_dev_2015_min_pre_panel"] = float(min(win.loc[i] for i in ga15))
    other = win.drop(index=[i for i in ga15 if i in win.index])
    big = other.abs().idxmax()
    m["a_largest_other_aww_yoy_dev"] = float(other.loc[big])
    m["a_largest_other_aww_yoy_dev_state"] = str(big[1])
    m["a_largest_other_aww_yoy_dev_quarter"] = S.qlabel(int(big[0]))
    return m, pd.DataFrame(rows)


def h1_checks(prefix, c, m_h1, m, intervals=True):
    """Whether the pooled, year-1 and year-2 H1 t-statistics exceed c_hi(0.95) under c."""
    for tag in ("h1", "h1_y1", "h1_y2"):
        tau, se = float(m_h1[f"{tag}_att"]), float(m_h1[f"{tag}_se"])
        m[f"{prefix}_{tag}_t_exceeds_chi95"] = int(tau / se > c["hi95"])
        if intervals:
            for k, v in S.intervals(tau, se, c).items():
                m[f"{prefix}_{tag}_{k}"] = float(v)


def part_b(tests, m_lvl, m_h1):
    m = {}
    d = tests[(tests.stat == "h1") & (tests.in_L == 1)].copy()
    if len(d) != 60:
        raise ValueError(f"{len(d)} H1 tests in L, expected 60")
    d["unit"] = d["unit"].astype(str).str.zfill(2)
    d["T"] = d.tau / d.se
    nu = float(m_lvl["nu_h1"])
    m["b_nu_h1_prespecified"] = nu
    pre_c = {k: float(m_lvl[f"crit_h1_{k}"]) for k in ("hi95", "hi975", "lo05", "lo025")}
    for k, v in pre_c.items():
        m[f"b_crit_h1_prespecified_{k}"] = v
    for tag in ("h1", "h1_y1", "h1_y2"):
        m[f"b_{tag}_t"] = float(m_h1[f"{tag}_att"]) / float(m_h1[f"{tag}_se"])
        m[f"b_{tag}_t_exceeds_chi95_prespecified"] = int(m_h1[f"{tag}_reject"])
    ga = d[d.unit == GA]
    rest = d[d.unit != GA]
    m["b_gaL_tests_removed"] = int(len(ga))
    m["b_n_L_remaining"] = int(len(rest))
    m["b_ga_T_max"] = float(ga["T"].max())
    m["b_others_T_max"] = float(rest["T"].max())
    m["b_others_T_max_state"] = str(rest.loc[rest["T"].idxmax(), "unit"])
    lq = S.l_quantiles(rest["T"].to_numpy())
    for k, v in lq.items():
        m[f"b_gaL_Lq_h1_{k}"] = v
    # (i) Georgia's L tests removed, level-mde's nu_h1
    c1 = S.critical_values(nu, lq)
    for k, v in c1.items():
        m[f"b_gaL_crit_h1_{k}"] = v
        m[f"b_gaL_crit_h1_{k}_from_L"] = int(v != S.critical_values(nu)[k])
    h1_checks("b_gaL", c1, m_h1, m)
    # (ii) also Georgia's placebo variance removed from nu (49 non-Georgia donors)
    donors = [u for u in S.R50 if u != GA]
    nu_hat2, nu2 = S.nu_for_donors(m_lvl, "h1", donors)
    m["b_nu_hat_h1_gaout"] = nu_hat2
    m["b_nu_h1_gaout"] = nu2
    m["b_s2_h1_ga_share"] = float(m_lvl[f"s2_h1_{GA}"]) / sum(float(m_lvl[f"s2_h1_{u}"]) for u in S.R50)
    c2 = S.critical_values(nu2, lq)
    for k, v in c2.items():
        m[f"b_gaLnu_crit_h1_{k}"] = v
    h1_checks("b_gaLnu", c2, m_h1, m)
    # (iii) leave one L state out, each of the ten in turn, at nu_h1
    states = sorted(d.unit.unique())
    m["b_loo_states"] = ",".join(states)
    changing = []
    for u in states:
        lq_u = S.l_quantiles(d.loc[d.unit != u, "T"].to_numpy())
        c_u = S.critical_values(nu, lq_u)
        m[f"b_loo_{u}_crit_h1_hi95"] = c_u["hi95"]
        m[f"b_loo_{u}_crit_h1_hi975"] = c_u["hi975"]
        ch = int(abs(c_u["hi95"] - pre_c["hi95"]) > 1e-12 or abs(c_u["hi975"] - pre_c["hi975"]) > 1e-12)
        m[f"b_loo_{u}_changes_chi"] = ch
        if ch:
            changing.append(u)
        h1_checks(f"b_loo_{u}", c_u, m_h1, m, intervals=False)
    m["b_loo_n_changing"] = len(changing)
    m["b_loo_changing_states"] = ",".join(changing)
    return m


def part_c(ev):
    m = {}
    ev = ev.copy()
    ev["qi"] = ev.quarter.map(S.qparse)
    seg = ev[ev.qi.between(S.qidx(2014, 1), S.qidx(2019, 4))]
    post = np.arange(S.REAL_B + 3, S.REAL_B + 11)
    horizon = float(np.mean(post - S.REAL_B))
    m["c_post_mean_horizon"] = horizon
    for outcome in ("emp", "wage"):
        d = seg[seg.outcome == outcome].sort_values("qi")
        if len(d) != 24:
            raise ValueError(f"{outcome}: {len(d)} quarters in 2014-2019, expected 24")
        t = d.qi.to_numpy(float)
        g = d.gap.to_numpy(float)
        x = t - t.mean()
        slope = float(x @ (g - g.mean()) / (x @ x))
        m[f"c_{outcome}_slope_2014_2019"] = slope
        m[f"c_{outcome}_implied_post"] = slope * horizon
        m[f"c_{outcome}_rms_2014_2019"] = float(np.sqrt(np.mean(g ** 2)))
        m[f"c_{outcome}_gap_2014q1"] = float(g[0])
        m[f"c_{outcome}_gap_2019q4"] = float(g[-1])
    return m


def main():
    sel = json.loads(SELECT.read_text())["selected"]
    m_lvl = json.loads(LEVEL.read_text())
    m_h1 = json.loads(H1.read_text())
    for name, mm in (("level-mde", m_lvl), ("h1-wage", m_h1)):
        if mm["selected"] != sel:
            raise ValueError(f"{name} used a different candidate")
    m = {"selected": sel, "post_hoc": "D7: report-only, chosen after the results; changes no label"}
    pre = S.read_panel_csv(PRE, pre_only=True)
    ma, tab = part_a(qcew_rows(), pre)
    m.update(ma)
    m.update(part_b(pd.read_csv(TESTS, dtype={"unit": str}), m_lvl, m_h1))
    m.update(part_c(pd.read_csv(EVENT)))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tab.to_csv(OUT_DIR / "georgia.csv", index=False, float_format="%.6g")
    S.write_json(OUT_DIR / "metrics.json", m)
    print(f"posthoc: c_hi95 with Georgia's L tests removed {m['b_gaL_crit_h1_hi95']:.3f}; "
          f"leave-one-out changes c_hi for {m['b_loo_changing_states'] or 'no state'}; "
          f"drift emp {m['c_emp_slope_2014_2019']:.4f}/q")


if __name__ == "__main__":
    sys.exit(main())
