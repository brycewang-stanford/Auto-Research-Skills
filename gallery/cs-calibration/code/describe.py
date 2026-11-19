"""Descriptive results (run `describe`): plan.json design.method step 11. No verdicts.

Reads results/cells.csv and writes:
- results/describe_summary.csv  mean and SD over the 10 seeds for every (dataset, model, calibrator)
                                and metric (brier, logloss, logloss_mach, ece, ece_db, auc,
                                n_clip_low, n_clip_high, ece_bins)
- results/describe_paired.csv   paired t(9) intervals, labelled descriptive: Platt minus none and
                                isotonic minus Platt for every model and dataset on Brier, log-loss,
                                ECE and AUC; RF minus LR (no recalibration) on Brier and log-loss
- runs/describe/metrics.json     the same numbers as flat keys, plus LR convergence and HGB n_iter checks
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from analyze import DATASETS, N_SEEDS, ds_key, paired_differences, paired_interval

MODELS = ("lr", "rf", "hgb")
CALIBRATORS = ("none", "platt", "isotonic")
SUMMARY_METRICS = ("brier", "logloss", "logloss_mach", "ece", "ece_db", "auc", "n_clip_low", "n_clip_high",
                   "ece_bins")
CONTRAST_METRICS = ("brier", "logloss", "ece", "auc")

# name: (treatment calibrator, comparison calibrator) within one model
CAL_CONTRASTS = {"platt_minus_none": ("platt", "none"), "iso_minus_platt": ("isotonic", "platt")}


def describe(cells: pd.DataFrame) -> tuple[list[dict], list[dict], dict]:
    """Summary rows, descriptive paired intervals and flat metrics from the 360 main cells."""
    metrics: dict = {"n_seeds": N_SEEDS}

    summary = []
    for name in DATASETS:
        for m in MODELS:
            for c in CALIBRATORS:
                sub = cells[(cells["dataset"] == name) & (cells["model"] == m) & (cells["calibrator"] == c)]
                assert len(sub) == N_SEEDS
                for met in SUMMARY_METRICS:
                    mean, sd = float(sub[met].mean()), float(sub[met].std(ddof=1))
                    summary.append(dict(dataset=name, model=m, calibrator=c, metric=met, mean=mean, sd=sd,
                                        n_seeds=len(sub)))
                    key = f"{ds_key(name)}_{m}_{c}_{met}"
                    metrics[f"{key}_mean"], metrics[f"{key}_sd"] = mean, sd

    paired = []
    def add(name, label, met, treat, comp):
        iv = paired_interval(paired_differences(cells, name, met, treat, comp))
        paired.append(dict(dataset=name, contrast=label, metric=met, treatment="/".join(treat),
                           comparison="/".join(comp), **iv, label="descriptive (no verdict)"))
        key = f"{ds_key(name)}_{label}_{met}"
        metrics.update({f"{key}_mean": iv["mean"], f"{key}_lo": iv["lo"], f"{key}_hi": iv["hi"]})

    for name in DATASETS:
        for m in MODELS:
            for label, (ct, cc) in CAL_CONTRASTS.items():
                for met in CONTRAST_METRICS:
                    add(name, f"{m}_{label}", met, (m, ct), (m, cc))
        for met in ("brier", "logloss"):
            add(name, "rf_minus_lr_none", met, ("rf", "none"), ("lr", "none"))

    # convergence and procedure checks (one value per dataset x seed)
    per_cell = cells.groupby(["dataset", "seed"]).first()
    metrics["lr_nonconverged_cells"] = int((per_cell["lr_converged"] == 0).sum())
    metrics["lr_n_iter_max"] = int(per_cell["lr_n_iter"].max())
    metrics["hgb_n_iter_min"] = int(per_cell["hgb_n_iter"].min())
    metrics["hgb_n_iter_max"] = int(per_cell["hgb_n_iter"].max())
    for name in DATASETS:
        sub = per_cell.loc[name]
        metrics[f"{ds_key(name)}_lr_nonconverged"] = int((sub["lr_converged"] == 0).sum())
        # the one-hot width can vary across seeds (a rare level missing from a seed's training split)
        metrics[f"{ds_key(name)}_width_min"] = int(sub["width"].min())
        metrics[f"{ds_key(name)}_width_max"] = int(sub["width"].max())
    elec = per_cell.loc["electricity"]
    for split in ("train", "cal", "test"):
        col = f"n_vicfill_{split}"
        metrics[f"electricity_{col}_mean"] = float(elec[col].mean())
        metrics[f"electricity_{col}_min"] = int(elec[col].min())
        metrics[f"electricity_{col}_max"] = int(elec[col].max())

    return summary, paired, metrics


def main() -> None:
    cells = pd.read_csv("results/cells.csv")
    assert len(cells) == 360, len(cells)
    summary, paired, metrics = describe(cells)
    pd.DataFrame(summary).to_csv("results/describe_summary.csv", index=False, float_format="%.17g")
    pd.DataFrame(paired).to_csv("results/describe_paired.csv", index=False, float_format="%.17g")
    out = Path("runs/describe")
    out.mkdir(parents=True, exist_ok=True)
    (out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    print(f"{len(summary)} summary rows, {len(paired)} descriptive intervals, {len(metrics)} metrics")


if __name__ == "__main__":
    main()
