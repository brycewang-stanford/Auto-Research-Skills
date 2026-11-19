"""Sensitivity (b), run `sens-ncal`: plan.json design.method step 12(b). Verdict-neutral.

On adult, bank-marketing and electricity, for each seed: rebuild the main cell exactly (same
subsample, splits, preprocessing and base models; the base models' uncalibrated test Brier is
asserted equal to results/cells.csv, so the frozen models are the ones main scored), draw a
stratified 1,351-row subset of the calibration split with train_test_split(train_size=1351,
stratify, random_state=rs), refit isotonic on it through FrozenEstimator, and score the same
test split (ece_db uses debias children 9, 10, 11 for lr, rf, hgb). H2a and H2b categories are
recomputed with d_s = brier(model, isotonic on 1,351) - brier(model, none), and phoneme's main
cells (whose calibration split already has 1,351 rows), with the same rule and margins.

Outputs: results/sens_ncal_cells.csv (90 rows), results/sens_ncal_tests.csv,
results/preds/sens-ncal/<dataset>_s<seed>.npz (git-ignored), runs/sens-ncal/metrics.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

import analyze
import experiment as ex

N_CAL_SUB = 1351
NCAL_DATASETS = ("adult", "bank-marketing", "electricity")


def ncal_cell(d: int, s: int, X, y, num, cat) -> dict:
    cell = ex.prepare_cell(d, s, X, y, num, cat)
    st = cell["streams"]
    A_ca, y_ca, A_te, y_te = cell["A_ca"], cell["y_ca"], cell["A_te"], cell["y_te"]
    A_sub, _, y_sub, _ = train_test_split(A_ca, y_ca, train_size=N_CAL_SUB, stratify=y_ca, random_state=st["rs"])
    rows, preds, base_brier = [], {}, {}
    for m in ex.MODELS:
        base = cell["models"][m]
        p_none = base.predict_proba(A_te)[:, 1].copy()
        base_brier[m] = ex.brier(p_none, y_te)
        p_iso = ex.fit_calibrator(base, A_sub, y_sub, "isotonic").predict_proba(A_te)[:, 1]
        assert np.array_equal(base.predict_proba(A_te)[:, 1], p_none), "base model changed during calibration"
        rng = np.random.default_rng(st["debias"][ex.debias_index_ncal(m)])
        rows.append(dict(dataset=ex.DATASETS[d], seed=s, model=m, calibrator="isotonic_ncal1351",
                         **ex.score(p_iso, y_te, rng), n_cal_sub=len(y_sub), pos_cal_sub=int(y_sub.sum()),
                         n_test=len(y_te)))
        preds[f"p_{m}_isotonic_ncal1351"] = p_iso.astype(np.float64)
    return dict(rows=rows, preds=preds, y_test=y_te.astype(np.float64), base_brier=base_brier)


def worker(d: int, s: int) -> dict:
    from threadpoolctl import threadpool_limits
    with threadpool_limits(limits=1):
        X, y, num, cat = ex.load_study_dataset(ex.DATASETS[d])
        return ncal_cell(d, s, X, y, num, cat)


def main() -> None:
    from joblib import Parallel, delayed
    main_cells = pd.read_csv("results/cells.csv")
    jobs = [(ex.DATASETS.index(n), s) for n in NCAL_DATASETS for s in ex.SEEDS]
    out = Parallel(n_jobs=ex.N_JOBS)(delayed(worker)(d, s) for d, s in jobs)

    # the base models are those of main: uncalibrated test Brier must match results/cells.csv exactly
    for (d, s), o in zip(jobs, out):
        for m, b in o["base_brier"].items():
            ref = main_cells[(main_cells["dataset"] == ex.DATASETS[d]) & (main_cells["seed"] == s) &
                             (main_cells["model"] == m) & (main_cells["calibrator"] == "none")]["brier"]
            assert len(ref) == 1 and float(ref.iloc[0]) == b, f"{ex.DATASETS[d]} s{s} {m}: base model differs from main"
        save_path = ex.RESULTS / "preds" / "sens-ncal" / f"{ex.DATASETS[d]}_s{s}.npz"
        ex.save_preds(save_path, o["y_test"], o["preds"])
    rows = [r for o in out for r in o["rows"]]
    ncal = ex.write_cells(rows, ex.RESULTS / "sens_ncal_cells.csv",
                          columns=["dataset", "seed", "model", "calibrator", "brier", "logloss", "logloss_mach",
                                   "n_clip_low", "n_clip_high", "ece", "ece_bins", "ece_db", "auc", "n_cal_sub",
                                   "pos_cal_sub", "n_test"])
    assert len(ncal) == 90 and (ncal["n_cal_sub"] == N_CAL_SUB).all()

    # H2a / H2b recomputed: isotonic-on-1,351 arm for the three large datasets, main cells for phoneme
    sub_iso = ncal.assign(calibrator="isotonic")[["dataset", "seed", "model", "calibrator", "brier"]]
    none_arm = main_cells[main_cells["calibrator"] == "none"][["dataset", "seed", "model", "calibrator", "brier"]]
    phon_iso = main_cells[(main_cells["dataset"] == "phoneme") & (main_cells["calibrator"] == "isotonic")][
        ["dataset", "seed", "model", "calibrator", "brier"]]
    cells = pd.concat([sub_iso, none_arm, phon_iso], ignore_index=True)

    metrics: dict = {"n_rows": len(ncal), "n_cal_sub": N_CAL_SUB}
    table = []
    for hid in ("h2a", "h2b"):
        metric, treat, comp, sign, margin, _ = analyze.HYPOTHESES[hid]
        spec = (metric, treat, comp, sign, margin, "sensitivity (b): calibration n = 1,351 on all datasets")
        rows_h, verdict = analyze.test_hypothesis(cells, hid, spec=spec)
        table += rows_h
        metrics.update(analyze.flat_metrics(f"{hid}_ncal", rows_h, verdict))
    for name in NCAL_DATASETS:
        for m in ex.MODELS:
            sub = ncal[(ncal["dataset"] == name) & (ncal["model"] == m)]
            for met in ("brier", "logloss", "ece", "ece_db", "auc"):
                metrics[f"{ex.ds_key(name)}_{m}_isoncal_{met}_mean"] = float(sub[met].mean())
                metrics[f"{ex.ds_key(name)}_{m}_isoncal_{met}_sd"] = float(sub[met].std(ddof=1))
    pd.DataFrame(table).to_csv(ex.RESULTS / "sens_ncal_tests.csv", index=False, float_format="%.17g")
    outd = Path("runs/sens-ncal")
    outd.mkdir(parents=True, exist_ok=True)
    (outd / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    for hid in ("h2a", "h2b"):
        print(f"{hid} (n_cal=1,351): {metrics[f'{hid}_ncal_overall']}  " +
              ", ".join(f"{r['dataset']}={r['category']}" for r in table if r["hypothesis"] == hid))


if __name__ == "__main__":
    main()
