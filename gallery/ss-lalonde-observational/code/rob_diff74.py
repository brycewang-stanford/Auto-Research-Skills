"""Run rob-diff74: conditional-DiD ATT on re78 - re74, time-invariant covariates only (DEV-15).

Adopted from gallery/ss-null-effect/code/rob_diff74.py (716b6c3); changes: the conditioning
set is this file's time-invariant covariates (age, educ, black, hisp, married, nodegree):
B 8 terms, T 6 columns; upper-only clip; no H1b.
Named estimand: the ATT under conditional parallel trends from each group's recorded 're74'
base period to 1978. Outcome Y = re78 - re74 (complete cases of re78; re74 is never missing).
Base-period caveat (F2): for CPS men re74 is calendar-1974 earnings; for NSW men earnings
13-24 months before random assignment, overlapping 1975 for later assignees and zero for every
man assigned after April 1976 by the DW sample rule, so the base is not the same calendar
period in the two groups. The primary estimator otherwise (propensity and outcome models
re-fitted; same folds, repetitions, seeds). Changes the assumption and the estimand: reported,
never triggers the disagreement rule, never a defence of the primary.

Run from the workspace root:  .venv/bin/python -I code/rob_diff74.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/rob-diff74/metrics.json")


def main() -> int:
    df = L.load_covariates()
    main_m = L.read_json(L.MAIN_METRICS)
    y78 = L.load_re78(df)
    ok = L.admissible(y78)
    df, y78 = df[ok].reset_index(drop=True), y78[ok]
    d = df["treat"].to_numpy(int)
    y = y78 - df["re74"].to_numpy(float)
    Xb = L.basis(df, L.TIME_INVARIANT).to_numpy(float)
    Xt = L.tree_features(df, L.TIME_INVARIANT)
    res = L.aipw(d, y, Xb, Xt)
    met = {"estimand": "ATT on re78 - re74 under conditional parallel trends (group-specific re74 base period)",
           "conditioning_set": ",".join(L.TIME_INVARIANT), "basis_n_terms": int(Xb.shape[1]),
           "tree_n_columns": int(Xt.shape[1]), "seed_base": L.SEED}
    met.update(L.summarize(res))
    met.update(L.per_repetition(res))
    met.update(L.compare_with_main(met, "", main_m))
    met["kish_ess_controls"] = res["kish_ess_controls"]
    met["max_control_weight"] = res["max_control_weight"]
    met["triggers_abstract_statement"] = False  # never, by the fixed rule
    L.write_metrics(OUT, met)
    print({k: met[k] for k in ("effect", "se", "ci_low", "ci_high", "n_clipped_units")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
