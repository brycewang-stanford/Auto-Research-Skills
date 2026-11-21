"""Run describe (design deviation D8; added at the paper stage after paper-r1 P3; report-only).

Levels only, for the summary-statistics table: no statistic compares California with another
unit, or one period with another (no differences, ratios or growth rates).

Inputs  data/derived/state_panel.csv   employment and weekly wage, private NAICS 722513 (state rows)
        data/derived/qcew_panel.csv    establishments, private NAICS 722513 (state rows, own 5)
Output  runs/describe/metrics.json, runs/describe/table.csv

Groups: California (06); R50 (the 50 other states and DC); D20 (Dube's 20 federal-minimum
states). Periods (design.method NOTATION, real base 2023Q3): pre = the fit window F =
2014Q1-2019Q4 and 2022Q1-2023Q3 (31 quarters; COVID quarters 2020Q1-2021Q4 out); post = P =
2024Q2-2026Q1 (8 quarters; 2026Q1 preliminary). All figures are published levels, not
seasonally adjusted. For each group and period:
  emp_mean     mean over the group's states and the period's quarters of quarterly employment
               (mean of the three monthly levels)
  emp_total    mean over the period's quarters of the group's summed employment
  aww          the group's average weekly wage, sum of total quarterly wages / (13 x sum of
               employment), averaged over the period's quarters; the same formula for every
               group, so California's figure can differ by rounding from BLS's published value
  estabs_mean  mean over states and quarters of the quarterly establishment count
  estabs_total mean over quarters of the group's summed establishment count
  n_states, n_quarters, n_obs (state-quarters)
"""
import sys
from pathlib import Path

import pandas as pd

import sclib as S

PANEL = Path("data/derived/state_panel.csv")
QCEW = Path("data/derived/qcew_panel.csv")
OUT_DIR = Path("runs/describe")
GROUPS = {"CA": [S.CA], "R50": S.R50, "D20": S.D20}


def periods():
    pre = [q for q in range(S.FIT_START, S.REAL_B + 1) if q not in S.COVID]
    post = list(range(S.REAL_B + 3, S.REAL_B + 11))
    return {"pre": pre, "post": post}


def establishments(path=QCEW):
    q = pd.read_csv(path, dtype={"state_fips": str, "industry": str, "own_code": str},
                    usecols=["state_fips", "area_level", "industry", "own_code", "year", "qtr",
                             "establishments"])
    q = q[(q.area_level == "state") & (q.industry == "722513") & (q.own_code == "5")
          & q.state_fips.isin(S.ALL51)].copy()
    if q.duplicated(["state_fips", "year", "qtr"]).any():
        raise ValueError("duplicate state rows for 722513")
    q["qi"] = 4 * q["year"] + q["qtr"] - 1
    return q[["state_fips", "qi", "establishments"]]


def describe(panel_df, estabs):
    df = panel_df.copy()
    df["state_fips"] = df["state_fips"].astype(str).str.zfill(2)
    df["qi"] = 4 * df["year"].astype(int) + df["qtr"].astype(int) - 1
    df = df.merge(estabs, on=["state_fips", "qi"], how="left")
    m, rows = {}, []
    for pname, qs in periods().items():
        for g, units in GROUPS.items():
            d = df[df.state_fips.isin(units) & df.qi.isin(qs)]
            if d[["emp_722513", "wages_722513", "establishments"]].isna().any().any():
                raise ValueError(f"missing value for {g} in the {pname} period")
            if len(d) != len(units) * len(qs):
                raise ValueError(f"{g} {pname}: {len(d)} rows, expected {len(units) * len(qs)}")
            by_q = d.groupby("qi")
            vals = {
                "emp_mean": float(d.emp_722513.mean()),
                "emp_total": float(by_q.emp_722513.sum().mean()),
                "aww": float((by_q.wages_722513.sum() / (13.0 * by_q.emp_722513.sum())).mean()),
                "estabs_mean": float(d.establishments.mean()),
                "estabs_total": float(by_q.establishments.sum().mean()),
                "n_states": int(d.state_fips.nunique()),
                "n_quarters": int(d.qi.nunique()),
                "n_obs": int(len(d)),
            }
            for k, v in vals.items():
                m[f"desc_{g}_{k}_{pname}"] = v
            rows.append({"group": g, "period": pname, **vals})
    pr = periods()
    m["desc_pre_quarters"] = f"{S.qlabel(pr['pre'][0])}-2019Q4, 2022Q1-{S.qlabel(pr['pre'][-1])}"
    m["desc_post_quarters"] = f"{S.qlabel(pr['post'][0])}-{S.qlabel(pr['post'][-1])}"
    return m, pd.DataFrame(rows)


def main():
    m, tab = describe(S.read_panel_csv(PANEL), establishments())
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tab.to_csv(OUT_DIR / "table.csv", index=False, float_format="%.6g")
    S.write_json(OUT_DIR / "metrics.json", m)
    print(f"describe: {len(tab)} rows")


if __name__ == "__main__":
    sys.exit(main())
