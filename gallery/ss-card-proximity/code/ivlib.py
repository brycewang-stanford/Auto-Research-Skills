"""Shared estimators for the Card (WP 4483) college-proximity replication.

Every run script imports this module. It implements plan.json design.method exactly:

- the analysis file and its re-checks (load_analysis);
- the column sets BASE_A, BASE_B, FB and the specifications A1-A6, B1-B6, T2C2, T2C5;
- OLS (statsmodels) and 2SLS (linearmodels IV2SLS, debiased=True) with conventional
  (sigma^2 = sum(e^2)/(n-k)) and HC1 (n/(n-k) times White's sandwich) standard errors;
- the one-instrument Anderson-Rubin (AR) set in closed form (H3(a), H1 homoskedastic AR
  set) and its grid check, the Conley-Hansen-Rossi (CHR) breakdown and union sets (H4);
- the control-function test and the stacked influence-function variance of the
  IV - OLS difference (H5);
- for Card's Panel B column 6 (H3(b)): the heteroskedasticity-robust projection of the
  full-vector AR statistic (class PanelB), the homoskedastic GKMC statistic and set
  (kappa_p against chi-square(1)), the GKM19 conditional critical values (Table 3
  interpolation, eq. 2.13 and fn. 4: "3T"; eq. 2.12 quantile as ivmodels 0.10.0 computes
  it: "3Q"), the common SET COMPUTATION procedure (invert_on_grid) and wrappers around
  ivmodels for the agreement checks;
- cluster-robust CR1 standard errors (r-cluster).

Notation follows design.method. Nothing here reads a file other than the analysis file
named by the caller. The only randomness is in PanelB.start_draws (default_rng(4483)).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
import scipy.linalg
import scipy.optimize
import scipy.stats
import statsmodels.api as sm
from linearmodels.iv import IV2SLS

# ----------------------------------------------------------------------------- constants

DATA = "data/derived/card_analysis.csv"
N_CARD = 3010
SEED = 4483

REG66 = [f"reg66{k}" for k in range(2, 10)]                      # region 1966 = 1 omitted
BASE_B = ["const", "black", "reg76r", "smsa76r", "smsa66r"] + REG66  # 13 columns
EXP = ["exp76", "exp762"]
BASE_A = BASE_B + EXP                                             # 15 columns
FB = (["daded", "momed", "nodaded", "nomomed"] + [f"f{k}" for k in range(1, 9)]
      + ["momdad14", "sinmom14"])                                 # 14 columns
AGE = ["age76", "age762"]
Z_B = ["nearc4"] + AGE                                            # Panel B instruments

CHI2_1_95 = 3.841459      # chi-square(1) 95% (design.method)
CHI2_3_95 = 7.814728      # chi-square(3) 95%
Z975 = 1.959964           # normal 97.5%
SY_10PCT = 16.38          # Stock-Yogo 10% maximal size, 1 instrument, 1 endogenous
MOP_5PCT_10PCT = 23.11    # Montiel Olea-Pflueger 5% size, 10% worst-case bias

# GKM19 Appendix B Table 3 (journal p. 519), k - m_W = 1, alpha = 5%: (kappa_1, c).
# Copied from sources/notes.md sec. 4b (task s-gkm19-table), all 36 finite rows; the
# printed infinity row is GKM19_CV_INF.
GKM19_TABLE3_KM1_5PCT = (
    (0.5, 0.4), (0.6, 0.5), (0.7, 0.6), (0.9, 0.7), (1.0, 0.8), (1.2, 0.9), (1.3, 1.0),
    (1.5, 1.1), (1.6, 1.2), (1.8, 1.3), (2.0, 1.4), (2.1, 1.5), (2.3, 1.6), (2.5, 1.7),
    (2.7, 1.8), (2.9, 1.9), (3.1, 2.0), (3.4, 2.1), (3.6, 2.2), (3.9, 2.3), (4.1, 2.4),
    (4.4, 2.5), (4.8, 2.6), (5.1, 2.7), (5.5, 2.8), (6.0, 2.9), (6.5, 3.0), (7.0, 3.1),
    (7.8, 3.2), (8.6, 3.3), (9.8, 3.4), (11.4, 3.5), (13.9, 3.6), (18.5, 3.7),
    (29.7, 3.8), (1000.0, 3.838),
)
GKM19_CV_INF = 3.841
GKM19_FN4_SCALE = 1000.0  # F(x) = 1 - exp(-x / 1000) for x >= 0 (our choice, fn. 4)

# Specifications: (kind, dependent, exogenous incl. const, endogenous, excluded instruments,
# focus variable, expected k). k = all right-hand-side columns including the intercept.
SPECS = {
    "A1": ("ols", "ed76", ["nearc4"] + BASE_A, [], [], "nearc4", 16),
    "A2": ("ols", "ed76", ["nearc4"] + BASE_A + FB, [], [], "nearc4", 30),
    "A3": ("ols", "lwage76", ["nearc4"] + BASE_A, [], [], "nearc4", 16),
    "A4": ("ols", "lwage76", ["nearc4"] + BASE_A + FB, [], [], "nearc4", 30),
    "A5": ("iv", "lwage76", BASE_A, ["ed76"], ["nearc4"], "ed76", 16),
    "A6": ("iv", "lwage76", BASE_A + FB, ["ed76"], ["nearc4"], "ed76", 30),
    "B1": ("ols", "ed76", Z_B + BASE_B, [], [], "nearc4", 16),
    "B2": ("ols", "ed76", Z_B + BASE_B + FB, [], [], "nearc4", 30),
    "B3": ("ols", "lwage76", Z_B + BASE_B, [], [], "nearc4", 16),
    "B4": ("ols", "lwage76", Z_B + BASE_B + FB, [], [], "nearc4", 30),
    "B5": ("iv", "lwage76", BASE_B, ["ed76"] + EXP, Z_B, "ed76", 16),
    "B6": ("iv", "lwage76", BASE_B + FB, ["ed76"] + EXP, Z_B, "ed76", 30),
    "T2C2": ("ols", "lwage76", ["ed76"] + BASE_A, [], [], "ed76", 16),
    "T2C5": ("ols", "lwage76", ["ed76"] + BASE_A + FB, [], [], "ed76", 30),
}
# Controls (exogenous columns other than the focus regressor) of the Panel A columns.
CONTROLS_A5 = BASE_A
CONTROLS_A6 = BASE_A + FB
CONTROLS_B6 = BASE_B + FB   # X of H3(b): 27 columns

RAW_NEEDED = (["lwage76", "ed76", "nearc4", "age76", "black", "reg76r", "smsa76r",
               "smsa66r", "famed", "daded", "momed", "nodaded", "nomomed", "momdad14",
               "sinmom14"] + [f"reg66{k}" for k in range(1, 10)])


class CheckFailed(RuntimeError):
    """An identity or agreement check required by design.method failed."""


def require(cond, message: str) -> None:
    """Raise CheckFailed unless cond holds (not `assert`, which -O would remove)."""
    if not bool(cond):
        raise CheckFailed(message)


def close_rel(a: float, b: float, tol: float) -> bool:
    """|a - b| <= tol x max(|a|, |b|, 1): relative, with an absolute floor near 0."""
    return abs(a - b) <= tol * max(abs(a), abs(b), 1.0)


def rel_diff(a, b) -> float:
    a, b = np.asarray(a, float), np.asarray(b, float)
    return float(np.max(np.abs(a - b) / np.maximum(np.maximum(np.abs(a), np.abs(b)), 1e-300)))


# ----------------------------------------------------------------------------- data


def check_frame(df: pd.DataFrame, n_expected: int | None = N_CARD) -> None:
    """Re-check the analysis file: N, no missing regressor, constructed variables."""
    if n_expected is not None:
        require(len(df) == n_expected, f"N = {len(df)}, expected {n_expected}")
    for name in RAW_NEEDED + EXP + ["age762"] + [f"f{k}" for k in range(1, 9)]:
        require(name in df.columns, f"column {name} missing")
        require(not df[name].isna().any(), f"missing values in {name}")
    age, ed = df["age76"].to_numpy(float), df["ed76"].to_numpy(float)
    require(np.array_equal(df["exp76"].to_numpy(float), age - ed - 6),
            "exp76 != age76 - ed76 - 6 on some row")
    require(np.array_equal(df["exp762"].to_numpy(float), df["exp76"].to_numpy(float) ** 2),
            "exp762 != exp76^2")
    require(np.array_equal(df["age762"].to_numpy(float), age ** 2), "age762 != age76^2")
    famed = df["famed"].to_numpy(float)
    for k in range(1, 9):
        require(np.array_equal(df[f"f{k}"].to_numpy(float), (famed == k).astype(float)),
                f"f{k} != 1{{famed = {k}}}")
    regs = df[[f"reg66{k}" for k in range(1, 10)]].to_numpy(float)
    require(np.all(regs.sum(axis=1) == 1), "region-1966 dummies do not sum to 1")


def load_analysis(path: str | Path = DATA, n_expected: int | None = N_CARD) -> pd.DataFrame:
    """Read the analysis file written by prepare-data and re-check it (design.method)."""
    df = pd.read_csv(path)
    check_frame(df, n_expected)
    df = df.copy()
    df["const"] = 1.0
    return df


def cols(df: pd.DataFrame, names) -> np.ndarray:
    return df[list(names)].to_numpy(dtype=float)


# ----------------------------------------------------------------------------- OLS / 2SLS


@dataclass
class Fit:
    """One regression: the focus coefficient with conventional and HC1 SEs."""
    name: str
    kind: str
    coef: float
    se_conv: float
    se_hc1: float
    n: int
    k: int
    params: pd.Series = field(repr=False)
    se_conv_all: pd.Series = field(repr=False)
    se_hc1_all: pd.Series = field(repr=False)
    resid: np.ndarray = field(repr=False)

    @property
    def se_conv_n(self) -> float:
        """Diagnostic SE with sigma^2 = sum(e^2)/n (read only if an H1 SE target fails)."""
        return self.se_conv * math.sqrt((self.n - self.k) / self.n)


def fit_ols(df: pd.DataFrame, y: str, regs: list[str], focus: str, name: str = "") -> Fit:
    X = df[regs].astype(float)
    yy = df[y].astype(float)
    require(np.linalg.matrix_rank(X.to_numpy()) == X.shape[1],
            f"{name or y}: regressors do not have full column rank")
    conv = sm.OLS(yy, X).fit()
    hc1 = sm.OLS(yy, X).fit(cov_type="HC1")
    return Fit(name, "ols", float(conv.params[focus]), float(conv.bse[focus]),
               float(hc1.bse[focus]), int(conv.nobs), X.shape[1], conv.params,
               conv.bse, hc1.bse, conv.resid.to_numpy())


def fit_2sls(df: pd.DataFrame, y: str, exog: list[str], endog: list[str],
             instr: list[str], focus: str, name: str = "") -> Fit:
    dep = df[y].astype(float)
    ex, en, iv = df[exog].astype(float), df[endog].astype(float), df[instr].astype(float)
    conv = IV2SLS(dep, ex, en, iv).fit(cov_type="unadjusted", debiased=True)
    rob = IV2SLS(dep, ex, en, iv).fit(cov_type="robust", debiased=True)
    pc, pr = conv.params.to_numpy(), rob.params.to_numpy()
    require(np.max(np.abs(pc - pr)) <= 1e-10 * max(1.0, float(np.max(np.abs(pc)))),
            "2SLS coefficients differ between covariance choices")
    return Fit(name, "iv", float(conv.params[focus]), float(conv.std_errors[focus]),
               float(rob.std_errors[focus]), int(conv.nobs), len(exog) + len(endog),
               conv.params, conv.std_errors, rob.std_errors, conv.resids.to_numpy())


def fit_spec(df: pd.DataFrame, name: str, check_k: bool = True) -> Fit:
    kind, y, exog, endog, instr, focus, k = SPECS[name]
    if kind == "ols":
        f = fit_ols(df, y, exog, focus, name)
    else:
        f = fit_2sls(df, y, exog, endog, instr, focus, name)
    if check_k:
        require(f.k == k, f"{name}: k = {f.k}, design says {k}")
    return f


# ----------------------------------------------------------------------------- matrices


def hc1_cov(X: np.ndarray, e: np.ndarray) -> np.ndarray:
    """HC1 covariance n/(n-k) (X'X)^-1 [sum x_i x_i' e_i^2] (X'X)^-1."""
    n, k = X.shape
    B = np.linalg.solve(X.T @ X, X.T)
    Be = B * e
    return n / (n - k) * Be @ Be.T


def joint_cov_focus(W: np.ndarray, E: np.ndarray, j: int, robust: bool) -> np.ndarray:
    """Joint covariance of the coefficient on column j of W across the outcomes in E.

    E holds the OLS residuals of m outcomes regressed on the same W. Robust (HC1):
    n/(n-k) (W'W)^-1 [sum w_i w_i' e_il e_im] (W'W)^-1 at entry (j, j).
    Conventional: [(W'W)^-1]_jj e_l'e_m / (n-k).
    """
    n, k = W.shape
    B = np.linalg.solve(W.T @ W, W.T)[j]          # row j of (W'W)^-1 W'
    if robust:
        A = B[:, None] * E                       # n x m
        return n / (n - k) * A.T @ A
    WtWinv_jj = float(np.linalg.inv(W.T @ W)[j, j])
    return WtWinv_jj * (E.T @ E) / (n - k)


# ----------------------------------------------------------------------------- 1-D sets


def _roots(a: float, b: float, c: float) -> tuple[float, float]:
    disc = b * b - 4 * a * c
    sq = math.sqrt(disc)
    qq = -0.5 * (b + math.copysign(sq, b)) if b != 0 else -0.5 * sq
    r1 = qq / a
    r2 = c / qq if qq != 0 else -r1
    return (min(r1, r2), max(r1, r2))


def quad_set(a: float, b: float, c: float) -> list[tuple[float, float]]:
    """{x : a x^2 + b x + c <= 0} as a sorted list of closed pieces (+-inf allowed)."""
    inf = math.inf
    if a == 0.0:
        if b > 0:
            return [(-inf, -c / b)]
        if b < 0:
            return [(-c / b, inf)]
        return [(-inf, inf)] if c <= 0 else []
    disc = b * b - 4 * a * c
    if a > 0:
        if disc < 0:
            return []
        return [_roots(a, b, c)]
    if disc <= 0:
        return [(-inf, inf)]
    r1, r2 = _roots(a, b, c)
    return [(-inf, r1), (r2, inf)]


def set_shape(pieces) -> str:
    if not pieces:
        return "empty"
    if len(pieces) == 1:
        lo, hi = pieces[0]
        if math.isinf(lo) and math.isinf(hi):
            return "whole-line"
        if math.isinf(lo) or math.isinf(hi):
            return "half-line"
        return "bounded"
    unb = math.isinf(pieces[0][0]) and math.isinf(pieces[-1][1])
    if len(pieces) == 2 and unb:
        return "two-half-lines"
    return f"{len(pieces)}-pieces" + ("-unbounded" if any(
        math.isinf(x) for p in pieces for x in p) else "")


def in_set(x: float, pieces) -> bool:
    return any(lo <= x <= hi for lo, hi in pieces)


def finite_or_none(x):
    return None if x is None or (isinstance(x, float) and not math.isfinite(x)) else float(x)


def pieces_str(pieces) -> str:
    if not pieces:
        return "empty"
    return " U ".join(f"[{lo:.6f}, {hi:.6f}]" for lo, hi in pieces)


def merge_pieces(pieces) -> list[tuple[float, float]]:
    out: list[list[float]] = []
    for lo, hi in sorted(pieces):
        if out and lo <= out[-1][1]:
            out[-1][1] = max(out[-1][1], hi)
        else:
            out.append([lo, hi])
    return [(a, b) for a, b in out]


def positive_bounded(pieces) -> int:
    """Decision rule (plan.json H3): one bounded interval whose lower bound is above 0."""
    return int(len(pieces) == 1 and set_shape(pieces) == "bounded" and pieces[0][0] > 0)


# ----------------------------------------------------------------------------- H3(a) / AR


@dataclass
class OneInstrumentAR:
    """Reduced form lambda and first stage pi on one instrument, same regressors W."""
    lam: float
    pi: float
    V: np.ndarray          # 2x2 covariance of (lam, pi): [[V_ll, V_lp], [V_lp, V_pp]]
    crit: float
    robust: bool
    n: int
    k: int

    def stat(self, b0):
        b0 = np.asarray(b0, float)
        num = (self.lam - b0 * self.pi) ** 2
        den = self.V[0, 0] - 2 * b0 * self.V[0, 1] + b0 ** 2 * self.V[1, 1]
        return num / den

    def pieces(self, lam_shift: float = 0.0):
        """AR set; lam_shift subtracts gamma0 from lambda (outcome y - gamma0 z, H4)."""
        lam = self.lam - lam_shift
        c = self.crit
        a = self.pi ** 2 - c * self.V[1, 1]
        b = -2.0 * (lam * self.pi - c * self.V[0, 1])
        cc = lam ** 2 - c * self.V[0, 0]
        return quad_set(a, b, cc)

    @property
    def se_lam(self) -> float:
        return math.sqrt(self.V[0, 0])

    @property
    def se_pi(self) -> float:
        return math.sqrt(self.V[1, 1])


def one_instrument_ar(df: pd.DataFrame, controls: list[str], robust: bool = True,
                      crit: float = CHI2_1_95, y: str = "lwage76", x: str = "ed76",
                      z: str = "nearc4") -> OneInstrumentAR:
    """lambda_hat, pi_hat and their joint covariance from two OLS on (z, controls)."""
    W = cols(df, [z] + controls)
    Y = cols(df, [y, x])
    coef, *_ = np.linalg.lstsq(W, Y, rcond=None)
    E = Y - W @ coef
    V = joint_cov_focus(W, E, 0, robust)
    return OneInstrumentAR(float(coef[0, 0]), float(coef[0, 1]), V, crit, robust,
                           W.shape[0], W.shape[1])


def ar_grid_check(df: pd.DataFrame, controls: list[str], ar: OneInstrumentAR,
                  lo: float = -1.0, hi: float = 1.0, step: float = 1e-4,
                  y: str = "lwage76", x: str = "ed76", z: str = "nearc4") -> dict:
    """Recompute AR(b0) on a grid as the HC1 t^2 of z in OLS of y - b0 x on (z, controls).

    Returns the largest relative difference from the closed form and the number of grid
    points whose acceptance differs from the closed-form set while lying more than one
    grid step from every closed-form bound (must be 0).
    """
    require(ar.robust, "grid check is for the robust AR set")
    W = cols(df, [z] + controls)
    n, k = W.shape
    yv, xv = df[y].to_numpy(float), df[x].to_numpy(float)
    grid = lo + step * np.arange(int(round((hi - lo) / step)) + 1)
    Qm, R = np.linalg.qr(W)
    a_row = scipy.linalg.solve_triangular(R, Qm.T)[0]          # row of (W'W)^-1 W' for z
    stats = np.empty_like(grid)
    for s in range(0, grid.size, 1000):
        b = grid[s:s + 1000]
        Yt = yv[:, None] - xv[:, None] * b[None, :]
        coef = scipy.linalg.solve_triangular(R, Qm.T @ Yt)
        resid = Yt - W @ coef
        var = n / (n - k) * ((a_row[:, None] * resid) ** 2).sum(axis=0)
        stats[s:s + 1000] = coef[0] ** 2 / var
    closed = ar.stat(grid)
    pieces = ar.pieces()
    acc_grid = stats <= ar.crit
    acc_closed = np.array([in_set(b, pieces) for b in grid])
    bounds = [v for p in pieces for v in p if math.isfinite(v)]
    far = np.array([all(abs(b - v) > step for v in bounds) for b in grid]) if bounds else \
        np.ones(grid.size, bool)
    bad = int(np.sum((acc_grid != acc_closed) & far))
    # acceptance of the grid statistic against the closed-form statistic, point by point
    bad_stat = int(np.sum((acc_grid != (closed <= ar.crit)) & far))
    return {"grid_points": int(grid.size), "max_rel_diff": rel_diff(stats, closed),
            "mismatch_beyond_one_step": bad + bad_stat}


# ----------------------------------------------------------------------------- H4 / CHR


def chr_breakdown(ar: OneInstrumentAR) -> float:
    """delta* = lambda_hat - z_0.975 se(lambda_hat), 0 if negative (one instrument)."""
    return max(0.0, ar.lam - Z975 * ar.se_lam)


def chr_breakdown_grid(ar: OneInstrumentAR, step: float = 1e-5, upper: float = 0.05) -> float:
    """Smallest gamma0 on a grid at which the AR set for y - gamma0 z contains 0."""
    while True:
        g = step * np.arange(int(round(upper / step)) + 1)
        for gamma0 in g:
            if in_set(0.0, ar.pieces(gamma0)):
                return float(gamma0)
        if upper >= 0.10 - 1e-12:
            return math.nan
        upper = 0.10


def iv_one_instrument_matrices(df: pd.DataFrame, controls: list[str], y="lwage76",
                               x="ed76", z="nearc4") -> dict:
    """Pieces for the just-identified 2SLS of y on (x, controls) with (z, controls)."""
    R = cols(df, [x] + controls)
    Q = cols(df, [z] + controls)
    yv = df[y].to_numpy(float)
    zv = df[z].to_numpy(float)
    Qq, _ = np.linalg.qr(Q)
    Xhat = Qq @ (Qq.T @ R)                                 # P_Q R
    Qx, Rx = np.linalg.qr(Xhat)
    B = scipy.linalg.solve_triangular(Rx, Qx.T)            # (Xhat'Xhat)^-1 Xhat' (QR)
    a = B[0]                                               # e1'(R'P_Q R)^-1 xhat_i
    beta_y = B @ yv
    beta_z = B @ zv
    return {"R": R, "Q": Q, "a": a, "beta_y": beta_y, "beta_z": beta_z,
            "u_y": yv - R @ beta_y, "u_z": zv - R @ beta_z, "n": R.shape[0], "k": R.shape[1]}


def chr_wald(m: dict, gammas: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Wald 2SLS interval for outcome y - gamma0 z (HC1), for each gamma0."""
    n, k = m["n"], m["k"]
    beta = m["beta_y"][0] - gammas * m["beta_z"][0]
    U = m["u_y"][:, None] - m["u_z"][:, None] * gammas[None, :]
    se = np.sqrt(n / (n - k) * ((m["a"][:, None] * U) ** 2).sum(axis=0))
    return beta, beta - Z975 * se, beta + Z975 * se


def chr_union(ar: OneInstrumentAR, m: dict, deltas: np.ndarray, step: float = 1e-4) -> list:
    """Union over gamma0 in {0, step, ..., delta} of the AR set and of the Wald interval."""
    out = []
    gmax = float(np.max(deltas))
    gammas = step * np.arange(int(round(gmax / step)) + 1)
    beta, wlo, whi = chr_wald(m, gammas)
    ar_sets = [ar.pieces(g) for g in gammas]
    for d in deltas:
        idx = gammas <= d + 1e-12
        u_ar = merge_pieces([p for s, keep in zip(ar_sets, idx) if keep for p in s])
        out.append({
            "delta": float(d),
            "ar_union_lo": u_ar[0][0] if u_ar else math.nan,
            "ar_union_hi": u_ar[-1][1] if u_ar else math.nan,
            "ar_union_npieces": len(u_ar),
            "wald_union_lo": float(np.min(wlo[idx])),
            "wald_union_hi": float(np.max(whi[idx])),
        })
    return out


def chr_wald_breakdown(m: dict, step: float = 1e-5, upper: float = 0.05) -> float:
    while True:
        g = step * np.arange(int(round(upper / step)) + 1)
        _, lo, hi = chr_wald(m, g)
        hit = np.nonzero((lo <= 0) & (hi >= 0))[0]
        if hit.size:
            return float(g[hit[0]])
        if upper >= 0.10 - 1e-12:
            return math.nan
        upper = 0.10


# ----------------------------------------------------------------------------- H5


def h5_control_function(df: pd.DataFrame, controls: list[str]) -> dict:
    """Robust control-function test and the stacked influence-function IV - OLS interval."""
    n = len(df)
    fs = sm.OLS(df["ed76"].astype(float), df[["nearc4"] + controls].astype(float)).fit()
    vhat = fs.resid.to_numpy()
    Xcf = np.column_stack([cols(df, ["ed76"] + controls), vhat])
    cf = sm.OLS(df["lwage76"].to_numpy(float), Xcf).fit(cov_type="HC1")
    rho, se_rho = float(cf.params[-1]), float(cf.bse[-1])
    t = rho / se_rho
    p = 2.0 * (1.0 - scipy.stats.norm.cdf(abs(t)))
    iv = fit_2sls(df, "lwage76", controls, ["ed76"], ["nearc4"], "ed76")
    ols = fit_ols(df, "lwage76", ["ed76"] + controls, "ed76")
    D = iv.coef - ols.coef
    m = iv_one_instrument_matrices(df, controls)
    k = m["k"]
    psi_iv = m["a"] * m["u_y"]
    R = m["R"]
    b_ols = np.linalg.solve(R.T @ R, R.T)[0]
    psi_ols = b_ols * ols.resid
    var_iv_if = n / (n - k) * np.sum(psi_iv ** 2)
    var_ols_if = n / (n - k) * np.sum(psi_ols ** 2)
    require(rel_diff(var_iv_if, iv.se_hc1 ** 2) < 1e-8, "IF variance of 2SLS != HC1")
    require(rel_diff(var_ols_if, ols.se_hc1 ** 2) < 1e-8, "IF variance of OLS != HC1")
    var_D = n / (n - k) * np.sum((psi_iv - psi_ols) ** 2)
    se_D = math.sqrt(var_D)
    g = float(sm.OLS(vhat, cols(df, ["ed76"] + controls)).fit().params[0])
    require(abs(D - (-rho * g)) <= 1e-10 * max(1.0, abs(D)), "D != -rho g")
    require(abs(float(cf.params[0]) - iv.coef) <= 1e-10 * max(1.0, abs(iv.coef)),
            "control-function coefficient on ed76 != 2SLS")
    haus = D / math.sqrt(iv.se_conv ** 2 - ols.se_conv ** 2) \
        if iv.se_conv > ols.se_conv else math.nan
    return {"rho": rho, "rho_se": se_rho, "cf_t": t, "cf_p": p,
            "cf_reject": int(abs(t) > Z975), "iv": iv.coef, "ols": ols.coef, "diff": D,
            "diff_se": se_D, "diff_lo": D - Z975 * se_D, "diff_hi": D + Z975 * se_D,
            "hausman_t_conv": haus, "var_iv_if": var_iv_if, "var_ols_if": var_ols_if,
            "psi_iv": psi_iv, "psi_ols": psi_ols}


# ----------------------------------------------------------------------------- GKM19


_TBL_K = np.array([0.0] + [r[0] for r in GKM19_TABLE3_KM1_5PCT])
_TBL_C = np.array([0.0] + [r[1] for r in GKM19_TABLE3_KM1_5PCT])


def c_gkm19_table(kappa1):
    """(3T) GKM19 critical value: eq. (2.13) with (0, 0) anchor; fn. 4 above 1000."""
    k1 = np.asarray(kappa1, float)
    lin = np.interp(np.minimum(k1, _TBL_K[-1]), _TBL_K, _TBL_C)
    F = 1.0 - np.exp(-np.maximum(k1 - _TBL_K[-1], 0.0) / GKM19_FN4_SCALE)
    tail = (1.0 - F) * _TBL_C[-1] + F * GKM19_CV_INF
    out = np.where(k1 <= _TBL_K[-1], lin, tail)
    return float(out) if np.ndim(out) == 0 else out


def p_gkm19_ivmodels(kappa_p: float, kappa_1: float, k: int = 3, mw: int = 2) -> float:
    """eq. (2.12) conditional p-value of kappa_p given kappa_1, as ivmodels 0.10.0 computes it."""
    from ivmodels.tests.anderson_rubin import \
        more_powerful_subvector_anderson_rubin_critical_value_function as fn
    # kappa_p is 0 at the 2SLS estimate of a just-identified model; rounding can make it
    # slightly negative, where the density's x^(-1/2) term is undefined.
    return float(fn(min(max(kappa_p, 0.0), kappa_1), kappa_1, k, mw))


def c_gkm19_quantile(kappa1: float, alpha: float = 0.05, k: int = 3, mw: int = 2) -> float:
    """(3Q) the 1 - alpha quantile of the eq. (2.12) distribution (ivmodels function)."""
    from ivmodels.tests.anderson_rubin import \
        more_powerful_subvector_anderson_rubin_critical_value_function as fn
    # The quantile lies below the chi-square(k - mw) quantile; for k - mw = 1 the upper
    # bracket 20 (tail probability < 1e-5) keeps quad's integration range short. The
    # lower bracket stays near 0 however large kappa_1 is (in Panel B kappa_1 grows like
    # b0^2, because exp76 + ed76 = age76 - 6 lies in the span of the instruments).
    upper = min(kappa1 * (1 - 1e-12), 20.0)
    lower = 1e-12 * min(kappa1, 1.0)
    return float(scipy.optimize.brentq(lambda z: fn(z, kappa1, k, mw) - alpha,
                                       lower, upper, xtol=1e-12,
                                       rtol=1e-14, maxiter=500))


# ----------------------------------------------------------------------------- set computation


def outer_grid(n_outer: int = 400, outer_max: float = 1e5) -> np.ndarray:
    """400 log-spaced points beyond |b0| = 1 up to 1e5 (1 itself is on the fine grid)."""
    return np.logspace(0.0, math.log10(outer_max), n_outer + 1)[1:]


def grid_points(fine_step: float = 5e-4, n_outer: int = 400, outer_max: float = 1e5) -> np.ndarray:
    m = int(round(1.0 / fine_step))
    fine = np.arange(-m, m + 1) * fine_step
    out = outer_grid(n_outer, outer_max)
    return np.concatenate([-out[::-1], fine, out])


def _bisect(accept, acc: float, rej: float, tol_abs: float, tol_rel: float) -> float:
    for _ in range(400):
        scale = max(abs(acc), abs(rej))
        tol = tol_abs if scale <= 1.0 else tol_rel * scale
        if abs(acc - rej) <= tol:
            break
        mid = 0.5 * (acc + rej)
        if accept(mid):
            acc = mid
        else:
            rej = mid
    return 0.5 * (acc + rej)


@dataclass
class GridSet:
    pieces: list
    points: np.ndarray
    accepted: np.ndarray
    unbounded_lo: bool
    unbounded_hi: bool

    @property
    def lo(self):
        return self.pieces[0][0] if self.pieces else math.nan

    @property
    def hi(self):
        return self.pieces[-1][1] if self.pieces else math.nan

    @property
    def npieces(self) -> int:
        return len(self.pieces)

    @property
    def shape(self) -> str:
        return set_shape(self.pieces)


def invert_on_grid(accept, accepted: np.ndarray | None = None, points: np.ndarray | None = None,
                   tol_abs: float = 1e-6, tol_rel: float = 1e-6) -> GridSet:
    """SET COMPUTATION of design.method for any accept(b0) -> bool.

    Acceptance is evaluated on the ordered point list (fine grid on [-1, 1], step 5e-4,
    and 400 log-spaced outer points per side up to 1e5); every neighbouring pair with
    different acceptance holds a boundary, found by bisection to an absolute tolerance of
    1e-6 for |b0| <= 1 and a relative one beyond. A side is unbounded only if the
    accepted piece reaches the last outer point (|b0| = 1e5) on that side.
    """
    pts = grid_points() if points is None else points
    acc = np.array([bool(accept(b)) for b in pts]) if accepted is None else accepted.astype(bool)
    pieces = []
    i, n = 0, pts.size
    while i < n:
        if not acc[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and acc[j + 1]:
            j += 1
        lo = -math.inf if i == 0 else _bisect(accept, pts[i], pts[i - 1], tol_abs, tol_rel)
        hi = math.inf if j == n - 1 else _bisect(accept, pts[j], pts[j + 1], tol_abs, tol_rel)
        pieces.append((lo, hi))
        i = j + 1
    return GridSet(pieces, pts, acc, bool(acc[0]), bool(acc[-1]))


# ----------------------------------------------------------------------------- Panel B (H3(b))


def _resid_on(X: np.ndarray, A: np.ndarray) -> np.ndarray:
    Qx, _ = np.linalg.qr(X)
    return A - Qx @ (Qx.T @ A)


class PanelB:
    """H3(b) for Card's Panel B col 6: y = b x + W g + X d + u, instruments Z.

    y = lwage76, x = ed76, W = (exp76, exp762), Z = (nearc4, age76, age762),
    X = BASE_B + FB (27 columns incl. intercept). Holds
    - the stacked regression of (y, x, W1, W2) on (Z, X): Z-coefficients pi_j (3-vectors)
      and their joint HC1 covariance S (blocks S_jl, 3x3), for the robust HAR(b0, g);
    - PP, MM: cross-products of (y, x, W) residualised on X, under P_Z and M_Z, for the
      homoskedastic kappa_p, kappa_1 (GKMC, GKM19) with Omega scaled by n - kZ - kX.
    """

    def __init__(self, y, x, W, Z, X, start_draws: np.ndarray | None = None,
                 g_full: np.ndarray | None = None, g_se: np.ndarray | None = None):
        self.y, self.x = np.asarray(y, float), np.asarray(x, float)
        self.W, self.Z, self.X = (np.asarray(a, float) for a in (W, Z, X))
        n = self.y.size
        self.n, self.kZ, self.kX = n, self.Z.shape[1], self.X.shape[1]
        self.mW = self.W.shape[1]
        self.dfd = n - self.kZ - self.kX
        Y4 = np.column_stack([self.y, self.x, self.W])
        self.Y4 = Y4
        Q = np.column_stack([self.Z, self.X])
        self.Q = Q
        Qm, R = np.linalg.qr(Q)
        B = scipy.linalg.solve_triangular(R, Qm.T)               # (Q'Q)^-1 Q'
        coef = B @ Y4
        E = Y4 - Q @ coef
        self.pis = coef[: self.kZ].T                             # 4 x 3
        Bz = B[: self.kZ]
        kq = Q.shape[1]
        S = np.empty((4, 4, self.kZ, self.kZ))
        A = [Bz * E[:, j] for j in range(4)]
        for j in range(4):
            for l in range(4):
                S[j, l] = n / (n - kq) * A[j] @ A[l].T
        self.S = S
        # homoskedastic pieces
        Yt = _resid_on(self.X, Y4)
        Zt = _resid_on(self.X, self.Z)
        Qz, _ = np.linalg.qr(Zt)
        PY = Qz @ (Qz.T @ Yt)
        self.PP = PY.T @ PY
        MY = Yt - PY
        self.MM = MY.T @ MY
        self.PP = 0.5 * (self.PP + self.PP.T)
        self.MM = 0.5 * (self.MM + self.MM.T)
        self.g_full = g_full
        self.g_se = g_se
        self.start_draws = start_draws

    # --- robust projection
    def _a(self, b0, g):
        return np.array([1.0, -b0, -g[0], -g[1]])

    def har(self, b0: float, g) -> float:
        a = self._a(b0, g)
        t = a @ self.pis
        V = np.tensordot(np.outer(a, a), self.S, axes=([0, 1], [0, 1]))
        return float(t @ np.linalg.solve(V, t))

    def har_and_grad(self, g, b0: float):
        a = self._a(b0, g)
        t = a @ self.pis
        V = np.tensordot(np.outer(a, a), self.S, axes=([0, 1], [0, 1]))
        w = np.linalg.solve(V, t)
        f = float(t @ w)
        grad = np.empty(2)
        for m in range(2):
            j = 2 + m
            dt = -self.pis[j]
            dVda = np.tensordot(a, self.S[j], axes=(0, 0))   # sum_l a_l S_jl
            dV = -(dVda + dVda.T)
            grad[m] = 2.0 * w @ dt - w @ dV @ w
        return f, grad

    def har_direct(self, b0: float, g) -> float:
        """HC1 Wald statistic of Z in the OLS of y - b0 x - W g on (Z, X) (statsmodels)."""
        r = self.y - b0 * self.x - self.W @ np.asarray(g, float)
        res = sm.OLS(r, self.Q).fit(cov_type="HC1")
        t = res.params[: self.kZ]
        V = res.cov_params()[: self.kZ, : self.kZ]
        return float(t @ np.linalg.solve(V, t))

    def har_grid(self, b0: float, G1: np.ndarray, G2: np.ndarray) -> np.ndarray:
        """HAR(b0, g) on arrays of g (vectorised; for the brute-force check)."""
        g1, g2 = G1.ravel(), G2.ravel()
        a = np.stack([np.ones_like(g1), -b0 * np.ones_like(g1), -g1, -g2], axis=1)
        t = a @ self.pis
        V = np.einsum("pj,pl,jlab->pab", a, a, self.S)
        w = np.linalg.solve(V, t[..., None])[..., 0]
        return np.einsum("pa,pa->p", t, w).reshape(G1.shape)

    def g_2sls(self, b0: float) -> np.ndarray:
        C = self._C(b0)
        P = C.T @ self.PP @ C
        return np.linalg.solve(P[1:, 1:], P[1:, 0])

    def g_liml(self, b0: float) -> np.ndarray:
        C = self._C(b0)
        P, M = C.T @ self.PP @ C, C.T @ self.MM @ C
        kap = 1.0 + scipy.linalg.eigh(P, M, eigvals_only=True)[0]
        A = P + (1.0 - kap) * M
        return np.linalg.solve(A[1:, 1:], A[1:, 0])

    def starts(self, b0: float) -> np.ndarray:
        ga = self.g_2sls(b0)
        out = [ga, self.g_liml(b0)]
        if self.g_full is not None:
            out.append(np.asarray(self.g_full, float))
        if self.start_draws is not None:
            out.extend(ga + 5.0 * self.g_se * d for d in self.start_draws)
        return np.array(out)

    def profile(self, b0: float) -> tuple[float, np.ndarray]:
        """m(b0) = min over g of HAR(b0, g): BFGS (gtol 1e-10) from every start."""
        best, arg = math.inf, None
        for s in self.starts(b0):
            r = scipy.optimize.minimize(self.har_and_grad, s, args=(b0,), jac=True,
                                        method="BFGS", options={"gtol": 1e-10})
            f = float(r.fun)
            if f < best:
                best, arg = f, np.asarray(r.x)
        return best, arg

    # --- homoskedastic
    def _C(self, b0: float) -> np.ndarray:
        C = np.zeros((4, 3))
        C[0, 0], C[1, 0] = 1.0, -b0
        C[2, 1] = C[3, 2] = 1.0
        return C

    def kappas(self, b0: float) -> tuple[float, float]:
        """(kappa_p, kappa_1): smallest and largest roots of |k Omega - (Y0,W)'P_Z(Y0,W)|."""
        C = self._C(b0)
        P, M = C.T @ self.PP @ C, C.T @ self.MM @ C
        d = 1.0 / np.sqrt(np.diag(M))          # equilibrate; the roots are unchanged
        P, M = P * np.outer(d, d), M * np.outer(d, d)
        ev = scipy.linalg.eigh(P, M, eigvals_only=True)
        return float(self.dfd * ev[0]), float(self.dfd * ev[-1])

    def gkmc_quadric(self, crit: float = CHI2_1_95) -> list[tuple[float, float]]:
        """Closed-form GKMC set: {b : min_g a'(PP - q MM)a <= 0}, a = (1, -b, -g)."""
        q = crit / self.dfd
        H = self.PP - q * self.MM
        Hvv = H[2:, 2:]
        if np.min(np.linalg.eigvalsh(Hvv)) <= 0:
            return [(-math.inf, math.inf)]
        G = H[:2, :2] - H[:2, 2:] @ np.linalg.solve(Hvv, H[2:, :2])
        # u = (1, -b): G00 - 2 b G01 + b^2 G11 <= 0
        return quad_set(float(G[1, 1]), float(-2.0 * G[0, 1]), float(G[0, 0]))


def panel_b_from_frame(df: pd.DataFrame, b6: Fit | None = None, seed: int = SEED,
                       n_draws: int = 20) -> PanelB:
    """PanelB for Card's col 6 from the analysis frame, with the design's starting values."""
    if b6 is None:
        b6 = fit_spec(df, "B6")
    g_full = b6.params[EXP].to_numpy(float)
    g_se = b6.se_hc1_all[EXP].to_numpy(float)
    draws = np.random.default_rng(seed).standard_normal((n_draws, 2))
    return PanelB(df["lwage76"], df["ed76"], cols(df, EXP), cols(df, Z_B),
                  cols(df, CONTROLS_B6), start_draws=draws, g_full=g_full, g_se=g_se)


# ----------------------------------------------------------------------------- ivmodels


def ivmodels_panel_b(pb: PanelB, b0: float) -> dict:
    """ivmodels 0.10.0 AR statistic (chi2 and gkm p-values) and its kappa_1 (x dfd)."""
    from ivmodels.models.kclass import KClass
    from ivmodels.tests import anderson_rubin_test
    from ivmodels.utils import oproj
    C = pb.X[:, 1:]          # X without the intercept; ivmodels fits the intercept
    stat, p_chi2 = anderson_rubin_test(pb.Z, pb.x.reshape(-1, 1), pb.y, np.array([b0]),
                                       W=pb.W, C=C, critical_values="chi2",
                                       fit_intercept=True)
    _, p_gkm = anderson_rubin_test(pb.Z, pb.x.reshape(-1, 1), pb.y, np.array([b0]),
                                   W=pb.W, C=C, critical_values="gkm", fit_intercept=True)
    Xc = np.column_stack([np.ones(pb.n), C])
    xr, yr, Zr, Wr = oproj(Xc, pb.x.reshape(-1, 1), pb.y, pb.Z, pb.W)
    spec = KClass._spectrum(X=Wr, y=yr - xr[:, 0] * b0, Z=Zr)
    return {"stat": float(stat), "kappa_p": float(stat) * (pb.kZ - pb.mW),
            "p_chi2": float(p_chi2), "p_gkm": float(p_gkm),
            "kappa_1": float(spec[-1]) * pb.dfd}


def ivmodels_inverse(pb: PanelB, critical_values: str) -> list[tuple[float, float]]:
    from ivmodels.confidence_set import ConfidenceSet
    from ivmodels.quadric import Quadric
    from ivmodels.tests import inverse_anderson_rubin_test
    res = inverse_anderson_rubin_test(pb.Z, pb.x.reshape(-1, 1), pb.y, alpha=0.05, W=pb.W,
                                      C=pb.X[:, 1:], critical_values=critical_values,
                                      fit_intercept=True)
    if isinstance(res, Quadric):
        res = ConfidenceSet.from_quadric(res)
    return sorted((float(a), float(b)) for a, b in res.boundaries)


def bounds_diff(p1, p2) -> float:
    """Largest absolute difference between matching finite bounds; inf if shapes differ."""
    if len(p1) != len(p2):
        return math.inf
    worst = 0.0
    for (a1, b1), (a2, b2) in zip(p1, p2):
        for u, v in ((a1, a2), (b1, b2)):
            if math.isinf(u) or math.isinf(v):
                if u != v:
                    return math.inf
            else:
                worst = max(worst, abs(u - v))
    return worst


# ----------------------------------------------------------------------------- clustering


def cr1_se(X: np.ndarray, e: np.ndarray, groups: np.ndarray, j: int) -> float:
    """CR1 SE of coefficient j: G/(G-1) (n-1)/(n-k) sandwich with cluster sums."""
    n, k = X.shape
    B = np.linalg.solve(X.T @ X, X.T)
    _, inv = np.unique(groups, return_inverse=True)
    G = inv.max() + 1
    s = np.zeros((G, k))
    np.add.at(s, inv, X * e[:, None])
    meat = s.T @ s
    XtXi = np.linalg.inv(X.T @ X)
    V = XtXi @ meat @ XtXi * (G / (G - 1)) * ((n - 1) / (n - k))
    del B
    return float(math.sqrt(V[j, j]))


def region_smsa_cells(df: pd.DataFrame) -> np.ndarray:
    region = (cols(df, [f"reg66{k}" for k in range(1, 10)]) @ np.arange(1, 10)).astype(int)
    return region * 10 + df["smsa66r"].to_numpy(int)


# ----------------------------------------------------------------------------- output


def _clean(v):
    if isinstance(v, (bool, np.bool_)):
        return int(v)
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (float, np.floating)):
        v = float(v)
        return v if math.isfinite(v) else None
    if v is None or isinstance(v, (int, str)):
        return v
    raise TypeError(f"metric value of type {type(v).__name__} is not flat")


def write_metrics(path: str | Path, metrics: dict) -> None:
    """Write a flat JSON object; non-finite floats become null (the claim text says why)."""
    flat = {k: _clean(v) for k, v in metrics.items()}
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(flat, indent=2) + "\n")


def run_dir(run_id: str) -> Path:
    p = Path("runs") / run_id
    p.mkdir(parents=True, exist_ok=True)
    return p
