"""Run select-re75 (descriptive, not a test): AIPW ATT of treat on re75 given X-.

X- = (age, educ, married, urban, region, children, health_limit, re74, unemp74): the
primary estimator (code/aipw_lib.py) with B(X-) (14 terms) and T(X-) (12 columns), the
propensity refitted on B(X-), same folds, repetitions and seeds. re75 is a covariate, so no
outcome is read. It measures selection on the 1975 earnings shock given 1974 earnings and is
not evidence for or against the identifying assumption; no p-value is reported or used.

Run from the workspace root:  .venv/bin/python -I code/select_re75.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/select-re75/metrics.json")
X_MINUS = ["age", "educ", "married", "urban", "region", "children", "health_limit", "re74", "unemp74"]


def main() -> int:
    df = L.load_data([])
    M = float(L.read_json(L.MARGIN_FILE)["margin_M"])
    d = df["treat"].to_numpy(int)
    y = df["re75"].to_numpy(float)
    Xb = L.basis(df, X_MINUS).to_numpy(float)
    Xt = L.tree_features(df, X_MINUS)
    res = L.aipw(d, y, Xb, Xt)
    met = {"outcome": "re75 (pre-program; descriptive)", "conditioning_set": ",".join(X_MINUS),
           "basis_n_terms": int(Xb.shape[1]), "tree_n_columns": int(Xt.shape[1]),
           "margin_M": M, "seed_base": L.SEED}
    s = L.summarize(res, "")
    for key in ("effect", "se", "ci_low", "ci_high", "n", "n_treated", "n_clipped_units"):
        met[key] = s[key]
    met["effect_over_M"] = res["theta"] / M
    met["effect_abs"] = abs(res["theta"])
    met["direction"] = "lower" if res["theta"] < 0 else "higher"
    L.write_metrics(OUT, met)
    print(met)
    return 0


if __name__ == "__main__":
    sys.exit(main())
