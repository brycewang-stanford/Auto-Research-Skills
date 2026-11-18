"""check-learner-ports (analysis plan 0; plan.json design.check_learner_ports). Data-prep run, synthetic only.

Measures, before the design gate, how far each scikit-learn port in code/dml_plr.py is from the
R function called exactly as the authors call it (code/authors/ML_Functions.R, verbatim), with
the difference between two R seeds as the yardstick. Never reads net_tfa or e401: the only real
data are the nine covariates; Y and D are synthetic with a known effect of 9000.

Synthetic units u = 1..10, each from numpy.random.default_rng(SeedSequence([4011, u])), drawn in
this order: uniform(n) for D, standard_t(3, n) for the Y noise, permutation(n) for one random
2-fold partition (numpy.array_split: folds of 4,958 and 4,957 rows).
  D ~ Bernoulli(expit(-1.5 + 0.25 i + 0.4 db - 0.001 (age - 40)^2)), i = inc / 1e4
  Y = 9000 D + 1500 (age - 40) + 900 sign(i)|i|^1.5 + 3000 pira + 2000 hown + 600 (educ - 12) + 8000 t_3
Python port seeds: SeedSequence([4011, u, fold, learner index, nuisance]); R seeds A = 100000 + u,
B = 200000 + u (each plus the learner index inside the R script).

Writes runs/check-learner-ports/metrics.json (flat), runs/check-learner-ports/units.csv (per-unit
theta for every implementation) and the unit files and R predictions under
runs/check-learner-ports/units/.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from joblib import Parallel, delayed
from scipy.special import expit
from scipy.stats import norm

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dml_plr as P  # noqa: E402  (the learner functions the main runs use)

OUT = Path("runs/check-learner-ports")
UNITS_DIR = OUT / "units"
N_UNITS = 10
TRUE_THETA = 9000.0
AUTHORS_FILE = Path("code/authors/ML_Functions.R")
AUTHORS_BLOB = "4e90ed647607c8a9e05fff64af3b212e1f90eaed"  # VC2015/DMLonGitHub ff35d21e, ML_Functions.R
T_CRIT_9DF = 2.262
SPREAD_FACTOR = 1.75
FLOOR = 25.0
COR_MIN = 0.999


def git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def make_unit(X: pd.DataFrame, u: int) -> pd.DataFrame:
    rng = np.random.default_rng(np.random.SeedSequence([4011, u]))
    n = len(X)
    age, educ = X.age.to_numpy(float), X.educ.to_numpy(float)
    i = X.inc.to_numpy(float) / 1e4
    p = expit(-1.5 + 0.25 * i + 0.4 * X.db.to_numpy(float) - 0.001 * (age - 40) ** 2)
    d = (rng.random(n) < p).astype(float)
    t3 = rng.standard_t(3, n)
    y = (TRUE_THETA * d + 1500 * (age - 40) + 900 * np.sign(i) * np.abs(i) ** 1.5
         + 3000 * X.pira.to_numpy(float) + 2000 * X.hown.to_numpy(float) + 600 * (educ - 12) + 8000 * t3)
    fold = np.empty(n, dtype=int)
    for f, block in enumerate(np.array_split(rng.permutation(n), 2), start=1):
        fold[block] = f
    unit = pd.DataFrame({"y": y, "d": d})
    for c in P.COVARIATES:
        unit[c] = X[c].to_numpy()
    unit["fold"] = fold
    unit["row"] = np.arange(1, n + 1)
    unit["unit"] = u
    return unit


def run_r(unit_file: Path, seed: int, out_file: Path) -> tuple[str, float]:
    t0 = time.perf_counter()
    res = subprocess.run(["Rscript", "code/check_learner_ports.R", str(unit_file), str(seed), str(out_file)],
                         capture_output=True, text=True)
    if res.returncode != 0:
        raise RuntimeError(f"Rscript failed for {unit_file} seed {seed}:\n{res.stderr[-3000:]}")
    return str(out_file), time.perf_counter() - t0


def py_fit(u: int, fold: int, learner: str, nuisance: int, Xtr, ytr, Xte, c_y: float, c_d: float):
    from threadpoolctl import threadpool_limits
    seed = P.fit_seed(4011, u, fold, P.LEARNER_INDEX[learner], nuisance)
    t0 = time.perf_counter()
    with threadpool_limits(1):
        pred, info = P.fit_nuisance(learner, nuisance, Xtr, ytr, Xte, seed, lasso_c_y=c_y, lasso_c_d=c_d)
    return (u, fold, learner, nuisance), pred, info, time.perf_counter() - t0


def c_eff(lambda0: float, n: float, p: float, nuisance: str) -> float:
    q = norm.ppf(1 - (0.1 / np.log(n)) / (2 * p))
    return lambda0 / (2 * np.sqrt(n) * q) if nuisance == "y" else lambda0 / ((np.sqrt(n) / 2) * q)


def main() -> None:
    t_start = time.perf_counter()
    blob = git_blob_sha1(AUTHORS_FILE)
    if blob != AUTHORS_BLOB:
        sys.exit(f"ERROR: {AUTHORS_FILE} git blob {blob} != {AUTHORS_BLOB}; the copy is not verbatim")
    X = pd.read_csv("data/derived/sipp1991.csv", usecols=P.COVARIATES)[P.COVARIATES]
    if X.isna().any().any():
        sys.exit("ERROR: missing covariate values")
    UNITS_DIR.mkdir(parents=True, exist_ok=True)
    units = {u: make_unit(X, u) for u in range(1, N_UNITS + 1)}
    for u, df in units.items():
        df.to_csv(UNITS_DIR / f"unit{u:02d}.csv", index=False, float_format="%.17g")

    # ---------------------------------------------------------------- R: authors' calls, two seeds
    subprocess.run(["Rscript", "code/check_learner_ports.R", "--versions", str(UNITS_DIR / "r_versions.json")],
                   check=True)
    r_versions = json.loads((UNITS_DIR / "r_versions.json").read_text())
    r_jobs = [(u, tag, base + u) for u in units for tag, base in (("A", 100000), ("B", 200000))]
    r_out = Parallel(n_jobs=-1, backend="threading")(
        delayed(run_r)(UNITS_DIR / f"unit{u:02d}.csv", seed, UNITS_DIR / f"r_unit{u:02d}_{tag}.csv")
        for u, tag, seed in r_jobs)
    t_r = time.perf_counter() - t_start
    print(f"R calls done: {len(r_out)} calls, {t_r:.0f} s wall, {sum(t for _, t in r_out):.0f} s summed", flush=True)
    r_pred = {(u, tag): pd.read_csv(UNITS_DIR / f"r_unit{u:02d}_{tag}.csv") for u, tag, _ in r_jobs}

    # effective lasso penalty constants of the authors' call path (seed A; deterministic)
    lasso_rows = pd.concat([r_pred[(u, "A")].query("learner == 'lasso'") for u in units])
    cy = np.array([c_eff(r.lambda0_y, r.n_y, r.p_y, "y") for r in lasso_rows.itertuples()])
    cd = np.array([c_eff(r.lambda0_d, r.n_d, r.p_d, "d") for r in lasso_rows.itertuples()])
    assert np.ptp(cy) < 1e-9 and np.ptp(cd) < 1e-9, "effective c differs across fits"
    c_eff_y, c_eff_d = round(float(cy.mean()), 6), round(float(cd.mean()), 6)
    p_r = sorted(set(lasso_rows.p_y.astype(int)) | set(lasso_rows.p_d.astype(int)))
    print(f"lasso: c_eff_y = {c_eff_y}, c_eff_d = {c_eff_d}, R p = {p_r}", flush=True)

    # ---------------------------------------------------------------- Python ports
    Xraw = X.to_numpy(float)
    Xdict = P.dictionary(Xraw)
    jobs = []
    for u, df in units.items():
        yv, dv, fold = df.y.to_numpy(), df.d.to_numpy(), df.fold.to_numpy()
        for f in (1, 2):
            tr, te = fold != f, fold == f
            for learner in P.LEARNERS:
                Xm = Xdict if learner == "lasso" else Xraw
                for nuisance, target in ((0, yv), (1, dv)):
                    jobs.append(delayed(py_fit)(u, f, learner, nuisance, Xm[tr], target[tr], Xm[te], c_eff_y, c_eff_d))
    t_py0 = time.perf_counter()
    py_out = Parallel(n_jobs=-1, backend="loky")(jobs)
    t_py = time.perf_counter() - t_py0
    print(f"Python ports done: {len(py_out)} fits, {t_py:.0f} s wall, {sum(r[3] for r in py_out):.0f} s summed",
          flush=True)
    py_pred = {key: pred for key, pred, _, _ in py_out}
    py_info = {key: info for key, _, info, _ in py_out}

    # ---------------------------------------------------------------- theta per unit and implementation
    rows, cors = [], []
    for u, df in units.items():
        yv, dv, fold = df.y.to_numpy(), df.d.to_numpy(), df.fold.to_numpy()
        for learner in P.LEARNERS:
            l_py, m_py = np.empty(len(df)), np.empty(len(df))
            for f in (1, 2):
                te = fold == f
                l_py[te] = py_pred[(u, f, learner, 0)]
                m_py[te] = py_pred[(u, f, learner, 1)]
            impl = {"py": (l_py, m_py)}
            for tag in ("A", "B"):
                r = r_pred[(u, tag)].query("learner == @learner")
                l_r, m_r = np.full(len(df), np.nan), np.full(len(df), np.nan)
                l_r[r.row.to_numpy() - 1] = r.l_hat.to_numpy()
                m_r[r.row.to_numpy() - 1] = r.m_hat.to_numpy()
                assert np.isfinite(l_r).all() and np.isfinite(m_r).all(), (u, learner, tag)
                impl[tag] = (l_r, m_r)
            row = {"unit": u, "learner": learner}
            for tag, (l_hat, m_hat) in impl.items():
                th, sg = P.dml2_theta(yv, dv, l_hat, m_hat)
                row[f"theta_{tag}"] = th
                row[f"sigma_{tag}"] = sg
                row[f"rmse_l_{tag}"] = float(np.sqrt(np.mean((yv - l_hat) ** 2)))
                row[f"rmse_m_{tag}"] = float(np.sqrt(np.mean((dv - m_hat) ** 2)))
            row["cor_l_py_A"] = float(np.corrcoef(impl["py"][0], impl["A"][0])[0, 1])
            row["cor_m_py_A"] = float(np.corrcoef(impl["py"][1], impl["A"][1])[0, 1])
            row["cor_l_B_A"] = float(np.corrcoef(impl["B"][0], impl["A"][0])[0, 1])
            row["cor_m_B_A"] = float(np.corrcoef(impl["B"][1], impl["A"][1])[0, 1])
            if learner == "nnet":
                row["nnet_iter_py_y"] = int(np.median([py_info[(u, f, "nnet", 0)]["iter"] for f in (1, 2)]))
                row["nnet_iter_py_d"] = int(np.median([py_info[(u, f, "nnet", 1)]["iter"] for f in (1, 2)]))
            rows.append(row)
    per_unit = pd.DataFrame(rows)
    per_unit.to_csv(OUT / "units.csv", index=False, float_format="%.10g")

    # ---------------------------------------------------------------- metrics and pass rules
    m: dict = {"n_units": N_UNITS, "theta_true": TRUE_THETA, "train_size_min": int(min(
        (units[1].fold != f).sum() for f in (1, 2))),
        "lasso_c_eff_y": c_eff_y, "lasso_c_eff_d": c_eff_d, "lasso_p_r": int(p_r[0]) if len(p_r) == 1 else -1,
        "authors_ml_functions_blob": blob}
    for k, val in r_versions.items():
        m[f"{k}_version"] = val
    import sklearn
    m["sklearn_version"] = sklearn.__version__
    m["numpy_version"] = np.__version__
    for learner in P.LEARNERS:
        g = per_unit[per_unit.learner == learner]
        dpa = (g.theta_py - g.theta_A).to_numpy()
        dba = (g.theta_B - g.theta_A).to_numpy()
        L = learner
        m[f"theta_py_mean_{L}"] = float(g.theta_py.mean())
        m[f"theta_ra_mean_{L}"] = float(g.theta_A.mean())
        m[f"theta_rb_mean_{L}"] = float(g.theta_B.mean())
        m[f"shift_{L}"] = float(dpa.mean())
        m[f"shift_se_{L}"] = float(dpa.std(ddof=1) / np.sqrt(N_UNITS))
        m[f"rms_port_{L}"] = float(np.sqrt(np.mean(dpa ** 2)))
        m[f"rms_seed_{L}"] = float(np.sqrt(np.mean(dba ** 2)))
        m[f"max_abs_port_{L}"] = float(np.abs(dpa).max())
        m[f"cor_l_min_{L}"] = float(g.cor_l_py_A.min())
        m[f"cor_m_min_{L}"] = float(g.cor_m_py_A.min())
        m[f"cor_l_min_seed_{L}"] = float(g.cor_l_B_A.min())
        m[f"cor_m_min_seed_{L}"] = float(g.cor_m_B_A.min())
        for nm in ("l", "m"):
            m[f"rmse_{nm}_py_{L}"] = float(np.median(g[f"rmse_{nm}_py"]))
            m[f"rmse_{nm}_ra_{L}"] = float(np.median(g[f"rmse_{nm}_A"]))
        if L == "lasso":  # deterministic in R: rms_seed = 0
            loc = m[f"max_abs_port_{L}"] <= FLOOR
            spr = m[f"cor_l_min_{L}"] >= COR_MIN and m[f"cor_m_min_{L}"] >= COR_MIN
        else:
            loc = abs(m[f"shift_{L}"]) <= max(T_CRIT_9DF * m[f"shift_se_{L}"], FLOOR)
            spr = m[f"rms_port_{L}"] <= max(SPREAD_FACTOR * m[f"rms_seed_{L}"], FLOOR)
        m[f"location_ok_{L}"] = bool(loc)
        m[f"spread_ok_{L}"] = bool(spr)
        m[f"pass_{L}"] = bool(loc and spr)
    if "nnet_iter_py_y" in per_unit:
        g = per_unit[per_unit.learner == "nnet"]
        m["nnet_iter_med_py_y"] = float(np.median(g.nnet_iter_py_y))
        m["nnet_iter_med_py_d"] = float(np.median(g.nnet_iter_py_d))
    m["n_pass"] = int(sum(m[f"pass_{L}"] for L in P.LEARNERS))
    (OUT / "metrics.json").write_text(json.dumps(m, indent=2) + "\n")
    print(json.dumps(m, indent=2))
    print(f"wall time {time.perf_counter() - t_start:.0f} s (R phase {t_r:.0f} s, Python phase {t_py:.0f} s)")


if __name__ == "__main__":
    main()
