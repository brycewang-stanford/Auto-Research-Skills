"""Shared helpers for the figure and table scripts (code/fig_*.py, code/tab_*.py).

Rules (crew/agents/figures-ra.md): every number comes from a logged run's metrics file,
declared with --input; a table cell the paper quotes is written as the claim's macro
(paper/numbers.tex), and the script asserts that the macro's claim holds the same value
as the metric it shows. Nothing here computes a new result.
"""
from __future__ import annotations

import json
from pathlib import Path

from common import DATASETS, METHODS, write_metrics  # noqa: F401  (re-exported)

# One style and one palette for every figure (Okabe-Ito; checked for colour-vision
# deficiency separation). Grayscale readers get a second encoding: marker and line style.
METHOD_STYLE = {
    "lr": {"label": "Logistic regression (LR)", "color": "#0072B2", "marker": "o", "ls": "-"},
    "rf": {"label": "Random forest (RF)", "color": "#009E73", "marker": "s", "ls": "--"},
    "gbdt": {"label": "Gradient boosting (GBDT)", "color": "#D55E00", "marker": "^", "ls": ":"},
}
INK = "#222222"
MUTED = "#8a8a8a"
LIGHT = "#c8c8c8"
SMD = 0.05            # smallest meaningful difference on the r scale (hypotheses H1, H2)

# Reporting words required by design.method for per-dataset outcomes.
OUTCOME_WORDS = {
    "supported": "supported",
    "contradicted": "contradicted",
    "no meaningful difference": "no meaningful difference",
    "inconclusive": "no detectable difference (inconclusive)",
    "excluded (uninformative)": "excluded (uninformative)",
}


def outcome_words(label: str) -> str:
    return OUTCOME_WORDS.get(label, label)


def load_metrics(run_id: str) -> dict:
    """Metrics file a logged run wrote (runs/<id>/metrics.json)."""
    return json.loads(Path(f"runs/{run_id}/metrics.json").read_text(encoding="utf-8"))


def rho_key(rho: float) -> str:
    return f"rho{rho:g}"


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
        "xtick.color": INK,
        "ytick.color": INK,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "pdf.fonttype": 42,
        "svg.hashsalt": "cs-label-noise",
    })
    return plt


def save_pdf(fig, path: str) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    # No creation date, so the same inputs give the same bytes.
    fig.savefig(path, format="pdf", bbox_inches="tight", pad_inches=0.02,
                metadata={"CreationDate": None, "ModDate": None})


class Macros:
    """Look up the claim macro for a (run, metric) pair and check it against the value."""

    def __init__(self, claims_path: str = "claims.jsonl"):
        self.by_metric: dict[tuple[str, str], dict] = {}
        for line in Path(claims_path).read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            c = json.loads(line)
            if c.get("kind") != "result" or not c.get("macro") or "value" not in c:
                continue
            first = c["support"][0]
            self.by_metric.setdefault((first.get("run"), first.get("metric")), c)
        self.used = 0
        self.direct = 0

    def cell(self, run: str, metric: str, value, fmt: str = ".3f", math: bool = True,
             alt: tuple = ()) -> str:
        """LaTeX for one number: the claim's macro if one exists, else the formatted metric.

        `alt` lists further (run, metric) pairs that report the same quantity (for example
        A(0) in h-tests and in descriptives); a claim on one of them is used only if its value
        equals `value` exactly. A claim on (run, metric) itself must equal `value`, or this fails.
        """
        claim = self.by_metric.get((run, metric))
        if claim is not None and claim["value"] != value:
            raise AssertionError(f"claim {claim['id']} value {claim['value']!r} != {run}:{metric} {value!r}")
        if claim is None:
            for key in alt:
                c = self.by_metric.get(tuple(key))
                if c is not None and c["value"] == value:
                    claim = c
                    break
        if claim is not None:
            if format(value, claim.get("format") or fmt) != format(value, fmt):
                raise AssertionError(f"claim {claim['id']} format {claim.get('format')} differs from {fmt}")
            self.used += 1
            body = "\\" + claim["macro"]
        else:
            self.direct += 1
            body = format(value, fmt)
        return f"${body}$" if math else body


def tex_name(name: str) -> str:
    return name.replace("_", "\\_")


def write_tex(path: str, source: str, body: list[str]) -> None:
    """Write a LaTeX fragment (a tabular only; the Writer adds the float and caption)."""
    head = [f"% Generated by {source} from logged runs. Do not edit by hand; rerun the script.",
            "% Needs \\usepackage{booktabs,array} and \\input{numbers.tex} for the macros."]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(head + body) + "\n", encoding="utf-8")
