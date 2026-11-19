"""Sensitivity (c), run `sens-elec-time`: plan.json design.method step 12(c). Verdict-neutral.

Electricity only. For each seed s, streams from SeedSequence([20261119, 2, s, 1]) (the split child is
unused): the same stratified 20,000-row subsample rule, then the subsample sorted by original file
row index (the time order; the date column is not used) and split chronologically 50/25/25
(earliest half train, next quarter calibration, latest quarter test). Preprocessing, the three
models, Platt and isotonic and every metric exactly as in main (ece_db children 0..8). The number
of rows from the first 17,424 file rows (constant Victoria fill values) in each split is recorded.
H1, H2a and H2b differences and categories are reported for electricity only and are never
counted in the k-of-4 rule.

Outputs: results/sens_elec_time_cells.csv (90 rows), results/sens_elec_time_tests.csv,
results/preds/sens-elec-time/electricity_s<seed>.npz (git-ignored), runs/sens-elec-time/metrics.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import analyze
import experiment as ex

D_ELEC = ex.DATASETS.index("electricity")
VARIANT = 1


def chrono_cell(s: int, X, y, num, cat) -> dict:
    st = ex.seed_streams(D_ELEC, s, variant=VARIANT)
    Xs, ys = ex.subsample(X, y, st["sub_int"])
    (X_tr, y_tr), (X_ca, y_ca), (X_te, y_te) = ex.split_chronological(Xs, ys)
    ex.check_split_sizes(len(y_tr), len(y_ca))
    assert X_tr.index.max() < X_ca.index.min() and X_ca.index.max() < X_te.index.min(), "split not chronological"
    _, (A_tr, A_ca, A_te) = ex.preprocess(num, cat, X_tr, X_ca, X_te)
    models, book, _ = ex.fit_models(A_tr, y_tr, st["rs"])
    book.update(n_train=len(y_tr), n_cal=len(y_ca), n_test=len(y_te), pos_train=int(y_tr.sum()),
                pos_cal=int(y_ca.sum()), pos_test=int(y_te.sum()), width=int(A_tr.shape[1]),
                **dict(zip(("n_vicfill_train", "n_vicfill_cal", "n_vicfill_test"),
                           ex.vic_fill_counts(X_tr.index, X_ca.index, X_te.index))),
                first_row_train=int(X_tr.index.min()), first_row_cal=int(X_ca.index.min()),
                first_row_test=int(X_te.index.min()), last_row_test=int(X_te.index.max()))
    rows, preds = ex.score_all(models, A_ca, y_ca, A_te, y_te, st["debias"])
    return dict(rows=[dict(dataset="electricity", seed=s, **r, **book) for r in rows], preds=preds,
                y_test=y_te.astype(np.float64))


def worker(s: int) -> dict:
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        X, y, num, cat = ex.load_study_dataset("electricity")
        return chrono_cell(s, X, y, num, cat)


def main() -> None:
    from joblib import Parallel, delayed
    out = Parallel(n_jobs=ex.N_JOBS)(delayed(worker)(s) for s in ex.SEEDS)
    for s, o in zip(ex.SEEDS, out):
        ex.save_preds(ex.RESULTS / "preds" / "sens-elec-time" / f"electricity_s{s}.npz", o["y_test"], o["preds"])
    rows = [r for o in out for r in o["rows"]]
    cols = ex.CELL_COLUMNS + ["first_row_train", "first_row_cal", "first_row_test", "last_row_test"]
    cells = ex.write_cells(rows, ex.RESULTS / "sens_elec_time_cells.csv", columns=cols)
    assert len(cells) == 90

    metrics: dict = {"n_rows": len(cells)}
    table = []
    for hid in ("h1", "h2a", "h2b"):
        metric, treat, comp, sign, margin, _ = analyze.HYPOTHESES[hid]
        spec = (metric, treat, comp, sign, margin, "sensitivity (c): chronological split, electricity only")
        rows_h, _ = analyze.test_hypothesis(cells, hid, spec=spec, datasets=("electricity",))
        table += rows_h
        metrics.update(analyze.flat_metrics(f"{hid}_time", rows_h, None))   # no k-of-4 verdict
    per_seed = cells.groupby("seed").first()
    for col in ("n_vicfill_train", "n_vicfill_cal", "n_vicfill_test", "lr_converged", "width"):
        metrics[f"{col}_min"], metrics[f"{col}_max"] = int(per_seed[col].min()), int(per_seed[col].max())
    for m in ex.MODELS:
        for c in ex.CALIBRATORS:
            sub = cells[(cells["model"] == m) & (cells["calibrator"] == c)]
            for met in ("brier", "logloss", "ece", "ece_db", "auc"):
                metrics[f"electricity_time_{m}_{c}_{met}_mean"] = float(sub[met].mean())
                metrics[f"electricity_time_{m}_{c}_{met}_sd"] = float(sub[met].std(ddof=1))
    pd.DataFrame(table).to_csv(ex.RESULTS / "sens_elec_time_tests.csv", index=False, float_format="%.17g")
    outd = Path("runs/sens-elec-time")
    outd.mkdir(parents=True, exist_ok=True)
    (outd / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    for r in table:
        print(f"{r['hypothesis']} (chronological, electricity): {r['category']}  "
              f"[{r['lo']:.4f}, {r['hi']:.4f}]")


if __name__ == "__main__":
    main()
