"""Table: the exclusion check, decided from rho = 0 cells only.

Reads runs/exclusion-check/metrics.json (headroom, m, informative flags, threshold),
runs/descriptives/metrics.json (A(0) per method, with its claim macros; checked against
runs/main-rho0/metrics.json) and claims.jsonl. Writes paper/tables/tab_exclusion.tex.
"""
from __future__ import annotations

import argparse
import math

from figlib import DATASETS, METHODS, Macros, load_metrics, tex_name, write_metrics, write_tex

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_exclusion.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

X, R0, D = "exclusion-check", "main-rho0", "descriptives"
mx, m0, md = load_metrics(X), load_metrics(R0), load_metrics(D)
mac = Macros()
thr = mx["threshold"]

body = [r"\begin{tabular}{@{}l r r r r r r r c c@{}}",
        r"\toprule",
        r" & & \multicolumn{3}{c}{$A(0)$} & \multicolumn{3}{c}{Headroom $h = A(0) - m$}"
        r" & \multicolumn{2}{c}{Informative} \\",
        r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}\cmidrule(l){9-10}",
        r"Dataset & $m$ & LR & RF & GBDT & LR & RF & GBDT & H1 & H2 \\",
        r"\midrule"]
n_below = 0
for d in DATASETS:
    m_val = mx[f"{d}.m_mean"]
    # main-rho0 averages m in floating point, exclusion-check exactly; they agree to rounding.
    assert math.isclose(m_val, m0[f"{d}.m_mean"], rel_tol=1e-12), "m differs between runs"
    cells = [tex_name(d), mac.cell(X, f"{d}.m_mean", m_val, alt=[(D, f"{d}.m_mean")])]
    for meth in METHODS:
        k = f"{d}.{meth}.rho0.acc_mean"
        # The claim macros for A(0) sit on descriptives (exact means); main-rho0 holds the same
        # seed means computed in floating point.
        assert math.isclose(md[k], m0[k], rel_tol=1e-12), f"A(0) differs between runs at {k}"
        cells.append(mac.cell(D, k, md[k]))
    below_any = False
    for meth in METHODS:
        k = f"{d}.{meth}.headroom"
        cell = mac.cell(X, k, mx[k])
        if mx[k] < thr:                      # display mark only; the flag below is the ledger's decision
            cell += r"$^{\ast}$"
            below_any = True
            n_below += 1
        cells.append(cell)
    inf1, inf2 = mx[f"{d}.informative_h1"], mx[f"{d}.informative_h2"]
    assert bool(inf1) == bool(inf2) == (not below_any), f"display mark disagrees with the ledger on {d}"
    cells += ["yes" if inf1 else "no", "yes" if inf2 else "no"]
    body.append(" & ".join(cells) + r" \\")
body.append(r"\midrule")
body.append(rf"\multicolumn{{10}}{{@{{}}l}}{{Informative datasets: "
            rf"{mac.cell(X, 'n_informative_h1', mx['n_informative_h1'], 'd')} for H1, "
            rf"{mac.cell(X, 'n_informative_h2', mx['n_informative_h2'], 'd')} for H2. "
            rf"$^{{\ast}}$\,headroom below {thr:g}.}} \\")
body += [r"\bottomrule", r"\end{tabular}"]
write_tex(args.out, "code/tab_exclusion.py", body)

write_metrics(args.metrics, {"n_rows": len(DATASETS), "n_headroom_below_threshold": n_below,
                             "n_macro_cells": mac.used, "n_direct_cells": mac.direct})
print(f"macro cells {mac.used}, direct cells {mac.direct}")
