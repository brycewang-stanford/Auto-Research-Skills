"""Run main-aipw: primary ATT of treat on re78 (plan.json design.analysis_plan; H1).

Adopted from gallery/ss-null-effect/code/main_aipw.py at commit 716b6c3 (sha256 230b7b08...7bf4);
changes are those of plan.json design.method.deviations only: no margin M and no H1b (DEV-9),
no 90% interval, the H1 decision is 'ci_low > 0' (DEV-11), upper-only clip (DEV-5), re78
counts made here (DEV-10), and re78 joined from data/raw by method.join_rule.

This is the first analysis run and the ONLY run that reads data/raw: it joins re78 (field 10)
to the outcome-free working file by the row key (src, row), checks fields 1-9 against the
working file exactly (aipw_lib.join_re78_from_raw), and writes the joined outcome to
data/derived/re78_by_key.csv (src, row, re78) for the later runs.

Estimator: cross-fitted AIPW ATT (code/aipw_lib.py); propensity LogisticRegressionCV on B(X)
(14 terms; diag_overlap.crossfit, the pre-gate code); outcome HistGradientBoosting on T(X)
(10 columns), CPS men of the training folds only; 5 folds x 5 repetitions, seeds 20261118 + s;
m clipped above at 0.99. Complete cases under design.method.outcome_validity: missing and
inadmissible re78 values are counted by arm; if any exist the full estimator is re-run on the
complete cases (folds re-drawn with the same seeds, denominator = observed treated).

H1: 95% CI = theta +/- 1.959964 SE; H1 holds iff ci_low > 0. p = 2 (1 - Phi(|theta| / SE)).
Relative effect: r = theta / (mu1 - theta), delta-method CI (aipw_lib.relative_effect).
Overlap: m_bar = mean over repetitions of the unclipped out-of-fold propensity; share of
treated with m_bar > 0.9 (O1), share of units clipped (O2), Kish ESS of the weighted controls,
largest control weight; m_bar compared with runs/diag-overlap/propensity.csv (same fits).
code-r1 F3: on the full sample the run STOPS (exit 1) if any unit's refitted m_bar differs from
diag-overlap's by more than 1e-12 + 1e-9 m_bar (the CSV holds 12 significant digits), because
the pre-gate rules B1/O1/O2 and the trimming count were fixed on those fits.
rob-ipow trigger (design.method.missing_outcomes, DEV-17): |share unobserved among treated -
share unobserved among controls| > 0.02, from counts only.

Run from the workspace root:  .venv/bin/python -I code/main_aipw.py
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/main-aipw/metrics.json")
IPOW_GAP = 0.02


def main() -> int:
    df = L.load_covariates()
    L.check_basis_reuse(df)
    y_all = L.join_re78_from_raw(df)
    L.write_re78(df, y_all)

    d_all = df["treat"].to_numpy(int)
    counts = L.outcome_counts(y_all, d_all, "re78")
    ok = L.admissible(y_all)
    sub = df[ok].reset_index(drop=True)
    d = sub["treat"].to_numpy(int)
    y = y_all[ok]
    Xb = L.basis(sub, L.COVS).to_numpy(float)
    Xt = L.tree_features(sub, L.COVS)
    res = L.aipw(d, y, Xb, Xt)

    met = {"outcome": "re78", "units": "1982 dollars",
           "estimand": "ATT, all NSW-treated men with admissible re78 (complete cases)",
           "seed_base": L.SEED, "n_folds": L.K, "n_repetitions": L.S, "clip_upper": L.CLIP_HI,
           "propensity_basis": "B(X)", "propensity_basis_n_terms": int(Xb.shape[1]),
           "tree_n_columns": int(Xt.shape[1]), "n_rows_joined": int(len(df))}
    met.update(L.summarize(res))
    met.update(L.per_repetition(res))
    met["se_psi_bar"] = float(np.sqrt(np.mean(res["psi_bar"] ** 2) / len(d)))
    met["n_clipped_unit_reps"] = res["n_clipped_unit_reps"]
    met["n_convergence_warnings"] = res["n_convergence_warnings"]
    met.update(L.relative_effect(d, y, res))
    met["control_mean_raw"] = float(y[d == 0].mean())

    # Overlap, from the primary propensity fits.
    m_bar = res["m_raw"].mean(axis=0)
    met["share_treated_above_09"] = float(np.mean(m_bar[d == 1] > 0.9))
    met["n_treated_above_09"] = int(np.sum(m_bar[d == 1] > 0.9))
    met["share_clipped_units"] = res["n_clipped_units"] / len(d)
    met["rule_O1_pass"] = bool(met["share_treated_above_09"] <= 0.05)
    met["rule_O2_pass"] = bool(met["share_clipped_units"] <= 0.01)
    met["kish_ess_controls"] = res["kish_ess_controls"]
    met["max_control_weight"] = res["max_control_weight"]
    met["m_bar_min_treated"] = float(m_bar[d == 1].min())
    met["m_bar_max_treated"] = float(m_bar[d == 1].max())
    if len(d) == len(df):
        diag = pd.read_csv(L.DIAG_PROP)
        if not diag[L.KEY].equals(sub[L.KEY]):
            sys.exit("ERROR: runs/diag-overlap/propensity.csv row keys differ from the working file")
        chk = L.mbar_check(diag["m_bar"].to_numpy(), m_bar)
        met["max_abs_diff_mbar_vs_diag_overlap"] = chk["max_abs_diff"]
        met["n_mbar_outside_tol_vs_diag_overlap"] = chk["n_outside_tol"]
        met["mbar_matches_diag_overlap"] = chk["ok"]
        if not chk["ok"]:
            L.write_metrics(OUT, met)
            sys.exit(f"ERROR: refitted propensities differ from diag-overlap's for {chk['n_outside_tol']} "
                     f"units (max abs diff {chk['max_abs_diff']:.3g}; tolerance 1e-12 + 1e-9 m_bar); "
                     "the gate's diagnostics would not describe the fits used. Stopping (code-r1 F3).")
    else:
        met["mbar_matches_diag_overlap"] = "not applicable: complete-case subsample, folds re-drawn"

    # Outcome counts by arm and the rob-ipow trigger (counts only).
    met.update(counts)
    gap = abs(counts["share_unobserved_re78_treated"] - counts["share_unobserved_re78_control"])
    met["unobserved_share_gap"] = float(gap)
    met["ipow_trigger"] = bool(gap > IPOW_GAP)
    met["n_dropped_treated"] = counts["unobserved_re78_treated"]
    met["n_dropped_control"] = counts["unobserved_re78_control"]

    L.write_metrics(OUT, met)
    print({k: met[k] for k in ("effect", "se", "ci_low", "ci_high", "p", "h1_holds", "n",
                               "n_clipped_units", "ipow_trigger")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
