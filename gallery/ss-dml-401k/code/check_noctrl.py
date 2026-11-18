"""check-noctrl (analysis plan 1): OLS of net_tfa on e401 with an intercept and no controls.

Data check only: confirms that the data and outcome are the paper's (Chernozhukov et al. 2018,
p. 43, report $19,559 (SE 1,413) with no controls). Computed on all 9,915 rows (the only sample
for every claim, design.sample_rule) and, as a pre-stated descriptive diagnostic only, on the
9,275-row Abadie (2003) income band 10,000 <= inc <= 200,000. A mismatch is reported as a data
discrepancy; it never changes the sample of any other run.

Writes runs/check-noctrl/metrics.json (flat).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

DATA = Path("data/derived/sipp1991.csv")
OUT = Path("runs/check-noctrl/metrics.json")
PUBLISHED, PUBLISHED_SE = 19559, 1413
N_EXPECTED = 9915


def ols_slope(y: np.ndarray, d: np.ndarray) -> dict:
    """Intercept + one regressor: coefficient on d, HC0 and classical SEs, N."""
    n = len(y)
    X = np.column_stack([np.ones(n), d])
    XtX_inv = np.linalg.inv(X.T @ X)
    b = XtX_inv @ X.T @ y
    e = y - X @ b
    classical = np.sqrt(e @ e / (n - 2) * XtX_inv[1, 1])
    meat = (X * e[:, None] ** 2).T @ X
    hc0 = np.sqrt((XtX_inv @ meat @ XtX_inv)[1, 1])
    return {"coef": float(b[1]), "se_hc0": float(hc0), "se_classical": float(classical), "n": int(n)}


def main() -> None:
    df = pd.read_csv(DATA, usecols=["net_tfa", "e401", "inc"])
    if df.isna().any().any():
        raise SystemExit("ERROR: missing values in net_tfa, e401 or inc; stop and tell the PI")
    full = ols_slope(df.net_tfa.to_numpy(float), df.e401.to_numpy(float))
    band_rows = df[(df.inc >= 10000) & (df.inc <= 200000)]
    band = ols_slope(band_rows.net_tfa.to_numpy(float), band_rows.e401.to_numpy(float))
    m = {f"full_{k}": v for k, v in full.items()}
    m.update({f"band_{k}": v for k, v in band.items()})
    m["published"] = PUBLISHED
    m["published_se"] = PUBLISHED_SE
    m["full_diff"] = full["coef"] - PUBLISHED
    m["full_n_ok"] = full["n"] == N_EXPECTED
    m["full_coef_ok"] = bool(abs(full["coef"] - PUBLISHED) <= 1.0)  # $1 rounding
    m["data_discrepancy"] = not (m["full_n_ok"] and m["full_coef_ok"])
    m["band_diff"] = band["coef"] - PUBLISHED
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(m, indent=2) + "\n")
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
