"""Outcome-blind overlap and balance diagnostics (plan.json design.method.overlap_and_balance).

Adopted from gallery/ss-null-effect/code/diag_overlap.py (sha256 235d2ecb...acf5) with the
adaptations listed in plan.json design.method.deviations, and nothing else changed:
  DEV-1  ten covariates: age, educ, black, hisp, married, nodegree, re74, re75, u74, u75.
  DEV-2  B(X), 14 terms: continuous covariates (age, educ, re74, re75) linear and squared,
         binaries linear, no interactions, standardized within each training fold.
  DEV-4  B+(X), escalation basis: B(X) plus all pairwise products of the ten covariates,
         dropping products that are constant or identical to a column already present
         (re74 x u74, re75 x u75, black x hisp are identically zero): 56 terms.
  DEV-5  upper clip only: m is clipped above at 0.99 before weights are formed; no floor.
         A unit is "clipped" if its raw out-of-fold m exceeds 0.99 in any repetition.
  DEV-6  rob-trim count: CPS men whose m_bar lies outside [min, max] of m_bar over the 185
         treated men (m_bar unclipped, from the primary full-sample fits); no treated man
         is ever dropped.
  DEV-7  folds, repetitions, seeds unchanged.

Input: data/derived/analysis_noRE78.csv only (row key src/row, treat, the ten covariates).
It refuses to run if an re78 column exists, never opens data/raw/, and never builds or fits
anything on the placebo's conditioning set X- (X without re75 and u75): every basis here
contains re75 and u75 (plan.json design_constraints).

Propensity (design.method.propensity_learner, cross_fitting), unchanged from the adopted code:
  - StandardScaler + LogisticRegressionCV on the basis, L2, Cs = 10 values log-spaced on
    [1e-4, 1e4], inner StratifiedKFold(5, shuffle, random_state = seed of the repetition),
    scoring neg_log_loss, solver lbfgs, max_iter 10000;
  - K = 5 outer StratifiedKFold on treat (shuffle), S = 5 repetitions, random_state
    20261118 + s, s = 0..4; out-of-fold predictions m_s,i.
  - m_bar_i = mean over repetitions of the unclipped out-of-fold m_s,i.
  scikit-learn 1.9.1 FutureWarnings (l1_ratios, legacy attributes) are silenced with a
  warnings filter only; no argument of the learner is changed, so the fit is unchanged.

Reported (definitions as in the adopted code):
  (a) nd_raw_<x>: normalized difference (x1 - x0) / sqrt(s1^2 + s0^2), unweighted, for the
      ten covariates; |nd| > 0.25 flagged, no action.
  (b) smd_w_<term>: ATT-weighted SMD for every term of B(X),
      (x1 - x0_w) / sqrt((s1^2 + s0^2) / 2), controls weighted by w = m / (1 - m) with m the
      clipped propensity of each repetition, averaged over repetitions; s1, s0 unweighted
      group SDs (ddof = 1). smd_w_rep_max_abs: largest |SMD| over repetitions taken
      separately (informational).
  (c) propensity histogram by treat: runs/<id>/propensity_hist.json, 20 bins of 0.05 on m_bar
      and, because 1.1% of units are treated, 0.5-wide bins on log10(m_bar) (allowed by
      the design).
  (d) share of treated with m_bar > 0.9; clipped units and unit-repetition pairs; Kish
      effective sample size of the weighted controls (sum w)^2 / sum w^2; largest control
      weight; number of CPS men rob-trim removes.

Decision rules (fixed in plan.json before this run):
  B1: every weighted |SMD| over the 14 terms of B(X) < 0.10. If B1 fails with B(X), B+(X)
      replaces B(X) once (run diag-overlap-ext, this script with --basis Bplus) and is final.
  O1: share of treated with m_bar > 0.9 <= 5%.
  O2: share of all units clipped (raw m > 0.99 in any repetition) <= 1%.

Seeds: outer folds and inner CV use 20261118 + s (s = 0..4); nothing else is random.

Run from the workspace root:
    .venv/bin/python -I code/diag_overlap.py                 # run diag-overlap, basis B(X)
    .venv/bin/python -I code/diag_overlap.py --basis Bplus   # run diag-overlap-ext, B+(X)
"""

import argparse
import itertools
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

DATA = Path("data/derived/analysis_noRE78.csv")
SEED = 20261118
K, S = 5, 5
CLIP_HI = 0.99
B1_MAX_ABS_SMD = 0.10
O1_MAX_SHARE_TREATED_ABOVE_09 = 0.05
O2_MAX_SHARE_CLIPPED = 0.01
ND_FLAG = 0.25
COVS = ["age", "educ", "black", "hisp", "married", "nodegree", "re74", "re75", "u74", "u75"]
CONTINUOUS = ("age", "educ", "re74", "re75")
EXPECTED_DROPPED_PRODUCTS = {"black_x_hisp", "re74_x_u74", "re75_x_u75"}
N_TERMS_B, N_TERMS_BPLUS = 14, 56


def load() -> pd.DataFrame:
    header = list(pd.read_csv(DATA, nrows=0).columns)
    if any(c.lower() == "re78" for c in header):
        sys.exit(f"ERROR: {DATA} contains an re78 column; refusing to run")
    df = pd.read_csv(DATA, usecols=["src", "row", "treat"] + COVS)
    if df[["treat"] + COVS].isna().any().any():
        sys.exit("ERROR: missing values in treatment or covariates")
    if not ((df.u74 == (df.re74 == 0)).all() and (df.u75 == (df.re75 == 0)).all()):
        sys.exit("ERROR: u74/u75 do not equal 1[re74 = 0]/1[re75 = 0]")
    return df


def basis_B(df: pd.DataFrame) -> pd.DataFrame:
    """B(X): 14 terms in the order of design.method.covariate_bases (DEV-2)."""
    cols: dict[str, pd.Series] = {}
    for c in COVS:
        cols[c] = df[c]
        if c in CONTINUOUS:
            cols[f"{c}_sq"] = df[c] ** 2
    out = pd.DataFrame(cols).astype(float)
    if set(("re75", "u75")) - set(out.columns):
        sys.exit("ERROR: basis lacks re75/u75 (placebo conditioning set is not allowed here)")
    return out


def basis_Bplus(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """B+(X): B(X) plus pairwise products of the ten covariates, dropping constant or
    duplicate columns (DEV-4). Returns the basis and the names of the dropped products."""
    out = basis_B(df)
    dropped = []
    for a, b in itertools.combinations(COVS, 2):
        name = f"{a}_x_{b}"
        p = df[a].to_numpy(float) * df[b].to_numpy(float)
        if np.all(p == p[0]) or any(np.array_equal(p, out[c].to_numpy()) for c in out.columns):
            dropped.append(name)
            continue
        out[name] = p
    return out, dropped


def propensity_learner(seed: int):
    """design.method.propensity_learner (unchanged from the adopted code)."""
    return make_pipeline(StandardScaler(), LogisticRegressionCV(
        Cs=np.logspace(-4, 4, 10), cv=StratifiedKFold(5, shuffle=True, random_state=seed),
        scoring="neg_log_loss", solver="lbfgs", max_iter=10_000))


def folds(d: np.ndarray, s: int):
    return list(StratifiedKFold(K, shuffle=True, random_state=SEED + s).split(np.zeros(len(d)), d))


def crossfit(X: np.ndarray, d: np.ndarray):
    """Out-of-fold propensity, shape (S, n), unclipped; chosen C per fit; fold treated counts."""
    m = np.zeros((S, len(d)))
    chosen_C, n1_test, n_conv_warn = [], [], 0
    for s in range(S):
        for tr, te in folds(d, s):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ConvergenceWarning)
                warnings.simplefilter("ignore", FutureWarning)
                fit = propensity_learner(SEED + s).fit(X[tr], d[tr])
            n_conv_warn += sum(issubclass(w.category, ConvergenceWarning) for w in caught)
            for w in caught:
                if not issubclass(w.category, ConvergenceWarning):
                    warnings.warn_explicit(w.message, w.category, w.filename, w.lineno)
            m[s, te] = fit.predict_proba(X[te])[:, 1]
            chosen_C.append(float(np.ravel(fit[-1].C_)[0]))
            n1_test.append(int(d[te].sum()))
    return m, np.array(chosen_C), np.array(n1_test), n_conv_warn


def wsmd(x: np.ndarray, d: np.ndarray, w: np.ndarray) -> float:
    x1, x0 = x[d == 1], x[d == 0]
    denom = np.sqrt((x1.var(ddof=1) + x0.var(ddof=1)) / 2)
    if denom == 0:
        return 0.0
    w0 = w[d == 0]
    return float((x1.mean() - np.sum(w0 * x0) / np.sum(w0)) / denom)


def main() -> int:
    warnings.simplefilter("ignore", FutureWarning)
    ap = argparse.ArgumentParser()
    ap.add_argument("--basis", choices=["B", "Bplus"], default="B")
    args = ap.parse_args()
    run_id = "diag-overlap" if args.basis == "B" else "diag-overlap-ext"
    outdir = Path("runs") / run_id

    df = load()
    d = df["treat"].to_numpy(int)
    n, n1 = len(d), int(d.sum())
    XB = basis_B(df)
    if XB.shape[1] != N_TERMS_B:
        sys.exit(f"ERROR: B(X) has {XB.shape[1]} terms, design says {N_TERMS_B}")
    if args.basis == "B":
        Xprop, dropped = XB, []
    else:
        Xprop, dropped = basis_Bplus(df)
        if Xprop.shape[1] != N_TERMS_BPLUS or set(dropped) != EXPECTED_DROPPED_PRODUCTS:
            sys.exit(f"ERROR: B+(X) has {Xprop.shape[1]} terms, dropped {dropped}; design says "
                     f"{N_TERMS_BPLUS} terms, dropped {sorted(EXPECTED_DROPPED_PRODUCTS)}")

    m_raw, chosen_C, n1_test, n_conv_warn = crossfit(Xprop.to_numpy(float), d)
    m_clip = np.minimum(m_raw, CLIP_HI)
    m_bar = m_raw.mean(axis=0)
    clipped_pairs = m_raw > CLIP_HI
    clipped_units = clipped_pairs.any(axis=0)

    # ATT weights for controls: mean over repetitions of m/(1-m) with the clipped m.
    w_rep = m_clip / (1 - m_clip)
    w = w_rep.mean(axis=0)
    w0 = w[d == 0]
    kish = float(w0.sum() ** 2 / np.sum(w0 ** 2))

    metrics: dict = {
        "run_id": run_id,
        "covariate_source": str(DATA),
        "propensity_basis": "B+(X)" if args.basis == "Bplus" else "B(X)",
        "propensity_basis_n_terms": int(Xprop.shape[1]),
        "propensity_basis_dropped_products": ",".join(dropped),
        "propensity_model": "StandardScaler + LogisticRegressionCV L2 lbfgs, Cs=logspace(-4,4,10), "
                            "inner StratifiedKFold(5, shuffle, seed of repetition), neg_log_loss, max_iter 10000",
        "fallback_Bplus_fired": bool(args.basis == "Bplus"),
        "seed_base": SEED,
        "seeds": ",".join(str(SEED + s) for s in range(S)),
        "n_folds": K, "n_repetitions": S,
        "clip_upper": CLIP_HI, "clip_lower": "none",
        "n": n, "n_treated": n1, "n_control": n - n1,
        "treated_per_test_fold_min": int(n1_test.min()),
        "treated_per_test_fold_max": int(n1_test.max()),
        "propensity_C_min": float(chosen_C.min()),
        "propensity_C_median": float(np.median(chosen_C)),
        "propensity_C_max": float(chosen_C.max()),
        "n_convergence_warnings": int(n_conv_warn),
    }

    # (a) unweighted normalized differences, ten covariates.
    flagged = []
    for c in COVS:
        x = df[c].to_numpy(float)
        x1, x0 = x[d == 1], x[d == 0]
        nd = float((x1.mean() - x0.mean()) / np.sqrt(x1.var(ddof=1) + x0.var(ddof=1)))
        metrics[f"nd_raw_{c}"] = nd
        if abs(nd) > ND_FLAG:
            flagged.append(c)
    metrics["nd_raw_n_flagged"] = len(flagged)
    metrics["nd_raw_flagged"] = ",".join(flagged)

    # (b) ATT-weighted SMDs for every term of B(X).
    b_terms = list(XB.columns)
    smd = {c: wsmd(XB[c].to_numpy(), d, w) for c in b_terms}
    smd_unw = {c: wsmd(XB[c].to_numpy(), d, np.ones(n)) for c in b_terms}
    for c in b_terms:
        metrics[f"smd_unweighted_{c}"] = smd_unw[c]
    for c in b_terms:
        metrics[f"smd_w_{c}"] = smd[c]
    worst = max(b_terms, key=lambda c: abs(smd[c]))
    metrics["smd_w_max_abs"] = abs(smd[worst])
    metrics["smd_w_max_abs_term"] = worst
    metrics["smd_w_n_terms_ge_010"] = int(sum(abs(smd[c]) >= B1_MAX_ABS_SMD for c in b_terms))
    metrics["smd_w_terms_ge_010"] = ",".join(c for c in b_terms if abs(smd[c]) >= B1_MAX_ABS_SMD)
    metrics["smd_w_rep_max_abs"] = float(max(
        abs(wsmd(XB[c].to_numpy(), d, w_rep[s])) for s in range(S) for c in b_terms))

    # (d) overlap.
    mb1, mb0 = m_bar[d == 1], m_bar[d == 0]
    lo, hi = float(mb1.min()), float(mb1.max())
    trim_below, trim_above = int(np.sum(mb0 < lo)), int(np.sum(mb0 > hi))
    metrics["share_treated_above_09"] = float(np.mean(mb1 > 0.9))
    metrics["n_treated_above_09"] = int(np.sum(mb1 > 0.9))
    metrics["n_clipped_units"] = int(clipped_units.sum())
    metrics["n_clipped_treated"] = int(clipped_units[d == 1].sum())
    metrics["n_clipped_control"] = int(clipped_units[d == 0].sum())
    metrics["share_clipped_units"] = float(clipped_units.mean())
    metrics["n_clipped_unit_reps"] = int(clipped_pairs.sum())
    metrics["kish_ess_controls"] = kish
    metrics["max_control_weight"] = float(w0.max())
    metrics["max_control_weight_any_rep"] = float(w_rep[:, d == 0].max())
    metrics["sum_control_weight"] = float(w0.sum())
    metrics["m_bar_min_treated"] = lo
    metrics["m_bar_median_treated"] = float(np.median(mb1))
    metrics["m_bar_max_treated"] = hi
    metrics["m_bar_min_control"] = float(mb0.min())
    metrics["m_bar_median_control"] = float(np.median(mb0))
    metrics["m_bar_max_control"] = float(mb0.max())
    metrics["trim_n_control_dropped"] = trim_below + trim_above
    metrics["trim_n_control_dropped_below"] = trim_below
    metrics["trim_n_control_dropped_above"] = trim_above
    metrics["trim_n_control_kept"] = int(len(mb0) - trim_below - trim_above)
    metrics["trim_n_treated_dropped"] = 0

    # Rules.
    b1 = metrics["smd_w_max_abs"] < B1_MAX_ABS_SMD
    o1 = metrics["share_treated_above_09"] <= O1_MAX_SHARE_TREATED_ABOVE_09
    o2 = metrics["share_clipped_units"] <= O2_MAX_SHARE_CLIPPED
    metrics["rule_B1_pass"] = bool(b1)
    metrics["rule_O1_pass"] = bool(o1)
    metrics["rule_O2_pass"] = bool(o2)
    metrics["escalate_to_Bplus_required"] = bool((not b1) and args.basis == "B")
    metrics["final_basis"] = ("B(X)" if b1 else "B+(X) (run diag-overlap-ext)") if args.basis == "B" else "B+(X)"
    metrics["trimmed_att_in_abstract_required"] = bool(not (o1 and o2))

    # (c) histograms and per-unit propensity (row key, treat and propensity only).
    outdir.mkdir(parents=True, exist_ok=True)
    edges = np.linspace(0, 1, 21)
    log_edges = np.arange(-12.0, 0.0001, 0.5)
    log_m = np.clip(np.log10(np.maximum(m_bar, 1e-300)), log_edges[0], 0.0)
    hist = {
        "bin_edges": edges.round(2).tolist(),
        "treated": np.histogram(mb1, edges)[0].tolist(),
        "control": np.histogram(mb0, edges)[0].tolist(),
        "log10_bin_edges": log_edges.round(2).tolist(),
        "log10_treated": np.histogram(log_m[d == 1], log_edges)[0].tolist(),
        "log10_control": np.histogram(log_m[d == 0], log_edges)[0].tolist(),
        "log10_note": "log10(m_bar); values below -12 are counted in the first bin",
        "propensity": "m_bar, mean over 5 repetitions of out-of-fold propensity, unclipped",
        "basis": metrics["propensity_basis"],
    }
    (outdir / "propensity_hist.json").write_text(json.dumps(hist, indent=2) + "\n")
    pd.DataFrame({"src": df["src"], "row": df["row"], "treat": d, "m_bar": m_bar}).to_csv(
        outdir / "propensity.csv", index=False, float_format="%.12g")
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps({k: v for k, v in metrics.items()
                      if not k.startswith(("smd_unweighted_", "nd_raw_"))}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
