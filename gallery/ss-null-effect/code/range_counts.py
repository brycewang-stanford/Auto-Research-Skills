"""Count inadmissible outcome values by treatment arm (design: run range-counts).

PI ruling on design-r2 F7; rules from plan.json design.method.outcome_validity, fixed
before any outcome value was examined. Reads data/raw/null_extract.csv with usecols =
treat + the six outcomes. OUTPUT IS COUNTS ONLY: no value, extreme, mean, quantile or
distribution of any outcome is printed or written. The sentinel rule compares each
sentinel code with the largest (or, for negative codes, smallest) admissible
non-sentinel value of the outcome; that extreme exists only inside sentinel_mask().

Categories, mutually exclusive and assigned in this order, for each outcome k and arm:
  missing     empty cell (as in run missing-counts)
  nonfinite   non-numeric text, NaN or +/-inf
  below       finite and below the admissible lower bound
  above       finite and above the admissible upper bound
  noninteger  inside the bounds but not an admissible level
              (employed78: not 0 or 1; wellbeing78: not an integer)
  sentinel    otherwise admissible, but a sentinel code outside the range of every
              other admissible value
Metrics per category: count and share by arm, and share treated - share control.
  out_of_range = below + above + noninteger
  inadmissible = nonfinite + out_of_range + sentinel
  dropped      = missing + inadmissible (the share the rob-ipow trigger, > 0.02, uses)

wellbeing78 safeguard: if inadmissible/n > 0.01 in either arm under the primary rule
(integer in [0, 10]), the rule becomes 'finite' with sentinel codes
{-9, -99, -999, 97, 98, 99, 999}. Counts under both rules are written; the effective
rule's counts are also written under range_wellbeing78_* and drive the trigger.

Run from the workspace root:
    .venv/bin/python -I code/range_counts.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw/null_extract.csv")
METRICS = Path("data/derived/range_counts.json")
TREAT = "treat"
OUTCOMES = ["re78", "re79", "employed78", "hours78", "benefits78", "wellbeing78"]
MONEY_SENTINELS = [999, 9999, 99999, 999999, 9999999]
WB_FALLBACK_SENTINELS = [-9, -99, -999, 97, 98, 99, 999]
IPOW_TRIGGER = 0.02
WB_SAFEGUARD = 0.01
CATS = ["missing", "nonfinite", "below", "above", "noninteger", "sentinel"]

# (lower, upper, level check, sentinel codes); None = no bound / no check
RULES = {
    "re78": (0, None, None, MONEY_SENTINELS),
    "re79": (0, None, None, MONEY_SENTINELS),
    "benefits78": (0, None, None, MONEY_SENTINELS),
    "hours78": (0, 8784, None, MONEY_SENTINELS),
    "employed78": (0, 1, "binary", []),
    "wellbeing78": (0, 10, "integer", []),
}
WB_FALLBACK = (None, None, None, WB_FALLBACK_SENTINELS)


def sentinel_mask(x: pd.Series, ok: pd.Series, codes: list) -> pd.Series:
    """Codes that lie beyond every admissible non-sentinel value. Extremes stay local."""
    if not codes:
        return pd.Series(False, index=x.index)
    is_code = x.isin(codes) & ok
    others = x[ok & ~is_code]
    hi = others.max() if len(others) else -np.inf
    lo = others.min() if len(others) else np.inf
    return is_code & (((x > 0) & (x > hi)) | ((x < 0) & (x < lo)))


def classify(raw: pd.Series, rule: tuple) -> dict[str, pd.Series]:
    lower, upper, level, codes = rule
    missing = raw.isna()
    x = pd.to_numeric(raw, errors="coerce").astype(float)
    finite = pd.Series(np.isfinite(x.to_numpy()), index=x.index)
    nonfinite = ~missing & ~finite
    below = finite & (x < lower) if lower is not None else pd.Series(False, index=x.index)
    above = finite & (x > upper) if upper is not None else pd.Series(False, index=x.index)
    inside = finite & ~below & ~above
    if level == "binary":
        noninteger = inside & ~x.isin([0, 1])
    elif level == "integer":
        noninteger = inside & (x != np.floor(x))
    else:
        noninteger = pd.Series(False, index=x.index)
    ok = inside & ~noninteger
    sentinel = sentinel_mask(x, ok, codes)
    return {"missing": missing, "nonfinite": nonfinite, "below": below, "above": above,
            "noninteger": noninteger, "sentinel": sentinel}


def summarize(prefix: str, masks: dict, treated: pd.Series, m: dict) -> dict:
    n_t, n_c = int(treated.sum()), int((~treated).sum())
    masks = dict(masks)
    masks["out_of_range"] = masks["below"] | masks["above"] | masks["noninteger"]
    masks["inadmissible"] = masks["nonfinite"] | masks["out_of_range"] | masks["sentinel"]
    masks["dropped"] = masks["missing"] | masks["inadmissible"]
    shares = {}
    for cat, mask in masks.items():
        ct, cc = int(mask[treated].sum()), int(mask[~treated].sum())
        m[f"{prefix}_{cat}_treated"] = ct
        m[f"{prefix}_{cat}_control"] = cc
        m[f"{prefix}_{cat}_share_treated"] = ct / n_t
        m[f"{prefix}_{cat}_share_control"] = cc / n_c
        m[f"{prefix}_{cat}_share_diff"] = ct / n_t - cc / n_c
        shares[cat] = (ct / n_t, cc / n_c)
    return shares


def main() -> int:
    df = pd.read_csv(RAW, usecols=[TREAT] + OUTCOMES,
                     dtype={k: str for k in OUTCOMES} | {TREAT: int})
    treated = df[TREAT] == 1
    m: dict = {"rows": int(len(df)), "n_treated": int(treated.sum()),
               "n_control": int((~treated).sum()), "ipow_trigger_threshold": IPOW_TRIGGER,
               "wellbeing78_safeguard_threshold": WB_SAFEGUARD}
    triggered = []
    for k in OUTCOMES:
        if k == "wellbeing78":
            primary = summarize("wb_primary", classify(df[k], RULES[k]), treated, m)
            fires = max(primary["inadmissible"]) > WB_SAFEGUARD
            fallback = summarize("wb_fallback", classify(df[k], WB_FALLBACK), treated, m)
            m["wellbeing78_safeguard_fires"] = bool(fires)
            m["wellbeing78_effective_rule"] = "finite+sentinels" if fires else "integer[0,10]"
            shares = summarize(f"range_{k}", classify(df[k], WB_FALLBACK if fires else RULES[k]),
                               treated, m)
        else:
            shares = summarize(f"range_{k}", classify(df[k], RULES[k]), treated, m)
        diff = shares["dropped"][0] - shares["dropped"][1]
        m[f"ipow_trigger_{k}"] = bool(abs(diff) > IPOW_TRIGGER)
        if abs(diff) > IPOW_TRIGGER:
            triggered.append(k)
    m["ipow_triggered_outcomes"] = ",".join(triggered)
    m["ipow_any_trigger"] = bool(triggered)

    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(m, indent=2) + "\n")
    print(f"wrote {METRICS}; wellbeing78 safeguard fires: {m['wellbeing78_safeguard_fires']}; "
          f"rob-ipow triggered for: {', '.join(triggered) or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
