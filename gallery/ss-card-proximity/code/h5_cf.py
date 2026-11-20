"""Run h5-cf (plan.json analysis_plan step 7): H5, the Panel A 2SLS against the OLS
coefficient on schooling. A6 (vs Table 2 col 5) primary, A5 (vs Table 2 col 2) alongside.
Claim texts compare the Panel A 2SLS and OLS coefficients, never 'the returns'.

Test: v_hat = residual of A2 (A1); OLS of lwage76 on ed76 + controls + v_hat with HC1;
reject equality iff |rho_hat / se_HC1(rho_hat)| > 1.959964 (two-sided 5%; valid under its
null rho = 0); normal p-value.
Interval (labelled 'Wald, not robust to a weak instrument'): D = beta_2SLS - beta_OLS,
Var(D) = n/(n-k) sum_i (psi_IV,i - psi_OLS,i)^2 with the stacked influence functions of
design.method (k = 30 for A6, 16 for A5), D +- 1.959964 sqrt(Var(D)).
Checks (failure = run fails): n/(n-k) sum psi^2 of each estimator alone = its HC1 variance
(linearmodels / statsmodels) to 1e-8 relative; D = -rho_hat g as an identity (g = the ed76
coefficient in an OLS of v_hat on ed76 + controls); the control-function coefficient on
ed76 = the 2SLS coefficient.
Also: whether the OLS estimate lies inside the H3(a) robust AR set (descriptive), and the
conventional Hausman t = D / sqrt(se_conv_IV^2 - se_conv_OLS^2) (Card fn 17).

Input: data/derived/card_analysis.csv.  Output: runs/h5-cf/metrics.json.
Usage: .venv/bin/python code/h5_cf.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "h5-cf"


def one_column(df, p: str, controls: list[str]) -> dict:
    r = ivlib.h5_control_function(df, controls)
    ar = ivlib.one_instrument_ar(df, controls, robust=True)
    pieces = ar.pieces()
    return {f"{p}_pacoef_cf_rho": r["rho"], f"{p}_pacoef_cf_rho_se": r["rho_se"],
            f"{p}_pacoef_cf_t": r["cf_t"], f"{p}_pacoef_cf_p": r["cf_p"],
            f"{p}_pacoef_cf_reject": r["cf_reject"], f"{p}_pacoef_iv": r["iv"],
            f"{p}_pacoef_ols": r["ols"], f"{p}_pacoef_diff": r["diff"],
            f"{p}_pacoef_diff_se": r["diff_se"], f"{p}_pacoef_diff_lo": r["diff_lo"],
            f"{p}_pacoef_diff_hi": r["diff_hi"],
            f"{p}_pacoef_hausman_t_conv": r["hausman_t_conv"],
            f"{p}_ols_in_pacoef_ar": int(ivlib.in_set(r["ols"], pieces)),
            f"{p}_pacoef_ar_pieces": ivlib.pieces_str(pieces)}


def compute(df) -> dict:
    m = {"n_sample": len(df)}
    m.update(one_column(df, "a6", ivlib.CONTROLS_A6))
    m.update(one_column(df, "a5", ivlib.CONTROLS_A5))
    return m


def main() -> int:
    t0 = time.time()
    m = compute(ivlib.load_analysis())
    ivlib.write_metrics(ivlib.run_dir(RUN) / "metrics.json", m)
    print(f"{RUN}: A6 CF t {m['a6_pacoef_cf_t']:.3f}; A5 CF t {m['a5_pacoef_cf_t']:.3f}; "
          f"wall {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
