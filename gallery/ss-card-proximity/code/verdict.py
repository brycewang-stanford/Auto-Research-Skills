"""Run verdict (plan.json analysis_plan step 11): decision flags from the metrics of runs
h1-b6, h1-a6, h1-a5, h2h3-weakiv, h3b-subvector, h4-chr, h5-cf, r-age1419, r-balance and
r-cluster. No estimation.

H1: a printed number with d decimals is reproduced iff |replicated - published| <
0.5 x 10^-d (unrounded replicated value; a tie at exactly half a unit is a miss); N must
equal 3010. 9 primary and 22 secondary targets (design.method, values from WP 4483 as the
Scout read them, sources/notes.md sec. 1; the A5 homoskedastic AR set from Cinelli and
Hazlett 2025, Table 2). Every miss is listed.
H2: F_conv > 16.38 and F_eff > 23.11 (A6, A5). H3(a): the Panel-A-coefficient flags.
H3(b): the return flag (robust projection). H5: control-function rejection flags.
H4: breakdown next to the value predicted from the published conventional numbers
(lambda - 1.959964 se: 0.045, 0.018 for A6; 0.042, 0.018 for A5).

Inputs: runs/<id>/metrics.json for the ten runs above.  Output: runs/verdict/metrics.json.
Usage: .venv/bin/python code/verdict.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "verdict"
INPUT_RUNS = ("h1-b6", "h1-a6", "h1-a5", "h2h3-weakiv", "h3b-subvector", "h4-chr", "h5-cf",
              "r-age1419", "r-balance", "r-cluster")

# (label, run, metric, published value as printed, decimals)
PRIMARY = (
    ("B6 2SLS", "h1-b6", "beta_iv", 0.132, 3),
    ("B6 2SLS SE", "h1-b6", "se_iv_conv", 0.049, 3),
    ("B2 first stage", "h1-b6", "fs_nearc4", 0.365, 3),
    ("B2 first stage SE", "h1-b6", "fs_nearc4_se", 0.105, 3),
    ("B4 reduced form", "h1-b6", "rf_nearc4", 0.048, 3),
    ("B4 reduced form SE", "h1-b6", "rf_nearc4_se", 0.019, 3),
    ("T2 col 5 OLS", "h1-b6", "ols_beta", 0.073, 3),
    ("T2 col 5 OLS SE", "h1-b6", "ols_se", 0.004, 3),
)
N_TARGET = ("N", "h1-b6", "n_sample", 3010)
SECONDARY = (
    ("A6 2SLS", "h1-a6", "a6_iv", 0.140, 3), ("A6 2SLS SE", "h1-a6", "a6_iv_se", 0.055, 3),
    ("A2 first stage", "h1-a6", "a6_fs", 0.322, 3), ("A2 SE", "h1-a6", "a6_fs_se", 0.083, 3),
    ("A4 reduced form", "h1-a6", "a6_rf", 0.045, 3), ("A4 SE", "h1-a6", "a6_rf_se", 0.018, 3),
    ("A5 2SLS", "h1-a5", "a5_iv", 0.132, 3), ("A5 2SLS SE", "h1-a5", "a5_iv_se", 0.055, 3),
    ("A1 first stage", "h1-a5", "a5_fs", 0.320, 3), ("A1 SE", "h1-a5", "a5_fs_se", 0.088, 3),
    ("A3 reduced form", "h1-a5", "a5_rf", 0.042, 3), ("A3 SE", "h1-a5", "a5_rf_se", 0.018, 3),
    ("T2 col 2 OLS", "h1-a5", "a5_ols", 0.075, 3), ("T2 col 2 OLS SE", "h1-a5", "a5_ols_se", 0.003, 3),
    ("B5 2SLS", "h1-b6", "b5_iv", 0.122, 3), ("B5 2SLS SE", "h1-b6", "b5_iv_se", 0.046, 3),
    ("B1 first stage", "h1-b6", "b1_fs", 0.382, 3), ("B1 SE", "h1-b6", "b1_fs_se", 0.114, 3),
    ("B3 reduced form", "h1-b6", "b3_rf", 0.047, 3), ("B3 SE", "h1-b6", "b3_rf_se", 0.019, 3),
    ("A5 hom. AR lower", "h1-a5", "a5_ar_hom_lo", 0.025, 3),
    ("A5 hom. AR upper", "h1-a5", "a5_ar_hom_hi", 0.285, 3),
)
PUB_RF = {"a6": (0.045, 0.018), "a5": (0.042, 0.018)}


def reproduced(value, published: float, decimals: int) -> int:
    if value is None:
        return 0
    return int(abs(float(value) - published) < 0.5 * 10 ** -decimals)


def slug(label: str) -> str:
    return "".join(c if c.isalnum() else "_" for c in label.lower()).strip("_").replace("__", "_")


def judge(mt: dict[str, dict]) -> dict:
    out: dict = {}
    misses = []
    n_ok = int(mt[N_TARGET[1]][N_TARGET[2]] == N_TARGET[3])
    out["h1_n_reproduced"] = n_ok
    if not n_ok:
        misses.append("N")
    prim = n_ok
    for label, run, key, pub, d in PRIMARY:
        ok = reproduced(mt[run][key], pub, d)
        out[f"h1_{slug(label)}_reproduced"] = ok
        prim += ok
        if not ok:
            misses.append(label)
    sec = 0
    for label, run, key, pub, d in SECONDARY:
        ok = reproduced(mt[run][key], pub, d)
        out[f"h1_{slug(label)}_reproduced"] = ok
        sec += ok
        if not ok:
            misses.append(label)
    out["h1_primary_reproduced"] = prim
    out["h1_primary_targets"] = len(PRIMARY) + 1
    out["h1_secondary_reproduced"] = sec
    out["h1_secondary_targets"] = len(SECONDARY)
    out["h1_misses"] = "; ".join(misses) if misses else "none"
    w = mt["h2h3-weakiv"]
    for p in ("a6", "a5"):
        out[f"h2_{p}_sy_above"] = int(w[f"{p}_f_conv"] > ivlib.SY_10PCT)
        out[f"h2_{p}_mop_above"] = int(w[f"{p}_f_eff"] > ivlib.MOP_5PCT_10PCT)
        out[f"h3a_{p}_pacoef_positive"] = int(w[f"{p}_pacoef_positive"])
        out[f"h5_{p}_pacoef_equality_rejected"] = int(mt["h5-cf"][f"{p}_pacoef_cf_reject"])
        lam, se = PUB_RF[p]
        out[f"h4_{p}_pacoef_breakdown"] = mt["h4-chr"][f"{p}_pacoef_chr_breakdown"]
        out[f"h4_{p}_pacoef_breakdown_pred_pub"] = max(0.0, lam - ivlib.Z975 * se)
    out["h3b_b6_return_positive"] = int(mt["h3b-subvector"]["h3b_b6_return_positive"])
    return out


def main() -> int:
    mt = {r: json.loads((Path("runs") / r / "metrics.json").read_text()) for r in INPUT_RUNS}
    out = judge(mt)
    ivlib.write_metrics(ivlib.run_dir(RUN) / "metrics.json", out)
    print(f"{RUN}: H1 primary {out['h1_primary_reproduced']}/{out['h1_primary_targets']}, "
          f"secondary {out['h1_secondary_reproduced']}/{out['h1_secondary_targets']}; "
          f"misses: {out['h1_misses']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
