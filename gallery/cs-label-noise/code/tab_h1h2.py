"""Tables: H1 and H2 per-dataset contrasts and outcomes, and the components behind them.

Reads runs/h-tests/metrics.json, runs/descriptives/metrics.json (only to match A(0), A(0.4)
and m to their claim macros) and claims.jsonl (macros). Writes
  paper/tables/tab_h1h2.tex   D, D1, D2 with decision interval, S, half-width, drop difference,
                              per-dataset outcome, and the overall count verdicts
  paper/tables/tab_parts.tex  per dataset and method: A(0), A(0.4), m, drop, h, lower end of
                              the headroom interval, r
"""
from __future__ import annotations

import argparse

from figlib import (DATASETS, METHODS, Macros, load_metrics, outcome_words, tex_name,
                    write_metrics, write_tex)

ap = argparse.ArgumentParser()
ap.add_argument("--out-main", default="paper/tables/tab_h1h2.tex")
ap.add_argument("--out-parts", default="paper/tables/tab_parts.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

R = "h-tests"
M = load_metrics(R)
mac = Macros()
METHOD_TEX = {"lr": "LR", "rf": "RF", "gbdt": "GBDT"}
CONTRASTS = [("H1", "D", r"$D = r_{\mathrm{GBDT}} - r_{\mathrm{RF}}$"),
             ("H2", "D1", r"$D_1 = r_{\mathrm{LR}} - r_{\mathrm{GBDT}}$"),
             ("H2", "D2", r"$D_2 = r_{\mathrm{LR}} - r_{\mathrm{RF}}$")]


def c(metric: str, alt: tuple = ()) -> str:
    return mac.cell(R, metric, M[metric], alt=alt)


def name(d: str) -> str:
    return tex_name(d) + (r"$^{\dagger}$" if M[f"{d}.c"] > 0.1 else "")


# --- main table -----------------------------------------------------------------------
# One block per dataset: a name row, the contrast rows, and an outcome row after each
# hypothesis, so the reporting words fit without a narrow wrapped column.
NC = 6
body = [r"\begin{tabular}{@{}l r c r r r@{}}",
        r"\toprule",
        r"Contrast & Estimate & 95\% decision interval & $S$ & Half-width & Drop diff. \\",
        r"\midrule"]
n_rows = 0
for i, d in enumerate(DATASETS):
    if i:
        body.append(r"\addlinespace")
    body.append(rf"\multicolumn{{{NC}}}{{@{{}}l}}{{{name(d)}}} \\")
    for hyp, key, label in CONTRASTS:
        b = f"{d}.{hyp}.{key}"
        body.append(" & ".join([
            r"\quad " + label,
            c(b + ".value"),
            f"[{c(b + '.lo')}, {c(b + '.hi')}]",
            c(b + ".S"),
            c(b + ".half"),
            c(b + ".ddrop"),
        ]) + r" \\")
        n_rows += 1
        if key in ("D", "D2"):
            outcome = outcome_words(M[f"{d}.{hyp}.outcome"])
            body.append(rf"\multicolumn{{{NC}}}{{@{{}}l}}{{\quad\quad {hyp} outcome: {outcome}}} \\")
body.append(r"\midrule")
for hyp in ("H1", "H2"):
    def n(key: str) -> str:
        return mac.cell(R, f"{hyp}.{key}", M[f"{hyp}.{key}"], "d")
    body.append(rf"\multicolumn{{{NC}}}{{@{{}}l}}{{{hyp} overall: \emph{{{M[hyp + '.verdict']}}} "
                rf"(count rule over {n('n_informative')} informative datasets; support needs {n('support_needed')})}} \\")
    body.append(rf"\multicolumn{{{NC}}}{{@{{}}l}}{{\quad {n('n_supported')} supported, {n('n_contradicted')} contradicted, "
                rf"{n('n_no_meaningful_difference')} no meaningful difference, {n('n_inconclusive')} inconclusive}} \\")
body += [r"\bottomrule", r"\end{tabular}"]
write_tex(args.out_main, "code/tab_h1h2.py", body)

# --- components table -----------------------------------------------------------------
D = "descriptives"
P = [r"\begin{tabular}{@{}l l r r r r r r r@{}}",
     r"\toprule",
     r"Dataset & Method & $m$ & $A(0)$ & $A(0.4)$ & Drop & $h = A(0) - m$ & $h$ lower & $r$ \\",
     r"\midrule"]
for i, d in enumerate(DATASETS):
    if i:
        P.append(r"\addlinespace")
    for j, meth in enumerate(METHODS):
        b = f"{d}.{meth}"
        P.append(" & ".join([
            name(d) if j == 0 else "",
            METHOD_TEX[meth],
            c(f"{d}.m", alt=[(D, f"{d}.m_mean")]) if j == 0 else "",
            c(b + ".A0", alt=[(D, f"{b}.rho0.acc_mean")]),
            c(b + ".A4", alt=[(D, f"{b}.rho0.4.acc_mean")]),
            c(b + ".drop", alt=[(D, f"{b}.rho0.4.drop")]),
            c(b + ".h"),
            c(b + ".h_lo"),
            c(b + ".r"),
        ]) + r" \\")
P += [r"\bottomrule", r"\end{tabular}"]
write_tex(args.out_parts, "code/tab_h1h2.py", P)

write_metrics(args.metrics, {"n_contrast_rows": n_rows, "n_macro_cells": mac.used,
                             "n_direct_cells": mac.direct})
print(f"macro cells {mac.used}, direct cells {mac.direct}")
