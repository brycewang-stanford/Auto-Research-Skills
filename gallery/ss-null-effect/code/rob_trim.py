"""Run rob-trim: trimmed-overlap ATT on re78 (a separate estimand; Crump et al. 2009).

m_bar = mean over the five repetitions of the unclipped out-of-fold propensity from the
primary propensity fits (refitted here with the identical code and seeds, and checked
against runs/diag-overlap/propensity.csv). Kept units: 0.1 <= m_bar <= 0.9. The full primary
estimator is re-run on the kept units (folds re-drawn on them with the same seeds,
propensity and outcome models refitted); the trimmed set is treated as fixed for the SE.
H1 and H1b decisions on the trimmed estimate are compared with main-aipw (disagreement rule).

Run from the workspace root:  .venv/bin/python -I code/rob_trim.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/rob-trim/metrics.json")
DIAG_PROP = Path("runs/diag-overlap/propensity.csv")


def main() -> int:
    df = L.load_data(["re78"])
    L.check_basis_reuse(df)
    M = float(L.read_json(L.MARGIN_FILE)["margin_M"])
    main_m = L.read_json(L.MAIN_METRICS)
    ok = L.admissible(df["re78"], "re78")
    df = df[ok].reset_index(drop=True)

    d = df["treat"].to_numpy(int)
    m_bar = L.crossfit_propensity(L.basis(df, L.COVS).to_numpy(float), d).mean(axis=0)
    diag = pd.read_csv(DIAG_PROP)
    max_diff = float(np.max(np.abs(diag["m_bar"].to_numpy() - m_bar))) if len(diag) == len(df) else float("nan")
    keep = (m_bar >= 0.1) & (m_bar <= 0.9)
    sub = df[keep].reset_index(drop=True)

    ds = sub["treat"].to_numpy(int)
    res = L.aipw(ds, sub["re78"].to_numpy(float), L.basis(sub, L.COVS).to_numpy(float),
                 L.tree_features(sub, L.COVS))
    met = {"estimand": "ATT among units with m_bar in [0.1, 0.9]", "margin_M": M,
           "max_abs_diff_mbar_vs_diag_overlap": max_diff,
           "n_dropped": int((~keep).sum()), "n_dropped_treated": int((~keep & (d == 1)).sum()),
           "n_dropped_control": int((~keep & (d == 0)).sum())}
    met.update(L.summarize(res, "", M))
    met["n_control"] = int(len(ds) - ds.sum())
    met.update(L.compare_with_main(met, "", main_m))
    met["triggers_abstract_statement"] = bool(met["h1_differs_from_main"] or met["h1b_differs_from_main"])
    L.write_metrics(OUT, met)
    print(met)
    return 0


if __name__ == "__main__":
    sys.exit(main())
