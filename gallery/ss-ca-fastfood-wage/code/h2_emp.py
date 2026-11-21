"""Run h2-emp (analysis_plan 4; hypotheses[1]).

Inputs  data/derived/state_panel.csv, runs/select/metrics.json, runs/level-mde/metrics.json
Output  runs/h2-emp/metrics.json, runs/h2-emp/placebos.csv (for fig_placebo)

Pooled 2024Q2-2026Q1 ATT of the selected candidate on its employment outcome (E, or P read on the
log-employment scale), base 2023Q3; SE = max(SE_s, SE_n); 95% and 90% CIs with level-mde
statistic h2's critical values (t at nu, L quantile); the H2 rule label; percent
100 (exp(tau) - 1) and implied jobs = mean 2024Q2-2026Q1 California employment (published
quarterly means, not seasonally adjusted) x (1 - exp(-tau)); MDE_h2, h90 and the label
probabilities carried from level-mde, and MDE_h2 and h90 recomputed with this run's SE
(report-only; design-r1 D6).
For an SDID candidate every critical value also carries the SDID floor q_cal of the pool the
run uses (design.method C1; echoed by level-mde).
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

import sclib as S

OUT = Path("runs/h2-emp/metrics.json")
PLACEBOS = Path("runs/h2-emp/placebos.csv")


def main():
    panel, selected, spec, pool, m_lvl = S.load_run_context()
    donors = S.POOLS[pool]
    win = S.standard_windows(S.REAL_B, fit_start=spec.fit_start, years=False, anticip=False)
    pop_of = S.pop_at_base(panel, win)
    res = S.placebo_inference(S.make_stat_fn(panel, spec, win), S.CA, donors, pop_of)
    r = res["pooled"]
    c, nu_hat, nu = S.crit_for(m_lvl, "h2", donors, spec, pool)
    m = {"selected": selected, "outcome": f"{spec.norm} (722513 employment)", "base": "2023Q3",
         "post": "2024Q2-2026Q1", "nu_hat": nu_hat, "nu": nu, "J": len(donors)}
    m.update(S.flatten_inference("h2", r, c, nu))
    ci = S.intervals(r["tau"], r["se"], c)
    sign, size, label = S.h2_label(ci)
    m.update({"h2_sign": sign, "h2_size": size, "h2_label": label})
    m["h2_pct"] = S.pct(r["tau"])
    for k in ("lo95", "hi95", "lo90", "hi90"):
        m[f"h2_pct_{k}"] = S.pct(ci[k])
    post = panel.positions(win.win["pooled"])
    emp_post = float(np.mean(panel.emp["722513"][panel.row[S.CA], post]))
    m["ca_emp_post_mean"] = emp_post
    m["h2_jobs"] = emp_post * float(-np.expm1(-r["tau"]))
    m["h2_jobs_lo95"] = emp_post * float(-np.expm1(-ci["lo95"]))
    m["h2_jobs_hi95"] = emp_post * float(-np.expm1(-ci["hi95"]))
    # carried from level-mde (pre-period) and recomputed with this run's SE (report-only)
    for k in ("mde_h2", "h90_h2", "se_pre_h2", "mde_h2_tJ", "h90_h2_tJ"):
        m[f"lvl_{k}"] = m_lvl[k]
    for k in S.CELL_KEYS.values():
        m[f"lvl_prob_tau0_{k}"] = m_lvl[f"prob_tau0_{k}"]
        m[f"lvl_prob_tau035_{k}"] = m_lvl[f"prob_tau035_{k}"]
    m["mde_h2_post_se"] = S.mde(c["hi975"], nu, r["se"])
    m["h90_h2_post_se"] = S.h90(c, r["se"])
    m.update(S.solver_metrics())
    PLACEBOS.parent.mkdir(parents=True, exist_ok=True)
    pu = pop_of(S.CA)
    pj = np.array([pop_of(j) for j in donors])
    pd.DataFrame({"state_fips": donors, "abbr": [panel.abbr.get(j, j) for j in donors],
                  "pop_base": pj, "tau": r["placebos"],
                  "tau_scaled": r["placebos"] * np.sqrt(pj / pu)}).to_csv(
        PLACEBOS, index=False, float_format="%.10g")
    S.write_json(OUT, m)
    print(f"h2: {m['h2_att']:.4f} [{m['h2_lo95']:.4f}, {m['h2_hi95']:.4f}] -> {label}")


if __name__ == "__main__":
    main()
