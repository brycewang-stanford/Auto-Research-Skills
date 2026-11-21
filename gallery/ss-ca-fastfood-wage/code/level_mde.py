"""Run level-mde (analysis_plan 2; design.method INFERENCE, DEGREES OF FREEDOM, LEVEL CHECK,
CRITICAL VALUES, MDE AND POWER).

Inputs  data/derived/state_panel_pre.csv (2014Q1-2019Q4; the script refuses any later quarter)
        runs/select/metrics.json (the selected candidate)
Output  runs/level-mde/metrics.json
        runs/level-mde/tests.csv   one row per statistic x pseudo-date x treated unit

Statistics (keys): h1 = selected candidate, pooled W; h2 = selected, pooled E-or-P; h3 = selected,
year-2-minus-year-1 difference; s1 = S1 (DDT endpoint trend, AGG, E, R50); s2 = S2 (SDID, P, D20,
fit window 2015Q1..B'); op = selected estimator and outcome with the other pool.

At each pseudo-date B' and for each unit u in the pool plus California, INFERENCE is applied with
u treated: California with the pool (J donors), every other unit with the pool minus u (J-1
donors; California excluded from its donors and placebos). T = tau / SE for SE, SE_s and SE_n.
Rates of T > t_0.95, T < -t_0.95 and |T| > t_0.975 (t at each test's own donor count; California
also at t_nu) over all tests, by population tercile at B', over the decision set L (the ten most
populous D20 states at B') and for California, with the effective number of independent draws.

nu_hat = (sum_j s_j^2)^2 / sum_j s_j^4 with s_j^2 = mean over the six B' of tau_j(B')^2, tau_j the
placebo estimates of California's test; nu = min(J, nu_hat). Critical values c_hi(p) =
max(t_{nu,p}, L quantile 'higher'), c_lo(p) = min(-t_{nu,1-p}, L quantile 'lower'). SE_pre =
sqrt(mean over B' of SE_CA(B')^2). MDE_h1 = (c_hi(0.95) + t_{nu,0.80}) SE_pre, MDE_h2 and MDE_h3
with c_hi(0.975); h90_h2 = max(c_hi(0.95), -c_lo(0.05)) SE_pre; the nine H2 label
probabilities under tau = 0 and -0.035 (T ~ t_nu, closed form). Report-only (design-r4 D14):
MDE_h2 and h90_h2 also under t_J (t_J in the t floor of the critical values and in the power
quantile; L quantiles unchanged).
"""
import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
# code/select.py shadows the standard-library module 'select'; load the standard one first.
sys.path[:] = [p for p in sys.path if str(Path(p or ".").resolve()) != _HERE]
import select  # noqa: E402,F401  (standard library)
sys.path.insert(0, _HERE)

import json  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import sclib as S  # noqa: E402

INPUT = Path("data/derived/state_panel_pre.csv")
SELECT_METRICS = Path("runs/select/metrics.json")
OUT_DIR = Path("runs/level-mde")
METRICS = OUT_DIR / "metrics.json"
TESTS_CSV = OUT_DIR / "tests.csv"
TAU_ALT = -0.035
SE_KEYS = {"se": "se", "ses": "se_s", "sen": "se_n"}


def load_input(src=INPUT):
    """Read the truncated panel; raise if it holds any quarter after 2019Q4 (0f (v))."""
    return S.Panel(S.read_panel_csv(src, pre_only=True))


def families(selected):
    """(family, spec, pool, {statistic key: stat name in the family}, windows options)."""
    spec, pool = S.parse_candidate(selected)
    s2_spec = S.Spec(est="SDID", norm="P", fit_start=S.qidx(2015, 1))
    return [
        ("h1", spec.with_(norm="W"), pool, {"h1": "pooled"}, dict(years=False, diff=False)),
        ("h2h3", spec, pool, {"h2": "pooled", "h3": "diff"}, dict(years=True, diff=True)),
        ("s1", S.Spec(est="DDTE", weighting="AGG", norm="E"), "R50", {"s1": "pooled"},
         dict(years=False, diff=False)),
        ("s2", s2_spec, "D20", {"s2": "pooled"}, dict(years=False, diff=False)),
        ("op", spec, S.other_pool(pool), {"op": "pooled"}, dict(years=False, diff=False)),
    ]


def run_tests(panel, selected):
    """Every level-check test. Returns a long DataFrame and California's placebo taus."""
    rows, ca_plc = [], {}
    for fam, spec, pool, stat_map, opt in families(selected):
        donors_pool = S.POOLS[pool]
        for B in S.PSEUDO_DATES:
            win = S.standard_windows(B, fit_start=spec.fit_start, years=opt["years"], anticip=False)
            fn = S.make_stat_fn(panel, spec, win, keys=["pooled"] + (["y1", "y2"] if opt["years"] else []),
                                diff=opt["diff"])
            pop_of = S.pop_at_base(panel, win)
            units = [S.CA] + list(donors_pool)
            terc = S.population_terciles(units, [pop_of(u) for u in units])
            L = set(S.decision_set_l(panel, B))
            for u, donors in S.level_check_units(donors_pool):
                res = S.placebo_inference(fn, u, donors, pop_of)
                for key, stat in stat_map.items():
                    r = res[stat]
                    rows.append({"stat": key, "pseudo_date": S.qlabel(B), "unit": u,
                                 "abbr": panel.abbr.get(u, u), "is_ca": int(u == S.CA),
                                 "in_L": int(u in L), "tercile": terc[u], "pop": pop_of(u),
                                 "J": r["J"], "tau": r["tau"], "se": r["se"], "se_s": r["se_s"],
                                 "se_n": r["se_n"], "fp_a": r["fp_a"], "fp_b": r["fp_b"],
                                 "fp_se": r["fp_se"]})
                    if u == S.CA:
                        ca_plc[(key, B)] = dict(zip(donors, r["placebos"]))
    return pd.DataFrame(rows), ca_plc


def summarise(tests, ca_plc, selected):
    spec, pool = S.parse_candidate(selected)
    pools = {"h1": pool, "h2": pool, "h3": pool, "s1": "R50", "s2": "D20", "op": S.other_pool(pool)}
    m = {"selected": selected, "selected_pool": pool, "other_pool": S.other_pool(pool),
         "pseudo_dates": ",".join(S.qlabel(b) for b in S.PSEUDO_DATES), "tau_alt": TAU_ALT,
         "b": S.B_SIZE}
    crit = {}
    for key, pl in pools.items():
        J = len(S.POOLS[pl])
        d = tests[tests.stat == key]
        ca = d[d.is_ca == 1].sort_values("pseudo_date")
        m[f"J_{key}"] = J
        m[f"pool_{key}"] = pl
        # degrees of freedom from California's placebos
        donors = S.POOLS[pl]
        s2 = np.array([np.mean([ca_plc[(key, B)][j] ** 2 for B in S.PSEUDO_DATES]) for j in donors])
        for j, v in zip(donors, s2):
            m[f"s2_{key}_{j}"] = float(v)
        nu_hat, nu = S.nu_from_s2(s2, J)
        m[f"nu_hat_{key}"] = nu_hat
        m[f"nu_{key}"] = nu
        # rejection rates
        for sk, col in SE_KEYS.items():
            T = (d["tau"] / d[col]).to_numpy()
            Jref = d["J"].to_numpy()
            groups = {"all": np.ones(len(d), bool), "t1": (d.tercile == 1).to_numpy(),
                      "t2": (d.tercile == 2).to_numpy(), "t3": (d.tercile == 3).to_numpy(),
                      "L": (d.in_L == 1).to_numpy(), "ca": (d.is_ca == 1).to_numpy()}
            for g, mask in groups.items():
                r = S.rejection_rates(T[mask], Jref[mask])
                for test in ("up", "lo", "two"):
                    m[f"rej_{key}_{sk}_{g}_{test}"] = r[test]
                if sk == "se":
                    m[f"n_tests_{key}_{g}"] = r["n"]
            Tca = (ca["tau"] / ca[col]).to_numpy()
            rnu = S.rejection_rates(Tca, np.full(len(Tca), nu))
            for test in ("up", "lo", "two"):
                m[f"rej_{key}_{sk}_ca_tnu_{test}"] = rnu[test]
            m[f"k_{key}_{sk}"] = float(np.sqrt(np.mean(Tca ** 2)))
        n_all = 2 * (J + 1)
        m[f"eff_draws_{key}_all"] = n_all
        m[f"eff_draws_{key}_L"] = 20
        m[f"eff_draws_{key}_ca"] = 2
        for g, n_eff in (("all", n_all), ("L", 20)):
            lo, hi = S.binomial_band(n_eff)
            m[f"band_{key}_{g}_lo"] = lo
            m[f"band_{key}_{g}_hi"] = hi
        # critical values: t at nu and the L quantiles of T (SE = max)
        TL = (d.loc[d.in_L == 1, "tau"] / d.loc[d.in_L == 1, "se"]).to_numpy()
        if len(TL) != 60:
            raise ValueError(f"{key}: {len(TL)} T values in L, expected 60")
        lq = S.l_quantiles(TL)
        for k, v in lq.items():
            m[f"Lq_{key}_{k}"] = v
        m[f"tnu_{key}_95"] = S.t_quantile(nu, 0.95)
        m[f"tnu_{key}_975"] = S.t_quantile(nu, 0.975)
        m[f"tnu_{key}_80"] = S.t_quantile(nu, 0.80)
        m[f"tJ_{key}_95"] = S.t_quantile(J, 0.95)
        m[f"tJ_{key}_975"] = S.t_quantile(J, 0.975)
        c = S.critical_values(nu, lq)
        crit[key] = c
        for k, v in c.items():
            m[f"crit_{key}_{k}"] = v
            m[f"crit_{key}_{k}_from_L"] = int(v != S.critical_values(nu)[k])
        # California at each B': SE variants and the Ferman-Pinto diagnostic
        for _, r in ca.iterrows():
            b = r["pseudo_date"]
            m[f"ca_{key}_{b}_tau"] = float(r["tau"])
            for c_ in ("se", "se_s", "se_n", "fp_a", "fp_b", "fp_se"):
                m[f"ca_{key}_{b}_{c_}"] = float(r[c_])
        for c_, name in (("se", "se_pre"), ("se_s", "se_s_pre"), ("se_n", "se_n_pre")):
            m[f"{name}_{key}"] = float(np.sqrt(np.mean(ca[c_].to_numpy() ** 2)))
    # MDE and power (selected candidate)
    nu1, nu2, nu3 = m["nu_h1"], m["nu_h2"], m["nu_h3"]
    m["mde_h1"] = S.mde(crit["h1"]["hi95"], nu1, m["se_pre_h1"])
    m["mde_h2"] = S.mde(crit["h2"]["hi975"], nu2, m["se_pre_h2"])
    m["mde_h3"] = S.mde(crit["h3"]["hi975"], nu3, m["se_pre_h3"])
    m["h3_informative"] = int(m["mde_h3"] <= 0.04)
    m["h90_h2"] = S.h90(crit["h2"], m["se_pre_h2"])
    m["h90_h2_below_b"] = int(m["h90_h2"] < S.B_SIZE)
    # report-only (design-r4 D14): the same two quantities with t_J in place of t_nu in the t floor
    # of the critical values and in the power quantile; L quantiles unchanged
    J2 = m["J_h2"]
    c_tJ = S.critical_values(J2, S.lq_from_metrics(m, "h2"))
    m["mde_h2_tJ"] = S.mde(c_tJ["hi975"], J2, m["se_pre_h2"])
    m["h90_h2_tJ"] = S.h90(c_tJ, m["se_pre_h2"])
    for tau, tag in ((0.0, "tau0"), (TAU_ALT, "tau035")):
        probs = S.label_probabilities(tau, m["se_pre_h2"], crit["h2"], nu2)
        for k, v in probs.items():
            m[f"prob_{tag}_{k}"] = v
        m[f"prob_{tag}_sum"] = float(sum(probs.values()))
    m["solver_solves"] = S.SOLVER_LOG["solves"]
    m["solver_kkt_max"] = S.SOLVER_LOG["kkt_max"]
    m["solver_not_converged"] = S.SOLVER_LOG["not_converged"]
    return m


def main():
    panel = load_input()
    selected = json.loads(SELECT_METRICS.read_text())["selected"]
    tests, ca_plc = run_tests(panel, selected)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tests.to_csv(TESTS_CSV, index=False, float_format="%.10g")
    m = summarise(tests, ca_plc, selected)
    m["input_last_quarter"] = S.qlabel(int(panel.qi[-1]))
    S.write_json(METRICS, m)
    print(f"level-mde for {selected}: nu_h2 {m['nu_h2']:.2f}, MDE_h2 {m['mde_h2']:.4f}, "
          f"h90 {m['h90_h2']:.4f}")


if __name__ == "__main__":
    main()
