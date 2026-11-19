"""Table: metric levels per dataset, model and calibrator (run `tab-levels`).

Reads runs/describe/metrics.json only (seed means and SDs over the 10 seeds of the 360 cells of
run `main`). Writes paper/tables/tab_levels.tex: for every (dataset, model, calibrator) the seed
mean and, in parentheses, the seed SD of the plug-in ECE, the Brier score, the log-loss (clipping
epsilon 1e-6) and the ROC-AUC, and the mean number of non-empty ECE bins.
"""
from __future__ import annotations

import argparse

from figlib import (CAL_TEX, CALIBRATORS, DATASETS, MODEL_TEX, MODELS, NAME, Cells, ds_key,
                    load_metrics, write_metrics, write_tex)

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_levels.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

R = "describe"
M = load_metrics(R)
assert M["n_seeds"] == 10
C = Cells({R: M})
# Same formats as the claims' macros of the same quantity, so a plain cell reads like a macro cell.
FMT = {"ece": (".4f", ".4f"), "brier": (".4f", ".4f"), "logloss": (".3f", ".4f"),
       "auc": (".3f", ".4f")}
# Quoted by the paper (a claim exists): ECE and Brier for every calibrator; log-loss and AUC for
# none and isotonic. Platt's log-loss and AUC are descriptive only and printed as plain numbers.
QUOTED = {"ece": set(CALIBRATORS), "brier": set(CALIBRATORS), "logloss": {"none", "isotonic"},
          "auc": {"none", "isotonic"}}


def mean_sd(base: str, metric: str, cal: str) -> str:
    fm, fs = FMT[metric]
    k = f"{base}_{metric}"
    if cal in QUOTED[metric]:
        m, s = C.macro(R, k + "_mean"), C.macro(R, k + "_sd")
    else:
        m, s = C.plain(R, k + "_mean", fm), C.plain(R, k + "_sd", fs)
    return rf"{m} {{\footnotesize ({s})}}"


NC = 8
body = [r"\begin{tabular}{@{}l l l r r r r r@{}}",
        r"\toprule",
        r"Dataset & Model & Calibrator & ECE & Brier & Log-loss & AUC & Bins \\",
        r"\midrule"]
n_rows = 0
for i, d in enumerate(DATASETS):
    if i:
        body.append(r"\midrule")
    for j, model in enumerate(MODELS):
        if j:
            body.append(r"\addlinespace[2pt]")
        for k, cal in enumerate(CALIBRATORS):
            base = f"{ds_key(d)}_{model}_{cal}"
            body.append(" & ".join([
                NAME[d] if (j == 0 and k == 0) else "",
                MODEL_TEX[model] if k == 0 else "",
                CAL_TEX[cal],
                mean_sd(base, "ece", cal),
                mean_sd(base, "brier", cal),
                mean_sd(base, "logloss", cal),
                mean_sd(base, "auc", cal),
                C.macro(R, base + "_ece_bins_mean"),
            ]) + r" \\")
            n_rows += 1
body += [r"\bottomrule", r"\end{tabular}"]
write_tex(args.out, "code/tab_levels.py", body, C.footer())

write_metrics(args.metrics, {"n_rows": n_rows, "n_macro_cells": len(C.macros),
                             "n_plain_cells": len(C.raw), "checksum_values": sum(C.values)})
print(f"rows {n_rows}, macros {len(C.macros)}, plain {len(C.raw)}")
