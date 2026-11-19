"""Table: published and replicated Card and Krueger (1994) Table 3 rows 1-5 and Table 4
column (i), side by side, with |difference|, the pre-registered 0.05 tolerance and the
verdict's reading.

Reads (all written by logged runs):
- runs/main-t3/metrics.json   replicated Table 3 rows 1-5
- runs/main-t4/metrics.json   replicated Table 4 column (i)
- runs/verdict/metrics.json   |difference| and met flag of every H1 target
- runs/pub-values/metrics.json published values (rows 1-5, Table 4 column (i))
The tolerance is verdict.TOLERANCE (code/verdict.py, the pre-registered constant the verdict
judged with); the script asserts that every met flag equals round(|difference|, 6) <= it.

Only H1 targets carry a verdict ("reproduced", "not reproduced", or for row 3 "within tol."
and the two row-3 markings). Rows 1, 2 and 5 and the Table 4 rows other than N, the NJ
coefficient and its SE are not targets; their |difference| is shown and marked "report only",
and no tolerance is applied to them (plan.json analysis_plan step 8: no judgment elsewhere).

Writes paper/tables/tab_replication.tex. Every replicated cell that a claim quotes is the
claim's macro; the macros used are listed at the end of the fragment.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import Macros, load_metrics, num, write_metrics, write_tex  # noqa: E402
from verdict import TOLERANCE  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_replication.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

t3, t4 = load_metrics("main-t3"), load_metrics("main-t4")
v, pub = load_metrics("verdict"), load_metrics("pub-values")
mac = Macros()

# Replicated cells that a claim quotes: (run, metric) -> macro (claims.jsonl, first support)
MACRO = {
    ("main-t3", "mean_w1_pa"): "MeanWOnePa", ("main-t3", "mean_w1_pa_se"): "MeanWOnePaSe",
    ("main-t3", "mean_w1_nj"): "MeanWOneNj", ("main-t3", "mean_w1_nj_se"): "MeanWOneNjSe",
    ("main-t3", "row1_diff"): "LevelGapWOne", ("main-t3", "row1_diff_se"): "LevelGapWOneSe",
    ("main-t3", "mean_w2_pa"): "MeanWTwoPa", ("main-t3", "mean_w2_pa_se"): "MeanWTwoPaSe",
    ("main-t3", "mean_w2_nj"): "MeanWTwoNj", ("main-t3", "mean_w2_nj_se"): "MeanWTwoNjSe",
    ("main-t3", "row2_diff"): "LevelGapWTwo", ("main-t3", "row2_diff_se"): "LevelGapWTwoSe",
    ("main-t3", "chg_r3_pa"): "DidFtePa", ("main-t3", "chg_r3_pa_se"): "DidFtePaSe",
    ("main-t3", "chg_r3_nj"): "DidFteNj", ("main-t3", "chg_r3_nj_se"): "DidFteNjSe",
    ("main-t3", "did_r3"): "DidFte", ("main-t3", "did_r3_se"): "DidFteSe",
    ("main-t3", "chg_r4_pa"): "DidFteBalancedPa", ("main-t3", "chg_r4_pa_se"): "DidFteBalancedPaSe",
    ("main-t3", "chg_r4_nj"): "DidFteBalancedNj", ("main-t3", "chg_r4_nj_se"): "DidFteBalancedNjSe",
    ("main-t3", "did_r4"): "DidFteBalanced", ("main-t3", "did_r4_se"): "DidFteBalancedSe",
    ("main-t3", "did_r5"): "DidRFive", ("main-t3", "did_r5_se"): "DidRFiveSe",
    ("main-t4", "n"): "RegN", ("main-t4", "b_nj"): "RegNj", ("main-t4", "se_nj"): "RegNjSe",
    ("main-t4", "root_mse"): "RegRootMse", ("main-t4", "dep_mean"): "RegDepMean",
    ("main-t4", "dep_sd"): "RegDepSd",
}
# |difference| of H1 targets: verdict metric -> macro
PART = {"h1a": "HOneA", "h1b": "HOneB", "h1c": "HOneC"}
KEY = {"did": "Did", "did_se": "DidSe", "pa": "Pa", "pa_se": "PaSe", "nj": "Nj", "nj_se": "NjSe",
       "b_nj": "BNj", "se_nj": "SeNj"}
FMT_REPL = {("main-t4", "n"): "d", ("main-t4", "dep_mean"): ".4f"}
RUNS = {"main-t3": t3, "main-t4": t4}

counts = {"n_lines": 0, "n_cells_target": 0, "n_cells_target_met": 0, "n_cells_report_only": 0}


def m(x) -> str:
    return "$" + x + "$"


def repl(run: str, metric: str) -> str:
    value = RUNS[run][metric]
    if (run, metric) in MACRO:
        return m(mac.use(MACRO[(run, metric)], run, metric, value))
    return m(mac.raw(value, FMT_REPL.get((run, metric), ".2f")))


def published(key: str) -> str:
    return m(num(pub[key], "d" if pub[key + "_dp"] == 0 else f".{pub[key + '_dp']}f"))


def cell(run: str, metric: str, pub_key: str, target: tuple[str, str] | None, row3: bool,
         note: str = "") -> list[str]:
    """Publ., Repl., |diff|, Tol., Status for one estimate or SE."""
    rep_value, pub_value = RUNS[run][metric], pub[pub_key]
    if target is None:
        counts["n_cells_report_only"] += 1
        diff = mac.raw(abs(rep_value - pub_value), ".5f")
        return [published(pub_key), repl(run, metric), m(diff), "--", "report only"]
    part, key = target
    # the verdict judged exactly these values
    assert v[f"{part}_{key}_rep"] == rep_value, (part, key)
    assert v[f"{part}_{key}_pub"] == pub_value, (part, key)
    diff = v[f"{part}_{key}_absdiff"]
    assert abs(diff - abs(rep_value - pub_value)) < 1e-12, (part, key)
    met = v[f"{part}_{key}_met"]
    assert met == int(round(diff, 6) <= TOLERANCE), (part, key)
    counts["n_cells_target"] += 1
    counts["n_cells_target_met"] += met
    if row3:
        status = "within tol." if met else "not reproduced"
    else:
        status = "reproduced" if met else "not reproduced"
    diff_cell = m(mac.use(f"{PART[part]}{KEY[key]}Absdiff", "verdict", f"{part}_{key}_absdiff", diff))
    return [published(pub_key), repl(run, metric), diff_cell, m(num(TOLERANCE, ".2f")), status + note]


T3_ROWS = [
    (1, r"1.\ Wave 1, all available", {"pa": "mean_w1_pa", "nj": "mean_w1_nj", "did": "row1_diff"}, None),
    (2, r"2.\ Wave 2, all available", {"pa": "mean_w2_pa", "nj": "mean_w2_nj", "did": "row2_diff"}, None),
    (3, r"3.\ Change in mean FTE", {"pa": "chg_r3_pa", "nj": "chg_r3_nj", "did": "did_r3"}, "h1a"),
    (4, r"4.\ Change, balanced sample", {"pa": "chg_r4_pa", "nj": "chg_r4_nj", "did": "did_r4"}, "h1b"),
    (5, r"5.\ As 4, temp.\ closed $=0$", {"pa": "chg_r5_pa", "nj": "chg_r5_nj", "did": "did_r5"}, None),
]
COLS = [("pa", "PA"), ("nj", "NJ"), ("did", r"NJ $-$ PA")]
NCOL = 12

body = [r"\begin{tabular}{@{}ll rrrrl rrrrl@{}}",
        r"\toprule",
        r" & & \multicolumn{5}{c}{Estimate} & \multicolumn{5}{c}{Standard error} \\",
        r"\cmidrule(lr){3-7}\cmidrule(lr){8-12}",
        r"Row & Column & Publ. & Repl. & $|\Delta|$ & Tol. & Status"
        r" & Publ. & Repl. & $|\Delta|$ & Tol. & Status \\",
        r"\midrule",
        rf"\multicolumn{{{NCOL}}}{{@{{}}l}}{{\textit{{Table 3: mean FTE employment per store}}}} \\"]

for r, label, metrics, part in T3_ROWS:
    for ci, (col, col_label) in enumerate(COLS):
        metric = metrics[col]
        target_pt = (part, col) if part else None
        target_se = (part, f"{col}_se") if part else None
        row3 = part == "h1a"
        line = [label if ci == 0 else "", col_label]
        line += cell("main-t3", metric, f"pub_r{r}_{col}", target_pt, row3)
        line += cell("main-t3", f"{metric}_se", f"pub_r{r}_{col}_se", target_se, row3)
        body.append(" & ".join(line) + r" \\")
        counts["n_lines"] += 1
    if part == "h1a":
        body.append(r" & & \multicolumn{5}{l}{\textit{Point gap: within tolerance, not at published precision}$^{a}$}"
                    r" & \multicolumn{5}{l}{\textit{SE construction not identified}$^{b}$} \\")
    body.append(r"\addlinespace")

body.append(rf"\multicolumn{{{NCOL}}}{{@{{}}l}}{{\textit{{Table 4, column (i): OLS of the change in FTE on NJ}}}} \\")

# N: a data check (observed at data prep), exact match required
assert v["h1c_n_rep"] == t4["n"] and v["h1c_n_pub"] == pub["pub_t4_n"]
assert v["h1c_n_met"] == int(t4["n"] == pub["pub_t4_n"])
counts["n_cells_target"] += 1
counts["n_cells_target_met"] += v["h1c_n_met"]
n_status = ("reproduced" if v["h1c_n_met"] else "not reproduced") + "$^{c}$"
body.append(" & ".join(["Stores ($N$)", "", published("pub_t4_n"), repl("main-t4", "n"),
                        m(mac.raw(abs(t4["n"] - pub["pub_t4_n"]), "d")), "exact", n_status,
                        "", "", "", "", ""]) + r" \\")
line = ["NJ coefficient", ""]
line += cell("main-t4", "b_nj", "pub_t4_b_nj", ("h1c", "b_nj"), False)
line += cell("main-t4", "se_nj", "pub_t4_se_nj", ("h1c", "se_nj"), False)
body.append(" & ".join(line) + r" \\")
for label, metric, key in (("SE of regression", "root_mse", "pub_t4_root_mse"),
                           (r"Mean of $\Delta$FTE", "dep_mean", "pub_t4_dep_mean"),
                           (r"SD of $\Delta$FTE", "dep_sd", "pub_t4_dep_sd")):
    line = [label, ""] + cell("main-t4", metric, key, None, False) + ["", "", "", "", ""]
    body.append(" & ".join(line) + r" \\")
counts["n_lines"] += 5
body += [r"\bottomrule", r"\end{tabular}"]

# the verdict's part flags agree with the cell flags shown
for part, n_cells in (("h1a", 6), ("h1b", 6)):
    assert v[f"{part}_point_met"] == int(all(v[f"{part}_{k}_met"] for k in ("did", "pa", "nj")))
    assert v[f"{part}_se_met"] == int(all(v[f"{part}_{k}_se_met"] for k in ("did", "pa", "nj")))
assert counts["n_lines"] == 20

write_tex(args.out, "code/tab_replication.py", body, mac.footer())
write_metrics(args.metrics, {**counts, "n_macro_cells": len(mac.sources), "n_direct_cells": mac.direct,
                             "tolerance": TOLERANCE})
print(f"wrote {args.out}: {counts['n_lines']} lines, {counts['n_cells_target_met']} of "
      f"{counts['n_cells_target']} target cells met, {len(mac.sources)} macros, {mac.direct} direct")
