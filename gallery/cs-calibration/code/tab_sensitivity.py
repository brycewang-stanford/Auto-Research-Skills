"""Tables: the pre-specified sensitivity analyses (run `tab-sensitivity`). None changes a verdict.

Reads runs/h-tests/metrics.json (H1 on the debiased ECE, and phoneme's main H2 rows),
runs/sens-ncal/metrics.json (isotonic refitted on 1,351 calibration rows),
runs/sens-elec-time/metrics.json (electricity, chronological split) and runs/describe/metrics.json
(electricity's random-split levels, for comparison). Writes
  paper/tables/tab_sensitivity.tex  Panel A: H1 recomputed on the debiased ECE of Kumar et al.
                                    (2019), descriptive. Panel B: H2a and H2b with isotonic fitted
                                    on 1,351 calibration rows, per dataset.
  paper/tables/tab_elec_time.tex    Panel C: electricity under the chronological split, levels of
                                    ECE, Brier and AUC per model and calibrator, beside the
                                    random-split ECE and Brier. Drift, not a leakage test.
"""
from __future__ import annotations

import argparse

from analyze import CATEGORY, HYPOTHESES, OVERALL
from figlib import (CAL_TEX, CALIBRATORS, DATASETS, MODEL_TEX, MODELS, NAME, Cells, ds_key,
                    load_metrics, write_metrics, write_tex)

ap = argparse.ArgumentParser()
ap.add_argument("--out-tests", default="paper/tables/tab_sensitivity.tex")
ap.add_argument("--out-elec", default="paper/tables/tab_elec_time.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

H, N, T, D = "h-tests", "sens-ncal", "sens-elec-time", "describe"
M = {r: load_metrics(r) for r in (H, N, T, D)}
assert M[H]["n_seeds"] == 10 and M[D]["n_seeds"] == 10
assert M[N]["n_rows"] == 90 and M[T]["n_rows"] == 90
C = Cells(M)
CAT_SHORT = {0: "no difference", 1: "holds", 2: "contradicted", 3: "inconclusive"}
assert set(CAT_SHORT) == set(CATEGORY)
NCAL = int(C.value(N, "n_cal_sub"))
C.raw.append(f"{N}:n_cal_sub:,d")


def row(run: str, prefix: str, name: str) -> str:
    code = C.word(run, prefix + "_cat")
    return " & ".join([r"\quad " + name, C.macro(run, prefix + "_mean"),
                       f"[{C.macro(run, prefix + '_lo')}, {C.macro(run, prefix + '_hi')}]",
                       CAT_SHORT[code]]) + r" \\"


def head(hid: str, what: str) -> str:
    metric, treat, comp, sign, margin, _ = HYPOTHESES[hid]
    side = "$>0$" if sign > 0 else "$<0$"
    return (rf"\multicolumn{{4}}{{@{{}}l}}{{{what}: {MODEL_TEX[treat[0]]} {CAL_TEX[treat[1]]} minus "
            rf"{MODEL_TEX[comp[0]]} {CAL_TEX[comp[1]]}; predicted {side}; margin $\pm{margin:g}$}} \\")


# --- Panels A and B -------------------------------------------------------------------------
body = [r"\begin{tabular}{@{}l r c l@{}}",
        r"\toprule",
        r"Dataset & Mean difference & 95\% paired $t(9)$ interval & Category \\",
        r"\midrule",
        r"\multicolumn{4}{@{}l}{\emph{Panel A. H1 on the debiased ECE (descriptive; never changes H1)}} \\",
        head("h1db", "Debiased ECE")]
n_rows = 0
for d in DATASETS:
    body.append(row(H, f"h1db_{ds_key(d)}", NAME[d]))
    n_rows += 1
v = C.word(H, "h1db_overall_code")
assert OVERALL[v] == M[H]["h1db_overall"]
body.append(rf"\multicolumn{{4}}{{@{{}}l}}{{\quad Same k-of-4 rule, descriptive: \emph{{{OVERALL[v]}}}}} \\")
body += [r"\addlinespace",
         rf"\multicolumn{{4}}{{@{{}}l}}{{\emph{{Panel B. H2a and H2b with isotonic fitted on {NCAL:,} "
         r"calibration rows (per dataset; no verdict)}} \\"]
for hid, label in (("h2a", "H2a, Brier score"), ("h2b", "H2b, Brier score")):
    body.append(head(hid, label))
    for d in DATASETS:
        if d == "phoneme":
            # phoneme's calibration split already has 1,351 rows: its main row is reused
            body.append(row(H, f"{hid}_{ds_key(d)}", NAME[d] + " (main run)"))
        else:
            body.append(row(N, f"{hid}_ncal_{ds_key(d)}", NAME[d]))
        n_rows += 1
body += [r"\bottomrule", r"\end{tabular}"]
write_tex(args.out_tests, "code/tab_sensitivity.py", body, C.footer())
n_macros_tests = len(C.macros)

# --- Panel C ----------------------------------------------------------------------------------
C2 = Cells(M)
E = [r"\begin{tabular}{@{}l l r r r r r@{}}",
     r"\toprule",
     r" & & \multicolumn{3}{c}{Chronological split} & \multicolumn{2}{c}{Random split (main)} \\",
     r"\cmidrule(lr){3-5}\cmidrule(l){6-7}",
     r"Model & Calibrator & ECE & Brier & AUC & ECE & Brier \\",
     r"\midrule"]
for j, model in enumerate(MODELS):
    if j:
        E.append(r"\addlinespace[2pt]")
    for k, cal in enumerate(CALIBRATORS):
        t = f"electricity_time_{model}_{cal}"
        r = f"electricity_{model}_{cal}"

        def ms(run: str, base: str, metric: str) -> str:
            return rf"{C2.macro(run, f'{base}_{metric}_mean')} {{\footnotesize ({C2.macro(run, f'{base}_{metric}_sd')})}}"

        E.append(" & ".join([MODEL_TEX[model] if k == 0 else "", CAL_TEX[cal],
                             ms(T, t, "ece"), ms(T, t, "brier"), ms(T, t, "auc"),
                             ms(D, r, "ece"), ms(D, r, "brier")]) + r" \\")
        n_rows += 1
E += [r"\bottomrule", r"\end{tabular}"]
write_tex(args.out_elec, "code/tab_sensitivity.py", E, C2.footer())

write_metrics(args.metrics, {"n_rows": n_rows, "n_macro_cells": n_macros_tests + len(C2.macros),
                             "n_plain_cells": len(C.raw) + len(C2.raw),
                             "checksum_values": sum(C.values) + sum(C2.values)})
print(f"rows {n_rows}, macros {n_macros_tests + len(C2.macros)}, plain {len(C.raw) + len(C2.raw)}")
