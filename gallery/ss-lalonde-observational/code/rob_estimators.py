"""Run rob-estimators: (a) OLS with HC2 SE and (b) normalized (Hajek) IPW ATT, on re78 (DEV-14).

Adopted from gallery/ss-null-effect/code/rob_estimators.py (716b6c3); changes: the 14-term
B(X) (DEV-2), upper-only clip at 0.99 (DEV-5), no H1b, H1 decision ci_low > 0.
(a) OLS of re78 on treat and B(X) (14 terms plus intercept: 16 regressors), HC2 SE
    (statsmodels); labelled a regression coefficient, not an ATT. Changes the estimand:
    never triggers the disagreement rule.
(b) Hajek IPW ATT: propensity LogisticRegression (L2, lbfgs) on B(X) standardized, with C
    fixed at the value LogisticRegressionCV (the primary propensity learner, inner-CV seed
    20261118) picks on the full sample; fitted in-sample on all units; m clipped above at
    0.99; theta = mean(Y | D = 1) - sum_{D=0} w Y / sum_{D=0} w, w = m / (1 - m).
    SE: nonparametric bootstrap, 999 draws of n units with replacement (unstratified, so the
    treated count varies), numpy default_rng(20261120), propensity re-fitted (same fixed C)
    in each draw; SE = SD of the draws (ddof = 1); 95% CI = theta +/- 1.959964 SE (and the
    percentile interval, for information). In the disagreement rule only through its point
    estimate: triggers the abstract statement if it lies outside main-aipw's 95% CI.

Run from the workspace root:  .venv/bin/python -I code/rob_estimators.py
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/rob-estimators/metrics.json")
B_IPW = 999
IPW_SEED = 20261120


def hajek(d: np.ndarray, y: np.ndarray, X: np.ndarray, C: float) -> tuple[float, int]:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        m_raw = make_pipeline(StandardScaler(), LogisticRegression(C=C, solver="lbfgs", max_iter=10_000)) \
            .fit(X, d).predict_proba(X)[:, 1]
    m = np.minimum(m_raw, L.CLIP_HI)
    w = m / (1 - m)
    c = d == 0
    theta = y[d == 1].mean() - np.sum(w[c] * y[c]) / np.sum(w[c])
    return float(theta), int((m_raw > L.CLIP_HI).sum())


def ols_hc2(d: np.ndarray, y: np.ndarray, Xb: np.ndarray):
    W = sm.add_constant(np.column_stack([d, Xb]), has_constant="add")
    return sm.OLS(y, W).fit(cov_type="HC2"), W.shape[1]


def main() -> int:
    df = L.load_covariates()
    L.check_basis_reuse(df)
    main_m = L.read_json(L.MAIN_METRICS)
    y = L.load_re78(df)
    ok = L.admissible(y)
    df, y = df[ok].reset_index(drop=True), y[ok]
    d = df["treat"].to_numpy(int)
    Xb = L.basis(df, L.COVS).to_numpy(float)
    n = len(d)
    met = {}

    # (a) OLS, HC2.
    fit, k = ols_hc2(d, y, Xb)
    b, se = float(fit.params[1]), float(fit.bse[1])
    met.update({"ols_effect": b, "ols_se": se, "ols_ci_low": b - L.Z95 * se,
                "ols_ci_high": b + L.Z95 * se, "ols_p": float(fit.pvalues[1]), "ols_n": n,
                "ols_n_regressors": int(k)})
    met["ols_h1_holds"] = L.h1_holds(met["ols_ci_low"])
    met["ols_effect_outside_main_ci95"] = bool(b < main_m["ci_low"] or b > main_m["ci_high"])

    # (b) Hajek IPW.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", FutureWarning)
        C = float(np.ravel(L.propensity_learner(L.SEED).fit(Xb, d)[-1].C_)[0])
    theta, n_clip = hajek(d, y, Xb, C)
    rng = np.random.default_rng(IPW_SEED)
    draws = np.empty(B_IPW)
    n1_draws = np.empty(B_IPW, dtype=int)
    for b_i in range(B_IPW):
        idx = rng.integers(0, n, n)
        draws[b_i] = hajek(d[idx], y[idx], Xb[idx], C)[0]
        n1_draws[b_i] = int(d[idx].sum())
    se_ipw = float(draws.std(ddof=1))
    met.update({
        "ipw_C": C, "ipw_effect": theta, "ipw_se": se_ipw,
        "ipw_ci_low": theta - L.Z95 * se_ipw, "ipw_ci_high": theta + L.Z95 * se_ipw,
        "ipw_pct_ci_low": float(np.quantile(draws, 0.025)),
        "ipw_pct_ci_high": float(np.quantile(draws, 0.975)),
        "ipw_n": n, "ipw_n_treated": int(d.sum()), "ipw_n_clipped": n_clip,
        "ipw_n_bootstrap": B_IPW, "ipw_bootstrap_seed": IPW_SEED,
        "ipw_bootstrap_n_treated_min": int(n1_draws.min()),
        "ipw_bootstrap_n_treated_max": int(n1_draws.max()),
    })
    met["ipw_h1_holds"] = L.h1_holds(met["ipw_ci_low"])
    met["ipw_h1_differs_from_main"] = bool(met["ipw_h1_holds"] != main_m["h1_holds"])
    met["ipw_effect_outside_main_ci95"] = bool(theta < main_m["ci_low"] or theta > main_m["ci_high"])
    met["ipw_triggers_abstract_statement"] = met["ipw_effect_outside_main_ci95"]
    L.write_metrics(OUT, met)
    print({k: met[k] for k in ("ols_effect", "ols_ci_low", "ols_ci_high", "ipw_effect", "ipw_ci_low",
                               "ipw_ci_high", "ipw_triggers_abstract_statement")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
