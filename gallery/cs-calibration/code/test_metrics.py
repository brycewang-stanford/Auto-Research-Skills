"""Unit tests (run `unit-tests`, data-prep): plan.json design.method step 13 and analysis_plan.

Hand-made and synthetic inputs only; no study dataset is read (data/raw is never opened).
Covers: the ECE tie rule on hand-computed cases (a tie group spanning a bin edge, an all-tied vector,
row-order invariance, the round-to-12-decimals rule, a brute-force reference), ece_db (Kumar et al.
2019, Def. G.3) on hand cases, clip counts and log-loss, brier against sklearn, LogitScore against
the base model's probabilities, FrozenEstimator leaving the base model bit-identical (and the
calibrators being fitted on the frozen logit scores of all calibration rows), the decision rule,
seed streams, subsample and splits, preprocessing fitted on train only, the manifest-typed CSV
reader, and end-to-end cells of main, sens-ncal and sens-elec-time on synthetic pools of the
study shapes.

Writes runs/unit-tests/metrics.json; exits 1 if any test fails.
"""
from __future__ import annotations

import json
import math
import pickle
import sys
import tempfile
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
from scipy.special import expit
from sklearn.calibration import _sigmoid_calibration
from sklearn.datasets import make_classification
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss
from threadpoolctl import threadpool_limits

import analyze
import describe
import experiment as ex
import sens_elec_time
import sens_ncal

TESTS = []
RECORD: dict = {}


def test(fn):
    TESTS.append(fn)
    return fn


def close(a, b, tol=1e-12):
    return math.isclose(float(a), float(b), rel_tol=tol, abs_tol=tol)


# ---------------------------------------------------------------- ECE: hand-computed cases
def hand_case_tie_across_edge():
    """n = 30, 15 bins (2 per bin if nothing were tied). p_i = (i+1)/100 except p_3 = p_4 = p_5 = 0.05.

    #smaller: i for i in {0,1,2} and i >= 6; 3 for the tie group i = 3,4,5.
    bin = floor(15 * #smaller / 30) = floor(#smaller / 2):
      bin 0 = {i0, i1}, bin 1 = {i2, i3, i4, i5} (the tie group joins its first member's bin),
      bin 2 = empty (dropped), bin k = {i_{2k}, i_{2k+1}} for k = 3..14.  14 non-empty bins.
    y = 1 only at i = 3 and i = 29.
      bin 0: |0 - (.01+.02)|                    = 0.03
      bin 1: |1 - (.03+.05+.05+.05)|            = 0.82
      bins 3..13: |0 - sum p| = .15+.19+...+.55 = 3.85   (11 terms, mean .35)
      bin 14: |1 - (.29+.30)|                   = 0.41
    ece = (0.03 + 0.82 + 3.85 + 0.41) / 30 = 5.11 / 30.
    A positional split (no tie rule) would give bins {i2,i3},{i4,i5}: (0.03+0.92+0.10+3.85+0.41)/30 = 5.31/30.
    """
    p = np.array([(i + 1) / 100 for i in range(30)])
    p[3:6] = 0.05
    y = np.zeros(30)
    y[[3, 29]] = 1
    expected_bins = np.array([0, 0, 1, 1, 1, 1] + [i // 2 for i in range(6, 30)])
    return p, y, expected_bins, 5.11 / 30, 14


@test
def ece_tie_group_spanning_bin_edge():
    p, y, bins, expected, n_bins = hand_case_tie_across_edge()
    assert np.array_equal(ex.equal_mass_bins(p), bins), ex.equal_mass_bins(p)
    e, nb = ex.ece(p, y)
    assert close(e, expected), (e, expected)
    assert nb == n_bins == 14
    assert not close(e, 5.31 / 30)
    RECORD["ece_hand_tie_edge"] = e


@test
def ece_row_order_invariant():
    p, y, _, expected, _ = hand_case_tie_across_edge()
    rng = np.random.default_rng(1)
    for _ in range(20):
        perm = rng.permutation(len(p))
        e, nb = ex.ece(p[perm], y[perm])
        assert close(e, expected) and nb == 14


@test
def ece_all_tied():
    """All 100 predictions 0.3, 40 positives: one bin, ece = |0.4 - 0.3| = 0.1."""
    p = np.full(100, 0.3)
    y = np.r_[np.ones(40), np.zeros(60)]
    assert np.all(ex.equal_mass_bins(p) == 0)
    e, nb = ex.ece(p, y)
    assert close(e, 0.1) and nb == 1, (e, nb)
    RECORD["ece_hand_all_tied"] = e


@test
def ece_distinct_one_per_bin():
    """n = 15 distinct predictions: bin i holds prediction i, so ece = mean |y_i - p_i|."""
    p = (np.arange(15) + 0.5) / 15
    y = (np.arange(15) % 2).astype(float)
    assert np.array_equal(ex.equal_mass_bins(p), np.arange(15))
    e, nb = ex.ece(p, y)
    assert close(e, np.mean(np.abs(y - p))) and nb == 15


@test
def ece_tie_rule_rounds_to_12_decimals():
    """Predictions equal after round(p, 12) are one tie group; means still use the unrounded p."""
    p = np.array([0.2, 0.2 + 1e-14, 0.2 - 1e-14, 0.7])
    y = np.array([1.0, 0.0, 0.0, 1.0])
    # n = 4: #smaller = 0,0,0,3 -> bins floor(15*0/4)=0 (x3), floor(45/4)=11
    assert np.array_equal(ex.equal_mass_bins(p), [0, 0, 0, 11])
    e, nb = ex.ece(p, y)
    expected = (abs(1 - p[:3].sum()) + abs(1 - 0.7)) / 4
    assert close(e, expected) and nb == 2, (e, expected, nb)
    # p differing in the 11th decimal are distinct
    assert np.array_equal(ex.equal_mass_bins(np.array([0.2, 0.2 + 1e-11, 0.9, 0.95])), [0, 3, 7, 11])


@test
def ece_matches_brute_force_with_ties():
    """O(n^2) reference implementation on RF-like predictions (multiples of 0.01, many ties)."""
    rng = np.random.default_rng(7)
    for n in (37, 500, 1351):
        p = np.round(rng.beta(0.6, 0.9, n), 2)
        y = (rng.random(n) < p).astype(float)
        q = np.round(p, 12)
        b = np.array([int(math.floor(15 * sum(qj < qi for qj in q) / n)) for qi in q]) if n <= 500 else \
            np.array([int(15 * np.sum(q < qi) // n) for qi in q])
        tot = 0.0
        for k in np.unique(b):
            m = b == k
            tot += abs(y[m].sum() - p[m].sum())
        e, nb = ex.ece(p, y)
        assert close(e, tot / n), (n, e, tot / n)
        assert nb == len(np.unique(b))
        # a tie group never spans two bins
        for v in np.unique(q):
            assert len(np.unique(b[q == v])) == 1


# ---------------------------------------------------------------- ece_db (Kumar et al. 2019, Def. G.3)
@test
def ece_db_no_correction_when_bin_labels_pure():
    """Every bin's mean label in {0, 1}: zero variance, so ece_db = ece."""
    p = np.linspace(0.05, 0.95, 30)   # 30 distinct sorted values: bin k = {2k, 2k+1}
    y = (np.arange(30) >= 16).astype(float)   # label boundary on a bin edge, so every bin is pure
    w, s, yb, nk = ex.bin_stats(p, y)
    assert set(np.unique(yb)) <= {0.0, 1.0}
    e, _ = ex.ece(p, y)
    db = ex.ece_debiased(p, y, np.random.default_rng(0))
    assert close(db, e), (db, e)


@test
def ece_db_single_bin_hand_value():
    """All p = 0.5, n = 1,000, 500 positives: one bin, ece = 0, so ece_db = -E|N(0, sigma)| with
    sigma = sqrt(0.25/1000); E = sigma*sqrt(2/pi) = 0.012616. M = 1,000 draws: MC SE about 0.0003."""
    p = np.full(1000, 0.5)
    y = np.r_[np.ones(500), np.zeros(500)]
    db = ex.ece_debiased(p, y, np.random.default_rng(123))
    target = -math.sqrt(0.25 / 1000) * math.sqrt(2 / math.pi)
    assert abs(db - target) < 0.0015, (db, target)
    assert db < 0                      # not floored at 0
    RECORD["ece_db_single_bin"] = db
    RECORD["ece_db_single_bin_target"] = target


@test
def ece_db_matches_explicit_formula_and_draw_layout():
    """One rng.normal call of shape (1000, K) over the non-empty bins in increasing bin order."""
    p, y, _, _, _ = hand_case_tie_across_edge()
    y = y.copy()
    y[[0, 7, 8, 12]] = 1               # make several bins impure
    seed = np.random.SeedSequence([1, 2, 3])
    got = ex.ece_debiased(p, y, np.random.default_rng(seed))
    bins = ex.equal_mass_bins(p)
    ks = sorted(set(bins.tolist()))
    n = len(p)
    pk = np.array([np.sum(bins == k) / n for k in ks])
    sk = np.array([p[bins == k].mean() for k in ks])
    yk = np.array([y[bins == k].mean() for k in ks])
    nk = np.array([np.sum(bins == k) for k in ks])
    R = np.random.default_rng(seed).normal(loc=yk, scale=np.sqrt(yk * (1 - yk) / nk), size=(1000, len(ks)))
    plug = sum(pk[i] * abs(sk[i] - yk[i]) for i in range(len(ks)))
    resampled = np.mean([sum(pk[i] * abs(sk[i] - R[m, i]) for i in range(len(ks))) for m in range(1000)])
    assert close(got, 2 * plug - resampled, 1e-10), (got, 2 * plug - resampled)


@test
def ece_db_reproducible_per_child_seed():
    rng = np.random.default_rng(5)
    p = rng.random(2000)
    y = (rng.random(2000) < p).astype(float)
    kids = np.random.SeedSequence([20261119, 0, 0]).spawn(4)[3].spawn(12)
    a = ex.ece_debiased(p, y, np.random.default_rng(kids[4]))
    b = ex.ece_debiased(p, y, np.random.default_rng(np.random.SeedSequence([20261119, 0, 0]).spawn(4)[3].spawn(12)[4]))
    c = ex.ece_debiased(p, y, np.random.default_rng(kids[5]))
    assert a == b and a != c


@test
def ece_db_reduces_floor_for_calibrated_and_not_for_miscalibrated():
    """Sanity: calibrated synthetic predictions -> plug-in ECE at its noise floor, ece_db near 0;
    strongly miscalibrated -> ece_db close to ece."""
    rng = np.random.default_rng(11)
    e_cal, db_cal, e_mis, db_mis = [], [], [], []
    for r in range(20):
        p = rng.random(5000)
        y = (rng.random(5000) < p).astype(float)
        e_cal.append(ex.ece(p, y)[0])
        db_cal.append(ex.ece_debiased(p, y, np.random.default_rng(r)))
        y2 = (rng.random(5000) < p ** 3).astype(float)
        e_mis.append(ex.ece(p, y2)[0])
        db_mis.append(ex.ece_debiased(p, y2, np.random.default_rng(100 + r)))
    # Normal approximation for a calibrated bin with label SE sigma: E|y_k - s_k| = 0.798 sigma (plug-in),
    # and E ece_db = 2(0.798 sigma) - E|N(0, 2 sigma^2)| = (2 - sqrt 2) 0.798 sigma = 0.468 sigma, so
    # E ece_db / E ece = 2 - sqrt(2) = 0.586: Def. G.3 removes about 41% of the l1 floor, not all of it.
    ratio = np.mean(db_cal) / np.mean(e_cal)
    assert 0.005 < np.mean(e_cal) < 0.03, np.mean(e_cal)
    assert 0.45 < ratio < 0.72, ratio
    assert abs(np.mean(db_mis) - np.mean(e_mis)) < 0.05 * np.mean(e_mis)
    RECORD["synthetic_calibrated_ece_mean"] = float(np.mean(e_cal))
    RECORD["synthetic_calibrated_ece_db_mean"] = float(np.mean(db_cal))
    RECORD["synthetic_calibrated_db_ratio"] = float(ratio)
    RECORD["synthetic_calibrated_db_ratio_theory"] = 2 - math.sqrt(2)
    RECORD["synthetic_miscalibrated_ece_mean"] = float(np.mean(e_mis))
    RECORD["synthetic_miscalibrated_ece_db_mean"] = float(np.mean(db_mis))


# ---------------------------------------------------------------- clip counts, log-loss, brier
@test
def clip_counts_hand():
    p = np.array([0.0, 1e-7, 1e-6, 0.5, 1 - 1e-6, 1 - 1e-7, 1.0])
    lo, hi = ex.clip_counts(p)
    assert (lo, hi) == (2, 2), (lo, hi)        # strict inequalities: 1e-6 and 1-1e-6 are not clipped
    RECORD["clip_low_hand"], RECORD["clip_high_hand"] = lo, hi


@test
def logloss_hand_and_against_sklearn():
    p = np.array([0.5, 0.0, 1.0, 0.9])
    y = np.array([1, 0, 0, 1])
    # p = 1.0, y = 0 is clipped to 1 - 1e-6, and 1 - (1 - 1e-6) is not exactly 1e-6 in float64
    expected = (-math.log(0.5) - math.log1p(-1e-6) - math.log(1 - (1 - 1e-6)) - math.log(0.9)) / 4
    assert close(ex.logloss(p, y), expected), (ex.logloss(p, y), expected)
    # machine-epsilon variant equals sklearn.metrics.log_loss in 1.9.1
    assert close(ex.logloss(p, y, ex.EPS_MACH), log_loss(y, p), 1e-10), (ex.logloss(p, y, ex.EPS_MACH), log_loss(y, p))
    rng = np.random.default_rng(3)
    q = rng.random(1000)
    yy = (rng.random(1000) < q).astype(int)
    assert close(ex.logloss(q, yy, ex.EPS_MACH), log_loss(yy, q), 1e-10)
    assert close(ex.logloss(q, yy), log_loss(yy, np.clip(q, 1e-6, 1 - 1e-6)), 1e-10)


@test
def brier_equals_sklearn():
    rng = np.random.default_rng(4)
    for n in (10, 1351, 5000):
        p = rng.random(n)
        y = (rng.random(n) < p).astype(int)
        assert close(ex.brier(p, y), brier_score_loss(y, p))
    assert close(ex.brier(np.array([0.0, 1.0, 0.25]), np.array([0, 0, 1])), (0 + 1 + 0.5625) / 3)


@test
def score_returns_all_metrics():
    rng = np.random.default_rng(9)
    p = np.round(rng.random(500), 2)
    p[:5] = 0.0
    y = (rng.random(500) < p).astype(int)
    out = ex.score(p, y, np.random.default_rng(0))
    assert set(out) == {"brier", "logloss", "logloss_mach", "n_clip_low", "n_clip_high", "ece", "ece_bins",
                        "ece_db", "auc"}
    assert out["n_clip_low"] == int(np.sum(p < 1e-6)) >= 5
    assert all(np.isfinite(v) for v in out.values())


# ---------------------------------------------------------------- LogitScore and FrozenEstimator
def fitted_models_on_synthetic():
    X, y = make_classification(n_samples=3000, n_features=8, n_informative=5, random_state=0)
    Xtr, ytr, Xca, yca, Xte = X[:1500], y[:1500], X[1500:2250], y[1500:2250], X[2250:]
    with threadpool_limits(limits=1):
        models = {"lr": LogisticRegression(max_iter=1000).fit(Xtr, ytr),
                  "rf": RandomForestClassifier(random_state=1, n_jobs=1).fit(Xtr, ytr),
                  "hgb": HistGradientBoostingClassifier(early_stopping=False, random_state=1).fit(Xtr, ytr)}
    return models, Xca, yca, Xte


@test
def logitscore_reproduces_base_probabilities():
    models, _, _, Xte = fitted_models_on_synthetic()
    for name, base in models.items():
        ls = ex.LogitScore(base)
        assert np.array_equal(ls.predict_proba(Xte), base.predict_proba(Xte))
        assert np.array_equal(ls.predict(Xte), base.predict(Xte))
        assert np.array_equal(ls.classes_, base.classes_)
        p = base.predict_proba(Xte)[:, 1]
        pc = np.clip(p, 1e-6, 1 - 1e-6)
        s = ls.decision_function(Xte)
        assert np.allclose(s, np.log(pc / (1 - pc)), rtol=1e-12, atol=1e-12)
        assert np.allclose(expit(s), pc, rtol=1e-9, atol=1e-15)
    # RF gives exact 0/1 probabilities, which map to +/- logit(1 - 1e-6) = +/- 13.8155
    s_rf = ex.LogitScore(models["rf"]).decision_function(Xte)
    assert close(np.max(np.abs(s_rf)), math.log((1 - 1e-6) / 1e-6), 1e-9)
    RECORD["rf_logit_bound"] = float(np.max(np.abs(s_rf)))


@test
def frozen_estimator_leaves_base_model_unchanged():
    models, Xca, yca, Xte = fitted_models_on_synthetic()
    for name, base in models.items():
        before_bytes = pickle.dumps(base)
        p0 = base.predict_proba(Xte)[:, 1].copy()
        ps = ex.calibrated_predictions(base, Xca, yca, Xte)        # asserts bit-identity internally
        assert pickle.dumps(base) == before_bytes, f"{name}: fitted model state changed"
        assert np.array_equal(base.predict_proba(Xte)[:, 1], p0)
        assert np.array_equal(ps["none"], p0)


@test
def calibrators_fit_on_frozen_logit_scores_of_all_calibration_rows():
    """isotonic = IsotonicRegression(out_of_bounds='clip') on the logit scores of every calibration row;
    platt = sklearn's Platt fit on the same scores.

    Isotonic on the logit equals isotonic on the clipped probability AT the calibration scores (same
    ranks, same pooled fit), but sklearn's predict interpolates linearly in the input scale between
    thresholds, so test points between two thresholds differ slightly between the two scales. The size
    of that difference is recorded (iso_logit_vs_prob_max_abs_diff), not asserted to be zero."""
    models, Xca, yca, Xte = fitted_models_on_synthetic()
    for name, base in models.items():
        ls = ex.LogitScore(base)
        s_ca, s_te = ls.decision_function(Xca), ls.decision_function(Xte)
        ps = ex.calibrated_predictions(base, Xca, yca, Xte)
        iso = IsotonicRegression(out_of_bounds="clip").fit(s_ca, yca).predict(s_te)
        assert np.allclose(ps["isotonic"], iso, rtol=0, atol=1e-12), name
        pc_ca = np.clip(base.predict_proba(Xca)[:, 1], 1e-6, 1 - 1e-6)
        pc_te = np.clip(base.predict_proba(Xte)[:, 1], 1e-6, 1 - 1e-6)
        ir_s = IsotonicRegression(out_of_bounds="clip").fit(s_ca, yca)
        ir_p = IsotonicRegression(out_of_bounds="clip").fit(pc_ca, yca)
        assert np.allclose(ir_s.predict(s_ca), ir_p.predict(pc_ca), rtol=0, atol=1e-12), name
        diff = float(np.max(np.abs(ps["isotonic"] - ir_p.predict(pc_te))))
        RECORD[f"iso_logit_vs_prob_max_abs_diff_{name}"] = diff
        assert diff < 0.05, (name, diff)
        a, b = _sigmoid_calibration(s_ca, yca)
        assert np.allclose(ps["platt"], expit(-(a * s_te + b)), rtol=1e-10, atol=1e-12), name
        cal = ex.fit_calibrator(base, Xca, yca, "isotonic")
        assert len(cal.calibrated_classifiers_) == 1          # ensemble=False: one calibrator


# ---------------------------------------------------------------- decision rule
@test
def paired_interval_matches_scipy():
    d = np.arange(1, 11, dtype=float)
    iv = analyze.paired_interval(d)
    lo, hi = stats.t.interval(0.95, 9, loc=d.mean(), scale=stats.sem(d))
    assert close(iv["lo"], lo, 1e-10) and close(iv["hi"], hi, 1e-10)
    assert close(iv["sd"], np.std(d, ddof=1)) and iv["n"] == 10
    assert close(analyze.T_CRIT, 2.2621571628, 1e-9)


@test
def categories_hand_cases():
    c = analyze.categorize
    # H1: predicted d > 0, margin 0.005
    assert c(-0.004, 0.004, 0.005, +1) == 0
    assert c(-0.005, 0.005, 0.005, +1) == 0          # boundary: inclusive
    assert c(0.001, 0.003, 0.005, +1) == 0           # 'no difference' takes precedence over 'holds'
    assert c(0.001, 0.010, 0.005, +1) == 1
    assert c(-0.010, -0.001, 0.005, +1) == 2
    assert c(-0.001, 0.010, 0.005, +1) == 3
    assert c(0.0, 0.010, 0.005, +1) == 3             # lo = 0 is not wholly on the predicted side
    # H2: predicted d < 0, margin 0.001
    assert c(-0.010, -0.002, 0.001, -1) == 1
    assert c(0.002, 0.010, 0.001, -1) == 2
    assert c(-0.0005, 0.0009, 0.001, -1) == 0
    assert c(-0.010, 0.0001, 0.001, -1) == 3
    assert c(-0.0009, -0.0001, 0.001, -1) == 0


@test
def overall_hand_cases():
    o = analyze.overall
    assert o([1, 1, 1, 0]) == 1
    assert o([1, 1, 1, 1]) == 1
    assert o([1, 1, 1, 2]) == 3        # holds on 3 but contradicted on one
    assert o([2, 2, 1, 1]) == 2
    assert o([2, 2, 2, 2]) == 2
    assert o([0, 0, 0, 3]) == 0
    assert o([0, 0, 0, 0]) == 0
    assert o([0, 0, 0, 1]) == 3        # 'no difference' needs holds/contradicted on none
    assert o([1, 1, 3, 3]) == 3
    assert o([2, 0, 0, 0]) == 3


@test
def test_hypothesis_end_to_end_on_synthetic_cells():
    rng = np.random.default_rng(0)
    rows = []
    for ds_i, name in enumerate(analyze.DATASETS):
        for s in range(10):
            base_ece = 0.02 + 0.002 * rng.standard_normal()
            gap = [0.03, 0.03, 0.0005, -0.03][ds_i]   # holds, holds, no difference, contradicted
            for m in ("lr", "rf", "hgb"):
                for c in ("none", "platt", "isotonic"):
                    e = base_ece + (gap + 0.0001 * rng.standard_normal() if m == "rf" else 0.0)
                    b = 0.1 - (0.01 if c == "isotonic" else 0.0) + 0.0001 * rng.standard_normal()
                    rows.append(dict(dataset=name, seed=s, model=m, calibrator=c, ece=e, ece_db=e, brier=b))
    cells = pd.DataFrame(rows)
    res, verdict = analyze.test_hypothesis(cells, "h1")
    assert [r["category_code"] for r in res] == [1, 1, 0, 2], [r["category_code"] for r in res]
    assert verdict == 3
    res2, verdict2 = analyze.test_hypothesis(cells, "h2a")
    assert all(r["category_code"] == 1 for r in res2) and verdict2 == 1
    # pairing: the difference is taken on the same seed
    d = analyze.paired_differences(cells, "adult", "ece", ("rf", "none"), ("lr", "none"))
    assert len(d) == 10 and np.all(d > 0.02)
    # a missing seed is an error
    try:
        analyze.paired_differences(cells[cells["seed"] != 3], "adult", "ece", ("rf", "none"), ("lr", "none"))
    except AssertionError:
        pass
    else:
        raise AssertionError("missing seed not detected")


# ---------------------------------------------------------------- seeds, subsample, splits
@test
def seed_streams_spec():
    st = ex.seed_streams(1, 4)
    sub, split, model, debias = np.random.SeedSequence([20261119, 1, 4]).spawn(4)
    assert st["sub_int"] == int(sub.generate_state(1)[0])
    assert (st["i_test"], st["i_cal"]) == tuple(int(v) for v in split.generate_state(2))
    assert st["rs"] == int(model.generate_state(1)[0])
    assert len(st["debias"]) == 12
    assert np.array_equal(np.random.default_rng(st["debias"][7]).random(3),
                          np.random.default_rng(debias.spawn(12)[7]).random(3))
    again = ex.seed_streams(1, 4)
    assert (again["sub_int"], again["i_test"], again["i_cal"], again["rs"]) == \
        (st["sub_int"], st["i_test"], st["i_cal"], st["rs"])
    assert ex.seed_streams(1, 5)["sub_int"] != st["sub_int"]
    assert ex.seed_streams(2, 4, variant=1)["rs"] != ex.seed_streams(2, 4)["rs"]
    assert ex.debias_index("lr", "none") == 0 and ex.debias_index("rf", "platt") == 4
    assert ex.debias_index("hgb", "isotonic") == 8
    assert [ex.debias_index_ncal(m) for m in ("lr", "rf", "hgb")] == [9, 10, 11]


SHAPES = {  # pool rows, numeric columns, categorical level counts, positive share (study shapes)
    "adult": dict(n=48_842, num=6, cats=[9, 16, 7, 15, 6, 5, 2, 42], pos=0.239),
    "bank-marketing": dict(n=45_211, num=7, cats=[12, 3, 4, 2, 2, 2, 3, 12, 4], pos=0.117),
    "electricity": dict(n=45_312, num=7, cats=[7], pos=0.425),
    "phoneme": dict(n=5_404, num=5, cats=[], pos=0.293),
}


def synthetic_pool(name: str, seed: int = 0, missing: bool = True):
    """make_classification pool with the study shape; categorical columns are strings with missing
    values (np.nan) in one categorical and one numeric column, as the CSV reader delivers them."""
    s = SHAPES[name]
    p = s["num"] + len(s["cats"])
    X, y = make_classification(n_samples=s["n"], n_features=p, n_informative=max(2, min(8, p - 1)),
                               n_redundant=min(2, max(0, p - 9)), weights=[1 - s["pos"]], flip_y=0.02,
                               random_state=1000 + seed)
    num = [f"x{j}" for j in range(s["num"])]
    cat = [f"c{j}" for j in range(len(s["cats"]))]
    df = pd.DataFrame(X[:, :s["num"]], columns=num)
    for j, k in enumerate(s["cats"]):
        z = X[:, s["num"] + j]
        edges = np.quantile(z, np.sort(np.random.default_rng(j).uniform(0, 1, k - 1)))
        df[cat[j]] = pd.Series([f"L{v}" for v in np.searchsorted(edges, z)], dtype=object)
    if missing:
        rng = np.random.default_rng(seed)
        if cat:
            df.loc[rng.random(len(df)) < 0.05, cat[0]] = np.nan
        df.loc[rng.random(len(df)) < 0.02, num[0]] = np.nan
    return df, y.astype(np.int64), num, cat


@test
def subsample_and_split_sizes_large_pool():
    X, y, _, _ = synthetic_pool("adult")
    st = ex.seed_streams(0, 0)
    Xs, ys = ex.subsample(X, y, st["sub_int"])
    assert len(ys) == 20_000 and abs(ys.mean() - y.mean()) < 1e-3           # stratified
    (Xtr, ytr), (Xca, yca), (Xte, yte) = ex.split_random(Xs, ys, st["i_test"], st["i_cal"])
    assert (len(ytr), len(yca), len(yte)) == (10_000, 5_000, 5_000)
    idx = [set(a.index) for a in (Xtr, Xca, Xte)]
    assert not (idx[0] & idx[1]) and not (idx[0] & idx[2]) and not (idx[1] & idx[2])
    assert idx[0] | idx[1] | idx[2] == set(Xs.index)
    for yy in (ytr, yca, yte):
        assert abs(yy.mean() - ys.mean()) < 1e-3
    again = ex.split_random(*ex.subsample(X, y, st["sub_int"]), st["i_test"], st["i_cal"])
    assert list(again[2][0].index) == list(Xte.index)                       # deterministic
    other = ex.seed_streams(0, 1)
    Xs2, _ = ex.subsample(X, y, other["sub_int"])
    overlap = len(set(Xs.index) & set(Xs2.index)) / 20_000
    assert 0.3 < overlap < 0.6                      # about 20,000/48,842 = 41% shared rows


@test
def split_sizes_phoneme_shape_uses_all_rows():
    X, y, _, _ = synthetic_pool("phoneme")
    st = ex.seed_streams(3, 0)
    Xs, ys = ex.subsample(X, y, st["sub_int"])
    assert len(ys) == 5404 and Xs is X
    (Xtr, ytr), (Xca, yca), (Xte, yte) = ex.split_random(Xs, ys, st["i_test"], st["i_cal"])
    assert (len(ytr), len(yca), len(yte)) == (2702, 1351, 1351)
    ex.check_split_sizes(len(ytr), len(yca))
    try:
        ex.check_split_sizes(10_001, 5000)
    except AssertionError:
        pass
    else:
        raise AssertionError("n_train > 10,000 not caught")


@test
def chronological_split_by_file_row():
    X, y, _, _ = synthetic_pool("electricity")
    Xs = X.sample(n=20_000, random_state=0)              # a shuffled subsample, as train_test_split returns
    ys = y[Xs.index.to_numpy()]
    (Xtr, ytr), (Xca, yca), (Xte, yte) = ex.split_chronological(Xs, ys)
    assert (len(ytr), len(yca), len(yte)) == (10_000, 5_000, 5_000)
    assert Xtr.index.is_monotonic_increasing and Xca.index.is_monotonic_increasing
    assert Xtr.index.max() < Xca.index.min() and Xca.index.max() < Xte.index.min()
    assert np.array_equal(ytr, y[Xtr.index.to_numpy()])  # labels follow their rows
    assert ex.vic_fill_counts([0, 17_423, 17_424, 40_000]) == [2]


# ---------------------------------------------------------------- preprocessing and the CSV reader
@test
def preprocessing_fitted_on_train_only():
    X, y, num, cat = synthetic_pool("bank-marketing")
    Xtr, Xca, Xte = X.iloc[:10_000], X.iloc[10_000:15_000].copy(), X.iloc[15_000:20_000].copy()
    Xte.iloc[0, Xte.columns.get_loc(cat[1])] = "UNSEEN_LEVEL"
    pre, (Atr, Aca, Ate) = ex.preprocess(num, cat, Xtr, Xca, Xte)
    imp = pre.named_transformers_["num"].named_steps["impute"]
    assert np.allclose(imp.statistics_, Xtr[num].median().to_numpy())
    sc = pre.named_transformers_["num"].named_steps["scale"]
    assert np.allclose(sc.mean_, Xtr[num].fillna(Xtr[num].median()).mean().to_numpy())
    widths = len(num) + sum(Xtr[c].fillna("missing").nunique() for c in cat)
    assert Atr.shape[1] == Aca.shape[1] == Ate.shape[1] == widths
    assert Atr.dtype == np.float64 and isinstance(Atr, np.ndarray)
    oh = pre.named_transformers_["cat"].named_steps["onehot"]
    assert "missing" in oh.categories_[0]                  # imputed missing level of c0
    # the unseen level gets an all-zero block for that column
    start = len(num) + len(oh.categories_[0])
    block = Ate[0, start:start + len(oh.categories_[1])]
    assert np.all(block == 0)
    assert np.isclose(Atr[:, :len(num)].mean(axis=0), 0, atol=1e-9).all()
    # phoneme shape: numeric only
    Xp, yp, nump, catp = synthetic_pool("phoneme")
    _, (Ap, _, _) = ex.preprocess(nump, catp, Xp.iloc[:2702], Xp.iloc[2702:4053], Xp.iloc[4053:])
    assert Ap.shape[1] == 5


@test
def csv_reader_uses_manifest_types():
    text = ("num_a,cat_b,num_c,cat_d,target\n"
            "1.0,x,2.5,1,0\n"
            ",None,3.0,2,1\n"        # empty numeric -> NaN; 'None' stays a level
            "4.0,,1.0,NA,0\n")       # empty categorical -> NaN; 'NA' stays a level
    entry = {"numeric_features": ["num_a", "num_c"], "categorical_features": ["cat_b", "cat_d"]}
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "toy.csv"
        path.write_text(text)
        X, y = ex.read_dataset_csv(path, entry)
        assert list(X.columns) == ["num_a", "cat_b", "num_c", "cat_d"]     # CSV (OpenML) order kept
        assert X["num_a"].dtype == np.float64 and np.isnan(X["num_a"].iloc[1])
        assert X["cat_b"].dtype == object and X["cat_b"].iloc[1] == "None" and pd.isna(X["cat_b"].iloc[2])
        assert X["cat_d"].tolist() == ["1", "2", "NA"]                      # integer-looking levels stay text
        assert y.tolist() == [0, 1, 0] and y.dtype == np.int64
        bad = {"numeric_features": ["num_a"], "categorical_features": ["cat_b", "cat_d"]}
        try:
            ex.read_dataset_csv(path, bad)
        except AssertionError:
            pass
        else:
            raise AssertionError("header mismatch not detected")


@test
def single_row_level_width_varies_and_summaries_survive():
    """code-r1 F1: a categorical level with a single row (as adult native-country has) is in a seed's
    training split only sometimes, so the one-hot width varies across seeds. The width must equal the
    base width plus one exactly when that row is in train, and main's and describe's summaries must
    record min/max instead of failing."""
    X, y, num, cat = synthetic_pool("adult", missing=False)
    rare_row = 123
    X.loc[rare_row, cat[0]] = "ONLY_ONE_ROW"
    widths, in_train = [], []
    for s in ex.SEEDS:
        st = ex.seed_streams(0, s)
        Xs, ys = ex.subsample(X, y, st["sub_int"])
        (Xtr, _), (Xca, _), (Xte, _) = ex.split_random(Xs, ys, st["i_test"], st["i_cal"])
        _, (Atr, Aca, Ate) = ex.preprocess(num, cat, Xtr, Xca, Xte)
        base = len(num) + sum(Xtr[c][Xtr[c] != "ONLY_ONE_ROW"].nunique() for c in cat)
        inside = rare_row in Xtr.index
        assert Atr.shape[1] == Aca.shape[1] == Ate.shape[1] == base + int(inside), (s, Atr.shape[1], base, inside)
        widths.append(Atr.shape[1])
        in_train.append(inside)
    assert any(in_train) and not all(in_train), in_train      # both cases occur over seeds 0..9
    assert len(set(widths)) == 2, widths
    RECORD["single_row_level_widths"] = "/".join(map(str, widths))

    # main's and describe's summaries on 360 synthetic cells whose width varies by seed
    rng = np.random.default_rng(2)
    rows = []
    for name in ex.DATASETS:
        sizes = (2702, 1351, 1351) if name == "phoneme" else (10_000, 5_000, 5_000)
        for s in ex.SEEDS:
            book = dict(n_train=sizes[0], n_cal=sizes[1], n_test=sizes[2], pos_train=1, pos_cal=1, pos_test=1,
                        width=widths[s], lr_n_iter=50, lr_converged=1, hgb_n_iter=100)
            if name == "electricity":
                book.update(n_vicfill_train=3000, n_vicfill_cal=1500, n_vicfill_test=1500)
            for m in ex.MODELS:
                for c in ex.CALIBRATORS:
                    rows.append(dict(dataset=name, seed=s, model=m, calibrator=c, brier=0.1 + 0.01 * rng.random(),
                                     logloss=0.3 + 0.01 * rng.random(), logloss_mach=0.3, n_clip_low=0, n_clip_high=0,
                                     ece=0.02 + 0.01 * rng.random(), ece_bins=15, ece_db=0.01 * rng.random(),
                                     auc=0.9, **book))
    with tempfile.TemporaryDirectory() as tmp:     # the CSV round trip main -> describe uses
        path = Path(tmp) / "cells.csv"
        ex.write_cells(rows, path)
        cells = pd.read_csv(path)
    m = ex.summarize_main(cells)
    assert m["n_rows"] == 360 and m["n_dataset_seed_cells"] == 40
    assert (m["width_min_adult"], m["width_max_adult"]) == (min(widths), max(widths))
    assert m["n_train_phoneme"] == 2702 and m["n_cal_adult"] == 5000
    summary, paired, dm = describe.describe(cells)
    assert (dm["adult_width_min"], dm["adult_width_max"]) == (min(widths), max(widths))
    assert len(summary) == 324 and len(paired) == 104


# ---------------------------------------------------------------- end-to-end cells on synthetic pools
@test
def main_cell_end_to_end_adult_shape():
    X, y, num, cat = synthetic_pool("adult")
    with threadpool_limits(limits=1):
        out = ex.run_cell(0, 0, X, y, num, cat)
    rows = out["rows"]
    assert len(rows) == 9 and {(r["model"], r["calibrator"]) for r in rows} == \
        {(m, c) for m in ex.MODELS for c in ex.CALIBRATORS}
    r0 = rows[0]
    assert (r0["n_train"], r0["n_cal"], r0["n_test"]) == (10_000, 5_000, 5_000)
    assert r0["hgb_n_iter"] == 100 and r0["lr_converged"] in (0, 1) and r0["lr_n_iter"] > 0
    assert r0["pos_train"] + r0["pos_cal"] + r0["pos_test"] == round(20_000 * y.mean()) or \
        abs(r0["pos_train"] + r0["pos_cal"] + r0["pos_test"] - 20_000 * y.mean()) <= 1
    assert set(out["preds"]) == {f"p_{m}_{c}" for m in ex.MODELS for c in ex.CALIBRATORS}
    assert all(v.shape == (5000,) and v.dtype == np.float64 for v in out["preds"].values())
    for r in rows:
        for k in ("brier", "logloss", "logloss_mach", "ece", "ece_db", "auc"):
            assert np.isfinite(r[k]), (r["model"], r["calibrator"], k)
        assert 1 <= r["ece_bins"] <= 15
    # metric values equal a recomputation from the saved predictions
    yt = out["y_test"]
    for r in rows:
        p = out["preds"][f"p_{r['model']}_{r['calibrator']}"]
        assert close(r["brier"], np.mean((p - yt) ** 2)) and close(r["ece"], ex.ece(p, yt)[0])
    RECORD["synthetic_adult_width"] = r0["width"]
    RECORD["synthetic_adult_rf_none_ece"] = next(r["ece"] for r in rows if r["model"] == "rf" and r["calibrator"] == "none")


@test
def main_cell_deterministic_phoneme_shape():
    X, y, num, cat = synthetic_pool("phoneme")
    with threadpool_limits(limits=1):
        a = ex.run_cell(3, 2, X, y, num, cat)
        b = ex.run_cell(3, 2, X, y, num, cat)
    for ra, rb in zip(a["rows"], b["rows"]):
        assert ra == rb, "run_cell not deterministic"
    for k in a["preds"]:
        assert np.array_equal(a["preds"][k], b["preds"][k])
    assert (a["rows"][0]["n_train"], a["rows"][0]["n_cal"], a["rows"][0]["n_test"]) == (2702, 1351, 1351)


@test
def sens_ncal_cell_uses_main_base_models():
    X, y, num, cat = synthetic_pool("bank-marketing")
    with threadpool_limits(limits=1):
        main_out = ex.run_cell(1, 0, X, y, num, cat)
        nc = sens_ncal.ncal_cell(1, 0, X, y, num, cat)
    for m in ex.MODELS:
        main_none = next(r["brier"] for r in main_out["rows"] if r["model"] == m and r["calibrator"] == "none")
        assert nc["base_brier"][m] == main_none, m            # same frozen base model as main
    assert len(nc["rows"]) == 3 and all(r["n_cal_sub"] == 1351 for r in nc["rows"])
    assert np.array_equal(nc["y_test"], main_out["y_test"])    # same test split
    iso_main = next(r["brier"] for r in main_out["rows"] if r["model"] == "rf" and r["calibrator"] == "isotonic")
    iso_sub = next(r["brier"] for r in nc["rows"] if r["model"] == "rf")
    assert iso_main != iso_sub                                  # a different calibration set was used


@test
def sens_elec_time_cell_chronological():
    X, y, num, cat = synthetic_pool("electricity")
    with threadpool_limits(limits=1):
        out = sens_elec_time.chrono_cell(0, X, y, num, cat)
    r = out["rows"][0]
    assert len(out["rows"]) == 9
    assert (r["n_train"], r["n_cal"], r["n_test"]) == (10_000, 5_000, 5_000)
    assert r["first_row_cal"] > r["first_row_train"] and r["first_row_test"] > r["first_row_cal"]
    assert r["n_vicfill_train"] + r["n_vicfill_cal"] + r["n_vicfill_test"] > 0
    # all rows before 17,424 that are in the subsample fall in the earliest half here
    assert r["n_vicfill_cal"] == 0 and r["n_vicfill_test"] == 0
    st_main, st_time = ex.seed_streams(2, 0), ex.seed_streams(2, 0, variant=1)
    assert st_main["sub_int"] != st_time["sub_int"]


# ---------------------------------------------------------------- runner
def main() -> int:
    passed, failed = [], []
    for fn in TESTS:
        try:
            fn()
            passed.append(fn.__name__)
            print(f"PASS {fn.__name__}")
        except Exception:  # noqa: BLE001 - report every failure
            failed.append(fn.__name__)
            print(f"FAIL {fn.__name__}\n{traceback.format_exc()}")
    out = Path("runs/unit-tests")
    out.mkdir(parents=True, exist_ok=True)
    metrics = dict(tests_run=len(TESTS), tests_passed=len(passed), tests_failed=len(failed),
                   reads_study_data=0, **RECORD)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"{len(passed)}/{len(TESTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
