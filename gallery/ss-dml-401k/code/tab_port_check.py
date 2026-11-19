"""Table: the pre-gate port check per learner (synthetic outcome; analysis plan 0).

Reads runs/check-learner-ports/metrics.json (the data-prep run on 10 synthetic units built
from the real covariates) and runs/verdict/metrics.json (which copied the shift, its SE, the
port and seed RMS and the pass flag; those cells are claim macros). Writes
paper/tables/tab_port_check.tex. All dollar amounts are synthetic-outcome dollars, not
real-data dollars and not tolerances (design.check_learner_ports.scale_limitation).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import LEARNERS, NAME, Macros, load_metrics, macro_name, write_metrics, write_tex  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_port_check.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

mac = Macros()
p = load_metrics("check-learner-ports")
v = load_metrics("verdict")


def cor(value: float) -> str:
    """Minimum correlation to 4 decimals; a value that would round to 1 is shown as >0.9999."""
    if value >= 0.99995:
        mac.direct += 1
        return r"$>$0.9999"
    return mac.raw(value, ".4f")


def dollars_raw(value: float, learner: str) -> str:
    """Synthetic-outcome dollars at the precision of the port-shift claims (lasso ,.2f; others
    ,.1f), so that two different numbers never print alike."""
    return "$" + mac.raw(value, ",.2f" if learner == "lasso" else ",.1f") + "$"


counts = {"n_rows": 0, "n_pass": 0, "n_fail": 0}
body = [r"\begin{tabular}{@{}l rr r rr r cc c@{}}",
        r"\toprule",
        r"\multicolumn{10}{@{}l}{\emph{Synthetic-outcome dollars: " + mac.raw(p["n_units"], ".0f")
        + r" synthetic units, true $\theta = " + mac.raw(p["theta_true"], ",.0f")
        + r"$, 2-fold, $\geq " + mac.raw(p["train_size_min"], ",.0f") + r"$ training rows}} \\",
        r"\midrule",
        r" & \multicolumn{2}{c}{Mean $\hat\theta$} & & \multicolumn{2}{c}{RMS of $\hat\theta$ gap}"
        r" & & \multicolumn{2}{c}{Min.\ correlation$^{b}$} & \\",
        r"\cmidrule(lr){2-3}\cmidrule(lr){5-6}\cmidrule(lr){8-9}",
        r"Learner & Python & R (seed A) & Shift (SE)$^{a}$ & Port & Seed$^{c}$"
        r" & Max $|$gap$|$ & $\hat\ell$ & $\hat m$ & Result \\",
        r"\midrule"]

for learner in LEARNERS:
    # verdict copied these from the port-check run; the table quotes the verdict's macros.
    assert v[f"port_shift_{learner}"] == p[f"shift_{learner}"]
    assert v[f"port_shift_se_{learner}"] == p[f"shift_se_{learner}"]
    assert v[f"port_rms_{learner}"] == p[f"rms_port_{learner}"]
    assert v[f"port_rms_seed_{learner}"] == p[f"rms_seed_{learner}"]
    assert v[f"port_pass_{learner}"] == p[f"pass_{learner}"]

    shift = mac.use(macro_name("PortShift", learner), "verdict", f"port_shift_{learner}",
                    v[f"port_shift_{learner}"])
    shift_se = mac.use(macro_name("PortShiftSe", learner), "verdict", f"port_shift_se_{learner}",
                       v[f"port_shift_se_{learner}"])
    sign = "+" if v[f"port_shift_{learner}"] > 0 else ""
    rms = mac.use(macro_name("PortRms", learner), "verdict", f"port_rms_{learner}",
                  v[f"port_rms_{learner}"])
    rms_seed = mac.use(macro_name("PortRmsSeed", learner), "verdict", f"port_rms_seed_{learner}",
                       v[f"port_rms_seed_{learner}"])
    ok = v[f"port_pass_{learner}"]
    counts["n_pass" if ok else "n_fail"] += 1
    result = "pass" if ok else r"\textbf{FAIL}$^{d}$"
    row = [NAME[learner],
           dollars_raw(p[f"theta_py_mean_{learner}"], learner),
           dollars_raw(p[f"theta_ra_mean_{learner}"], learner),
           f"${sign}{shift}$ (${shift_se}$)",
           f"${rms}$", f"${rms_seed}$",
           dollars_raw(p[f"max_abs_port_{learner}"], learner),
           f"{cor(p[f'cor_l_min_{learner}'])} ({cor(p[f'cor_l_min_seed_{learner}'])})",
           f"{cor(p[f'cor_m_min_{learner}'])} ({cor(p[f'cor_m_min_seed_{learner}'])})",
           result]
    body.append(" & ".join(row) + r" \\")
    counts["n_rows"] += 1

body += [r"\bottomrule", r"\end{tabular}"]
assert counts["n_rows"] == 5 and counts["n_pass"] + counts["n_fail"] == 5
assert counts["n_pass"] == p["n_pass"]
write_tex(args.out, "code/tab_port_check.py", body, mac.footer())
write_metrics(args.metrics, {**counts, "n_macro_cells": len(mac.sources), "n_direct_cells": mac.direct})
print(f"wrote {args.out}: {counts['n_rows']} rows, {len(mac.sources)} macro cells, {mac.direct} direct")
