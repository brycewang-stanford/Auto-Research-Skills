"""Run main-aipw: primary ATT of treat on re78 (plan.json design.analysis_plan, H1 and H1b).

Estimator: cross-fitted AIPW ATT (code/aipw_lib.py), propensity LogisticRegressionCV on B(X)
(reused from code/diag_overlap.py), outcome HistGradientBoosting on T(X), 5 folds x 5
repetitions, seeds 20261118 + s. Complete cases under design.method.outcome_validity
(0 values are missing or inadmissible per the pre-gate runs; the script recomputes this).

H1:  95% CI = theta +/- 1.959964 SE; reject iff it excludes 0.
H1b: M = margin_M of data-prep run `margin` (read from data/derived/margin_metrics.json);
     p_TOST = max(1 - Phi((theta + M)/SE), Phi((theta - M)/SE)); supported iff p_TOST < 0.05,
     equivalently the 90% CI inside (-M, M); smallest satisfied margin max(|lo90|, |hi90|).
Relative effect: r = theta / (mu1 - theta), delta-method CI from the joint influence functions
     psi_r = [mu1 psi_theta - theta psi_mu] / (mu1 - theta)^2, psi_mu = D (Y - mu1) / pi_hat,
     psi_theta = psi_bar (mean over repetitions).
Overlap shares: m_bar = mean over repetitions of the unclipped out-of-fold propensity; also
     compared with runs/diag-overlap/propensity.csv (the same fits, run before the gate).

Run from the workspace root:  .venv/bin/python -I code/main_aipw.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/main-aipw/metrics.json")
DIAG_PROP = Path("runs/diag-overlap/propensity.csv")


def main() -> int:
    df = L.load_data(["re78"])
    L.check_basis_reuse(df)
    M = float(L.read_json(L.MARGIN_FILE)["margin_M"])
    ok = L.admissible(df["re78"], "re78")
    n_dropped_t = int((~ok & (df.treat == 1)).sum())
    n_dropped_c = int((~ok & (df.treat == 0)).sum())
    sub = df[ok].reset_index(drop=True)

    d = sub["treat"].to_numpy(int)
    y = sub["re78"].to_numpy(float)
    Xb = L.basis(sub, L.COVS).to_numpy(float)
    Xt = L.tree_features(sub, L.COVS)
    res = L.aipw(d, y, Xb, Xt)

    met = {"outcome": "re78", "estimand": "ATT, full sample (complete cases)",
           "margin_M": M, "seed_base": L.SEED, "n_folds": L.K, "n_repetitions": L.S}
    met.update(L.summarize(res, "", M))
    met["n_control"] = int(len(d) - d.sum())
    met["n_dropped_treated"] = n_dropped_t
    met["n_dropped_control"] = n_dropped_c
    met["effect_over_M"] = res["theta"] / M
    for s in range(L.S):
        met[f"theta_rep{s}"] = float(res["thetas"][s])
        met[f"se_rep{s}"] = float(res["ses"][s])
    met["se_psi_bar"] = float(np.sqrt(np.mean(res["psi_bar"] ** 2) / len(d)))

    # Relative effect and counterfactual mean.
    pi = d.mean()
    mu1 = float(y[d == 1].mean())
    th = res["theta"]
    cf = mu1 - th
    psi_mu = d * (y - mu1) / pi
    psi_r = (mu1 * res["psi_bar"] - th * psi_mu) / cf ** 2
    se_r = float(np.sqrt(np.mean(psi_r ** 2) / len(d)))
    r = th / cf
    met.update({
        "treated_mean": mu1, "cf_mean": cf,
        "rel_effect": r, "rel_se": se_r,
        "rel_ci_low": r - L.Z95 * se_r, "rel_ci_high": r + L.Z95 * se_r,
        "rel_effect_pct": 100 * r,
        "rel_ci_low_pct": 100 * (r - L.Z95 * se_r), "rel_ci_high_pct": 100 * (r + L.Z95 * se_r),
        "control_mean_raw": float(y[d == 0].mean()),
    })

    # Overlap, from the primary propensity fits.
    m_bar = res["m_raw"].mean(axis=0)
    met["share_all_outside_01_09"] = float(np.mean((m_bar < 0.1) | (m_bar > 0.9)))
    met["n_all_outside_01_09"] = int(np.sum((m_bar < 0.1) | (m_bar > 0.9)))
    met["share_treated_above_09"] = float(np.mean(m_bar[d == 1] > 0.9))
    met["share_clipped_units"] = res["n_clipped_units"] / len(d)
    met["rule_O1_pass"] = bool(met["share_treated_above_09"] <= 0.05)
    met["rule_O2_pass"] = bool(met["share_clipped_units"] <= 0.01)
    if len(d) == len(df):
        diag = pd.read_csv(DIAG_PROP)
        met["max_abs_diff_mbar_vs_diag_overlap"] = float(np.max(np.abs(diag["m_bar"].to_numpy() - m_bar)))

    met.update(L.echo_counts(["re78"]))
    L.write_metrics(OUT, met)
    print({k: met[k] for k in ("effect", "se", "ci_low", "ci_high", "ci90_low", "ci90_high",
                               "p", "p_tost", "h1_reject", "h1b_supported", "min_margin")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
