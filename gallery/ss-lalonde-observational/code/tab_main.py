"""Table: primary contrast (H1), H3 placebo, robustness estimates and H2 (descriptive).

Reads runs/main-aipw, placebo-re75, rob-trim, rob-learners, rob-covsets, rob-estimators,
rob-diff74 and h2-benchmark metrics.json only. Writes paper/tables/tab_main.tex, a bare
tabular (the Writer adds the float, caption and label).

Every number in the fragment is a claim macro from paper/numbers.tex. The macro names are
fixed below by (run, metric), following the claim ids of design.claim_ids; the script reads no
claim file, so it writes the metric value it read next to each row as a LaTeX comment, and a
separate check (outside the run) compares those values with the claims. The yes/no cells are
the runs' own logged flags; which rows can trigger the disagreement rule is the design's rule
(design.threats, DEV-11), written here as a constant and checked against the flags.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import load_metrics, write_metrics, write_tex  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_main.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

# (label, run, metric prefix, macro stem, can trigger, trigger flag)
ROB = [
    ("Control-only trimming$^{b}$", "rob-trim", "", "Trim", "yes", "triggers_abstract_statement"),
    ("Learners (a): parametric nuisances", "rob-learners", "linear_", "LearnerLinear", "yes",
     "linear_triggers_abstract_statement"),
    ("Learners (b): random forests", "rob-learners", "rf_", "LearnerRf", "yes", "rf_triggers_abstract_statement"),
    ("Covariate set (a): earnings-history core$^{c}$", "rob-covsets", "covset_a_", "CovsetA", "yes",
     "covset_a_triggers_abstract_statement"),
    ("Covariate set (b): single lag$^{c}$", "rob-covsets", "covset_b_", "CovsetB", "no", None),
    ("OLS coefficient on treat (HC2)", "rob-estimators", "ols_", "Ols", "no", None),
    ("Hajek IPW (bootstrap SE)", "rob-estimators", "ipw_", "Ipw", "yes$^{d}$", "ipw_triggers_abstract_statement"),
    ("Conditional DiD on re78 $-$ re74$^{e}$", "rob-diff74", "", "DiffSeventyfour", "no", "triggers_abstract_statement"),
]
# Estimate macro per row: the claim ids name OLS "ols-coef" (\OlsCoef); every other row "<stem>Effect".
EST = {"Ols": "OlsCoef"}


def m_(name: str) -> str:
    return f"${{\\{name}}}$"


def ci(stem: str) -> str:
    return f"[{m_(stem + 'CiLow')}, {m_(stem + 'CiHigh')}]"


def trace(run: str, m: dict, keys: list[str]) -> str:
    return "% " + run + ": " + ", ".join(f"{k} = {m[k]!r}" for k in keys)


main = load_metrics("main-aipw")
P = load_metrics("placebo-re75")
H2 = load_metrics("h2-benchmark")
assert H2["main_effect"] == main["effect"]
assert main["h1_holds"] is True

body = [r"\begin{tabular}{@{}l r c c c@{}}", r"\toprule",
        r" & & & \multicolumn{2}{c}{Disagreement rule$^{a}$} \\", r"\cmidrule(l){4-5}",
        r"Specification & Estimate & 95\% CI & Can trigger & Triggered \\",
        r"\midrule",
        r"\multicolumn{5}{@{}l}{\emph{A. Primary (H1): ATT contrast on 1978 earnings, all $\PrimaryNTreated$ treated men}} \\",
        trace("main-aipw", main, ["effect", "ci_low", "ci_high", "h1_holds"]),
        f"Cross-fitted AIPW, ten covariates & {m_('PrimaryEffect')} & {ci('Primary')} & \\multicolumn{{2}}{{c}}{{reference}} \\\\",
        r"\midrule",
        r"\multicolumn{5}{@{}l}{\emph{B. Placebo (H3): same estimator, outcome 1975 earnings, without re75 and u75}} \\",
        trace("placebo-re75", P, ["effect", "ci_low", "ci_high", "verdict", "ci_excludes_zero"])]
verdict = P["verdict"]
reason = " (CI excludes 0)" if P["ci_excludes_zero"] else ""
body.append(f"Placebo on re75 & {m_('PlaceboEffect')} & {ci('Placebo')} & \\multicolumn{{2}}{{c}}{{H3: {verdict}{reason}}} \\\\")
body += [r"\midrule",
         r"\multicolumn{5}{@{}l}{\emph{C. Robustness, outcome 1978 earnings (all reported; the primary is never replaced)}} \\"]
n_trig = 0
for label, run, pre, stem, can, flag in ROB:
    m = load_metrics(run)
    if can == "no":
        assert flag is None or m[flag] is False, f"{run}:{pre} cannot trigger but its flag is true"
        did = "--"
    else:
        did = "yes" if m[flag] else "no"
        n_trig += bool(m[flag])
    body.append(trace(run, m, [pre + "effect", pre + "ci_low", pre + "ci_high"] + ([flag] if flag else [])))
    body.append(f"{label} & {m_(EST.get(stem, stem + 'Effect'))} & {ci(stem)} & {can} & {did} \\\\")
body += [r"\midrule",
         r"\multicolumn{5}{@{}l}{\emph{D. H2, descriptive: primary minus the experimental benchmark}} \\",
         trace("h2-benchmark", H2, ["benchmark", "benchmark_se", "h2_diff", "h2_se_combined", "h2_ci_low", "h2_ci_high"]),
         f"Primary $-$ {m_('HTwoBenchmarkValue')} (SE {m_('HTwoBenchmarkSe')}) & {m_('HTwoDiff')} & "
         f"[{m_('HTwoCiLow')}, {m_('HTwoCiHigh')}]$^{{f}}$ & \\multicolumn{{2}}{{c}}{{no test}} \\\\",
         r"\bottomrule", r"\end{tabular}"]
write_tex(args.out, "code/tab_main.py", body)

write_metrics(args.metrics, {
    "n_rows": 1 + 1 + len(ROB) + 1, "n_rows_robustness": len(ROB),
    "n_rows_can_trigger": sum(1 for r in ROB if r[4] != "no"), "n_rows_triggered": n_trig,
    "placebo_verdict": verdict, "n_macro_cells": 1 + 2 * 3 + 3 * len(ROB) + 5,
})
