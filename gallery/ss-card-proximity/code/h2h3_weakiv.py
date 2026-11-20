"""Run h2h3-weakiv (plan.json analysis_plan step 4): H2 and H3(a), Panel A col 6 primary,
col 5 alongside. All statements concern the Panel A coefficient on schooling.

H2: F_conv = (pi_hat / se_conv)^2 and F_eff = (pi_hat / se_HC1)^2 of nearc4 in A2 (A1),
flags F_conv > 16.38 (Stock-Yogo 10% maximal size) and F_eff > 23.11 (Montiel
Olea-Pflueger, 5% size, 10% worst-case bias; with one instrument F_eff is the HC1 F).
H3(a): robust AR(b0) = (lambda - b0 pi)^2 / (V_ll - 2 b0 V_lp + b0^2 V_pp), lambda and pi
the nearc4 coefficients of A4 and A2 (A3 and A1), V their joint HC1 covariance; set
{b0 : AR(b0) <= 3.841459} solved from the quadratic. Checks (failure = run fails):
AR(0) = squared robust reduced-form t to 1e-10; the closed form agrees with a grid
(b0 in [-1, 1], step 1e-4) on which AR(b0) is recomputed as the HC1 t^2 of nearc4 in the
OLS of lwage76 - b0 ed76 on nearc4 + controls (no acceptance disagreement beyond one grid
step). Flag {p}_pacoef_positive: the set is one bounded interval above 0 (decides only
'the Panel A coefficient on schooling is positive'). An unbounded side is written as null
with the shape string.

Input: data/derived/card_analysis.csv.  Output: runs/h2h3-weakiv/metrics.json.
Usage: .venv/bin/python code/h2h3_weakiv.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "h2h3-weakiv"


def one_column(df, p: str, fs_spec: str, rf_spec: str, controls: list[str]) -> dict:
    fs, rf = ivlib.fit_spec(df, fs_spec), ivlib.fit_spec(df, rf_spec)
    m = {f"{p}_f_conv": (fs.coef / fs.se_conv) ** 2, f"{p}_f_eff": (fs.coef / fs.se_hc1) ** 2}
    m[f"{p}_f_conv_above_sy"] = int(m[f"{p}_f_conv"] > ivlib.SY_10PCT)
    m[f"{p}_f_eff_above_mop"] = int(m[f"{p}_f_eff"] > ivlib.MOP_5PCT_10PCT)
    ar = ivlib.one_instrument_ar(df, controls, robust=True)
    ivlib.require(abs(ar.lam - rf.coef) < 1e-10 and abs(ar.pi - fs.coef) < 1e-10,
                  "AR inputs differ from the reduced form / first stage")
    ivlib.require(ivlib.rel_diff(ar.se_lam, rf.se_hc1) < 1e-10, "V_ll != HC1 var of RF")
    ivlib.require(ivlib.rel_diff(ar.se_pi, fs.se_hc1) < 1e-10, "V_pp != HC1 var of FS")
    t_rf = rf.coef / rf.se_hc1
    ar0 = float(ar.stat(0.0))
    ivlib.require(abs(ar0 - t_rf ** 2) <= 1e-10 * max(1.0, t_rf ** 2), "AR(0) != robust RF t^2")
    pieces = ar.pieces()
    chk = ivlib.ar_grid_check(df, controls, ar)
    ivlib.require(chk["mismatch_beyond_one_step"] == 0,
                  f"{p}: closed-form AR set disagrees with the grid beyond one step")
    m.update({
        f"{p}_ar_lo": pieces[0][0] if pieces else None,
        f"{p}_ar_hi": pieces[-1][1] if pieces else None,
        f"{p}_ar_shape": ivlib.set_shape(pieces), f"{p}_ar_npieces": len(pieces),
        f"{p}_ar_pieces": ivlib.pieces_str(pieces),
        f"{p}_ar_contains_0": int(ivlib.in_set(0.0, pieces)),
        f"{p}_pacoef_positive": ivlib.positive_bounded(pieces),
        f"{p}_rf_t_robust": t_rf, f"{p}_ar0": ar0,
        f"{p}_ar_grid_points": chk["grid_points"],
        f"{p}_ar_grid_max_rel_diff": chk["max_rel_diff"],
        f"{p}_ar_grid_mismatch": chk["mismatch_beyond_one_step"],
        f"{p}_lam": ar.lam, f"{p}_pi": ar.pi, f"{p}_V_ll": ar.V[0, 0],
        f"{p}_V_lp": ar.V[0, 1], f"{p}_V_pp": ar.V[1, 1],
    })
    return m


def compute(df) -> dict:
    m = {"n_sample": len(df)}
    m.update(one_column(df, "a6", "A2", "A4", ivlib.CONTROLS_A6))
    m.update(one_column(df, "a5", "A1", "A3", ivlib.CONTROLS_A5))
    return m


def main() -> int:
    t0 = time.time()
    m = compute(ivlib.load_analysis())
    ivlib.write_metrics(ivlib.run_dir(RUN) / "metrics.json", m)
    print(f"{RUN}: A6 AR {m['a6_ar_pieces']}; A5 AR {m['a5_ar_pieces']}; "
          f"wall {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
