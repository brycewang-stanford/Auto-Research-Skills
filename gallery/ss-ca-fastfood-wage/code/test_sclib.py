"""check-methods (analysis_plan 0f; data-prep; Prop 99 and synthetic data only).

    python3 code/test_sclib.py            the run (every part, full replications)

Inputs  data/raw/synthdid/california_prop99.csv        (i)
        data/derived/state_panel_pre.csv               (iii) and (iv): (iv) reads the pop column only
        data/derived/state_panel.csv                   (iii) only: seasonal factors, which use
                                                       2014Q1-2019Q4 rows only; no statistic of any
                                                       later quarter is computed
Output  runs/check-methods/metrics.json, runs/check-methods/mc_rates.csv

(i)   Prop 99 (39 states, 1970-2000, treated from 1989): DID and SDID (zeta = (1 x 12)^(1/4)
      sigma_hat) must lie in the rounding interval of the value Arkhangelsky et al. (2021) Table 1
      prints: DID [-27.35, -27.25), SDID [-15.65, -15.55). The paper's SC (no intercept, zeta =
      1e-6 sigma_hat, no time weights) is judged by design.method C3: (i-SC-1) sclib's estimate
      equals, to within 1e-3 packs, that of exact_simplex_ls below (a primal active-set solve
      that shares no code with sclib.simplex_ls; its own KKT residual <= 1e-6), and sclib's KKT
      residual is <= 1e-6; (i-SC-2) the Frank-Wolfe port of synthdid (commit 70c1ce3 defaults:
      100 iterations, weights <= max/4 set to 0 and renormalised, up to 10,000 iterations,
      min_decrease 1e-5 sigma_hat), fed the problem sclib builds (sclib.sdid_unit_problem,
      sclib.sigma_hat), lies in [-19.65, -19.55); its unsparsified value is reported too.
      Printed to 3 decimals.
(ii)  Synthetic panels, one treated unit, 20 and 50 donors, known effect: DD/DDT closed forms equal
      OLS TWFE (unit and time effects; unit trends fitted on the trend window for DDT; population
      weights included) to 1e-10; SC and SDID recover exact weights when the treated unit is a
      convex combination; demeaned SC equals the SDID routine with zeta = 0 and uniform time
      weights; every weight solve meets the KKT conditions to 1e-6.
(iii) Seasonal factors from state_panel_pre.csv equal those from state_panel.csv.
(iv)  Monte Carlo of the inference (design.method INFERENCE, DEGREES OF FREEDOM, C1, C2): see
      PASS_TEXT. The SDID calibration draws (C1) come first, from default_rng(20261122); the (iv)
      panels come from default_rng(20261121) exactly as in the first run.
(v)   select_rule.py and level_mde.py raise an error if their input holds a quarter after 2019Q4.

The script records every check as a metric and exits 0 when it completes; a failed check is a
metric equal to 0, not a crash (the run record keeps the evidence).
Options --parts, --reps-scale, --synthetic-pops and --out exist for development only; the run
uses none of them.
"""
import sys
from pathlib import Path

import argparse
import io
import multiprocessing as mp
import os
import time

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats

import sclib as S

PROP99 = Path("data/raw/synthdid/california_prop99.csv")
PRE = Path("data/derived/state_panel_pre.csv")
FULL = Path("data/derived/state_panel.csv")
OUT_DIR = Path("runs/check-methods")
SEED = 20261121
SEED_CAL = 20261122                     # SDID calibration draws (design.method C1)
CAL_R = {"D20": 4000, "R50": 1000}      # per rho
SC1_TOL = 1e-3
KKT_TOL = 1e-6
EQ_TOL = 1e-10
W_TOL = 1e-5      # weight recovery (SLSQP's attainable accuracy on exact-fit problems)

PROP99_TARGETS = {"did": (-27.35, -27.25), "sdid": (-15.65, -15.55)}
SC_PRINT = (-19.65, -19.55)             # i-SC-2: the printed -19.6's rounding interval

MC_DESIGNS = ["pureB", "pureA", "mixed", "heteroA", "heteroA_CA2"]
MC_RHOS = [0.0, 0.5]
MC_EST = [("DD-POPW-E", "D20", 2000), ("DDT-POPW-E", "D20", 2000), ("SC-E", "D20", 2000),
          ("SDID-E", "D20", 2000), ("DD-POPW-E", "R50", 2000), ("DDT-POPW-E", "R50", 2000),
          ("SC-E", "R50", 500), ("SDID-E", "R50", 500)]
MC_R = {"D20": 2000, "R50": 2000}       # panels drawn per pool and design (SC/SDID R50 use 500)
MC_B = S.qidx(2017, 2)
MC_SIGMA2 = 1e-4

PASS_TEXT = """check-methods (iv) pass conditions, stated before the Monte Carlo runs
(R = replications; band(r) = 3 sqrt(r (1 - r) / R); California treated at 2017Q2, true effect 0;
SE = max(SE_s, SE_n); J = 20 (D20) or 50 (R50)):
 (a) pure B, pure A, mixed (rho 0 and 0.5): with t_J critical values, California's upper and
     lower one-sided 5% tests and its two-sided 5% test each reject at most 0.05 + band(0.05).
     A failure of (a) is returned to the Designer before the design gate.
 (b) hetero-A: nu_MC = min(J, (sum_j s_j^2)^2 / sum_j s_j^4), s_j^2 = variance of donor j's placebo
     estimate across the R replications; r1 = 1 - F_{nu_MC}(t_{J,0.95}) (each one-sided tail),
     r2 = 2 (1 - F_{nu_MC}(t_{J,0.975})) (two-sided). Each t_J rate at most r + band(r), and each
     rate at t_{nu_MC} at most 0.05 + band(0.05). A failure of (b) is a bug to look for (C2: the
     SDID-E D20 rho = 0 cell is expected to fail again with the same draws).
 (a-SDID) replaces (a) for SDID-E (design.method C1): on the same replications, pure A, pure B and
     mixed, both pools and both rho, each tail and the two-sided test reject at most
     0.05 + band(0.05) with critical values max(t_J, q_cal,hi(p)) and min(-t_J, q_cal,lo(p)),
     q_cal from the calibration draws (pure A, rho 0 and 0.5, D20 4,000 and R50 1,000 each,
     default_rng(20261122)): q_cal,hi(p) = the larger over rho of the p-quantile of T (method
     'higher'), q_cal,lo(p) = the smaller (method 'lower'). SDID's t_J rates are reported as
     uncorrected. A failure of (a-SDID) is a bug to look for.
 (c) hetero-A-CA2: report-only, at t_J and at t_{nu_MC} with its own nu_MC.
Reported next to them: scaled-only (SE_s) and unscaled-only (SE_n) rates at t_J; SDID-E's rates
with the floor in every design (report-only outside (a-SDID))."""


# --------------------------------------------------------------------------- helpers

def kkt_reset():
    S.SOLVER_LOG.update({"solves": 0, "kkt_max": 0.0, "not_converged": 0, "kkt_above_1e6": 0})


def in_interval(x, lo_hi):
    return int(lo_hi[0] <= x < lo_hi[1])


def synthetic_panel_df(rng, units, first=(2014, 1), last=(2026, 1), effect=0.0,
                       effect_from=S.qidx(2024, 2), unit_trends=False, noise=0.02,
                       suppress=None):
    """A synthetic state panel with the columns of data/derived/state_panel.csv. Log employment =
    unit effect + common quarter effect (with seasonality) + optional unit trend + noise; the
    first unit gets `effect` (log points) from effect_from on. Wages, populations and the 7225 /
    722511 / 10 series are generated alike. suppress: units whose 7225 row is missing in 2024Q4."""
    q0, q1 = S.qidx(*first), S.qidx(*last)
    qs = np.arange(q0, q1 + 1)
    T, N = len(qs), len(units)
    season = np.array([0.0, 0.03, 0.05, -0.02])[qs % 4]
    common = 0.004 * (qs - q0) + season
    rows = []
    for i, u in enumerate(units):
        a = rng.normal(10.0, 1.0)
        tr = rng.normal(0.0, 0.002) if unit_trends else 0.0
        e = rng.normal(0.0, noise, T)
        le = a + common + tr * (qs - q0) + e + (effect if i == 0 else 0.0) * (qs >= effect_from)
        lp = a + 4.0 + 0.002 * (qs - q0) + rng.normal(0, 0.001)
        lw = 6.0 + 0.006 * (qs - q0) + season * 0.5 + rng.normal(0, noise, T)
        emp = np.exp(le)
        for k, q in enumerate(qs):
            y, qq = q // 4, q % 4 + 1
            e7225 = emp[k] * 2.1 * np.exp(rng.normal(0, 0.005))
            sup = int(suppress is not None and u in suppress and q == S.qidx(2024, 4))
            rows.append({"state_fips": u, "state_abbr": u, "year": y, "qtr": qq,
                         "quarter": f"{y}Q{qq}", "emp_722513": emp[k],
                         "emp_722511": emp[k] * 0.9 * np.exp(rng.normal(0, 0.005)),
                         "emp_7225": np.nan if sup else e7225,
                         "emp_10": emp[k] * 25 * np.exp(rng.normal(0, 0.003)),
                         "emp_nonff": 0.0, "sep_722513": emp[k] * np.exp(rng.normal(0, 0.004)),
                         "wages_722513": 13 * emp[k] * np.exp(lw[k]),
                         "aww_722513": np.exp(lw[k]), "pop": np.exp(lp[k]), "pop_extrap": 0,
                         "sup_7225": sup})
    df = pd.DataFrame(rows)
    df["emp_nonff"] = df["emp_10"] - df["emp_722513"]
    return df


# --------------------------------------------------------------------------- (i) Prop 99

def exact_simplex_ls(A, b, pen=0.0, tol=1e-13, max_iter=1000):
    """Independent exact solve of min ||A w - b||^2 + pen ||w||^2 over the simplex: a primal
    active-set method whose subproblems (the equality-constrained least squares on the free set)
    are solved exactly from their KKT system by numpy.linalg.lstsq. Shares no code with
    sclib.simplex_ls (design.method C3 i-SC-1; IMPLEMENTATION CHOICES 3). The objective is
    divided by b'b (scale-free residual). Returns (w, own KKT residual)."""
    A = np.asarray(A, float)
    b = np.asarray(b, float)
    n = A.shape[1]
    scale = float(b @ b) if float(b @ b) > 0 else 1.0
    H = 2.0 * (A.T @ A + pen * np.eye(n)) / scale
    g = 2.0 * (A.T @ b) / scale
    w = np.full(n, 1.0 / n)
    free = np.ones(n, bool)
    for _ in range(max_iter):
        idx = np.flatnonzero(free)
        k = len(idx)
        K = np.zeros((k + 1, k + 1))
        K[:k, :k] = H[np.ix_(idx, idx)]
        K[:k, k] = 1.0
        K[k, :k] = 1.0
        sol = np.linalg.lstsq(K, np.concatenate([g[idx], [1.0]]), rcond=None)[0]
        v = np.zeros(n)
        v[idx] = sol[:k]
        neg = idx[v[idx] < 0]
        if len(neg):
            steps = w[neg] / (w[neg] - v[neg])
            j = neg[int(np.argmin(steps))]
            w = np.maximum(w + float(steps.min()) * (v - w), 0.0)
            w[j] = 0.0
            free[j] = False
            continue
        w = v
        grad = H @ w - g
        mu = float(grad[idx].mean())
        out = np.flatnonzero(~free)
        if len(out) == 0 or (grad[out] - mu).min() >= -tol:
            break
        free[out[int(np.argmin(grad[out] - mu))]] = True
    w = np.maximum(w, 0.0)
    w = w / w.sum()
    grad = H @ w - g
    lam = float(w @ grad)
    resid = float(np.max(np.abs(np.minimum(w, grad - lam))))
    return w, resid


def fw_step(A, x, b, eta):
    """synthdid fw.step (R package synthdid, commit 70c1ce3)."""
    Ax = A @ x
    half_grad = (Ax - b) @ A + eta * x
    i = int(np.argmin(half_grad))
    d_x = -x.copy()
    d_x[i] = 1 - x[i]
    if np.all(d_x == 0):
        return x
    d_err = A[:, i] - Ax
    step = -(half_grad @ d_x) / (d_err @ d_err + eta * (d_x @ d_x))
    return x + min(1.0, max(0.0, step)) * d_x


def fw_weights(A, b, eta, x=None, min_decrease=1e-3, max_iter=1000):
    """synthdid sc.weight.fw on the problem min ||A x - b||^2 + eta ||x||^2 (its objective value is
    that divided by the number of rows; it stops when an iteration lowers it by min_decrease^2
    or less)."""
    N0, n = A.shape
    x = np.full(n, 1.0 / n) if x is None else x
    vals, t = [], 0
    while t < max_iter and (t < 2 or vals[-2] - vals[-1] > min_decrease ** 2):
        x = fw_step(A, x, b, eta)
        err = A @ x - b
        vals.append((eta * np.sum(x ** 2) + np.sum(err ** 2)) / N0)
        t += 1
    return x


def fw_synthdid(A, b, eta, min_decrease, sparsify=True):
    """synthdid's default: 100 iterations, sparsify (weights <= max/4 set to 0, renormalised),
    then up to 10,000 iterations; unsparsified: up to 10,000 iterations from uniform."""
    if not sparsify:
        return fw_weights(A, b, eta, min_decrease=min_decrease, max_iter=10000)
    x = fw_weights(A, b, eta, min_decrease=min_decrease, max_iter=100)
    x = np.where(x <= x.max() / 4, 0.0, x)
    return fw_weights(A, b, eta, x=x / x.sum(), min_decrease=min_decrease, max_iter=10000)


def part_i(m):
    kkt_reset()
    df = pd.read_csv(PROP99, sep=";")
    W = df.pivot(index="State", columns="Year", values="PacksPerCapita")
    treated = df[df.treated == 1]
    m["p99_states"], m["p99_years"] = int(W.shape[0]), int(W.shape[1])
    m["p99_treated_rows"] = int(len(treated))
    m["p99_treated_is_ca_1989_2000"] = int(set(treated.State) == {"California"}
                                           and treated.Year.min() == 1989 and treated.Year.max() == 2000)
    y = W.loc["California"].to_numpy(float)
    Y = W.loc[[s for s in W.index if s != "California"]].to_numpy(float)
    years = W.columns.to_numpy()
    pre, post = np.flatnonzero(years < 1989), np.flatnonzero(years >= 1989)
    m["p99_T_pre"], m["p99_T_post"], m["p99_N_co"] = len(pre), len(post), Y.shape[0]
    wins = {"pooled": post}
    did = float((y[post].mean() - y[pre].mean()) - (Y[:, post].mean() - Y[:, pre].mean()))
    sdid, f_sdid = S.sdid_fit(y, Y, pre, wins, tpost=len(post))
    sig = S.sigma_hat(Y, pre)
    sc, f_sc = S.sdid_fit(y, Y, pre, wins, zeta=1e-6 * sig, unit_intercept=False, time_weights=False)
    est = {"did": did, "sdid": sdid["pooled"]}
    m["p99_sigma_hat"] = sig
    m["p99_zeta_sdid"] = f_sdid["zeta"]
    for k, v in est.items():
        m[f"p99_{k}"] = v
        m[f"p99_{k}_3dp"] = round(v, 3)
        m[f"p99_{k}_lo"], m[f"p99_{k}_hi"] = PROP99_TARGETS[k]
        m[f"p99_{k}_pass"] = in_interval(v, PROP99_TARGETS[k])
    m["p99_kkt_max"] = S.SOLVER_LOG["kkt_max"]
    m["p99_kkt_pass"] = int(S.SOLVER_LOG["kkt_max"] <= KKT_TOL)
    # SC (design.method C3)
    A, b, pen = S.sdid_unit_problem(y, Y, pre, 1e-6 * sig, unit_intercept=False)
    sc_val = sc["pooled"]
    m["p99_sc"] = sc_val
    m["p99_sc_3dp"] = round(sc_val, 3)
    m["p99_sc_kkt"] = float(f_sc["solves"][0]["kkt"])
    w_ex, kkt_ex = exact_simplex_ls(A, b, pen)
    sc_ex = float(np.mean(y[post] - w_ex @ Y[:, post]))
    m["p99_sc_exact"] = sc_ex
    m["p99_sc_exact_3dp"] = round(sc_ex, 3)
    m["p99_sc_exact_kkt"] = kkt_ex
    m["i_sc_1_absdiff"] = abs(sc_val - sc_ex)
    m["i_sc_1_pass"] = int(abs(sc_val - sc_ex) <= SC1_TOL and kkt_ex <= KKT_TOL
                           and m["p99_sc_kkt"] <= KKT_TOL)
    w_fw = fw_synthdid(A, b, pen, 1e-5 * sig, sparsify=True)
    w_fw0 = fw_synthdid(A, b, pen, 1e-5 * sig, sparsify=False)
    m["p99_sc_fw_sparsified"] = float(np.mean(y[post] - w_fw @ Y[:, post]))
    m["p99_sc_fw_sparsified_3dp"] = round(m["p99_sc_fw_sparsified"], 3)
    m["p99_sc_fw_unsparsified"] = float(np.mean(y[post] - w_fw0 @ Y[:, post]))
    m["p99_sc_fw_unsparsified_3dp"] = round(m["p99_sc_fw_unsparsified"], 3)
    m["i_sc_2_lo"], m["i_sc_2_hi"] = SC_PRINT
    m["i_sc_2_pass"] = in_interval(m["p99_sc_fw_sparsified"], SC_PRINT)
    m["part_i_pass"] = int(m["p99_did_pass"] and m["p99_sdid_pass"] and m["p99_kkt_pass"]
                           and m["i_sc_1_pass"] and m["i_sc_2_pass"])
    print(f"(i) Prop 99: DID {did:.3f}, SDID {est['sdid']:.3f}; SC sclib {sc_val:.3f}, exact "
          f"{sc_ex:.3f}, FW sparsified {m['p99_sc_fw_sparsified']:.3f}, FW unsparsified "
          f"{m['p99_sc_fw_unsparsified']:.3f}")


# --------------------------------------------------------------------------- (ii) synthetic

def twfe_dd(Y, wts, Bp, post):
    """WLS of y_it on unit and time dummies and D = 1(unit 0, t in post) over periods {B} + post."""
    per = [Bp] + list(post)
    N = Y.shape[0]
    rows, yv, wv = [], [], []
    for i in range(N):
        for k, t in enumerate(per):
            x = np.zeros(N + len(per) - 1 + 1)
            x[i] = 1.0
            if k > 0:
                x[N + k - 1] = 1.0
            x[-1] = float(i == 0 and k > 0)
            rows.append(x)
            yv.append(Y[i, t])
            wv.append(wts[i])
    fit = sm.WLS(np.array(yv), np.array(rows), weights=np.array(wv)).fit()
    return float(fit.params[-1])


def twfe_trends(Y, wts, tpos):
    """WLS on the trend window with unit effects, time effects and unit trends (the last unit's
    trend is the reference). Returns the unit trends."""
    N = Y.shape[0]
    tp = list(tpos)
    rows, yv, wv = [], [], []
    for i in range(N):
        for k, t in enumerate(tp):
            x = np.zeros(N + (len(tp) - 1) + (N - 1))
            x[i] = 1.0
            if k > 0:
                x[N + k - 1] = 1.0
            if i < N - 1:
                x[N + len(tp) - 1 + i] = float(t)
            rows.append(x)
            yv.append(Y[i, t])
            wv.append(wts[i])
    fit = sm.WLS(np.array(yv), np.array(rows), weights=np.array(wv)).fit()
    return np.append(fit.params[N + len(tp) - 1:], 0.0)


def part_ii(m, rng):
    kkt_reset()
    ok = True
    win = S.standard_windows(S.REAL_B, years=False, anticip=False)
    for pool in ("D20", "R50"):
        donors = S.POOLS[pool]
        units = [S.CA] + donors
        for trends in (False, True):
            df = synthetic_panel_df(rng, units, effect=-0.03, unit_trends=trends)
            panel = S.Panel(df)
            Bp = panel.pos(win.B)
            post = panel.positions(win.win["pooled"])
            tp = panel.positions(win.trend)
            for est in ("DD", "DDT"):
                for wt in ("AGG", "POPW"):
                    for norm in ("E", "P"):
                        spec = S.Spec(est=est, weighting=wt, norm=norm)
                        tau = S.estimate(panel, spec, win, S.CA, donors)[0]["pooled"]
                        if wt == "POPW":
                            Y = panel.unit_series("722513", norm, units)
                            p = np.array([panel.pop_at(u, win.B) for u in donors])
                            wts = np.concatenate([[1.0], p / p.sum()])
                        else:
                            Y = np.vstack([panel.unit_series("722513", norm, [S.CA])[0],
                                           panel.aggregate("722513", norm, donors)])
                            wts = np.array([1.0, 1.0])
                        if est == "DDT":
                            d = twfe_trends(Y, wts, tp)
                            Y = Y - d[:, None] * np.arange(Y.shape[1])[None, :]
                        tw = twfe_dd(Y, wts, Bp, post)
                        key = f"ii_twfe_{est}_{wt}_{norm}_{pool}_{'trend' if trends else 'flat'}"
                        m[f"{key}_absdiff"] = abs(tau - tw)
                        m[f"{key}_pass"] = int(abs(tau - tw) <= EQ_TOL)
                        ok &= bool(m[f"{key}_pass"])
            # known effect: exact recovery when the DGP has no noise in the gap (POPW)
        df = synthetic_panel_df(rng, units, effect=-0.03, noise=0.0, unit_trends=True)
        panel = S.Panel(df)
        for est in ("DD", "DDT"):
            spec = S.Spec(est=est, weighting="POPW", norm="E")
            tau = S.estimate(panel, spec, win, S.CA, donors)[0]["pooled"]
            if est == "DD":
                continue    # unit trends in the DGP: DD is not unbiased here, DDT is
            m[f"ii_known_effect_DDT_POPW_{pool}_err"] = abs(tau + 0.03)
            m[f"ii_known_effect_DDT_POPW_{pool}_pass"] = int(abs(tau + 0.03) <= EQ_TOL)
            ok &= bool(m[f"ii_known_effect_DDT_POPW_{pool}_pass"])
        df = synthetic_panel_df(rng, units, effect=-0.03, noise=0.0, unit_trends=False)
        panel = S.Panel(df)
        for wt in ("AGG", "POPW"):
            tau = S.estimate(panel, S.Spec(est="DD", weighting=wt, norm="E"), win, S.CA, donors)[0]["pooled"]
            m[f"ii_known_effect_DD_{wt}_{pool}_err"] = abs(tau + 0.03)
            m[f"ii_known_effect_DD_{wt}_{pool}_pass"] = int(abs(tau + 0.03) <= EQ_TOL)
            ok &= bool(m[f"ii_known_effect_DD_{wt}_{pool}_pass"])

        # exact weights: SC and SDID unit weights (zeta = 0) with a convex-combination treated unit
        J = len(donors)
        Tpre, Tpost = 2 * J, 8
        Yd = np.cumsum(rng.normal(0, 0.05, (J, Tpre + Tpost)), axis=1) + rng.normal(10, 1, (J, 1))
        wstar = np.zeros(J)
        idx = rng.choice(J, 5, replace=False)
        wstar[idx] = rng.dirichlet(np.ones(5))
        effect = 0.05
        y = wstar @ Yd + 0.7
        y[Tpre:] += effect
        fp, wins = np.arange(Tpre), {"pooled": np.arange(Tpre, Tpre + Tpost)}
        tau_sc, f_sc = S.sc_fit(y, Yd, fp, wins)
        m[f"ii_sc_weights_{pool}_maxerr"] = float(np.max(np.abs(f_sc["w"] - wstar)))
        m[f"ii_sc_effect_{pool}_err"] = abs(tau_sc["pooled"] - effect)
        tau_sd, f_sd = S.sdid_fit(y, Yd, fp, wins, zeta=0.0)
        m[f"ii_sdid_weights_{pool}_maxerr"] = float(np.max(np.abs(f_sd["omega"] - wstar)))
        m[f"ii_sdid_effect_{pool}_err"] = abs(tau_sd["pooled"] - effect)
        for k in (f"ii_sc_weights_{pool}", f"ii_sdid_weights_{pool}"):
            m[f"{k}_pass"] = int(m[f"{k}_maxerr"] <= W_TOL)
            ok &= bool(m[f"{k}_pass"])
        for k in (f"ii_sc_effect_{pool}", f"ii_sdid_effect_{pool}"):
            m[f"{k}_pass"] = int(m[f"{k}_err"] <= W_TOL)
            ok &= bool(m[f"{k}_pass"])
        # exact time weights: donors' post mean = lambda* ' Y_pre + c (J > Tpre for uniqueness)
        Tp2 = max(4, J // 2)
        Yt = rng.normal(10, 1, (J, Tp2 + 4))
        lstar = np.zeros(Tp2)
        lstar[rng.choice(Tp2, 3, replace=False)] = rng.dirichlet(np.ones(3))
        target = Yt[:, :Tp2] @ lstar + 0.3
        Yt[:, -1] = 4 * target - Yt[:, Tp2:Tp2 + 3].sum(axis=1)       # post mean = target
        yt = Yt.mean(axis=0) + rng.normal(0, 0.01, Tp2 + 4)
        _, f_t = S.sdid_fit(yt, Yt, np.arange(Tp2), {"pooled": np.arange(Tp2, Tp2 + 4)})
        m[f"ii_sdid_time_weights_{pool}_maxerr"] = float(np.max(np.abs(f_t["lambdas"]["pooled"] - lstar)))
        m[f"ii_sdid_time_weights_{pool}_pass"] = int(m[f"ii_sdid_time_weights_{pool}_maxerr"] <= W_TOL)
        ok &= bool(m[f"ii_sdid_time_weights_{pool}_pass"])
        # demeaned SC = SDID routine with zeta = 0 and uniform time weights (noisy panel)
        df = synthetic_panel_df(rng, units, effect=-0.03)
        panel = S.Panel(df)
        yy = panel.unit_series("722513", "E", [S.CA])[0]
        YY = panel.unit_series("722513", "E", donors)
        fpp = panel.positions(win.fit)
        wp = {"pooled": panel.positions(win.win["pooled"])}
        a, _ = S.sc_fit(yy, YY, fpp, wp)
        b_, _ = S.sdid_fit(yy, YY, fpp, wp, zeta=0.0, lambdas={"pooled": np.full(len(fpp), 1 / len(fpp))})
        m[f"ii_sc_equals_sdid_zeta0_{pool}_absdiff"] = abs(a["pooled"] - b_["pooled"])
        m[f"ii_sc_equals_sdid_zeta0_{pool}_pass"] = int(abs(a["pooled"] - b_["pooled"]) <= EQ_TOL)
        ok &= bool(m[f"ii_sc_equals_sdid_zeta0_{pool}_pass"])
        # every estimator runs on the noisy panel (KKT recorded)
        for est in ("SC", "SDID"):
            S.estimate(panel, S.Spec(est=est, norm="P"), S.standard_windows(S.REAL_B), S.CA, donors)
    # small unit checks of the decision helpers
    c = S.critical_values(20.0)
    probs = S.label_probabilities(0.0, 0.01, c, 20.0)
    m["ii_label_prob_sum_err"] = abs(sum(probs.values()) - 1.0)
    m["ii_label_prob_sum_pass"] = int(m["ii_label_prob_sum_err"] < 1e-12)
    m["ii_satterthwaite_equal_vars"] = S.satterthwaite_df(np.ones(20))
    m["ii_satterthwaite_pass"] = int(abs(m["ii_satterthwaite_equal_vars"] - 20) < 1e-12)
    ok &= bool(m["ii_label_prob_sum_pass"] and m["ii_satterthwaite_pass"])
    m["ii_kkt_max"] = S.SOLVER_LOG["kkt_max"]
    m["ii_kkt_pass"] = int(S.SOLVER_LOG["kkt_max"] <= KKT_TOL)
    m["part_ii_pass"] = int(ok and m["ii_kkt_pass"])
    print(f"(ii) synthetic identities: pass {m['part_ii_pass']} (KKT max {m['ii_kkt_max']:.2e})")


# --------------------------------------------------------------------------- (iii) seasonal factors

def factors_of(path):
    """Seasonal factors of every series that enters an estimator, from one file's 2014-2019 rows."""
    df = pd.read_csv(path, dtype={"state_fips": str})
    df = df[df.year <= 2019]          # the factors use 2014Q1-2019Q4 only
    panel = S.Panel(df)
    out = {}
    for ind in S.INDUSTRIES:
        out[f"E_{ind}"] = S.seasonal_factors(np.log(panel.emp[ind]), panel.qi)
        for pool in ("D20", "R50"):
            r = panel.rows(S.POOLS[pool])
            out[f"AGG_{ind}_{pool}"] = S.seasonal_factors(np.log(panel.emp[ind][r].sum(axis=0)), panel.qi)
    out["W"] = S.seasonal_factors(np.log(panel.aww), panel.qi)
    for pool in ("D20", "R50"):
        r = panel.rows(S.POOLS[pool])
        out[f"AGG_W_{pool}"] = S.seasonal_factors(
            np.log(panel.wages[r].sum(axis=0) / (13 * panel.emp["722513"][r].sum(axis=0))), panel.qi)
    return out


def part_iii(m):
    a, b = factors_of(PRE), factors_of(FULL)
    diff = max(float(np.max(np.abs(a[k] - b[k]))) for k in a)
    m["iii_series_compared"] = len(a)
    m["iii_factor_max_absdiff"] = diff
    m["part_iii_pass"] = int(diff <= 1e-12 and set(a) == set(b))
    print(f"(iii) seasonal factors pre vs full: max |diff| {diff:.1e}")


# --------------------------------------------------------------------------- (iv) Monte Carlo

def mc_populations(synthetic, rng):
    """2016Q1 populations of California, D20 and R50 (the pop column only)."""
    if synthetic:
        return {u: float(np.exp(rng.normal(15, 1))) * (8 if u == S.CA else 1) for u in S.ALL51}
    df = pd.read_csv(PRE, dtype={"state_fips": str}, usecols=["state_fips", "quarter", "pop"])
    d = df[df.quarter == "2016Q1"]
    return dict(zip(d.state_fips, d["pop"].astype(float)))


def mc_variances(design, units, pops):
    """State-shock variances (a) and size-related variances (u) per unit; unit 0 = California."""
    p = np.array([pops[u] for u in units])
    pop_med = float(np.median(p))
    s2 = MC_SIGMA2
    va = np.zeros(len(units))
    vu = np.zeros(len(units))
    if design in ("pureB", "mixed"):
        vu = s2 * pop_med / p
    if design in ("pureA", "mixed"):
        va = np.full(len(units), s2)
    if design in ("heteroA", "heteroA_CA2"):
        va = np.array([4 * s2 if u in S.OIL else s2 for u in units])
        va[0] = va[1:].mean() * (2.0 if design == "heteroA_CA2" else 1.0)
    return va, vu


def ar1(rng, R, N, T, var, rho):
    """Stationary Gaussian AR(1) with marginal variance var (per unit)."""
    sd = np.sqrt(var)[None, :]
    eps = rng.standard_normal((R, N, T))
    e = np.empty((R, N, T))
    e[:, :, 0] = sd * eps[:, :, 0]
    for t in range(1, T):
        e[:, :, t] = rho * e[:, :, t - 1] + np.sqrt(1 - rho ** 2) * sd * eps[:, :, t]
    return e


def mc_windows():
    qi = np.arange(S.qidx(2014, 1), S.qidx(2019, 4) + 1)
    win = S.standard_windows(MC_B, years=False, anticip=False)
    pos = lambda qs: np.array([int(q - qi[0]) for q in qs])  # noqa: E731
    return len(qi), int(MC_B - qi[0]), pos(win.fit), pos(win.trend), pos(win.win["pooled"])


def mc_dd(Y, pops_arr, est, Bp, fp, tp, post):
    """DD-POPW / DDT-POPW for California (unit 0, donors 1..J) and each placebo (j treated, the
    other J-1 donors). Returns tau_ca (R,), placebos (R, J)."""
    R, N, T = Y.shape
    x = tp - tp.mean()

    def tau_of(u, D):
        w = pops_arr[D] / pops_arr[D].sum()
        g = Y[:, u, :] - np.einsum("rnt,n->rt", Y[:, D, :], w)
        if est == "DD":
            return g[:, post].mean(axis=1) - g[:, Bp]
        b = (g[:, tp] - g[:, tp].mean(axis=1, keepdims=True)) @ x / (x @ x)
        return (g[:, post] - g[:, [Bp]] - b[:, None] * (post - Bp)[None, :]).mean(axis=1)

    donors = np.arange(1, N)
    tau_ca = tau_of(0, donors)
    plc = np.column_stack([tau_of(j, donors[donors != j]) for j in donors])
    return tau_ca, plc


def mc_qp_chunk(args):
    """SC / SDID for a block of replications (run in worker processes)."""
    est, Y, fp, post = args
    kkt_reset()
    R, N, T = Y.shape
    wins = {"pooled": post}
    donors = np.arange(1, N)
    tau_ca = np.empty(R)
    plc = np.empty((R, N - 1))

    def tau_of(Yr, u, D):
        if est == "SC":
            return S.sc_fit(Yr[u], Yr[D], fp, wins)[0]["pooled"]
        return S.sdid_fit(Yr[u], Yr[D], fp, wins, tpost=len(post))[0]["pooled"]

    for r in range(R):
        Yr = Y[r]
        tau_ca[r] = tau_of(Yr, 0, donors)
        for k, j in enumerate(donors):
            plc[r, k] = tau_of(Yr, j, donors[donors != j])
    return tau_ca, plc, S.SOLVER_LOG["kkt_max"], S.SOLVER_LOG["not_converged"]


def mc_T(tau_ca, plc, pops_arr):
    """California's T = tau / SE with SE = max(SE_s, SE_n), and SE_s, SE_n."""
    pu = pops_arr[0]
    pj = pops_arr[1:]
    se_s = np.sqrt(np.mean(plc ** 2 * (pj / pu)[None, :], axis=1))
    se_n = np.sqrt(np.mean(plc ** 2, axis=1))
    return tau_ca / np.maximum(se_s, se_n), se_s, se_n


def mc_rates(tau_ca, plc, pops_arr, J, floor=None):
    T_max, se_s, se_n = mc_T(tau_ca, plc, pops_arr)
    s2 = plc.var(axis=0, ddof=1)
    nu = float(min(J, S.satterthwaite_df(s2)))
    out = {"nu_mc": nu, "share_se_n": float(np.mean(se_n >= se_s))}

    def rates(T, df):
        t95, t975 = stats.t.ppf(0.95, df), stats.t.ppf(0.975, df)
        return float(np.mean(T > t95)), float(np.mean(T < -t95)), float(np.mean(np.abs(T) > t975))

    for name, Tv in (("max", T_max), ("scaled", tau_ca / se_s), ("unscaled", tau_ca / se_n)):
        up, lo, two = rates(Tv, J)
        out.update({f"{name}_tJ_up": up, f"{name}_tJ_lo": lo, f"{name}_tJ_two": two})
    up, lo, two = rates(T_max, nu)
    out.update({"max_tnu_up": up, "max_tnu_lo": lo, "max_tnu_two": two})
    if floor is not None:
        c = S.critical_values(J, None, floor)        # max(t_J, q_cal,hi), min(-t_J, q_cal,lo)
        out.update({"floor_up": float(np.mean(T_max > c["hi95"])),
                    "floor_lo": float(np.mean(T_max < c["lo05"])),
                    "floor_two": float(np.mean((T_max > c["hi975"]) | (T_max < c["lo025"])))})
    return out


def band(r, R):
    return 3.0 * np.sqrt(r * (1 - r) / R)


def mc_panels(rng, R, units, pops, design, rho, T):
    """(iv) panels: unit effects ln(pop), linear quarter effects, a_jt + u_jt (AR(1))."""
    va, vu = mc_variances(design, units, pops)
    pops_arr = np.array([pops[u] for u in units])
    e = ar1(rng, R, len(units), T, va, rho) + ar1(rng, R, len(units), T, vu, rho)
    return np.log(pops_arr)[None, :, None] + 0.004 * np.arange(T)[None, None, :] + e


def mc_qp(pool_exec, est, Y, fp, post, chunk=10):
    R = Y.shape[0]
    jobs = [(est, Y[s:min(R, s + chunk)], fp, post) for s in range(0, R, chunk)]
    res = pool_exec.map(mc_qp_chunk, jobs)
    return (np.concatenate([r[0] for r in res]), np.vstack([r[1] for r in res]),
            max(r[2] for r in res), sum(r[3] for r in res))


def sdid_calibration(m, pool_exec, pops, reps_scale, T, fp, post):
    """design.method C1: q_cal per pool from fresh pure-A SDID-E draws (rho 0 and 0.5)."""
    rng = np.random.default_rng(SEED_CAL)
    qcal, kkt_max = {}, 0.0
    for pool in ("D20", "R50"):
        units = [S.CA] + S.POOLS[pool]
        pops_arr = np.array([pops[u] for u in units])
        R = max(1, int(round(CAL_R[pool] * reps_scale)))
        qs = {}
        for rho in MC_RHOS:
            t0 = time.time()
            Y = mc_panels(rng, R, units, pops, "pureA", rho, T)
            tau_ca, plc, kk, _ = mc_qp(pool_exec, "SDID", Y, fp, post)
            kkt_max = max(kkt_max, kk)
            Tm, _, _ = mc_T(tau_ca, plc, pops_arr)
            qs[rho] = {"hi95": float(np.quantile(Tm, 0.95, method="higher")),
                       "hi975": float(np.quantile(Tm, 0.975, method="higher")),
                       "lo05": float(np.quantile(Tm, 0.05, method="lower")),
                       "lo025": float(np.quantile(Tm, 0.025, method="lower"))}
            tag = f"rho{str(rho).replace('.', '')}"
            for k, v in qs[rho].items():
                m[f"qcal_{pool}_{tag}_{k}"] = v
            m[f"qcal_{pool}_{tag}_R"] = R
            print(f"  calibration {pool} rho={rho}: {time.time() - t0:.0f}s", flush=True)
        q = {"hi95": max(qs[r]["hi95"] for r in MC_RHOS), "hi975": max(qs[r]["hi975"] for r in MC_RHOS),
             "lo05": min(qs[r]["lo05"] for r in MC_RHOS), "lo025": min(qs[r]["lo025"] for r in MC_RHOS)}
        for k, v in q.items():
            m[f"qcal_{pool}_{k}"] = v
        qcal[pool] = q
    m["qcal_seed"] = SEED_CAL
    m["qcal_kkt_max"] = kkt_max
    return qcal


def part_iv(m, rng, reps_scale=1.0, synthetic=False, out_dir=OUT_DIR, workers=None):
    print(PASS_TEXT)
    pops = mc_populations(synthetic, rng)
    T, Bp, fp, tp, post = mc_windows()
    workers = workers or max(1, min(8, (os.cpu_count() or 2)))
    rows = []
    kkt_max, not_conv = 0.0, 0
    ctx = mp.get_context("spawn")
    with ctx.Pool(workers) as pool_exec:
        qcal = sdid_calibration(m, pool_exec, pops, reps_scale, T, fp, post)
        for pool in ("D20", "R50"):
            units = [S.CA] + S.POOLS[pool]
            J = len(units) - 1
            pops_arr = np.array([pops[u] for u in units])
            Rmax = max(1, int(round(MC_R[pool] * reps_scale)))
            for design in MC_DESIGNS:
                for rho in MC_RHOS:
                    t0 = time.time()
                    Y = mc_panels(rng, Rmax, units, pops, design, rho, T)
                    for est, epool, R_est in MC_EST:
                        if epool != pool:
                            continue
                        R = max(1, int(round(R_est * reps_scale)))
                        if est in ("DD-POPW-E", "DDT-POPW-E"):
                            tau_ca, plc = mc_dd(Y[:R], pops_arr, est.split("-")[0], Bp, fp, tp, post)
                        else:
                            tau_ca, plc, kk, nc = mc_qp(pool_exec, est.split("-")[0], Y[:R], fp, post)
                            kkt_max = max(kkt_max, kk)
                            not_conv += nc
                        row = {"estimator": est, "pool": pool, "design": design, "rho": rho,
                               "R": R, "J": J}
                        row.update(mc_rates(tau_ca, plc, pops_arr, J,
                                            qcal[pool] if est == "SDID-E" else None))
                        rows.append(row)
                    print(f"  {pool} {design} rho={rho}: {time.time() - t0:.0f}s", flush=True)
    tab = pd.DataFrame(rows)
    # pass conditions
    fails_a, fails_a_sdid, fails_b = [], [], []
    for i, r in tab.iterrows():
        R, J, nu = r["R"], r["J"], r["nu_mc"]
        b05 = 0.05 + band(0.05, R)
        tab.loc[i, "bound_05"] = b05
        name = f"{r['estimator']}/{r['pool']}/{r['design']}/rho{r['rho']}"
        if r["design"] in ("pureB", "pureA", "mixed"):
            ok_tJ = all(r[f"max_tJ_{k}"] <= b05 for k in ("up", "lo", "two"))
            tab.loc[i, "pass_tJ"] = int(ok_tJ)
            if r["estimator"] == "SDID-E":
                ok = all(r[f"floor_{k}"] <= b05 for k in ("up", "lo", "two"))   # (a-SDID)
                if not ok:
                    fails_a_sdid.append(name)
            else:
                ok = ok_tJ                                                       # (a)
                if not ok:
                    fails_a.append(name)
            tab.loc[i, "pass"] = int(ok)
        elif r["design"] == "heteroA":
            r1 = 1 - stats.t.cdf(stats.t.ppf(0.95, J), nu)
            r2 = 2 * (1 - stats.t.cdf(stats.t.ppf(0.975, J), nu))
            tab.loc[i, "r1"], tab.loc[i, "r2"] = r1, r2
            tab.loc[i, "bound_r1"], tab.loc[i, "bound_r2"] = r1 + band(r1, R), r2 + band(r2, R)
            ok = (r["max_tJ_up"] <= r1 + band(r1, R) and r["max_tJ_lo"] <= r1 + band(r1, R)
                  and r["max_tJ_two"] <= r2 + band(r2, R)
                  and all(r[f"max_tnu_{k}"] <= b05 for k in ("up", "lo", "two")))
            tab.loc[i, "pass"] = int(ok)
            if not ok:
                fails_b.append(f"{r['estimator']}/{r['pool']}/rho{r['rho']}")
        else:
            tab.loc[i, "pass"] = -1     # report-only
    out_dir.mkdir(parents=True, exist_ok=True)
    tab.to_csv(out_dir / "mc_rates.csv", index=False, float_format="%.6g")
    for _, r in tab.iterrows():
        key = f"mc_{r['estimator']}_{r['pool']}_{r['design']}_rho{str(r['rho']).replace('.', '')}"
        cols = ["nu_mc", "max_tJ_up", "max_tJ_lo", "max_tJ_two", "max_tnu_up", "max_tnu_lo",
                "max_tnu_two", "scaled_tJ_up", "scaled_tJ_lo", "scaled_tJ_two", "unscaled_tJ_two"]
        if r["estimator"] == "SDID-E":
            cols += ["floor_up", "floor_lo", "floor_two"]
        for col in cols:
            m[f"{key}_{col}"] = float(r[col])
        m[f"{key}_pass"] = int(r["pass"])
    m["mc_combinations"] = int(len(tab))
    m["mc_pass_a"] = int(not fails_a)
    m["mc_fail_a"] = ";".join(fails_a)
    m["a_sdid_pass"] = int(not fails_a_sdid)
    m["a_sdid_fail"] = ";".join(fails_a_sdid)
    m["mc_pass_b"] = int(not fails_b)
    m["mc_fail_b"] = ";".join(fails_b)
    m["mc_kkt_max"] = kkt_max
    m["mc_kkt_pass"] = int(kkt_max <= KKT_TOL)
    m["mc_not_converged"] = int(not_conv)
    m["mc_seed"] = SEED
    m["mc_reps_scale"] = reps_scale
    m["mc_populations"] = "synthetic" if synthetic else "state_panel_pre.csv 2016Q1 pop"
    print(f"(iv) Monte Carlo: (a) pass {m['mc_pass_a']} {fails_a}; (a-SDID) pass "
          f"{m['a_sdid_pass']} {fails_a_sdid}; (b) pass {m['mc_pass_b']} {fails_b}")


# --------------------------------------------------------------------------- (v) input guard

def part_v(m, rng):
    import level_mde
    import select_rule
    units = [S.CA] + S.D20
    df = synthetic_panel_df(rng, units, last=(2020, 1))
    bad = df.to_csv(index=False)
    good = df[df.year <= 2019].to_csv(index=False)
    for name, mod in (("select_rule", select_rule), ("level_mde", level_mde)):
        try:
            mod.load_input(io.StringIO(bad))
            raised = 0
        except ValueError:
            raised = 1
        try:
            mod.load_input(io.StringIO(good))
            accepts = 1
        except ValueError:
            accepts = 0
        m[f"v_{name}_raises_after_2019q4"] = raised
        m[f"v_{name}_accepts_pre"] = accepts
    m["part_v_pass"] = int(all(m[f"v_{n}_raises_after_2019q4"] and m[f"v_{n}_accepts_pre"]
                               for n in ("select_rule", "level_mde")))
    print(f"(v) input guard: pass {m['part_v_pass']}")


# --------------------------------------------------------------------------- main

def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="i,ii,iii,iv,v", help="development only")
    ap.add_argument("--reps-scale", type=float, default=1.0, help="development only")
    ap.add_argument("--synthetic-pops", action="store_true", help="development only")
    ap.add_argument("--out", default=str(OUT_DIR), help="development only")
    args = ap.parse_args(argv)
    parts = args.parts.split(",")
    out_dir = Path(args.out)
    rng = np.random.default_rng(SEED)
    m = {"seed": SEED, "parts": args.parts}
    t0 = time.time()
    if "i" in parts:
        part_i(m)
    if "ii" in parts:
        part_ii(m, rng)
    if "iii" in parts:
        part_iii(m)
    if "v" in parts:
        part_v(m, rng)
    if "iv" in parts:
        part_iv(m, np.random.default_rng(SEED), args.reps_scale, args.synthetic_pops, out_dir)
    full = [p for p in ("i", "ii", "iii", "v") if p in parts]
    m["all_deterministic_checks_pass"] = int(all(m[f"part_{p}_pass"] for p in full))
    S.write_json(out_dir / "metrics.json", m)
    print(f"done in {time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()
