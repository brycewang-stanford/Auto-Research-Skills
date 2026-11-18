"""Prepare the 1991 SIPP 401(k) extract for the PLR replication.

Reads data/raw/sipp1991.dta (written by code/fetch_sipp.py), checks the row count
and the presence of the eleven variables the study uses, and writes
data/derived/sipp1991.csv with exactly those columns and every row (no sample
restriction is applied).

Outputs
- data/derived/sipp1991.csv          outcome, treatment and nine controls, all rows
- data/derived/sipp1991_summary.json  per-variable summary statistics, each variable
                                      on its own (pooled over all rows; nothing is
                                      computed by e401 or across e401 and net_tfa)
- data/prepare_metrics.json           flat counts: rows, missing values per column,
                                      checks against the source

Run from the workspace root:
    .venv/bin/python -I code/prepare_sipp.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/sipp1991.dta")
OUT = Path("data/derived/sipp1991.csv")
SUMMARY = Path("data/derived/sipp1991_summary.json")
METRICS = Path("data/prepare_metrics.json")

EXPECTED_ROWS = 9915  # Belloni et al. (2017, Sec. 7); ddml; DoubleML docs
OUTCOME = "net_tfa"
TREATMENT = "e401"
CONTROLS = ["age", "inc", "educ", "fsize", "marr", "twoearn", "db", "pira", "hown"]
KEEP = [OUTCOME, TREATMENT] + CONTROLS
BINARY = [TREATMENT, "marr", "twoearn", "db", "pira", "hown"]


def describe(series: pd.Series) -> dict:
    s = series.dropna().astype("float64")
    q = s.quantile([0.01, 0.25, 0.5, 0.75, 0.99])
    return {
        "n": int(s.size),
        "mean": float(s.mean()),
        "sd": float(s.std(ddof=1)),
        "min": float(s.min()),
        "p01": float(q[0.01]),
        "p25": float(q[0.25]),
        "median": float(q[0.5]),
        "p75": float(q[0.75]),
        "p99": float(q[0.99]),
        "max": float(s.max()),
        "n_distinct": int(s.nunique()),
    }


def main() -> int:
    raw = pd.read_stata(RAW, convert_categoricals=False)
    metrics: dict = {
        "rows_raw": int(len(raw)),
        "columns_raw": int(raw.shape[1]),
        "rows_expected": EXPECTED_ROWS,
        "rows_match_expected": bool(len(raw) == EXPECTED_ROWS),
    }

    missing_vars = [v for v in KEEP if v not in raw.columns]
    metrics["required_vars_missing"] = len(missing_vars)
    if missing_vars:
        print(f"MISSING VARIABLES: {missing_vars}", file=sys.stderr)
        METRICS.write_text(json.dumps(metrics, indent=2) + "\n")
        return 1
    metrics["raw_columns_not_kept"] = ",".join(c for c in raw.columns if c not in KEEP)

    df = raw[KEEP].copy()
    for col in KEEP:
        metrics[f"missing_{col}"] = int(df[col].isna().sum())
    metrics["rows_any_missing"] = int(df.isna().any(axis=1).sum())

    # Coding checks on single variables only.
    for col in BINARY:
        metrics[f"nonbinary_{col}"] = int((~df[col].isin([0, 1])).sum())
    metrics["count_e401_eq_1"] = int((df[TREATMENT] == 1).sum())
    metrics["count_net_tfa_negative"] = int((df[OUTCOME] < 0).sum())
    metrics["count_net_tfa_zero"] = int((df[OUTCOME] == 0).sum())
    metrics["count_inc_nonpositive"] = int((df["inc"] <= 0).sum())
    # Diagnostic only (no restriction applied): rows inside the sample rules that
    # Abadie (2003) states for his 9,275-row sample.
    metrics["count_inc_10k_200k"] = int(df["inc"].between(10000, 200000).sum())
    metrics["count_age_25_64"] = int(df["age"].between(25, 64).sum())

    # No sample restriction: every raw row is kept.
    metrics["rows_dropped"] = int(len(raw) - len(df))
    metrics["rows_kept"] = int(len(df))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    summary = {col: describe(df[col]) for col in KEEP}
    # Pooled means inside Abadie's (2003) income band, for comparison with the
    # "Entire Sample" column of his Table I (9,275 rows). Single variables only.
    band = df[df["inc"].between(10000, 200000)]
    summary["abadie_income_band_means"] = {
        "n": int(len(band)),
        **{col: float(band[col].astype("float64").mean())
           for col in ["net_tfa", "e401", "pira", "inc", "age", "marr", "fsize"]},
    }
    summary["abadie_income_band_sds"] = {
        col: float(band[col].astype("float64").std(ddof=1))
        for col in ["net_tfa", "e401", "pira", "inc", "age", "marr", "fsize"]
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")

    METRICS.write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"wrote {OUT}: {len(df)} rows x {df.shape[1]} columns")
    return 0 if metrics["rows_match_expected"] else 1


if __name__ == "__main__":
    sys.exit(main())
