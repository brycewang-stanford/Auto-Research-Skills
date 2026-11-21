"""Run h1-wage (analysis_plan 3; hypotheses[0]).

Inputs  data/derived/state_panel.csv, runs/select/metrics.json, runs/level-mde/metrics.json
Output  runs/h1-wage/metrics.json

The selected candidate re-applied to log average weekly wage (W) with the same pool (SC/SDID
weights refitted on wages, the DDT trend fitted on wages; F16), base 2023Q3, pooled window
2024Q2-2026Q1 and the year windows 2024Q2-2025Q1 and 2025Q2-2026Q1. Inference: placebo SE =
max(SE_s, SE_n); critical values from level-mde statistic h1 (t at nu, L quantile). One-sided 5%
test for each window: reject if tau / SE > c_hi(0.95). Dollars at California's 2023Q3 published
average weekly wage: aww_CA,2023Q3 * (exp(tau) - 1).
"""
import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
# code/select.py shadows the standard-library module 'select'; load the standard one first.
sys.path[:] = [p for p in sys.path if str(Path(p or ".").resolve()) != _HERE]
import select  # noqa: E402,F401  (standard library)
sys.path.insert(0, _HERE)

import sclib as S  # noqa: E402

OUT = Path("runs/h1-wage/metrics.json")


def main():
    panel, selected, spec, pool, m_lvl = S.load_run_context()
    donors = S.POOLS[pool]
    specW = spec.with_(norm="W")
    win = S.standard_windows(S.REAL_B, fit_start=spec.fit_start, years=True, anticip=False)
    res = S.placebo_inference(S.make_stat_fn(panel, specW, win), S.CA, donors, S.pop_at_base(panel, win))
    c, nu_hat, nu = S.crit_for(m_lvl, "h1", donors)
    aww_base = float(panel.aww[panel.row[S.CA], panel.pos(S.REAL_B)])
    m = {"selected": selected, "outcome": "W (log average weekly wage, 722513)", "base": "2023Q3",
         "nu_hat": nu_hat, "nu": nu, "J": len(donors), "aww_ca_2023q3": aww_base}
    for w, tag in (("pooled", "h1"), ("y1", "h1_y1"), ("y2", "h1_y2")):
        r = res[w]
        m.update(S.flatten_inference(tag, r, c, nu))
        m[f"{tag}_t"] = r["tau"] / r["se"]
        m[f"{tag}_reject"] = S.one_sided_reject(r["tau"], r["se"], c)
        m[f"{tag}_pct"] = S.pct(r["tau"])
        m[f"{tag}_dollars"] = aww_base * float(S.np.expm1(r["tau"]))
    m["h1_flag"] = m["h1_reject"]
    m.update(S.solver_metrics())
    S.write_json(OUT, m)
    print(f"h1: {m['h1_att']:.4f} (SE {m['h1_se']:.4f}), reject {m['h1_reject']}")


if __name__ == "__main__":
    main()
