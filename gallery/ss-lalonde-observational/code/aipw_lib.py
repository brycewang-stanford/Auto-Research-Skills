"""Shared pieces of the primary estimator (plan.json design.method), used by every analysis run.

Adopted from gallery/ss-null-effect/code/aipw_lib.py at commit 716b6c3 (sha256 86435b8f...b541)
with only the adaptations in plan.json design.method.deviations:
  DEV-1  the ten covariates of these files (age, educ, black, hisp, married, nodegree, re74,
         re75, u74, u75); no region one-hot.
  DEV-2  B(X) by the adopted rule (continuous covariates age, educ, re74, re75 linear and
         squared, binaries linear, no interactions; standardized inside the learner).
  DEV-3  T(X): the covariates of the set, unscaled.
  DEV-5  upper clip only: m is clipped above at 0.99; no floor. "Clipped" = raw m > 0.99.
  DEV-10 outcome counts (missing, inadmissible) are made by the analysis runs, by arm.
  DEV-11 the H1 decision is this study's: 95% CI entirely above zero (ci_low > 0). There is
         no margin M, no H1b and no 90% interval.
  join   re78 is read from data/raw only by main-aipw through method.join_rule
         (join_re78_from_raw); main-aipw writes the joined outcome, keyed by (src, row), to
         data/derived/re78_by_key.csv, and every later run that needs re78 reads that file
         (load_re78) and checks its key against the working file.
Everything else is the adopted code: AIPW ATT score, per-repetition SE, mean aggregation with
the between-repetition variance term, outcome learner, folds and seeds.

Nothing here reads a file or draws a random number on import. Each analysis script imports
this module and records it with `--code code/aipw_lib.py` (and `--code code/diag_overlap.py`,
which it imports) so that their hashes are in the ledger.

Reuse of the pre-gate code: the covariates are loaded by diag_overlap.load() (the reader of
the outcome-free working file, which refuses a file with an re78 column), the propensity
learner, the outer folds and the primary propensity cross-fit are diag_overlap's own
functions (diag_overlap.propensity_learner, folds, crossfit), so the primary propensity fits
are the code that ran before the gate. `basis()` builds B(X) for any covariate subset in the
column order of diag_overlap.basis_B and is checked against it on the full set
(check_basis_reuse).

Primary estimator (design.method.primary_estimator, cross_fitting, propensity_clipping):
  per repetition s = 0..4, K = 5 StratifiedKFold folds on treat, shuffle, random_state
  20261118 + s; out-of-fold m_i (clipped above at 0.99) and g0_i (fitted on the CPS men of
  the training folds only);
  theta_s = sum_i [D_i (Y_i - g0_i) - (1 - D_i) w_i (Y_i - g0_i)] / sum_i D_i, w = m / (1 - m);
  psi_s,i = [D_i (Y_i - g0_i) - (1 - D_i) w_i (Y_i - g0_i) - D_i theta_s] / pi_hat;
  SE_s = sqrt(mean(psi_s^2) / n);
  theta = mean_s theta_s; Var = mean_s [SE_s^2 + (theta_s - theta)^2]; psi_bar = mean_s psi_s.
"""

from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import norm
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.exceptions import ConvergenceWarning

sys.path.insert(0, str(Path(__file__).resolve().parent))
import diag_overlap  # noqa: E402  (reused: loader, propensity learner, folds, cross-fit, B(X))

propensity_learner = diag_overlap.propensity_learner
folds = diag_overlap.folds

SEED = diag_overlap.SEED          # 20261118
K, S = diag_overlap.K, diag_overlap.S   # 5, 5
CLIP_HI = diag_overlap.CLIP_HI    # 0.99, no lower clip (DEV-5)
Z95 = float(norm.ppf(0.975))      # 1.959964

COVS = list(diag_overlap.COVS)
CONTINUOUS = tuple(diag_overlap.CONTINUOUS)
X_MINUS = [c for c in COVS if c not in ("re75", "u75")]          # H3 placebo
COVSET_A = ["age", "educ", "married", "re74", "re75", "u74", "u75"]  # rob-covsets (a)
COVSET_B = [c for c in COVS if c not in ("re74", "u74")]          # rob-covsets (b)
TIME_INVARIANT = ["age", "educ", "black", "hisp", "married", "nodegree"]  # rob-diff74

DERIVED_FILE = diag_overlap.DATA  # data/derived/analysis_noRE78.csv
RAW_FILES = {
    "nswre74_treated": Path("data/raw/nswre74_treated.txt"),
    "cps_controls": Path("data/raw/cps_controls.txt"),
}
RAW_FIELDS = ["treat", "age", "educ", "black", "hisp", "married", "nodegree", "re74", "re75", "re78"]
RE78_FILE = Path("data/derived/re78_by_key.csv")
DIAG_METRICS = Path("runs/diag-overlap/metrics.json")
DIAG_PROP = Path("runs/diag-overlap/propensity.csv")
MAIN_METRICS = Path("runs/main-aipw/metrics.json")
SENTINELS = [999, 9999, 99999, 999999, 9999999]
KEY = ["src", "row"]


# ------------------------------------------------------------------ data

def read_json(path: Path) -> dict:
    return json.loads(Path(path).read_text())


def load_covariates() -> pd.DataFrame:
    """Row key, treat and the ten covariates from the outcome-free working file.

    diag_overlap.load() refuses a file with an re78 column and checks u74/u75. The size of
    the file and the final propensity basis are checked against run diag-overlap.
    """
    df = diag_overlap.load()
    diag = read_json(DIAG_METRICS)
    if len(df) != diag["n"] or int(df["treat"].sum()) != diag["n_treated"]:
        sys.exit("ERROR: working file does not match run diag-overlap (n, n_treated)")
    if diag["final_basis"] != "B(X)" or not diag["rule_B1_pass"]:
        sys.exit("ERROR: diag-overlap did not fix B(X) as the final basis; the scripts implement B(X) only")
    return df


def _number_or_nan(token: str) -> float:
    try:
        return float(token)
    except ValueError:
        return float("nan")


def join_re78_from_raw(df: pd.DataFrame) -> np.ndarray:
    """design.method.join_rule. Only main-aipw calls this.

    Parses both raw files (ten whitespace-separated fields per non-blank line; row = 1-based
    line number, as written by code/prepare_data.py), takes field 10 (re78) by (src, row),
    and stops unless every derived row has exactly one raw line and every raw line one
    derived row, and fields 1-9 of each raw line equal treat and the eight raw covariates of
    the derived row exactly (u74 and u75 rebuilt from the raw re74/re75 and compared too).
    A field-10 token that is not a number becomes NaN (counted as missing by the caller).
    Returns re78 aligned with the rows of df.
    """
    recs = []
    for src, path in RAW_FILES.items():
        for lineno, line in enumerate(path.read_text(encoding="ascii").splitlines(), start=1):
            if not line.strip():
                continue
            tok = line.split()
            if len(tok) != len(RAW_FIELDS):
                sys.exit(f"ERROR: {path}:{lineno} has {len(tok)} fields, expected {len(RAW_FIELDS)}")
            recs.append([src, lineno] + [float(t) for t in tok[:9]] + [_number_or_nan(tok[9])])
    raw = pd.DataFrame(recs, columns=KEY + RAW_FIELDS)
    if raw.duplicated(KEY).any():
        sys.exit("ERROR: duplicate (src, row) keys in the raw files")
    # The derived values are re-read with the exact (round-trip) parser for the comparison.
    exact = pd.read_csv(DERIVED_FILE, usecols=KEY + ["treat"] + COVS, float_precision="round_trip")
    if not exact[KEY].equals(df[KEY].reset_index(drop=True)):
        sys.exit("ERROR: working file row keys differ between readers")
    m = exact.merge(raw, on=KEY, how="outer", suffixes=("", "_raw"), indicator=True)
    unmatched = int((m["_merge"] != "both").sum())
    if unmatched:
        sys.exit(f"ERROR: join_rule: {unmatched} rows unmatched between data/raw and {DERIVED_FILE}")
    bad = 0
    for c in RAW_FIELDS[:9]:
        bad += int((m[c].astype(float) != m[f"{c}_raw"].astype(float)).sum())
    bad += int((m["u74"] != (m["re74_raw"] == 0).astype(int)).sum())
    bad += int((m["u75"] != (m["re75_raw"] == 0).astype(int)).sum())
    if bad:
        sys.exit(f"ERROR: join_rule: {bad} field mismatches between data/raw and {DERIVED_FILE}")
    y = df[KEY].merge(m[KEY + ["re78"]], on=KEY, how="left", validate="one_to_one")["re78"]
    return y.to_numpy(float)


def write_re78(df: pd.DataFrame, y: np.ndarray) -> None:
    """Joined outcome keyed by (src, row); float repr round-trips exactly."""
    RE78_FILE.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame({"src": df["src"].to_numpy(), "row": df["row"].to_numpy(), "re78": y}).to_csv(
        RE78_FILE, index=False)


def load_re78(df: pd.DataFrame) -> np.ndarray:
    """re78 from data/derived/re78_by_key.csv (written by main-aipw), aligned with df.

    Stops unless its keys are exactly the working file's keys, in the same order.
    """
    out = pd.read_csv(RE78_FILE, dtype={"src": str, "row": "int64"}, float_precision="round_trip")
    if list(out.columns) != KEY + ["re78"]:
        sys.exit(f"ERROR: {RE78_FILE} has columns {list(out.columns)}")
    if not out[KEY].equals(df[KEY].reset_index(drop=True)):
        sys.exit(f"ERROR: {RE78_FILE} keys do not match {DERIVED_FILE}")
    return out["re78"].to_numpy(float)


def admissible(y, outcome: str = "re78") -> np.ndarray:
    """design.method.outcome_validity for earnings: finite and >= 0, with the sentinel rule
    (a value in SENTINELS above every other admissible value is inadmissible)."""
    v = pd.to_numeric(pd.Series(np.asarray(y, dtype=float)), errors="coerce").to_numpy(float)
    ok = np.isfinite(v) & (v >= 0)
    sent = ok & np.isin(v, SENTINELS)
    others = v[ok & ~sent]
    top = others.max() if others.size else -np.inf
    return ok & ~(sent & (v > top))


def outcome_counts(y: np.ndarray, d: np.ndarray, name: str) -> dict:
    """Missing (NaN) and inadmissible (present, not admissible) counts and shares by arm."""
    miss = np.isnan(y)
    inad = ~miss & ~admissible(y)
    out = {}
    for arm, mask in (("treated", d == 1), ("control", d == 0)):
        out[f"missing_{name}_{arm}"] = int((miss & mask).sum())
        out[f"inadmissible_{name}_{arm}"] = int((inad & mask).sum())
        out[f"unobserved_{name}_{arm}"] = int(((miss | inad) & mask).sum())
        out[f"share_unobserved_{name}_{arm}"] = float(((miss | inad) & mask).sum() / mask.sum())
    return out


# ------------------------------------------------------------------ bases

def basis(df: pd.DataFrame, covs: list[str]) -> pd.DataFrame:
    """B(X) restricted to `covs`, in the column order of diag_overlap.basis_B (DEV-2)."""
    cols: dict[str, pd.Series] = {}
    for c in COVS:
        if c in covs:
            cols[c] = df[c]
            if c in CONTINUOUS:
                cols[f"{c}_sq"] = df[c] ** 2
    return pd.DataFrame(cols).astype(float)


def tree_features(df: pd.DataFrame, covs: list[str]) -> np.ndarray:
    """T(X) restricted to `covs`: the covariates, unscaled, in COVS order (DEV-3)."""
    return df[[c for c in COVS if c in covs]].to_numpy(float)


def check_basis_reuse(df: pd.DataFrame) -> None:
    mine, theirs = basis(df, COVS), diag_overlap.basis_B(df)
    if list(mine.columns) != list(theirs.columns) or not np.array_equal(mine.to_numpy(), theirs.to_numpy()):
        sys.exit("ERROR: basis() differs from diag_overlap.basis_B")


# ------------------------------------------------------------------ learners

def outcome_learner(seed: int):
    """design.method.outcome_learner (unchanged)."""
    return HistGradientBoostingRegressor(
        loss="squared_error", learning_rate=0.05, max_iter=300, max_leaf_nodes=15,
        min_samples_leaf=20, l2_regularization=1.0, early_stopping=False, random_state=seed)


def _fit_quiet(est, X, y, counter: list):
    """Fit with scikit-learn FutureWarnings silenced (no argument changed); count ConvergenceWarnings."""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", ConvergenceWarning)
        warnings.simplefilter("ignore", FutureWarning)
        est.fit(X, y)
    counter[0] += sum(issubclass(w.category, ConvergenceWarning) for w in caught)
    for w in caught:
        if not issubclass(w.category, ConvergenceWarning):
            warnings.warn_explicit(w.message, w.category, w.filename, w.lineno)
    return est


def crossfit_propensity(X: np.ndarray, d: np.ndarray, make=None, target: np.ndarray | None = None):
    """Out-of-fold probabilities, shape (S, n), unclipped, and the ConvergenceWarning count.

    make=None: the primary propensity cross-fit, exactly diag_overlap.crossfit (the pre-gate
    code). Otherwise the classifier `make(seed)` on the same folds (stratified on d) and
    seeds; `target` (default d) is the label fitted, e.g. the observation indicator R in rob-ipow.
    """
    if make is None and target is None:
        m, _, _, n_conv = diag_overlap.crossfit(X, d)
        return m, int(n_conv)
    make = make or propensity_learner
    lab = d if target is None else target
    m = np.zeros((S, len(d)))
    n_conv = [0]
    for s in range(S):
        for tr, te in folds(d, s):
            fit = _fit_quiet(make(SEED + s), X[tr], lab[tr], n_conv)
            m[s, te] = fit.predict_proba(X[te])[:, 1]
    return m, n_conv[0]


def crossfit_outcome(X: np.ndarray, d: np.ndarray, y: np.ndarray, make=outcome_learner,
                     observed: np.ndarray | None = None) -> np.ndarray:
    """Out-of-fold E[Y | treat = 0, X], fitted on the controls of the training folds (and only
    those with observed Y if `observed` is given); shape (S, n)."""
    obs = np.ones(len(d), bool) if observed is None else observed
    g = np.zeros((S, len(d)))
    n_conv = [0]
    for s in range(S):
        for tr, te in folds(d, s):
            c = tr[(d[tr] == 0) & obs[tr]]
            g[s, te] = _fit_quiet(make(SEED + s), X[c], y[c], n_conv).predict(X[te])
    return g


def control_weights(m_raw: np.ndarray, d: np.ndarray) -> np.ndarray:
    """ATT control weights w = m / (1 - m) with the clipped m, averaged over repetitions (as diag-overlap)."""
    m = np.minimum(m_raw, CLIP_HI)
    return (m / (1 - m)).mean(axis=0)


def att_from_nuisances(d: np.ndarray, y: np.ndarray, m_raw: np.ndarray, g: np.ndarray) -> dict:
    """Mean-aggregated cross-fitted AIPW ATT (design.method.primary_estimator, cross_fitting)."""
    n, pi = len(d), d.mean()
    m = np.minimum(m_raw, CLIP_HI)
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
    clipped = m_raw > CLIP_HI
    w0 = control_weights(m_raw, d)[d == 0]
    return {"theta": theta, "se": se, "thetas": thetas, "ses": ses,
            "psi_bar": np.mean(psis, axis=0), "n": int(n), "n_treated": int(d.sum()),
            "n_clipped_units": int(clipped.any(axis=0).sum()),
            "n_clipped_unit_reps": int(clipped.sum()),
            "kish_ess_controls": float(w0.sum() ** 2 / np.sum(w0 ** 2)),
            "max_control_weight": float(w0.max())}


def aipw(d, y, Xprop, Xout, m_raw=None, prop_make=None, out_make=outcome_learner) -> dict:
    """Full primary estimator; pass m_raw to reuse propensity fits on the same sample and folds.
    prop_make=None is the primary propensity cross-fit (diag_overlap.crossfit)."""
    n_conv = 0
    if m_raw is None:
        m_raw, n_conv = crossfit_propensity(Xprop, d, prop_make)
    g = crossfit_outcome(Xout, d, y, out_make)
    res = att_from_nuisances(d, y, m_raw, g)
    res["m_raw"] = m_raw
    res["n_convergence_warnings"] = n_conv
    return res


def att_ipow_from_nuisances(d, y, R, r, m_raw, g) -> dict:
    """design.method.missing_outcomes (rob-ipow): per repetition s,
    theta_s = sum_i (R_i / r_s,i) [D_i (Y_i - g0_i) - (1 - D_i) w_i (Y_i - g0_i)] / sum_i D_i,
    r clipped below at 0.05 (by the caller), psi_s,i = [(R_i / r_s,i) num_i - D_i theta_s] / pi_hat
    (r treated as known), aggregated over repetitions as the primary estimator. Units with
    R = 0 contribute 0 to the sum (their Y is never used)."""
    n, pi = len(d), d.mean()
    m = np.minimum(m_raw, CLIP_HI)
    yy = np.where(R == 1, y, 0.0)
    thetas, ses, psis = [], [], []
    for s in range(S):
        w = m[s] / (1 - m[s])
        resid = np.where(R == 1, yy - g[s], 0.0)
        num = (R / r[s]) * (d * resid - (1 - d) * w * resid)
        theta_s = num.sum() / d.sum()
        psi = (num - d * theta_s) / pi
        thetas.append(theta_s)
        ses.append(np.sqrt(np.mean(psi ** 2) / n))
        psis.append(psi)
    thetas, ses = np.array(thetas), np.array(ses)
    theta = float(thetas.mean())
    se = float(np.sqrt(np.mean(ses ** 2 + (thetas - theta) ** 2)))
    return {"theta": theta, "se": se, "thetas": thetas, "ses": ses, "n": int(n),
            "n_treated": int(d.sum()), "n_clipped_units": int((m_raw > CLIP_HI).any(axis=0).sum())}


# ------------------------------------------------------------------ inference and rules

def summarize(res: dict, prefix: str = "") -> dict:
    """Flat metrics: estimate, SE, 95% CI, p, sample sizes, clipped units, H1 decision."""
    th, se = res["theta"], res["se"]
    out = {
        f"{prefix}effect": th, f"{prefix}se": se,
        f"{prefix}ci_low": th - Z95 * se, f"{prefix}ci_high": th + Z95 * se,
        f"{prefix}p": float(2 * norm.sf(abs(th) / se)),
        f"{prefix}n": res["n"], f"{prefix}n_treated": res["n_treated"],
        f"{prefix}n_control": res["n"] - res["n_treated"],
    }
    if "n_clipped_units" in res:
        out[f"{prefix}n_clipped_units"] = res["n_clipped_units"]
    out[f"{prefix}h1_holds"] = h1_holds(out[f"{prefix}ci_low"])
    return out


def per_repetition(res: dict, prefix: str = "") -> dict:
    out = {}
    for s in range(S):
        out[f"{prefix}theta_rep{s}"] = float(res["thetas"][s])
        out[f"{prefix}se_rep{s}"] = float(res["ses"][s])
    return out


def h1_holds(ci_low: float) -> bool:
    """design.method.h1_test: H1 holds iff the 95% CI lies entirely above zero."""
    return bool(ci_low > 0)


def compare_with_main(metrics: dict, prefix: str, main: dict) -> dict:
    """Decision comparison with main-aipw (design.threats, rule for disagreement)."""
    return {
        f"{prefix}h1_differs_from_main": bool(metrics[f"{prefix}h1_holds"] != main["h1_holds"]),
        f"{prefix}effect_outside_main_ci95": bool(
            metrics[f"{prefix}effect"] < main["ci_low"] or metrics[f"{prefix}effect"] > main["ci_high"]),
    }


PLACEBO_BOUND = 900.0  # fixed at the question gate (H3)


def placebo_verdict(ci_low: float, ci_high: float, bound: float = PLACEBO_BOUND) -> tuple[str, int]:
    """design.method.h3_placebo, in this order: FAIL if the 95% CI excludes 0 (precedence);
    else PASS if -bound <= ci_low and ci_high <= bound; else INCONCLUSIVE.
    Codes: pass 1, inconclusive 0, fail -1."""
    if ci_low > 0 or ci_high < 0:
        return "fail", -1
    if -bound <= ci_low and ci_high <= bound:
        return "pass", 1
    return "inconclusive", 0


def trim_keep(m_bar: np.ndarray, d: np.ndarray) -> np.ndarray:
    """design.method.control_only_trimming: keep every treated man; keep a CPS man iff his
    m_bar lies in [min, max] of m_bar over the treated (inclusive)."""
    lo, hi = m_bar[d == 1].min(), m_bar[d == 1].max()
    return (d == 1) | ((m_bar >= lo) & (m_bar <= hi))


def relative_effect(d: np.ndarray, y: np.ndarray, res: dict) -> dict:
    """design.method.relative_effect: r = theta / (mu1 - theta), delta-method CI from
    psi_r = [mu1 psi_theta - theta psi_mu] / (mu1 - theta)^2, psi_mu = D (Y - mu1) / pi_hat,
    psi_theta = psi_bar (mean over repetitions)."""
    pi = d.mean()
    mu1 = float(y[d == 1].mean())
    th = res["theta"]
    cf = mu1 - th
    psi_mu = d * (y - mu1) / pi
    psi_r = (mu1 * res["psi_bar"] - th * psi_mu) / cf ** 2
    se_r = float(np.sqrt(np.mean(psi_r ** 2) / len(d)))
    r = th / cf
    return {"treated_mean": mu1, "cf_mean": cf, "rel_effect": r, "rel_se": se_r,
            "rel_ci_low": r - Z95 * se_r, "rel_ci_high": r + Z95 * se_r,
            "rel_effect_pct": 100 * r, "rel_ci_low_pct": 100 * (r - Z95 * se_r),
            "rel_ci_high_pct": 100 * (r + Z95 * se_r)}


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
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean, indent=2) + "\n")
