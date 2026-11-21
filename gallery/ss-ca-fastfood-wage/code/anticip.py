"""Run anticip (analysis_plan 6; report-only: no label, no test claim).

Inputs  data/derived/state_panel.csv, runs/select/metrics.json, runs/level-mde/metrics.json
Output  runs/anticip/metrics.json

The employment and wage ATTs of the selected candidate over the anticipation window A =
2023Q4-2024Q1 against base 2023Q3, same estimator, pool and SE. SDID: omega fitted with zeta at
T_post = 8 (the omega of the main estimate), lambda fitted for A; the wage refits its weights (H1).
Critical values: level-mde statistics h2 (employment) and h1 (wage), the 'corresponding anticip
statistics' of design.method LEVEL CHECK. No quarter after 2024Q1 is read by the estimates.
For an SDID candidate every critical value also carries the SDID floor q_cal of the pool the
run uses (design.method C1; echoed by level-mde).
"""
import sys
from pathlib import Path

import sclib as S

OUT = Path("runs/anticip/metrics.json")


def main():
    panel, selected, spec, pool, m_lvl = S.load_run_context()
    donors = S.POOLS[pool]
    win = S.standard_windows(S.REAL_B, fit_start=spec.fit_start, years=False, anticip=True,
                             pooled=False)
    pop_of = S.pop_at_base(panel, win)
    m = {"selected": selected, "window": "2023Q4-2024Q1", "base": "2023Q3", "J": len(donors)}
    for tag, sp, stat in (("anticip_emp", spec, "h2"), ("anticip_wage", spec.with_(norm="W"), "h1")):
        r = S.placebo_inference(S.make_stat_fn(panel, sp, win), S.CA, donors, pop_of)["A"]
        c, nu_hat, nu = S.crit_for(m_lvl, stat, donors, sp, pool)
        m.update(S.flatten_inference(tag, r, c, nu))
        m[f"{tag}_nu_hat"] = nu_hat
        m[f"{tag}_nu"] = nu
        m[f"{tag}_pct"] = S.pct(r["tau"])
    m.update(S.solver_metrics())
    S.write_json(OUT, m)
    print(f"anticip: emp {m['anticip_emp_att']:.4f}, wage {m['anticip_wage_att']:.4f}")


if __name__ == "__main__":
    main()
