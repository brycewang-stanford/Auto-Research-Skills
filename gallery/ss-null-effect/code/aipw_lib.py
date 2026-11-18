"""Shared pieces of the primary estimator (plan.json design.method), used by every analysis run.

Nothing here reads a file or draws a random number on import. Each analysis script imports
this module and records it with `--code code/aipw_lib.py` so that its hash is in the ledger.

Reuse: the propensity learner and the B(X) basis are imported from code/diag_overlap.py,
the script that ran the outcome-blind overlap diagnostics before the design gate, so the
primary propensity fits are the same code (design.method.propensity_learner). `basis()`
builds B(X) for any covariate subset in the same column order and is checked against
diag_overlap.basis_B on the full set.

Primary estimator (design.method.primary_estimator, cross_fitting, propensity_clipping):
  per repetition s = 0..4, K = 5 StratifiedKFold folds on treat, shuffle, random_state
  20261118 + s; out-of-fold m_i (clipped to [0.01, 0.99]) and g0_i (fitted on the controls
  of the training folds only);
  theta_s = sum_i [D_i (Y_i - g0_i) - (1 - D_i) w_i (Y_i - g0_i)] / sum_i D_i, w = m / (1 - m);
  psi_s,i = [D_i (Y_i - g0_i) - (1 - D_i) w_i (Y_i - g0_i) - D_i theta_s] / pi_hat;
  SE_s = sqrt(mean(psi_s^2) / n);
  theta = mean_s theta_s; Var = mean_s [SE_s^2 + (theta_s - theta)^2]; psi_bar = mean_s psi_s.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.model_selection import StratifiedKFold

sys.path.insert(0, str(Path(__file__).resolve().parent))
import diag_overlap  # noqa: E402  (reused: propensity learner and B(X))

propensity_learner = diag_overlap.propensity_learner

SEED = 20261118
K, S = 5, 5
CLIP = (0.01, 0.99)
Z95 = float(norm.ppf(0.975))  # 1.959964
Z90 = float(norm.ppf(0.95))   # 1.644854

COV_FILE = Path("data/derived/covariates.csv")
RAW_FILE = Path("data/raw/null_extract.csv")
MARGIN_FILE = Path("data/derived/margin_metrics.json")
MISSING_FILE = Path("data/derived/missing_counts.json")
RANGE_FILE = Path("data/derived/range_counts.json")
MAIN_METRICS = Path("runs/main-aipw/metrics.json")

COVS = ["age", "educ", "married", "urban", "region", "children", "health_limit",
        "re74", "re75", "unemp74", "unemp75"]
REGIONS = ["northeast", "midwest", "south", "west"]
OUTCOMES = ["re78", "re79", "employed78", "hours78", "benefits78", "wellbeing78"]
SENTINELS = [999, 9999, 99999, 999999, 9999999]


# ------------------------------------------------------------------ data

def load_data(outcomes: list[str]) -> pd.DataFrame:
    """Covariates and treatment from covariates.csv; the named outcomes from the raw extract.

    Only `id` and the named outcome columns are read from the raw file (usecols); the
    survey items are never read.
    """
    cov = pd.read_csv(COV_FILE, usecols=["id", "treat"] + COVS)
    if not outcomes:
        return cov
    bad = set(outcomes) - set(OUTCOMES)
    if bad:
        sys.exit(f"ERROR: not a planned outcome: {sorted(bad)}")
    out = pd.read_csv(RAW_FILE, usecols=["id"] + outcomes)
    df = cov.merge(out, on="id", how="left", validate="one_to_one")
    if len(df) != 4000:
        sys.exit("ERROR: expected 4,000 rows")
    return df


def admissible(y: pd.Series, outcome: str) -> np.ndarray:
    """design.method.outcome_validity: True where the value is admissible (else treated as missing)."""
    v = pd.to_numeric(y, errors="coerce").to_numpy(float)
    finite = np.isfinite(v)
    if outcome in ("re78", "re79", "benefits78"):
        ok = finite & (v >= 0)
    elif outcome == "employed78":
        ok = finite & np.isin(v, [0.0, 1.0])
    elif outcome == "hours78":
        ok = finite & (v >= 0) & (v <= 8784)
    elif outcome == "wellbeing78":
        ok = finite & (v >= 0) & (v <= 10) & (np.floor(v) == v)
    else:
        raise ValueError(outcome)
    if outcome in ("re78", "re79", "benefits78", "hours78"):
        sent = ok & np.isin(v, SENTINELS)
        others = v[ok & ~sent]
        top = others.max() if others.size else -np.inf
        ok = ok & ~(sent & (v > top))
    return ok


def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def echo_counts(outcomes: list[str]) -> dict:
    """Missing and inadmissible counts by arm, echoed from the pre-gate data-prep runs."""
    mc, rc = read_json(MISSING_FILE), read_json(RANGE_FILE)
    out = {}
    for k in outcomes:
        out[f"missing_{k}_treated"] = mc[f"missing_{k}_treated"]
        out[f"missing_{k}_control"] = mc[f"missing_{k}_control"]
        out[f"invalid_{k}_treated"] = rc[f"range_{k}_inadmissible_treated"]
        out[f"invalid_{k}_control"] = rc[f"range_{k}_inadmissible_control"]
    return out


# ------------------------------------------------------------------ bases

def basis(df: pd.DataFrame, covs: list[str]) -> pd.DataFrame:
    """B(X) restricted to the terms of `covs`, in the column order of diag_overlap.basis_B."""
    cols: dict[str, pd.Series] = {}
    if "age" in covs:
        cols["age"] = df.age; cols["age_sq"] = df.age ** 2
    if "educ" in covs:
        cols["educ"] = df.educ; cols["educ_sq"] = df.educ ** 2
    for c in ("children", "married", "urban", "health_limit"):
        if c in covs:
            cols[c] = df[c]
    if "re74" in covs:
        cols["re74"] = df.re74; cols["re74_sq"] = df.re74 ** 2
    if "re75" in covs:
        cols["re75"] = df.re75; cols["re75_sq"] = df.re75 ** 2
    for c in ("unemp74", "unemp75"):
        if c in covs:
            cols[c] = df[c]
    if "region" in covs:
        for r in ("northeast", "south", "west"):
            cols[f"region_{r}"] = (df.region == r)
    return pd.DataFrame(cols).astype(float)


def tree_features(df: pd.DataFrame, covs: list[str]) -> np.ndarray:
    """T(X) restricted to `covs`: numeric covariates unscaled, region one-hot (all four levels)."""
    num = [c for c in ("age", "educ", "married", "urban", "children", "health_limit",
                       "re74", "re75", "unemp74", "unemp75") if c in covs]
    parts = [df[num].to_numpy(float)]
    if "region" in covs:
        parts.append(np.column_stack([(df.region == r).to_numpy(float) for r in REGIONS]))
    return np.hstack(parts)


def check_basis_reuse(df: pd.DataFrame) -> None:
    mine, theirs = basis(df, COVS), diag_overlap.basis_B(df)
    if list(mine.columns) != list(theirs.columns) or not np.array_equal(mine.to_numpy(), theirs.to_numpy()):
        sys.exit("ERROR: basis() differs from diag_overlap.basis_B")


# ------------------------------------------------------------------ learners

def outcome_learner(seed: int):
    """design.method.outcome_learner."""
    return HistGradientBoostingRegressor(
        loss="squared_error", learning_rate=0.05, max_iter=300, max_leaf_nodes=15,
        min_samples_leaf=20, l2_regularization=1.0, early_stopping=False, random_state=seed)


def folds(d: np.ndarray, s: int):
    return list(StratifiedKFold(K, shuffle=True, random_state=SEED + s).split(np.zeros(len(d)), d))


def crossfit_propensity(X: np.ndarray, d: np.ndarray, make=propensity_learner) -> np.ndarray:
    """Out-of-fold P(treat = 1 | X), shape (S, n), unclipped."""
    m = np.zeros((S, len(d)))
    for s in range(S):
        for tr, te in folds(d, s):
            m[s, te] = make(SEED + s).fit(X[tr], d[tr]).predict_proba(X[te])[:, 1]
    return m


def crossfit_outcome(X: np.ndarray, d: np.ndarray, y: np.ndarray, make=outcome_learner) -> np.ndarray:
    """Out-of-fold E[Y | treat = 0, X], fitted on the controls of the training folds; shape (S, n)."""
    g = np.zeros((S, len(d)))
    for s in range(S):
        for tr, te in folds(d, s):
            c = tr[d[tr] == 0]
            g[s, te] = make(SEED + s).fit(X[c], y[c]).predict(X[te])
    return g


def att_from_nuisances(d: np.ndarray, y: np.ndarray, m_raw: np.ndarray, g: np.ndarray) -> dict:
    """Mean-aggregated cross-fitted AIPW ATT (design.method.primary_estimator, cross_fitting)."""
    n, pi = len(d), d.mean()
    m = np.clip(m_raw, *CLIP)
    thetas, ses, psis = [], [], []
    for s in range(S):
        w = m[s] / (1 - m[s])
        num = d * (y - g[s]) - (1 - d) * w * (y - g[s])
        theta_s = num.sum() / d.sum()
        psi = (num - d * theta_s) / pi
        thetas.append(theta_s)
        ses.append(np.sqrt(np.mean(psi ** 2) / n))
        psis.append(psi)
    thetas, ses = np.array(thetas), np.array(ses)
    theta = float(thetas.mean())
    se = float(np.sqrt(np.mean(ses ** 2 + (thetas - theta) ** 2)))
    clipped = ((m_raw < CLIP[0]) | (m_raw > CLIP[1]))
    return {"theta": theta, "se": se, "thetas": thetas, "ses": ses,
            "psi_bar": np.mean(psis, axis=0), "n": int(n), "n_treated": int(d.sum()),
            "n_clipped_units": int(clipped.any(axis=0).sum()),
            "n_clipped_unit_reps": int(clipped.sum())}


def aipw(d, y, Xprop, Xout, m_raw=None, prop_make=propensity_learner, out_make=outcome_learner) -> dict:
    """Full primary estimator; pass m_raw to reuse propensity fits on the same sample and folds."""
    if m_raw is None:
        m_raw = crossfit_propensity(Xprop, d, prop_make)
    g = crossfit_outcome(Xout, d, y, out_make)
    res = att_from_nuisances(d, y, m_raw, g)
    res["m_raw"] = m_raw
    return res


# ------------------------------------------------------------------ inference

def summarize(res: dict, prefix: str, M: float | None = None) -> dict:
    """Flat metrics: estimate, SE, 95% and 90% CIs, p, and (with M) the H1/H1b decisions."""
    th, se = res["theta"], res["se"]
    out = {
        f"{prefix}effect": th, f"{prefix}se": se,
        f"{prefix}ci_low": th - Z95 * se, f"{prefix}ci_high": th + Z95 * se,
        f"{prefix}ci90_low": th - Z90 * se, f"{prefix}ci90_high": th + Z90 * se,
        f"{prefix}p": float(2 * norm.sf(abs(th) / se)),
        f"{prefix}n": res["n"], f"{prefix}n_treated": res["n_treated"],
    }
    if "n_clipped_units" in res:
        out[f"{prefix}n_clipped_units"] = res["n_clipped_units"]
    out[f"{prefix}h1_reject"] = bool(out[f"{prefix}ci_low"] > 0 or out[f"{prefix}ci_high"] < 0)
    if M is not None:
        p_tost = max(float(norm.sf((th + M) / se)), float(norm.cdf((th - M) / se)))
        lo90, hi90 = out[f"{prefix}ci90_low"], out[f"{prefix}ci90_high"]
        out[f"{prefix}p_tost"] = p_tost
        out[f"{prefix}h1b_supported"] = bool(p_tost < 0.05)
        out[f"{prefix}ci90_inside_margin"] = bool(-M < lo90 and hi90 < M)
        out[f"{prefix}min_margin"] = max(abs(lo90), abs(hi90))
    return out


def compare_with_main(metrics: dict, prefix: str, main: dict) -> dict:
    """Decision comparison with main-aipw (design.threats, rule for disagreement)."""
    out = {
        f"{prefix}h1_differs_from_main": bool(metrics[f"{prefix}h1_reject"] != main["h1_reject"]),
    }
    if f"{prefix}h1b_supported" in metrics:
        out[f"{prefix}h1b_differs_from_main"] = bool(metrics[f"{prefix}h1b_supported"] != main["h1b_supported"])
    out[f"{prefix}effect_outside_main_ci95"] = bool(
        metrics[f"{prefix}effect"] < main["ci_low"] or metrics[f"{prefix}effect"] > main["ci_high"])
    return out


def write_metrics(path: Path, metrics: dict) -> None:
    clean = {}
    for k, v in metrics.items():
        if isinstance(v, (np.bool_, bool)):
            clean[k] = bool(v)
        elif isinstance(v, (np.integer,)):
            clean[k] = int(v)
        elif isinstance(v, (np.floating, float)):
            clean[k] = float(v)
        else:
            clean[k] = v
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean, indent=2) + "\n")
