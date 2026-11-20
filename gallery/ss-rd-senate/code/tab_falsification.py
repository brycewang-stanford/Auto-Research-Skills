"""Table: H2 falsification tests (a)-(d) and the H3 descriptive sensitivity rows.

Every cell is a LaTeX macro from paper/numbers.tex. Each macro is checked here: its
claim must name a run metric, and the claim value must equal that metric in the
named run's metrics file (runs/h2-density, h2-covariates, h2-placebo, h2-selection,
h3-sensitivity). Selection macros are on the proportion scale (the table says so);
the MDE for H2(d) is already in percentage points (claim text and metric mde_pp).

Output: paper/tables/tab_falsification.tex (tabular only). Metrics:
runs/tab-falsification/metrics.json.

Usage (crew.py run --kind analysis):
    .venv/bin/python code/tab_falsification.py runs/tab-falsification/metrics.json
"""
import argparse
import json
import os

from tab_main import check_macro, load_claims, load_macros

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(WS, "paper", "tables", "tab_falsification.tex")

DASH = "--"


def row(label, est, ci_or_p, n, mde):
    return f"{label} & {est} & {ci_or_p} & {n} & {mde} \\\\"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics")
    args = ap.parse_args()

    macro_to_id = load_macros()
    claims_by_id = {c["id"]: c for c in load_claims()}
    cache = {}
    checked = []

    def m(name):
        checked.append(check_macro(name, macro_to_id, claims_by_id, cache))
        return "\\" + name

    lines = [
        r"\begin{tabular}{lrrrr}",
        r"\toprule",
        r"Test (scale of estimate) & Estimate & 95\% CI or $p$ & $N$ & MDE (80\% power) \\",
        r"\midrule",
        r"\multicolumn{5}{l}{\emph{Panel A. Falsification tests (H2), each tested on its own}} \\",
        row(r"H2(a) density of margin at 0 (density units)", m("RdDensityDiff"),
            f"$p$ = {m('RdDensityP')}", m("RdDensityN"), m("RdDensityMde")),
        row(r"H2(b) class (covariate units)", m("RdCovClassCoef"),
            f"$p$ = {m('RdCovClassP')} (Holm {m('RdCovClassHolm')})", m("RdCovClassN"),
            m("RdCovClassMde")),
        row(r"H2(b) termshouse (covariate units)", m("RdCovTermshouseCoef"),
            f"$p$ = {m('RdCovTermshouseP')} (Holm {m('RdCovTermshouseHolm')})",
            m("RdCovTermshouseN"), m("RdCovTermshouseMde")),
        row(r"H2(b) termssenate (covariate units)", m("RdCovTermssenateCoef"),
            f"$p$ = {m('RdCovTermssenateP')} (Holm {m('RdCovTermssenateHolm')})",
            m("RdCovTermssenateN"), m("RdCovTermssenateMde")),
        row(r"H2(b) population (persons)", m("RdCovPopulationCoef"),
            f"$p$ = {m('RdCovPopulationP')} (Holm {m('RdCovPopulationHolm')})",
            m("RdCovPopulationN"), m("RdCovPopulationMde")),
        row(f"H2(c) placebo, left, $c_L$ = {m('RdPlaceboCL')} (report only; pp)",
            m("RdPlaceboLeftEst"),
            f"[{m('RdPlaceboLeftCiLow')}, {m('RdPlaceboLeftCiHigh')}]",
            m("RdPlaceboLeftN"), DASH),
        row(f"H2(c) placebo, right, $c_R$ = {m('RdPlaceboCR')} (report only; pp)",
            m("RdPlaceboRightEst"),
            f"[{m('RdPlaceboRightCiLow')}, {m('RdPlaceboRightCiHigh')}]",
            m("RdPlaceboRightN"), DASH),
        row(r"H2(d) observed-outcome share (proportion; MDE in pp)", m("RdSelectionCoef"),
            f"[{m('RdSelectionCiLow')}, {m('RdSelectionCiHigh')}]; $p$ = {m('RdSelectionP')}",
            m("RdSelectionN"), m("RdSelectionMde")),
        r"\midrule",
        r"\multicolumn{5}{l}{\emph{Panel B. H3 descriptive sensitivity of H1 (pp; no decision rule)}} \\",
        row(f"(i) printed 2014 bandwidths, $h$ = {m('RdSensPrintedBw')}", m("RdSensPrintedEst"),
            f"[{m('RdSensPrintedLo')}, {m('RdSensPrintedHi')}]", m("RdSensPrintedN"), DASH),
        row(f"(ii) half H1 bandwidth, $h$ = {m('RdSensHalfBw')}", m("RdSensHalfEst"),
            f"[{m('RdSensHalfLo')}, {m('RdSensHalfHi')}]", m("RdSensHalfN"), DASH),
        row(f"(iii) double H1 bandwidth, $h$ = {m('RdSensDoubleBw')}", m("RdSensDoubleEst"),
            f"[{m('RdSensDoubleLo')}, {m('RdSensDoubleHi')}]", m("RdSensDoubleN"), DASH),
        row(f"(iv) $p$ = 2, $q$ = 3, $h$ = {m('RdSensPTwoBw')}", m("RdSensPTwoEst"),
            f"[{m('RdSensPTwoLo')}, {m('RdSensPTwoHi')}]", m("RdSensPTwoN"), DASH),
        row(f"(v) H1 with masspoints \\texttt{{adjust}}, $h$ = {m('RdSensAdjustBw')}",
            m("RdSensAdjustEst"), f"[{m('RdSensAdjustLo')}, {m('RdSensAdjustHi')}]",
            m("RdSensAdjustN"), DASH),
        r"\bottomrule",
        r"\end{tabular}",
        "",
    ]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(lines))

    out = {
        "n_macros_checked": len(checked),
        "max_macro_check_diff": max(checked),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.metrics)), exist_ok=True)
    with open(args.metrics, "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    print("\n".join(lines))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
