"""Table: primary ATT and every robustness estimate; descriptive selection on the 1975 shock.

Reads runs/main-aipw, rob-trim, rob-covsets, rob-learners, rob-estimators, rob-diff74 and
select-re75 metrics.json, and claims.jsonl (macros). Writes paper/tables/tab_main.tex.
A cell is "--" when the run did not log that quantity; nothing is computed here.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import Macros, load_metrics, write_metrics, write_tex  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_main.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

mac = Macros()
M = load_metrics("main-aipw")["margin_M"]

# (label, run, metric prefix) in the order of design.analysis_plan; same rows as fig_forest.
ROWS = [
    ("Primary: cross-fitted AIPW", "main-aipw", ""),
    ("Trimmed overlap, $\\bar m \\in [0.1, 0.9]$$^{a}$", "rob-trim", ""),
    ("Covariate set (a)$^{b}$", "rob-covsets", "covset_a_"),
    ("Covariate set (b)$^{b}$", "rob-covsets", "covset_b_"),
    ("Parametric nuisances", "rob-learners", "linear_"),
    ("Random-forest nuisances", "rob-learners", "rf_"),
    ("OLS coefficient (HC2)", "rob-estimators", "ols_"),
    ("Hajek IPW (bootstrap SE)", "rob-estimators", "ipw_"),
    ("Conditional DiD, re78 $-$ re74$^{c}$", "rob-diff74", ""),
]


def cell(run: str, m: dict, key: str, fmt: str) -> str:
    if key not in m or m[key] is None:
        return "--"
    if fmt == "p" and m[key] < 0.001:
        mac.direct += 1
        return "$<0.001$"
    return mac.cell(run, key, m[key], ".3f" if fmt == "p" else fmt)


def yesno(m: dict, key: str) -> str:
    return "--" if key not in m else ("yes" if m[key] else "no")


body = [r"\begin{tabular}{@{}l r r c c r r c c r@{}}", r"\toprule",
        r"Specification & Estimate & SE & 95\% CI & 90\% CI & $p$ & $p_{\mathrm{TOST}}$"
        r" & Rejects 0 & Within $\pm M$ & $n$ \\",
        r"\midrule",
        r"\multicolumn{10}{@{}l}{\emph{A. ATT of enrolment on 1978 earnings (nominal dollars)}} \\"]
n_rows = 0
for label, run, pre in ROWS:
    m = load_metrics(run)
    assert m["margin_M"] == M
    ci95 = f"[{cell(run, m, pre + 'ci_low', ',.0f')}, {cell(run, m, pre + 'ci_high', ',.0f')}]"
    ci90 = ("--" if pre + "ci90_low" not in m else
            f"[{cell(run, m, pre + 'ci90_low', ',.0f')}, {cell(run, m, pre + 'ci90_high', ',.0f')}]")
    body.append(" & ".join([
        label, cell(run, m, pre + "effect", ",.0f"), cell(run, m, pre + "se", ",.0f"), ci95, ci90,
        cell(run, m, pre + "p", "p"), cell(run, m, pre + "p_tost", "p"),
        yesno(m, pre + "h1_reject"), yesno(m, pre + "h1b_supported"),
        cell(run, m, pre + "n", ",.0f")]) + r" \\")
    n_rows += 1

s = load_metrics("select-re75")
body += [r"\midrule",
         r"\multicolumn{10}{@{}l}{\emph{B. Descriptive, not an estimate of the ATT: selection on the 1975 earnings shock$^{d}$}} \\",
         " & ".join([r"re75 given 1974 covariates", cell("select-re75", s, "effect", ",.0f"),
                     cell("select-re75", s, "se", ",.0f"),
                     f"[{cell('select-re75', s, 'ci_low', ',.0f')}, {cell('select-re75', s, 'ci_high', ',.0f')}]",
                     "--", "--", "--", "--", "--", cell("select-re75", s, "n", ",.0f")]) + r" \\",
         r"\midrule",
         r"\multicolumn{10}{@{}l}{Equivalence margin $M = \$" + mac.cell("main-aipw", "margin_M", M, ",.2f", math_mode=False)
         + r"$ (10\% of participants' mean 1975 earnings, fixed before any outcome was read).} \\",
         r"\bottomrule", r"\end{tabular}"]
write_tex(args.out, "code/tab_main.py", body)

write_metrics(args.metrics, {"n_rows_panel_a": n_rows, "n_rows_panel_b": 1,
                             "n_macro_cells": mac.used, "n_direct_cells": mac.direct, "margin_M": M})
