"""Fix the H1b equivalence margin and the precision proxy before the design gate.

Reads data/derived/covariates.csv, which contains no outcome, and uses only the
treatment indicator and re75 (plan.json, hypothesis H1b):

  M               = 0.10 x mean(re75 | treat = 1)
  precision_proxy = sqrt(var_t(re75) / n_t + var_c(re75) / n_c), sample variances (ddof=1):
                    the standard error a difference in means would have if the outcome
                    had re75's variance in each group.
  m_over_proxy    = M / precision_proxy, a rough guide to whether H1b is testable
                    (TOST at 5% needs the 90% interval, about +/- 1.645 SE, inside +/- M).

Earnings are in the file's nominal units (the brief states no price year).

Run from the workspace root:
    .venv/bin/python -I code/margin.py
"""

import json
import math
import sys
from pathlib import Path

import pandas as pd

IN = Path("data/derived/covariates.csv")
METRICS = Path("data/derived/margin_metrics.json")
MARGIN_SHARE = 0.10


def main() -> int:
    df = pd.read_csv(IN, usecols=["treat", "re75"])
    t = df.loc[df["treat"] == 1, "re75"]
    c = df.loc[df["treat"] == 0, "re75"]
    margin = MARGIN_SHARE * float(t.mean())
    proxy = math.sqrt(t.var(ddof=1) / len(t) + c.var(ddof=1) / len(c))
    m = {
        "margin_share": MARGIN_SHARE,
        "re75_mean_treated": float(t.mean()),
        "margin_M": margin,
        "n_treated": int(len(t)),
        "n_control": int(len(c)),
        "re75_var_treated": float(t.var(ddof=1)),
        "re75_var_control": float(c.var(ddof=1)),
        "precision_proxy_se": proxy,
        "m_over_proxy": margin / proxy,
        "tost_halfwidth_proxy_90": 1.6448536269514722 * proxy,
    }
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(m, indent=2) + "\n")
    print(f"M = {margin:.2f}; precision proxy SE = {proxy:.2f}; M/SE = {margin / proxy:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
