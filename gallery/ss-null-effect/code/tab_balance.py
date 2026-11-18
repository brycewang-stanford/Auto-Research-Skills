"""Table: covariate balance before and after ATT weighting, and overlap summary.

Reads data/derived/prep_metrics.json (arm means, written by the data-prep run
prepare-covariates), runs/diag-overlap/metrics.json (unweighted and ATT-weighted SMDs for
every term of B(X), overlap counts) and claims.jsonl (macros). Writes
paper/tables/tab_balance.tex. Nothing is re-estimated.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import Macros, load_json, load_metrics, write_metrics, write_tex  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_balance.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

P = load_json("data/derived/prep_metrics.json")
D = load_metrics("diag-overlap")
mac = Macros()
R = "diag-overlap"
EARN = {"re74", "re75"}

# (label, covariate key in prep_metrics or None for a squared term, B(X) term in diag-overlap)
ROWS = [
    ("Age", "age", "age"), (r"Age$^2$", None, "age_sq"),
    ("Years of schooling (educ)", "educ", "educ"), (r"educ$^2$", None, "educ_sq"),
    ("Married", "married", "married"), ("Urban", "urban", "urban"),
    ("Number of children", "children", "children"), ("Health limitation", "health_limit", "health_limit"),
    ("Earnings 1974 (re74, \\$)", "re74", "re74"), (r"re74$^2$", None, "re74_sq"),
    ("Earnings 1975 (re75, \\$)", "re75", "re75"), (r"re75$^2$", None, "re75_sq"),
    ("No earnings in 1974 (unemp74)", "unemp74", "unemp74"),
    ("No earnings in 1975 (unemp75)", "unemp75", "unemp75"),
    ("Region: northeast", "region_northeast", "region_northeast"),
    ("Region: south", "region_south", "region_south"),
    ("Region: west", "region_west", "region_west"),
    ("Region: midwest (reference)$^{a}$", "region_midwest", "region_midwest"),
]


def mean_cell(key: str | None, arm: str) -> str:
    if key is None:
        return "--"
    fmt = ",.0f" if key in EARN else ".2f"
    return f"${format(P[f'{key}_mean_{arm}'], fmt)}$"


body = [r"\begin{tabular}{@{}l r r r r@{}}", r"\toprule",
        r" & \multicolumn{2}{c}{Mean} & \multicolumn{2}{c}{Standardized difference} \\",
        r"\cmidrule(lr){2-3}\cmidrule(l){4-5}",
        r"Covariate (term of $B(X)$) & Treated & Controls & Unweighted & ATT-weighted \\",
        r"\midrule"]
for label, key, term in ROWS:
    su, sw = D[f"smd_unweighted_{term}"], D[f"smd_w_{term}"]
    if key is not None:
        assert abs(P[f"{key}_std_diff"] - su) < 1e-9, f"{key}: prep and diag-overlap SMDs differ"
    body.append(" & ".join([label, mean_cell(key, "t"), mean_cell(key, "c"),
                            mac.cell(R, f"smd_unweighted_{term}", su, ".3f"),
                            mac.cell(R, f"smd_w_{term}", sw, ".3f")]) + r" \\")
body.append(r"\midrule")
body.append(r"Number of people & " + mac.cell(R, "n_treated", D["n_treated"], ",.0f",
                                                alt=(("main-aipw", "n_treated"),))
            + " & " + mac.cell(R, "n_control", D["n_control"], ",.0f", alt=(("main-aipw", "n_control"),))
            + r" & & \\")
body += [r"\midrule", r"\multicolumn{5}{@{}l}{\emph{Overlap of the cross-fitted propensity score $\bar m(X)$}} \\"]
OVER = [
    (r"Largest $|$ATT-weighted standardized difference$|$ (term: " + D["smd_w_max_abs_term"] + ")",
     "smd_w_max_abs", ".3f", ()),
    (r"Treated with $\bar m > 0.9$", "n_treated_above_09", ",.0f", ()),
    (r"Controls with $\bar m < 0.1$", "n_control_below_01", ",.0f", ()),
    (r"Share of all people with $\bar m$ outside $[0.1, 0.9]$", "share_all_outside_01_09", ".3f",
     (("main-aipw", "share_all_outside_01_09"),)),
    (r"Units with a propensity clipped at $[0.01, 0.99]$", "n_clipped_units", ",.0f",
     (("main-aipw", "n_clipped_units"),)),
    (r"Range of $\bar m$, treated", None, None, ()),
    (r"Range of $\bar m$, controls", None, None, ()),
    ("Kish effective sample size of the weighted controls", "kish_ess_controls", ",.0f", ()),
    ("Largest control weight $w$$^{b}$", "max_control_weight", ".1f", ()),
]
for label, key, fmt, alt in OVER:
    if key is None:
        arm = "treated" if "treated" in label else "control"
        val = f"$[{D[f'm_bar_min_{arm}']:.3f}, {D[f'm_bar_max_{arm}']:.3f}]$"
    else:
        val = mac.cell(R, key, D[key], fmt, alt=alt)
    body.append(rf"\multicolumn{{4}}{{@{{}}l}}{{{label}}} & {val} \\")
body += [r"\bottomrule", r"\end{tabular}"]
write_tex(args.out, "code/tab_balance.py", body)

write_metrics(args.metrics, {"n_covariate_rows": len(ROWS), "n_overlap_rows": len(OVER),
                             "n_macro_cells": mac.used, "n_direct_cells": mac.direct,
                             "max_abs_smd_weighted": D["smd_w_max_abs"]})
