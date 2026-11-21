"""Build the state x quarter panel of the design (plan.json design.data; analysis_plan step 0e).

Inputs
  data/derived/qcew_panel.csv                   QCEW rows (run prepare-data); state rows only:
      722513 and 722511 private (agglvl 58), 7225 private (56), 10 Total Covered (50)
  data/raw/census/sc-est2020int-alldata6.csv    2010-2020 intercensal estimates (run fetch-pop)
  data/raw/census/NST-EST2025-ALLDATA.csv       Vintage 2025 estimates (run fetch-pop)

Outputs
  data/derived/state_panel.csv       50 states + DC, 2014Q1-2026Q1 (51 x 49 rows)
  data/derived/state_panel_pre.csv   the same rows for 2014Q1-2019Q4 only, byte for byte
  data/prepare_state_metrics.json    counts and pass/fail checks

Variables (design.data)
  emp_X        mean(month1_emplvl, month2_emplvl, month3_emplvl), X in 722513, 722511, 7225, 10
  emp_nonff    emp_10 - emp_722513
  sep_722513   month3_emplvl of 722513
  wages_722513 total_qtrly_wages of 722513 (nominal dollars)
  aww_722513   avg_wkly_wage of 722513 as BLS publishes it
  pop          July 1 resident population, ln-linearly interpolated to the quarter
  pop_extrap   1 if the quarter lies after the last July 1 anchor (2025.5) and pop is extrapolated
  sup_7225     1 if the state 7225 row is suppressed (emp_7225 then missing)

Population (design.data, source 2): July 1 anchors 2013-2019 from the intercensal file
(SEX 0, ORIGIN 0, summed over RACE 1-6 and AGE 0-85), 2020-2025 from Vintage 2025
(POPESTIMATE2020-2025). Anchor of year y at y + 0.5; quarter q of year y at y + (q - 0.5)/4;
ln pop linear between anchors; after 2025.5, ln pop(2025) + (x - 2025.5) * [ln pop(2025) -
ln pop(2024)].

Checks (analysis_plan 0e): 51 units x 49 quarters; no missing 722513 / 722511 / 10 state value;
the aww identity |avg_wkly_wage - total_qtrly_wages / (13 * emp)| <= $1; the population splice
(count of states whose V2025 July 2020 / intercensal July 2019 ratio is outside 0.97-1.03;
population only); the extrapolation flag; state_panel_pre.csv = the 2014Q1-2019Q4 rows of
state_panel.csv byte for byte. Further population-only consistency checks are counted.

No statistic of employment or wages that compares areas or periods is computed. The script
fails (nonzero exit) if a required check fails.
"""
import json
import math
from pathlib import Path

import pandas as pd

QCEW = Path("data/derived/qcew_panel.csv")
INTERCENSAL = Path("data/raw/census/sc-est2020int-alldata6.csv")
V2025 = Path("data/raw/census/NST-EST2025-ALLDATA.csv")
OUT_FULL = Path("data/derived/state_panel.csv")
OUT_PRE = Path("data/derived/state_panel_pre.csv")
METRICS = Path("data/prepare_state_metrics.json")

ABBR = {"01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA", "08": "CO", "09": "CT",
        "10": "DE", "11": "DC", "12": "FL", "13": "GA", "15": "HI", "16": "ID", "17": "IL",
        "18": "IN", "19": "IA", "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
        "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO", "30": "MT", "31": "NE",
        "32": "NV", "33": "NH", "34": "NJ", "35": "NM", "36": "NY", "37": "NC", "38": "ND",
        "39": "OH", "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC", "46": "SD",
        "47": "TN", "48": "TX", "49": "UT", "50": "VT", "51": "VA", "53": "WA", "54": "WV",
        "55": "WI", "56": "WY"}
D20 = ["01", "13", "19", "16", "18", "20", "21", "22", "28", "37", "38", "33", "40", "42", "45",
       "47", "48", "49", "55", "56"]
START, END, PRE_END = (2014, 1), (2026, 1), (2019, 4)
LAST_ANCHOR = 2025
COLUMNS = ["state_fips", "state_abbr", "year", "qtr", "quarter", "emp_722513", "emp_722511",
           "emp_7225", "emp_10", "emp_nonff", "sep_722513", "wages_722513", "aww_722513", "pop",
           "pop_extrap", "sup_7225"]


def quarters():
    y, q = START
    while (y, q) <= END:
        yield y, q
        y, q = (y, q + 1) if q < 4 else (y + 1, 1)


def population(metrics):
    """July 1 anchors by state, 2013-2025, and the population-only checks."""
    ic = pd.read_csv(INTERCENSAL, dtype={"SUMLEV": str, "STATE": str}, encoding="latin-1")
    ic = ic[ic.STATE.isin(ABBR)]
    years_ic = list(range(2013, 2020))
    cols_ic = [f"POPESTIMATE{y}" for y in years_ic]
    tot = ic[(ic.SEX == 0) & (ic.ORIGIN == 0)].groupby("STATE")[cols_ic].sum()
    by_sex = ic[(ic.SEX.isin([1, 2])) & (ic.ORIGIN == 0)].groupby("STATE")[cols_ic].sum()
    by_origin = ic[(ic.SEX == 0) & (ic.ORIGIN.isin([1, 2]))].groupby("STATE")[cols_ic].sum()
    cells = len(ABBR) * len(years_ic)
    metrics["pop_intercensal_state_years"] = int(tot.size)
    metrics["pop_intercensal_sex_sum_matches"] = int((tot == by_sex.loc[tot.index]).to_numpy().sum())
    metrics["pop_intercensal_origin_sum_matches"] = int((tot == by_origin.loc[tot.index]).to_numpy().sum())
    if metrics["pop_intercensal_sex_sum_matches"] != cells or metrics["pop_intercensal_origin_sum_matches"] != cells:
        print("WARNING: intercensal SEX or ORIGIN parts do not add up to the totals in every state-year")

    v = pd.read_csv(V2025, dtype={"SUMLEV": str, "STATE": str}, encoding="latin-1")
    years_v = list(range(2020, LAST_ANCHOR + 1))
    cols_v = [f"POPESTIMATE{y}" for y in years_v]
    vs = v[(v.SUMLEV == "040") & v.STATE.isin(ABBR)].set_index("STATE")[cols_v]
    us = v[v.SUMLEV == "010"][cols_v].iloc[0]
    metrics["pop_v2025_states"] = int(len(vs))
    metrics["pop_v2025_years_51_sum_to_us"] = int(sum(int(vs[c].sum()) == int(us[c]) for c in cols_v))

    anchors = pd.concat([tot.rename(columns=lambda c: int(c[-4:])),
                         vs.rename(columns=lambda c: int(c[-4:]))], axis=1)
    anchors = anchors.loc[sorted(ABBR)]
    if anchors.isna().any().any() or (anchors <= 0).any().any():
        raise SystemExit("ERROR: missing or non-positive population anchor")
    ratio = anchors[2020] / anchors[2019]
    metrics["splice_states_checked"] = int(ratio.notna().sum())
    metrics["splice_states_ratio_outside_0.97_1.03"] = int(((ratio < 0.97) | (ratio > 1.03)).sum())
    metrics["splice_pass"] = int(metrics["splice_states_ratio_outside_0.97_1.03"] == 0)
    return anchors


def ln_pop_at(anchor_row, x):
    """ln population at time x (years), anchors at y + 0.5. Returns (ln pop, extrapolated)."""
    years = sorted(anchor_row.index)
    lp = {y: math.log(float(anchor_row[y])) for y in years}
    last = years[-1]
    if x > last + 0.5:
        return lp[last] + (x - (last + 0.5)) * (lp[last] - lp[last - 1]), 1
    if x < years[0] + 0.5:
        raise SystemExit(f"ERROR: quarter time {x} precedes the first anchor")
    y0 = int(math.floor(x - 0.5))
    if y0 == last:  # x exactly at the last anchor
        return lp[last], 0
    w = (x - (y0 + 0.5))
    return (1 - w) * lp[y0] + w * lp[y0 + 1], 0


def main():
    metrics = {}
    anchors = population(metrics)

    q = pd.read_csv(QCEW, dtype={"area_fips": str, "state_fips": str, "industry": str,
                                 "own_code": str, "agglvl_code": str, "disclosure_code": str})
    st = q[q.area_level == "state"]
    metrics["qcew_state_rows_read"] = int(len(st))
    dropped = st[~st.state_fips.isin(ABBR)]
    metrics["qcew_state_rows_dropped_pr_vi"] = int(len(dropped))
    metrics["qcew_state_codes_dropped"] = ",".join(sorted(dropped.state_fips.unique()))
    st = st[st.state_fips.isin(ABBR)].copy()
    st["emp"] = st[["month1_emplvl", "month2_emplvl", "month3_emplvl"]].mean(axis=1, skipna=False)
    if st.duplicated(["state_fips", "industry", "year", "qtr"]).any():
        raise SystemExit("ERROR: duplicate state-industry-quarter rows")

    grid = pd.DataFrame([(s, y, qq) for s in sorted(ABBR) for (y, qq) in quarters()],
                        columns=["state_fips", "year", "qtr"])
    out = grid.copy()
    out["state_abbr"] = out.state_fips.map(ABBR)
    out["quarter"] = out.year.astype(str) + "Q" + out.qtr.astype(str)
    keys = ["state_fips", "year", "qtr"]
    for ind in ["722513", "722511", "7225", "10"]:
        part = st[st.industry == ind][keys + ["emp", "month3_emplvl", "total_qtrly_wages",
                                              "avg_wkly_wage", "suppressed"]]
        part = part.rename(columns={c: f"{c}_{ind}" for c in part.columns if c not in keys})
        metrics[f"rows_matched_{ind}"] = int(len(out.merge(part, on=keys, how="inner")))
        out = out.merge(part, on=keys, how="left")
        metrics[f"missing_{ind}"] = int(out[f"emp_{ind}"].isna().sum())
        metrics[f"suppressed_{ind}"] = int(out[f"suppressed_{ind}"].fillna(0).sum())

    out["emp_nonff"] = out["emp_10"] - out["emp_722513"]
    out["sep_722513"] = out["month3_emplvl_722513"]
    out["wages_722513"] = out["total_qtrly_wages_722513"]
    out["aww_722513"] = out["avg_wkly_wage_722513"]
    out["sup_7225"] = out["suppressed_7225"].fillna(0).astype(int)

    # required: no missing 722513 / 722511 / 10 state value
    need = ["emp_722513", "emp_722511", "emp_10", "sep_722513", "wages_722513", "aww_722513",
            "total_qtrly_wages_722511", "total_qtrly_wages_10", "avg_wkly_wage_722511", "avg_wkly_wage_10"]
    metrics["missing_required_values"] = int(out[need].isna().sum().sum())
    metrics["missing_emp_7225"] = int(out["emp_7225"].isna().sum())
    metrics["sup_7225_rows"] = int(out["sup_7225"].sum())
    metrics["missing_emp_7225_equals_sup_7225"] = int(
        (out["emp_7225"].isna() == (out["sup_7225"] == 1)).all())

    # aww identity, row by row (no aggregation across rows)
    resid = (out["aww_722513"] - out["wages_722513"] / (13 * out["emp_722513"])).abs()
    metrics["aww_rows_checked"] = int(resid.notna().sum())
    metrics["aww_rows_outside_1usd"] = int((resid > 1).sum())
    metrics["aww_identity_pass"] = int(metrics["aww_rows_outside_1usd"] == 0
                                       and metrics["aww_rows_checked"] == len(out))

    # population
    pops, flags = [], []
    for s, y, qq in zip(out.state_fips, out.year, out.qtr):
        lp, flag = ln_pop_at(anchors.loc[s], y + (qq - 0.5) / 4)
        pops.append(math.exp(lp))
        flags.append(flag)
    out["pop"] = pops
    out["pop_extrap"] = flags
    metrics["pop_missing"] = int(out["pop"].isna().sum())
    ext = out[out.pop_extrap == 1]
    metrics["pop_extrap_rows"] = int(len(ext))
    metrics["pop_extrap_quarters"] = ",".join(sorted(ext.quarter.unique()))

    out = out[COLUMNS].sort_values(keys).reset_index(drop=True)
    metrics["rows"] = int(len(out))
    metrics["units"] = int(out.state_fips.nunique())
    metrics["quarters"] = int(out.quarter.nunique())
    metrics["first_quarter"] = out.quarter.iloc[0]
    metrics["last_quarter"] = out.quarter.iloc[-1]
    metrics["balanced_51x49"] = int(metrics["units"] == 51 and metrics["quarters"] == 49
                                    and metrics["rows"] == 51 * 49
                                    and not out.duplicated(keys).any())
    metrics["d20_states_present"] = int(sum(s in set(out.state_fips) for s in D20))
    metrics["california_present"] = int("06" in set(out.state_fips))

    OUT_FULL.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_FULL, index=False, lineterminator="\n")
    pre = out[(out.year < PRE_END[0]) | ((out.year == PRE_END[0]) & (out.qtr <= PRE_END[1]))]
    pre.to_csv(OUT_PRE, index=False, lineterminator="\n")

    # byte-for-byte: the pre file equals the header plus the 2014Q1-2019Q4 lines of the full file
    full_lines = OUT_FULL.read_bytes().split(b"\n")
    header, body = full_lines[0], [ln for ln in full_lines[1:] if ln]
    year_col = header.split(b",").index(b"year")
    kept = [ln for ln in body if int(ln.split(b",")[year_col]) <= PRE_END[0]]
    expected = b"\n".join([header] + kept) + b"\n"
    metrics["pre_rows"] = int(len(pre))
    metrics["pre_quarters"] = int(pre.quarter.nunique())
    metrics["pre_last_quarter"] = pre.quarter.iloc[-1] if len(pre) else ""
    metrics["pre_bytes_identical"] = int(OUT_PRE.read_bytes() == expected)
    metrics["pre_max_year"] = int(pre.year.max())

    required = ["balanced_51x49", "aww_identity_pass", "pre_bytes_identical",
                "missing_emp_7225_equals_sup_7225"]
    failed = [k for k in required if metrics[k] != 1]
    if metrics["missing_required_values"] or metrics["pop_missing"]:
        failed.append("missing values")
    METRICS.write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps(metrics))
    if failed:
        raise SystemExit(f"ERROR: checks failed: {failed}")


if __name__ == "__main__":
    main()
