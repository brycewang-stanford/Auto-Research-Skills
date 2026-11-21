"""Run sec-dube (analysis_plan 8; secondary S2, reported whatever the rule picks).

Inputs  data/derived/state_panel.csv, runs/select/metrics.json, runs/level-mde/metrics.json
Output  runs/sec-dube/metrics.json

S2 = Dube's SDID under the 2023Q3 timing: SA log(emp/pop) (P), D20, fit window 2015Q1-2023Q3
without C, post 2024Q2-2026Q1; the wage effect applies the employment omega and lambda (Dube's
choice). Inference as design.method INFERENCE (each placebo with its own employment fit, reused
for its wage), with level-mde statistic s2's critical values (t at nu_s2, L quantile); the
reused-weights wage interval uses the same s2 values (same comparison and donors). S2's H2 rule
label enters the verdict.

Report-only cross-check: Dube's own timing (fit 2015Q1-2023Q4 without C, 2024Q1 dropped, post
2024Q2-2025Q3, so zeta uses T_post = 6), in percent (100 x tau), with the scaled placebo SE
(SE_s, Dube's Ferman-Pinto scaling) next to Table 1 Panel A SDID: -0.26 [0.54], wage +6.99.
Our seasonal factors are 2014-2019 and our SDID has the intercept and two penalties
(deviation D3), so the difference measures those choices together.
"""
import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
# code/select.py shadows the standard-library module 'select'; load the standard one first.
sys.path[:] = [p for p in sys.path if str(Path(p or ".").resolve()) != _HERE]
import select  # noqa: E402,F401  (standard library)
sys.path.insert(0, _HERE)

import sclib as S  # noqa: E402

OUT = Path("runs/sec-dube/metrics.json")
PRINT_EMP, PRINT_SE, PRINT_WAGE = -0.26, 0.54, 6.99   # Dube (2026) Table 1 Panel A, SDID
FIT_START_DUBE = S.qidx(2015, 1)


def main():
    panel, selected, spec, pool, m_lvl = S.load_run_context()
    donors = S.D20
    s2 = S.Spec(est="SDID", norm="P", fit_start=FIT_START_DUBE)
    c, nu_hat, nu = S.crit_for(m_lvl, "s2", donors)
    m = {"selected": selected, "spec": "S2: SDID, P, D20, fit 2015Q1-2023Q3 without C",
         "J": len(donors), "nu_hat": nu_hat, "nu": nu}
    win = S.standard_windows(S.REAL_B, fit_start=FIT_START_DUBE, years=False, anticip=False)
    res = S.placebo_inference(S.make_reuse_stat_fn(panel, s2, win), S.CA, donors,
                              S.pop_at_base(panel, win))
    for tag, key in (("s2", "pooled"), ("s2_wage_reused", "wr_pooled")):
        r = res[key]
        m.update(S.flatten_inference(tag, r, c, nu))
        m[f"{tag}_pct"] = S.pct(r["tau"])
    ci = S.intervals(res["pooled"]["tau"], res["pooled"]["se"], c)
    sign, size, label = S.h2_label(ci)
    m.update({"s2_sign": sign, "s2_size": size, "s2_label": label})
    # Dube's own timing (report-only)
    Bd = S.qidx(2023, 4)
    wd = S.custom_windows(Bd, pooled=range(S.qidx(2024, 2), S.qidx(2025, 3) + 1),
                          fit_start=FIT_START_DUBE, note="Dube timing")
    rd = S.placebo_inference(S.make_reuse_stat_fn(panel, s2, wd), S.CA, donors,
                             S.pop_at_base(panel, wd))
    m.update({"dube_timing_emp_100tau": 100 * rd["pooled"]["tau"],
              "dube_timing_emp_se_s_100": 100 * rd["pooled"]["se_s"],
              "dube_timing_emp_se_100": 100 * rd["pooled"]["se"],
              "dube_timing_wage_100tau": 100 * rd["wr_pooled"]["tau"],
              "dube_print_emp": PRINT_EMP, "dube_print_se": PRINT_SE, "dube_print_wage": PRINT_WAGE})
    m["dube_timing_emp_minus_print"] = m["dube_timing_emp_100tau"] - PRINT_EMP
    m["dube_timing_wage_minus_print"] = m["dube_timing_wage_100tau"] - PRINT_WAGE
    m.update(S.solver_metrics())
    S.write_json(OUT, m)
    print(f"S2: {m['s2_att']:.4f} -> {label}; Dube timing {m['dube_timing_emp_100tau']:.2f}")


if __name__ == "__main__":
    main()
