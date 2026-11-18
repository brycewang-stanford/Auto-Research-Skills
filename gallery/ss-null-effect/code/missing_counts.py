"""Count missing outcome values by treatment arm (design: run missing-counts).

PI ruling on design-r1 F4; plan.json method.missing_outcomes. Reads data/raw/null_extract.csv
with usecols = treat + the six outcomes, every outcome column as text (dtype=str), so no
outcome value is converted to a number or summarized. For each outcome k it records
only missingness:

  missing_<k>_treated, missing_<k>_control            counts of missing values
  missing_<k>_share_treated, missing_<k>_share_control shares of the arm
  missing_<k>_share_diff                               share treated - share control
  nonnumeric_<k>                                       non-missing entries that are not
                                                       numbers (format check: a count only)
  ipow_trigger_<k>                                     |share_diff| > 0.02 (rob-ipow runs)

survey_q01-survey_q20 are not read.

Run from the workspace root:
    .venv/bin/python -I code/missing_counts.py
"""

import json
import sys
from pathlib import Path

import pandas as pd

RAW = Path("data/raw/null_extract.csv")
METRICS = Path("data/derived/missing_counts.json")
TREAT = "treat"
OUTCOMES = ["re78", "re79", "employed78", "hours78", "benefits78", "wellbeing78"]
TRIGGER = 0.02  # plan.json method.missing_outcomes


def main() -> int:
    df = pd.read_csv(RAW, usecols=[TREAT] + OUTCOMES,
                     dtype={k: str for k in OUTCOMES} | {TREAT: int})
    treated = df[TREAT] == 1
    n_t, n_c = int(treated.sum()), int((~treated).sum())
    m: dict = {"rows": int(len(df)), "n_treated": n_t, "n_control": n_c,
               "trigger_threshold": TRIGGER}
    triggered = []
    for k in OUTCOMES:
        miss = df[k].isna()
        nonnumeric = int((pd.to_numeric(df[k], errors="coerce").isna() & ~miss).sum())
        mt, mc = int(miss[treated].sum()), int(miss[~treated].sum())
        st, sc = mt / n_t, mc / n_c
        m[f"missing_{k}_treated"] = mt
        m[f"missing_{k}_control"] = mc
        m[f"missing_{k}_share_treated"] = st
        m[f"missing_{k}_share_control"] = sc
        m[f"missing_{k}_share_diff"] = st - sc
        m[f"nonnumeric_{k}"] = nonnumeric
        m[f"ipow_trigger_{k}"] = bool(abs(st - sc) > TRIGGER)
        if abs(st - sc) > TRIGGER:
            triggered.append(k)
    m["ipow_triggered_outcomes"] = ",".join(triggered)
    m["ipow_any_trigger"] = bool(triggered)

    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(m, indent=2) + "\n")
    print(f"wrote {METRICS}; rob-ipow triggered for: {', '.join(triggered) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
