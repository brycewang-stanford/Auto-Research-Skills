"""Run event-path (analysis_plan 16; report-only, for the figure).

Inputs  data/derived/state_panel.csv, runs/select/metrics.json, runs/level-mde/metrics.json
Output  runs/event-path/metrics.json, runs/event-path/event_path.csv

Quarterly California-minus-counterfactual gaps 2014Q1-2026Q1 for the selected candidate, on its
employment outcome (E or P) and on W, with the real-B fit (base 2023Q3; SC w and SDID omega and
pooled-window lambda fitted as in h2-emp / h1-wage; the DDT trend over 2022Q1-2023Q3):
  DD    g_t - g_B
  DDT   g_t - g_B - b (t - B)
  SC    (y_t - ybar_F) - sum_j w_j (Y_jt - Ybar_jF)
  SDID  (y_t - lambda'y_F) - sum_j omega_j (Y_jt - lambda'Y_jF)
Pointwise bands: the gap's own placebo SE = max(SE_s, SE_n) at each quarter and the selected
candidate's H2 critical values (L quantile; t at nu). COVID quarters, AB 257 (2022Q3) and AB 1228
(2023Q4) are flagged for the figure. Which reading the 2022Q1-2023Q3 gaps admit depends on the
estimator (design-r2 D11), recorded as 'figure_case'.
"""
import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
# code/select.py shadows the standard-library module 'select'; load the standard one first.
sys.path[:] = [p for p in sys.path if str(Path(p or ".").resolve()) != _HERE]
import select  # noqa: E402,F401  (standard library)
sys.path.insert(0, _HERE)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import sclib as S  # noqa: E402

OUT_DIR = Path("runs/event-path")
CASE_NOTE = {
    "DD": "2022Q1-2023Q3 gaps are out of fit: a visible check of falsification (ii)",
    "DDT": "2022Q1-2023Q3 gaps are residuals around the fitted trend (curvature only); the "
           "2014-2019 segment is outside the trend's fit",
    "SC": "every non-COVID pre-period quarter is in the fit window: in-sample fit, not a "
          "pre-trend test",
    "SDID": "every non-COVID pre-period quarter is in the fit window: in-sample fit, not a "
            "pre-trend test",
}


def main():
    panel, selected, spec, pool, m_lvl = S.load_run_context()
    donors = S.POOLS[pool]
    win = S.standard_windows(S.REAL_B, fit_start=spec.fit_start, years=False, anticip=False)
    pop_of = S.pop_at_base(panel, win)
    c, nu_hat, nu = S.crit_for(m_lvl, "h2", donors)
    rows = []
    for outcome, sp in (("emp", spec), ("wage", spec.with_(norm="W"))):
        res = S.placebo_inference(S.make_gap_stat_fn(panel, sp, win), S.CA, donors, pop_of)
        for p, q in enumerate(panel.qi):
            r = res[f"g{p}"]
            ci = S.intervals(r["tau"], r["se"], c)
            rows.append({"outcome": outcome, "quarter": S.qlabel(int(q)), "gap": r["tau"],
                         "se": r["se"], "se_s": r["se_s"], "se_n": r["se_n"],
                         "lo95": ci["lo95"], "hi95": ci["hi95"],
                         "covid": int(int(q) in S.COVID), "in_fit": int(int(q) in set(win.fit)),
                         "post": int(int(q) in set(win.win["pooled"])),
                         "ab257": int(q == S.qidx(2022, 3)), "ab1228": int(q == S.qidx(2023, 4))})
    tab = pd.DataFrame(rows)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tab.to_csv(OUT_DIR / "event_path.csv", index=False, float_format="%.10g")
    m = {"selected": selected, "figure_case": spec.est, "figure_note": CASE_NOTE[spec.est],
         "nu_hat": nu_hat, "nu": nu, "n_rows": len(tab)}
    m.update({f"c_{k}": v for k, v in c.items()})
    for outcome in ("emp", "wage"):
        d = tab[(tab.outcome == outcome) & tab.quarter.isin(
            [S.qlabel(q) for q in range(S.qidx(2022, 1), S.qidx(2023, 3) + 1)])]
        m[f"{outcome}_2022q1_2023q3_n"] = len(d)
        m[f"{outcome}_2022q1_2023q3_band_excludes_0"] = int(((d.lo95 > 0) | (d.hi95 < 0)).sum())
        m[f"{outcome}_2022q1_2023q3_rms_gap"] = float(np.sqrt(np.mean(d.gap ** 2)))
    m.update(S.solver_metrics())
    S.write_json(OUT_DIR / "metrics.json", m)
    print(f"event-path: {len(tab)} rows ({spec.est})")


if __name__ == "__main__":
    main()
