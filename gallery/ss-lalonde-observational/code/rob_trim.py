"""Run rob-trim: control-only trimming to the treated propensity range (design.method.control_only_trimming).

Adopted from gallery/ss-null-effect/code/rob_trim.py (716b6c3) with DEV-6: the adopted rule
kept units with m_bar in [0.1, 0.9] (dropping treated units); here no treated man is dropped,
and a CPS man is dropped iff his m_bar lies outside [min, max] of m_bar over the 185 treated
men (aipw_lib.trim_keep; bounds inclusive). The estimand stays the ATT for all treated men.

m_bar = mean over the five repetitions of the unclipped out-of-fold propensity from the
primary propensity fits (re-fitted here with the identical pre-gate code and seeds on the
primary analysis sample, and compared with runs/diag-overlap/propensity.csv and with the
trimming count diag-overlap recorded). The full primary estimator is then re-run on the kept
units (folds re-drawn on them with the same seeds, propensity and outcome models re-fitted);
the kept set is treated as fixed for the SE.

What it checks (design-r1 F3): whether re-fitting m and g0 on the kept CPS men moves the
estimate; it does not test reliance on the dropped CPS men. In the disagreement rule: the
abstract statement is triggered iff the H1 decision (ci_low > 0) differs from main-aipw's.

Run from the workspace root:  .venv/bin/python -I code/rob_trim.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/rob-trim/metrics.json")


def main() -> int:
    df = L.load_covariates()
    L.check_basis_reuse(df)
    main_m = L.read_json(L.MAIN_METRICS)
    diag_m = L.read_json(L.DIAG_METRICS)
    y_all = L.load_re78(df)
    ok = L.admissible(y_all)
    df = df[ok].reset_index(drop=True)
    y_all = y_all[ok]

    d = df["treat"].to_numpy(int)
    m_raw, _ = L.crossfit_propensity(L.basis(df, L.COVS).to_numpy(float), d)
    m_bar = m_raw.mean(axis=0)
    met = {"estimand": "ATT for all treated men; CPS men outside the treated m_bar range dropped",
           "seed_base": L.SEED}
    if len(df) == diag_m["n"]:
        diag = pd.read_csv(L.DIAG_PROP)
        met["max_abs_diff_mbar_vs_diag_overlap"] = float(np.max(np.abs(diag["m_bar"].to_numpy() - m_bar)))
    keep = L.trim_keep(m_bar, d)
    lo, hi = float(m_bar[d == 1].min()), float(m_bar[d == 1].max())
    sub = df[keep].reset_index(drop=True)
    ds = sub["treat"].to_numpy(int)
    res = L.aipw(ds, y_all[keep], L.basis(sub, L.COVS).to_numpy(float), L.tree_features(sub, L.COVS))

    met.update({
        "trim_m_bar_low": lo, "trim_m_bar_high": hi,
        "n_treated_dropped": int((~keep & (d == 1)).sum()),
        "n_control_dropped": int((~keep & (d == 0)).sum()),
        "n_control_dropped_below": int(((d == 0) & (m_bar < lo)).sum()),
        "n_control_dropped_above": int(((d == 0) & (m_bar > hi)).sum()),
        "n_control_kept": int(((d == 0) & keep).sum()),
    })
    met["n_control_dropped_matches_diag_overlap"] = bool(
        met["n_control_dropped"] == diag_m["trim_n_control_dropped"])
    met.update(L.summarize(res))
    met.update(L.per_repetition(res))
    met["kish_ess_controls"] = res["kish_ess_controls"]
    met["max_control_weight"] = res["max_control_weight"]
    met.update(L.compare_with_main(met, "", main_m))
    met["triggers_abstract_statement"] = bool(met["h1_differs_from_main"])
    L.write_metrics(OUT, met)
    print({k: met[k] for k in ("effect", "se", "ci_low", "ci_high", "n_control_kept",
                               "n_control_dropped", "h1_holds", "triggers_abstract_statement")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
