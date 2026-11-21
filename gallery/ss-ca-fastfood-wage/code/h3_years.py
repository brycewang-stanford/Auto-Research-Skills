"""Run h3-years (analysis_plan 5; hypotheses[2]).

Inputs  data/derived/state_panel.csv, runs/select/metrics.json, runs/level-mde/metrics.json,
        runs/h1-wage/metrics.json
Output  runs/h3-years/metrics.json

Year-1 (2024Q2-2025Q1) and year-2 (2025Q2-2026Q1) employment ATTs of the selected candidate
(SDID: omega fitted once with the 8-quarter window, lambda refitted per year; SC: one w), their
difference tau_2 - tau_1 with its placebo SE (the difference computed for every placebo) and 95%
CI from level-mde statistic h3, the H3 label, and MDE_h3 recomputed with this run's SE. The label
is 'uninformative' if level-mde's h3_informative = 0 or the recomputed MDE_h3 exceeds 0.04.
The yearly ATTs carry level-mde statistic h2's critical values.

Own-wage elasticities (design.method DECISIONS; design-r1 D5), point values only: employment ATT
/ wage ATT with the employment fit reused (SC: the employment w; SDID: the employment omega and,
per window, the employment lambda; DD and DDT: the H1 wage ATT, which already is that one). For SC
and SDID the ratio with the H1 (refitted) wage ATT is reported next to it. Computed only for a
window whose H1 wage effect rejects the one-sided 5% test and whose reused-weights wage ATT is
positive; otherwise 'not computed'.
"""
import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
# code/select.py shadows the standard-library module 'select'; load the standard one first.
sys.path[:] = [p for p in sys.path if str(Path(p or ".").resolve()) != _HERE]
import select  # noqa: E402,F401  (standard library)
sys.path.insert(0, _HERE)

import json  # noqa: E402

import sclib as S  # noqa: E402

H1 = Path("runs/h1-wage/metrics.json")
OUT = Path("runs/h3-years/metrics.json")


def main():
    panel, selected, spec, pool, m_lvl = S.load_run_context()
    m_h1 = json.loads(H1.read_text())
    if m_h1["selected"] != selected:
        raise ValueError("runs/h1-wage used a different candidate")
    donors = S.POOLS[pool]
    win = S.standard_windows(S.REAL_B, fit_start=spec.fit_start, years=True, anticip=False)
    res = S.placebo_inference(S.make_stat_fn(panel, spec, win, diff=True), S.CA, donors,
                              S.pop_at_base(panel, win))
    c3, nu3_hat, nu3 = S.crit_for(m_lvl, "h3", donors)
    c2, nu2_hat, nu2 = S.crit_for(m_lvl, "h2", donors)
    m = {"selected": selected, "J": len(donors), "nu_hat_h3": nu3_hat, "nu_h3": nu3,
         "nu_hat_h2": nu2_hat, "nu_h2": nu2}
    m.update(S.flatten_inference("h3_y1", res["y1"], c2, nu2))
    m.update(S.flatten_inference("h3_y2", res["y2"], c2, nu2))
    m.update(S.flatten_inference("h3_diff", res["diff"], c3, nu3))
    m["h3_pooled_att"] = res["pooled"]["tau"]
    d = res["diff"]
    ci = S.intervals(d["tau"], d["se"], c3)
    m["h3_rule_label"] = S.h3_label(ci["lo95"], ci["hi95"])
    m["lvl_mde_h3"] = m_lvl["mde_h3"]
    m["lvl_h3_informative"] = m_lvl["h3_informative"]
    m["mde_h3_post_se"] = S.mde(c3["hi975"], nu3, d["se"])
    m["mde_h3_max"] = max(m["lvl_mde_h3"], m["mde_h3_post_se"])
    informative = int(m_lvl["h3_informative"] == 1 and m["mde_h3_post_se"] <= 0.04)
    m["h3_informative"] = informative
    m["h3_label"] = m["h3_rule_label"] if informative else "uninformative"
    # own-wage elasticities
    _, tw = S.estimate_reused(panel, spec, win, S.CA, donors)
    for w, h1tag, tag in (("pooled", "h1", "pooled"), ("y1", "h1_y1", "y1"), ("y2", "h1_y2", "y2")):
        emp = res[w]["tau"]
        wr = tw[w]
        m[f"wage_reused_{tag}"] = wr
        ok = int(m_h1[f"{h1tag}_reject"] == 1 and wr > 0)
        m[f"owe_{tag}_computed"] = ok
        m[f"owe_{tag}"] = emp / wr if ok else "not computed"
        if spec.est in ("SC", "SDID"):
            m[f"owe_{tag}_refitted_wage_weights"] = emp / m_h1[f"{h1tag}_att"] if ok else "not computed"
    m.update(S.solver_metrics())
    S.write_json(OUT, m)
    print(f"h3: diff {d['tau']:.4f} [{ci['lo95']:.4f}, {ci['hi95']:.4f}] -> {m['h3_label']}")


if __name__ == "__main__":
    main()
