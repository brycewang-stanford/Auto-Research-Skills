"""Run diag-panelb (plan.json design.deviations D4; task e-diag-panelb): POST HOC,
report-only diagnosis of the H1 misses in Card's Panel B columns 1-4.

Hypothesis: Card estimated the Panel B first-stage and reduced-form columns with exp76 and
exp762 kept in the equation as endogenous regressors instrumented by age76 and age762,
with nearc4 and the controls exogenous. Under it, each column is a just-identified 2SLS:

  B1*: ed76    ~ nearc4 + exp76 + exp762 + BASE_B,      exp76, exp762 instrumented by
  B2*: ed76    ~ nearc4 + exp76 + exp762 + BASE_B + FB  age76, age762 (k = 16 / 30)
  B3*: lwage76 ~ nearc4 + exp76 + exp762 + BASE_B
  B4*: lwage76 ~ nearc4 + exp76 + exp762 + BASE_B + FB

estimated with linearmodels IV2SLS (debiased=True) through ivlib.fit_2sls, conventional
(sigma^2 = sum(e^2)/(n-k)) and HC1 standard errors. For each column the coefficient on
nearc4 and its conventional SE are compared with Card's printed values (WP 4483 Table 3
Panel B, sources/notes.md sec. 1) by the H1 rounding rule: reproduced iff
|replicated - published| < 0.5 x 10^-3.

Identity checks (failure = run fails): B4* / B2* equals the B6 2SLS coefficient on ed76,
and B3* / B1* equals the B5 2SLS coefficient, to 1e-10 relative. Both hold exactly in
these just-identified models: with beta = lambda/pi and g = c - beta a (a, c the exp
coefficients of the education and wage equations), the B6 moment conditions
Z'(y - beta ed - W g - X d) = Z'(wage residual) - beta Z'(education residual) = 0.

This run changes no H1 target, verdict count or claim of the approved plan (D4). Its
results are reported as a post hoc diagnosis of the B1-B4 misses.

Input: data/derived/card_analysis.csv.  Output: runs/diag-panelb/metrics.json.
Usage (workspace root): .venv/bin/python code/diag_panelb.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "diag-panelb"

# column: (dependent, family background?, published coefficient, published SE, k)
COLUMNS = {
    "b1": ("ed76", False, 0.382, 0.114, 16),
    "b2": ("ed76", True, 0.365, 0.105, 30),
    "b3": ("lwage76", False, 0.047, 0.019, 16),
    "b4": ("lwage76", True, 0.048, 0.019, 30),
}


def reproduced(value: float, published: float, decimals: int = 3) -> int:
    """H1 rounding rule (design.method): |replicated - published| < 0.5 x 10^-d."""
    return int(abs(float(value) - published) < 0.5 * 10 ** -decimals)


def compute(df) -> dict:
    m: dict = {"n_sample": len(df)}
    fits = {}
    for col, (dep, fb, pub, pub_se, k) in COLUMNS.items():
        exog = ["nearc4"] + ivlib.BASE_B + (ivlib.FB if fb else [])
        f = ivlib.fit_2sls(df, dep, exog, ivlib.EXP, ivlib.AGE, "nearc4", f"{col}*")
        ivlib.require(f.k == k, f"{col}*: k = {f.k}, expected {k}")
        ivlib.require(f.n == len(df), f"{col}*: n = {f.n}")
        fits[col] = f
        p = f"diag_{col}"
        m.update({p: f.coef, f"{p}_se": f.se_conv, f"{p}_se_hc1": f.se_hc1, f"{p}_k": f.k,
                  f"{p}_pub": pub, f"{p}_se_pub": pub_se,
                  f"{p}_reproduced": reproduced(f.coef, pub),
                  f"{p}_se_reproduced": reproduced(f.se_conv, pub_se)})
    b6, b5 = ivlib.fit_spec(df, "B6"), ivlib.fit_spec(df, "B5")
    for num, den, iv, tag in (("b4", "b2", b6, "b6"), ("b3", "b1", b5, "b5")):
        ratio = fits[num].coef / fits[den].coef
        m[f"diag_{num}_over_{den}"] = ratio
        m[f"diag_{tag}_2sls"] = iv.coef
        m[f"diag_{num}_over_{den}_minus_{tag}"] = ratio - iv.coef
        ivlib.require(abs(ratio - iv.coef) <= 1e-10 * max(1.0, abs(iv.coef)),
                      f"{num}*/{den}* = {ratio} != {tag.upper()} 2SLS {iv.coef}")
    m["diag_targets_reproduced"] = sum(m[f"diag_{c}_reproduced"] + m[f"diag_{c}_se_reproduced"]
                                       for c in COLUMNS)
    m["diag_targets"] = 2 * len(COLUMNS)
    return m


def main() -> int:
    t0 = time.time()
    m = compute(ivlib.load_analysis())
    ivlib.write_metrics(ivlib.run_dir(RUN) / "metrics.json", m)
    print(f"{RUN}: B2* {m['diag_b2']:.4f} ({m['diag_b2_se']:.4f}), "
          f"B4* {m['diag_b4']:.4f} ({m['diag_b4_se']:.4f}); "
          f"{m['diag_targets_reproduced']}/{m['diag_targets']} printed numbers reproduced; "
          f"wall {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
