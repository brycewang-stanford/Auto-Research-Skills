"""Run sens-imbens: Imbens (2003) sensitivity analysis for re78 (plan.json design.method.sensitivity).

Adopted from gallery/ss-null-effect/code/sens_imbens.py (716b6c3) with only DEV-16: B(X) is
the 14-term basis; the benchmark groups are re-listed for these covariates (8 groups); the
targets t_M and t_E are not computed (they need the H1b margin, which does not exist here);
t_0 and the reading rule are kept.

Model: U ~ Bernoulli(0.5), independent of X;
  logit P(treat = 1 | X, U) = gamma'Z + alpha U,   Z = [1, B(X) standardized on the full sample];
  re78 = tau treat + beta'Z + delta U + e,  e ~ N(0, sigma^2); constant treatment effect.
Fitted for fixed (alpha, delta) by generalized EM: E-step posterior q_i = P(U = 1 | D, Y, X);
M-step one Newton step for gamma, least squares of (Y - delta q) on [treat, Z] for (tau, beta),
sigma^2 = mean[(Y - delta q - W b)^2 + delta^2 q (1 - q)]; at most 200 iterations; stop when
the observed-data log-likelihood changes by less than 1e-8 x |log-likelihood|.
Starting values: the U-free fits (unpenalized logit of treat on Z; OLS of re78 on [treat, Z]),
with the intercepts shifted by -alpha/2 and -delta/2 (E[U] = 0.5).

Strength of U: R2_D(alpha) = (alpha^2/4) / (alpha^2/4 + pi^2/3);
  R2_Y(delta) = (delta^2/4) / sigma0^2 (capped at 1), sigma0^2 = RSS/n of the OLS of re78 on
  treat and B(X); alpha = (2 pi / sqrt 3) sqrt(R2_D / (1 - R2_D)), delta = +/- 2 sigma0 sqrt(R2_Y).
Grid: R2_D, R2_Y in {0, .01, .02, .05, .10, .15, .20, .30}, delta of both signs (128 points);
diagonal R2_D = R2_Y = R2 in {.0025, .005, .01, .02, .03, .05, .075, .10, .15, .20, .30},
both signs (22 points). bias = tau(alpha, delta) - tau(0, 0), applied additively to the AIPW
estimate (an approximation, stated as such). tau(0, 0) equals the OLS coefficient of
rob-estimators (a) (tau00_minus_ols reports the difference).
Target (from runs/main-aipw/metrics.json): t_0 = min(|lo95|, |hi95|), the shift that moves the
nearer 95% bound to zero, i.e. flips the H1 decision.
R2*_0: smallest diagonal R2 with max over signs of |bias| >= t_0, linearly interpolated between
consecutive diagonal points, the diagonal starting at R2 = 0 (bias 0); if none, 0.30 with
out_of_grid = true (reported as '> 0.30').
Benchmarks (groups of B(X) terms dropped together): age {age, age_sq}; educ {educ, educ_sq};
black; hisp; married; nodegree; earn74 {re74, re74_sq, u74}; earn75 {re75, re75_sq, u75}.
R2_Y(G) = (RSS_-G - RSS) / RSS_-G (OLS of re78 on treat and B(X) with and without G);
R2_D(G) = (V - V_-G) / (V - V_-G + pi^2/3), floored at 0, with V the sample variance (ddof 1)
of the fitted index of an unpenalized logit of treat on B(X). The model is fitted at each
group's (R2_D(G), R2_Y(G)), both signs (16 points; 166 in all); robust to G iff |bias| < t_0
for both signs. Strongest robust group = largest max-|bias| among robust groups; weakest
non-robust group = smallest among non-robust groups; the earn75 result is always reported.
The earn74 benchmark carries the F2 caveat (re74 measured over different periods).
Convergence (code-r1 F2): the converged flag of each unpenalized logit (EM start gamma0, full
index V, and V_-G for every group) is written, with their count of failures
(n_logits_nonconverged), next to the EM non-convergence count; no rule depends on them.

Run from the workspace root:  .venv/bin/python -I code/sens_imbens.py
"""

import math
import sys
from pathlib import Path

import numpy as np
import statsmodels.api as sm
from scipy.special import expit, log_expit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/sens-imbens/metrics.json")
GRID = [0.0, 0.01, 0.02, 0.05, 0.10, 0.15, 0.20, 0.30]
DIAG = [0.0025, 0.005, 0.01, 0.02, 0.03, 0.05, 0.075, 0.10, 0.15, 0.20, 0.30]
EM_MAX_ITER = 200
EM_TOL = 1e-8
GROUPS = {
    "age": ["age", "age_sq"], "educ": ["educ", "educ_sq"], "black": ["black"], "hisp": ["hisp"],
    "married": ["married"], "nodegree": ["nodegree"],
    "earn74": ["re74", "re74_sq", "u74"], "earn75": ["re75", "re75_sq", "u75"],
}
PI2_3 = math.pi ** 2 / 3


def alpha_of(r2d: float) -> float:
    return (2 * math.pi / math.sqrt(3)) * math.sqrt(r2d / (1 - r2d))


def r2d_of(alpha: float) -> float:
    return (alpha ** 2 / 4) / (alpha ** 2 / 4 + PI2_3)


def standardize(X: np.ndarray) -> np.ndarray:
    return (X - X.mean(axis=0)) / X.std(axis=0)


class Imbens:
    def __init__(self, d: np.ndarray, y: np.ndarray, Xb: np.ndarray):
        self.d, self.y = d.astype(float), y
        self.Z = np.column_stack([np.ones(len(d)), standardize(Xb)])
        self.W = np.column_stack([self.d, self.Z])
        lg0 = sm.Logit(self.d, self.Z).fit(method="newton", disp=0, maxiter=100, tol=1e-12)
        self.gamma0_converged = bool(lg0.mle_retvals["converged"])
        self.gamma0 = lg0.params
        self.b0 = np.linalg.lstsq(self.W, y, rcond=None)[0]
        self.sigma0_sq = float(np.mean((y - self.W @ self.b0) ** 2))

    def _logf(self, gamma, b, sigma2, alpha, delta):
        eta = self.Z @ gamma
        r = self.y - self.W @ b
        lp0 = np.where(self.d == 1, log_expit(eta), log_expit(-eta))
        lp1 = np.where(self.d == 1, log_expit(eta + alpha), log_expit(-eta - alpha))
        c = -0.5 * np.log(2 * np.pi * sigma2)
        lf0 = lp0 + c - r ** 2 / (2 * sigma2)
        lf1 = lp1 + c - (r - delta) ** 2 / (2 * sigma2)
        return lf0, lf1

    def fit(self, alpha: float, delta: float) -> dict:
        gamma = self.gamma0.copy(); gamma[0] -= alpha / 2
        b = self.b0.copy(); b[1] -= delta / 2
        sigma2 = self.sigma0_sq
        lf0, lf1 = self._logf(gamma, b, sigma2, alpha, delta)
        ll_old = float(np.sum(np.logaddexp(lf0, lf1) + np.log(0.5)))
        converged, it = False, 0
        for it in range(1, EM_MAX_ITER + 1):
            q = expit(lf1 - lf0)  # P(U = 1 | data)
            eta = self.Z @ gamma
            p0, p1 = expit(eta), expit(eta + alpha)
            grad = self.Z.T @ (self.d - (1 - q) * p0 - q * p1)
            h = (1 - q) * p0 * (1 - p0) + q * p1 * (1 - p1)
            gamma = gamma + np.linalg.solve((self.Z * h[:, None]).T @ self.Z, grad)
            b = np.linalg.lstsq(self.W, self.y - delta * q, rcond=None)[0]
            sigma2 = float(np.mean((self.y - delta * q - self.W @ b) ** 2 + delta ** 2 * q * (1 - q)))
            lf0, lf1 = self._logf(gamma, b, sigma2, alpha, delta)
            ll = float(np.sum(np.logaddexp(lf0, lf1) + np.log(0.5)))
            if abs(ll - ll_old) < EM_TOL * abs(ll):
                converged = True
                break
            ll_old = ll
        return {"tau": float(b[0]), "iter": it, "converged": converged}


def r2_star(diag_maxabs: list[float], t: float) -> tuple[float, bool]:
    pts = [(0.0, 0.0)] + list(zip(DIAG, diag_maxabs))
    for (r_prev, b_prev), (r_cur, b_cur) in zip(pts[:-1], pts[1:]):
        if b_cur >= t:
            if b_cur == b_prev:
                return r_cur, False
            return r_prev + (t - b_prev) * (r_cur - r_prev) / (b_cur - b_prev), False
    return 0.30, True


def benchmark_r2(d: np.ndarray, y: np.ndarray, XB, terms: list[str], rss_full: float, V: float):
    """(R2_D(G), R2_Y(G)) for the group of B(X) columns `terms` (method.sensitivity)."""
    keep = [c for c in XB.columns if c not in terms]
    Xg = XB[keep].to_numpy(float)
    fit_g = sm.OLS(y, sm.add_constant(np.column_stack([d, Xg]), has_constant="add")).fit()
    rss_g = float(np.sum((y - fit_g.fittedvalues) ** 2))
    r2y = (rss_g - rss_full) / rss_g
    Zg = sm.add_constant(standardize(Xg), has_constant="add")
    lg_g = sm.Logit(d, Zg).fit(method="newton", disp=0, maxiter=100, tol=1e-12)
    Vg = float(np.var(Zg @ lg_g.params, ddof=1))
    r2d = max(0.0, (V - Vg) / (V - Vg + PI2_3))
    return r2d, r2y, bool(lg_g.mle_retvals["converged"])


def main() -> int:
    df = L.load_covariates()
    L.check_basis_reuse(df)
    main_m = L.read_json(L.MAIN_METRICS)
    y = L.load_re78(df)
    ok = L.admissible(y)
    df, y = df[ok].reset_index(drop=True), y[ok]
    d = df["treat"].to_numpy(int)
    XB = L.basis(df, L.COVS)
    Xb = XB.to_numpy(float)
    if sorted(t for g in GROUPS.values() for t in g) != sorted(XB.columns):
        sys.exit("ERROR: benchmark groups do not partition B(X)")

    model = Imbens(d, y, Xb)
    sigma0 = math.sqrt(model.sigma0_sq)
    base = model.fit(0.0, 0.0)
    tau00 = base["tau"]
    ols = sm.OLS(y, sm.add_constant(np.column_stack([d, Xb]), has_constant="add")).fit()
    met = {"aipw_effect": main_m["effect"], "sigma0": sigma0, "tau00": tau00,
           "tau00_minus_ols": tau00 - float(ols.params[1]), "n": int(len(d)),
           "em_max_iter": EM_MAX_ITER, "em_tol": EM_TOL}
    iters, nonconv = [base["iter"]], int(not base["converged"])

    def bias_at(r2d: float, r2y: float) -> tuple[float, float]:
        nonlocal nonconv
        a = alpha_of(r2d)
        dl = 2 * sigma0 * math.sqrt(min(r2y, 1.0))
        out = []
        for sign in (1, -1):
            f = model.fit(a, sign * dl)
            iters.append(f["iter"]); nonconv += int(not f["converged"])
            out.append(f["tau"] - tau00)
        return out[0], out[1]

    # Grid (128 points).
    for r2d in GRID:
        for r2y in GRID:
            bp, bn = bias_at(r2d, r2y)
            met[f"grid_d{r2d:g}_y{r2y:g}_pos_bias"] = bp
            met[f"grid_d{r2d:g}_y{r2y:g}_neg_bias"] = bn
    # Diagonal (22 points).
    diag_maxabs = []
    for r2 in DIAG:
        bp, bn = bias_at(r2, r2)
        met[f"diag_{r2:g}_pos_bias"] = bp
        met[f"diag_{r2:g}_neg_bias"] = bn
        diag_maxabs.append(max(abs(bp), abs(bn)))

    # Benchmarks (16 points).
    rss_full = float(np.sum((y - ols.fittedvalues) ** 2))
    Zfull = sm.add_constant(standardize(Xb), has_constant="add")
    lg_full = sm.Logit(d, Zfull).fit(method="newton", disp=0, maxiter=100, tol=1e-12)
    V = float(np.var(Zfull @ lg_full.params, ddof=1))
    met["logit_full_converged"] = bool(lg_full.mle_retvals["converged"])
    bench_absmax = {}
    for g, terms in GROUPS.items():
        r2d, r2y, conv_g = benchmark_r2(d, y, XB, terms, rss_full, V)
        met[f"bench_{g}_logit_converged"] = conv_g
        bp, bn = bias_at(r2d, r2y)
        met[f"bench_{g}_r2d"] = r2d
        met[f"bench_{g}_r2y"] = r2y
        met[f"bench_{g}_pos_bias"] = bp
        met[f"bench_{g}_neg_bias"] = bn
        met[f"bench_{g}_abs_bias"] = max(abs(bp), abs(bn))
        bench_absmax[g] = max(abs(bp), abs(bn))

    # Target t_0 and the reading rule.
    lo95, hi95 = main_m["ci_low"], main_m["ci_high"]
    t0 = min(abs(lo95), abs(hi95))
    met["h1_holds_main"] = bool(main_m["h1_holds"])
    r2, oog = r2_star(diag_maxabs, t0)
    met["target_zero"] = t0
    met["r2star_zero"] = r2
    met["r2star_zero_out_of_grid"] = oog
    met["r2star_zero_text"] = "> 0.30" if oog else f"{r2:.4f}"
    robust = {g: bench_absmax[g] < t0 for g in GROUPS}
    for g in GROUPS:
        met[f"robust_zero_{g}"] = bool(robust[g])
    rob = [g for g in GROUPS if robust[g]]
    non = [g for g in GROUPS if not robust[g]]
    met["n_robust_zero"] = len(rob)
    met["strongest_robust_zero"] = max(rob, key=lambda g: bench_absmax[g]) if rob else ""
    met["weakest_nonrobust_zero"] = min(non, key=lambda g: bench_absmax[g]) if non else ""

    met["logit_gamma0_converged"] = model.gamma0_converged
    logit_flags = [met["logit_gamma0_converged"], met["logit_full_converged"]] + [
        met[f"bench_{g}_logit_converged"] for g in GROUPS]
    met["n_logits_nonconverged"] = int(sum(not f for f in logit_flags))
    met["em_points"] = len(iters)
    met["em_max_iterations_used"] = int(max(iters))
    met["em_nonconverged_points"] = nonconv
    L.write_metrics(OUT, met)
    print({k: v for k, v in met.items() if not k.startswith(("grid_", "diag_"))})
    return 0


if __name__ == "__main__":
    sys.exit(main())
