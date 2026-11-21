"""Stack the QCEW industry slices into one county/state/national panel.

Reads data/raw/qcew/<year>q<qtr>_<code>.csv (written by code/fetch_data.py) and writes
  data/derived/qcew_panel.csv               the panel
  data/derived/suppression_by_state_year.csv county-cell counts by state, industry, year
  data/prepare_metrics.json                  row counts kept/dropped and checks

Row selection (aggregation-level codes from the BLS QCEW agglevel titles,
https://data.bls.gov/cew/doc/titles/agglevel/agglevel_titles.csv, and ownership codes from
https://data.bls.gov/cew/doc/titles/ownership/ownership_titles.csv):
  722513, 722511 (NAICS 6-digit), own_code 5 (Private):
      agglvl 18 national / 58 state / 78 county  "NAICS 6-digit -- by ownership sector"
  7225 (NAICS 4-digit), own_code 5:
      agglvl 16 national / 56 state / 76 county  "NAICS 4-digit -- by ownership sector"
  10 (total, all industries), own_code 0 (Total Covered):
      agglvl 10 national / 50 state / 70 county  "Total Covered"
Everything else (MSA, CSA, MicroSA and U.S. summary levels; government ownership; private
and government rows of industry 10) is dropped and counted by reason.

Suppressed cells (disclosure_code "N"): BLS reports the establishment count but writes 0
for employment and wages; those zeros are set to missing here. Rows with disclosure_code
"-" (not in the layout documentation; every such row has 0 establishments) are kept as
reported and counted.

No statistic of employment or wages that compares areas or periods is computed; the only
sums are the identity checks (counties add up to states, states to the nation) for
industry 10, reported as counts of quarters that match.
"""
import json
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/qcew")
OUT = Path("data/derived")
INDUSTRIES = ["722513", "722511", "7225", "10"]
START, END = (2014, 1), (2026, 1)
KEEP = {  # industry -> (own_code, {agglvl: area_level})
    "722513": ("5", {"18": "national", "58": "state", "78": "county"}),
    "722511": ("5", {"18": "national", "58": "state", "78": "county"}),
    "7225": ("5", {"16": "national", "56": "state", "76": "county"}),
    "10": ("0", {"10": "national", "50": "state", "70": "county"}),
}
NUM = ["qtrly_estabs", "month1_emplvl", "month2_emplvl", "month3_emplvl",
       "total_qtrly_wages", "avg_wkly_wage"]
VALUE = ["month1_emplvl", "month2_emplvl", "month3_emplvl", "total_qtrly_wages", "avg_wkly_wage"]


def quarters():
    y, q = START
    while (y, q) <= END:
        yield y, q
        y, q = (y, q + 1) if q < 4 else (y + 1, 1)


def level_of_dropped(agg: str) -> str:
    a = int(agg)
    if a < 30:
        return "national"
    if a < 50:
        return "msa_csa"
    if a < 70:
        return "state"
    if a < 80:
        return "county"
    if a < 90:
        return "microsa"
    return "us_summary"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    frames, metrics = [], {}
    rows_read, dropped = 0, {}
    for y, q in quarters():
        for code in INDUSTRIES:
            d = pd.read_csv(RAW / f"{y}q{q}_{code}.csv", dtype=str, keep_default_na=False)
            rows_read += len(d)
            assert (d["industry_code"] == code).all(), f"{y}q{q}_{code}: unexpected industry_code"
            assert (d["year"] == str(y)).all() and (d["qtr"] == str(q)).all()
            assert (d["size_code"] == "0").all()
            own, levels = KEEP[code]
            keep = d["agglvl_code"].isin(levels) & (d["own_code"] == own)
            for (agg, o), n in d[~keep].groupby(["agglvl_code", "own_code"]).size().items():
                if agg in levels:
                    reason = f"{level_of_dropped(agg)}_own{o}"
                else:
                    reason = f"{level_of_dropped(agg)}_agglvl"
                key = f"dropped_{code}_{reason}"
                dropped[key] = dropped.get(key, 0) + int(n)
            k = d[keep].copy()
            k["area_level"] = k["agglvl_code"].map(levels)
            frames.append(k)
    p = pd.concat(frames, ignore_index=True)
    for c in NUM:
        p[c] = pd.to_numeric(p[c], errors="raise")
    p["year"] = p["year"].astype(int)
    p["qtr"] = p["qtr"].astype(int)
    p["state_fips"] = p["area_fips"].str[:2].where(p["area_level"] != "national", "US")
    unknown = (p["area_level"] == "county") & p["area_fips"].str.endswith("999")
    p.loc[unknown, "area_level"] = "county_unknown"
    p["suppressed"] = (p["disclosure_code"] == "N").astype(int)
    # suppressed cells carry zeros, not values
    assert (p.loc[p["suppressed"] == 1, VALUE] == 0).all().all(), "suppressed row with a nonzero value"
    p.loc[p["suppressed"] == 1, VALUE] = float("nan")
    p = p.rename(columns={"industry_code": "industry", "qtrly_estabs": "establishments"})
    cols = ["area_fips", "state_fips", "area_level", "industry", "own_code", "agglvl_code",
            "year", "qtr", "disclosure_code", "suppressed", "establishments",
            "month1_emplvl", "month2_emplvl", "month3_emplvl", "total_qtrly_wages", "avg_wkly_wage"]
    p = p[cols].sort_values(["industry", "area_level", "area_fips", "year", "qtr"]).reset_index(drop=True)
    dup = int(p.duplicated(["area_fips", "industry", "year", "qtr"]).sum())
    assert dup == 0, f"{dup} duplicate area-industry-quarter rows"
    p.to_csv(OUT / "qcew_panel.csv", index=False)

    metrics["rows_read"] = rows_read
    metrics["rows_kept"] = len(p)
    metrics["rows_dropped"] = rows_read - len(p)
    metrics.update(dict(sorted(dropped.items())))
    assert sum(dropped.values()) == metrics["rows_dropped"]
    metrics["duplicate_keys"] = dup
    for (ind, lev), n in p.groupby(["industry", "area_level"]).size().items():
        metrics[f"kept_{ind}_{lev}"] = int(n)
    for ind in INDUSTRIES:
        s = p[p["industry"] == ind]
        metrics[f"suppressed_{ind}_all_levels"] = int(s["suppressed"].sum())
        metrics[f"dash_code_{ind}"] = int((s["disclosure_code"] == "-").sum())
        metrics[f"n_states_{ind}"] = int(s.loc[s["area_level"] == "state", "area_fips"].nunique())
        metrics[f"n_counties_{ind}"] = int(s.loc[s["area_level"] == "county", "area_fips"].nunique())
    # county-industry cells by state x industry x year (named counties, not XX999)
    c = p[p["area_level"] == "county"]
    tab = (c.groupby(["state_fips", "industry", "year"])
             .agg(county_quarter_cells=("suppressed", "size"),
                  suppressed_cells=("suppressed", "sum"),
                  dash_cells=("disclosure_code", lambda s: int((s == "-").sum())),
                  counties=("area_fips", "nunique"))
             .reset_index())
    tab.to_csv(OUT / "suppression_by_state_year.csv", index=False)
    yearly = c.groupby(["industry", "year"]).agg(cells=("suppressed", "size"),
                                                 supp=("suppressed", "sum"),
                                                 counties=("area_fips", "nunique"))
    for (ind, yr), r in yearly.iterrows():
        metrics[f"county_cells_{ind}_{yr}"] = int(r["cells"])
        metrics[f"county_suppressed_{ind}_{yr}"] = int(r["supp"])
        metrics[f"county_n_{ind}_{yr}"] = int(r["counties"])
    # identity checks for industry 10 total covered (all disclosed in practice)
    t = p[p["industry"] == "10"]
    key = ["year", "qtr"]
    cty = t[t["area_level"].isin(["county", "county_unknown"])].groupby(["state_fips"] + key)["month3_emplvl"].sum()
    st = t[t["area_level"] == "state"].set_index(["state_fips"] + key)["month3_emplvl"]
    j = pd.concat([cty.rename("c"), st.rename("s")], axis=1).dropna()
    metrics["check10_state_quarters"] = len(j)
    metrics["check10_counties_sum_to_state"] = int((j["c"] == j["s"]).sum())
    nat = t[t["area_level"] == "national"].set_index(key)["month3_emplvl"]
    sts = t[t["area_level"] == "state"].groupby(key)["month3_emplvl"].sum()
    jj = pd.concat([sts.rename("s"), nat.rename("n")], axis=1).dropna()
    metrics["check10_quarters"] = len(jj)
    metrics["check10_states_sum_to_nation"] = int((jj["s"] == jj["n"]).sum())
    sts51 = t[(t["area_level"] == "state") & ~t["state_fips"].isin(["72", "78"])].groupby(key)["month3_emplvl"].sum()
    j51 = pd.concat([sts51.rename("s"), nat.rename("n")], axis=1).dropna()
    metrics["check10_50states_dc_sum_to_nation"] = int((j51["s"] == j51["n"]).sum())
    metrics["suppressed_10_all_levels_check"] = int(t["suppressed"].sum())
    Path("data/prepare_metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps({k: v for k, v in metrics.items() if not k.startswith("county_")}, indent=1))


if __name__ == "__main__":
    main()
