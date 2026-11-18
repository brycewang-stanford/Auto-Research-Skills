"""Decision tests, ablation tests and descriptives (plan.json design.method STATISTICS).

    --test main      run h-tests      H1 (D = r_GBDT - r_RF) and H2 (D1 = r_LR - r_GBDT, D2 = r_LR - r_RF)
    --test noes      run abl-noes     A1: Delta = D_main - D_noES, D_noES = r_GBDT-noES - r_RF
    --test cleanval  run abl-cleanval A2: Delta, Delta1, Delta2 with rho=0.4 selected on clean validation labels
    --test half      run abl-budget   A3: Delta, Delta1, Delta2 with the best of the first 10 candidates
    --describe       run descriptives accuracy table, drops, rankings, tuned hyperparameters, diagnostics

Everything is per dataset and never pooled. J = 10 seeds. For method k on a dataset:
A(rho) = mean over seeds of clean-test accuracy, m = mean over seeds of the test majority
rate, h = A(0) - m, drop = A(0) - A(0.4), r = drop / h (from seed means, never per seed).
Decision interval for a contrast D = r_a - r_b: per-seed linearized values
l_ks = [(a0_ks - a4_ks) - r_k (a0_ks - m_s)] / h_k, u_s = l_as - l_bs, S = SD(u, ddof=1),
D +/- t_{0.975,9} sqrt(c) S with c = 1/J + n_te/n_tr on breast_cancer and credit-g
(Nadeau-Bengio) and c = 1/J on adult and covtype. The seed bootstrap is descriptive only.
Exclusion is read from results/exclusion.json and never recomputed here.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from fractions import Fraction
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (BOOT_SEED, DATASETS, METHODS, N_BOOT, NB_CORRECTED, RESULTS, RHOS, SEEDS,  # noqa: E402
                    SIZES, exact_mean, rho_key, write_metrics)

J = len(SEEDS)
TCRIT = float(stats.t.ppf(0.975, J - 1))
SMD_R = 0.05        # smallest meaningful difference in r
SMD_DROP = 0.01     # ... and in the absolute drops (1 accuracy point), same direction
SMD_R_X, SMD_DROP_X = Fraction(5, 100), Fraction(1, 100)   # exact versions used in every comparison (code-r1 F1)
H_FLOOR = 0.01      # unstable denominator: lower 95% bound of h below 1 point
BOOT_IDX = np.random.default_rng(BOOT_SEED).integers(0, J, size=(N_BOOT, J))   # shared by every contrast
UNSTABLE = "inconclusive (unstable denominator)"
EXCLUDED = "excluded (uninformative)"


def cfactor(name: str) -> float:
    n_tr, n_te = SIZES[name]
    return 1.0 / J + (n_te / n_tr if name in NB_CORRECTED else 0.0)


# ------------------------------------------------------------------ data access

def load_main() -> pd.DataFrame:
    cells = pd.concat([pd.read_csv(RESULTS / "cells_rho0.csv"), pd.read_csv(RESULTS / "cells_noisy.csv")],
                      ignore_index=True)
    assert set(cells["variant"]) == {"main"}
    return cells


def seed_vector(cells: pd.DataFrame, name: str, method: str, rho: float, column: str = "test_acc") -> np.ndarray:
    sel = cells[(cells["dataset"] == name) & (cells["method"] == method) & (cells["rho"] == rho)].sort_values("seed")
    assert sel["seed"].tolist() == list(SEEDS), (name, method, rho, sel["seed"].tolist())
    return sel[column].to_numpy(dtype=float)


def majority_vector(cells: pd.DataFrame, name: str) -> np.ndarray:
    sel = cells[(cells["dataset"] == name) & (cells["rho"] == 0.0)]
    per_seed = sel.groupby("seed")["majority_rate"].agg(["min", "max"])
    assert (per_seed["min"] == per_seed["max"]).all(), "test split differs across methods"
    assert per_seed.index.tolist() == list(SEEDS)
    return per_seed["min"].to_numpy(dtype=float)


def read_exclusion() -> dict:
    return json.loads((RESULTS / "exclusion.json").read_text(encoding="utf-8"))


# ------------------------------------------------------------------ statistics

def ratio(a0: np.ndarray, a4: np.ndarray, m: np.ndarray, n: int) -> dict:
    """Seed means are computed exactly from test-set counts out of n (code-r1 F1); floats are reported."""
    A0x, A4x, Mx = exact_mean(a0, n), exact_mean(a4, n), exact_mean(m, n)
    hx, dropx = A0x - Mx, A0x - A4x
    rx = dropx / hx if hx != 0 else None
    A0, A4, h, drop = float(A0x), float(A4x), float(hx), float(dropx)
    r = float(rx) if rx is not None else math.nan
    lin = ((a0 - a4) - r * (a0 - m)) / h          # first-order influence of seed s on r
    return {"A0": A0, "A4": A4, "h": h, "drop": drop, "r": r, "lin": lin, "a0": a0, "a4": a4, "m": m,
            "hx": hx, "dropx": dropx, "rx": rx}


def t_interval(est: float, per_seed: np.ndarray, c: float) -> dict:
    S = float(np.std(per_seed, ddof=1))
    half = TCRIT * math.sqrt(c) * S
    return {"est": est, "S": S, "half": half, "lo": est - half, "hi": est + half}


def headroom_check(part: dict, c: float) -> dict:
    x = part["a0"] - part["m"]
    iv = t_interval(float(x.mean()), x, c)
    iv["stable"] = iv["lo"] >= H_FLOOR
    return iv


def boot_r(part: dict) -> np.ndarray:
    a0, a4, m = part["a0"][BOOT_IDX].mean(1), part["a4"][BOOT_IDX].mean(1), part["m"][BOOT_IDX].mean(1)
    with np.errstate(divide="ignore", invalid="ignore"):
        return (a0 - a4) / (a0 - m)


def boot_pct(values: np.ndarray) -> tuple[float, float, int]:
    finite = np.isfinite(values)
    lo, hi = np.percentile(values[finite], [2.5, 97.5]) if finite.any() else (math.nan, math.nan)
    return float(lo), float(hi), int((~finite).sum())


def contrast(pa: dict, pb: dict, c: float) -> dict:
    estx = pa["rx"] - pb["rx"]
    u = pa["lin"] - pb["lin"]
    iv = t_interval(float(estx), u, c)
    iv["estx"] = estx
    iv["u"] = u
    iv["ddropx"] = pa["dropx"] - pb["dropx"]
    iv["ddrop"] = float(iv["ddropx"])
    iv["boot_lo"], iv["boot_hi"], iv["boot_nonfinite"] = boot_pct(boot_r(pa) - boot_r(pb))
    return iv


def outcome_h1(iv: dict) -> str:
    """D > 0 is the hypothesised direction (GBDT loses the larger share)."""
    if iv["lo"] > 0 and iv["estx"] >= SMD_R_X and iv["ddropx"] >= SMD_DROP_X:
        return "supported"
    if iv["hi"] < 0 and iv["estx"] <= -SMD_R_X and iv["ddropx"] <= -SMD_DROP_X:
        return "contradicted"
    if iv["lo"] > -SMD_R and iv["hi"] < SMD_R:
        return "no meaningful difference"
    return "inconclusive"


def outcome_h2(ivs: list[dict]) -> str:
    """D1, D2 < 0 is the hypothesised direction (LR loses the smallest share)."""
    if all(iv["hi"] < 0 and iv["estx"] <= -SMD_R_X and iv["ddropx"] <= -SMD_DROP_X for iv in ivs):
        return "supported"
    if any(iv["lo"] > 0 and iv["estx"] >= SMD_R_X and iv["ddropx"] >= SMD_DROP_X for iv in ivs):
        return "contradicted"
    if all(iv["lo"] > -SMD_R and iv["hi"] < SMD_R for iv in ivs):
        return "no meaningful difference"
    return "inconclusive"


def overall(outcomes: dict[str, str], informative: list[str]) -> dict:
    n = len(informative)
    got = [outcomes[d] for d in informative]
    ns, nc = got.count("supported"), got.count("contradicted")
    need = max(2, math.ceil(0.75 * n))
    if n == 0:
        verdict = "not testable"
    elif ns >= need and nc == 0:
        verdict = "supported"
    elif nc >= n / 2:
        verdict = "contradicted"
    else:
        verdict = "inconclusive"
    return {"n_informative": n, "n_supported": ns, "n_contradicted": nc,
            "n_no_meaningful_difference": got.count("no meaningful difference"),
            "n_inconclusive": got.count("inconclusive"), "n_unstable": got.count(UNSTABLE),
            "support_needed": need, "verdict": verdict}


def put_iv(metrics: dict, prefix: str, iv: dict, boot: bool = True) -> None:
    for key in ("est", "S", "half", "lo", "hi", "ddrop"):
        if key in iv:
            metrics[f"{prefix}.{'value' if key == 'est' else key}"] = iv[key]
    if boot and "boot_lo" in iv:
        metrics[f"{prefix}.boot_lo"] = iv["boot_lo"]
        metrics[f"{prefix}.boot_hi"] = iv["boot_hi"]
        metrics[f"{prefix}.boot_nonfinite"] = iv["boot_nonfinite"]


def put_ratio(metrics: dict, prefix: str, part: dict, hc: dict) -> None:
    for key in ("A0", "A4", "h", "drop", "r"):
        metrics[f"{prefix}.{key}"] = part[key]
    metrics[f"{prefix}.h_lo"] = hc["lo"]
    metrics[f"{prefix}.h_hi"] = hc["hi"]
    metrics[f"{prefix}.h_stable"] = int(hc["stable"])


def strip(obj):
    """JSON-safe copy of nested results (drops per-seed arrays)."""
    if isinstance(obj, dict):
        return {k: strip(v) for k, v in obj.items() if not isinstance(v, np.ndarray)}
    if isinstance(obj, (list, tuple)):
        return [strip(v) for v in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    return obj


# ------------------------------------------------------------------ main tests

def main_parts(cells: pd.DataFrame, name: str, column: str = "test_acc", methods=METHODS) -> dict:
    m = majority_vector(cells, name)
    n = SIZES[name][1]
    return {k: ratio(seed_vector(cells, name, k, 0.0, column), seed_vector(cells, name, k, 0.4, column), m, n)
            for k in methods}


def test_main(metrics: dict, detail: dict) -> None:
    cells = load_main()
    excl = read_exclusion()
    out_h1, out_h2 = {}, {}
    metrics["tcrit"] = TCRIT
    for name in DATASETS:
        c = cfactor(name)
        parts = main_parts(cells, name)
        hcs = {k: headroom_check(parts[k], c) for k in METHODS}
        metrics[f"{name}.c"] = c
        metrics[f"{name}.m"] = float(exact_mean(parts["lr"]["m"], SIZES[name][1]))
        for k in METHODS:
            put_ratio(metrics, f"{name}.{k}", parts[k], hcs[k])
        # H1
        iv = contrast(parts["gbdt"], parts["rf"], c)
        res = outcome_h1(iv)
        if not (hcs["gbdt"]["stable"] and hcs["rf"]["stable"]):
            res = UNSTABLE
        if name not in excl["informative_h1"]:
            res = EXCLUDED
        out_h1[name] = res
        put_iv(metrics, f"{name}.H1.D", iv)
        metrics[f"{name}.H1.outcome"] = res
        metrics[f"{name}.H1.informative"] = int(name in excl["informative_h1"])
        # H2
        iv1 = contrast(parts["lr"], parts["gbdt"], c)
        iv2 = contrast(parts["lr"], parts["rf"], c)
        res2 = outcome_h2([iv1, iv2])
        if not all(hcs[k]["stable"] for k in METHODS):
            res2 = UNSTABLE
        if name not in excl["informative_h2"]:
            res2 = EXCLUDED
        out_h2[name] = res2
        put_iv(metrics, f"{name}.H2.D1", iv1)
        put_iv(metrics, f"{name}.H2.D2", iv2)
        metrics[f"{name}.H2.outcome"] = res2
        metrics[f"{name}.H2.informative"] = int(name in excl["informative_h2"])
        detail[name] = {"c": c, "parts": parts, "headroom": hcs, "H1": {"D": iv, "outcome": res},
                        "H2": {"D1": iv1, "D2": iv2, "outcome": res2}}
    for hyp, outs, inf in (("H1", out_h1, excl["informative_h1"]), ("H2", out_h2, excl["informative_h2"])):
        ov = overall(outs, inf)
        for key, value in ov.items():
            metrics[f"{hyp}.{key}"] = value
        detail[hyp] = ov


# ------------------------------------------------------------------ ablations

def ablation_status(delta: dict, informative: bool, stable: bool) -> str:
    if not informative:
        return EXCLUDED
    if not stable:
        return UNSTABLE
    excludes_zero = delta["lo"] > 0 or delta["hi"] < 0
    return "attributed" if excludes_zero and abs(delta["estx"]) >= SMD_R_X else "not attributed"


def delta_iv(main_iv: dict, abl_iv: dict, c: float) -> dict:
    estx = main_iv["estx"] - abl_iv["estx"]
    iv = t_interval(float(estx), main_iv["u"] - abl_iv["u"], c)
    iv["estx"] = estx
    return iv


def acc_metrics(metrics: dict, prefix: str, values: np.ndarray) -> None:
    metrics[f"{prefix}.acc_mean"] = float(values.mean())
    metrics[f"{prefix}.acc_sd"] = float(np.std(values, ddof=1))
    metrics[f"{prefix}.n_seeds"] = int(len(values))
    for s, v in enumerate(values):
        metrics[f"{prefix}.acc.s{s}"] = float(v)


def run_ablation(kind: str, metrics: dict, detail: dict) -> None:
    cells = load_main()
    excl = read_exclusion()
    tag = {"noes": "A1", "cleanval": "A2", "half": "A3"}[kind]
    if kind == "noes":
        abl = pd.read_csv(RESULTS / "cells_noes.csv")
        assert set(abl["variant"]) == {"gbdt_noes"} and set(abl["rho"]) == {0.0, 0.4}
    elif kind == "cleanval":
        abl = pd.read_csv(RESULTS / "cells_cleanval.csv")
        assert set(abl["variant"]) == {"cleanval"} and set(abl["rho"]) == {0.4}
    metrics["tcrit"] = TCRIT
    for name in DATASETS:
        c = cfactor(name)
        parts = main_parts(cells, name)
        m = parts["lr"]["m"]
        hc_main = {k: headroom_check(parts[k], c) for k in METHODS}
        d_h1 = contrast(parts["gbdt"], parts["rf"], c)
        if kind == "noes":
            a0 = seed_vector(abl, name, "gbdt_noes", 0.0)
            a4 = seed_vector(abl, name, "gbdt_noes", 0.4)
            pn = ratio(a0, a4, m, SIZES[name][1])
            hcn = headroom_check(pn, c)
            acc_metrics(metrics, f"{name}.gbdt_noes.rho0", a0)
            acc_metrics(metrics, f"{name}.gbdt_noes.rho0.4", a4)
            put_ratio(metrics, f"{name}.gbdt_noes", pn, hcn)
            metrics[f"{name}.gbdt_noes.n_iter_median.rho0"] = float(
                abl[(abl["dataset"] == name) & (abl["rho"] == 0.0)]["n_iter"].median())
            metrics[f"{name}.gbdt_noes.n_iter_median.rho0.4"] = float(
                abl[(abl["dataset"] == name) & (abl["rho"] == 0.4)]["n_iter"].median())
            ab = contrast(pn, parts["rf"], c)
            dl = delta_iv(d_h1, ab, c)
            stable_abl = hcn["stable"]
            stable = stable_abl and hc_main["gbdt"]["stable"] and hc_main["rf"]["stable"]
            st = ablation_status(dl, name in excl["informative_h1"], stable)
            put_iv(metrics, f"{name}.{tag}.D_main", d_h1)
            put_iv(metrics, f"{name}.{tag}.D_abl", ab)
            put_iv(metrics, f"{name}.{tag}.Delta", dl, boot=False)
            metrics[f"{name}.{tag}.abl_denominator_stable"] = int(stable_abl)
            metrics[f"{name}.{tag}.Delta.status"] = st
            detail[name] = {"abl_parts": {"gbdt_noes": pn}, "headroom_abl": hcn, "D_main": d_h1,
                            "D_abl": ab, "Delta": dl, "status": st}
            continue
        # A2 and A3: H1 contrast and both H2 contrasts
        if kind == "cleanval":
            ap = {k: ratio(parts[k]["a0"], seed_vector(abl, name, k, 0.4), m, SIZES[name][1]) for k in METHODS}
            hca = hc_main                         # same rho=0 accuracies as main
            for k in METHODS:
                acc_metrics(metrics, f"{name}.{k}.cleanval.rho0.4", ap[k]["a4"])
                sel = abl[(abl["dataset"] == name) & (abl["method"] == k)]
                metrics[f"{name}.{k}.cleanval.val_acc_clean_mean"] = float(sel["val_acc_clean"].mean())
                metrics[f"{name}.{k}.cleanval.val_acc_noisy_mean"] = float(sel["val_acc_noisy"].mean())
                metrics[f"{name}.{k}.cleanval.r"] = ap[k]["r"]
                metrics[f"{name}.{k}.cleanval.drop"] = ap[k]["drop"]
        else:
            ap = main_parts(cells, name, column="test_acc_half")
            hca = {k: headroom_check(ap[k], c) for k in METHODS}
            for k in METHODS:
                acc_metrics(metrics, f"{name}.{k}.half.rho0", ap[k]["a0"])
                acc_metrics(metrics, f"{name}.{k}.half.rho0.4", ap[k]["a4"])
                put_ratio(metrics, f"{name}.{k}.half", ap[k], hca[k])
        abl_stable = all(hca[k]["stable"] for k in METHODS)
        metrics[f"{name}.{tag}.abl_denominators_stable"] = int(abl_stable)
        rows = {}
        for label, (a, b), hyp in (("Delta", ("gbdt", "rf"), "informative_h1"),
                                   ("Delta1", ("lr", "gbdt"), "informative_h2"),
                                   ("Delta2", ("lr", "rf"), "informative_h2")):
            dm = contrast(parts[a], parts[b], c)
            da = contrast(ap[a], ap[b], c)
            dl = delta_iv(dm, da, c)
            stable = all(hc_main[k]["stable"] and hca[k]["stable"] for k in (a, b))
            st = ablation_status(dl, name in excl[hyp], stable)
            dname = {"Delta": "D", "Delta1": "D1", "Delta2": "D2"}[label]
            put_iv(metrics, f"{name}.{tag}.{dname}_main", dm)
            put_iv(metrics, f"{name}.{tag}.{dname}_abl", da)
            put_iv(metrics, f"{name}.{tag}.{label}", dl, boot=False)
            metrics[f"{name}.{tag}.{label}.status"] = st
            rows[label] = {"D_main": dm, "D_abl": da, "Delta": dl, "status": st}
        detail[name] = {"abl_parts": ap, "contrasts": rows}


# ------------------------------------------------------------------ descriptives

def n_flip_ref(rho: float, n: int) -> int:
    from fractions import Fraction
    return math.floor(Fraction(str(rho)) * n + Fraction(1, 2))


def describe(metrics: dict, detail: dict) -> None:
    cells = load_main()
    params = cells["params"].map(json.loads)
    for key in ("C", "min_samples_leaf", "max_features", "learning_rate"):
        cells[key] = params.map(lambda p, key=key: p.get(key, np.nan))
    fails = sum(int(row.n_flipped_train != n_flip_ref(row.rho, row.n_train)
                    or row.n_flipped_val != n_flip_ref(row.rho, row.n_val)) for row in cells.itertuples())
    metrics["n_cells"] = int(len(cells))
    metrics["n_flip_check_failures"] = fails
    metrics["n_convergence_warnings"] = int(cells["n_convergence_warnings"].sum())
    metrics["n_cells_with_convergence_warnings"] = int((cells["n_convergence_warnings"] > 0).sum())
    table_rows = []
    for name in DATASETS:
        c = cfactor(name)
        n_te = SIZES[name][1]
        m = majority_vector(cells, name)
        metrics[f"{name}.m_mean"] = float(exact_mean(m, n_te))
        metrics[f"{name}.m_sd"] = float(np.std(m, ddof=1))
        acc = {k: {rho: seed_vector(cells, name, k, rho) for rho in RHOS} for k in METHODS}
        for k in METHODS:
            for rho in RHOS:
                p = f"{name}.{k}.{rho_key(rho)}"
                sel = cells[(cells["dataset"] == name) & (cells["method"] == k) & (cells["rho"] == rho)]
                metrics[f"{p}.acc_mean"] = float(exact_mean(acc[k][rho], n_te))
                metrics[f"{p}.acc_sd"] = float(np.std(acc[k][rho], ddof=1))
                metrics[f"{p}.drop"] = float(exact_mean(acc[k][0.0], n_te) - exact_mean(acc[k][rho], n_te))
                for col in ("val_acc_noisy", "val_acc_clean", "train_acc_noisy", "pred_majority_share"):
                    metrics[f"{p}.{col}_mean"] = float(sel[col].mean())
                hp = {"lr": ("C",), "rf": ("min_samples_leaf", "max_features"),
                      "gbdt": ("learning_rate", "n_iter")}[k]
                for col in hp:
                    q25, q50, q75 = np.percentile(sel[col].to_numpy(dtype=float), [25, 50, 75])
                    metrics[f"{p}.{col}_median"] = float(q50)
                    metrics[f"{p}.{col}_q25"] = float(q25)
                    metrics[f"{p}.{col}_q75"] = float(q75)
                if k == "gbdt":
                    metrics[f"{p}.n_iter_plateau_median"] = float(np.median(sel["n_iter"].to_numpy() - 20))
                table_rows.append({"dataset": name, "method": k, "rho": rho, "acc_mean": float(acc[k][rho].mean()),
                                   "acc_sd": float(np.std(acc[k][rho], ddof=1)), "n_seeds": J,
                                   "m_mean": float(m.mean())})
        for rho in RHOS:
            means = {k: float(acc[k][rho].mean()) for k in METHODS}
            ranking = sorted(METHODS, key=lambda k: -means[k])
            metrics[f"{name}.{rho_key(rho)}.ranking"] = ">".join(ranking)
            for a, b in (("gbdt", "rf"), ("lr", "gbdt"), ("lr", "rf")):
                gap = acc[a][rho] - acc[b][rho]
                iv = t_interval(float(exact_mean(acc[a][rho], n_te) - exact_mean(acc[b][rho], n_te)), gap, c)
                p = f"{name}.{rho_key(rho)}.gap.{a}-{b}"
                put_iv(metrics, p, iv, boot=False)
                metrics[f"{p}.within_noise"] = int(iv["lo"] <= 0 <= iv["hi"])
            for first, second in zip(ranking, ranking[1:]):
                gap = acc[first][rho] - acc[second][rho]
                iv = t_interval(float(exact_mean(acc[first][rho], n_te) - exact_mean(acc[second][rho], n_te)), gap, c)
                metrics[f"{name}.{rho_key(rho)}.rank_{first}_over_{second}.within_noise"] = int(iv["lo"] <= 0 <= iv["hi"])
    pd.DataFrame(table_rows).to_csv(RESULTS / "accuracy_table.csv", index=False)
    detail["accuracy_table"] = table_rows


# ------------------------------------------------------------------ entry point

def main() -> int:
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", choices=("main", "noes", "cleanval", "half"))
    group.add_argument("--describe", action="store_true")
    ap.add_argument("--metrics", required=True)
    args = ap.parse_args()
    metrics: dict = {}
    detail: dict = {}
    if args.describe:
        describe(metrics, detail)
        out = RESULTS / "descriptives.json"
    elif args.test == "main":
        test_main(metrics, detail)
        out = RESULTS / "h_tests.json"
    else:
        run_ablation(args.test, metrics, detail)
        out = RESULTS / f"ablation_{args.test}.json"
    out.write_text(json.dumps(strip(detail), indent=1, sort_keys=True, default=float) + "\n", encoding="utf-8")
    write_metrics(args.metrics, metrics)
    print(f"{len(metrics)} metrics -> {args.metrics}; detail -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
