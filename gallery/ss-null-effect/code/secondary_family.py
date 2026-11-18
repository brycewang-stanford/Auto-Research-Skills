"""Run secondary-family: ATTs on re79, employed78, hours78, benefits78, wellbeing78 (H2).

Each outcome uses the primary estimator (code/aipw_lib.py) on the same folds and the same
propensity fits (fitted once per repetition and fold, reused; if an outcome had missing or
inadmissible values it would be re-estimated on its complete cases with refitted nuisances,
which the pre-gate counts show is not needed).

Multiplicity (design.method.secondary_family): one Gaussian multiplier bootstrap, B = 10,000,
xi_b,i ~ N(0, 1) from numpy default_rng(20261119), the same xi for the five outcomes, drawn
in blocks of 1,000 rows of an (B x n) matrix; t*_b,k = (sum_i xi_b,i psi_bar_k,i / n) / SE_k,
nuisances not refitted. Romano-Wolf stepdown: outcomes ordered by |t_k|; at each step the
adjusted p is the share of draws whose max |t*| over the outcomes not yet passed is >= |t_k|,
made monotone. Max-t: c = 95% quantile (numpy linear) of max_k |t*_b,k|; theta_k +/- c SE_k.
Unadjusted normal p-values reported alongside. 'Detected' iff Romano-Wolf p < 0.05.

Units: re79, benefits78 nominal dollars; employed78 also in percentage points (x 100);
hours78 hours; wellbeing78 own scale and in control-SD units (SD among controls, ddof = 1).

Run from the workspace root:  .venv/bin/python -I code/secondary_family.py
"""

import sys
from pathlib import Path

import numpy as np
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import aipw_lib as L  # noqa: E402

OUT = Path("runs/secondary-family/metrics.json")
FAMILY = ["re79", "employed78", "hours78", "benefits78", "wellbeing78"]
B = 10_000
BOOT_SEED = 20261119
BLOCK = 1_000


def main() -> int:
    df = L.load_data(FAMILY)
    L.check_basis_reuse(df)
    d_all = df["treat"].to_numpy(int)
    n = len(df)
    Xb_all = L.basis(df, L.COVS).to_numpy(float)
    Xt_all = L.tree_features(df, L.COVS)
    m_shared = L.crossfit_propensity(Xb_all, d_all)

    met: dict = {"family": ",".join(FAMILY), "n_bootstrap": B, "bootstrap_seed": BOOT_SEED,
                 "seed_base": L.SEED}
    thetas, ses, psis = [], [], []
    for k in FAMILY:
        ok = L.admissible(df[k], k)
        met[f"{k}_n_dropped_treated"] = int((~ok & (d_all == 1)).sum())
        met[f"{k}_n_dropped_control"] = int((~ok & (d_all == 0)).sum())
        y_all = df[k].to_numpy(float)
        if ok.all():
            res = L.aipw(d_all, y_all, Xb_all, Xt_all, m_raw=m_shared)
            psi_stacked = res["psi_bar"]
        else:  # complete cases, everything refitted on the subsample
            sub = df[ok].reset_index(drop=True)
            d = sub["treat"].to_numpy(int)
            res = L.aipw(d, sub[k].to_numpy(float), L.basis(sub, L.COVS).to_numpy(float),
                         L.tree_features(sub, L.COVS))
            psi_stacked = np.zeros(n)
            psi_stacked[ok] = (n / ok.sum()) * res["psi_bar"]
        met.update(L.summarize(res, f"{k}_"))
        met[f"{k}_control_mean_raw"] = float(y_all[ok & (d_all == 0)].mean())
        thetas.append(res["theta"]); ses.append(res["se"]); psis.append(psi_stacked)

    thetas, ses, psis = np.array(thetas), np.array(ses), np.vstack(psis)

    # Gaussian multiplier bootstrap (one draw matrix, shared across outcomes).
    rng = np.random.default_rng(BOOT_SEED)
    tstar = np.empty((B, len(FAMILY)))
    for start in range(0, B, BLOCK):
        xi = rng.standard_normal((BLOCK, n))
        tstar[start:start + BLOCK] = (xi @ psis.T / n) / ses
    abs_t = np.abs(tstar)
    t_obs = np.abs(thetas / ses)

    order = np.argsort(-t_obs, kind="stable")
    p_rw = np.empty(len(FAMILY))
    running = 0.0
    for j, k in enumerate(order):
        p = float(np.mean(abs_t[:, order[j:]].max(axis=1) >= t_obs[k]))
        running = max(running, p)
        p_rw[k] = running
    crit = float(np.quantile(abs_t.max(axis=1), 0.95))
    met["maxt_crit"] = crit
    met["bootstrap_sd_check_max_rel_dev"] = float(np.max(np.abs(tstar.std(axis=0, ddof=1) - 1)))

    for i, k in enumerate(FAMILY):
        met[f"{k}_p_unadj"] = float(2 * norm.sf(t_obs[i]))
        met[f"{k}_p_rw"] = float(p_rw[i])
        met[f"{k}_detected"] = bool(p_rw[i] < 0.05)
        met[f"{k}_maxt_low"] = float(thetas[i] - crit * ses[i])
        met[f"{k}_maxt_high"] = float(thetas[i] + crit * ses[i])
        met[f"{k}_rw_step"] = int(np.where(order == i)[0][0]) + 1
    met["n_detected"] = int(sum(met[f"{k}_detected"] for k in FAMILY))

    # Unit conversions for reporting.
    for key in ("effect", "se", "ci_low", "ci_high", "maxt_low", "maxt_high"):
        met[f"employed78_{key}_pp"] = 100 * met[f"employed78_{key}"]
    ok_wb = L.admissible(df["wellbeing78"], "wellbeing78")
    sd_wb = float(df.loc[ok_wb & (d_all == 0), "wellbeing78"].std(ddof=1))
    met["wellbeing78_control_sd"] = sd_wb
    for key in ("effect", "ci_low", "ci_high", "maxt_low", "maxt_high"):
        met[f"wellbeing78_{key}_sd"] = met[f"wellbeing78_{key}"] / sd_wb

    met.update(L.echo_counts(FAMILY))
    L.write_metrics(OUT, met)
    for k in FAMILY:
        print(k, round(met[f"{k}_effect"], 4), round(met[f"{k}_se"], 4),
              "p", round(met[f"{k}_p_unadj"], 4), "p_rw", round(met[f"{k}_p_rw"], 4))
    print("max-t crit", round(crit, 4))
    return 0


if __name__ == "__main__":
    sys.exit(main())
