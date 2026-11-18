"""Run rob-covsets: primary estimator on re78 with two pre-fixed alternative conditioning sets.

(a) earnings-history core: age, educ, married, re74, re75, unemp74, unemp75
    (B: 11 terms; T: 7 columns). In the disagreement rule.
(b) single lag: every covariate except re74 and unemp74 (B: 14 terms; T: 12 columns).
    Changes the assumption; reported, never triggers.
Propensity and outcome models refitted for each set; same folds, repetitions and seeds.

Run from the workspace root:  .venv/bin/python -I code/rob_covsets.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/rob-covsets/metrics.json")
SETS = {
    "covset_a": ["age", "educ", "married", "re74", "re75", "unemp74", "unemp75"],
    "covset_b": [c for c in L.COVS if c not in ("re74", "unemp74")],
}


def main() -> int:
    df = L.load_data(["re78"])
    M = float(L.read_json(L.MARGIN_FILE)["margin_M"])
    main_m = L.read_json(L.MAIN_METRICS)
    df = df[L.admissible(df["re78"], "re78")].reset_index(drop=True)
    d = df["treat"].to_numpy(int)
    y = df["re78"].to_numpy(float)
    met = {"margin_M": M, "seed_base": L.SEED}
    for name, covs in SETS.items():
        Xb = L.basis(df, covs).to_numpy(float)
        Xt = L.tree_features(df, covs)
        res = L.aipw(d, y, Xb, Xt)
        p = f"{name}_"
        met[f"{p}covariates"] = ",".join(covs)
        met[f"{p}basis_n_terms"] = int(Xb.shape[1])
        met[f"{p}tree_n_columns"] = int(Xt.shape[1])
        met.update(L.summarize(res, p, M))
        met.update(L.compare_with_main(met, p, main_m))
    met["covset_a_triggers_abstract_statement"] = bool(
        met["covset_a_h1_differs_from_main"] or met["covset_a_h1b_differs_from_main"])
    L.write_metrics(OUT, met)
    print(met)
    return 0


if __name__ == "__main__":
    sys.exit(main())
