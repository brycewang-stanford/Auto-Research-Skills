"""Run rob-diff74: conditional-DiD ATT on re78 - re74, time-invariant covariates only.

Named estimand: the ATT under conditional parallel trends from 1974 to 1978. Outcome
Y = re78 - re74; conditioning set (age, educ, married, urban, region, children,
health_limit): B 11 terms, T 10 columns; the primary estimator otherwise (propensity and
outcome models refitted; same folds, repetitions, seeds). Changes the assumption: reported,
never triggers the disagreement rule. Its expected bias has no known sign (plan.json).

Run from the workspace root:  .venv/bin/python -I code/rob_diff74.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/rob-diff74/metrics.json")
TIME_INVARIANT = ["age", "educ", "married", "urban", "region", "children", "health_limit"]


def main() -> int:
    df = L.load_data(["re78"])
    M = float(L.read_json(L.MARGIN_FILE)["margin_M"])
    main_m = L.read_json(L.MAIN_METRICS)
    df = df[L.admissible(df["re78"], "re78")].reset_index(drop=True)
    d = df["treat"].to_numpy(int)
    y = (df["re78"] - df["re74"]).to_numpy(float)
    Xb = L.basis(df, TIME_INVARIANT).to_numpy(float)
    Xt = L.tree_features(df, TIME_INVARIANT)
    res = L.aipw(d, y, Xb, Xt)
    met = {"estimand": "ATT on re78 - re74 under conditional parallel trends 1974-1978",
           "conditioning_set": ",".join(TIME_INVARIANT), "basis_n_terms": int(Xb.shape[1]),
           "tree_n_columns": int(Xt.shape[1]), "margin_M": M, "seed_base": L.SEED}
    met.update(L.summarize(res, "", M))
    met.update(L.compare_with_main(met, "", main_m))
    L.write_metrics(OUT, met)
    print(met)
    return 0


if __name__ == "__main__":
    sys.exit(main())
