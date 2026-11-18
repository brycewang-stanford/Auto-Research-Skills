"""Write the result claims in claims.jsonl from the run ledger (not a run; no computation).

Every `value` is copied from `runs/<id>/run.json` metrics, so `crew.py validate` can check
it. Citation claims already in claims.jsonl are kept; result claims are regenerated.
Macro names are letters only: dataset Bc/Cg/Ad/Ct, method Lr/Rf/Gb/Ne (GBDT-noES),
rho Zero/One/Two/Three/Four.

    python3 code/make_claims.py
"""
from __future__ import annotations

import json
from pathlib import Path

DS = {"breast_cancer": "Bc", "credit-g": "Cg", "adult": "Ad", "covtype": "Ct"}
MT = {"lr": "Lr", "rf": "Rf", "gbdt": "Gb", "gbdt_noes": "Ne"}
MNAME = {"lr": "logistic regression", "rf": "the random forest", "gbdt": "gradient boosting",
         "gbdt_noes": "gradient boosting without early stopping"}
RH = {0.0: "Zero", 0.1: "One", 0.2: "Two", 0.3: "Three", 0.4: "Four"}
CLAIMS = Path("claims.jsonl")

claims: list[dict] = []
metrics_cache: dict[str, dict] = {}


def metrics(run: str) -> dict:
    if run not in metrics_cache:
        metrics_cache[run] = json.loads(Path(f"runs/{run}/run.json").read_text())["metrics"]
    return metrics_cache[run]


def num(cid: str, run: str, metric: str, text: str, macro: str, fmt: str) -> None:
    value = metrics(run)[metric]
    if value is None:          # non-finite in the run (e.g. bootstrap with zero headroom): no number to claim
        return
    claims.append({"id": cid, "kind": "result", "text": text, "support": [{"run": run, "metric": metric}],
                   "value": value, "macro": macro, "format": fmt})


REPORT_WORDS = {"inconclusive": "no detectable difference (inconclusive)"}   # design.method 'Reporting words'


def word(cid: str, run: str, metric: str, template: str, outcome: bool = False) -> None:
    value = metrics(run)[metric]
    if outcome:
        value = REPORT_WORDS.get(value, value)
    claims.append({"id": cid, "kind": "result", "text": template.format(value),
                   "support": [{"run": run, "metric": metric}]})


def ivclaims(run: str, prefix: str, cid: str, macro: str, label: str, boot: bool = True) -> None:
    num(f"{cid}", run, f"{prefix}.value", f"{label}: point estimate.", macro, ".3f")
    num(f"{cid}-lo", run, f"{prefix}.lo", f"{label}: lower end of the 95% decision interval.", macro + "Lo", ".3f")
    num(f"{cid}-hi", run, f"{prefix}.hi", f"{label}: upper end of the 95% decision interval.", macro + "Hi", ".3f")
    num(f"{cid}-s", run, f"{prefix}.S", f"{label}: per-seed SD S of the linearized difference.", macro + "S", ".3f")
    num(f"{cid}-half", run, f"{prefix}.half", f"{label}: half-width of the 95% decision interval.", macro + "Half", ".3f")
    if boot:
        num(f"{cid}-blo", run, f"{prefix}.boot_lo", f"{label}: 2.5th percentile of the descriptive seed bootstrap.", macro + "BootLo", ".3f")
        num(f"{cid}-bhi", run, f"{prefix}.boot_hi", f"{label}: 97.5th percentile of the descriptive seed bootstrap.", macro + "BootHi", ".3f")


def main() -> None:
    # descriptives: majority rates, accuracy table, tuned hyperparameters, diagnostics
    run = "descriptives"
    num("c-n-cells", run, "n_cells", "Number of main-experiment cells (4 datasets x 3 methods x 5 noise rates x 10 seeds).", "NCells", "d")
    num("c-flip-fail", run, "n_flip_check_failures", "Cells whose flipped-label count differs from floor(rho n + 0.5).", "NFlipFail", "d")
    num("c-convwarn", run, "n_cells_with_convergence_warnings", "Main cells in which logistic regression raised a convergence warning.", "NConvWarnCells", "d")
    for d, dc in DS.items():
        num(f"c-m-{dc}", run, f"{d}.m_mean", f"Majority-class share of the test split on {d}, mean over 10 seeds.", f"Maj{dc}", ".3f")
        for k in ("lr", "rf", "gbdt"):
            mc = MT[k]
            for rho, rc in RH.items():
                p = f"{d}.{k}.rho{rho:g}"
                num(f"c-acc-{dc}-{mc}-{rc}", run, f"{p}.acc_mean", f"Mean clean-test accuracy of {MNAME[k]} on {d} at rho={rho:g} over 10 seeds.", f"Acc{dc}{mc}{rc}", ".3f")
                num(f"c-sd-{dc}-{mc}-{rc}", run, f"{p}.acc_sd", f"SD over 10 seeds of the clean-test accuracy of {MNAME[k]} on {d} at rho={rho:g}.", f"Sd{dc}{mc}{rc}", ".3f")
                num(f"c-pms-{dc}-{mc}-{rc}", run, f"{p}.pred_majority_share_mean", f"Share of test predictions equal to the test majority class, {MNAME[k]} on {d} at rho={rho:g}, mean over seeds.", f"Pms{dc}{mc}{rc}", ".3f")
                num(f"c-vn-{dc}-{mc}-{rc}", run, f"{p}.val_acc_noisy_mean", f"Noisy-validation accuracy of the selected {MNAME[k]} on {d} at rho={rho:g}, mean over seeds.", f"Vn{dc}{mc}{rc}", ".3f")
                num(f"c-vc-{dc}-{mc}-{rc}", run, f"{p}.val_acc_clean_mean", f"Clean-validation accuracy of the selected {MNAME[k]} on {d} at rho={rho:g}, mean over seeds.", f"Vc{dc}{mc}{rc}", ".3f")
                num(f"c-tn-{dc}-{mc}-{rc}", run, f"{p}.train_acc_noisy_mean", f"Training accuracy against the noisy training labels, selected {MNAME[k]} on {d} at rho={rho:g}, mean over seeds.", f"Tn{dc}{mc}{rc}", ".3f")
                if k == "lr":
                    num(f"c-C-{dc}-{rc}", run, f"{p}.C_median", f"Median over seeds of the selected logistic-regression C on {d} at rho={rho:g}.", f"C{dc}{rc}", ".3g")
                if k == "rf":
                    num(f"c-msl-{dc}-{rc}", run, f"{p}.min_samples_leaf_median", f"Median over seeds of the selected random-forest min_samples_leaf on {d} at rho={rho:g}.", f"Msl{dc}{rc}", ".3g")
                    num(f"c-mf-{dc}-{rc}", run, f"{p}.max_features_median", f"Median over seeds of the selected random-forest max_features on {d} at rho={rho:g}.", f"Mf{dc}{rc}", ".2f")
                if k == "gbdt":
                    num(f"c-lrate-{dc}-{rc}", run, f"{p}.learning_rate_median", f"Median over seeds of the selected GBDT learning rate on {d} at rho={rho:g}.", f"Lrate{dc}{rc}", ".3g")
                    num(f"c-iter-{dc}-{rc}", run, f"{p}.n_iter_median", f"Median over seeds of the selected GBDT's number of boosting iterations (n_iter_) on {d} at rho={rho:g}.", f"Iter{dc}{rc}", ".0f")
        for rho, rc in RH.items():
            word(f"c-rank-{dc}-{rc}", run, f"{d}.rho{rho:g}.ranking", f"Ranking by mean clean-test accuracy on {d} at rho={rho:g} (descriptive): {{}}.")
            for a, b in (("gbdt", "rf"), ("lr", "gbdt"), ("lr", "rf")):
                word(f"c-wn-{dc}-{rc}-{MT[a]}{MT[b]}", run, f"{d}.rho{rho:g}.gap.{a}-{b}.within_noise",
                     f"Accuracy gap {a} minus {b} on {d} at rho={rho:g} within noise (1 = its paired 95% interval contains 0): {{}}.")

    # exclusion-check
    run = "exclusion-check"
    for d, dc in DS.items():
        for k in ("lr", "rf", "gbdt"):
            num(f"c-head-{dc}-{MT[k]}", run, f"{d}.{k}.headroom", f"Headroom A(0) - m of {MNAME[k]} on {d}, from rho=0 cells only.", f"Head{dc}{MT[k]}", ".3f")
        word(f"c-inf1-{dc}", run, f"{d}.informative_h1", f"{d} informative for H1 (1 = yes): {{}}.")
        word(f"c-inf2-{dc}", run, f"{d}.informative_h2", f"{d} informative for H2 (1 = yes): {{}}.")
    num("c-ninf-h1", run, "n_informative_h1", "Number of datasets informative for H1.", "NInfHOne", "d")
    num("c-ninf-h2", run, "n_informative_h2", "Number of datasets informative for H2.", "NInfHTwo", "d")

    # h-tests
    run = "h-tests"
    for d, dc in DS.items():
        for k in ("lr", "rf", "gbdt"):
            mc = MT[k]
            num(f"c-h-{dc}-{mc}", run, f"{d}.{k}.h", f"Headroom h = A(0) - m of {MNAME[k]} on {d}.", f"H{dc}{mc}", ".3f")
            num(f"c-hlo-{dc}-{mc}", run, f"{d}.{k}.h_lo", f"Lower end of the 95% interval of the headroom of {MNAME[k]} on {d}.", f"Hlo{dc}{mc}", ".3f")
            num(f"c-drop-{dc}-{mc}", run, f"{d}.{k}.drop", f"Absolute accuracy drop A(0) - A(0.4) of {MNAME[k]} on {d}.", f"Drop{dc}{mc}", ".3f")
            num(f"c-r-{dc}-{mc}", run, f"{d}.{k}.r", f"Share of headroom lost r between rho=0 and 0.4, {MNAME[k]} on {d}.", f"R{dc}{mc}", ".3f")
        ivclaims(run, f"{d}.H1.D", f"c-h1-{dc}", f"HOneD{dc}", f"H1 on {d}, D = r_GBDT - r_RF")
        num(f"c-h1-{dc}-ddrop", run, f"{d}.H1.D.ddrop", f"H1 on {d}: difference in absolute drops, GBDT minus RF.", f"HOneDdrop{dc}", ".3f")
        word(f"c-h1-{dc}-out", run, f"{d}.H1.outcome", f"H1 outcome on {d}: {{}}.", outcome=True)
        for j, other in ((1, "gbdt"), (2, "rf")):
            jw = "One" if j == 1 else "Two"
            ivclaims(run, f"{d}.H2.D{j}", f"c-h2-{dc}-d{j}", f"HTwoD{jw}{dc}", f"H2 on {d}, D{j} = r_LR - r_{other.upper()}")
            num(f"c-h2-{dc}-d{j}-ddrop", run, f"{d}.H2.D{j}.ddrop", f"H2 on {d}: difference in absolute drops, LR minus {other.upper()}.", f"HTwoD{jw}Ddrop{dc}", ".3f")
        word(f"c-h2-{dc}-out", run, f"{d}.H2.outcome", f"H2 outcome on {d}: {{}}.", outcome=True)
    for hyp, hw in (("H1", "HOne"), ("H2", "HTwo")):
        for key, kw in (("n_informative", "NInf"), ("n_supported", "NSup"), ("n_contradicted", "NCon"),
                        ("n_no_meaningful_difference", "NNmd"), ("n_inconclusive", "NInc"), ("n_unstable", "NUns"),
                        ("support_needed", "NNeed")):
            num(f"c-{hyp.lower()}-{key}", run, f"{hyp}.{key}", f"{hyp}: {key.replace('_', ' ')} (over informative datasets).", f"{hw}{kw}", "d")
        word(f"c-{hyp.lower()}-verdict", run, f"{hyp}.verdict", f"{hyp} overall verdict: {{}}.")

    # ablations
    run = "abl-noes"
    for d, dc in DS.items():
        for rho, rc in ((0.0, "Zero"), (0.4, "Four")):
            num(f"c-acc-{dc}-Ne-{rc}", run, f"{d}.gbdt_noes.rho{rho:g}.acc_mean", f"Mean clean-test accuracy of GBDT without early stopping on {d} at rho={rho:g}.", f"Acc{dc}Ne{rc}", ".3f")
            num(f"c-sd-{dc}-Ne-{rc}", run, f"{d}.gbdt_noes.rho{rho:g}.acc_sd", f"SD over seeds of the accuracy of GBDT without early stopping on {d} at rho={rho:g}.", f"Sd{dc}Ne{rc}", ".3f")
            num(f"c-iter-{dc}-Ne-{rc}", run, f"{d}.gbdt_noes.n_iter_median.rho{rho:g}", f"Median selected max_iter of GBDT without early stopping on {d} at rho={rho:g}.", f"Iter{dc}Ne{rc}", ".0f")
        num(f"c-r-{dc}-Ne", run, f"{d}.gbdt_noes.r", f"Share of headroom lost by GBDT without early stopping on {d}.", f"R{dc}Ne", ".3f")
        num(f"c-drop-{dc}-Ne", run, f"{d}.gbdt_noes.drop", f"Absolute drop of GBDT without early stopping on {d}.", f"Drop{dc}Ne", ".3f")
        ivclaims(run, f"{d}.A1.D_abl", f"c-a1-{dc}-dabl", f"AOneDabl{dc}", f"A1 on {d}, D_abl = r_GBDT-noES - r_RF")
        ivclaims(run, f"{d}.A1.Delta", f"c-a1-{dc}-delta", f"AOneDelta{dc}", f"A1 on {d}, Delta = D_main - D_abl", boot=False)
        word(f"c-a1-{dc}-status", run, f"{d}.A1.Delta.status", f"A1 (early stopping) on {d}: {{}}.")
    a2 = "A2 (clean validation labels for both model selection and GBDT early stopping, which this ablation does not separate)"
    for run, tag, tw in (("abl-cleanval", "A2", "ATwo"), ("abl-budget", "A3", "AThree")):
        name = a2 if tag == "A2" else "A3 (best of the first 10 candidates)"
        for d, dc in DS.items():
            for lab, dn, lw in (("Delta", "D", ""), ("Delta1", "D1", "One"), ("Delta2", "D2", "Two")):
                ivclaims(run, f"{d}.{tag}.{dn}_abl", f"c-{tag.lower()}-{dc}-{dn.lower()}abl", f"{tw}D{lw}abl{dc}", f"{name} on {d}, {dn} under the ablation")
                ivclaims(run, f"{d}.{tag}.{lab}", f"c-{tag.lower()}-{dc}-{lab.lower()}", f"{tw}Delta{lw}{dc}", f"{name} on {d}, {lab} = {dn}_main - {dn}_abl", boot=False)
                text = f"{name} {lab} on {d}: {{}}."
                if (tag, d, lab) == ("A2", "adult", "Delta"):
                    text = (f"{name} Delta on adult: {{}} under the pre-registered rule (interval excludes 0 and |Delta| >= 0.05). "
                            "Because A2 changes both the selection labels and the labels GBDT's early stopping monitors, the effect "
                            "cannot be assigned to model selection. Direction: the H1 gap D is larger under clean-label selection "
                            "and stopping than under the main noisy-label procedure (Delta < 0). The interval's upper end is close to 0, "
                            "and it is the plain t(9) interval that design.method calls slightly narrow on adult.")
                word(f"c-{tag.lower()}-{dc}-{lab.lower()}-status", run, f"{d}.{tag}.{lab}.status", text)
            for k in ("lr", "rf", "gbdt"):
                if tag == "A2":
                    num(f"c-acc-{dc}-{MT[k]}-cv", run, f"{d}.{k}.cleanval.rho0.4.acc_mean", f"Mean clean-test accuracy at rho=0.4 of {MNAME[k]} on {d} selected on clean validation labels.", f"Acc{dc}{MT[k]}Cv", ".3f")
                    num(f"c-r-{dc}-{MT[k]}-cv", run, f"{d}.{k}.cleanval.r", f"Share of headroom lost by {MNAME[k]} on {d} with clean-validation selection at rho=0.4.", f"R{dc}{MT[k]}Cv", ".3f")
                else:
                    for rho, rc in ((0.0, "Zero"), (0.4, "Four")):
                        num(f"c-acc-{dc}-{MT[k]}-half-{rc}", run, f"{d}.{k}.half.rho{rho:g}.acc_mean", f"Mean clean-test accuracy of {MNAME[k]} on {d} at rho={rho:g}, best of the first 10 candidates.", f"Acc{dc}{MT[k]}Half{rc}", ".3f")
                    num(f"c-r-{dc}-{MT[k]}-half", run, f"{d}.{k}.half.r", f"Share of headroom lost by {MNAME[k]} on {d} with half the tuning budget.", f"R{dc}{MT[k]}Half", ".3f")

    support = []
    for run, tag, labs in (("abl-noes", "A1", ("Delta",)), ("abl-cleanval", "A2", ("Delta", "Delta1", "Delta2")),
                           ("abl-budget", "A3", ("Delta", "Delta1", "Delta2"))):
        for d in DS:
            for lab in labs:
                if metrics(run)[f"{d}.{tag}.{lab}.status"] != "excluded (uninformative)":
                    support.append({"run": run, "metric": f"{d}.{tag}.{lab}.status"})
    hits = [s for s in support if metrics(s["run"])[s["metric"]] == "attributed"]
    claims.append({"id": "c-abl-count", "kind": "result",
                   "text": (f"Of the {len(support)} ablation Delta tests on informative datasets (A1 3, A2 9, A3 9), "
                            f"{len(hits)} has an interval that excludes 0 and |Delta| >= 0.05: A2 Delta on adult. "
                            "About one such interval is expected by chance at 95% across this many tests; "
                            "no multiplicity correction was planned."),
                   "support": support})

    kept = []
    for line in CLAIMS.read_text(encoding="utf-8").splitlines():
        if line.strip() and json.loads(line).get("kind") != "result":
            kept.append(line)
    ids = [c["id"] for c in claims]
    macros = [c["macro"] for c in claims if "macro" in c]
    assert len(ids) == len(set(ids)) and len(macros) == len(set(macros))
    CLAIMS.write_text("\n".join(kept + [json.dumps(c) for c in claims]) + "\n", encoding="utf-8")
    print(f"{len(claims)} result claims written; {len(kept)} citation claims kept")


if __name__ == "__main__":
    main()
