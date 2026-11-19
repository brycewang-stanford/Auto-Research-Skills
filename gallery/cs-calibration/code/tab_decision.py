"""Table: the pre-registered decision table for H1, H2a and H2b (run `tab-decision`).

Reads runs/h-tests/metrics.json only. The margins, predicted signs, contrasts and category words
are imported from code/analyze.py, the code run `h-tests` executed, so none is retyped here.
Writes paper/tables/tab_decision.tex: per hypothesis and dataset the mean paired difference
(treatment minus comparison over 10 seeds), its plain paired t(9) 95% interval and the category;
then the overall k-of-4 verdict with the category counts.
"""
from __future__ import annotations

import argparse

from analyze import CATEGORY, HYPOTHESES, OVERALL, overall
from figlib import (CAL_TEX, DATASETS, MODEL_TEX, NAME, Cells, ds_key, load_metrics,
                    write_metrics, write_tex)

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_decision.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

R = "h-tests"
M = load_metrics(R)
assert M["n_seeds"] == 10
C = Cells({R: M})
METRIC_TEX = {"ece": "ECE (plug-in, 15 equal-mass bins)", "brier": "Brier score"}
CAT_SHORT = {0: "no difference", 1: "holds", 2: "contradicted", 3: "inconclusive"}
assert set(CAT_SHORT) == set(CATEGORY)

NC = 4
body = [r"\begin{tabular}{@{}l r c l@{}}",
        r"\toprule",
        r"Dataset & Mean difference & 95\% paired $t(9)$ interval & Category \\",
        r"\midrule"]
n_rows = 0
pivot_flags = {}


def elec_pivotal(hid: str) -> bool:
    """Would the overall verdict change if electricity's category were any other category?
    (analyze.overall, the rule run h-tests applied.) Electricity's random splits may leak across
    neighbouring half-hours, a question sens-elec-time could not settle."""
    cats = {d: int(M[f"{hid}_{ds_key(d)}_cat"]) for d in DATASETS}
    base = overall(list(cats.values()))
    return any(overall([alt if d == "electricity" else c for d, c in cats.items()]) != base
               for alt in CATEGORY if alt != cats["electricity"])


for i, hid in enumerate(("h1", "h2a", "h2b")):
    metric, treat, comp, sign, margin, role = HYPOTHESES[hid]
    assert role == "confirmatory"
    label = {"h1": "H1", "h2a": "H2a", "h2b": "H2b"}[hid]
    t = f"{MODEL_TEX[treat[0]]} {CAL_TEX[treat[1]]}"
    c = f"{MODEL_TEX[comp[0]]} {CAL_TEX[comp[1]]}"
    side = "$>0$" if sign > 0 else "$<0$"
    if i:
        body.append(r"\addlinespace")
    body.append(rf"\multicolumn{{{NC}}}{{@{{}}l}}{{\textbf{{{label}}}: {METRIC_TEX[metric]}, "
                rf"{t} minus {c}; predicted {side}; margin $\pm{margin:g}$}} \\")
    pivot_flags[f"{hid}_elec_pivotal"] = int(elec_pivotal(hid))
    for d in DATASETS:
        k = f"{hid}_{ds_key(d)}"
        dagger = r"$^{\dagger}$" if d == "electricity" and pivot_flags[f"{hid}_elec_pivotal"] else ""
        code = int(C.word(R, k + "_cat"))
        body.append(" & ".join([
            r"\quad " + NAME[d] + dagger,
            C.macro(R, k + "_mean"),
            f"[{C.macro(R, k + '_lo')}, {C.macro(R, k + '_hi')}]",
            CAT_SHORT[code],
        ]) + r" \\")
        n_rows += 1
    v = int(C.word(R, f"{hid}_overall_code"))
    assert OVERALL[v] == M[f"{hid}_overall"], (OVERALL[v], M[f"{hid}_overall"])
    counts = ", ".join(f"{C.plain(R, f'{hid}_n_{key}', 'd')} {word}" for key, word in
                       (("holds", "holds"), ("contradicted", "contradicted"),
                        ("nodiff", "no difference"), ("inconclusive", "inconclusive")))
    body.append(rf"\multicolumn{{{NC}}}{{@{{}}l}}{{\quad Overall (k-of-4 rule): \emph{{{OVERALL[v]}}} ({counts})}} \\")
body += [r"\bottomrule", r"\end{tabular}"]
write_tex(args.out, "code/tab_decision.py", body, C.footer())

write_metrics(args.metrics, {"n_dataset_rows": n_rows, "n_macro_cells": len(C.macros),
                             "n_plain_cells": len(C.raw), "checksum_values": sum(C.values), **pivot_flags})
print(f"rows {n_rows}, macros {len(C.macros)}, plain {len(C.raw)}")
