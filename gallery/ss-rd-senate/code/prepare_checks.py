"""Design-stage data checks for the Senate RD file (no outcome statistic).

Computes (a) ties and mass points in `margin`, overall and within |margin| <= 30;
(b) the file's descriptive statistics for margin, class, termshouse, termssenate and
population, compared with the values printed in Calonico, Cattaneo, Farrell and
Titiunik (2017), Sec. 7.2 (p. 390 summary table; p. 391 rdplot N per side;
p. 400 rdbwselect min/max of margin); (c) counts of non-missing outcome by side of
the cutoff, which is a count of cases, not a statistic of vote's values.

It never computes a statistic of `vote` by side of the cutoff, nor any regression.

Usage (run through crew.py run --kind data-prep):
    .venv/bin/python code/prepare_checks.py runs/dr-checks/metrics.json
"""
import json
import math
import os
import sys

import numpy as np
import pandas as pd

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(WS, "data", "raw", "rdrobust_senate.csv")

# Printed in CCFT 2017, Sec. 7.2, p. 390 ("sum vote margin class termshouse
# termssenate population"): (Obs, Mean, SD, Min, Max, display decimals).
PRINTED_SUMMARY = {
    # var: (Obs, Mean, mean decimals, SD, SD decimals, Min, Max)
    "margin": (1390, 7.171159, 6, 34.32488, 5, -100, 100),
    "class": (1390, 2.023022, 6, 0.8231983, 7, 1, 3),
    "termshouse": (1108, 1.436823, 6, 2.357133, 6, 0, 16),
    "termssenate": (1108, 4.555957, 6, 3.720294, 6, 1, 20),
    # population: mean and SD printed as integers; max printed as 3.73e+07 (3 significant digits)
    "population": (1390, 3827919, 0, 4436950, 0, 78000, 37300000),
}
# Printed N per side, p. 391 (rdplot) and p. 392 (rdrobust default output).
PRINTED_N_LEFT, PRINTED_N_RIGHT = 595, 702
# Printed in the rdbwselect output, p. 400: min/max of margin on each side (vote non-missing).
PRINTED_LEFT_MAX_MARGIN = -0.079    # closest negative margin to 0
PRINTED_RIGHT_MIN_MARGIN = 0.036    # closest non-negative margin to 0
PRINTED_VOTE_OBS = 1297             # p. 390


def close(a, b, decimals):
    """Match at the printed display precision (half a unit in the last printed decimal)."""
    return abs(a - b) <= 0.5 * 10 ** (-decimals) + 1e-12


def ties(s):
    vc = s.value_counts()
    shared = vc[vc >= 2]
    top = vc.iloc[0]
    return {
        "distinct": int(vc.shape[0]),
        "values_shared_by_2plus": int(shared.shape[0]),
        "obs_in_shared_values": int(shared.sum()),
        "max_multiplicity": int(top),
        "value_with_max_multiplicity": float(vc.index[0]),
        "n_values_with_max_multiplicity": int((vc == top).sum()),
    }


def main():
    metrics_path = sys.argv[1]
    df = pd.read_csv(RAW)
    for col in ["year", "vote", "margin", "class", "termshouse", "termssenate", "population"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    m = {"rows": int(len(df))}

    # (a) ties and mass points in margin
    mg = df["margin"].dropna()
    t_all = ties(mg)
    inwin = mg[mg.abs() <= 30]
    t_win = ties(inwin)
    for k, v in t_all.items():
        m[f"margin_all_{k}"] = v
    m["margin_all_n"] = int(len(mg))
    for k, v in t_win.items():
        m[f"margin_win30_{k}"] = v
    m["margin_win30_n"] = int(len(inwin))
    m["margin_all_share_in_shared_values"] = round(t_all["obs_in_shared_values"] / len(mg), 6)
    m["margin_win30_share_in_shared_values"] = round(t_win["obs_in_shared_values"] / len(inwin), 6)
    m["margin_eq_plus100_count"] = int((mg == 100).sum())
    m["margin_eq_minus100_count"] = int((mg == -100).sum())
    m["margin_all_nonint_share"] = round(float((mg % 1 != 0).mean()), 6)

    # (b) descriptive statistics, compared with printed values
    for var, (p_obs, p_mean, d_mean, p_sd, d_sd, p_min, p_max) in PRINTED_SUMMARY.items():
        s_ = df[var].dropna()
        n = int(len(s_))
        mean, sd, mn, mx = float(s_.mean()), float(s_.std(ddof=1)), float(s_.min()), float(s_.max())
        m[f"{var}_obs"] = n
        m[f"{var}_mean"] = mean
        m[f"{var}_sd"] = sd
        m[f"{var}_min"] = mn
        m[f"{var}_max"] = mx
        m[f"{var}_match_obs"] = int(n == p_obs)
        m[f"{var}_match_mean"] = int(close(mean, p_mean, d_mean))
        m[f"{var}_match_sd"] = int(close(sd, p_sd, d_sd))
        m[f"{var}_match_min"] = int(mn == p_min)
        if var == "population":
            m[f"{var}_match_max"] = int(round(mx / 1e7, 2) == round(p_max / 1e7, 2))
        else:
            m[f"{var}_match_max"] = int(mx == p_max)

    # (c) counts of non-missing outcome by side (counts only; vote values not used)
    has_out = df["vote"].notna()
    left = df[has_out & (df["margin"] < 0)]
    right = df[has_out & (df["margin"] >= 0)]
    m["vote_nonmissing_obs"] = int(has_out.sum())
    m["vote_nonmissing_match"] = int(has_out.sum() == PRINTED_VOTE_OBS)
    m["n_left_nonmissing"] = int(len(left))
    m["n_right_nonmissing"] = int(len(right))
    m["n_left_match"] = int(len(left) == PRINTED_N_LEFT)
    m["n_right_match"] = int(len(right) == PRINTED_N_RIGHT)
    m["left_closest_to_zero"] = float(left["margin"].max())
    m["right_closest_to_zero"] = float(right["margin"].min())
    m["left_closest_match"] = int(round(float(left["margin"].max()), 3) == PRINTED_LEFT_MAX_MARGIN)
    m["right_closest_match"] = int(round(float(right["margin"].min()), 3) == PRINTED_RIGHT_MIN_MARGIN)
    m["left_min_margin_nonmissing"] = float(left["margin"].min())
    m["right_max_margin_nonmissing"] = float(right["margin"].max())

    with open(metrics_path, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
