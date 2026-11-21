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

(a) Georgia's 2014-2015 NAICS 722513 weekly-wage drop (results-r1 R1). State facts only, no
    causal claim. For Georgia (13), NAICS 722513, 722511, 7225 and industry 10 (state rows), and
    the 722513 county rows, by quarter 2014Q1-2016Q4: disclosure code, establishments, mean
    monthly employment, average weekly wage; the number of Georgia counties with a 722513 row and
    with a suppressed one. Year-over-year log changes (quarter t against t-4) of Georgia's 722513
    weekly wage, employment and establishments, each minus the median over the 51 units of the
    same change, for 2015Q1-2015Q4; and the largest absolute such wage deviation over every
    state and quarter 2015Q1-2019Q4 other than Georgia's 2015, for scale.
(b) The H1 decision-set quantiles without Georgia (results-r1 R1): from runs/level-mde/tests.csv,
    the T = tau / SE values (SE = max) of statistic h1 in L, Georgia's six removed (54 values);
    q95 and q975 with numpy method 'higher', q05 and q025 with 'lower', as level-mde computes
    them; c_hi(p) = max(t_{nu_h1,p}, q) and c_lo(p) = min(-t_{nu_h1,1-p}, q) with level-mde's
    nu_h1 (unchanged). With these, the one-sided 5% H1 decisions (tau / SE > c_hi(0.95)) for the
    pooled, year-1 and year-2 wage ATTs of h1-wage, and their 95% and 90% intervals.
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


def qcew_georgia(path=QCEW):
    """Georgia's state rows (four industries) and 722513 county rows, 2014Q1-2016Q4."""
    cols = ["area_fips", "state_fips", "area_level", "industry", "own_code", "year", "qtr",
            "disclosure_code", "suppressed", "establishments", "month1_emplvl", "month2_emplvl",
            "month3_emplvl", "avg_wkly_wage"]
    q = pd.read_csv(path, dtype={"area_fips": str, "state_fips": str, "industry": str,
                                 "own_code": str, "disclosure_code": str}, usecols=cols)
    q["qi"] = 4 * q["year"] + q["qtr"] - 1
    q = q[(q.state_fips == GA) & q.qi.between(Q_FIRST, Q_LAST) & q.industry.isin(IND)].copy()
    q["emp"] = q[["month1_emplvl", "month2_emplvl", "month3_emplvl"]].mean(axis=1)
    q["disclosure_code"] = q["disclosure_code"].fillna("")
    return q


def part_a(q, pre):
    m, rows = {}, []
    st = q[q.area_level == "state"]
    for ind in IND:
        d = st[st.industry == ind].sort_values("qi")
        for _, r in d.iterrows():
            rows.append({"industry": ind, "level": "state", "quarter": S.qlabel(int(r.qi)),
                         "disclosure_code": r.disclosure_code, "establishments": r.establishments,
                         "emp": r.emp, "avg_wkly_wage": r.avg_wkly_wage})
        m[f"a_ga_{ind}_rows"] = int(len(d))
        m[f"a_ga_{ind}_suppressed_quarters"] = int(d.suppressed.sum())
    cty = q[(q.area_level == "county") & (q.industry == "722513")]
    for qi, d in cty.groupby("qi"):
        lab = S.qlabel(int(qi))
        rows.append({"industry": "722513", "level": "county_sum", "quarter": lab,
                     "disclosure_code": f"{int(d.suppressed.sum())} of {len(d)} suppressed",
                     "establishments": d.establishments.sum(), "emp": d.emp.sum(),
                     "avg_wkly_wage": np.nan})
        m[f"a_ga_722513_counties_{lab}"] = int(len(d))
        m[f"a_ga_722513_counties_suppressed_{lab}"] = int(d.suppressed.sum())
    # year-over-year log changes against the cross-state median (722513, state rows)
    s13 = st[st.industry == "722513"].set_index("qi")
    p = pre.copy()
    p["qi"] = 4 * p["year"] + p["qtr"] - 1
    wide_w = p.pivot(index="qi", columns="state_fips", values="aww_722513")
    wide_e = p.pivot(index="qi", columns="state_fips", values="emp_722513")
    dw = np.log(wide_w) - np.log(wide_w.shift(4))
    de = np.log(wide_e) - np.log(wide_e.shift(4))
    dev_w = dw.sub(dw.median(axis=1), axis=0)
    dev_e = de.sub(de.median(axis=1), axis=0)
    for y, qq in [(2015, 1), (2015, 2), (2015, 3), (2015, 4)]:
        qi = S.qidx(y, qq)
        lab = S.qlabel(qi)
        m[f"a_ga_aww_yoy_dev_{lab}"] = float(dev_w.loc[qi, GA])
        m[f"a_ga_emp_yoy_dev_{lab}"] = float(dev_e.loc[qi, GA])
        m[f"a_ga_estabs_yoy_{lab}"] = float(np.log(s13.loc[qi, "establishments"])
                                            - np.log(s13.loc[qi - 4, "establishments"]))
        m[f"a_ga_aww_{lab}"] = float(wide_w.loc[qi, GA])
        m[f"a_ga_aww_{S.qlabel(qi - 4)}"] = float(wide_w.loc[qi - 4, GA])
    # scale: the largest other |wage deviation| over 2015Q1-2019Q4
    win = dev_w.loc[S.qidx(2015, 1):S.qidx(2019, 4)].stack()
    ga15 = [(S.qidx(2015, k), GA) for k in (1, 2, 3, 4)]
    other = win.drop(index=[i for i in ga15 if i in win.index])
    big = other.abs().idxmax()
    m["a_largest_other_aww_yoy_dev"] = float(other.loc[big])
    m["a_largest_other_aww_yoy_dev_state"] = str(big[1])
    m["a_largest_other_aww_yoy_dev_quarter"] = S.qlabel(int(big[0]))
    m["a_ga_aww_yoy_dev_2015_min"] = float(min(m[f"a_ga_aww_yoy_dev_{S.qlabel(i)}"] for i, _ in ga15))
    return m, pd.DataFrame(rows)


def part_b(tests, m_lvl, m_h1):
    m = {}
    d = tests[(tests.stat == "h1") & (tests.in_L == 1)]
    if len(d) != 60:
        raise ValueError(f"{len(d)} H1 tests in L, expected 60")
    dx = d[d.unit.astype(str).str.zfill(2) != GA]
    m["b_n_L_without_ga"] = int(len(dx))
    m["b_ga_L_tests"] = int(len(d) - len(dx))
    T = (dx.tau / dx.se).to_numpy()
    T_ga = (d.tau / d.se)[d.unit.astype(str).str.zfill(2) == GA].to_numpy()
    m["b_ga_T_max"] = float(T_ga.max())
    m["b_others_T_max"] = float(T.max())
    lq = S.l_quantiles(T)
    nu = float(m_lvl["nu_h1"])
    c = S.critical_values(nu, lq)
    for k, v in lq.items():
        m[f"b_Lq_h1_noga_{k}"] = v
    for k, v in c.items():
        m[f"b_crit_h1_noga_{k}"] = v
        m[f"b_crit_h1_noga_{k}_from_L"] = int(v != S.critical_values(nu)[k])
        m[f"b_crit_h1_prespecified_{k}"] = float(m_lvl[f"crit_h1_{k}"])
    m["b_nu_h1"] = nu
    for tag in ("h1", "h1_y1", "h1_y2"):
        tau, se = float(m_h1[f"{tag}_att"]), float(m_h1[f"{tag}_se"])
        m[f"b_{tag}_t"] = tau / se
        m[f"b_{tag}_reject_noga"] = S.one_sided_reject(tau, se, c)
        m[f"b_{tag}_reject_prespecified"] = int(m_h1[f"{tag}_reject"])
        for k, v in S.intervals(tau, se, c).items():
            m[f"b_{tag}_noga_{k}"] = float(v)
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
    ma, tab = part_a(qcew_georgia(), pre)
    m.update(ma)
    m.update(part_b(pd.read_csv(TESTS, dtype={"unit": str}), m_lvl, m_h1))
    m.update(part_c(pd.read_csv(EVENT)))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tab.to_csv(OUT_DIR / "georgia.csv", index=False, float_format="%.6g")
    S.write_json(OUT_DIR / "metrics.json", m)
    print(f"posthoc: H1 without Georgia c_hi95 {m['b_crit_h1_noga_hi95']:.3f}, pooled reject "
          f"{m['b_h1_reject_noga']}; drift emp {m['c_emp_slope_2014_2019']:.4f}/q")


if __name__ == "__main__":
    sys.exit(main())
