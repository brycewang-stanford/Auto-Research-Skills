"""Run r-balance (plan.json analysis_plan step 9; report only). HC1 throughout; each
coefficient in points and in sample-SD units (SD of the outcome in the regression sample,
n - 1), with N.

(a) kww on nearc4 for age76 in 24..25 (age 14-15 in 1966) with BASE_B + FB + 1{age76 = 25}
    (age762 dropped: two ages);
(b) kww on nearc4 for all men with age76 + age762 + BASE_B + FB (age, not experience);
(c) iq on nearc4 with the controls of (b), where iq is non-missing;
(d) share with non-missing iq among nearc4 = 1 and nearc4 = 0, the difference and its HC1
    SE (univariate regression of the indicator on nearc4).
Rows with a missing kww (iq) are left out of (a)-(b) ((c)); counts are written.
Fixed reading (design): a 95% CI excluding 0 in (a) or (c) is reported as evidence of
selection on ability or better schools near colleges; (b) is descriptive only.

Input: data/derived/card_analysis.csv.  Output: runs/r-balance/metrics.json.
Usage: .venv/bin/python code/r_balance.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "r-balance"


def one(d, y: str, regs: list[str], p: str) -> dict:
    d = d[d[y].notna()]
    f = ivlib.fit_ols(d, y, ["nearc4"] + regs, "nearc4", p)
    sd = float(d[y].std(ddof=1))
    lo, hi = f.coef - ivlib.Z975 * f.se_hc1, f.coef + ivlib.Z975 * f.se_hc1
    return {p: f.coef, f"{p}_se": f.se_hc1, f"{p}_n": f.n, f"{p}_sd": sd,
            f"{p}_sd_units": f.coef / sd, f"{p}_se_sd_units": f.se_hc1 / sd,
            f"{p}_lo": lo, f"{p}_hi": hi, f"{p}_ci_excludes_0": int(lo > 0 or hi < 0)}


def compute(df) -> dict:
    df = df.copy()
    df["age25"] = (df["age76"] == 25).astype(float)
    young = df[df["age76"].isin([24, 25])]
    m = {"n_sample": len(df), "n_age24_25": len(young)}
    m.update(one(young, "kww", ["age25"] + ivlib.BASE_B + ivlib.FB, "bal_kww_young"))
    ctrl_b = ivlib.AGE + ivlib.BASE_B + ivlib.FB
    m.update(one(df, "kww", ctrl_b, "bal_kww_all"))
    m.update(one(df, "iq", ctrl_b, "bal_iq"))
    df["iq_obs"] = df["iq"].notna().astype(float)
    f = ivlib.fit_ols(df, "iq_obs", ["const", "nearc4"], "nearc4", "iq_obs")
    near = df["nearc4"] == 1
    m.update({"iq_obs_share_near": float(df.loc[near, "iq_obs"].mean()),
              "iq_obs_share_far": float(df.loc[~near, "iq_obs"].mean()),
              "iq_obs_diff": f.coef, "iq_obs_diff_se": f.se_hc1, "iq_obs_n": int(df["iq_obs"].sum())})
    ivlib.require(abs(m["iq_obs_diff"] - (m["iq_obs_share_near"] - m["iq_obs_share_far"])) < 1e-12,
                  "iq_obs_diff != difference of shares")
    return m


def main() -> int:
    t0 = time.time()
    m = compute(ivlib.load_analysis())
    ivlib.write_metrics(ivlib.run_dir(RUN) / "metrics.json", m)
    print(f"{RUN}: kww(14-15) {m['bal_kww_young']:.3f} ({m['bal_kww_young_se']:.3f}); "
          f"wall {time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
