"""Run post-results-derived: arithmetic on logged run outputs only, for claim traceability (results-r2 F6).

POST-RESULTS DIAGNOSTIC, written after the results gate at the PI's instruction. It fits no model,
reads no data file and re-estimates nothing. Inputs (all recorded outputs of earlier runs):
  runs/main-aipw/metrics.json, runs/rob-trim/metrics.json, runs/diag-overlap/propensity.csv.
Outputs (flat metrics):
  - main-aipw single-repetition 95% bounds theta_rep_s -/+ 1.959964 se_rep_s, s = 0..4, and the
    number of repetitions whose interval includes zero (the primary rule uses the mean over
    repetitions; these are descriptive);
  - rob-trim minus main-aipw, and the min and max of rob-trim's per-repetition estimates;
  - the share of the CPS control weight m_bar / (1 - m_bar) (unclipped m_bar from
    diag-overlap's propensity.csv, as in plan.json design.method.control_only_trimming)
    carried by the CPS men rob-trim drops (m_bar below rob-trim's logged lower cutoff
    trim_m_bar_low or above trim_m_bar_high); the count is checked against rob-trim's.

Run from the workspace root:  .venv/bin/python -I code/post_results_derived.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm

OUT = Path("runs/post-results-derived/metrics.json")
Z95 = float(norm.ppf(0.975))
S = 5


def main() -> int:
    m = json.loads(Path("runs/main-aipw/metrics.json").read_text())
    t = json.loads(Path("runs/rob-trim/metrics.json").read_text())
    prop = pd.read_csv("runs/diag-overlap/propensity.csv")
    met = {"label": "post-results diagnostic: arithmetic on logged run outputs; no model fitted"}

    n_incl = 0
    for s in range(S):
        lo = m[f"theta_rep{s}"] - Z95 * m[f"se_rep{s}"]
        hi = m[f"theta_rep{s}"] + Z95 * m[f"se_rep{s}"]
        met[f"main_rep{s}_ci_low"] = lo
        met[f"main_rep{s}_ci_high"] = hi
        n_incl += int(lo <= 0 <= hi)
    met["main_n_reps_ci_include_zero"] = n_incl
    met["main_n_reps"] = S
    if not np.isclose(np.mean([m[f"theta_rep{s}"] for s in range(S)]), m["effect"], rtol=1e-12):
        sys.exit("ERROR: main-aipw per-repetition estimates do not average to its effect")

    met["trim_minus_main"] = t["effect"] - m["effect"]
    reps = [t[f"theta_rep{s}"] for s in range(S)]
    met["trim_rep_min"] = float(min(reps))
    met["trim_rep_max"] = float(max(reps))

    c = prop[prop["treat"] == 0]["m_bar"].to_numpy(float)
    w = c / (1 - c)
    dropped = (c < t["trim_m_bar_low"]) | (c > t["trim_m_bar_high"])
    if int(dropped.sum()) != t["n_control_dropped"]:
        sys.exit("ERROR: dropped count differs from rob-trim's")
    met["trim_dropped_weight"] = float(w[dropped].sum())
    met["control_weight_total"] = float(w.sum())
    met["trim_dropped_weight_share_pct"] = 100 * met["trim_dropped_weight"] / met["control_weight_total"]

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(met, indent=2) + "\n")
    print(met)
    return 0


if __name__ == "__main__":
    sys.exit(main())
