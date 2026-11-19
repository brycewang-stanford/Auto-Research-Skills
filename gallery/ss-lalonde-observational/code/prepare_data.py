"""Build the outcome-free working file for the NSW-treated vs CPS-1 study.

Reads data/raw/nswre74_treated.txt and data/raw/cps_controls.txt (written by
code/fetch_data.py). Each line has ten whitespace-separated fields in the order the
data page states: treat, age, educ, black, hisp, married, nodegree, RE74, RE75, RE78.

RE78 is set aside before any data-prep run (plan.json design_constraints): this script
splits each line into tokens and converts ONLY the first nine to numbers. The tenth
token (RE78) is never converted, stored, summarised or written. It stays only in
data/raw and is joined back by the first analysis run after the design gate, using
the row key (src, row) written here.

Outputs
- data/derived/analysis_noRE78.csv    16,177 rows: src, row, treat, age, educ, black,
                                      hisp, married, nodegree, re74, re75, u74, u75
- data/derived/covariate_summary.json one-variable summaries of each covariate within
                                      each group (as in Dehejia-Wahba 1999 Table 1);
                                      no between-group contrast, test or model is computed
- data/prepare_metrics.json           flat counts: rows read, kept, dropped and why;
                                      coding checks

No sample restriction is applied: every row of both files is kept.

Run from the workspace root:
    .venv/bin/python -I code/prepare_data.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAW = {
    "nswre74_treated": (Path("data/raw/nswre74_treated.txt"), 185, 1),
    "cps_controls": (Path("data/raw/cps_controls.txt"), 15992, 0),
}
OUT = Path("data/derived/analysis_noRE78.csv")
SUMMARY = Path("data/derived/covariate_summary.json")
METRICS = Path("data/prepare_metrics.json")

FIELDS = ["treat", "age", "educ", "black", "hisp", "married", "nodegree", "re74", "re75"]
N_FIELDS_IN_FILE = 10  # the tenth is RE78 and is not parsed
BINARY = ["treat", "black", "hisp", "married", "nodegree", "u74", "u75"]
COVARIATES = ["age", "educ", "black", "hisp", "married", "nodegree", "re74", "re75", "u74", "u75"]
COLUMNS = ["src", "row"] + FIELDS + ["u74", "u75"]


def read_first_nine(path: Path, src: str) -> pd.DataFrame:
    """Parse fields 1-9 of each non-blank line; field 10 (RE78) is left as raw text and dropped."""
    records = []
    for lineno, line in enumerate(path.read_text(encoding="ascii").splitlines(), start=1):
        if not line.strip():
            continue
        tokens = line.split()
        if len(tokens) != N_FIELDS_IN_FILE:
            raise ValueError(f"{path}:{lineno}: {len(tokens)} fields, expected {N_FIELDS_IN_FILE}")
        records.append([src, lineno] + [float(t) for t in tokens[:9]])
    return pd.DataFrame(records, columns=["src", "row"] + FIELDS)


def describe(s: pd.Series) -> dict:
    s = s.astype("float64")
    return {
        "n": int(s.size),
        "mean": float(s.mean()),
        "sd": float(s.std(ddof=1)),
        "min": float(s.min()),
        "median": float(s.median()),
        "max": float(s.max()),
        "share_zero": float((s == 0).mean()),
    }


def main() -> int:
    metrics: dict = {}
    frames = []
    ok = True
    for src, (path, expected_rows, treat_value) in RAW.items():
        df = read_first_nine(path, src)
        metrics[f"rows_read_{src}"] = int(len(df))
        metrics[f"rows_expected_{src}"] = expected_rows
        metrics[f"rows_match_{src}"] = bool(len(df) == expected_rows)
        metrics[f"treat_constant_{src}"] = bool((df["treat"] == treat_value).all())
        ok = ok and metrics[f"rows_match_{src}"] and metrics[f"treat_constant_{src}"]
        frames.append(df)
    data = pd.concat(frames, ignore_index=True)

    # Coding checks on single variables (no relation to any outcome).
    for col in FIELDS:
        metrics[f"missing_{col}"] = int(data[col].isna().sum())
    for col in ["age", "educ"]:
        metrics[f"nonintegral_{col}"] = int((data[col] != np.round(data[col])).sum())
    for col in ["re74", "re75"]:
        metrics[f"negative_{col}"] = int((data[col] < 0).sum())
        # Mass at the file maximum within each source (CPS earnings are SSA records,
        # top-coded at the Social Security maximum; lalonde1986 fn).
        for src, grp in data.groupby("src", sort=False):
            metrics[f"max_{col}_{src}"] = float(grp[col].max())
            metrics[f"count_at_max_{col}_{src}"] = int((grp[col] == grp[col].max()).sum())

    # Integer-valued fields are stored as integers.
    for col in ["treat", "age", "educ", "black", "hisp", "married", "nodegree"]:
        data[col] = data[col].round().astype("int64")
    # Zero-earnings ("unemployed") indicators, as in Dehejia and Wahba (1999).
    data["u74"] = (data["re74"] == 0).astype("int64")
    data["u75"] = (data["re75"] == 0).astype("int64")

    for col in BINARY:
        metrics[f"nonbinary_{col}"] = int((~data[col].isin([0, 1])).sum())
    metrics["count_black_and_hisp"] = int(((data["black"] == 1) & (data["hisp"] == 1)).sum())
    metrics["count_nodegree_ne_educ_lt_12"] = int((data["nodegree"] != (data["educ"] < 12)).sum())
    metrics["duplicate_covariate_rows_within_src"] = int(
        data.duplicated(subset=["src"] + FIELDS[1:], keep="first").sum())

    data = data[COLUMNS]
    metrics["rows_kept"] = int(len(data))
    metrics["rows_dropped"] = 0
    metrics["rows_kept_treat_1"] = int((data["treat"] == 1).sum())
    metrics["rows_kept_treat_0"] = int((data["treat"] == 0).sum())
    metrics["columns_written"] = ",".join(COLUMNS)
    metrics["re78_written"] = "re78" in data.columns

    OUT.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(OUT, index=False, float_format="%.10g")

    # Per-group, per-variable summaries (descriptive Table 1; no contrasts).
    summary = {src: {col: describe(grp[col]) for col in COVARIATES}
               for src, grp in data.groupby("src", sort=False)}
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n")

    METRICS.write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"wrote {OUT}: {len(data)} rows x {data.shape[1]} columns")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
