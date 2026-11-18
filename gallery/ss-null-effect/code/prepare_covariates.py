"""Write the outcome-free covariate file and covariate balance by treatment group.

OUTCOMES ARE SEALED until the design gate. This script reads the header row, then loads
ONLY id, the treatment indicator and the eleven pre-program covariates fixed in
plan.json (pandas usecols), so no outcome or survey value is ever parsed. The other
columns are checked by name only.

Outputs
  data/derived/covariates.csv    id, treat, the eleven covariates
  data/derived/prep_metrics.json rows, treated count/share, and per covariate the mean
                                 and SD in each group and the standardized difference
                                 (mean_t - mean_c) / sqrt((var_t + var_c) / 2), ddof=1.
                                 region is categorical: one share per level.

Run from the workspace root:
    .venv/bin/python -I code/prepare_covariates.py
"""

import csv
import json
import math
import sys
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/null_extract.csv")
OUT = Path("data/derived/covariates.csv")
METRICS = Path("data/derived/prep_metrics.json")

TREAT = "treat"  # the enrolment indicator (round-1 question review, F5)
COVARIATES = ["age", "educ", "married", "urban", "region", "children", "health_limit",
              "re74", "re75", "unemp74", "unemp75"]
SEALED = ["re78", "re79", "employed78", "hours78", "benefits78", "wellbeing78"] + \
    [f"survey_q{i:02d}" for i in range(1, 21)]
EXPECTED_ROWS = 4000  # task.json brief: "an administrative extract for 4,000 working-age adults"


def std_diff(t: pd.Series, c: pd.Series) -> float:
    pooled = math.sqrt((t.var(ddof=1) + c.var(ddof=1)) / 2)
    return float((t.mean() - c.mean()) / pooled) if pooled > 0 else 0.0


def main() -> int:
    with RAW.open(newline="") as fh:
        header = next(csv.reader(fh))
    keep = ["id", TREAT] + COVARIATES
    missing = [c for c in keep if c not in header]
    if missing:
        print(f"Header lacks {missing}; header is {header}", file=sys.stderr)
        return 1
    unexpected = [c for c in header if c not in keep + SEALED]
    absent_sealed = [c for c in SEALED if c not in header]

    df = pd.read_csv(RAW, usecols=keep)[keep]  # never parses a sealed column
    if set(df[TREAT].unique()) - {0, 1}:
        print(f"{TREAT} is not 0/1", file=sys.stderr)
        return 1
    if not df["id"].is_unique:
        print("id is not unique", file=sys.stderr)
        return 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)

    t, c = df[df[TREAT] == 1], df[df[TREAT] == 0]
    m: dict = {
        "treatment_column": TREAT,
        "header_n_columns": len(header),
        "header_unexpected_columns": ",".join(unexpected),
        "header_absent_sealed_columns": ",".join(absent_sealed),
        "rows": int(len(df)),
        "rows_match_brief": bool(len(df) == EXPECTED_ROWS),
        "n_treated": int(len(t)),
        "n_control": int(len(c)),
        "share_treated": float(len(t) / len(df)),
        "missing_values_kept_columns": int(df.isna().sum().sum()),
    }

    # are the unemployment indicators exactly "zero earnings that year"?
    for year in ("74", "75"):
        m[f"unemp{year}_ne_re{year}_zero_rows"] = int(
            ((df[f"re{year}"] == 0).astype(int) != df[f"unemp{year}"]).sum())

    numeric = [v for v in COVARIATES if v != "region"]
    columns: dict[str, tuple[pd.Series, pd.Series]] = {v: (t[v], c[v]) for v in numeric}
    for level in sorted(df["region"].unique()):
        columns[f"region_{level}"] = ((t["region"] == level).astype(float),
                                      (c["region"] == level).astype(float))
    # descriptive: zero earnings in a pre-program year (covariates only)
    for v in ("re74", "re75"):
        columns[f"{v}_zero"] = ((t[v] == 0).astype(float), (c[v] == 0).astype(float))

    largest_name, largest = "", 0.0
    for name, (ts, cs) in columns.items():
        d = std_diff(ts, cs)
        m[f"{name}_mean_t"] = float(ts.mean())
        m[f"{name}_mean_c"] = float(cs.mean())
        m[f"{name}_sd_t"] = float(ts.std(ddof=1))
        m[f"{name}_sd_c"] = float(cs.std(ddof=1))
        m[f"{name}_std_diff"] = d
        if abs(d) > abs(largest):
            largest_name, largest = name, d
    m["largest_abs_std_diff_variable"] = largest_name
    m["largest_abs_std_diff"] = largest

    METRICS.write_text(json.dumps(m, indent=2) + "\n")
    print(f"wrote {OUT}: {len(df)} rows, {len(t)} treated, {len(c)} control; "
          f"largest |std diff| {largest_name} = {largest:.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
