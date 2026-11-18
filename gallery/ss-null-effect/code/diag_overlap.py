"""Outcome-blind balance and overlap diagnostics (plan.json design.method.comparability_checks).

Reads data/derived/covariates.csv only: id, treat and the eleven pre-program covariates.
It never reads data/raw/ and refuses to run if any outcome or survey column is present.

Propensity: the primary estimator's cross-fitted propensity, exactly as in
design.method.propensity_learner / cross_fitting:
  - sklearn LogisticRegressionCV on the basis (B(X), or B+(X) for the escalation run),
    standardized within each training fold, L2, Cs = 10 values log-spaced on [1e-4, 1e4],
    inner StratifiedKFold(5, shuffle, random_state = seed of the repetition),
    scoring neg_log_loss, solver lbfgs, max_iter 10000;
  - K = 5 outer StratifiedKFold on treat (shuffle), S = 5 repetitions with
    random_state 20261118 + s, s = 0..4; out-of-fold predictions m_s,i.
  - clipping to [0.01, 0.99] before weights (design.method.propensity_clipping).
  - m_bar_i = mean over repetitions of the out-of-fold m_s,i (unclipped; the clip bounds
    lie outside [0.1, 0.9], so no overlap share depends on this choice).

Reported (definitions):
  (a) nd_raw_<x>: Imbens-Wooldridge normalized difference (x1 - x0) / sqrt(s1^2 + s0^2),
      unweighted, for the eleven covariates (region per level); |nd| > 0.25 flagged
      "regression-sensitive", no further action.
  (b) smd_w_<term>: ATT-weighted standardized mean difference for every term of B(X),
      (x1 - x0_w) / sqrt((s1^2 + s0^2) / 2), controls weighted by w = m/(1 - m) with m the
      clipped propensity of each repetition, averaged over repetitions (the weights the
      primary estimator applies, averaged over its S cross-fits); x0_w is the weighted
      control mean; s1, s0 are the unweighted group SDs (ddof = 1), so the denominator is
      the same before and after weighting. smd_w_rep_max_abs: the largest |SMD| over the
      S repetitions taken separately (informational, not a rule).
  (c) propensity histogram by treat: runs/<id>/propensity_hist.json (20 bins of 0.05).
  (d) share of all units with m_bar outside [0.1, 0.9]; share of treated with m_bar > 0.9;
      clipped units (a unit is clipped if any of its S out-of-fold m_s,i lies outside
      [0.01, 0.99]) and clipped unit-repetition pairs; Kish effective sample size of the
      weighted controls, (sum w)^2 / sum w^2.

Decision rules, fixed in plan.json before this run:
  B1: every weighted |SMD| over the terms of B(X) < 0.10. If B1 fails with B(X), the
      propensity basis is replaced by B+(X) once (run diag-overlap-ext, this script with
      --basis Bplus); whatever B+ yields is final.
  O1: share of treated with m_bar > 0.9 <= 5%.
  O2: share of all units clipped <= 1%.

Seeds: outer folds and inner CV use 20261118 + s (s = 0..4); nothing else is random.

Run from the workspace root:
    .venv/bin/python -I code/diag_overlap.py                 # run diag-overlap, basis B(X)
    .venv/bin/python -I code/diag_overlap.py --basis Bplus   # run diag-overlap-ext, B+(X)
"""

import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegressionCV
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

COV = Path("data/derived/covariates.csv")
SEED = 20261118
K, S = 5, 5
CLIP = (0.01, 0.99)
B1_MAX_ABS_SMD = 0.10
O1_MAX_SHARE_TREATED_ABOVE_09 = 0.05
O2_MAX_SHARE_CLIPPED = 0.01
ND_FLAG = 0.25
COVS = ["age", "educ", "married", "urban", "region", "children", "health_limit",
        "re74", "re75", "unemp74", "unemp75"]
REGIONS = ["midwest", "northeast", "south", "west"]
OUTCOME_NAMES = {"re78", "re79", "employed78", "hours78", "benefits78", "wellbeing78"}


def load() -> pd.DataFrame:
    header = pd.read_csv(COV, nrows=0).columns
    leaked = (OUTCOME_NAMES & set(header)) | {c for c in header if c.startswith("survey_")}
    if leaked:
        sys.exit(f"ERROR: {COV} contains outcome columns {sorted(leaked)}; refusing to run")
    df = pd.read_csv(COV, usecols=["id", "treat"] + COVS)
    if df.isna().any().any():
        sys.exit("ERROR: missing values in treatment or covariates")
    return df


def basis_B(df: pd.DataFrame) -> pd.DataFrame:
    """B(X): 17 terms (design.method.covariate_bases); midwest is the reference region."""
    out = pd.DataFrame({
        "age": df.age, "age_sq": df.age ** 2, "educ": df.educ, "educ_sq": df.educ ** 2,
        "children": df.children, "married": df.married, "urban": df.urban,
        "health_limit": df.health_limit, "re74": df.re74, "re74_sq": df.re74 ** 2,
        "re75": df.re75, "re75_sq": df.re75 ** 2, "unemp74": df.unemp74, "unemp75": df.unemp75,
    })
    for r in ("northeast", "south", "west"):
        out[f"region_{r}"] = (df.region == r)
    return out.astype(float)


def basis_Bplus(df: pd.DataFrame) -> pd.DataFrame:
    """B+(X): B(X), all pairwise products of the ten listed covariates, region x {re74, re75}."""
    out = basis_B(df)
    pair_vars = ["age", "educ", "children", "married", "urban", "health_limit",
                 "re74", "re75", "unemp74", "unemp75"]
    for a, b in itertools.combinations(pair_vars, 2):
        out[f"{a}_x_{b}"] = df[a].astype(float) * df[b].astype(float)
    for r in ("northeast", "south", "west"):
        for e in ("re74", "re75"):
            out[f"region_{r}_x_{e}"] = (df.region == r).astype(float) * df[e].astype(float)
    return out


def propensity_learner(seed: int):
    return make_pipeline(StandardScaler(), LogisticRegressionCV(
        Cs=np.logspace(-4, 4, 10), cv=StratifiedKFold(5, shuffle=True, random_state=seed),
        scoring="neg_log_loss", solver="lbfgs", max_iter=10_000))


def crossfit(X: np.ndarray, d: np.ndarray):
    m = np.zeros((S, len(d)))
    chosen_C = []
    for s in range(S):
        outer = StratifiedKFold(K, shuffle=True, random_state=SEED + s)
        for tr, te in outer.split(np.zeros(len(d)), d):
            fit = propensity_learner(SEED + s).fit(X[tr], d[tr])
            m[s, te] = fit.predict_proba(X[te])[:, 1]
            chosen_C.append(float(fit[-1].C_[0]))
    return m, np.array(chosen_C)


def wsmd(x: np.ndarray, d: np.ndarray, w: np.ndarray) -> float:
    x1, x0 = x[d == 1], x[d == 0]
    denom = np.sqrt((x1.var(ddof=1) + x0.var(ddof=1)) / 2)
    if denom == 0:
        return 0.0
    w0 = w[d == 0]
    return float((x1.mean() - np.sum(w0 * x0) / np.sum(w0)) / denom)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--basis", choices=["B", "Bplus"], default="B")
    args = ap.parse_args()
    run_id = "diag-overlap" if args.basis == "B" else "diag-overlap-ext"
    outdir = Path("runs") / run_id

    df = load()
    d = df["treat"].to_numpy(int)
    n, n1 = len(d), int(d.sum())
    XB = basis_B(df)
    Xprop = XB if args.basis == "B" else basis_Bplus(df)

    m_raw, chosen_C = crossfit(Xprop.to_numpy(float), d)
    m_clip = np.clip(m_raw, *CLIP)
    m_bar = m_raw.mean(axis=0)
    clipped_pairs = (m_raw < CLIP[0]) | (m_raw > CLIP[1])
    clipped_units = clipped_pairs.any(axis=0)

    # ATT weights for controls: average over repetitions of m/(1-m) with clipped m.
    w_rep = m_clip / (1 - m_clip)
    w = w_rep.mean(axis=0)
    w0 = w[d == 0]
    kish = float(w0.sum() ** 2 / np.sum(w0 ** 2))

    metrics: dict = {
        "run_id": run_id,
        "propensity_basis": "B+(X)" if args.basis == "Bplus" else "B(X)",
        "propensity_basis_n_terms": int(Xprop.shape[1]),
        "propensity_model": "LogisticRegressionCV L2 lbfgs, Cs=logspace(-4,4,10), inner 5-fold, neg_log_loss, standardized in-fold",
        "enlarge_once_fired": bool(args.basis == "Bplus"),
        "seed_base": SEED, "n_folds": K, "n_repetitions": S,
        "n": n, "n_treated": n1, "n_control": n - n1,
        "propensity_C_min": float(chosen_C.min()),
        "propensity_C_median": float(np.median(chosen_C)),
        "propensity_C_max": float(chosen_C.max()),
    }

    # (a) raw Imbens-Wooldridge normalized differences, eleven covariates, region per level.
    raw = df[[c for c in COVS if c != "region"]].astype(float).copy()
    for r in REGIONS:
        raw[f"region_{r}"] = (df.region == r).astype(float)
    flagged = []
    for c in raw.columns:
        x = raw[c].to_numpy()
        x1, x0 = x[d == 1], x[d == 0]
        nd = float((x1.mean() - x0.mean()) / np.sqrt(x1.var(ddof=1) + x0.var(ddof=1)))
        metrics[f"nd_raw_{c}"] = nd
        if abs(nd) > ND_FLAG:
            flagged.append(c)
    metrics["nd_raw_n_flagged_regression_sensitive"] = len(flagged)
    metrics["nd_raw_flagged"] = ",".join(flagged)

    # (b) ATT-weighted SMDs for every term of B(X) (plus midwest, informational).
    XBm = XB.copy()
    XBm["region_midwest"] = (df.region == "midwest").astype(float)
    smd = {c: wsmd(XBm[c].to_numpy(), d, w) for c in XBm.columns}
    smd_unw = {c: wsmd(XBm[c].to_numpy(), d, np.ones(n)) for c in XBm.columns}
    for c in XBm.columns:
        metrics[f"smd_unweighted_{c}"] = smd_unw[c]
        metrics[f"smd_w_{c}"] = smd[c]
    b_terms = list(XB.columns)
    worst = max(b_terms, key=lambda c: abs(smd[c]))
    metrics["smd_w_max_abs"] = abs(smd[worst])
    metrics["smd_w_max_abs_term"] = worst
    metrics["smd_w_n_terms_ge_010"] = int(sum(abs(smd[c]) >= B1_MAX_ABS_SMD for c in b_terms))
    metrics["smd_w_terms_ge_010"] = ",".join(c for c in b_terms if abs(smd[c]) >= B1_MAX_ABS_SMD)
    metrics["smd_w_rep_max_abs"] = float(max(
        abs(wsmd(XB[c].to_numpy(), d, w_rep[s])) for s in range(S) for c in b_terms))

    # (d) overlap.
    metrics["share_all_outside_01_09"] = float(np.mean((m_bar < 0.1) | (m_bar > 0.9)))
    metrics["n_all_outside_01_09"] = int(np.sum((m_bar < 0.1) | (m_bar > 0.9)))
    metrics["share_treated_above_09"] = float(np.mean(m_bar[d == 1] > 0.9))
    metrics["n_treated_above_09"] = int(np.sum(m_bar[d == 1] > 0.9))
    metrics["n_control_below_01"] = int(np.sum(m_bar[d == 0] < 0.1))
    metrics["n_clipped_units"] = int(clipped_units.sum())
    metrics["share_clipped_units"] = float(clipped_units.mean())
    metrics["n_clipped_unit_reps"] = int(clipped_pairs.sum())
    metrics["kish_ess_controls"] = kish
    metrics["max_control_weight"] = float(w0.max())
    metrics["m_bar_min_treated"] = float(m_bar[d == 1].min())
    metrics["m_bar_max_treated"] = float(m_bar[d == 1].max())
    metrics["m_bar_min_control"] = float(m_bar[d == 0].min())
    metrics["m_bar_max_control"] = float(m_bar[d == 0].max())

    # Rules.
    b1 = metrics["smd_w_max_abs"] < B1_MAX_ABS_SMD
    o1 = metrics["share_treated_above_09"] <= O1_MAX_SHARE_TREATED_ABOVE_09
    o2 = metrics["share_clipped_units"] <= O2_MAX_SHARE_CLIPPED
    metrics["rule_B1_pass"] = bool(b1)
    metrics["rule_O1_pass"] = bool(o1)
    metrics["rule_O2_pass"] = bool(o2)
    metrics["escalate_to_Bplus_required"] = bool((not b1) and args.basis == "B")
    metrics["trimmed_att_in_abstract_required"] = bool(not (o1 and o2))

    # (c) histogram and per-unit propensity (treat and propensity only).
    outdir.mkdir(parents=True, exist_ok=True)
    edges = np.linspace(0, 1, 21)
    hist = {
        "bin_edges": edges.round(2).tolist(),
        "treated": np.histogram(m_bar[d == 1], edges)[0].tolist(),
        "control": np.histogram(m_bar[d == 0], edges)[0].tolist(),
        "propensity": "m_bar, mean over 5 repetitions of out-of-fold propensity, unclipped",
        "basis": metrics["propensity_basis"],
    }
    (outdir / "propensity_hist.json").write_text(json.dumps(hist, indent=2) + "\n")
    pd.DataFrame({"id": df["id"], "treat": d, "m_bar": m_bar}).to_csv(
        outdir / "propensity.csv", index=False, float_format="%.10f")
    (outdir / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(json.dumps({k: v for k, v in metrics.items()
                      if not k.startswith(("smd_unweighted_", "nd_raw_"))}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
