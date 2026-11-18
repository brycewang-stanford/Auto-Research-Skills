"""Table: the secondary outcome family (H2) with unadjusted and Romano-Wolf p-values and
max-t simultaneous 95% intervals.

Reads runs/secondary-family/metrics.json and claims.jsonl (macros). Writes
paper/tables/tab_secondary.tex. The plan reports max-t intervals for this family; the
unadjusted per-outcome 95% intervals are deliberately not shown (results-r1 F3).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import Macros, load_metrics, write_metrics, write_tex  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_secondary.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

R = "secondary-family"
F = load_metrics(R)
mac = Macros()
assert F["family"] == "re79,employed78,hours78,benefits78,wellbeing78"

# Units as plan.json design.method.secondary_family states them; the brief documents
# no further meaning for these columns.
# (label, outcome key, metric suffix for effect/se/maxt, format)
ROWS = [
    ("re79 (nominal \\$)", "re79", "", ",.0f"),
    ("employed78 (percentage points)", "employed78", "_pp", ".1f"),
    ("hours78 (hours)", "hours78", "", ".1f"),
    ("benefits78 (nominal \\$)", "benefits78", "", ",.0f"),
    ("wellbeing78 (its own scale)$^{a}$", "wellbeing78", "", ".2f"),
]


def c(key: str, fmt: str) -> str:
    return mac.cell(R, key, F[key], fmt)


body = [r"\begin{tabular}{@{}l r r r r c c@{}}", r"\toprule",
        r"Outcome (unit) & Estimate & SE & $p$, unadjusted & $p$, Romano--Wolf"
        r" & Max-$t$ simultaneous 95\% interval & Detected \\",
        r"\midrule"]
for label, k, sfx, fmt in ROWS:
    body.append(" & ".join([
        label, c(f"{k}_effect{sfx}", fmt), c(f"{k}_se{sfx}", fmt),
        c(f"{k}_p_unadj", ".3f"), c(f"{k}_p_rw", ".3f"),
        f"[{c(f'{k}_maxt_low{sfx}', fmt)}, {c(f'{k}_maxt_high{sfx}', fmt)}]",
        "yes" if F[f"{k}_detected"] else "no"]) + r" \\")
body.append(" & ".join([
    r"\quad wellbeing78 (control-group SDs)$^{b}$", c("wellbeing78_effect_sd", ".3f"), "--",
    "--", "--", f"[{c('wellbeing78_maxt_low_sd', '.3f')}, {c('wellbeing78_maxt_high_sd', '.3f')}]",
    "--"]) + r" \\")
body += [r"\midrule",
         r"\multicolumn{7}{@{}l}{Max-$t$ critical value " + c("maxt_crit", ".3f")
         + r"; Gaussian multiplier bootstrap, " + c("n_bootstrap", ",.0f")
         + r" draws; outcomes detected (Romano--Wolf $p < 0.05$): " + c("n_detected", "d") + r".} \\",
         r"\bottomrule", r"\end{tabular}"]
write_tex(args.out, "code/tab_secondary.py", body)

write_metrics(args.metrics, {"n_outcomes": len(ROWS), "n_detected": F["n_detected"],
                             "n_macro_cells": mac.used, "n_direct_cells": mac.direct})
