"""Shared helpers for the figure scripts (code/fig_event.py, fig_select.py, fig_placebo.py).

Rules (crew/agents/figures-ra.md): every plotted number comes from a file a logged run wrote
(runs/<id>/...), declared with --input when the figure run is made; nothing here reads
claims.jsonl, data/raw or data/derived, and nothing estimates anything. The figure scripts only
redraw run outputs, check that those outputs agree with each other, and write a caption file
whose run-dependent parts (candidate, pool, outcome, J, nu) are printed from the same outputs.

Units: every estimate in these runs is a difference of logs. Figures show 100 x log points
(close to percent for small values); the caption says so.

Import order: code/select.py shadows the standard-library module 'select', which matplotlib
reaches through subprocess -> selectors. Each figure script therefore loads the standard module
before code/ is on sys.path (the same prologue as the run scripts); this module must be imported
after that prologue.
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
