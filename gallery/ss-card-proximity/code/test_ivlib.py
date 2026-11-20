"""check-synthetic (plan.json analysis_plan step 0c): every estimator on synthetic data only.

Never reads data/derived/card_analysis.csv, nls.dat or read1.lst; no real outcome is
computed. Randomness: numpy default_rng(4483), spawned once per design below. Errors are
heteroskedastic in every design.

Checks (each records <name>_pass; the script exits 1 if any fails):
 1. se-formulas    Conventional (sigma^2 = e'e/(n-k)) and HC1 SEs of OLS (statsmodels) and
                   2SLS (linearmodels, one and three endogenous regressors) equal hand-coded
                   matrix formulas to 1e-10 relative.
 2. iv-ratio       One-instrument 2SLS = reduced form / first stage (1e-10).
 3. ar-shapes      The closed-form robust AR set equals grid inversion (b0 in [-1, 1], step
                   1e-4, AR recomputed as the HC1 t^2 of the instrument; no disagreement
                   beyond one grid step) in three designs with the expected shapes: strong
                   instrument -> bounded; weak instrument (with a direct effect, so the
                   reduced form is significant) -> two half-lines; irrelevant -> whole line.
                   AR(0) = squared robust reduced-form t (1e-10) in each.
 4. chr            CHR breakdown = lambda - 1.959964 se_HC1(lambda) and equals the first
                   gamma0 grid point (step 1e-5) whose AR set contains 0, within one step;
                   the Wald CHR SE equals linearmodels' HC1 SE on the shifted outcome.
 5. if-variance    Stacked influence-function variance of 2SLS and OLS alone = HC1 (1e-8,
                   inside ivlib.h5_control_function); D = -rho g; Var(D) agrees with a
                   2,000-draw pairs-bootstrap variance: |Var_boot / Var_IF - 1| <= 0.15
                   (tolerance fixed here before the run: the Monte Carlo SE of a 2,000-draw
                   variance is about sqrt(2/1999) = 0.032 relative, so 0.15 is about 4.7 MC
                   SEs and also absorbs the n/(n-k) factor of HC1).
 6. panel-b-S / panel-b-WN  Two designs mimicking Panel B: n = 3010, 3 instruments (a
                   binary nearc4-like z1, standardised age z2 and z2^2), 2 nuisance
                   regressors, 27 exogenous controls incl. the intercept, structural and
                   first-stage errors correlated across equations and multiplied by
                   sqrt(0.25 + z1^2 + 0.5 z2^2). S: strong nuisance (concentration
                   parameter for W = 300); WN: weak nuisance (population kappa_1 = 5). In
                   both: stacked HAR = direct HC1 regression at 20 random (b0, g) to 1e-8
                   relative; at 10 values of b0 the BFGS profile minimum <= the minimum of
                   a 401 x 401 grid over g (centred on the LIML g, half-width 10 HC1 SEs)
                   x (1 + 1e-6); the robust projection set contains the true b0 in at least
                   0.921 of 500 heteroskedastic replications (GKMC and GKM19 coverage
                   reported, not asserted); own kappa_p, kappa_1 = ivmodels 0.10.0 (1e-8
                   relative), own GKMC quadric = ivmodels inverse ('chi2') (1e-6), and the
                   (3Q) set from the SET COMPUTATION = ivmodels inverse ('gkm') (1e-4).
 7. gkm19-cv       The ivmodels eq. (2.12) quantile at every finite tabulated kappa_1 lies in
                   (table - 0.1 - 1e-3, table + 1e-6]; |quantile(1000) - 3.838| < 1e-3; (3T)
                   returns every tabulated value at its kappa_1, (kappa_1 / 0.5) x 0.4 below
                   0.5 (0.2 at 0.25, 0 at 0), 3.838 at 1000, 3.838 + 0.003 (1 - exp(-1)) at
                   2000, within 1e-6 of 3.841 at 1e5, and is continuous and non-decreasing
                   on a grid from 0 to 1e5 (no step larger than the largest table slope
                   times the grid step). The quantile is also found, within 1e-4 of
                   3.841459, at kappa_1 = 1e5, 1e10 and 1e16 (added: in Panel B kappa_1
                   grows like b0^2 on the outer grid).
 8. set-computation  On synthetic acceptance regions with known roots (a bounded interval
                   whose upper bound is in (1, 2); two half-lines; a bounded set plus a
                   distant piece in (4, 6); the whole line) ivlib.invert_on_grid returns the
                   right pieces to its tolerances and calls a side unbounded only in the
                   half-line and whole-line cases.
 9. entry-points   A synthetic file with the analysis file's columns (written to
                   runs/check-synthetic/synthetic_card.csv and read back with
                   ivlib.load_analysis) goes through compute() of every run script,
                   including their internal identity checks, and verdict.judge. Their
                   outputs go to runs/check-synthetic/entry/ (synthetic only).

Output: runs/check-synthetic/metrics.json (pass flags and synthetic-only numbers).
Usage, from the workspace root:  .venv/bin/python code/test_ivlib.py
"""
from __future__ import annotations

import json
import math
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm
from linearmodels.iv import IV2SLS

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

OUT = Path("runs/check-synthetic")
METRICS: dict = {}
FAILED: list[str] = []
RNG = np.random.default_rng(ivlib.SEED)
(R_SE, R_SHAPES, R_CHR, R_IF, R_S, R_WN, R_ENTRY) = RNG.spawn(7)


def check(name: str):
    def deco(fn):
        def run():
            t0 = time.time()
            try:
                fn()
                ok = True
            except Exception:  # noqa: BLE001 - record and continue with the other checks
                traceback.print_exc()
                ok = False
            METRICS[f"{name}_pass"] = int(ok)
            if not ok:
                FAILED.append(name)
            print(f"[{'PASS' if ok else 'FAIL'}] {name} ({time.time() - t0:.1f} s)", flush=True)
        return run
    return deco


def rel(a, b):
    return ivlib.rel_diff(a, b)


# --------------------------------------------------------------------------- designs


def one_iv_frame(rng, pi: float, direct: float, n: int = 3010, kc: int = 16) -> tuple:
    C = np.column_stack([np.ones(n), rng.standard_normal((n, kc - 1))])
    z = (rng.random(n) < 0.5 + 0.2 * np.tanh(C[:, 1])).astype(float)
    h = np.sqrt(0.25 + z + 0.5 * C[:, 1] ** 2)
    e = rng.multivariate_normal([0, 0], [[1.0, 0.5], [0.5, 1.0]], size=n) * h[:, None]
    x = pi * z + C @ rng.normal(0, 0.3, kc) + e[:, 1]
    y = 0.1 * x + direct * z + C @ rng.normal(0, 0.3, kc) + 0.5 * e[:, 0]
    names = [f"c{j}" for j in range(kc)]
    df = pd.DataFrame(C, columns=names)
    df["y"], df["x"], df["z"] = y, x, z
    return df, names


PB_SIGMA = np.array([[1.0, 0.5, 0.3, -0.2], [0.5, 1.0, -0.3, 0.1],
                     [0.3, -0.3, 1.0, 0.2], [-0.2, 0.1, 0.2, 1.0]])
PB_BETA, PB_GAMMA = 0.10, np.array([0.5, -0.3])
PB_PI_W = np.array([[-0.3, 0.0], [1.0, 0.5], [0.0, 1.0]])   # rows z1, z2, z3; cols W1, W2


def panel_b_arrays(rng, s: float, n: int = 3010) -> dict:
    """One Panel-B-like sample; s scales the instruments' coefficients on W."""
    nb, nn = 13, 13
    C = np.column_stack([np.ones(n), (rng.random((n, nb)) < 0.3).astype(float),
                         rng.standard_normal((n, nn))])                    # 27 columns
    z1 = (rng.random(n) < 0.68).astype(float)
    age = rng.integers(24, 35, size=n).astype(float)
    z2 = (age - 29.0) / 3.16
    Z = np.column_stack([z1, z2, z2 ** 2])
    h = np.sqrt(0.25 + z1 ** 2 + 0.5 * z2 ** 2)
    E = rng.standard_normal((n, 4)) @ np.linalg.cholesky(PB_SIGMA).T * h[:, None]
    dC = rng.normal(0, 0.2, (27, 4))
    x = 0.35 * z1 + C @ dC[:, 1] + E[:, 1]
    W = s * (Z @ PB_PI_W) + C @ dC[:, 2:] + E[:, 2:]
    y = PB_BETA * x + W @ PB_GAMMA + C @ dC[:, 0] + E[:, 0]
    return {"y": y, "x": x, "W": W, "Z": Z, "X": C, "h": h}


def pb_population_strength(d: dict, s: float) -> tuple[float, float]:
    """(population kappa_1 at the true b0, concentration parameter for W) at scale s.

    With all variables residualised on X, the Z-coefficients of (Y0, W), Y0 = y - b x, are
    s [PI_W g, PI_W]; Omega = E[h^2] x the covariance of (u + g'v_W, v_W). kappa_1 is the
    largest root of |k Omega - N|, N = Pi' Z~'Z~ Pi; the concentration parameter is the
    smallest eigenvalue of Omega_WW^-1 PI_W' Z~'Z~ PI_W s^2.
    """
    Zt = ivlib._resid_on(d["X"], d["Z"])
    ZZ = Zt.T @ Zt
    T = np.array([[1.0, 0.0, PB_GAMMA[0], PB_GAMMA[1]], [0, 0, 1, 0], [0, 0, 0, 1]])
    Om = float(np.mean(d["h"] ** 2)) * T @ PB_SIGMA @ T.T
    Pi = s * np.column_stack([PB_PI_W @ PB_GAMMA, PB_PI_W])
    k1 = float(np.max(np.real(np.linalg.eigvals(np.linalg.solve(Om, Pi.T @ ZZ @ Pi)))))
    PW = s * PB_PI_W
    conc = float(np.min(np.real(np.linalg.eigvals(np.linalg.solve(Om[1:, 1:], PW.T @ ZZ @ PW)))))
    return k1, conc


def panel_b_object(d: dict, draws: np.ndarray) -> tuple[ivlib.PanelB, float, float]:
    endog = np.column_stack([d["x"], d["W"]])
    res = IV2SLS(d["y"], d["X"], endog, d["Z"]).fit(cov_type="robust", debiased=True)
    params, se = res.params.to_numpy(), res.std_errors.to_numpy()
    kx = d["X"].shape[1]
    g_full, g_se = params[kx + 1: kx + 3], se[kx + 1: kx + 3]
    pb = ivlib.PanelB(d["y"], d["x"], d["W"], d["Z"], d["X"], start_draws=draws,
                      g_full=g_full, g_se=g_se)
    return pb, float(params[kx]), float(se[kx])


# --------------------------------------------------------------------------- checks


@check("se_formulas")
def t_se():
    df, cn = one_iv_frame(R_SE, 0.5, 0.0)
    n = len(df)
    # OLS
    X = df[["x"] + cn].to_numpy()
    y = df["y"].to_numpy()
    f = ivlib.fit_ols(df, "y", ["x"] + cn, "x")
    b = np.linalg.solve(X.T @ X, X.T @ y)
    e = y - X @ b
    k = X.shape[1]
    XtXi = np.linalg.inv(X.T @ X)
    se_conv = math.sqrt(e @ e / (n - k) * XtXi[0, 0])
    meat = (X * e[:, None] ** 2).T @ X
    se_hc1 = math.sqrt(n / (n - k) * (XtXi @ meat @ XtXi)[0, 0])
    worst = max(rel(f.coef, b[0]), rel(f.se_conv, se_conv), rel(f.se_hc1, se_hc1))
    # 2SLS, one endogenous
    worst2 = 0.0
    for endog, instr, frame in ((["x"], ["z"], df), (None, None, None)):
        if endog is None:   # three endogenous regressors (Panel B-like)
            d = panel_b_arrays(R_SE, 1.0)
            frame = pd.DataFrame(d["X"], columns=[f"c{j}" for j in range(27)])
            frame["y"], frame["x"] = d["y"], d["x"]
            frame["w1"], frame["w2"] = d["W"][:, 0], d["W"][:, 1]
            frame["z1"], frame["z2"], frame["z3"] = d["Z"].T
            exog = [f"c{j}" for j in range(27)]
            endog, instr = ["x", "w1", "w2"], ["z1", "z2", "z3"]
        else:
            exog = cn
        fi = ivlib.fit_2sls(frame, "y", exog, endog, instr, "x")
        R = frame[endog + exog].to_numpy()
        Q = frame[instr + exog].to_numpy()
        yy = frame["y"].to_numpy()
        Xh = Q @ np.linalg.solve(Q.T @ Q, Q.T @ R)
        A = np.linalg.inv(Xh.T @ Xh)
        bb = A @ Xh.T @ yy
        u = yy - R @ bb
        nn, kk = R.shape
        sc = math.sqrt(u @ u / (nn - kk) * A[0, 0])
        sr = math.sqrt(nn / (nn - kk) * (A @ ((Xh * u[:, None] ** 2).T @ Xh) @ A)[0, 0])
        worst2 = max(worst2, rel(fi.coef, bb[0]), rel(fi.se_conv, sc), rel(fi.se_hc1, sr))
    METRICS["se_formulas_ols_max_rel"] = worst
    METRICS["se_formulas_2sls_max_rel"] = worst2
    ivlib.require(worst < 1e-10 and worst2 < 1e-10, f"SE formulas differ ({worst}, {worst2})")


@check("iv_ratio")
def t_ratio():
    df, cn = one_iv_frame(R_SE, 0.4, 0.0)
    fi = ivlib.fit_2sls(df, "y", cn, ["x"], ["z"], "x")
    fs = ivlib.fit_ols(df, "x", ["z"] + cn, "z")
    rf = ivlib.fit_ols(df, "y", ["z"] + cn, "z")
    METRICS["iv_ratio_abs_diff"] = abs(fi.coef - rf.coef / fs.coef)
    ivlib.require(METRICS["iv_ratio_abs_diff"] < 1e-10, "2SLS != RF/FS")


@check("ar_shapes")
def t_shapes():
    expected = {"strong": (0.5, 0.0, "bounded"), "weak": (0.06, 0.15, "two-half-lines"),
                "irrelevant": (0.0, 0.0, "whole-line")}
    for tag, (pi, direct, shape) in expected.items():
        df, cn = one_iv_frame(R_SHAPES, pi, direct)
        ar = ivlib.one_instrument_ar(df, cn, robust=True, y="y", x="x", z="z")
        rf = ivlib.fit_ols(df, "y", ["z"] + cn, "z")
        t2 = (rf.coef / rf.se_hc1) ** 2
        pieces = ar.pieces()
        chk = ivlib.ar_grid_check(df, cn, ar, y="y", x="x", z="z")
        METRICS[f"ar_shapes_{tag}_shape"] = ivlib.set_shape(pieces)
        METRICS[f"ar_shapes_{tag}_pieces"] = ivlib.pieces_str(pieces)
        METRICS[f"ar_shapes_{tag}_grid_mismatch"] = chk["mismatch_beyond_one_step"]
        METRICS[f"ar_shapes_{tag}_grid_max_rel"] = chk["max_rel_diff"]
        METRICS[f"ar_shapes_{tag}_fs_t2"] = ar.pi ** 2 / ar.V[1, 1]
        ivlib.require(abs(float(ar.stat(0.0)) - t2) <= 1e-10 * max(1.0, t2), "AR(0) != RF t^2")
        ivlib.require(chk["mismatch_beyond_one_step"] == 0, f"{tag}: grid disagrees")
        ivlib.require(ivlib.set_shape(pieces) == shape, f"{tag}: shape {ivlib.set_shape(pieces)}")


@check("chr")
def t_chr():
    df, cn = one_iv_frame(R_CHR, 0.5, 0.0)
    df["y"] = df["y"] + 0.04 * df["z"]            # a direct effect so delta* > 0
    ar = ivlib.one_instrument_ar(df, cn, robust=True, y="y", x="x", z="z")
    rf = ivlib.fit_ols(df, "y", ["z"] + cn, "z")
    dstar = ivlib.chr_breakdown(ar)
    dgrid = ivlib.chr_breakdown_grid(ar)
    METRICS.update({"chr_dstar": dstar, "chr_dstar_grid": dgrid,
                    "chr_rf_lower": rf.coef - ivlib.Z975 * rf.se_hc1})
    ivlib.require(dstar > 0, "synthetic delta* should be positive")
    ivlib.require(abs(dstar - (rf.coef - ivlib.Z975 * rf.se_hc1)) < 1e-12, "delta* != RF lower")
    ivlib.require(abs(dgrid - dstar) <= 1e-5 + 1e-12, "grid breakdown off by more than a step")
    mats = ivlib.iv_one_instrument_matrices(df, cn, y="y", x="x", z="z")
    worst = 0.0
    for g in (0.0, 0.0123, 0.031):
        sh = df.assign(y=df["y"] - g * df["z"])
        fi = ivlib.fit_2sls(sh, "y", cn, ["x"], ["z"], "x")
        b, lo, hi = ivlib.chr_wald(mats, np.array([g]))
        worst = max(worst, rel(b[0], fi.coef), rel((hi[0] - lo[0]) / (2 * ivlib.Z975), fi.se_hc1))
    METRICS["chr_wald_vs_linearmodels_max_rel"] = worst
    ivlib.require(worst < 1e-8, "Wald CHR != linearmodels")


@check("if_variance")
def t_if():
    df, cn = one_iv_frame(R_IF, 0.5, 0.0)
    df = df.rename(columns={"y": "lwage76", "x": "ed76", "z": "nearc4"})
    r = ivlib.h5_control_function(df, cn)       # asserts IF = HC1 and D = -rho g inside
    n = len(df)
    R = ivlib.cols(df, ["ed76"] + cn)
    Q = ivlib.cols(df, ["nearc4"] + cn)
    y = df["lwage76"].to_numpy()
    draws = np.empty(2000)
    for bi in range(2000):
        idx = R_IF.integers(0, n, n)
        Rb, Qb, yb = R[idx], Q[idx], y[idx]
        Xh = Qb @ np.linalg.lstsq(Qb, Rb, rcond=None)[0]
        biv = np.linalg.lstsq(Xh, yb, rcond=None)[0][0]
        bols = np.linalg.lstsq(Rb, yb, rcond=None)[0][0]
        draws[bi] = biv - bols
    vb = float(np.var(draws, ddof=1))
    ratio = vb / r["diff_se"] ** 2
    METRICS.update({"if_var_D": r["diff_se"] ** 2, "if_var_D_boot": vb, "if_boot_ratio": ratio,
                    "if_tolerance": 0.15})
    ivlib.require(abs(ratio - 1) <= 0.15, f"bootstrap / IF variance = {ratio:.3f}")


def panel_b_check(tag: str, rng, target: str):
    draws = np.random.default_rng(ivlib.SEED).standard_normal((20, 2))
    base = panel_b_arrays(rng, 1.0)
    k1_1, conc_1 = pb_population_strength(base, 1.0)
    s = math.sqrt(300.0 / conc_1) if target == "S" else math.sqrt(5.0 / k1_1)
    d = panel_b_arrays(rng, s)
    k1_pop, conc = pb_population_strength(d, s)
    METRICS[f"pb_{tag}_scale"] = s
    METRICS[f"pb_{tag}_pop_kappa1"] = k1_pop
    METRICS[f"pb_{tag}_concentration_W"] = conc
    pb, bhat, bse = panel_b_object(d, draws)
    # (i) stacked HAR = direct regression
    worst = 0.0
    for _ in range(20):
        b0 = PB_BETA + rng.normal(0, 0.3)
        g = pb.g_full + 3.0 * pb.g_se * rng.standard_normal(2)
        worst = max(worst, rel(pb.har(b0, g), pb.har_direct(b0, g)))
    METRICS[f"pb_{tag}_har_max_rel"] = worst
    ivlib.require(worst < 1e-8, f"{tag}: stacked HAR != direct ({worst})")
    # gradient used by BFGS against central differences
    gerr = 0.0
    for b0 in (bhat, bhat + bse):
        g = pb.g_liml(b0) + pb.g_se * 0.7
        f0, gr = pb.har_and_grad(g, b0)
        for j in range(2):
            e = np.zeros(2)
            e[j] = 1e-6 * max(abs(g[j]), pb.g_se[j])
            num = (pb.har_and_grad(g + e, b0)[0] - pb.har_and_grad(g - e, b0)[0]) / (2 * e[j])
            gerr = max(gerr, abs(num - gr[j]) / max(1.0, abs(gr[j])))
    METRICS[f"pb_{tag}_grad_max_rel"] = gerr
    ivlib.require(gerr < 1e-4, f"{tag}: analytic gradient off ({gerr})")
    # (ii) BFGS profile vs brute-force grid
    worst_ratio = 0.0
    for i, b0 in enumerate(bhat + bse * np.linspace(-4, 4, 10)):
        mb, _ = pb.profile(b0)
        gl = pb.g_liml(b0)
        G1, G2 = np.meshgrid(gl[0] + pb.g_se[0] * np.linspace(-10, 10, 401),
                             gl[1] + pb.g_se[1] * np.linspace(-10, 10, 401), indexing="ij")
        mg = float(np.min(pb.har_grid(b0, G1, G2)))
        METRICS[f"pb_{tag}_b0_{i}"] = float(b0)
        METRICS[f"pb_{tag}_bfgs_min_{i}"] = mb
        METRICS[f"pb_{tag}_grid_min_{i}"] = mg
        worst_ratio = max(worst_ratio, mb / max(mg, 1e-300))
        ivlib.require(mb <= mg * (1 + 1e-6) + 1e-12, f"{tag}: BFGS {mb} > grid {mg} at {b0}")
    METRICS[f"pb_{tag}_bfgs_over_grid_max"] = worst_ratio
    # (iv) ivmodels agreement
    wk = 0.0
    for b0 in (0.0, PB_BETA, bhat + 2 * bse, -0.4, 0.7):
        kp, k1 = pb.kappas(b0)
        iv = ivlib.ivmodels_panel_b(pb, b0)
        wk = max(wk, rel(kp, iv["kappa_p"]), rel(k1, iv["kappa_1"]))
    METRICS[f"pb_{tag}_ivmodels_kappa_max_rel"] = wk
    ivlib.require(wk < 1e-8, f"{tag}: kappa != ivmodels ({wk})")
    quad, ivq = pb.gkmc_quadric(), ivlib.ivmodels_inverse(pb, "chi2")
    METRICS[f"pb_{tag}_gkmc_quadric"] = ivlib.pieces_str(quad)
    METRICS[f"pb_{tag}_gkmc_quadric_vs_ivmodels"] = ivlib.bounds_diff(quad, ivq)
    ivlib.require(ivlib.bounds_diff(quad, ivq) < 1e-6, f"{tag}: GKMC quadric != ivmodels")
    pts = ivlib.grid_points()
    kap = np.array([pb.kappas(b) for b in pts])
    acc_q = kap[:, 0] <= np.array([ivlib.c_gkm19_quantile(k) for k in kap[:, 1]])

    def acc_fn(b):
        kp, k1 = pb.kappas(b)
        return kp <= ivlib.c_gkm19_quantile(k1)

    gq = ivlib.invert_on_grid(acc_fn, accepted=acc_q, points=pts)
    ivg = ivlib.ivmodels_inverse(pb, "gkm")
    gc = ivlib.invert_on_grid(lambda b: pb.kappas(b)[0] <= ivlib.CHI2_1_95,
                              accepted=kap[:, 0] <= ivlib.CHI2_1_95, points=pts)
    METRICS[f"pb_{tag}_gkm19q_set"] = ivlib.pieces_str(gq.pieces)
    METRICS[f"pb_{tag}_gkm19q_vs_ivmodels"] = ivlib.bounds_diff(gq.pieces, ivg)
    METRICS[f"pb_{tag}_gkmc_grid_vs_quadric"] = ivlib.bounds_diff(gc.pieces, quad)
    ivlib.require(ivlib.bounds_diff(gq.pieces, ivg) < 1e-4, f"{tag}: (3Q) != ivmodels gkm")
    ivlib.require(ivlib.bounds_diff(gc.pieces, quad) < 1e-5, f"{tag}: GKMC grid != quadric")
    # (iii) coverage over 500 replications
    cov_r = cov_c = cov_t = 0
    for rr in rng.spawn(500):
        dd = panel_b_arrays(rr, s)
        p, _, _ = panel_b_object(dd, draws)
        cov_r += p.profile(PB_BETA)[0] <= ivlib.CHI2_3_95
        kp, k1 = p.kappas(PB_BETA)
        cov_c += kp <= ivlib.CHI2_1_95
        cov_t += kp <= ivlib.c_gkm19_table(k1)
    METRICS[f"pb_{tag}_coverage_robust"] = cov_r / 500
    METRICS[f"pb_{tag}_coverage_gkmc"] = cov_c / 500
    METRICS[f"pb_{tag}_coverage_gkm19"] = cov_t / 500
    bound = 0.95 - 3 * math.sqrt(0.95 * 0.05 / 500)
    METRICS["pb_coverage_bound"] = bound
    ivlib.require(cov_r / 500 >= bound, f"{tag}: robust coverage {cov_r / 500}")


@check("panel_b_S")
def t_pb_s():
    panel_b_check("S", R_S, "S")


@check("panel_b_WN")
def t_pb_wn():
    panel_b_check("WN", R_WN, "WN")


@check("gkm19_cv")
def t_gkm():
    worst_lo = worst_hi = math.inf
    for k1, cv in ivlib.GKM19_TABLE3_KM1_5PCT:
        q = ivlib.c_gkm19_quantile(k1)
        ivlib.require(cv - 0.1 - 1e-3 < q <= cv + 1e-6, f"quantile {q} at {k1} vs table {cv}")
        worst_lo = min(worst_lo, q - (cv - 0.1 - 1e-3))
        worst_hi = min(worst_hi, cv + 1e-6 - q)
        ivlib.require(ivlib.c_gkm19_table(k1) == cv, f"(3T) at {k1} != {cv}")
    METRICS["gkm19_q_min_margin_low"] = worst_lo
    METRICS["gkm19_q_min_margin_high"] = worst_hi
    q1000 = ivlib.c_gkm19_quantile(1000.0)
    METRICS["gkm19_q_at_1000"] = q1000
    ivlib.require(abs(q1000 - 3.838) < 1e-3, "quantile at 1000")
    # Panel B's kappa_1 grows like b0^2 on the outer grid (exp76 + ed76 = age76 - 6 is in
    # the instruments' span); the quantile must still be found there.
    for big in (1e5, 1e10, 1e16):
        qb = ivlib.c_gkm19_quantile(big)
        METRICS[f"gkm19_q_at_1e{int(round(math.log10(big)))}"] = qb
        ivlib.require(abs(qb - ivlib.CHI2_1_95) < 1e-4, f"quantile at {big}: {qb}")
    k0, c0 = ivlib.GKM19_TABLE3_KM1_5PCT[0]
    for f in (0.0, 0.25, 0.5, 0.9):
        ivlib.require(abs(ivlib.c_gkm19_table(f * k0) - f * c0) < 1e-15, "below first point")
    ivlib.require(ivlib.c_gkm19_table(1000.0) == 3.838, "3T(1000)")
    ivlib.require(abs(ivlib.c_gkm19_table(2000.0) - (3.838 + 0.003 * (1 - math.exp(-1)))) < 1e-15,
                  "3T(2000)")
    ivlib.require(abs(ivlib.c_gkm19_table(1e5) - 3.841) < 1e-6, "3T(1e5)")
    tk = np.array([0.0] + [r[0] for r in ivlib.GKM19_TABLE3_KM1_5PCT])
    tc = np.array([0.0] + [r[1] for r in ivlib.GKM19_TABLE3_KM1_5PCT])
    slope = float(np.max(np.diff(tc) / np.diff(tk)))
    for lo, hi, step in ((0.0, 1000.0, 0.001), (1000.0, 1e5, 0.1)):
        g = lo + step * np.arange(int(round((hi - lo) / step)) + 1)
        d = np.diff(ivlib.c_gkm19_table(g))
        ivlib.require(np.all(d >= -1e-15), "3T decreases")
        ivlib.require(np.all(d <= slope * step * (1 + 1e-9) + 1e-15), "3T jumps")
    METRICS["gkm19_table_max_slope"] = slope


@check("set_computation")
def t_sets():
    inf = math.inf
    cases = {
        "bounded_out": (lambda b: (b - 0.3) * (b - 1.7) <= 0, [(0.3, 1.7)]),
        "half_lines": (lambda b: (b + 0.5) * (b - 0.8) >= 0, [(-inf, -0.5), (0.8, inf)]),
        "distant": (lambda b: (b + 0.2) * (b - 0.4) * (b - 4.5) * (b - 5.5) <= 0,
                    [(-0.2, 0.4), (4.5, 5.5)]),
        "whole": (lambda b: True, [(-inf, inf)]),
    }
    for tag, (fn, truth) in cases.items():
        gs = ivlib.invert_on_grid(fn)
        ivlib.require(len(gs.pieces) == len(truth), f"{tag}: {gs.pieces}")
        for (a, b), (ta, tb) in zip(gs.pieces, truth):
            for u, v in ((a, ta), (b, tb)):
                if math.isinf(v):
                    ivlib.require(u == v, f"{tag}: unbounded side missed")
                else:
                    tol = 1e-6 if abs(v) <= 1 else 1e-6 * abs(v)
                    ivlib.require(abs(u - v) <= tol, f"{tag}: bound {u} vs {v}")
        unb = gs.unbounded_lo or gs.unbounded_hi
        ivlib.require(unb == (tag in ("half_lines", "whole")), f"{tag}: unbounded flag")
        METRICS[f"set_{tag}"] = ivlib.pieces_str(gs.pieces)


def synthetic_card_frame(rng, n: int = 3010) -> pd.DataFrame:
    """A file with the analysis file's columns and a Card-like structure (synthetic)."""
    reg = rng.choice(np.arange(1, 10), size=n, p=[.05, .16, .2, .06, .21, .1, .11, .03, .08])
    smsa66 = (rng.random(n) < 0.65).astype(int)
    near = (rng.random(n) < 0.45 + 0.3 * smsa66).astype(int)
    age = rng.integers(24, 35, size=n)
    famed = rng.integers(1, 10, size=n)
    momed = np.clip(np.round(10 + 3 * rng.standard_normal(n), 2), 0, 18)
    daded = np.clip(np.round(10 + 3.5 * rng.standard_normal(n), 2), 0, 18)
    black = (rng.random(n) < 0.23).astype(int)
    ability = rng.standard_normal(n)
    h = np.sqrt(0.25 + near + 0.5 * ((age - 29) / 3.2) ** 2)
    v = h * (0.8 * ability + 1.6 * rng.standard_normal(n))
    ed = np.clip(np.round(10.5 + 0.35 * near + 0.08 * (momed - 10) + 0.1 * (daded - 10)
                          - 0.9 * black + 0.05 * (age - 29) + v), 1, 18).astype(int)
    exp = age - ed - 6
    u = h * (0.15 * ability + 0.33 * rng.standard_normal(n))
    lw = (5.0 + 0.10 * ed + 0.08 * exp - 0.0023 * exp ** 2 - 0.18 * black
          + 0.1 * smsa66 + 0.01 * (reg - 5) + u)
    momdad14 = (rng.random(n) < .79).astype(int)
    south = (reg >= 5) & (reg <= 7)
    df = pd.DataFrame({
        "id": np.arange(1, n + 1), "nearc4": near, "ed76": ed, "age76": age,
        "daded": daded, "nodaded": (rng.random(n) < .2).astype(int), "momed": momed,
        "nomomed": (rng.random(n) < .1).astype(int), "momdad14": momdad14,
        "sinmom14": ((1 - momdad14) * (rng.random(n) < .5)).astype(int),
        **{f"reg66{k}": (reg == k).astype(int) for k in range(1, 10)},
        "lwage76": lw, "famed": famed, "black": black,
        "smsa76r": ((smsa66 + (rng.random(n) < .1)) > 0).astype(int),
        "reg76r": np.where(rng.random(n) < 0.1, ~south, south).astype(int),
        "smsa66r": smsa66,
        "kww": np.where(rng.random(n) < 0.015, np.nan,
                        np.round(33 + 3 * ability + 0.5 * ed + 5 * rng.standard_normal(n))),
        "iq": np.where(rng.random(n) < 0.32, np.nan,
                       np.round(100 + 10 * ability + 10 * rng.standard_normal(n))),
        "exp76": exp, "exp762": exp ** 2, "age762": age ** 2,
        **{f"f{k}": (famed == k).astype(int) for k in range(1, 9)},
    })
    return df


@check("entry_points")
def t_entry():
    import h1_a5
    import h1_a6
    import h1_b6
    import h2h3_weakiv
    import h3b_subvector
    import h4_chr
    import h5_cf
    import r_age1419
    import r_balance
    import r_cluster
    import verdict
    path = OUT / "synthetic_card.csv"
    synthetic_card_frame(R_ENTRY).to_csv(path, index=False)
    df = ivlib.load_analysis(path)
    entry = OUT / "entry"
    mods = {"h1-b6": h1_b6, "h1-a6": h1_a6, "h1-a5": h1_a5, "h2h3-weakiv": h2h3_weakiv,
            "h3b-subvector": h3b_subvector, "h4-chr": h4_chr, "h5-cf": h5_cf,
            "r-age1419": r_age1419, "r-balance": r_balance, "r-cluster": r_cluster}
    mt = {}
    for rid, mod in mods.items():
        t0 = time.time()
        d = entry / rid
        d.mkdir(parents=True, exist_ok=True)
        if rid in ("h3b-subvector", "h4-chr"):
            m = mod.compute(df, d)
        else:
            m = mod.compute(df)
        ivlib.write_metrics(d / "metrics.json", m)
        mt[rid] = json.loads((d / "metrics.json").read_text())
        print(f"  entry {rid}: {len(m)} metrics, {time.time() - t0:.1f} s", flush=True)
    v = verdict.judge(mt)
    ivlib.write_metrics(entry / "verdict" / "metrics.json", v)
    METRICS["entry_verdict_primary"] = v["h1_primary_reproduced"]
    METRICS["entry_h3b_rob_pieces"] = mt["h3b-subvector"]["b6_ar_rob_pieces"]
    METRICS["entry_h3b_gkm19_pieces"] = mt["h3b-subvector"]["b6_ar_gkm19_pieces"]
    # verdict rule on hand-made values: strict half-unit rule, N exact
    ivlib.require(verdict.reproduced(0.1324, 0.132, 3) == 1, "0.1324 should round to 0.132")
    ivlib.require(verdict.reproduced(0.1326, 0.132, 3) == 0, "0.1326 should not")
    ivlib.require(verdict.reproduced(None, 0.132, 3) == 0, "None is a miss")
    for col in ("spec", "delta", "ar_lo", "ar_hi", "wald_lo", "wald_hi"):
        ivlib.require(col in pd.read_csv(entry / "h4-chr" / "chr_grid.csv").columns, col)
    prof = pd.read_csv(entry / "h3b-subvector" / "profile.csv")
    for col in ("b0", "m", "kappa_p", "kappa_1", "c_gkm19", "c_gkm19q"):
        ivlib.require(col in prof.columns, col)
    ivlib.require(len(prof) == ivlib.grid_points().size, "profile rows")


def main() -> int:
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    for fn in (t_se, t_ratio, t_shapes, t_chr, t_if, t_gkm, t_sets, t_pb_s, t_pb_wn, t_entry):
        fn()
    METRICS["checks_failed"] = len(FAILED)
    METRICS["failed_list"] = ", ".join(FAILED) if FAILED else "none"
    ivlib.write_metrics(OUT / "metrics.json", METRICS)
    print(f"check-synthetic: {len(FAILED)} failed ({METRICS['failed_list']}); "
          f"wall {time.time() - t0:.1f} s")
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
