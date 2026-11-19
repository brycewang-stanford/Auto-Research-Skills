"""Shared helpers for the figure and table scripts (code/fig_*.py, code/tab_*.py).

Rules (crew/agents/figures-ra.md): every number comes from a file a logged run wrote, declared
with --input (runs/<id>/metrics.json, or the git-ignored test predictions under results/preds/
that run `main` wrote); nothing is typed by hand and nothing new is estimated. Design constants
(margins, predicted signs, category words, the 15-bin rule) are imported from the code the
runs executed (analyze.py, experiment.py), not retyped.

Macros. A table cell that the paper also quotes is written as the claim's macro from
paper/numbers.tex. The scripts do not read claims.jsonl (it is not a run output, and any later
claim edit would invalidate the run). They name the macro by the claims' fixed convention for the
(run, metric) pair they read (macro_for below) and list every macro they used with its
(run, metric) source, and every cell they wrote as a plain number with its source, in comments at
the end of the fragment. A separate check against claims.jsonl (paper/figures/CAPTIONS.md, "Macro
check") confirms that each listed macro's claim is backed by exactly that (run, metric) with that
value, and that no plain-number cell has a claim.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

DATASETS = ("adult", "bank-marketing", "electricity", "phoneme")
MODELS = ("lr", "rf", "hgb")
CALIBRATORS = ("none", "platt", "isotonic")
NAME = {"adult": "adult", "bank-marketing": "bank-marketing", "electricity": "electricity",
        "phoneme": "phoneme"}
MODEL_TEX = {"lr": "LR", "rf": "RF", "hgb": "HGB"}
CAL_TEX = {"none": "none", "platt": "Platt", "isotonic": "isotonic"}

# Macro name parts (the claims' convention).
M_DS = {"adult": "Adult", "bank_marketing": "Bank", "electricity": "Elec", "phoneme": "Phoneme"}
M_MODEL = {"lr": "Lr", "rf": "Rf", "hgb": "Hgb"}
M_CAL = {"none": "None", "platt": "Platt", "isotonic": "Iso"}
M_METRIC = {"ece": "Ece", "ece_db": "EceDb", "brier": "Brier", "logloss": "Logloss", "auc": "Auc",
            "ece_bins": "EceBins"}
M_HYP = {"h1": "HOne", "h2a": "HTwoA", "h2b": "HTwoB", "h1db": "HOneDb"}
M_STAT = {"mean": "Mean", "lo": "Lo", "hi": "Hi", "cat": "Cat"}

# One palette for every figure (Okabe-Ito, separable under colour-vision deficiency). Every
# encoding that matters also has a grayscale cue (marker shape and fill, line style).
INK = "#222222"
MUTED = "#8a8a8a"
LIGHT = "#e3e3e3"
BLUE = "#0072B2"
VERMILLION = "#D55E00"


def ds_key(name: str) -> str:
    return name.replace("-", "_")


def load_json(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_metrics(run_id: str) -> dict:
    """Metrics file a logged run wrote (runs/<id>/metrics.json)."""
    return load_json(f"runs/{run_id}/metrics.json")


def write_metrics(path: str, metrics: dict) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def finite(*xs) -> bool:
    return all(isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)
               for x in xs)


def _cell_parts(rest: str):
    """'<ds>_<model>_<cal>_<metric>_<mean|sd>' -> parts, or None."""
    for ds in M_DS:
        if not rest.startswith(ds + "_"):
            continue
        tail = rest[len(ds) + 1:]
        for model in M_MODEL:
            for cal in M_CAL:
                pre = f"{model}_{cal}_"
                if tail.startswith(pre):
                    metric_stat = tail[len(pre):]
                    for stat in ("mean", "sd"):
                        if metric_stat.endswith("_" + stat):
                            metric = metric_stat[: -len(stat) - 1]
                            if metric in M_METRIC:
                                return ds, model, cal, metric, stat
    return None


def macro_for(run: str, metric: str) -> str | None:
    """The claim macro the claims' convention gives to (run, metric), or None if the convention
    gives none. Whether a claim with that macro exists is checked separately (CAPTIONS.md)."""
    if run in ("h-tests", "sens-ncal", "sens-elec-time"):
        for hyp, mh in M_HYP.items():
            for infix, mi in (("", ""), ("_ncal", "Ncal"), ("_time", "Time")):
                pre = f"{hyp}{infix}_"
                if not metric.startswith(pre):
                    continue
                rest = metric[len(pre):]
                if rest == "overall_code":
                    return f"{mh}{mi}OverallCode"
                for ds, md in M_DS.items():
                    for stat, ms in M_STAT.items():
                        if rest == f"{ds}_{stat}":
                            return f"{mh}{mi}{md}{ms}"
    if run == "describe":
        parts = _cell_parts(metric)
        if parts:
            ds, model, cal, met, stat = parts
            return M_DS[ds] + M_MODEL[model] + M_CAL[cal] + M_METRIC[met] + ("Sd" if stat == "sd" else "")
    if run == "sens-elec-time" and metric.startswith("electricity_time_"):
        parts = _cell_parts("electricity_" + metric[len("electricity_time_"):])
        if parts:
            _, model, cal, met, stat = parts
            return "ElecTime" + M_MODEL[model] + M_CAL[cal] + M_METRIC[met] + ("Sd" if stat == "sd" else "")
    return None


class Cells:
    """Write numbers into a table as claim macros (quoted) or plain numbers (not quoted), and
    remember the source of each."""

    def __init__(self, metrics_by_run: dict[str, dict]) -> None:
        self.M = metrics_by_run
        self.macros: dict[str, str] = {}
        self.raw: list[str] = []
        self.words: list[str] = []
        self.values: list[float] = []

    def value(self, run: str, metric: str):
        v = self.M[run][metric]
        if not finite(v):
            raise ValueError(f"{run}:{metric} is not a finite number: {v!r}")
        self.values.append(float(v))
        return v

    def macro(self, run: str, metric: str) -> str:
        """A quoted number: the claim's macro, in math mode so a minus sign is a minus."""
        self.value(run, metric)
        name = macro_for(run, metric)
        if name is None:
            raise KeyError(f"no macro convention for {run}:{metric}")
        src = f"{run}:{metric}"
        if self.macros.setdefault(name, src) != src:
            raise AssertionError(f"macro {name} used for {self.macros[name]} and {src}")
        return f"$\\{name}$"

    def plain(self, run: str, metric: str, fmt: str) -> str:
        """A number no claim quotes, formatted from the run's metric."""
        v = self.value(run, metric)
        self.raw.append(f"{run}:{metric}:{fmt}")
        return "$" + format(v, fmt) + "$"

    def word(self, run: str, metric: str) -> int:
        """A category or verdict code, printed as its word (the claim's text gives the same word
        for the code its macro holds)."""
        v = self.value(run, metric)
        if v != int(v):
            raise ValueError(f"{run}:{metric} is not an integer code: {v!r}")
        self.words.append(f"{run}:{metric}")
        return int(v)

    def footer(self) -> list[str]:
        lines = ["% Macros used (macro = run:metric of the claim's first support):"]
        lines += [f"%   \\{m} = {s}" for m, s in sorted(self.macros.items())]
        lines.append("% Plain numbers (run:metric:format; no claim quotes them):")
        lines += [f"%   {r}" for r in self.raw]
        if self.words:
            lines.append("% Codes printed as words (run:metric):")
            lines += [f"%   {w}" for w in self.words]
        return lines


def write_tex(path: str, source: str, body: list[str], footer: list[str]) -> None:
    """Write a LaTeX fragment (a bare tabular; the Writer adds the float and caption)."""
    head = [f"% Generated by {source} from logged runs. Do not edit by hand; rerun the script.",
            "% Needs \\usepackage{booktabs} and \\input{numbers.tex} for the macros."]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(head + body + footer) + "\n", encoding="utf-8")


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
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
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
        "axes.unicode_minus": True,
    })
    return plt


def save_pdf(fig, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # No creation date, so the same inputs give the same bytes.
    fig.savefig(path, format="pdf", bbox_inches="tight", pad_inches=0.02,
                metadata={"CreationDate": None, "ModDate": None})
