"""Run h4-chr (plan.json analysis_plan step 6): H4, Conley-Hansen-Rossi sensitivity of the
Panel A coefficient on schooling to a direct effect gamma of nearc4 on lwage76 in [0, delta].
A6 primary, A5 alongside. Descriptive; a statement about the Panel A coefficient (which
assumes experience exogenous), never about 'the return'.

AR-based (robust to a weak instrument): for outcome lwage76 - gamma0 nearc4 the H3(a) set
has lambda_hat replaced by lambda_hat - gamma0 (the residuals, so V, are unchanged).
Breakdown delta* = lambda_hat - 1.959964 se_HC1(lambda_hat) (0 if negative), the smallest
delta at which the robust 95% union first includes 0; share = delta* / lambda_hat.
Confirmed on a gamma0 grid over [0, 0.05], step 1e-5 (extended to 0.10 if needed): the
first grid gamma0 whose AR set contains 0 must lie within one step of delta* (failure =
run fails). Union sets over gamma0 in {0, 1e-4, ..., delta}.
Secondary, not robust: the Wald union of beta_hat(gamma0) +- 1.959964 x the HC1 2SLS SE
for outcome lwage76 - gamma0 nearc4, and its breakdown on the same grid.

Input: data/derived/card_analysis.csv.
Outputs: runs/h4-chr/metrics.json; runs/h4-chr/chr_grid.csv with one row per (spec,
delta), delta = 0, 1e-4, ..., 0.02 (includes 0, 0.005, 0.010, 0.015, 0.020): spec (A6/A5),
delta, ar_lo, ar_hi, ar_npieces, wald_lo, wald_hi (an unbounded side as -inf / inf).
Usage: .venv/bin/python code/h4_chr.py
"""
from __future__ import annotations

import csv
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "h4-chr"
DELTAS = (0.0, 0.005, 0.010, 0.015, 0.020)
GRID_DELTAS = np.round(1e-4 * np.arange(201), 10)       # 0 .. 0.02, step 1e-4


def one_column(df, p: str, iv_spec: str, controls: list[str]):
    ar = ivlib.one_instrument_ar(df, controls, robust=True)
    fi = ivlib.fit_spec(df, iv_spec)
    mats = ivlib.iv_one_instrument_matrices(df, controls)
    ivlib.require(abs(mats["beta_y"][0] - fi.coef) < 1e-10, "2SLS matrices != linearmodels")
    beta0, lo0, hi0 = ivlib.chr_wald(mats, np.array([0.0]))
    ivlib.require(ivlib.rel_diff((hi0[0] - lo0[0]) / (2 * ivlib.Z975), fi.se_hc1) < 1e-8,
                  "Wald SE at gamma0 = 0 != linearmodels HC1")
    gam = 0.0123
    shifted = df.assign(lwage76=df["lwage76"] - gam * df["nearc4"])
    fg = ivlib.fit_spec(shifted, iv_spec)
    _, lo_g, hi_g = ivlib.chr_wald(mats, np.array([gam]))
    ivlib.require(ivlib.rel_diff((hi_g[0] - lo_g[0]) / (2 * ivlib.Z975), fg.se_hc1) < 1e-8,
                  "Wald SE at gamma0 = 0.0123 != linearmodels HC1 on the shifted outcome")
    dstar = ivlib.chr_breakdown(ar)
    dgrid = ivlib.chr_breakdown_grid(ar)
    ivlib.require(abs(dgrid - dstar) <= 1e-5 + 1e-12, f"{p}: grid breakdown {dgrid} vs {dstar}")
    wald_b = ivlib.chr_wald_breakdown(mats)
    union = ivlib.chr_union(ar, mats, GRID_DELTAS)
    m = {f"{p}_pacoef_chr_breakdown": dstar, f"{p}_pacoef_chr_breakdown_grid": dgrid,
         f"{p}_pacoef_chr_share": dstar / ar.lam, f"{p}_pacoef_chr_wald_breakdown": wald_b,
         f"{p}_rf": ar.lam, f"{p}_rf_se_hc1": ar.se_lam}
    for row in union:
        d = row["delta"]
        if any(abs(d - x) < 1e-12 for x in DELTAS):
            tag = f"d{int(round(d * 1000)):03d}"
            m[f"{p}_chr_union_{tag}_ar_lo"] = row["ar_union_lo"]
            m[f"{p}_chr_union_{tag}_ar_hi"] = row["ar_union_hi"]
            m[f"{p}_chr_union_{tag}_ar_npieces"] = row["ar_union_npieces"]
            m[f"{p}_chr_union_{tag}_wald_lo"] = row["wald_union_lo"]
            m[f"{p}_chr_union_{tag}_wald_hi"] = row["wald_union_hi"]
    return m, union


def compute(df, out_dir: Path | None = None) -> dict:
    m = {"n_sample": len(df)}
    rows = []
    for p, spec, controls in (("a6", "A6", ivlib.CONTROLS_A6), ("a5", "A5", ivlib.CONTROLS_A5)):
        mm, union = one_column(df, p, spec, controls)
        m.update(mm)
        rows += [(spec, r) for r in union]
    if out_dir is not None:
        with (out_dir / "chr_grid.csv").open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["spec", "delta", "ar_lo", "ar_hi", "ar_npieces", "wald_lo", "wald_hi"])
            for spec, r in rows:
                w.writerow([spec, repr(r["delta"]), repr(float(r["ar_union_lo"])),
                            repr(float(r["ar_union_hi"])), r["ar_union_npieces"],
                            repr(float(r["wald_union_lo"])), repr(float(r["wald_union_hi"]))])
    return m


def main() -> int:
    t0 = time.time()
    out = ivlib.run_dir(RUN)
    m = compute(ivlib.load_analysis(), out)
    ivlib.write_metrics(out / "metrics.json", m)
    print(f"{RUN}: delta* A6 {m['a6_pacoef_chr_breakdown']:.5f}, "
          f"A5 {m['a5_pacoef_chr_breakdown']:.5f}; wall {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
