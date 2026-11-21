"""Estimators and inference for ss-ca-fastfood-wage (plan.json design.method).

One function per estimator and per inference step. Nothing here is random. Every run script
imports this module; check-methods (code/test_sclib.py) tests it on the Prop 99 data and on
synthetic panels before any analysis run.

Notation (design.method NOTATION): quarters are integers qi = 4 * year + quarter - 1, so the
difference of two quarter indices is elapsed calendar quarters (the COVID gap counts as
elapsed time). A panel holds every quarter of its file on one grid; "positions" are column
numbers on that grid.

Contents
  quarters ........ qidx, qlabel, qparse, COVID, windows (fit F, trend, A, P, year 1, year 2)
  data ............ Panel: unit series E, P, W with the fixed 2014-2019 seasonal factors,
                    donor aggregates (AGG) and population-weighted donor means (POPW)
  seasonal ........ seasonal_factors, seasonal_adjust (2x4 centred MA on 2014Q1-2019Q4)
  weights ......... simplex_ls (SLSQP, simplex, uniform start, ftol 1e-12, maxiter 2000),
                    kkt_residual
  estimators ...... dd_taus, ddt_slope, ddt_taus, ddt_endpoint_slope, sc_fit (demeaned SC),
                    sigma_hat (eq. 2.2), sdid_fit (Algorithm 1, no sparsification)
  candidates ...... CANDIDATES (24, design order), parse_candidate, estimate, estimate_reused
  inference ....... placebo_inference (placebo taus, SE_s, SE_n, SE = max, Ferman-Pinto step 3)
  df and critical values . satterthwaite_df, nu_from_s2, nu_for_donors (nu = min(J, nu_hat)),
                    t_quantile, l_quantiles, critical_values, intervals, one_sided_reject
  level check ..... level_check_units, rejection_rates, population_terciles, decision_set_l
  decisions ....... h2_sign, h2_size, h2_label, H2_CELLS, label_probabilities, h3_label,
                    mde, h90
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import minimize

# --------------------------------------------------------------------------- constants

CA = "06"
# Dube's 20 federal-minimum states, in the order design.data lists them
D20 = ["01", "13", "19", "16", "18", "20", "21", "22", "28", "37", "38", "33", "40", "42", "45",
       "47", "48", "49", "55", "56"]
ALL51 = ["01", "02", "04", "05", "06", "08", "09", "10", "11", "12", "13", "15", "16", "17", "18",
         "19", "20", "21", "22", "23", "24", "25", "26", "27", "28", "29", "30", "31", "32", "33",
         "34", "35", "36", "37", "38", "39", "40", "41", "42", "44", "45", "46", "47", "48", "49",
         "50", "51", "53", "54", "55", "56"]
R50 = [u for u in ALL51 if u != CA]
POOLS = {"D20": D20, "R50": R50}
OIL = ["38", "56", "40", "22", "48"]          # ND, WY, OK, LA, TX (check-methods hetero-A designs)
AK_MI = ["02", "26"]                          # dropped by CEMN (deviation D4)
B_SIZE = 0.02                                 # the H2 bound b
INDUSTRIES = ["722513", "722511", "7225", "10", "nonff"]


def qidx(year, q):
    return 4 * int(year) + int(q) - 1


def qlabel(qi):
    return f"{qi // 4}Q{qi % 4 + 1}"


def qparse(label):
    y, q = str(label).split("Q")
    return qidx(int(y), int(q))


COVID = frozenset(range(qidx(2020, 1), qidx(2021, 4) + 1))   # C = 2020Q1-2021Q4
SA_FIRST, SA_LAST = qidx(2014, 1), qidx(2019, 4)              # seasonal-factor years
PRE_END = qidx(2019, 4)                                       # cutoff of select and level-mde
FIT_START = qidx(2014, 1)
REAL_B = qidx(2023, 3)
PSEUDO_DATES = [qidx(2016, 1), qidx(2016, 2), qidx(2016, 3), qidx(2016, 4), qidx(2017, 1),
                qidx(2017, 2)]


# --------------------------------------------------------------------------- windows

@dataclass
class Windows:
    """Quarter sets of one estimate (design.method NOTATION). All entries are quarter indices.

    B       base quarter
    fit     fit window F (quarters fit_start..B not in C, unless stated otherwise)
    trend   DDT trend window (B-8..B not in C, unless stated otherwise)
    win     named estimation windows; 'pooled' is the 8-quarter post window P
    """
    B: int
    fit: list
    trend: list
    win: dict
    endpoint_lag: int = 8
    note: str = ""
    tpost_n: object = None      # SDID zeta's T_post when 'pooled' is not among the windows

    @property
    def tpost(self):
        return int(self.tpost_n) if self.tpost_n is not None else len(self.win["pooled"])


def standard_windows(B, fit_start=FIT_START, years=True, anticip=True, pooled=True):
    """F(B), trend B-8..B, A(B) = {B+1, B+2}, P(B) = B+3..B+10, year 1 = B+3..B+6, year 2 = B+7..B+10.
    pooled=False leaves P out of the windows (anticip); SDID's zeta still uses T_post = 8."""
    fit = [q for q in range(fit_start, B + 1) if q not in COVID]
    trend = [q for q in range(B - 8, B + 1) if q not in COVID]
    win = {"pooled": list(range(B + 3, B + 11))} if pooled else {}
    if years:
        win["y1"] = list(range(B + 3, B + 7))
        win["y2"] = list(range(B + 7, B + 11))
    if anticip:
        win["A"] = [B + 1, B + 2]
    return Windows(B=B, fit=fit, trend=trend, win=win, tpost_n=None if pooled else 8)


def custom_windows(B, pooled, fit_start=FIT_START, trend="b8", extra=None, note=""):
    """Windows for the robustness runs: explicit post window; trend 'b8' (B-8..B not in C) or
    'last9' (the last 9 non-C quarters up to B; rob-pre-ab257, design-r2 D10)."""
    fit = [q for q in range(fit_start, B + 1) if q not in COVID]
    if trend == "b8":
        tr = [q for q in range(B - 8, B + 1) if q not in COVID]
    elif trend == "last9":
        tr = [q for q in range(FIT_START, B + 1) if q not in COVID][-9:]
    else:
        raise ValueError(trend)
    win = {"pooled": list(pooled)}
    if extra:
        win.update({k: list(v) for k, v in extra.items()})
    return Windows(B=B, fit=fit, trend=tr, win=win, note=note)


# --------------------------------------------------------------------------- seasonal adjustment

def seasonal_factors(y, qi):
    """Fixed seasonal factors s_q from 2014Q1-2019Q4 (design.method SEASONAL ADJUSTMENT).

    y: array (..., T) on the consecutive quarter grid qi. m_t = (0.5 y_{t-2} + y_{t-1} + y_t +
    y_{t+1} + 0.5 y_{t+2}) / 4 for t = 2014Q3..2019Q2; s_q = mean of y_t - m_t over the five
    quarters of type q, minus the mean of the four. Returns (..., 4), index 0 = Q1.
    """
    qi = np.asarray(qi)
    p0 = int(np.flatnonzero(qi == SA_FIRST)[0])
    if p0 + 24 > len(qi) or qi[p0 + 23] != SA_LAST:
        raise ValueError("the grid must contain 2014Q1-2019Q4 consecutively")
    seg = np.asarray(y, float)[..., p0:p0 + 24]
    if not np.all(np.isfinite(seg)):
        raise ValueError("non-finite value inside the seasonal-factor years 2014-2019")
    m = (0.5 * seg[..., 0:20] + seg[..., 1:21] + seg[..., 2:22] + seg[..., 3:23]
         + 0.5 * seg[..., 4:24]) / 4.0
    d = seg[..., 2:22] - m                       # t = 2014Q3..2019Q2, five of each type
    types = qi[p0 + 2:p0 + 22] % 4
    s = np.stack([d[..., types == k].mean(axis=-1) for k in range(4)], axis=-1)
    return s - s.mean(axis=-1, keepdims=True)


def seasonal_adjust(y, qi):
    """y_t - s_q(t) for all t on the grid."""
    s = seasonal_factors(y, qi)
    return np.asarray(y, float) - s[..., np.asarray(qi) % 4]


# --------------------------------------------------------------------------- data

class Panel:
    """State x quarter panel (data/derived/state_panel*.csv, or a synthetic frame with the same
    columns). Outcomes (design.method OUTCOMES), seasonally adjusted after aggregation:
      E: SA ln(employment), P: SA ln(employment) - ln(pop), W: SA ln(avg weekly wage);
      AGG aggregates: summed employment / population / wages, then logged, then SA;
      AGG wage: ln(sum total_qtrly_wages / (13 * sum mean employment)).
    """

    def __init__(self, df):
        df = df.copy()
        df["state_fips"] = df["state_fips"].astype(str).str.zfill(2)
        df["qi"] = 4 * df["year"].astype(int) + df["qtr"].astype(int) - 1
        self.units = sorted(df["state_fips"].unique())
        lo, hi = int(df["qi"].min()), int(df["qi"].max())
        self.qi = np.arange(lo, hi + 1)
        if len(df) != len(self.units) * len(self.qi) or df.duplicated(["state_fips", "qi"]).any():
            raise ValueError("panel is not balanced on a consecutive quarter grid")
        df = df.sort_values(["state_fips", "qi"])
        self.row = {u: i for i, u in enumerate(self.units)}
        shape = (len(self.units), len(self.qi))

        def mat(col):
            return df[col].to_numpy(float).reshape(shape) if col in df.columns else None

        self.emp = {ind: mat(f"emp_{ind}") for ind in INDUSTRIES if f"emp_{ind}" in df.columns}
        self.wages = mat("wages_722513")
        self.aww = mat("aww_722513")
        self.pop = mat("pop")
        self.sep = mat("sep_722513")
        self.sup7225 = mat("sup_7225")
        self.abbr = (dict(zip(df["state_fips"], df["state_abbr"].astype(str))) if "state_abbr" in df.columns
                     else {u: u for u in self.units})
        self._cache = {}

    # grid helpers
    def pos(self, q):
        p = int(q) - int(self.qi[0])
        if not 0 <= p < len(self.qi):
            raise IndexError(f"quarter {qlabel(int(q))} is outside the panel")
        return p

    def positions(self, quarters):
        return np.array([self.pos(q) for q in quarters], dtype=int)

    def rows(self, units):
        return [self.row[u] for u in units]

    def pop_at(self, unit, q):
        return float(self.pop[self.row[unit], self.pos(q)])

    # outcomes
    def unit_matrix(self, ind, n):
        """All units' series of outcome n in {E, P, W} for industry ind (rows = self.units)."""
        key = (ind, n)
        if key not in self._cache:
            if n == "W":
                if ind != "722513":
                    raise ValueError("the wage outcome is defined for 722513 only")
                y = seasonal_adjust(np.log(self.aww), self.qi)
            elif n in ("E", "P"):
                y = seasonal_adjust(np.log(self.emp[ind]), self.qi)
                if n == "P":
                    y = y - np.log(self.pop)
            else:
                raise ValueError(n)
            self._cache[key] = y
        return self._cache[key]

    def unit_series(self, ind, n, units):
        return self.unit_matrix(ind, n)[self.rows(units)]

    def aggregate(self, ind, n, units):
        """AGG (CEM): the donor aggregate series, i.e. summed levels, logged, then SA."""
        r = self.rows(units)
        if n == "W":
            y = np.log(self.wages[r].sum(axis=0) / (13.0 * self.emp["722513"][r].sum(axis=0)))
            return seasonal_adjust(y, self.qi)
        y = seasonal_adjust(np.log(self.emp[ind][r].sum(axis=0)), self.qi)
        if n == "P":
            y = y - np.log(self.pop[r].sum(axis=0))
        return y

    def popw(self, ind, n, units, Bpos):
        """POPW (Dube): population-weighted mean of donor log series, weights pop_j at B."""
        r = self.rows(units)
        p = self.pop[r, Bpos]
        return (p / p.sum()) @ self.unit_matrix(ind, n)[r]

    def donor_average(self, ind, n, units, weighting, Bpos):
        if weighting == "AGG":
            return self.aggregate(ind, n, units)
        if weighting == "POPW":
            return self.popw(ind, n, units, Bpos)
        raise ValueError(weighting)


def check_pre_only(df):
    """select.py and level_mde.py: raise if the input holds any quarter after 2019Q4 (0f (v))."""
    qi = 4 * df["year"].astype(int) + df["qtr"].astype(int) - 1
    if (qi > PRE_END).any() or ("quarter" in df.columns
                                and df["quarter"].map(qparse).gt(PRE_END).any()):
        raise ValueError("input contains a quarter after 2019Q4; this script reads data through "
                         "2019Q4 only (design.method SELECTION RULE, LEVEL CHECK)")
    return df


def read_panel_csv(path, pre_only=False, usecols=None):
    df = pd.read_csv(path, dtype={"state_fips": str}, usecols=usecols)
    if pre_only:
        check_pre_only(df)
    return df


# --------------------------------------------------------------------------- simplex weights

SOLVER_LOG = {"solves": 0, "kkt_max": 0.0, "not_converged": 0}
KKT_RESTART = 1e-7
RESTARTS = 3


def kkt_residual(Q, c, w):
    """KKT residual of min w'Qw - 2c'w over the simplex: gradient g = 2(Qw - c), multiplier
    mu = w'g; residual = max_j |min(w_j, g_j - mu)| (0 at the optimum)."""
    g = 2.0 * (Q @ w - c)
    mu = float(w @ g)
    return float(np.max(np.abs(np.minimum(w, g - mu))))


def simplex_ls(A, b, pen=0.0, x0=None):
    """min ||A w - b||^2 + pen ||w||^2 subject to w >= 0, sum w = 1 (design.method: SLSQP,
    simplex constraints, start at uniform weights, ftol 1e-12, maxiter 2000; restarted from its own
    solution, at most RESTARTS times, while the KKT residual exceeds 1e-7).

    The objective is divided by its value scale s^2 (s^2 = b'b, or trace(A'A)/n if b = 0) before
    SLSQP sees it, which leaves the minimiser unchanged and makes ftol and the KKT tolerance
    scale-free (log-employment fits have objectives near 1e-4, the Prop 99 fits near 1e5).
    info['kkt'] is the KKT residual of the scaled problem (check-methods requires <= 1e-6).
    Returns (w, info) with info = {kkt, success, nit, obj (unscaled objective)}."""
    A = np.asarray(A, float)
    b = np.asarray(b, float)
    n = A.shape[1]
    s2 = float(b @ b)
    if not s2 > 0:
        s2 = float(np.sum(A * A)) / n if np.sum(A * A) > 0 else 1.0
    Q = (A.T @ A + pen * np.eye(n)) / s2
    c = (A.T @ b) / s2
    bb = float(b @ b) / s2

    def f(w):
        return float(w @ Q @ w - 2.0 * c @ w + bb)

    if n == 1:
        w = np.ones(1)
        return w, {"kkt": 0.0, "success": True, "nit": 0, "obj": f(w) * s2}

    def jac(w):
        return 2.0 * (Q @ w - c)

    def slsqp(start):
        res = minimize(f, start, jac=jac, method="SLSQP", bounds=[(0.0, 1.0)] * n,
                       constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1.0,
                                     "jac": lambda w: np.ones_like(w)}],
                       options={"ftol": 1e-12, "maxiter": 2000})
        w = np.clip(res.x, 0.0, None)
        return w / w.sum(), res

    w, res = slsqp(np.full(n, 1.0 / n) if x0 is None else np.asarray(x0, float))
    kkt = kkt_residual(Q, c, w)
    nit, success, restarts = int(res.nit), bool(res.success), 0
    # SLSQP's ftol bounds the objective, not the gradient: near the optimum its gradient accuracy
    # is about sqrt(ftol) = 1e-6. Restart SLSQP (same options) from its own solution while the KKT
    # residual exceeds 1e-7, at most RESTARTS times, keeping a restart only if it lowers the residual.
    while kkt > KKT_RESTART and restarts < RESTARTS:
        w2, res2 = slsqp(w)
        restarts += 1
        k2 = kkt_residual(Q, c, w2)
        nit += int(res2.nit)
        if k2 < kkt and f(w2) <= f(w) + 1e-15:
            w, kkt, success = w2, k2, bool(res2.success)
        else:
            break
    SOLVER_LOG["solves"] += 1
    SOLVER_LOG["kkt_max"] = max(SOLVER_LOG["kkt_max"], kkt)
    SOLVER_LOG["not_converged"] += int(not success)
    return w, {"kkt": kkt, "success": success, "nit": nit, "restarts": restarts, "obj": f(w) * s2}


# --------------------------------------------------------------------------- estimators

def dd_taus(g, Bp, wins):
    """DD: tau = mean_{t in window} g_t - g_B (g = treated minus donor average)."""
    return {k: float(np.mean(g[p]) - g[Bp]) for k, p in wins.items()}


def ddt_slope(g, tpos):
    """OLS slope of g_t on t over the trend positions (calendar quarters)."""
    t = np.asarray(tpos, float)
    x = t - t.mean()
    yy = g[np.asarray(tpos, int)]
    return float(x @ (yy - yy.mean()) / (x @ x))


def ddt_endpoint_slope(g, Bp, lag=8):
    """S1 (CEM): endpoint trend (g_B - g_{B-8}) / 8."""
    return float((g[Bp] - g[Bp - lag]) / lag)


def ddt_taus(g, Bp, slope, wins):
    """DDT: tau = mean_{t in window} [g_t - g_B - b (t - B)]."""
    return {k: float(np.mean(g[p] - g[Bp] - slope * (np.asarray(p) - Bp))) for k, p in wins.items()}


def sc_fit(y, Y, fp, wins, w=None):
    """Demeaned synthetic control (Doudchenko-Imbens; Ferman-Pinto 2021 eq. 8): simplex w
    minimising sum_F [(y_t - ybar_F) - sum_j w_j (Y_jt - Ybar_jF)]^2, no penalty; tau = mean over
    the window of the same demeaned gap. y: (T,), Y: (J, T), fp: fit positions."""
    fp = np.asarray(fp, int)
    yb = y[fp].mean()
    Yb = Y[:, fp].mean(axis=1)
    info = None
    if w is None:
        w, info = simplex_ls((Y[:, fp] - Yb[:, None]).T, y[fp] - yb)
    gap = (y - yb) - w @ (Y - Yb[:, None])
    taus = {k: float(np.mean(gap[np.asarray(p, int)])) for k, p in wins.items()}
    return taus, {"w": w, "gap": gap, "solve": info}


def sigma_hat(Y, fp):
    """Arkhangelsky et al. (2021) eq. (2.2): sigma_hat^2 = sum over donors j and consecutive
    calendar-quarter pairs (t, t+1) both in F of (Delta_jt - Delta_bar)^2 / (J x number of pairs)."""
    fs = set(int(p) for p in fp)
    pairs = np.array([p for p in sorted(fs) if p + 1 in fs], dtype=int)
    D = Y[:, pairs + 1] - Y[:, pairs]
    return float(np.sqrt(np.sum((D - D.mean()) ** 2) / D.size))


def sdid_fit(y, Y, fp, wins, tpost=None, omega=None, lambdas=None, zeta=None,
             unit_intercept=True, time_weights=True, n_tr=1):
    """Synthetic DID (Arkhangelsky et al. 2021, Algorithm 1, no sparsification).

    Unit weights (omega0, omega in the simplex) minimise sum_F (omega0 + omega'Y_t - y_t)^2 +
    zeta^2 |F| ||omega||^2, zeta = (n_tr * tpost)^(1/4) sigma_hat. Time weights per window
    (lambda0, lambda in the simplex) minimise sum_j (lambda0 + lambda'Y_j,F - mean_window Y_j)^2 +
    (1e-6 sigma_hat)^2 J ||lambda||^2. Intercepts are unpenalised and profiled out exactly
    (centring). tau = (mean_window y - lambda'y_F) - omega'(mean_window Y - Y_F lambda).
    omega is fitted once (with tpost = length of the pooled window unless given) and reused for
    every window; lambda is refitted per window unless lambdas are given.
    With time_weights=False tau = mean_window (y - omega'Y) (the paper's SC when also
    unit_intercept=False and zeta = 1e-6 sigma_hat).
    """
    fp = np.asarray(fp, int)
    J = Y.shape[0]
    sig = sigma_hat(Y, fp)
    if tpost is None:
        tpost = len(wins["pooled"])
    if zeta is None:
        zeta = (n_tr * tpost) ** 0.25 * sig
    solves = []
    if omega is None:
        A = Y[:, fp].T
        bvec = y[fp]
        if unit_intercept:
            A = A - A.mean(axis=0)
            bvec = bvec - bvec.mean()
        omega, info = simplex_ls(A, bvec, pen=zeta ** 2 * len(fp))
        solves.append(info)
    lam_out, taus = {}, {}
    for k, p in wins.items():
        p = np.asarray(p, int)
        if time_weights:
            if lambdas is not None and k in lambdas:
                lam = lambdas[k]
            else:
                A = Y[:, fp]
                bvec = Y[:, p].mean(axis=1)
                A = A - A.mean(axis=0)
                bvec = bvec - bvec.mean()
                lam, info = simplex_ls(A, bvec, pen=(1e-6 * sig) ** 2 * J)
                solves.append(info)
            lam_out[k] = lam
            taus[k] = float((y[p].mean() - lam @ y[fp]) - omega @ (Y[:, p].mean(axis=1) - Y[:, fp] @ lam))
        else:
            taus[k] = float(np.mean(y[p] - omega @ Y[:, p]))
    gap = None
    if time_weights and "pooled" in lam_out:
        lam = lam_out["pooled"]
        gap = (y - lam @ y[fp]) - omega @ (Y - (Y[:, fp] @ lam)[:, None])
    return taus, {"omega": omega, "lambdas": lam_out, "zeta": zeta, "sigma": sig, "gap": gap,
                  "solves": solves}


# --------------------------------------------------------------------------- candidates

def _candidate_ids():
    ids = []
    for e in ["DD", "DDT"]:
        for w in ["AGG", "POPW"]:
            for n in ["E", "P"]:
                for pool in ["D20", "R50"]:
                    ids.append(f"{e}-{w}-{n}-{pool}")
    for e in ["SC", "SDID"]:
        for n in ["E", "P"]:
            for pool in ["D20", "R50"]:
                ids.append(f"{e}-{n}-{pool}")
    return ids


CANDIDATES = _candidate_ids()   # 24, in the design's order (also the last tie-break)


@dataclass(frozen=True)
class Spec:
    """est in {DD, DDT, DDTE (S1 endpoint trend), SC, SDID}; weighting AGG/POPW for DD-type;
    norm in {E, P, W}; industry in INDUSTRIES; fit_start for the fit window."""
    est: str
    weighting: object = None
    norm: str = "E"
    industry: str = "722513"
    fit_start: int = FIT_START

    def with_(self, **kw):
        d = dict(est=self.est, weighting=self.weighting, norm=self.norm, industry=self.industry,
                 fit_start=self.fit_start)
        d.update(kw)
        return Spec(**d)


def parse_candidate(cid):
    """'DDT-POPW-P-D20' -> (Spec, 'D20'); 'SDID-E-R50' -> (Spec, 'R50')."""
    parts = cid.split("-")
    if parts[0] in ("DD", "DDT"):
        return Spec(est=parts[0], weighting=parts[1], norm=parts[2]), parts[3]
    if parts[0] in ("SC", "SDID"):
        return Spec(est=parts[0], norm=parts[1]), parts[2]
    raise ValueError(cid)


def other_pool(pool):
    return "R50" if pool == "D20" else "D20"


def _check_finite(arr, pos, what):
    if not np.all(np.isfinite(arr[..., pos])):
        raise ValueError(f"missing value in {what} at a quarter the estimate uses")


def estimate(panel, spec, win, treated, donors, reuse=None):
    """Estimate of spec with `treated` against `donors` over every window in win.win.

    Returns (taus, fit): taus = {window: tau}; fit holds the gap path ('gap', over the whole
    grid), and the fitted weights (SC 'w'; SDID 'omega', 'lambdas') or the DDT slope.
    reuse: the fit of another outcome whose weights are applied unchanged (SC w; SDID omega and
    the per-window lambdas); DD and DDT have no fitted weights, so reuse is ignored for them.
    """
    Bp = panel.pos(win.B)
    fp = panel.positions(win.fit)
    wins = {k: panel.positions(v) for k, v in win.win.items()}
    used = np.unique(np.concatenate([fp, [Bp]] + list(wins.values())))
    if spec.est in ("DD", "DDT", "DDTE"):
        y = panel.unit_series(spec.industry, spec.norm, [treated])[0]
        ybar = panel.donor_average(spec.industry, spec.norm, donors, spec.weighting, Bp)
        g = y - ybar
        t = np.arange(len(g))
        if spec.est == "DD":
            _check_finite(g, used, "g")
            return dd_taus(g, Bp, wins), {"gap": g - g[Bp], "slope": 0.0}
        if spec.est == "DDT":
            tp = panel.positions(win.trend)
            _check_finite(g, np.unique(np.concatenate([used, tp])), "g")
            b = ddt_slope(g, tp)
        else:
            _check_finite(g, np.unique(np.concatenate([used, [Bp - win.endpoint_lag]])), "g")
            b = ddt_endpoint_slope(g, Bp, win.endpoint_lag)
        return ddt_taus(g, Bp, b, wins), {"gap": g - g[Bp] - b * (t - Bp), "slope": b}
    y = panel.unit_series(spec.industry, spec.norm, [treated])[0]
    Y = panel.unit_series(spec.industry, spec.norm, donors)
    _check_finite(y, used, "treated series")
    _check_finite(Y, used, "donor series")
    if spec.est == "SC":
        return sc_fit(y, Y, fp, wins, w=None if reuse is None else reuse["w"])
    if spec.est == "SDID":
        if reuse is None:
            return sdid_fit(y, Y, fp, wins, tpost=win.tpost)
        return sdid_fit(y, Y, fp, wins, tpost=win.tpost, omega=reuse["omega"],
                        lambdas=reuse["lambdas"])
    raise ValueError(spec.est)


def estimate_reused(panel, spec_emp, win, treated, donors):
    """Wage ATT with the employment fit reused (design.method DECISIONS; S2): fit spec_emp on
    employment, then apply its weights to log weekly wage. Returns (taus_emp, taus_wage_reused)."""
    taus_e, fit_e = estimate(panel, spec_emp, win, treated, donors)
    taus_w, _ = estimate(panel, spec_emp.with_(norm="W"), win, treated, donors, reuse=fit_e)
    return taus_e, taus_w


# --------------------------------------------------------------------------- statistic functions

def make_stat_fn(panel, spec, win, keys=None, diff=False):
    """stat_fn(u, donors) for placebo_inference: the taus of spec over win's windows (or `keys`),
    plus 'diff' = tau_y2 - tau_y1 (H3) when diff=True."""
    def fn(u, donors):
        taus, _ = estimate(panel, spec, win, u, donors)
        out = dict(taus) if keys is None else {k: taus[k] for k in keys}
        if diff:
            out["diff"] = taus["y2"] - taus["y1"]
        return out
    return fn


def make_reuse_stat_fn(panel, spec_emp, win, keys=("pooled",)):
    """stat_fn returning the employment taus ('<k>') and the wage taus with the employment fit
    reused ('wr_<k>'), each unit with its own employment fit (S2)."""
    def fn(u, donors):
        te, tw = estimate_reused(panel, spec_emp, win, u, donors)
        out = {k: te[k] for k in keys}
        out.update({f"wr_{k}": tw[k] for k in keys})
        return out
    return fn


def make_gap_stat_fn(panel, spec, win):
    """stat_fn returning the gap at every grid position (event path): 'g<position>'."""
    def fn(u, donors):
        _, fit = estimate(panel, spec, win, u, donors)
        return {f"g{p}": float(v) for p, v in enumerate(fit["gap"])}
    return fn


def pop_at_base(panel, win):
    return lambda u: panel.pop_at(u, win.B)


# --------------------------------------------------------------------------- inference

def se_from_placebos(tau_j, pop_j, pop_u):
    """SE_s = sqrt(mean tau_j^2 pop_j / pop_u) (Dube's Ferman-Pinto scaling), SE_n =
    sqrt(mean tau_j^2), SE = max(SE_s, SE_n); Ferman-Pinto step 3 (diagnostic only): OLS of tau_j^2
    on 1 and 1/pop_j, SE_FP = sqrt(max(0, A_hat + B_hat / pop_u))."""
    tau_j = np.asarray(tau_j, float)
    pop_j = np.asarray(pop_j, float)
    se_s = float(np.sqrt(np.mean(tau_j ** 2 * pop_j / pop_u)))
    se_n = float(np.sqrt(np.mean(tau_j ** 2)))
    X = np.column_stack([np.ones_like(pop_j), pop_u / pop_j])      # 1/pop_j scaled by pop_u
    coef, *_ = np.linalg.lstsq(X, tau_j ** 2, rcond=None)
    a_hat = float(coef[0])
    b_hat = float(coef[1] * pop_u)                                  # back to the 1/pop_j scale
    se_fp = float(np.sqrt(max(0.0, a_hat + b_hat / pop_u)))
    return {"se": max(se_s, se_n), "se_s": se_s, "se_n": se_n, "fp_a": a_hat, "fp_b": b_hat,
            "fp_se": se_fp}


def placebo_inference(stat_fn, treated, donors, pop_of):
    """design.method INFERENCE. stat_fn(u, donors_u) -> {statistic: value}. The treated unit's
    statistics use `donors` (J); placebo j is treated with the other J-1 donors (the treated unit
    excluded). pop_of(u) = population at B. Returns {statistic: dict(tau, se, se_s, se_n, J,
    fp_a, fp_b, fp_se, placebos (array, donor order))} and the placebo dicts."""
    tau = stat_fn(treated, list(donors))
    plc = {j: stat_fn(j, [d for d in donors if d != j]) for j in donors}
    pu = pop_of(treated)
    pj = np.array([pop_of(j) for j in donors])
    out = {}
    for k, v in tau.items():
        tj = np.array([plc[j][k] for j in donors])
        r = se_from_placebos(tj, pj, pu)
        r.update({"tau": float(v), "J": len(donors), "placebos": tj})
        out[k] = r
    return out


# --------------------------------------------------------------------------- critical values

def t_quantile(J, p):
    return float(stats.t.ppf(p, J))


def l_quantiles(T_L):
    """Empirical quantiles of the decision set's T values: 0.95 and 0.975 with numpy method
    'higher', 0.025 and 0.05 with method 'lower' (design.method CRITICAL VALUES)."""
    T_L = np.asarray(T_L, float)
    return {"q95": float(np.quantile(T_L, 0.95, method="higher")),
            "q975": float(np.quantile(T_L, 0.975, method="higher")),
            "q05": float(np.quantile(T_L, 0.05, method="lower")),
            "q025": float(np.quantile(T_L, 0.025, method="lower"))}


def satterthwaite_df(s2):
    """(sum_j s_j^2)^2 / sum_j s_j^4: the Satterthwaite df of SE_n = sqrt(mean tau_j^2) when the
    placebo variances s_j^2 differ (design.method DEGREES OF FREEDOM)."""
    s2 = np.asarray(s2, float)
    return float(s2.sum() ** 2 / np.sum(s2 ** 2))


def nu_from_s2(s2, J):
    """nu_hat (Satterthwaite df of the given s_j^2) and nu = min(J, nu_hat)."""
    nu_hat = satterthwaite_df(s2)
    return nu_hat, float(min(J, nu_hat))


def nu_for_donors(m, stat, donors):
    """nu_hat and nu of statistic `stat` over a run's own donor set, from the per-donor s_j^2
    level-mde writes (s2_<stat>_<fips> = mean over the six pseudo-dates of tau_j(B')^2 in
    California's level-check test); nu is capped at the run's own J = len(donors)."""
    s2 = [float(m[f"s2_{stat}_{u}"]) for u in donors]
    return nu_from_s2(s2, len(donors))


def critical_values(df, lq=None):
    """c_hi(p) = max(t_{nu,p}, L quantile), c_lo(p) = min(-t_{nu,1-p}, L quantile), with t at
    df = nu (scipy.stats.t accepts non-integer df). lq=None: the t quantiles only."""
    c = {"hi95": t_quantile(df, 0.95), "hi975": t_quantile(df, 0.975),
         "lo05": -t_quantile(df, 0.95), "lo025": -t_quantile(df, 0.975)}
    if lq is not None:
        c = {"hi95": max(c["hi95"], lq["q95"]), "hi975": max(c["hi975"], lq["q975"]),
             "lo05": min(c["lo05"], lq["q05"]), "lo025": min(c["lo025"], lq["q025"])}
    return c


def lq_from_metrics(m, stat):
    """The L quantiles of statistic `stat` as level-mde writes them (Lq_<stat>_q95 ...)."""
    return {k: float(m[f"Lq_{stat}_{k}"]) for k in ("q95", "q975", "q05", "q025")}


def intervals(tau, se, c):
    """95% CI [tau - c_hi(0.975) SE, tau - c_lo(0.025) SE]; 90% CI [tau - c_hi(0.95) SE,
    tau - c_lo(0.05) SE]."""
    return {"lo95": tau - c["hi975"] * se, "hi95": tau - c["lo025"] * se,
            "lo90": tau - c["hi95"] * se, "hi90": tau - c["lo05"] * se}


def one_sided_reject(tau, se, c):
    """H1: reject if tau / SE > c_hi(0.95)."""
    return int(tau / se > c["hi95"])


def t_pvalues(tau, se, df):
    """For information only: one-sided (upper) and two-sided p-values from t at df (= nu)."""
    T = tau / se
    return {"p_upper": float(stats.t.sf(T, df)), "p_two": float(2 * stats.t.sf(abs(T), df))}


# --------------------------------------------------------------------------- level check

def level_check_units(pool, ca=CA):
    """Units treated in the level check and their donor sets: California with the pool (J
    donors); every other pool unit u with D_u = pool minus u (J-1), California excluded both from
    its donors and from its placebos (design-r2 D8)."""
    out = [(ca, list(pool))]
    for u in pool:
        out.append((u, [d for d in pool if d != u]))
    return out


def population_terciles(units, pops):
    """Terciles of the J+1 units by population (1 = smallest); np.array_split of the ascending
    order (sizes differ by at most one)."""
    order = np.argsort(np.asarray(pops, float), kind="stable")
    terc = {}
    for k, chunk in enumerate(np.array_split(order, 3), start=1):
        for i in chunk:
            terc[units[i]] = k
    return terc


def decision_set_l(panel, q, n=10, d20=D20):
    """The ten most populous D20 states at quarter q (design.method DECISION SET L)."""
    pops = [(panel.pop_at(u, q), u) for u in d20]
    return [u for _, u in sorted(pops, reverse=True)[:n]]


def rejection_rates(T, J_ref):
    """Rates of T > t_{0.95}, T < -t_{0.95} and |T| > t_{0.975}, with t at each test's own df
    (arrays T and J_ref of the same length)."""
    T = np.asarray(T, float)
    J_ref = np.asarray(J_ref, float)
    t95 = stats.t.ppf(0.95, J_ref)
    t975 = stats.t.ppf(0.975, J_ref)
    return {"up": float(np.mean(T > t95)), "lo": float(np.mean(T < -t95)),
            "two": float(np.mean(np.abs(T) > t975)), "n": int(len(T))}


def binomial_band(n_eff, p=0.05, z=1.96):
    """0.05 +/- z sqrt(p(1-p)/n_eff): the band the level rates are read against."""
    h = z * np.sqrt(p * (1 - p) / n_eff)
    return float(p - h), float(p + h)


# --------------------------------------------------------------------------- decisions

def h2_sign(L, U):
    if U < 0:
        return "negative"
    if L > 0:
        return "positive"
    return "sign undetermined"


def h2_size(l, u, b=B_SIZE):
    if -b < l and u < b:
        return "smaller than b"
    if u < -b or l > b:
        return "at least b"
    return "size undetermined"


H2_CELLS = {
    ("negative", "at least b"): "decline of at least 2%",
    ("negative", "smaller than b"): "decline smaller than 2%",
    ("negative", "size undetermined"): "decline, size not distinguishable from 2%",
    ("sign undetermined", "smaller than b"): "no effect as large as 2%",
    ("sign undetermined", "at least b"): "inconclusive",
    ("sign undetermined", "size undetermined"): "inconclusive",
    ("positive", "at least b"): "increase of at least 2%",
    ("positive", "smaller than b"): "increase smaller than 2%",
    ("positive", "size undetermined"): "increase, size not distinguishable from 2%",
}
CELL_KEYS = {("negative", "at least b"): "neg_atleast", ("negative", "smaller than b"): "neg_smaller",
             ("negative", "size undetermined"): "neg_undet",
             ("sign undetermined", "smaller than b"): "und_smaller",
             ("sign undetermined", "at least b"): "und_atleast",
             ("sign undetermined", "size undetermined"): "und_undet",
             ("positive", "at least b"): "pos_atleast", ("positive", "smaller than b"): "pos_smaller",
             ("positive", "size undetermined"): "pos_undet"}


def h2_label(ci, b=B_SIZE):
    """The nine-cell H2 rule (hypotheses[1]): sign from the 95% CI, size from the 90% CI."""
    sign = h2_sign(ci["lo95"], ci["hi95"])
    size = h2_size(ci["lo90"], ci["hi90"], b)
    return sign, size, H2_CELLS[(sign, size)]


def label_probabilities(tau, se, c, df, b=B_SIZE):
    """P(each of the nine H2 cells) when tau_hat = tau + se T, T ~ t_nu (df = nu), and the CIs use
    se and c (closed form from the t_nu cdf; design.method MDE AND POWER)."""
    bps = sorted({c["lo025"] * se, c["hi975"] * se, -b + c["hi95"] * se, b + c["lo05"] * se,
                  -b + c["lo05"] * se, b + c["hi95"] * se})
    edges = [-np.inf] + bps + [np.inf]
    probs = {k: 0.0 for k in CELL_KEYS.values()}
    for lo, hi in zip(edges[:-1], edges[1:]):
        if np.isinf(lo):
            mid = hi - 1.0
        elif np.isinf(hi):
            mid = lo + 1.0
        else:
            mid = 0.5 * (lo + hi)
        ci = intervals(mid, se, c)
        cell = (h2_sign(ci["lo95"], ci["hi95"]), h2_size(ci["lo90"], ci["hi90"], b))
        mass = stats.t.cdf((hi - tau) / se, df) - stats.t.cdf((lo - tau) / se, df)
        probs[CELL_KEYS[cell]] += float(mass)
    return probs


def h3_label(lo95, hi95):
    if hi95 < 0:
        return "larger decline in year two"
    if lo95 > 0:
        return "smaller decline in year two"
    return "no detectable change"


def mde(c_hi, df, se_pre):
    """(c_hi + t_{nu,0.80}) SE_pre (df = nu)."""
    return float((c_hi + t_quantile(df, 0.80)) * se_pre)


def h90(c, se_pre):
    """Half-width of the 90% CI: max(c_hi(0.95), -c_lo(0.05)) SE_pre."""
    return float(max(c["hi95"], -c["lo05"]) * se_pre)


def pct(tau):
    """100 (exp(tau) - 1)."""
    return float(100.0 * np.expm1(tau))


# --------------------------------------------------------------------------- run helpers

def flatten_inference(prefix, r, c=None, nu=None):
    """Flat metrics for one statistic's inference result (and its CIs when c and nu are given)."""
    m = {f"{prefix}_att": r["tau"], f"{prefix}_se": r["se"], f"{prefix}_se_s": r["se_s"],
         f"{prefix}_se_n": r["se_n"], f"{prefix}_J": r["J"], f"{prefix}_fp_a": r["fp_a"],
         f"{prefix}_fp_b": r["fp_b"], f"{prefix}_fp_se": r["fp_se"]}
    if c is not None:
        for k, v in intervals(r["tau"], r["se"], c).items():
            m[f"{prefix}_{k}"] = float(v)
        m.update({f"{prefix}_c_{k}": float(v) for k, v in c.items()})
        p = t_pvalues(r["tau"], r["se"], nu)
        m[f"{prefix}_p_upper_tnu"] = p["p_upper"]
        m[f"{prefix}_p_two_tnu"] = p["p_two"]
    return m


def write_json(path, obj):
    import json
    from pathlib import Path
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    def conv(v):
        if isinstance(v, (np.floating,)):
            return float(v)
        if isinstance(v, (np.integer,)):
            return int(v)
        return v

    Path(path).write_text(json.dumps({k: conv(v) for k, v in obj.items()}, indent=1, sort_keys=False) + "\n")


# --------------------------------------------------------------------------- post-period run context

PANEL_FULL = "data/derived/state_panel.csv"
SELECT_METRICS = "runs/select/metrics.json"
LEVEL_METRICS = "runs/level-mde/metrics.json"


def load_run_context(panel_path=PANEL_FULL, select_path=SELECT_METRICS, level_path=LEVEL_METRICS):
    """The full panel, the selected candidate (from runs/select) and the level-mde metrics.
    Nothing is hard-coded: the candidate and the inference values come from those two files."""
    import json
    from pathlib import Path
    m_sel = json.loads(Path(select_path).read_text())
    m_lvl = json.loads(Path(level_path).read_text())
    selected = m_sel["selected"]
    if m_lvl.get("selected") != selected:
        raise ValueError("runs/level-mde was computed for a different candidate than runs/select")
    spec, pool = parse_candidate(selected)
    panel = Panel(read_panel_csv(panel_path))
    return panel, selected, spec, pool, m_lvl


def crit_for(m_lvl, stat, donors):
    """Critical values of a run: t at its own nu (nu_hat over its own donors, capped at its own J)
    and the L quantiles of level-mde statistic `stat`. Returns (c, nu_hat, nu)."""
    nu_hat, nu = nu_for_donors(m_lvl, stat, donors)
    return critical_values(nu, lq_from_metrics(m_lvl, stat)), nu_hat, nu


def solver_metrics():
    return {"solver_solves": SOLVER_LOG["solves"], "solver_kkt_max": SOLVER_LOG["kkt_max"],
            "solver_not_converged": SOLVER_LOG["not_converged"]}
