"""Run rob-ipow (conditional): inverse-probability-of-observation weighted AIPW ATT on re78.

Runs only if main-aipw's trigger fired (design.method.missing_outcomes, DEV-17): |share of
missing or inadmissible re78 among treated - among controls| > 0.02 (metric ipow_trigger in
runs/main-aipw/metrics.json). The script refuses to run otherwise. The adopted design specified
this run but ss-null-effect never wrote it (its trigger did not fire); this is written from the
adopted text, which is reproduced here.

R_i = 1 if re78 is observed and admissible (aipw_lib.admissible), else 0.
r(X, D) = P(R = 1 | X, D): LogisticRegressionCV with the primary settings on (treat, B(X)),
  cross-fitted on the primary folds (all 16,177 units, stratified on treat, seeds 20261118 + s),
  clipped below at 0.05.
m: the full-sample propensity of the primary fits (all units; covariates are never missing),
  clipped above at 0.99.
g0: HistGradientBoosting on T(X), fitted on the observed CPS men of the training folds.
theta_IPOW = sum_i (R_i / r_i) [D_i (Y_i - g0_i) - (1 - D_i) w_i (Y_i - g0_i)] / sum_i D_i,
  per repetition, mean-aggregated with the primary variance rule; SE from the influence
  function with r treated as known (aipw_lib.att_ipow_from_nuisances). Targets the full-sample
  ATT under MAR given X and treat. Changes the assumption: never triggers the disagreement rule.

Run from the workspace root:  .venv/bin/python -I code/rob_ipow.py
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/rob-ipow/metrics.json")
R_FLOOR = 0.05


def main() -> int:
    main_m = L.read_json(L.MAIN_METRICS)
    if not main_m.get("ipow_trigger", False):
        sys.exit("ERROR: the rob-ipow trigger did not fire in main-aipw; this run is not planned")
    df = L.load_covariates()
    L.check_basis_reuse(df)
    y = L.load_re78(df)
    R = L.admissible(y).astype(int)
    d = df["treat"].to_numpy(int)
    Xb = L.basis(df, L.COVS).to_numpy(float)
    Xt = L.tree_features(df, L.COVS)

    m_raw, n_conv_m = L.crossfit_propensity(Xb, d)
    XR = np.column_stack([d, Xb])
    r_raw, n_conv_r = L.crossfit_propensity(XR, d, make=L.propensity_learner, target=R)
    r = np.maximum(r_raw, R_FLOOR)
    g = L.crossfit_outcome(Xt, d, np.where(R == 1, y, 0.0), observed=R == 1)
    res = L.att_ipow_from_nuisances(d, y, R, r, m_raw, g)

    met = {"estimand": "ATT, all treated men, under MAR of re78 given X and treat",
           "seed_base": L.SEED, "r_floor": R_FLOOR,
           "n_observed": int(R.sum()), "n_observed_treated": int(R[d == 1].sum()),
           "n_observed_control": int(R[d == 0].sum()),
           "n_r_floored_unit_reps": int((r_raw < R_FLOOR).sum()),
           "n_convergence_warnings": int(n_conv_m + n_conv_r)}
    met.update(L.summarize(res))
    met.update(L.per_repetition(res))
    met.update(L.compare_with_main(met, "", main_m))
    met["triggers_abstract_statement"] = False  # never, by the fixed rule
    L.write_metrics(OUT, met)
    print({k: met[k] for k in ("effect", "se", "ci_low", "ci_high", "n_observed")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
