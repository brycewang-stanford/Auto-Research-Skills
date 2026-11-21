"""Shared helpers for the figure scripts (code/fig_event.py, fig_select.py, fig_placebo.py).

Rules (crew/agents/figures-ra.md): every plotted number comes from a file a logged run wrote
(runs/<id>/...), declared with --input when the figure run is made; nothing here reads
claims.jsonl, data/raw or data/derived, and nothing estimates anything. The figure scripts only
redraw run outputs, check that those outputs agree with each other, and write a caption file
whose run-dependent parts (candidate, pool, outcome, J, nu) are printed from the same outputs.

Units: every estimate in these runs is a difference of logs. Figures show 100 x log points
(close to percent for small values); the caption says so.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

# One palette for every figure (Okabe-Ito, separable under colour-vision deficiency). Every
# distinction that matters also has a grayscale cue (position, marker fill or shape, hatching,
# line style), so the figures read in print.
INK = "#222222"
MUTED = "#8a8a8a"
LIGHT = "#d9d9d9"
BAND = "#c6c6c6"
BLUE = "#0072B2"
VERMILLION = "#D55E00"
GREEN = "#009E73"
ORANGE = "#E69F00"

SCALE = 100.0   # log points -> 100 x log points
UNIT_LABEL = "100 × log points"

OUTCOME_NAME = {
    "E": "seasonally adjusted log employment, NAICS 722513",
    "P": "seasonally adjusted log employment per resident, NAICS 722513",
    "W": "seasonally adjusted log average weekly wage, NAICS 722513",
}
ESTIMATOR_NAME = {
    "DD": "difference in differences (DD)",
    "DDT": "difference in differences with a linear trend (DDT)",
    "SC": "demeaned synthetic control (SC)",
    "SDID": "synthetic difference in differences (SDID)",
}
POOL_NAME = {
    "D20": "D20 (the 20 federal-minimum states)",
    "R50": "R50 (the other 49 states and DC)",
}
WEIGHTING_NAME = {"AGG": "aggregate donor series", "POPW": "population-weighted donor mean"}


class FigureInputError(ValueError):
    """A run output is missing a field or disagrees with another run output."""


def load_json(path: str | Path) -> dict:
    p = Path(path)
    if not p.exists():
        raise FigureInputError(f"{p}: missing (the run that writes it has not been made)")
    return json.loads(p.read_text(encoding="utf-8"))


def load_csv(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise FigureInputError(f"{p}: missing (the run that writes it has not been made)")
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def need(d: dict, key: str, where: str):
    if key not in d:
        raise FigureInputError(f"{where}: field '{key}' is missing")
    return d[key]


def fnum(row: dict, key: str, where: str) -> float:
    v = float(need(row, key, where))
    if not math.isfinite(v):
        raise FigureInputError(f"{where}: field '{key}' is not finite")
    return v


def close(a: float, b: float, tol: float = 1e-8) -> bool:
    return abs(a - b) <= tol * max(1.0, abs(a), abs(b))


def parse_candidate(cid: str) -> dict:
    """'DDT-POPW-P-D20' or 'SDID-E-R50' -> est, weighting, norm, pool (the id format runs/select
    writes; the same rule as sclib.parse_candidate, restated so the figures need no estimator
    code)."""
    parts = str(cid).split("-")
    if parts[0] in ("DD", "DDT") and len(parts) == 4:
        return {"est": parts[0], "weighting": parts[1], "norm": parts[2], "pool": parts[3]}
    if parts[0] in ("SC", "SDID") and len(parts) == 3:
        return {"est": parts[0], "weighting": None, "norm": parts[1], "pool": parts[2]}
    raise FigureInputError(f"candidate id '{cid}' has an unknown format")


def describe_candidate(cid: str) -> str:
    c = parse_candidate(cid)
    w = f", {WEIGHTING_NAME[c['weighting']]}" if c["weighting"] else ""
    return f"{ESTIMATOR_NAME[c['est']]}{w}, donor pool {POOL_NAME[c['pool']]}"


CRIT_NAME = {"hi95": "c_hi(0.95)", "hi975": "c_hi(0.975)", "lo05": "c_lo(0.05)", "lo025": "c_lo(0.025)"}


def sdid_floor(lvl: dict, lvl_path: str, selected: str, c: dict, keys: tuple) -> dict:
    """The SDID Monte Carlo floor on the H2 critical values (design.method C1), as run level-mde
    reports it: sdid_floor_h2 (1 for an SDID candidate), pool_h2 and q_cal of that pool
    (qcal_<pool>_<key>, echoed from check-methods). Checks that the flag matches the selected
    estimator and that the run's critical values c lie at least as far from zero as q_cal.
    Returns {applies, pool, qcal, binding (the keys among `keys` that the floor sets), phrase,
    sentence}: phrase replaces 'the decision-set quantile as a floor' in a caption and sentence
    is appended after it ('' when the floor does not apply)."""
    if need(lvl, "selected", lvl_path) != selected:
        raise FigureInputError(f"{lvl_path} is for {lvl['selected']}, the run for {selected}")
    cand = parse_candidate(selected)
    applies = int(need(lvl, "sdid_floor_h2", lvl_path))
    if applies != int(cand["est"] == "SDID"):
        raise FigureInputError(f"{lvl_path}: sdid_floor_h2 = {applies} for estimator {cand['est']}")
    if not applies:
        return {"applies": 0, "pool": None, "qcal": {}, "binding": [],
                "phrase": "the decision-set quantile as a floor", "sentence": ""}
    pool = need(lvl, "pool_h2", lvl_path)
    if pool != cand["pool"]:
        raise FigureInputError(f"{lvl_path}: pool_h2 {pool} is not the pool of {selected}")
    q = {k: float(need(lvl, f"qcal_{pool}_{k}", lvl_path)) for k in ("hi95", "hi975", "lo05", "lo025")}
    tol = 1e-12
    for k in keys:
        if (k.startswith("hi") and c[k] < q[k] - tol) or (k.startswith("lo") and c[k] > q[k] + tol):
            raise FigureInputError(f"critical value {k} = {c[k]} is inside the SDID floor {q[k]}")
    binding = [k for k in keys if close(c[k], q[k], 1e-12)]
    qtxt = ", ".join(f"q_cal for {CRIT_NAME[k]} = {fmt(q[k])}" for k in keys)
    if binding:
        names = [CRIT_NAME[k] for k in binding]
        sets = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
        bind_txt = f"here the floor sets {sets}" + (" (the others come from t or the quantile)"
                                                    if len(binding) < len(keys) else "")
    else:
        bind_txt = "here the floor does not bind: every critical value comes from t or the quantile"
    sentence = (f" Because the estimator is SDID, each critical value is also at least as far from "
                f"zero as the Monte Carlo floor q_cal of pool {pool} from run check-methods "
                f"(design.method C1): c_hi(p) = max(t_ν,p, decision-set quantile, q_cal,hi(p)) and "
                f"c_lo(p) = min(−t_ν,1−p, decision-set quantile, q_cal,lo(p)); {qtxt}; {bind_txt}. "
                "The floor was calibrated on synthetic panels with the pseudo-date windows, not the "
                "real ones, so it carries over to these intervals by assumption; it can only widen them.")
    return {"applies": 1, "pool": pool, "qcal": q, "binding": binding,
            "phrase": "the decision-set quantile and the SDID Monte Carlo floor as floors",
            "sentence": sentence}


def quarter_index(label: str) -> int:
    y, q = str(label).split("Q")
    return 4 * int(y) + int(q) - 1


def quarter_label(qi: int) -> str:
    return f"{qi // 4}Q{qi % 4 + 1}"


def fmt(x: float, spec: str = ".2f") -> str:
    """A number for a label or caption, with a true minus sign and no negative zero."""
    s = format(x, spec)
    if s.lstrip("-").strip("0.,") == "":
        s = s.lstrip("-")
    return s.replace("-", "−")


def mpl_setup():
    import matplotlib
    matplotlib.use("pdf")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
        "font.size": 8,
        "axes.titlesize": 8.5,
        "axes.labelsize": 8,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.5,
        "axes.linewidth": 0.6,
        "axes.edgecolor": INK,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "hatch.linewidth": 0.5,
        "svg.hashsalt": "ss-ca-fastfood-wage",
    })
    return plt


def save_pdf(fig, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # No creation date, so the same inputs give the same bytes.
    fig.savefig(path, format="pdf", bbox_inches="tight", pad_inches=0.02,
                metadata={"CreationDate": None, "ModDate": None})


def write_text(path: str | Path, text: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(text.rstrip() + "\n", encoding="utf-8")


def write_metrics(path: str | Path, metrics: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(metrics, indent=1, sort_keys=True) + "\n", encoding="utf-8")
