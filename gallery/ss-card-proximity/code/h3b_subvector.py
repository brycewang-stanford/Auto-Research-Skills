"""Run h3b-subvector (plan.json analysis_plan step 5): H3(b), Card's Panel B column 6.

Subvector Anderson-Rubin sets for the coefficient on ed76 with the experience
coefficients g (exp76, exp762) as nuisance parameters; Z = (nearc4, age76, age762),
X = BASE_B + FB (27 columns), n - 30 = 2980.

(1) PRIMARY, heteroskedasticity-robust projection: m(b0) = min over g of HAR(b0, g), HAR
    the HC1 Wald statistic of Z in the OLS of lwage76 - b0 ed76 - W g on (Z, X), computed
    from one stacked regression (ivlib.PanelB); BFGS (gtol 1e-10) from the 2SLS and LIML
    g at b0, the B6 g, and 20 draws N(2SLS g, diag(25 x HC1 SE^2 of the B6 g)) with
    default_rng(4483) (drawn once; the same 20 standard-normal offsets at every b0).
    Accepted iff m(b0) <= 7.814728 (chi-square(3) 95%).
(2) GKMC (homoskedastic): kappa_p(b0) <= 3.841459.
(3) GKM19: kappa_p(b0) <= c(kappa_1(b0)); (3T) Table 3 interpolation (REPORTED), (3Q) the
    eq. (2.12) 95% quantile as ivmodels 0.10.0 computes it (labelled; alongside).
Every set is computed by ivlib.invert_on_grid (design.method SET COMPUTATION).

Checks (failure = run fails): stacked HAR = direct statsmodels HC1 regression at 20
(b0, g) points to 1e-8 relative (b0 = 20 points evenly spaced on [-0.5, 0.8]; g = B6 g +
5 x HC1 SE x the same 20 draws); own kappa_p and kappa_1 = ivmodels at the B6 estimate, 0
and every finite reported bound inside [-1, 1], and at -0.5, 0.5, 1, to 1e-6 relative (with
an absolute floor: |a - b| <= 1e-6 max(|a|, |b|, 1), since kappa_p = 0 at the 2SLS
estimate of this just-identified model); ivmodels' kappa_1 recomputed with our scaling
2980; ivmodels' GKM p-value (kappa_1 scaled by 2981) = ours to 1e-3 where kappa_p > 1e-8.
Differences at reported bounds beyond |b0| = 1 are written as metrics only (kappa_1 grows
like b0^2 there and ivmodels' root solver loses precision). The GKMC
set from the procedure = our closed-form quadric = ivmodels inverse_anderson_rubin_test
('chi2') to 1e-4 in each bound; our (3Q) set = ivmodels inverse_anderson_rubin_test
('gkm') to 1e-4.

Flag h3b_b6_return_positive: the robust projection set is one bounded interval with lower
bound above 0 (the only flag about the return to schooling).

Input: data/derived/card_analysis.csv.
Outputs: runs/h3b-subvector/metrics.json; runs/h3b-subvector/profile.csv with one row per
point of the point list: b0, m (robust profile), kappa_p, kappa_1, c_gkm19 (3T),
c_gkm19q (3Q), acc_rob, acc_gkmc, acc_gkm19, acc_gkm19q (0/1).
Usage: .venv/bin/python code/h3b_subvector.py
"""
from __future__ import annotations

import csv
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "h3b-subvector"
SETS = ("rob", "gkmc", "gkm19", "gkm19q")


def close(p1, p2, tol=1e-4) -> bool:
    """Same number of pieces and every bound within tol (relative beyond |b0| = 1)."""
    if len(p1) != len(p2):
        return False
    for (a1, b1), (a2, b2) in zip(p1, p2):
        for u, v in ((a1, a2), (b1, b2)):
            if math.isinf(u) or math.isinf(v):
                if u != v:
                    return False
            elif abs(u - v) > tol * max(1.0, abs(u)):
                return False
    return True


def compute(df, out_dir: Path | None = None) -> dict:
    b6 = ivlib.fit_spec(df, "B6")
    pb = ivlib.panel_b_from_frame(df, b6)
    ivlib.require(pb.dfd == len(df) - 30, f"dfd = {pb.dfd}")
    m: dict = {"n_sample": len(df), "b6_beta_2sls": b6.coef, "b6_dfd": pb.dfd,
               "b6_g_exp76": float(pb.g_full[0]), "b6_g_exp762": float(pb.g_full[1]),
               "b6_g_exp76_se_hc1": float(pb.g_se[0]), "b6_g_exp762_se_hc1": float(pb.g_se[1])}

    # stacked HAR against the direct regression
    worst = 0.0
    for b0, d in zip(np.linspace(-0.5, 0.8, 20), pb.start_draws):
        g = pb.g_full + 5.0 * pb.g_se * d
        worst = max(worst, ivlib.rel_diff(pb.har(b0, g), pb.har_direct(b0, g)))
    ivlib.require(worst < 1e-8, f"stacked HAR != direct regression ({worst:.2e})")
    m["b6_har_stacked_vs_direct_max_rel"] = worst
    m["b6_rob_m_at_2sls"] = pb.profile(b6.coef)[0]

    # statistics on the point list
    pts = ivlib.grid_points()
    prof = np.array([pb.profile(b)[0] for b in pts])
    kap = np.array([pb.kappas(b) for b in pts])
    c3t = ivlib.c_gkm19_table(kap[:, 1])
    c3q = np.array([ivlib.c_gkm19_quantile(k1) for k1 in kap[:, 1]])

    def acc_rob(b):
        return pb.profile(b)[0] <= ivlib.CHI2_3_95

    def acc_gkmc(b):
        return pb.kappas(b)[0] <= ivlib.CHI2_1_95

    def acc_gkm19(b):
        kp, k1 = pb.kappas(b)
        return kp <= ivlib.c_gkm19_table(k1)

    def acc_gkm19q(b):
        kp, k1 = pb.kappas(b)
        return kp <= ivlib.c_gkm19_quantile(k1)

    acc = {"rob": prof <= ivlib.CHI2_3_95, "gkmc": kap[:, 0] <= ivlib.CHI2_1_95,
           "gkm19": kap[:, 0] <= c3t, "gkm19q": kap[:, 0] <= c3q}
    fns = {"rob": acc_rob, "gkmc": acc_gkmc, "gkm19": acc_gkm19, "gkm19q": acc_gkm19q}
    sets = {s: ivlib.invert_on_grid(fns[s], accepted=acc[s], points=pts) for s in SETS}

    for s, gs in sets.items():
        p = f"b6_ar_{s}"
        m.update({f"{p}_lo": gs.lo, f"{p}_hi": gs.hi, f"{p}_npieces": gs.npieces,
                  f"{p}_shape": gs.shape, f"{p}_pieces": ivlib.pieces_str(gs.pieces),
                  f"{p}_lo_unbounded": int(gs.unbounded_lo),
                  f"{p}_hi_unbounded": int(gs.unbounded_hi),
                  f"{p}_contains_0": int(ivlib.in_set(0.0, gs.pieces))})
    m["b6_rob_m_at_0"] = pb.profile(0.0)[0]
    m["h3b_b6_return_positive"] = ivlib.positive_bounded(sets["rob"].pieces)
    m["gkm19_3t_3q_same_decision_on_0"] = int(
        ivlib.in_set(0.0, sets["gkm19"].pieces) == ivlib.in_set(0.0, sets["gkm19q"].pieces))

    # GKMC: procedure vs closed-form quadric vs ivmodels
    quad = pb.gkmc_quadric()
    ivm_chi2 = ivlib.ivmodels_inverse(pb, "chi2")
    ivm_gkm = ivlib.ivmodels_inverse(pb, "gkm")
    m["b6_ar_gkmc_quadric_pieces"] = ivlib.pieces_str(quad)
    m["b6_ar_gkmc_ivmodels_pieces"] = ivlib.pieces_str(ivm_chi2)
    m["b6_ar_gkm19q_ivmodels_pieces"] = ivlib.pieces_str(ivm_gkm)
    m["b6_gkmc_quadric_vs_ivmodels"] = ivlib.bounds_diff(quad, ivm_chi2)
    m["b6_gkmc_grid_vs_quadric"] = ivlib.bounds_diff(sets["gkmc"].pieces, quad)
    m["b6_gkm19q_grid_vs_ivmodels"] = ivlib.bounds_diff(sets["gkm19q"].pieces, ivm_gkm)
    ivlib.require(close(quad, ivm_chi2), "GKMC closed form != ivmodels (1e-4)")
    ivlib.require(close(sets["gkmc"].pieces, quad), "GKMC procedure != closed form (1e-4)")
    ivlib.require(close(sets["gkm19q"].pieces, ivm_gkm), "(3Q) set != ivmodels gkm (1e-4)")

    # kappa_1 and critical values at the 2SLS estimate and at every reported bound
    points = {"2sls": b6.coef, "zero": 0.0}
    for s, gs in sets.items():
        for side, v in (("lo", gs.lo), ("hi", gs.hi)):
            if math.isfinite(v):
                points[f"{s}_{side}"] = v
    # ivmodels agreement: failing checks at |b0| <= 1 (the 2SLS estimate, 0, -0.5, 0.5, 1
    # and every finite reported bound inside [-1, 1]); at a bound beyond |b0| = 1 the
    # differences are recorded only, because kappa_1 grows like b0^2 there
    # (exp76 + ed76 = age76 - 6 is in the instruments' span) and ivmodels' root solver
    # loses precision for |b0| of order 1e3 and above (seen on the synthetic Card file).
    checks = dict(points)
    checks.update({"m0p5": -0.5, "p0p5": 0.5, "p1": 1.0})
    bad, worst_p = [], 0.0
    worst = {"in": [0.0, 0.0], "out": [0.0, 0.0]}
    for tag, b in checks.items():
        kp, k1 = pb.kappas(b)
        if tag in points:
            m[f"b6_kappa1_at_{tag}"] = k1
            m[f"b6_kappap_at_{tag}"] = kp
            m[f"b6_c3t_at_{tag}"] = ivlib.c_gkm19_table(k1)
            m[f"b6_c3q_at_{tag}"] = ivlib.c_gkm19_quantile(k1)
        iv = ivlib.ivmodels_panel_b(pb, b)
        dkp = abs(kp - iv["kappa_p"]) / max(abs(kp), abs(iv["kappa_p"]), 1.0)
        dk1 = abs(k1 - iv["kappa_1"]) / max(abs(k1), abs(iv["kappa_1"]), 1.0)
        where = "in" if abs(b) <= 1.0 else "out"
        worst[where] = [max(worst[where][0], dkp), max(worst[where][1], dk1)]
        if where == "in":
            if dkp > 1e-6 or dk1 > 1e-6:
                bad.append(f"{tag}: kappa_p {kp} vs {iv['kappa_p']}, kappa_1 {k1} vs {iv['kappa_1']}")
            if kp > 1e-8:          # p-values compared where the statistic is not 0
                dp = abs(ivlib.p_gkm19_ivmodels(kp, k1) - iv["p_gkm"])
                if not dp < 1e-3:  # NaN fails too
                    bad.append(f"{tag}: GKM p-value differs by {dp}")
                worst_p = max(worst_p, dp)
    m["b6_ivmodels_kappap_max_rel"] = worst["in"][0]
    m["b6_ivmodels_kappa1_max_rel"] = worst["in"][1]
    m["b6_ivmodels_kappap_max_rel_outer"] = worst["out"][0]
    m["b6_ivmodels_kappa1_max_rel_outer"] = worst["out"][1]
    m["b6_ivmodels_p_gkm_max_abs"] = worst_p
    m["b6_ivmodels_points_checked"] = sum(abs(b) <= 1.0 for b in checks.values())
    ivlib.require(not bad, "own statistics != ivmodels: " + "; ".join(bad))
    m["b6_kappa1"] = m["b6_kappa1_at_2sls"]
    m["b6_kappa1_min"] = float(kap[:, 1].min())
    m["b6_kappa1_min_at_b0"] = float(pts[int(np.argmin(kap[:, 1]))])
    m["grid_points"] = int(pts.size)

    if out_dir is not None:
        with (out_dir / "profile.csv").open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["b0", "m", "kappa_p", "kappa_1", "c_gkm19", "c_gkm19q",
                        "acc_rob", "acc_gkmc", "acc_gkm19", "acc_gkm19q"])
            for i, b in enumerate(pts):
                w.writerow([repr(float(b)), repr(float(prof[i])), repr(float(kap[i, 0])),
                            repr(float(kap[i, 1])), repr(float(c3t[i])), repr(float(c3q[i]))]
                           + [int(acc[s][i]) for s in SETS])
    return m


def main() -> int:
    t0 = time.time()
    df = ivlib.load_analysis()
    out = ivlib.run_dir(RUN)
    m = compute(df, out)
    ivlib.write_metrics(out / "metrics.json", m)
    print(f"{RUN}: robust {m['b6_ar_rob_pieces']}; GKMC {m['b6_ar_gkmc_pieces']}; "
          f"GKM19 {m['b6_ar_gkm19_pieces']}; wall {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
