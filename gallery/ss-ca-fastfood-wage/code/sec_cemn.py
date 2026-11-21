"""Run sec-cemn (analysis_plan 7; secondary S1, reported whatever the rule picks).

Inputs  data/derived/state_panel.csv, runs/select/metrics.json, runs/level-mde/metrics.json
Output  runs/sec-cemn/metrics.json

S1 = CEM's detrended indexed DD under the 2023Q3 timing: g_t = SA ln(E_CA) - SA ln(sum of R50
employment); tau = mean over 2024Q2-2026Q1 of [g_t - g_B - (t - B)(g_B - g_{B-8}) / 8], with
CEM's endpoint trend 2021Q3-2023Q3 (2021Q3 kept: the one use of a COVID quarter, deviation D2).
The simple (undetrended) version is reported too. Inference as design.method INFERENCE with the
R50 placebos and level-mde statistic s1's critical values (t at nu_s1, L quantile); the simple
version uses the same s1 values (it is the same comparison without the trend). CEM's placebo rank
p = (b + 1) / (m + 1), b = number of placebo estimates at or below California's, m = J (one-sided,
lower tail; unscaled placebo estimates). S1's H2 rule label enters the verdict.

Report-only cross-check against print: September-to-September fixed horizon 2023-2025 on month-3
employment levels (sep_722513, not seasonally adjusted), California minus the summed 48 states of
R50 without Alaska and Michigan (CEMN), indexed to September 2023 = 100, in index points: simple
= 100 (CA_2025 / CA_2023 - US_2025 / US_2023); detrended = simple minus two times the annual
2021-2023 trend, the annual trend being half the September 2021 to September 2023 change of the
California-minus-US indexed difference. Next to CEMN Table 3 Panel B (-2.74, -3.72).
"""
import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
# code/select.py shadows the standard-library module 'select'; load the standard one first.
sys.path[:] = [p for p in sys.path if str(Path(p or ".").resolve()) != _HERE]
import select  # noqa: E402,F401  (standard library)
sys.path.insert(0, _HERE)

import numpy as np  # noqa: E402

import sclib as S  # noqa: E402

OUT = Path("runs/sec-cemn/metrics.json")
PRINT_SIMPLE = -2.74     # CEMN (2026) Table 3 Panel B, FF, Rest of US, simple
PRINT_DETR = -3.72       # CEMN (2026) Table 3 Panel B, FF, Rest of US, detrended


def cem_fixed_horizon(panel):
    """September-to-September indexed DD on month-3 levels, 48-state comparison (CEMN)."""
    us = [u for u in S.R50 if u not in S.AK_MI]
    sep = {y: S.qidx(y, 3) for y in (2021, 2023, 2025)}
    ca = {y: float(panel.sep[panel.row[S.CA], panel.pos(q)]) for y, q in sep.items()}
    rest = {y: float(panel.sep[panel.rows(us), panel.pos(q)].sum()) for y, q in sep.items()}
    idx_ca = {y: 100.0 * ca[y] / ca[2023] for y in sep}
    idx_us = {y: 100.0 * rest[y] / rest[2023] for y in sep}
    simple = (idx_ca[2025] - 100.0) - (idx_us[2025] - 100.0)
    annual_trend = ((idx_ca[2023] - idx_ca[2021]) - (idx_us[2023] - idx_us[2021])) / 2.0
    detr = simple - 2.0 * annual_trend
    return simple, detr, annual_trend, len(us)


def main():
    panel, selected, spec, pool, m_lvl = S.load_run_context()
    donors = S.R50
    win = S.standard_windows(S.REAL_B, years=False, anticip=False)
    pop_of = S.pop_at_base(panel, win)
    c, nu_hat, nu = S.crit_for(m_lvl, "s1", donors)
    m = {"selected": selected, "spec": "S1: DDT endpoint trend, AGG, E, R50", "J": len(donors),
         "nu_hat": nu_hat, "nu": nu, "trend_start": "2021Q3"}
    for tag, sp in (("s1", S.Spec(est="DDTE", weighting="AGG", norm="E")),
                    ("s1_simple", S.Spec(est="DD", weighting="AGG", norm="E"))):
        r = S.placebo_inference(S.make_stat_fn(panel, sp, win), S.CA, donors, pop_of)["pooled"]
        m.update(S.flatten_inference(tag, r, c, nu))
        ci = S.intervals(r["tau"], r["se"], c)
        sign, size, label = S.h2_label(ci)
        m.update({f"{tag}_sign": sign, f"{tag}_size": size, f"{tag}_label": label,
                  f"{tag}_pct": S.pct(r["tau"])})
        b = int(np.sum(r["placebos"] <= r["tau"]))
        m[f"{tag}_rank_p"] = (b + 1) / (len(donors) + 1)
    simple, detr, trend, n_us = cem_fixed_horizon(panel)
    m.update({"cemn_fh_states": n_us, "cemn_fh_simple": simple, "cemn_fh_detrended": detr,
              "cemn_fh_annual_trend": trend, "cemn_print_simple": PRINT_SIMPLE,
              "cemn_print_detrended": PRINT_DETR, "cemn_fh_simple_minus_print": simple - PRINT_SIMPLE,
              "cemn_fh_detrended_minus_print": detr - PRINT_DETR})
    m.update(S.solver_metrics())
    S.write_json(OUT, m)
    print(f"S1: {m['s1_att']:.4f} -> {m['s1_label']}; fixed horizon {simple:.2f} / {detr:.2f}")


if __name__ == "__main__":
    main()
