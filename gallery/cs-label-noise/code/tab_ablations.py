"""Table: ablation tests Delta = D_main - D_ablation with decision intervals and status.

Reads runs/abl-noes/metrics.json (A1), runs/abl-cleanval/metrics.json (A2),
runs/abl-budget/metrics.json (A3) and claims.jsonl. Writes paper/tables/tab_ablations.tex.
"""
from __future__ import annotations

import argparse

from figlib import DATASETS, Macros, load_metrics, tex_name, write_metrics, write_tex

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_ablations.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

ABL = [("A1", "abl-noes", "A1 no early stopping", ("Delta",)),
       ("A2", "abl-cleanval", "A2 clean-label validation", ("Delta", "Delta1", "Delta2")),
       ("A3", "abl-budget", "A3 half budget", ("Delta", "Delta1", "Delta2"))]
MET = {run: load_metrics(run) for _, run, _, _ in ABL}
mac = Macros()
MARK = {"attributed": r"$^{a}$", "not attributed": "", "excluded (uninformative)": r"$^{x}$"}

body = [r"\begin{tabular}{@{}l l r c r c r c@{}}",
        r"\toprule",
        r" & & \multicolumn{2}{c}{$\Delta$ (H1 contrast $D$)} & \multicolumn{2}{c}{$\Delta_1$ (H2 contrast $D_1$)}"
        r" & \multicolumn{2}{c}{$\Delta_2$ (H2 contrast $D_2$)} \\",
        r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(l){7-8}",
        r"Dataset & Ablation & Est. & 95\% interval & Est. & 95\% interval & Est. & 95\% interval \\",
        r"\midrule"]
counts = {"attributed": 0, "not attributed": 0, "excluded": 0, "other": 0}
for i, d in enumerate(DATASETS):
    if i:
        body.append(r"\addlinespace")
    for j, (tag, run, label, keys) in enumerate(ABL):
        m = MET[run]
        cells = [tex_name(d) if j == 0 else "", label]
        for key in ("Delta", "Delta1", "Delta2"):
            if key not in keys:
                cells += ["--", ""]
                continue
            b = f"{d}.{tag}.{key}"
            status = m[b + ".status"]
            if status not in MARK:
                raise SystemExit(f"unexpected status {status!r} at {b}")
            counts["excluded" if status.startswith("excluded") else status] += 1
            cells.append(mac.cell(run, b + ".value", m[b + ".value"]) + MARK[status])
            cells.append(f"[{mac.cell(run, b + '.lo', m[b + '.lo'])}, {mac.cell(run, b + '.hi', m[b + '.hi'])}]")
        body.append(" & ".join(cells) + r" \\")
body.append(r"\midrule")
body.append(r"\multicolumn{8}{@{}l}{$^{a}$\,attributed: the interval excludes 0 and $|\Delta| \geq 0.05$"
            r" (pre-registered rule). $^{x}$\,excluded at $\rho = 0$ (uninformative); not tested.} \\")
body.append(r"\multicolumn{8}{@{}l}{--\,: A1 (no early stopping) was planned for the H1 contrast only.} \\")
body += [r"\bottomrule", r"\end{tabular}"]
write_tex(args.out, "code/tab_ablations.py", body)

write_metrics(args.metrics, {"n_attributed": counts["attributed"], "n_not_attributed": counts["not attributed"],
                             "n_excluded": counts["excluded"], "n_macro_cells": mac.used,
                             "n_direct_cells": mac.direct})
print(counts, f"macro cells {mac.used}, direct cells {mac.direct}")
