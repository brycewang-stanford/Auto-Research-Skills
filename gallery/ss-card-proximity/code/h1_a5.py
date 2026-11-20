"""Run h1-a5 (plan.json analysis_plan step 3): Panel A column 5, A1, A3, Table 2 col 2,
and the homoskedastic Anderson-Rubin set for A5.

A5 2SLS (lwage76 on ed76, instrument nearc4, BASE_A), A1 first stage and A3 reduced form
(coefficient on nearc4), Table 2 column 2 OLS; conventional and HC1 SEs. Homoskedastic AR
set for A5: AR(b0) = conventional t^2 of nearc4 in the OLS of lwage76 - b0 ed76 on
nearc4 + BASE_A, accepted iff AR(b0) <= t(0.975, 2994)^2 (Cinelli and Hazlett's degrees of
freedom; secondary target [0.025, 0.285]); the chi-square(1) version is a diagnostic.
Identity: A5 2SLS = A3 / A1 to 1e-10.

Input: data/derived/card_analysis.csv.  Output: runs/h1-a5/metrics.json.
Usage: .venv/bin/python code/h1_a5.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import scipy.stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402
from h1_a6 import panel_a  # noqa: E402

RUN = "h1-a5"


def compute(df) -> dict:
    m = panel_a(df, "A5", "A1", "A3", "a5")
    ols = ivlib.fit_spec(df, "T2C2")
    m.update({"a5_ols": ols.coef, "a5_ols_se": ols.se_conv, "a5_ols_se_hc1": ols.se_hc1,
              "a5_ols_se_conv_n": ols.se_conv_n, "a5_ols_k": ols.k})
    dof = len(df) - 16
    crit_t = float(scipy.stats.t.ppf(0.975, dof) ** 2)
    m["a5_ar_hom_crit"] = crit_t
    for tag, crit in (("", crit_t), ("_chi2", ivlib.CHI2_1_95)):
        ar = ivlib.one_instrument_ar(df, ivlib.CONTROLS_A5, robust=False, crit=crit)
        ivlib.require(abs(ar.lam - m["a5_rf"]) < 1e-10 and abs(ar.pi - m["a5_fs"]) < 1e-10,
                      "AR inputs differ from A3/A1")
        ivlib.require(abs(ar.se_lam - m["a5_rf_se"]) < 1e-10 * max(1, ar.se_lam),
                      "homoskedastic V_ll != conventional SE^2 of A3")
        p = ar.pieces()
        m[f"a5_ar_hom{tag}_lo"] = p[0][0] if p else None
        m[f"a5_ar_hom{tag}_hi"] = p[-1][1] if p else None
        m[f"a5_ar_hom{tag}_shape"] = ivlib.set_shape(p)
        m[f"a5_ar_hom{tag}_npieces"] = len(p)
    return m


def main() -> int:
    t0 = time.time()
    m = compute(ivlib.load_analysis())
    ivlib.write_metrics(ivlib.run_dir(RUN) / "metrics.json", m)
    print(f"{RUN}: A5 2SLS {m['a5_iv']:.4f}; AR set {m['a5_ar_hom_shape']}; "
          f"wall {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
