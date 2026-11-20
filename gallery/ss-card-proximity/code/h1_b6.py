"""Run h1-b6 (plan.json analysis_plan step 1): PRIMARY H1 targets, Card's basic specification.

Panel B column 6 2SLS (ed76, exp76, exp762 endogenous; nearc4, age76, age762 excluded
instruments; BASE_B + FB), its first stage B2 and reduced form B4 (coefficient on nearc4),
Table 2 column 5 OLS, N; and Panel B columns 1, 3 and 5 (secondary targets). Conventional
(n - k) SEs are the H1 comparison; HC1 SEs and the sum(e^2)/n diagnostic are written
alongside. Seed claims: iv-return = beta_iv, iv-return-se = se_iv_conv,
first-stage = fs_nearc4, ols-return = ols_beta.

Input: data/derived/card_analysis.csv.  Output: runs/h1-b6/metrics.json.
Usage (workspace root): .venv/bin/python code/h1_b6.py
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "h1-b6"


def fit_metrics(f: ivlib.Fit, p: str) -> dict:
    return {p: f.coef, f"{p}_se": f.se_conv, f"{p}_se_hc1": f.se_hc1,
            f"{p}_se_conv_n": f.se_conv_n, f"{p}_k": f.k, f"{p}_n": f.n}


def compute(df) -> dict:
    b6, b2, b4, t25 = (ivlib.fit_spec(df, s) for s in ("B6", "B2", "B4", "T2C5"))
    b5, b1, b3 = (ivlib.fit_spec(df, s) for s in ("B5", "B1", "B3"))
    for f in (b6, b2, b4, t25, b5, b1, b3):
        ivlib.require(f.n == len(df), f"{f.name}: n = {f.n}")
    m = {"n_sample": len(df),
         # seed claims and the primary targets
         "beta_iv": b6.coef, "se_iv_conv": b6.se_conv, "se_iv_hc1": b6.se_hc1,
         "se_iv_conv_n": b6.se_conv_n,
         "iv_return_pct": 100.0 * (math.exp(b6.coef) - 1.0),
         "fs_nearc4": b2.coef, "fs_nearc4_se": b2.se_conv, "fs_nearc4_se_hc1": b2.se_hc1,
         "fs_nearc4_se_conv_n": b2.se_conv_n,
         "rf_nearc4": b4.coef, "rf_nearc4_se": b4.se_conv, "rf_nearc4_se_hc1": b4.se_hc1,
         "rf_nearc4_se_conv_n": b4.se_conv_n,
         "ols_beta": t25.coef, "ols_se": t25.se_conv, "ols_se_hc1": t25.se_hc1,
         "ols_se_conv_n": t25.se_conv_n,
         "b6_g_exp76": float(b6.params["exp76"]), "b6_g_exp762": float(b6.params["exp762"])}
    m.update(fit_metrics(b5, "b5_iv"))
    m.update(fit_metrics(b1, "b1_fs"))
    m.update(fit_metrics(b3, "b3_rf"))
    return m


def main() -> int:
    t0 = time.time()
    df = ivlib.load_analysis()
    m = compute(df)
    ivlib.write_metrics(ivlib.run_dir(RUN) / "metrics.json", m)
    print(f"{RUN}: B6 2SLS {m['beta_iv']:.4f} ({m['se_iv_conv']:.4f}); "
          f"wall time {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
