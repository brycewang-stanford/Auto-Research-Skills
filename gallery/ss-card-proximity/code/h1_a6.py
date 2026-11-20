"""Run h1-a6 (plan.json analysis_plan step 2): Panel A column 6 and columns 2 and 4.

Panel A (experience exogenous) with family background: A6 2SLS of lwage76 on ed76
(instrument nearc4) + BASE_A + FB, A2 first stage and A4 reduced form (coefficient on
nearc4); conventional (n - k) and HC1 SEs. Identity check (failure = run fails): the A6
2SLS coefficient equals A4 / A2 to 1e-10.

Input: data/derived/card_analysis.csv.  Output: runs/h1-a6/metrics.json.
Usage: .venv/bin/python code/h1_a6.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "h1-a6"


def panel_a(df, iv: str, fs: str, rf: str, p: str) -> dict:
    fi, ff, fr = ivlib.fit_spec(df, iv), ivlib.fit_spec(df, fs), ivlib.fit_spec(df, rf)
    ratio = fr.coef / ff.coef
    ivlib.require(abs(fi.coef - ratio) <= 1e-10, f"{iv} 2SLS != {rf}/{fs}")
    m = {}
    for f, tag in ((fi, "iv"), (ff, "fs"), (fr, "rf")):
        ivlib.require(f.n == len(df), f"{f.name}: n = {f.n}")
        m.update({f"{p}_{tag}": f.coef, f"{p}_{tag}_se": f.se_conv,
                  f"{p}_{tag}_se_hc1": f.se_hc1, f"{p}_{tag}_se_conv_n": f.se_conv_n,
                  f"{p}_{tag}_k": f.k})
    m[f"{p}_iv_minus_ratio"] = fi.coef - ratio
    m[f"{p}_n"] = fi.n
    return m


def compute(df) -> dict:
    return panel_a(df, "A6", "A2", "A4", "a6")


def main() -> int:
    t0 = time.time()
    m = compute(ivlib.load_analysis())
    ivlib.write_metrics(ivlib.run_dir(RUN) / "metrics.json", m)
    print(f"{RUN}: A6 2SLS {m['a6_iv']:.4f} ({m['a6_iv_se']:.4f}); wall {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
