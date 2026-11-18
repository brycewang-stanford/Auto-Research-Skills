"""Table: clean-test accuracy, mean (SD) over the 10 seeds, at every flip rate.

Reads runs/descriptives/metrics.json and claims.jsonl. Writes paper/tables/tab_accuracy.tex.
"""
from __future__ import annotations

import argparse

from common import RHOS
from figlib import DATASETS, METHODS, Macros, load_metrics, rho_key, tex_name, write_metrics, write_tex

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_accuracy.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

R = "descriptives"
M = load_metrics(R)
X = load_metrics("exclusion-check")
mac = Macros()
METHOD_TEX = {"lr": "LR", "rf": "RF", "gbdt": "GBDT"}

body = [r"\begin{tabular}{@{}l l r " + "c " * len(RHOS) + r"@{}}",
        r"\toprule",
        r" & & & \multicolumn{" + str(len(RHOS)) + r"}{c}{Flip rate $\rho$} \\",
        r"\cmidrule(l){4-" + str(3 + len(RHOS)) + "}",
        r"Dataset & Method & $m$ & " + " & ".join(f"{r:g}" for r in RHOS) + r" \\",
        r"\midrule"]
for i, d in enumerate(DATASETS):
    if i:
        body.append(r"\addlinespace")
    excluded = not X[f"{d}.informative_h1"]
    for j, meth in enumerate(METHODS):
        cells = [(tex_name(d) + (" (excluded)" if excluded else "")) if j == 0 else "", METHOD_TEX[meth],
                 mac.cell(R, f"{d}.m_mean", M[f"{d}.m_mean"]) if j == 0 else ""]
        for rho in RHOS:
            b = f"{d}.{meth}.{rho_key(rho)}"
            cells.append(f"{mac.cell(R, b + '.acc_mean', M[b + '.acc_mean'])} "
                         f"({mac.cell(R, b + '.acc_sd', M[b + '.acc_sd'])})")
        body.append(" & ".join(cells) + r" \\")
body += [r"\bottomrule", r"\end{tabular}"]
write_tex(args.out, "code/tab_accuracy.py", body)

write_metrics(args.metrics, {"n_rows": len(DATASETS) * len(METHODS), "n_macro_cells": mac.used,
                             "n_direct_cells": mac.direct})
print(f"macro cells {mac.used}, direct cells {mac.direct}")
