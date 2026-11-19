"""Table: published vs replicated estimates for the 10 cells, with the H2 reading.

Reads runs/main-<learner>/metrics.json (replicated estimate, bracketed and adjusted SE,
80%-power detectable shift) and runs/verdict/metrics.json (published estimate and SEs,
difference, tolerance, testability, H2 status, pre-gate port-check result). Writes
paper/tables/tab_side_by_side.tex. Every number is a claim macro; nothing is computed here
except the sign shown in front of a positive difference.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import (FOLDS, LEARNERS, NAME, Macros, cell_key, load_metrics,  # noqa: E402
                    macro_name, write_metrics, write_tex)

STATUS_PASS = "pass"
STATUS_NT_INSIDE = "inside the tolerance, not testable at this resolution"

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_side_by_side.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

mac = Macros()
v = load_metrics("verdict")
counts = {"n_rows": 0, "n_pass": 0, "n_not_testable_inside": 0, "n_outside": 0,
          "n_port_failed_rows": 0}


def m(quantity: str, run: str, metric: str, value, learner: str, k: int) -> str:
    return "$" + mac.use(macro_name(quantity, learner, k), run, metric, value) + "$"


body = [r"\begin{tabular}{@{}l c rr rr rr rrr l l@{}}",
        r"\toprule",
        r" & & \multicolumn{2}{c}{Estimate} & \multicolumn{2}{c}{Bracketed SE}"
        r" & \multicolumn{2}{c}{Adjusted SE} & & & & & Port check \\",
        r"\cmidrule(lr){3-4}\cmidrule(lr){5-6}\cmidrule(lr){7-8}",
        r"Learner & $K$ & Publ. & Repl. & Publ. & Repl. & Publ. & Repl."
        r" & Repl.\ $-$ publ. & Tolerance & MDS$_{80}$ & H2 reading & (pre-gate) \\",
        r"\midrule"]

for li, learner in enumerate(LEARNERS):
    run = f"main-{learner}"
    r = load_metrics(run)
    port_ok = v[f"port_pass_{learner}"]
    assert isinstance(port_ok, bool)
    for k in FOLDS:
        c = cell_key(learner, k)
        # The verdict copied the replicated cell from the main run; they must agree exactly.
        assert v[f"rep_theta_{c}"] == r[f"theta_k{k}"]
        assert v[f"rep_se_med_{c}"] == r[f"se_med_k{k}"]
        assert v[f"rep_se_adj_{c}"] == r[f"se_adj_k{k}"]
        assert v[f"tolerance_{c}"] == r[f"tolerance_k{k}"]
        assert abs(v[f"diff_{c}"] - r[f"diff_k{k}"]) < 1e-9

        diff = v[f"diff_{c}"]
        sign = "+" if diff > 0 else ""
        diff_cell = "$" + sign + mac.use(macro_name("Diff", learner, k), "verdict", f"diff_{c}", diff) + "$"

        status, inside, testable = v[f"h2_status_{c}"], v[f"h2_inside_{c}"], v[f"testable_{c}"]
        if not inside:
            reading = "outside: " + (v[f"h2_reading_{c}"] or "see text")
            counts["n_outside"] += 1
        elif testable:
            assert status == STATUS_PASS, status
            reading = r"pass$^{b}$"
            counts["n_pass"] += 1
        else:
            assert status == STATUS_NT_INSIDE, status
            reading = r"inside, not testable$^{a}$"
            counts["n_not_testable_inside"] += 1

        port = "pass" if port_ok else r"\textbf{failed}$^{c}$"
        counts["n_port_failed_rows"] += 0 if port_ok else 1
        label = NAME[learner] if k == FOLDS[0] else ""
        row = [label, str(k),
               m("PubTheta", "verdict", f"pub_theta_{c}", v[f"pub_theta_{c}"], learner, k),
               m("Theta", run, f"theta_k{k}", r[f"theta_k{k}"], learner, k),
               m("PubSeMed", "verdict", f"pub_se_med_{c}", v[f"pub_se_med_{c}"], learner, k),
               m("SeMed", run, f"se_med_k{k}", r[f"se_med_k{k}"], learner, k),
               m("PubSeAdj", "verdict", f"pub_se_adj_{c}", v[f"pub_se_adj_{c}"], learner, k),
               m("SeAdj", run, f"se_adj_k{k}", r[f"se_adj_k{k}"], learner, k),
               diff_cell,
               m("Tol", "verdict", f"tolerance_{c}", v[f"tolerance_{c}"], learner, k),
               m("Mds", run, f"mds80_k{k}", r[f"mds80_k{k}"], learner, k),
               reading, port]
        body.append(" & ".join(row) + r" \\")
        counts["n_rows"] += 1
    if li < len(LEARNERS) - 1:
        body.append(r"\addlinespace")

body += [r"\bottomrule", r"\end{tabular}"]
assert counts["n_rows"] == 10
write_tex(args.out, "code/tab_side_by_side.py", body, mac.footer())
write_metrics(args.metrics, {**counts, "n_macro_cells": len(mac.sources), "n_direct_cells": mac.direct})
print(f"wrote {args.out}: {counts['n_rows']} rows, {len(mac.sources)} macro cells, {mac.direct} direct")
