"""Table: Imbens (2003) sensitivity analysis: targets, diagonal R2*, and the nine benchmark
covariate groups with their |bias| and the reading-rule verdict for each target.

Reads runs/sens-imbens/metrics.json and claims.jsonl (macros). Writes
paper/tables/tab_sensitivity.tex. Verdicts are the run's own robust_<target>_<group>
booleans; nothing is recomputed.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import Macros, load_metrics, write_metrics, write_tex  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_sensitivity.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

R = "sens-imbens"
S = load_metrics(R)
mac = Macros()

TARGETS = [  # (key, label, meaning)
    ("margin", r"$t_M = M$", "shift that would move the estimate to the margin"),
    ("zero", r"$t_0$", r"shift that would move the nearer 95\% bound to zero (flips H1)"),
    ("equiv", r"$t_E$", r"shift that would end equivalence (90\% CI leaves $\pm M$)"),
]
# Groups dropped together from B(X), as design.method.sensitivity defines them.
GROUPS = [
    ("age", "age", r"age, age$^2$"), ("educ", "educ", r"educ, educ$^2$"),
    ("married", "married", "married"), ("urban", "urban", "urban"),
    ("region", "region", "3 region dummies"), ("children", "children", "children"),
    ("health", "health\\_limit", "health\\_limit"),
    ("earn74", "earnings74", r"re74, re74$^2$, unemp74"),
    ("earn75", "earnings75", r"re75, re75$^2$, unemp75"),
]


def c(key: str, fmt: str) -> str:
    return mac.cell(R, key, S[key], fmt)


body = [r"\begin{tabular}{@{}l l r r r c c c@{}}", r"\toprule",
        r"\multicolumn{8}{@{}l}{\emph{A. Targets and the diagonal breakdown point}} \\",
        r"\multicolumn{4}{@{}l}{Target} & Value (\$) & \multicolumn{3}{c}{$R^2_*$ ($R^2_D = R^2_Y$)} \\",
        r"\midrule"]
for k, lab, meaning in TARGETS:
    r2 = r"$> 0.30$" if S[f"r2star_{k}_out_of_grid"] else c(f"r2star_{k}", ".3f")
    body.append(rf"\multicolumn{{4}}{{@{{}}l}}{{{lab}: {meaning}}} & {c(f'target_{k}', ',.0f')}"
                rf" & \multicolumn{{3}}{{c}}{{{r2}}} \\")
body += [r"\midrule",
         r"\multicolumn{8}{@{}l}{\emph{B. Benchmark covariate groups (a confounder as strong as the group)}} \\",
         r" & & & & & \multicolumn{3}{c}{Robust for target} \\",
         r"\cmidrule(l){6-8}",
         r"Group & Terms dropped from $B(X)$ & $R^2_D$ & $R^2_Y$ & $|$bias$|$ (\$) & $t_M$ & $t_0$ & $t_E$ \\",
         r"\midrule"]
n_robust = {k: 0 for k, _, _ in TARGETS}
for key, name, terms in GROUPS:
    verdicts = []
    for k, _, _ in TARGETS:
        ok = S[f"robust_{k}_{key}"]
        n_robust[k] += int(ok)
        verdicts.append("yes" if ok else "no")
    body.append(" & ".join([name, terms, c(f"bench_{key}_r2d", ".3f"), c(f"bench_{key}_r2y", ".3f"),
                            c(f"bench_{key}_abs_bias", ",.0f")] + verdicts) + r" \\")
for k, _, _ in TARGETS:
    assert n_robust[k] == S[f"n_robust_{k}"], f"verdict count for {k} differs from the run"
body += [r"\midrule",
         r"\multicolumn{8}{@{}l}{U-free estimate in the Imbens model: $\tau(0,0) = " + c("tau00", ",.0f")[1:-1]
         + r"$ (equals the OLS coefficient);} \\",
         r"\multicolumn{8}{@{}l}{AIPW estimate " + mac.cell(R, "aipw_effect", S["aipw_effect"], ",.0f",
                                                         alt=(("main-aipw", "effect"),))
         + r"; residual SD of the U-free outcome model $\sigma_0 = " + c("sigma0", ",.0f")[1:-1] + r"$.} \\",
         r"\multicolumn{8}{@{}l}{$|$bias$|$ is computed within the Imbens model and transferred} \\",
         r"\multicolumn{8}{@{}l}{additively to the AIPW estimate as an approximation.} \\",
         r"\bottomrule", r"\end{tabular}"]
write_tex(args.out, "code/tab_sensitivity.py", body)

write_metrics(args.metrics, {"n_targets": len(TARGETS), "n_groups": len(GROUPS),
                             **{f"n_robust_{k}": v for k, v in n_robust.items()},
                             "n_macro_cells": mac.used, "n_direct_cells": mac.direct})
