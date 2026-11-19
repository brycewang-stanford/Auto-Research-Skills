"""Hypothesis tests (run `h-tests`): plan.json design.method steps 9-10, and sensitivity (a).

Reads results/cells.csv. For each hypothesis and dataset: the 10 paired per-seed differences
d_s = treatment_s - comparison_s, their mean, SD (ddof=1), the plain paired t(9) 95% interval and
the category; then the k-of-4 overall verdict.

  H1  : ece(rf, none)       - ece(lr, none)     predicted d > 0, margin 0.005   (confirmatory)
  H2a : brier(rf, isotonic) - brier(rf, none)   predicted d < 0, margin 0.001   (confirmatory)
  H2b : brier(hgb, isotonic)- brier(hgb, none)  predicted d < 0, margin 0.001   (confirmatory)
  H1db: H1 on ece_db (Kumar et al. 2019, Def. G.3)                              (sensitivity a; never
        changes the H1 verdict)

Category codes: 0 no difference, 1 holds, 2 contradicted, 3 no detectable difference (inconclusive).
Overall codes:  0 no difference, 1 supported, 2 contradicted, 3 inconclusive.

Outputs: results/htests.csv (one row per hypothesis x dataset) and runs/h-tests/metrics.json.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

N_SEEDS = 10
T_CRIT = float(stats.t.ppf(0.975, N_SEEDS - 1))
assert abs(T_CRIT - 2.2621571628) < 1e-9, T_CRIT

DATASETS = ("adult", "bank-marketing", "electricity", "phoneme")
CATEGORY = {0: "no difference", 1: "holds", 2: "contradicted", 3: "no detectable difference (inconclusive)"}
OVERALL = {0: "no difference", 1: "supported", 2: "contradicted", 3: "inconclusive"}

# id: (metric, treatment (model, calibrator), comparison (model, calibrator), predicted sign, margin, role)
HYPOTHESES = {
    "h1": ("ece", ("rf", "none"), ("lr", "none"), +1, 0.005, "confirmatory"),
    "h2a": ("brier", ("rf", "isotonic"), ("rf", "none"), -1, 0.001, "confirmatory"),
    "h2b": ("brier", ("hgb", "isotonic"), ("hgb", "none"), -1, 0.001, "confirmatory"),
    "h1db": ("ece_db", ("rf", "none"), ("lr", "none"), +1, 0.005, "sensitivity (a): never changes H1"),
}


def ds_key(name: str) -> str:
    return name.replace("-", "_")


def paired_interval(d: np.ndarray) -> dict:
    """Mean, SD (ddof=1) and the plain paired t(n-1) 95% interval of the per-seed differences."""
    d = np.asarray(d, dtype=np.float64)
    assert len(d) == N_SEEDS, f"expected {N_SEEDS} paired differences, got {len(d)}"
    mean, sd = float(np.mean(d)), float(np.std(d, ddof=1))
    half = T_CRIT * sd / math.sqrt(len(d))
    return dict(mean=mean, sd=sd, lo=mean - half, hi=mean + half, n=len(d))


def categorize(lo: float, hi: float, margin: float, sign: int) -> int:
    """Categories in order of precedence (design.method step 10)."""
    if -margin <= lo and hi <= margin:
        return 0                                  # no difference
    if (sign > 0 and lo > 0) or (sign < 0 and hi < 0):
        return 1                                  # holds: wholly on the predicted side
    if (sign > 0 and hi < 0) or (sign < 0 and lo > 0):
        return 2                                  # contradicted: wholly on the other side
    return 3                                      # no detectable difference (inconclusive)


def overall(categories: list[int]) -> int:
    """k-of-4 rule over the datasets."""
    holds, contra, nodiff = (sum(c == k for c in categories) for k in (1, 2, 0))
    if holds >= 3 and contra == 0:
        return 1                                  # supported
    if contra >= 2:
        return 2                                  # contradicted
    if nodiff >= 3 and holds == 0 and contra == 0:
        return 0                                  # no difference
    return 3                                      # inconclusive


def paired_differences(cells: pd.DataFrame, dataset: str, metric: str, treat: tuple, comp: tuple) -> np.ndarray:
    """d_s = treatment_s - comparison_s on the same seed; both arms must cover seeds 0..9 exactly once."""
    def arm(model, cal):
        a = cells[(cells["dataset"] == dataset) & (cells["model"] == model) & (cells["calibrator"] == cal)]
        a = a.set_index("seed")[metric].sort_index()
        assert list(a.index) == list(range(N_SEEDS)), f"{dataset} {model}/{cal}: seeds {list(a.index)}"
        return a.to_numpy(dtype=np.float64)
    return arm(*treat) - arm(*comp)


def test_hypothesis(cells: pd.DataFrame, hid: str, spec=None, datasets=DATASETS) -> tuple[list[dict], int]:
    metric, treat, comp, sign, margin, role = spec or HYPOTHESES[hid]
    rows = []
    for name in datasets:
        iv = paired_interval(paired_differences(cells, name, metric, treat, comp))
        cat = categorize(iv["lo"], iv["hi"], margin, sign)
        rows.append(dict(hypothesis=hid, role=role, dataset=name, metric=metric,
                         treatment="/".join(treat), comparison="/".join(comp), predicted_sign=sign,
                         margin=margin, **iv, category_code=cat, category=CATEGORY[cat]))
    return rows, overall([r["category_code"] for r in rows])


def flat_metrics(prefix: str, rows: list[dict], verdict: int | None) -> dict:
    out = {}
    for r in rows:
        k = f"{prefix}_{ds_key(r['dataset'])}"
        out.update({f"{k}_mean": r["mean"], f"{k}_sd": r["sd"], f"{k}_lo": r["lo"], f"{k}_hi": r["hi"],
                    f"{k}_cat": r["category_code"]})
    if verdict is not None:
        cats = [r["category_code"] for r in rows]
        out.update({f"{prefix}_overall": OVERALL[verdict], f"{prefix}_overall_code": verdict,
                    f"{prefix}_n_holds": cats.count(1), f"{prefix}_n_contradicted": cats.count(2),
                    f"{prefix}_n_nodiff": cats.count(0), f"{prefix}_n_inconclusive": cats.count(3)})
    return out


def main() -> None:
    cells = pd.read_csv("results/cells.csv")
    assert len(cells) == 360, len(cells)
    table, metrics = [], {"t_crit": T_CRIT, "n_seeds": N_SEEDS}
    for hid in HYPOTHESES:
        rows, verdict = test_hypothesis(cells, hid)
        table += rows
        metrics.update(flat_metrics(hid, rows, verdict))
    pd.DataFrame(table).to_csv("results/htests.csv", index=False, float_format="%.17g")
    out = Path("runs/h-tests")
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    for hid in HYPOTHESES:
        print(f"{hid}: {metrics[f'{hid}_overall']}  " +
              ", ".join(f"{r['dataset']}={r['category']}" for r in table if r["hypothesis"] == hid))


if __name__ == "__main__":
    main()
