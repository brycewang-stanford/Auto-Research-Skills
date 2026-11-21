"""Placebo-outcome runs (analysis_plan 14-15): python3 code/placebo_outcome.py nonff|722511.

Inputs  data/derived/state_panel.csv, runs/select/metrics.json, runs/level-mde/metrics.json
Output  runs/plc-nonff/metrics.json or runs/plc-722511/metrics.json

The selected candidate (estimator, weighting, normalisation, pool, base 2023Q3, post
2024Q2-2026Q1) applied to employment in all covered industries except 722513 (nonff =
emp_10 - emp_722513) or to full-service employment (722511). Critical values: level-mde statistic
h2 (L quantile; t at nu over the pool). plc-nonff 'fails' if its 95% CI excludes 0 (the H2 label
is then qualified as not separable from a California-wide shock; no re-specification).
plc-722511 is reported only (not a clean placebo; never a DDD comparison).
For an SDID candidate every critical value also carries the SDID floor q_cal of the pool the
run uses (design.method C1; echoed by level-mde).
"""
import sys
from pathlib import Path

import sclib as S

RUN_IDS = {"nonff": "plc-nonff", "722511": "plc-722511"}


def main(which):
    if which not in RUN_IDS:
        raise SystemExit(f"argument must be one of {sorted(RUN_IDS)}")
    panel, selected, spec, pool, m_lvl = S.load_run_context()
    donors = S.POOLS[pool]
    sp = spec.with_(industry=which)
    win = S.standard_windows(S.REAL_B, fit_start=spec.fit_start, years=False, anticip=False)
    r = S.placebo_inference(S.make_stat_fn(panel, sp, win), S.CA, donors,
                            S.pop_at_base(panel, win))["pooled"]
    c, nu_hat, nu = S.crit_for(m_lvl, "h2", donors, spec, pool)
    m = {"selected": selected, "outcome": which, "J": len(donors), "nu_hat": nu_hat, "nu": nu}
    m.update(S.flatten_inference("plc", r, c, nu))
    m["plc_pct"] = S.pct(r["tau"])
    ci = S.intervals(r["tau"], r["se"], c)
    m["plc_ci95_excludes_0"] = int(ci["lo95"] > 0 or ci["hi95"] < 0)
    if which == "nonff":
        m["plc_fails"] = m["plc_ci95_excludes_0"]
    m.update(S.solver_metrics())
    S.write_json(Path("runs") / RUN_IDS[which] / "metrics.json", m)
    print(f"{RUN_IDS[which]}: {r['tau']:.4f} [{ci['lo95']:.4f}, {ci['hi95']:.4f}]")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
