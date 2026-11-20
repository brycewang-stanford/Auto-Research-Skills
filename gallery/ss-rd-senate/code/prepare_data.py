"""Prepare the Senate RD data for analysis without sample restrictions.

The design gate has not yet fixed a sample restriction, so this step keeps every
row, coerces types, and writes a derived file plus a metrics file that describes
the variables (missingness, ranges, counts). It computes NO statistic of `vote`
by side of the cutoff and NO relationship between the outcome and the running
variable or covariates.

Usage (run through crew.py run --kind data-prep):
    .venv/bin/python code/prepare_data.py runs/prepare-data/metrics.json
"""
import json
import os
import sys

import pandas as pd

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")
DERIVED = os.path.join(WS, "data", "derived", "senate_rd.csv")
EXPECTED_COLUMNS = ["state", "year", "vote", "margin", "class",
                    "termshouse", "termssenate", "population"]
COVARIATES = ["class", "termshouse", "termssenate", "population"]


def main():
    metrics_path = sys.argv[1]
    df = pd.read_csv(RAW)
    if list(df.columns) != EXPECTED_COLUMNS:
        raise SystemExit(f"unexpected columns: {list(df.columns)}")

    for col in ["year", "vote", "margin"] + COVARIATES:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["state"] = df["state"].astype("string").str.strip()

    n_raw = len(df)
    # No sample restriction until the design is approved: nothing is dropped.
    df["vote_observed"] = df["vote"].notna().astype(int)
    n_kept = len(df)

    os.makedirs(os.path.dirname(DERIVED), exist_ok=True)
    df.to_csv(DERIVED, index=False)

    def rng(s):
        return [float(s.min()), float(s.max())] if s.notna().any() else [None, None]

    metrics = {
        "rows_raw": n_raw,
        "rows_kept": n_kept,
        "rows_dropped": n_raw - n_kept,
        "n_vote_observed": int(df["vote_observed"].sum()),
        "missing_vote": int(df["vote"].isna().sum()),
        "missing_margin": int(df["margin"].isna().sum()),
        "missing_year": int(df["year"].isna().sum()),
        "missing_state": int(df["state"].isna().sum()),
        "margin_min": rng(df["margin"])[0],
        "margin_max": rng(df["margin"])[1],
        "margin_rows_negative": int((df["margin"] < 0).sum()),
        "margin_rows_zero": int((df["margin"] == 0).sum()),
        "margin_rows_positive": int((df["margin"] > 0).sum()),
        "year_min": rng(df["year"])[0],
        "year_max": rng(df["year"])[1],
        "n_states": int(df["state"].nunique()),
    }
    for c in COVARIATES:
        lo, hi = rng(df[c])
        metrics[f"missing_{c}"] = int(df[c].isna().sum())
        metrics[f"{c}_min"] = lo
        metrics[f"{c}_max"] = hi

    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
        f.write("\n")
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
