"""Run verdict (analysis_plan 17; design.method DECISIONS, exactly the approved rules).

Inputs  runs/level-mde, h1-wage, h2-emp, h3-years, sec-cemn, sec-dube, rob-base-2023q4,
        rob-pre-ab257, rob-pool, rob-7225, rob-final-quarters, plc-nonff (metrics.json each)
Output  runs/verdict/metrics.json

H1 supported if the pooled W statistic rejects the one-sided 5% test; if not, H2 is reported as
uninformative about the wage floor. H2: sign from the 95% CI, size from the 90% CI against
b = 0.02, the label from the nine-cell table (recomputed here from h2-emp's intervals and checked
against h2-emp's own label). H3: h3-years' label or 'uninformative'. Elasticities as h3-years
computed them, or 'not computed'. Secondaries S1, S2 and runs 9-13 report the label the H2 rule
gives them, marked 'not the headline'; if S1, S2 or any of runs 9, 10, 11, 13 has a different
sign category from the primary, the headline is stated as 'not robust to <check>' (design-r1 D4).
rob-7225's labels are reported and do not qualify the headline. If plc-nonff's 95% CI excludes
0, 'not separable from a California-wide shock' is appended to the H2 label (analysis_plan 14
and 17; design.method IMPLEMENTATION CHOICES 12).
"""
import sys
from pathlib import Path

import json

import sclib as S

RUNS = Path("runs")
OUT = RUNS / "verdict" / "metrics.json"
QUALIFIERS = [("S1", "sec-cemn", "s1"), ("S2", "sec-dube", "s2"),
              ("rob-base-2023q4", "rob-base-2023q4", "rob"), ("rob-pre-ab257", "rob-pre-ab257", "rob"),
              ("rob-pool", "rob-pool", "rob"), ("rob-final-quarters", "rob-final-quarters", "rob")]
REPORTED = [("rob-7225", "rob-7225", "rob"), ("rob-7225-alldonors", "rob-7225", "rob_alldonors")]


def load(run):
    return json.loads((RUNS / run / "metrics.json").read_text())


def label_of(m, tag):
    ci = {k: m[f"{tag}_{k}"] for k in ("lo95", "hi95", "lo90", "hi90")}
    return S.h2_label(ci)


def main():
    lvl, h1, h2, h3 = load("level-mde"), load("h1-wage"), load("h2-emp"), load("h3-years")
    sel = lvl["selected"]
    for name, m in (("h1-wage", h1), ("h2-emp", h2), ("h3-years", h3)):
        if m["selected"] != sel:
            raise ValueError(f"{name} used a different candidate")
    out = {"selected": sel}
    out["h1_flag"] = int(h1["h1_reject"])
    out["h1_label"] = "supported" if out["h1_flag"] else "not supported"
    sign, size, label = label_of(h2, "h2")
    if label != h2["h2_label"]:
        raise ValueError("h2-emp label disagrees with the rule")
    out.update({"h2_sign": sign, "h2_size": size, "h2_label": label})
    out["h2_wage_floor_note"] = ("" if out["h1_flag"] else
                                 "uninformative about the wage floor (H1 not supported)")
    out["h3_label"] = h3["h3_label"]
    for w in ("pooled", "y1", "y2"):
        out[f"owe_{w}"] = h3[f"owe_{w}"]
        if f"owe_{w}_refitted_wage_weights" in h3:
            out[f"owe_{w}_refitted_wage_weights"] = h3[f"owe_{w}_refitted_wage_weights"]
    not_robust = []
    for name, run, tag in QUALIFIERS + REPORTED:
        m = load(run)
        if m["selected"] != sel:
            raise ValueError(f"{run} used a different candidate")
        s, z, lab = label_of(m, tag)
        key = name.replace("-", "_")
        out.update({f"{key}_sign": s, f"{key}_size": z, f"{key}_label": lab,
                    f"{key}_headline": "not the headline"})
        if (name, run, tag) in QUALIFIERS and s != sign:
            not_robust.append(name)
    out["not_robust_to"] = ",".join(not_robust)
    out["n_not_robust"] = len(not_robust)
    out["h2_headline"] = label + (f" (not robust to {', '.join(not_robust)})" if not_robust else "")
    plc = load("plc-nonff")
    if plc["selected"] != sel:
        raise ValueError("plc-nonff used a different candidate")
    out["plc_nonff_ci95_excludes_0"] = int(plc["plc_ci95_excludes_0"])
    out["h2_label_qualified"] = label + ("; not separable from a California-wide shock"
                                         if out["plc_nonff_ci95_excludes_0"] else "")
    if out["plc_nonff_ci95_excludes_0"]:
        out["h2_headline"] += "; not separable from a California-wide shock"
    S.write_json(OUT, out)
    print(f"verdict: H1 {out['h1_label']}; H2 {out['h2_headline']}; H3 {out['h3_label']}")


if __name__ == "__main__":
    main()
