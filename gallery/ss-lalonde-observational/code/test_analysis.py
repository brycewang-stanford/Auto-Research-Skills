"""Unit tests (run `unit-tests`, data-prep): every analysis script, on hand-made and synthetic data only.

No study file is read: data/raw, data/derived and runs/ of this workspace are never opened. The
end-to-end tests build throw-away synthetic workspaces in a temporary directory (respects
TMPDIR) with raw files in the format of the Dehejia data page (ten fields, '%.7e' with a
three-digit exponent), derive the working file with the real code/prepare_data.py (expected row
counts patched to the synthetic counts), run the real code/diag_overlap.py on it, and then run
the real main() of every analysis script with the workspace as working directory.

Covers: constants fixed by the design (seeds, folds, clip, bound, grids); B(X), B(X-), the
reduced bases and T(X) (term lists and counts, equality with diag_overlap.basis_B); the outcome
validity rule and the counts by arm; the AIPW ATT score, the upper-only clip and the
aggregation rule on hand cases; the estimator on a large synthetic sample with oracle nuisances;
the H1 rule, the H3 verdict rule, the disagreement comparison, control-only trimming; the
relative-effect delta method; the join rule (exact match, field mismatch, unmatched rows,
non-numeric re78) and the joined-outcome reader; the IPOW score; Hajek IPW and HC2 against
hand computations; the Imbens model (R2 maps, tau(0,0) = OLS, sign of the bias, R2* rule);
H2's formula; that only h2_benchmark.py contains the benchmark; that only main_aipw.py reads
data/raw; that the placebo runs with data/raw and the joined outcome removed; and every script
end to end on a synthetic workspace without missing outcomes (true ATT 1,500) and one with
missing and inadmissible re78 values (rob-ipow triggered), including every metric named by
plan.json design.claim_ids.

Tests run with one OpenMP thread (threadpoolctl); the analysis runs themselves do not limit threads.

Writes runs/unit-tests/metrics.json; exits 1 if any test fails.

Run from the workspace root:  .venv/bin/python -I code/test_analysis.py
"""

from __future__ import annotations

import ast
import contextlib
import io
import json
import math
import os
import re
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.special import expit
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

CODE = Path(__file__).resolve().parent
sys.path.insert(0, str(CODE))
import aipw_lib as L  # noqa: E402
import diag_overlap  # noqa: E402
import h2_benchmark  # noqa: E402
import main_aipw  # noqa: E402
import placebo_re75  # noqa: E402
import prepare_data  # noqa: E402
import rob_covsets  # noqa: E402
import rob_diff74  # noqa: E402
import rob_estimators  # noqa: E402
import rob_ipow  # noqa: E402
import rob_learners  # noqa: E402
import rob_trim  # noqa: E402
import sens_imbens  # noqa: E402

ORIG = Path.cwd()
OUT = ORIG / "runs/unit-tests/metrics.json"
TESTS: list = []
RECORD: dict = {}
TRUE_ATT = 1500.0
SYNTH_SEED = 7

ANALYSIS_SCRIPTS = ["aipw_lib.py", "main_aipw.py", "placebo_re75.py", "rob_trim.py", "rob_covsets.py",
                    "rob_learners.py", "rob_estimators.py", "rob_diff74.py", "rob_ipow.py",
                    "sens_imbens.py", "h2_benchmark.py"]

# plan.json design.claim_ids -> (run, metric). sens groups: g in GROUPS.
CLAIM_METRICS = {
    "primary-effect": ("main-aipw", "effect"), "primary-ci-low": ("main-aipw", "ci_low"),
    "primary-ci-high": ("main-aipw", "ci_high"), "primary-se": ("main-aipw", "se"),
    "primary-p": ("main-aipw", "p"), "primary-n": ("main-aipw", "n"),
    "primary-n-treated": ("main-aipw", "n_treated"), "primary-n-control": ("main-aipw", "n_control"),
    "primary-n-clipped": ("main-aipw", "n_clipped_units"),
    "primary-treated-mean": ("main-aipw", "treated_mean"), "primary-cf-mean": ("main-aipw", "cf_mean"),
    "primary-rel-effect": ("main-aipw", "rel_effect"), "primary-rel-ci-low": ("main-aipw", "rel_ci_low"),
    "primary-rel-ci-high": ("main-aipw", "rel_ci_high"),
    "primary-re78-invalid-treated": ("main-aipw", "unobserved_re78_treated"),
    "primary-re78-invalid-control": ("main-aipw", "unobserved_re78_control"),
    "overlap-treated-above-09": ("main-aipw", "share_treated_above_09"),
    "overlap-kish-ess": ("main-aipw", "kish_ess_controls"),
    "overlap-max-control-weight": ("main-aipw", "max_control_weight"),
    "placebo-effect": ("placebo-re75", "effect"), "placebo-se": ("placebo-re75", "se"),
    "placebo-ci-low": ("placebo-re75", "ci_low"), "placebo-ci-high": ("placebo-re75", "ci_high"),
    "placebo-verdict": ("placebo-re75", "verdict_code"),
    "placebo-n-clipped": ("placebo-re75", "n_clipped_units"),
    "trim-effect": ("rob-trim", "effect"), "trim-ci-low": ("rob-trim", "ci_low"),
    "trim-ci-high": ("rob-trim", "ci_high"), "trim-n-control-kept": ("rob-trim", "n_control_kept"),
    "trim-n-control-dropped": ("rob-trim", "n_control_dropped"),
    "covset-a-effect": ("rob-covsets", "covset_a_effect"), "covset-a-ci-low": ("rob-covsets", "covset_a_ci_low"),
    "covset-a-ci-high": ("rob-covsets", "covset_a_ci_high"),
    "covset-b-effect": ("rob-covsets", "covset_b_effect"), "covset-b-ci-low": ("rob-covsets", "covset_b_ci_low"),
    "covset-b-ci-high": ("rob-covsets", "covset_b_ci_high"),
    "learner-linear-effect": ("rob-learners", "linear_effect"),
    "learner-linear-ci-low": ("rob-learners", "linear_ci_low"),
    "learner-linear-ci-high": ("rob-learners", "linear_ci_high"),
    "learner-rf-effect": ("rob-learners", "rf_effect"), "learner-rf-ci-low": ("rob-learners", "rf_ci_low"),
    "learner-rf-ci-high": ("rob-learners", "rf_ci_high"),
    "ols-coef": ("rob-estimators", "ols_effect"), "ols-ci-low": ("rob-estimators", "ols_ci_low"),
    "ols-ci-high": ("rob-estimators", "ols_ci_high"), "ipw-effect": ("rob-estimators", "ipw_effect"),
    "ipw-ci-low": ("rob-estimators", "ipw_ci_low"), "ipw-ci-high": ("rob-estimators", "ipw_ci_high"),
    "diff74-effect": ("rob-diff74", "effect"), "diff74-ci-low": ("rob-diff74", "ci_low"),
    "diff74-ci-high": ("rob-diff74", "ci_high"),
    "ipow-re78-effect": ("rob-ipow", "effect"), "ipow-re78-ci-low": ("rob-ipow", "ci_low"),
    "ipow-re78-ci-high": ("rob-ipow", "ci_high"),
    "sens-r2-zero": ("sens-imbens", "r2star_zero"), "sens-tau00": ("sens-imbens", "tau00"),
    "h2-diff": ("h2-benchmark", "h2_diff"), "h2-se-combined": ("h2-benchmark", "h2_se_combined"),
    "h2-ci-low": ("h2-benchmark", "h2_ci_low"), "h2-ci-high": ("h2-benchmark", "h2_ci_high"),
}
for _g in sens_imbens.GROUPS:
    CLAIM_METRICS[f"sens-bench-{_g}-r2d"] = ("sens-imbens", f"bench_{_g}_r2d")
    CLAIM_METRICS[f"sens-bench-{_g}-r2y"] = ("sens-imbens", f"bench_{_g}_r2y")
    CLAIM_METRICS[f"sens-bench-{_g}-bias"] = ("sens-imbens", f"bench_{_g}_abs_bias")


def test(fn):
    TESTS.append(fn)
    return fn


def close(a, b, tol=1e-10):
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


def check(cond, msg=""):
    if not cond:
        raise AssertionError(msg)


def expect_exit(fn, *args):
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            fn(*args)
    except SystemExit as e:
        return str(e.code)
    raise AssertionError(f"{getattr(fn, '__name__', fn)} did not stop")


@contextlib.contextmanager
def cwd(path: Path):
    old = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(old)


def quiet(fn, *args):
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*args)


# ---------------------------------------------------------------- synthetic data
def synth_frame(n: int = 2500, seed: int = SYNTH_SEED) -> pd.DataFrame:
    """Covariates like the study's, treatment from a logit in B(X)-type terms, potential outcomes
    with a constant effect TRUE_ATT (so the sample ATT is exactly TRUE_ATT)."""
    rng = np.random.default_rng(seed)
    age = rng.integers(16, 56, n)
    educ = np.clip(np.round(rng.normal(11.5, 2.8, n)), 0, 18).astype(int)
    u = rng.random(n)
    black = (u < 0.25).astype(int)
    hisp = ((u >= 0.25) & (u < 0.33)).astype(int)
    married = (rng.random(n) < 0.6).astype(int)
    nodegree = (educ < 12).astype(int)
    re74 = np.where(rng.random(n) < 0.25, 0.0,
                    np.minimum(np.round(rng.lognormal(np.log(10000), 0.7, n), 2), 25862.32))
    re75 = np.where(rng.random(n) < 0.22, 0.0,
                    np.minimum(np.round(0.6 * re74 + rng.lognormal(np.log(5000), 0.7, n), 2), 25243.55))
    u74, u75 = (re74 == 0).astype(int), (re75 == 0).astype(int)
    idx = (-3.0 - 0.03 * (age - 30) - 0.1 * (educ - 11) + 1.0 * black + 0.3 * hisp - 0.5 * married
           + 0.4 * u74 + 0.4 * u75 - 0.00004 * (re75 - 5000))
    treat = (rng.random(n) < expit(idx)).astype(int)
    y0 = (2500 + 0.35 * re75 + 0.25 * re74 + 250 * (educ - 11) - 700 * black + 1200 * married
          + 40 * (age - 30) + rng.normal(0, 2500, n))
    y0 = np.round(np.clip(y0, 0, 90000), 2)
    re78 = np.round(y0 + TRUE_ATT * treat, 2)
    return pd.DataFrame({"treat": treat, "age": age, "educ": educ, "black": black, "hisp": hisp,
                         "married": married, "nodegree": nodegree, "re74": re74, "re75": re75,
                         "re78": re78, "u74": u74, "u75": u75})


def tok(v) -> str:
    """'%.7e' with a three-digit exponent, as on the Dehejia data page; strings pass through."""
    if isinstance(v, str):
        return v
    s = f"{float(v):.7e}"
    mant, exp = s.split("e")
    return f"{mant}e{exp[0]}{int(exp[1:]):03d}"


def write_raw(ws: Path, df: pd.DataFrame, re78_tokens: list | None = None) -> None:
    raw = ws / "data/raw"
    raw.mkdir(parents=True, exist_ok=True)
    fields = ["treat", "age", "educ", "black", "hisp", "married", "nodegree", "re74", "re75", "re78"]
    toks = df[fields].astype(object).to_numpy()
    if re78_tokens is not None:
        toks[:, 9] = re78_tokens
    for name, t in (("nswre74_treated.txt", 1), ("cps_controls.txt", 0)):
        rows = toks[df["treat"].to_numpy() == t]
        (raw / name).write_text("".join("  " + "  ".join(tok(v) for v in r) + "\n" for r in rows),
                                encoding="ascii")


def build_ws(root: Path, df: pd.DataFrame, re78_tokens: list | None = None) -> Path:
    """Synthetic workspace: raw files -> prepare_data.py -> diag_overlap.py (both the real code)."""
    ws = root
    (ws / "runs").mkdir(parents=True, exist_ok=True)
    write_raw(ws, df, re78_tokens)
    n1, n0 = int(df.treat.sum()), int((1 - df.treat).sum())
    saved = dict(prepare_data.RAW)
    prepare_data.RAW["nswre74_treated"] = (saved["nswre74_treated"][0], n1, 1)
    prepare_data.RAW["cps_controls"] = (saved["cps_controls"][0], n0, 0)
    argv = sys.argv
    try:
        with cwd(ws):
            check(quiet(prepare_data.main) == 0, "prepare_data failed on synthetic files")
            sys.argv = ["diag_overlap.py"]
            check(quiet(diag_overlap.main) == 0, "diag_overlap failed on synthetic files")
    finally:
        prepare_data.RAW.clear(); prepare_data.RAW.update(saved)
        sys.argv = argv
    return ws


def ordered_like_derived(df: pd.DataFrame) -> pd.DataFrame:
    """Row order of the derived file: treated file first, then CPS file, each in file order."""
    return pd.concat([df[df.treat == 1], df[df.treat == 0]], ignore_index=True)


def metrics(ws: Path, run: str) -> dict:
    return json.loads((ws / "runs" / run / "metrics.json").read_text())


# ---------------------------------------------------------------- constants
@test
def test_constants():
    check(L.SEED == 20261118 and L.K == 5 and L.S == 5, "seed/folds/repetitions")
    check(L.CLIP_HI == 0.99, "upper clip")
    check(close(L.Z95, 1.959963984540054), "z")
    check(L.PLACEBO_BOUND == 900.0, "placebo bound")
    check(rob_estimators.B_IPW == 999 and rob_estimators.IPW_SEED == 20261120, "IPW bootstrap")
    check(rob_ipow.R_FLOOR == 0.05 and main_aipw.IPOW_GAP == 0.02, "rob-ipow constants")
    check(sens_imbens.EM_MAX_ITER == 200 and sens_imbens.EM_TOL == 1e-8, "EM")
    check(len(sens_imbens.GRID) ** 2 * 2 == 128 and len(sens_imbens.DIAG) * 2 == 22, "grid sizes")
    check(len(sens_imbens.GROUPS) == 8, "8 benchmark groups")
    check(128 + 22 + 2 * len(sens_imbens.GROUPS) == 166, "166 EM points")
    check(diag_overlap.propensity_learner is L.propensity_learner, "propensity learner reused")
    lr = L.propensity_learner(5)[-1]
    check(lr.Cs.shape == (10,) and close(lr.Cs[0], 1e-4) and close(lr.Cs[-1], 1e4), "Cs")
    check(lr.scoring == "neg_log_loss" and lr.solver == "lbfgs" and lr.max_iter == 10_000, "LRCV")
    check(lr.cv.random_state == 5 and lr.cv.n_splits == 5 and lr.cv.shuffle, "inner CV seed")
    hgb = L.outcome_learner(3)
    check((hgb.learning_rate, hgb.max_iter, hgb.max_leaf_nodes, hgb.min_samples_leaf,
           hgb.l2_regularization, hgb.early_stopping, hgb.random_state)
          == (0.05, 300, 15, 20, 1.0, False, 3), "outcome learner")
    rf = rob_learners.rf_c(9)
    check((rf.n_estimators, rf.min_samples_leaf, rf.max_features, rf.random_state)
          == (500, 5, "sqrt", 9), "random forest")


# ---------------------------------------------------------------- bases
@test
def test_bases():
    df = synth_frame(300)
    check(L.check_basis_reuse(df) is None, "basis reuse")
    full = L.basis(df, L.COVS)
    check(list(full.columns) == ["age", "age_sq", "educ", "educ_sq", "black", "hisp", "married",
                                 "nodegree", "re74", "re74_sq", "re75", "re75_sq", "u74", "u75"], "B(X) terms")
    check(L.X_MINUS == ["age", "educ", "black", "hisp", "married", "nodegree", "re74", "u74"], "X-")
    bm = L.basis(df, L.X_MINUS)
    check(list(bm.columns) == ["age", "age_sq", "educ", "educ_sq", "black", "hisp", "married",
                               "nodegree", "re74", "re74_sq", "u74"], "B(X-) terms")
    check(L.tree_features(df, L.X_MINUS).shape[1] == 8, "T(X-) 8")
    check(L.basis(df, L.COVSET_A).shape[1] == 11 and L.tree_features(df, L.COVSET_A).shape[1] == 7, "covset a")
    check(L.basis(df, L.COVSET_B).shape[1] == 11 and L.tree_features(df, L.COVSET_B).shape[1] == 8, "covset b")
    check(set(L.COVS) - set(L.COVSET_A) == {"black", "hisp", "nodegree"}, "covset a drops")
    check(set(L.COVS) - set(L.COVSET_B) == {"re74", "u74"}, "covset b drops")
    check(L.basis(df, L.TIME_INVARIANT).shape[1] == 8 and L.tree_features(df, L.TIME_INVARIANT).shape[1] == 6,
          "time-invariant set")
    check(np.array_equal(L.tree_features(df, L.COVS), df[L.COVS].to_numpy(float)), "T(X) unscaled")
    check(np.allclose(full["re74_sq"], df.re74 ** 2), "squares")


# ---------------------------------------------------------------- outcome validity
@test
def test_admissible_and_counts():
    v = np.array([0.0, 5.5, -1.0, np.nan, np.inf, 100.0, 9999999.0])
    check(L.admissible(v).tolist() == [True, True, False, False, False, True, False], "sentinel above max")
    v2 = np.array([100.0, 99999.0, 200000.0])
    check(L.admissible(v2).tolist() == [True, True, True], "sentinel not above max stays")
    y = np.array([1.0, np.nan, -2.0, 3.0, np.nan, 4.0])
    d = np.array([1, 1, 1, 0, 0, 0])
    c = L.outcome_counts(y, d, "re78")
    check((c["missing_re78_treated"], c["inadmissible_re78_treated"], c["unobserved_re78_treated"]) == (1, 1, 2))
    check((c["missing_re78_control"], c["inadmissible_re78_control"], c["unobserved_re78_control"]) == (1, 0, 1))
    check(close(c["share_unobserved_re78_treated"], 2 / 3) and close(c["share_unobserved_re78_control"], 1 / 3))


# ---------------------------------------------------------------- AIPW score
@test
def test_att_hand_case():
    d = np.array([1, 1, 0, 0])
    y = np.array([10.0, 8.0, 3.0, 1.0])
    g = np.tile([4.0, 4.0, 2.0, 2.0], (L.S, 1))
    m = np.tile([0.5, 0.5, 0.5, 0.25], (L.S, 1))
    r = L.att_from_nuisances(d, y, m, g)
    num = np.array([6.0, 4.0, -1.0, 1 / 3])
    theta = num.sum() / 2
    psi = (num - d * theta) / 0.5
    check(close(r["theta"], theta), "theta")
    check(close(r["se"], math.sqrt(np.mean(psi ** 2) / 4)), "se")
    check(r["n_clipped_units"] == 0, "no clipping")
    w0 = np.array([1.0, 1 / 3])
    check(close(r["kish_ess_controls"], w0.sum() ** 2 / np.sum(w0 ** 2)) and close(r["max_control_weight"], 1.0))


@test
def test_clip_upper_only_and_aggregation():
    d = np.array([1, 0, 0, 1, 0])
    y = np.array([5.0, 2.0, 1.0, 7.0, 3.0])
    rng = np.random.default_rng(1)
    g = rng.normal(2, 1, (L.S, 5))
    m = np.tile([0.5, 0.995, 1e-9, 0.3, 0.2], (L.S, 1))
    m[2, 4] = 0.999  # unit 4 clipped in one repetition only
    r = L.att_from_nuisances(d, y, m, g)
    check(r["n_clipped_units"] == 2 and r["n_clipped_unit_reps"] == L.S + 1, "clip counts")
    thetas, ses = [], []
    for s in range(L.S):
        mm = np.minimum(m[s], 0.99)
        w = mm / (1 - mm)
        num = d * (y - g[s]) - (1 - d) * w * (y - g[s])
        th = num.sum() / d.sum()
        psi = (num - d * th) / d.mean()
        thetas.append(th); ses.append(math.sqrt(np.mean(psi ** 2) / 5))
    thetas, ses = np.array(thetas), np.array(ses)
    check(close(r["theta"], thetas.mean()), "mean aggregation")
    check(close(r["se"], math.sqrt(np.mean(ses ** 2 + (thetas - thetas.mean()) ** 2))), "variance rule")
    # no floor: the 1e-9 unit has weight ~1e-9, the 0.995 unit has weight 99
    mm = np.minimum(m[0], 0.99)
    check(close((mm / (1 - mm))[2], 1e-9 / (1 - 1e-9)) and close((mm / (1 - mm))[1], 99.0), "weights")


@test
def test_oracle_estimator_recovers_att():
    rng = np.random.default_rng(11)
    n = 200_000
    x = rng.normal(size=n)
    p = expit(-3 + 0.8 * x)
    d = (rng.random(n) < p).astype(int)
    g0 = 1000 + 500 * x
    y = g0 + 300 * d + rng.normal(0, 1000, n)
    r = L.att_from_nuisances(d, y, np.tile(p, (L.S, 1)), np.tile(g0, (L.S, 1)))
    RECORD["oracle_att_estimate"] = r["theta"]
    check(abs(r["theta"] - 300) < 4 * r["se"], f"oracle {r['theta']:.1f} (se {r['se']:.1f}) vs 300")


@test
def test_rules():
    check(L.h1_holds(0.01) and not L.h1_holds(0.0) and not L.h1_holds(-5), "H1 rule")
    V = L.placebo_verdict
    check(V(10, 500) == ("fail", -1) and V(-500, -1) == ("fail", -1), "fail")
    check(V(1000, 2000) == ("fail", -1), "fail takes precedence")
    check(V(-900, 900) == ("pass", 1) and V(0.0, 10) == ("pass", 1), "pass, bounds inclusive")
    check(V(-899.9, 950) == ("inconclusive", 0) and V(-950, 100) == ("inconclusive", 0), "inconclusive")
    main = {"h1_holds": True, "ci_low": 100.0, "ci_high": 900.0}
    c = L.compare_with_main({"x_effect": 950.0, "x_ci_low": -10.0, "x_h1_holds": False}, "x_", main)
    check(c == {"x_h1_differs_from_main": True, "x_effect_outside_main_ci95": True}, "compare")
    c = L.compare_with_main({"effect": 500.0, "ci_low": 50.0, "h1_holds": True}, "", main)
    check(c == {"h1_differs_from_main": False, "effect_outside_main_ci95": False}, "compare 2")


@test
def test_trim_keep():
    m_bar = np.array([0.2, 0.05, 0.01, 0.05, 0.2, 0.3, 0.001])
    d = np.array([1, 1, 0, 0, 0, 0, 1])
    keep = L.trim_keep(m_bar, d)
    check(keep.tolist() == [True, True, True, True, True, False, True], "trim, inclusive")
    d2 = np.array([1, 1, 0, 0, 0, 0, 0])
    keep2 = L.trim_keep(m_bar, d2)
    check(keep2.tolist() == [True, True, False, True, True, False, False], "drops below and above")
    check(keep2[d2 == 1].all(), "treated never dropped")


@test
def test_relative_effect_delta_method():
    rng = np.random.default_rng(3)
    n = 50
    d = (rng.random(n) < 0.3).astype(int)
    y = rng.normal(100, 10, n)
    psi_theta = rng.normal(0, 5, n)
    res = {"theta": 12.0, "psi_bar": psi_theta}
    out = L.relative_effect(d, y, res)
    mu1 = y[d == 1].mean()
    check(close(out["rel_effect"], 12.0 / (mu1 - 12.0)) and close(out["cf_mean"], mu1 - 12.0))
    eps = 1e-6
    f = lambda th, mu: th / (mu - th)  # noqa: E731
    dth = (f(12 + eps, mu1) - f(12 - eps, mu1)) / (2 * eps)
    dmu = (f(12, mu1 + eps) - f(12, mu1 - eps)) / (2 * eps)
    psi_r = dth * psi_theta + dmu * d * (y - mu1) / d.mean()
    check(close(out["rel_se"], math.sqrt(np.mean(psi_r ** 2) / n), 1e-6), "delta method")


@test
def test_ipow_score():
    rng = np.random.default_rng(5)
    n = 400
    d = (rng.random(n) < 0.2).astype(int)
    y = rng.normal(10, 3, n)
    m = np.tile(np.clip(rng.random(n), 0.01, 0.98), (L.S, 1))
    g = rng.normal(9, 1, (L.S, n))
    a = L.att_from_nuisances(d, y, m, g)
    b = L.att_ipow_from_nuisances(d, y, np.ones(n, int), np.ones((L.S, n)), m, g)
    check(close(a["theta"], b["theta"]) and close(a["se"], b["se"]), "R = 1, r = 1 equals AIPW")
    # Oracle MAR check on a large sample.
    n = 200_000
    x = rng.normal(size=n)
    p = expit(-2.5 + 0.7 * x)
    d = (rng.random(n) < p).astype(int)
    g0 = 1000 + 400 * x
    y = g0 + 250 * d + rng.normal(0, 800, n)
    r_true = expit(1.5 - 0.8 * x - 1.0 * d)
    R = (rng.random(n) < r_true).astype(int)
    y_obs = np.where(R == 1, y, np.nan)
    o = L.att_ipow_from_nuisances(d, y_obs, R, np.tile(np.maximum(r_true, 0.05), (L.S, 1)),
                                  np.tile(p, (L.S, 1)), np.tile(g0, (L.S, 1)))
    RECORD["oracle_ipow_estimate"] = o["theta"]
    check(np.isfinite(o["theta"]) and abs(o["theta"] - 250) < 4 * o["se"], f"ipow {o['theta']:.1f}")


@test
def test_csv_float_round_trip():
    """The join compares floats exactly, so pandas' default CSV parser must round-trip repr and %.10g."""
    rng = np.random.default_rng(12)
    v = np.concatenate([rng.lognormal(8, 2, 20000), np.round(rng.uniform(0, 90000, 20000), 2)])
    text = "x\n" + "\n".join([repr(float(x)) for x in v] + [f"{x:.10g}" for x in v])
    got = pd.read_csv(io.StringIO(text))["x"].to_numpy()
    check(np.array_equal(got, np.array([float(t) for t in text.split("\n")[1:]])), "default parser exact")


# ---------------------------------------------------------------- join rule
@test
def test_join_rule():
    tmp = Path(tempfile.mkdtemp(prefix="lalonde-join-"))
    try:
        df = synth_frame(400, seed=21)
        ws = build_ws(tmp / "ws", df)
        exp = ordered_like_derived(df)
        with cwd(ws):
            cov = diag_overlap.load()
            y = L.join_re78_from_raw(cov)
            check(np.array_equal(y, exp["re78"].to_numpy(float)), "joined re78 equals generated values")
            L.write_re78(cov, y)
            check(np.array_equal(L.load_re78(cov), y), "re78_by_key round trip")
            check(list(pd.read_csv(L.RE78_FILE).columns) == ["src", "row", "re78"], "joined file columns")
            # A shuffled key file is refused.
            pd.read_csv(L.RE78_FILE).iloc[::-1].to_csv(L.RE78_FILE, index=False)
            expect_exit(L.load_re78, cov)
            raw = Path("data/raw/cps_controls.txt")
            text = raw.read_text()
            lines = text.splitlines(keepends=True)
            # A covariate differing in the last printed digit is refused.
            f = lines[3].split()
            f[7] = tok(float(f[7]) + 0.01) if float(f[7]) > 0 else tok(1.0)
            raw.write_text("".join(lines[:3] + ["  " + "  ".join(f) + "\n"] + lines[4:]))
            check("mismatch" in expect_exit(L.join_re78_from_raw, cov), "field mismatch")
            # A missing raw line is refused.
            raw.write_text("".join(lines[:-1]))
            check("unmatched" in expect_exit(L.join_re78_from_raw, cov), "unmatched row")
            # An extra field is refused.
            raw.write_text("".join(lines[:-1] + [lines[-1].rstrip("\n") + "  1.0000000e+000\n"]))
            check("fields" in expect_exit(L.join_re78_from_raw, cov), "field count")
            # A non-numeric re78 token becomes NaN.
            f = lines[0].split(); f[9] = "NA"
            raw.write_text("".join(["  " + "  ".join(f) + "\n"] + lines[1:]))
            y2 = L.join_re78_from_raw(cov)
            n1 = int(cov.treat.sum())
            check(np.isnan(y2[n1]) and np.isfinite(np.delete(y2, n1)).all(), "NA token -> NaN")
            raw.write_text(text)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------- other estimators
@test
def test_hajek_and_hc2():
    rng = np.random.default_rng(8)
    n = 600
    X = rng.normal(size=(n, 3))
    d = (rng.random(n) < expit(-1.5 + X[:, 0])).astype(int)
    y = 2 + X @ np.array([1.0, -0.5, 0.2]) + 1.5 * d + rng.normal(0, 1 + 0.5 * np.abs(X[:, 1]), n)
    theta, nclip = rob_estimators.hajek(d, y, X, 0.7)
    m = make_pipeline(StandardScaler(), LogisticRegression(C=0.7, solver="lbfgs", max_iter=10_000)) \
        .fit(X, d).predict_proba(X)[:, 1]
    w = np.minimum(m, 0.99) / (1 - np.minimum(m, 0.99))
    manual = y[d == 1].mean() - np.sum(w[d == 0] * y[d == 0]) / np.sum(w[d == 0])
    check(close(theta, manual) and nclip == int((m > 0.99).sum()), "Hajek")
    fit, k = rob_estimators.ols_hc2(d, y, X)
    W = sm.add_constant(np.column_stack([d, X]), has_constant="add")
    XtXi = np.linalg.inv(W.T @ W)
    e = y - W @ (XtXi @ W.T @ y)
    h = np.einsum("ij,jk,ik->i", W, XtXi, W)
    V = XtXi @ (W.T * (e ** 2 / (1 - h))) @ W @ XtXi
    check(k == 5 and close(fit.bse[1], math.sqrt(V[1, 1]), 1e-8), "HC2")


@test
def test_imbens_model():
    for r in (0.0, 0.01, 0.1, 0.3):
        check(close(sens_imbens.r2d_of(sens_imbens.alpha_of(r)), r), "R2_D map")
    rng = np.random.default_rng(4)
    n = 3000
    X = rng.normal(size=(n, 4))
    d = (rng.random(n) < expit(-2 + X[:, 0] - 0.5 * X[:, 1])).astype(int)
    y = 5 + X @ np.array([1.0, 2.0, -1.0, 0.5]) + 2.0 * d + rng.normal(0, 2, n)
    mod = sens_imbens.Imbens(d, y, X)
    b0 = mod.fit(0.0, 0.0)
    ols = sm.OLS(y, sm.add_constant(np.column_stack([d, X]))).fit()
    check(b0["converged"] and close(b0["tau"], ols.params[1], 1e-8), "tau(0,0) = OLS")
    s0 = math.sqrt(mod.sigma0_sq)
    a, dl = sens_imbens.alpha_of(0.1), 2 * s0 * math.sqrt(0.1)
    bp = mod.fit(a, dl)["tau"] - b0["tau"]
    bn = mod.fit(a, -dl)["tau"] - b0["tau"]
    bp2 = mod.fit(sens_imbens.alpha_of(0.2), 2 * s0 * math.sqrt(0.2))["tau"] - b0["tau"]
    RECORD["imbens_bias_pos_r2_01"] = bp
    check(bp < 0 < bn and bp2 < bp, f"bias signs/monotone: {bp:.4f}, {bn:.4f}, {bp2:.4f}")
    # R2* reading rule.
    D = sens_imbens.DIAG
    dm = [10 * r for r in D]  # |bias| = 10 * R2
    r2, oog = sens_imbens.r2_star(dm, 0.5)
    check(close(r2, 0.05) and not oog, "exact grid point")
    r2, oog = sens_imbens.r2_star(dm, 0.6)
    check(close(r2, 0.05 + (0.6 - 0.5) * (0.075 - 0.05) / (0.75 - 0.5)) and not oog, "interpolation")
    r2, oog = sens_imbens.r2_star(dm, 0.01)
    check(close(r2, 0.001) and not oog, "interpolation from R2 = 0")
    check(sens_imbens.r2_star(dm, 5.0) == (0.30, True), "out of grid")
    terms = sorted(t for g in sens_imbens.GROUPS.values() for t in g)
    check(terms == sorted(L.basis(synth_frame(50), L.COVS).columns), "groups partition B(X)")


@test
def test_h2_formula():
    out = h2_benchmark.h2(1000.0, 500.0)
    se = math.sqrt(500.0 ** 2 + h2_benchmark.BENCH_SE ** 2)
    check(close(out["h2_diff"], 1000.0 - h2_benchmark.BENCH) and close(out["h2_se_combined"], se))
    check(close(out["h2_ci_low"], out["h2_diff"] - L.Z95 * se) and close(out["h2_ci_high"], out["h2_diff"] + L.Z95 * se))


# ---------------------------------------------------------------- static checks on the scripts
@test
def test_benchmark_only_in_h2():
    b, s = int(h2_benchmark.BENCH), int(h2_benchmark.BENCH_SE)
    pats = [re.compile(rf"(?<![\d.]){b}(?![\d])"), re.compile(rf"(?<![\d.]){b // 1000},{b % 1000:03d}(?!\d)"),
            re.compile(rf"(?<![\d.]){s}(?![\d])")]
    offenders = []
    for f in sorted(CODE.glob("*.py")):
        if f.name == "h2_benchmark.py":
            continue
        text = f.read_text()
        offenders += [f"{f.name}:{p.pattern}" for p in pats if p.search(text)]
    check(not offenders, f"benchmark found in {offenders}")
    h2src = (CODE / "h2_benchmark.py").read_text()
    check("aipw_lib" not in h2src and "data/" not in h2src, "h2 reads only main-aipw's metrics")


@test
def test_raw_read_only_by_main():
    def names(name):
        """Identifiers and attribute names used in the code, and non-docstring string constants."""
        tree = ast.parse((CODE / name).read_text())
        docs = {id(n.body[0].value) for n in ast.walk(tree)
                if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef)) and n.body
                and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
        out = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Name):
                out.add(n.id)
            elif isinstance(n, ast.Attribute):
                out.add(n.attr)
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
                out.add(n.value)
        return out
    for name in ANALYSIS_SCRIPTS:
        if name == "aipw_lib.py":
            continue
        used = names(name)
        raw = {"join_re78_from_raw", "RAW_FILES"} & used or any("data/raw" in u for u in used)
        check(bool(raw) == (name == "main_aipw.py"), f"{name}: raw access {raw}")
    used = names("placebo_re75.py")
    check(not {"load_re78", "RE78_FILE", "re78"} & used, "placebo reads the joined outcome")


# ---------------------------------------------------------------- end to end
@test
def test_end_to_end_synthetic():
    tmp = Path(tempfile.mkdtemp(prefix="lalonde-e2e-"))
    try:
        df = synth_frame()
        ws = build_ws(tmp / "a", df)
        diag = metrics(ws, "diag-overlap")
        RECORD["e2e_n"], RECORD["e2e_n_treated"] = diag["n"], diag["n_treated"]
        RECORD["e2e_diag_smd_w_max_abs"] = diag["smd_w_max_abs"]
        check(diag["rule_B1_pass"] and diag["final_basis"] == "B(X)", "synthetic B1 must pass for the e2e test")
        with cwd(ws):
            check(quiet(main_aipw.main) == 0, "main-aipw")
            m = metrics(ws, "main-aipw")
            exp = ordered_like_derived(df)
            got = pd.read_csv("data/derived/re78_by_key.csv")
            check(np.array_equal(got["re78"].to_numpy(), exp["re78"].to_numpy(float)), "joined file")
            check(m["max_abs_diff_mbar_vs_diag_overlap"] < 1e-12, "m_bar = diag-overlap (csv has 12 digits)")
            check(m["unobserved_re78_treated"] == 0 and m["unobserved_re78_control"] == 0, "no missing")
            check(m["ipow_trigger"] is False, "trigger off")
            check(m["n"] == diag["n"] and m["n_control"] == diag["n_control"], "n")
            check(m["h1_holds"] == (m["ci_low"] > 0), "H1 flag")
            check(close(m["kish_ess_controls"], diag["kish_ess_controls"], 1e-9)
                  and close(m["max_control_weight"], diag["max_control_weight"], 1e-9), "weights = diag")
            RECORD["e2e_main_effect"], RECORD["e2e_main_se"] = m["effect"], m["se"]
            check(abs(m["effect"] - TRUE_ATT) < 4 * m["se"], f"ATT {m['effect']:.1f} (se {m['se']:.1f})")

            # Placebo with data/raw and the joined outcome removed.
            os.rename("data/raw", "data/raw_hidden")
            os.rename("data/derived/re78_by_key.csv", "data/derived/re78_hidden.csv")
            try:
                check(quiet(placebo_re75.main) == 0, "placebo")
            finally:
                os.rename("data/raw_hidden", "data/raw")
                os.rename("data/derived/re78_hidden.csv", "data/derived/re78_by_key.csv")
            p = metrics(ws, "placebo-re75")
            check(p["basis_n_terms"] == 11 and p["tree_n_columns"] == 8, "placebo bases")
            check("re75" not in p["basis_terms"] and "u75" not in p["basis_terms"], "placebo X-")
            check((p["verdict"], p["verdict_code"]) == L.placebo_verdict(p["ci_low"], p["ci_high"]), "verdict")
            RECORD["e2e_placebo_effect"], RECORD["e2e_placebo_verdict_code"] = p["effect"], p["verdict_code"]

            for mod in (rob_trim, rob_learners, rob_covsets, rob_estimators, rob_diff74, sens_imbens):
                check(quiet(mod.main) == 0, mod.__name__)
            check("not planned" in expect_exit(rob_ipow.main), "rob-ipow refuses without trigger")
            check(quiet(h2_benchmark.main) == 0, "h2")

            t = metrics(ws, "rob-trim")
            check(t["n_treated_dropped"] == 0 and t["n_treated"] == diag["n_treated"], "trim keeps treated")
            check(t["n_control_dropped"] == diag["trim_n_control_dropped"]
                  and t["n_control_dropped_matches_diag_overlap"], "trim count = diag-overlap")
            check(t["max_abs_diff_mbar_vs_diag_overlap"] < 1e-12, "trim m_bar")
            RECORD["e2e_trim_n_control_dropped"] = t["n_control_dropped"]
            c = metrics(ws, "rob-covsets")
            check(c["covset_a_basis_n_terms"] == 11 and c["covset_a_tree_n_columns"] == 7
                  and c["covset_b_basis_n_terms"] == 11 and c["covset_b_tree_n_columns"] == 8, "covset bases")
            check(c["covset_a_dropped_covariates"] == "black,hisp,nodegree", "covset a dropped")
            e = metrics(ws, "rob-estimators")
            check(e["ols_n_regressors"] == 16, "OLS regressors")
            dd = metrics(ws, "rob-diff74")
            check(dd["basis_n_terms"] == 8 and dd["tree_n_columns"] == 6, "diff74 bases")
            s = metrics(ws, "sens-imbens")
            check(s["em_points"] == 167, "166 points + tau(0,0)")
            check(abs(s["tau00_minus_ols"]) < 1e-6 * max(1.0, abs(s["tau00"])), "tau00 = OLS")
            check(close(s["tau00"], e["ols_effect"], 1e-6), "tau00 = rob-estimators (a)")
            check(close(s["target_zero"], min(abs(m["ci_low"]), abs(m["ci_high"]))), "t_0")
            RECORD["e2e_sens_r2star_zero"] = s["r2star_zero"]
            RECORD["e2e_em_nonconverged"] = s["em_nonconverged_points"]
            h = metrics(ws, "h2-benchmark")
            check(close(h["h2_diff"], m["effect"] - h2_benchmark.BENCH), "h2")

            # Every metric named by design.claim_ids exists (rob-ipow: second workspace).
            missing = [cid for cid, (run, key) in CLAIM_METRICS.items()
                       if run != "rob-ipow" and key not in metrics(ws, run)]
            check(not missing, f"claim metrics missing: {missing}")

            # Rerun determinism of main-aipw on the same files.
            before = metrics(ws, "main-aipw")
            check(quiet(main_aipw.main) == 0 and metrics(ws, "main-aipw") == before, "main-aipw deterministic")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


@test
def test_end_to_end_missing_outcomes():
    tmp = Path(tempfile.mkdtemp(prefix="lalonde-e2e-miss-"))
    try:
        df = synth_frame()
        toks = [tok(v) for v in df["re78"]]
        t_idx = np.flatnonzero(df.treat.to_numpy() == 1)
        c_idx = np.flatnonzero(df.treat.to_numpy() == 0)
        n_sent = max(2, int(round(0.1 * len(t_idx))))
        for i in t_idx[:n_sent]:
            toks[i] = tok(9999999.0)
        toks[c_idx[0]] = "NA"
        toks[c_idx[1]] = tok(-1.0)
        ws = build_ws(tmp / "b", df, toks)
        with cwd(ws):
            check(quiet(main_aipw.main) == 0, "main-aipw")
            m = metrics(ws, "main-aipw")
            check(m["inadmissible_re78_treated"] == n_sent and m["missing_re78_control"] == 1
                  and m["inadmissible_re78_control"] == 1, "counts")
            check(m["n"] == len(df) - n_sent - 2 and m["n_treated"] == len(t_idx) - n_sent, "complete cases")
            check(m["ipow_trigger"] is True, "trigger fires")
            check("max_abs_diff_mbar_vs_diag_overlap" not in m, "no m_bar comparison on a subsample")
            check(quiet(rob_ipow.main) == 0, "rob-ipow")
            o = metrics(ws, "rob-ipow")
            check(o["n"] == len(df) and o["n_observed"] == len(df) - n_sent - 2, "ipow sample")
            check(all(k in o for k in ("effect", "ci_low", "ci_high")) and np.isfinite(o["effect"]), "ipow metrics")
            RECORD["e2e_ipow_effect"], RECORD["e2e_ipow_se"] = o["effect"], o["se"]
            check(abs(o["effect"] - TRUE_ATT) < 4 * o["se"], f"ipow ATT {o['effect']:.1f}")
            check(quiet(rob_trim.main) == 0, "rob-trim on complete cases")
            check("max_abs_diff_mbar_vs_diag_overlap" not in metrics(ws, "rob-trim"), "trim subsample")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main() -> int:
    passed, failed = 0, []
    for fn in TESTS:
        try:
            # One OpenMP thread for the tests only (HistGradientBoosting on a few thousand rows
            # spin-waits badly on a loaded machine); fitted values do not depend on the thread count.
            with threadpool_limits(limits=1, user_api="openmp"):
                fn()
            passed += 1
            print(f"PASS {fn.__name__}")
        except Exception:  # noqa: BLE001
            failed.append(fn.__name__)
            print(f"FAIL {fn.__name__}\n{traceback.format_exc()}")
    os.chdir(ORIG)
    out = {"tests_run": len(TESTS), "tests_passed": passed, "tests_failed": len(failed),
           "failed_tests": ",".join(failed), "reads_study_data": 0, "true_att_synthetic": TRUE_ATT}
    out.update(RECORD)
    L.write_metrics(OUT, out)
    print(f"{passed}/{len(TESTS)} tests passed")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
