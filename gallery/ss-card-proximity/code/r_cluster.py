"""Run r-cluster (plan.json analysis_plan step 10; report only): for A6 and A5, the first
stage and reduced form (coefficient on nearc4) with CR1 SEs clustered on region-1966
(reg661-reg669) x smsa66r cells: G, the smallest cell size, the number of cells under 30
men, the ratio to the HC1 SE, and the clustered reduced-form t against t(0.975, G - 1).
CR1 = statsmodels cov_type='cluster' (G/(G-1) x (n-1)/(n-k)), checked against ivlib.cr1_se
to 1e-10 relative (failure = run fails).
Fixed reading (design): a clustered t below its critical value means H3 and H4 depend on
treating men as independent; a t above it is not reported as robustness to county-level
dependence (CR1 with few, unequal cells can over-reject).

Input: data/derived/card_analysis.csv.  Output: runs/r-cluster/metrics.json.
Usage: .venv/bin/python code/r_cluster.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import scipy.stats
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "r-cluster"


def compute(df) -> dict:
    groups = ivlib.region_smsa_cells(df)
    _, sizes = np.unique(groups, return_counts=True)
    G = int(sizes.size)
    tcrit = float(scipy.stats.t.ppf(0.975, G - 1))
    m = {"n_sample": len(df), "n_clusters": G, "min_cluster_size": int(sizes.min()),
         "n_clusters_under30": int((sizes < 30).sum()), "t_crit_cl": tcrit}
    for p, fs_spec, rf_spec in (("a6", "A2", "A4"), ("a5", "A1", "A3")):
        for tag, spec in (("fs", fs_spec), ("rf", rf_spec)):
            _, y, regs, *_ = ivlib.SPECS[spec]
            X = ivlib.cols(df, regs)
            yv = df[y].to_numpy(float)
            res = sm.OLS(yv, X).fit(cov_type="cluster", cov_kwds={"groups": groups})
            se_cl = float(res.bse[0])
            own = ivlib.cr1_se(X, yv - X @ res.params, groups, 0)
            ivlib.require(ivlib.rel_diff(se_cl, own) < 1e-10, f"CR1 {spec} != own formula")
            hc1 = ivlib.fit_spec(df, spec)
            t_cl = float(res.params[0]) / se_cl
            m.update({f"{p}_{tag}": float(res.params[0]), f"{p}_{tag}_se_cl": se_cl,
                      f"{p}_{tag}_se_hc1": hc1.se_hc1, f"{p}_{tag}_cl_ratio": se_cl / hc1.se_hc1,
                      f"{p}_{tag}_t_cl": t_cl,
                      f"{p}_{tag}_t_cl_above_crit": int(abs(t_cl) > tcrit)})
    return m


def main() -> int:
    t0 = time.time()
    m = compute(ivlib.load_analysis())
    ivlib.write_metrics(ivlib.run_dir(RUN) / "metrics.json", m)
    print(f"{RUN}: G {m['n_clusters']}; A6 RF t_cl {m['a6_rf_t_cl']:.3f}; "
          f"wall {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
