"""Run r-age1419 (plan.json analysis_plan step 8; report only): Card Table 4 row 7.

The basic specification (Panel B col 6 2SLS and Table 2 col 5 OLS) on men aged 14-19 in
1966, i.e. age76 in 24..29; compared with the published 0.094 (0.064), OLS 0.076 (0.006),
N 2037. A different N is reported; no other age rule is tried. Conventional (n - k) SEs as
in H1, HC1 alongside. Nothing here changes a specification or claim.

Input: data/derived/card_analysis.csv.  Output: runs/r-age1419/metrics.json.
Usage: .venv/bin/python code/r_age1419.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "r-age1419"


def compute(df) -> dict:
    young = df[(df["age76"] >= 24) & (df["age76"] <= 29)]
    iv = ivlib.fit_spec(young, "B6")
    ols = ivlib.fit_spec(young, "T2C5")
    return {"young_n": len(young), "young_iv": iv.coef, "young_iv_se": iv.se_conv,
            "young_iv_se_hc1": iv.se_hc1, "young_ols": ols.coef, "young_ols_se": ols.se_conv,
            "young_ols_se_hc1": ols.se_hc1,
            "young_iv_lo": iv.coef - ivlib.Z975 * iv.se_conv,
            "young_iv_hi": iv.coef + ivlib.Z975 * iv.se_conv}


def main() -> int:
    t0 = time.time()
    m = compute(ivlib.load_analysis())
    ivlib.write_metrics(ivlib.run_dir(RUN) / "metrics.json", m)
    print(f"{RUN}: N {m['young_n']}, IV {m['young_iv']:.4f} ({m['young_iv_se']:.4f}); "
          f"wall {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
