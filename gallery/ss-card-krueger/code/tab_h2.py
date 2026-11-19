"""Table: H2, the balanced-sample NJ-minus-PA difference unwinsorized and winsorized at the
pooled 5th/95th percentiles, with the cutoffs, the capped-store counts by state and tail,
and the two report-only secondaries (closures excluded from winsorization; the
Neumark-Wascher sample rule).

Reads (all written by logged runs):
- runs/h2-winsor/metrics.json and runs/h2-winsor/capped.csv   H2 (pooled 5/95, closures in)
- runs/h2-closures-excl/metrics.json                          secondary s1
- runs/h2-nw-rule/metrics.json                                secondary s2
- runs/main-t3/metrics.json      row-4 state changes beside the unwinsorized difference
- runs/verdict/metrics.json      the H2 flags (the only place H2 is judged)

Writes paper/tables/tab_h2.tex. Every cell that a claim quotes is the claim's macro; the
macros used are listed at the end of the fragment. Nothing is estimated here.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import Macros, load_metrics, write_metrics, write_tex  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/tables/tab_h2.tex")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

w, s1, s2 = load_metrics("h2-winsor"), load_metrics("h2-closures-excl"), load_metrics("h2-nw-rule")
t3, v = load_metrics("main-t3"), load_metrics("verdict")
RUNS = {"h2-winsor": w, "h2-closures-excl": s1, "h2-nw-rule": s2, "main-t3": t3, "verdict": v}
mac = Macros()

# ---- consistency of the inputs (identities, not estimates)
TOL = 1e-9
assert abs(w["did_u"] - t3["did_r4"]) < TOL and abs(w["did_u_se"] - t3["did_r4_se"]) < TOL
assert abs(s1["did_u"] - w["did_u"]) < TOL
assert w["n"] == s1["n"] == t3["n_bal_nj"] + t3["n_bal_pa"] == w["n_nj"] + w["n_pa"]
assert s1["n_pool"] == w["n"] - w["n_closed_nj"] - w["n_closed_pa"]
assert s2["n"] == s2["n_nj"] + s2["n_pa"] == s1["n_pool"]
assert v["h2_did_u"] == w["did_u"] and v["h2_did_w"] == w["did_w"]
sign = lambda x: (x > 0) - (x < 0)  # noqa: E731
assert v["h2_sign_same"] == int(sign(w["did_w"]) == sign(w["did_u"]))
assert v["h2_half_kept"] == int(abs(w["did_w"]) >= 0.5 * abs(w["did_u"]))
assert v["h2_holds"] == int(v["h2_sign_same"] and v["h2_half_kept"])
assert abs(w["ratio_w_u"] - w["did_w"] / w["did_u"]) < TOL
with open("runs/h2-winsor/capped.csv", newline="", encoding="utf-8") as fh:
    capped = list(csv.DictReader(fh))
for tail in ("low", "high"):
    for st in ("nj", "pa"):
        k = sum(1 for r in capped if r["tail"] == tail and r["state"] == st.upper())
        assert k == w[f"capped_{tail}_{st}"], (tail, st)
    k = sum(1 for r in capped if r["tail"] == tail and r["closed_perm"] == "1")
    assert k == w[f"capped_{tail}_closed"], tail
    vals = [float(r["DFTE"]) for r in capped if r["tail"] == tail]
    assert all(x < w["q05"] for x in vals) if tail == "low" else all(x > w["q95"] for x in vals)


def c(run: str, metric: str, macro: str | None = None, fmt: str = ".2f") -> str:
    value = RUNS[run][metric]
    return "$" + (mac.use(macro, run, metric, value) if macro else mac.raw(value, fmt)) + "$"


def yes(flag: int) -> str:
    assert flag in (0, 1)
    return "yes" if flag else "no"


DASH = "--"
rows: list[list[str]] = []
rows.append([r"NJ $-$ PA difference",
             c("h2-winsor", "did_u", "HTwoUnwinsorized"), c("h2-winsor", "did_w", "HTwoWinsorized"),
             c("h2-closures-excl", "did_w", "HTwoClosuresExcl"), c("h2-nw-rule", "b_nj", "NwRuleDid")])
rows.append(["", "(" + c("h2-winsor", "did_u_se", "HTwoUnwinsorizedSe") + ")",
             "(" + c("h2-winsor", "did_w_se", "HTwoWinsorizedSe") + ")",
             "(" + c("h2-closures-excl", "did_w_se", "HTwoClosuresExclSe") + ")",
             "(" + c("h2-nw-rule", "se_nj", "NwRuleDidSe") + ") ["
             + c("h2-nw-rule", "se_nj_hc1", "NwRuleDidSeHcOne") + "]"])
rows.append([r"Ratio to (1)", DASH, c("h2-winsor", "ratio_w_u", "HTwoRatio"),
             c("h2-closures-excl", "ratio_w_u", "HTwoClosuresExclRatio"), DASH])
rows.append([r"Mean change, NJ", c("main-t3", "chg_r4_nj", "DidFteBalancedNj"), DASH, DASH,
             c("h2-nw-rule", "chg_nj", "NwRuleChgNj")])
rows.append([r"Mean change, PA", c("main-t3", "chg_r4_pa", "DidFteBalancedPa"), DASH, DASH,
             c("h2-nw-rule", "chg_pa", "NwRuleChgPa")])
rows.append(["addlinespace"])
rows.append([r"Stores (NJ / PA)",
             c("h2-winsor", "n", "HTwoN") + " (" + c("main-t3", "n_bal_nj", "NBalNj") + " / "
             + c("main-t3", "n_bal_pa", "NBalPa") + ")",
             c("h2-winsor", "n", "HTwoN"), c("h2-closures-excl", "n", fmt="d"),
             c("h2-nw-rule", "n", "NwRuleN") + " (" + c("h2-nw-rule", "n_nj", fmt="d") + " / "
             + c("h2-nw-rule", "n_pa", fmt="d") + ")"])
rows.append([r"Permanent closures ($\Delta$FTE $= -$FTE$_1$)", "included", "included, winsorized",
             "included, not winsorized", "dropped"])
rows.append([r"Chain and ownership controls", "no", "no", "no", "yes"])
rows.append([r"Stores in the percentile pool", DASH, c("h2-winsor", "n", "HTwoN"),
             c("h2-closures-excl", "n_pool", fmt="d"), DASH])
rows.append([r"Lower cutoff (5th percentile)", DASH, c("h2-winsor", "q05", "HTwoQZeroFive"),
             c("h2-closures-excl", "q05_nc", "HTwoClosuresExclQZeroFive"), DASH])
rows.append([r"Upper cutoff (95th percentile)", DASH, c("h2-winsor", "q95", "HTwoQNineFive"),
             c("h2-closures-excl", "q95_nc", "HTwoClosuresExclQNineFive"), DASH])
rows.append(["addlinespace"])
rows.append([r"Capped below the lower cutoff, NJ", DASH, c("h2-winsor", "capped_low_nj", "HTwoCappedLowNj"),
             c("h2-closures-excl", "capped_low_nj", "HTwoClosuresExclCappedLowNj"), DASH])
rows.append([r"\quad PA", DASH, c("h2-winsor", "capped_low_pa", "HTwoCappedLowPa"),
             c("h2-closures-excl", "capped_low_pa", "HTwoClosuresExclCappedLowPa"), DASH])
rows.append([r"\quad of which permanent closures", DASH,
             c("h2-winsor", "capped_low_closed", "HTwoCappedLowClosed"), "none (excluded)", DASH])
rows.append([r"Capped above the upper cutoff, NJ", DASH, c("h2-winsor", "capped_high_nj", "HTwoCappedHighNj"),
             c("h2-closures-excl", "capped_high_nj", "HTwoClosuresExclCappedHighNj"), DASH])
rows.append([r"\quad PA", DASH, c("h2-winsor", "capped_high_pa", "HTwoCappedHighPa"),
             c("h2-closures-excl", "capped_high_pa", "HTwoClosuresExclCappedHighPa"), DASH])
rows.append([r"\quad of which permanent closures", DASH,
             c("h2-winsor", "capped_high_closed", "HTwoCappedHighClosed"), "none (excluded)", DASH])
rows.append(["addlinespace"])
rows.append([r"H2: same sign as (1)", DASH, yes(v["h2_sign_same"]), "report only", "report only"])
rows.append([r"H2: at least half of (1) kept", DASH, yes(v["h2_half_kept"]), "report only", "report only"])
rows.append([r"H2 holds", DASH, r"\textbf{" + yes(v["h2_holds"]) + "}", "report only", "report only"])

body = [r"\begin{tabular}{@{}l cccc@{}}",
        r"\toprule",
        r" & (1) & (2) & (3) & (4) \\",
        r" & Unwinsorized & Winsorized, pooled & Secondary s1: closures & Secondary s2: \\",
        r" & (row 4) & 5th/95th pct.\ (H2) & excluded from winsorizing & Neumark--Wascher rule \\",
        r"\midrule"]
for r in rows:
    body.append(r"\addlinespace" if r == ["addlinespace"] else " & ".join(r) + r" \\")
body += [r"\bottomrule", r"\end{tabular}"]

write_tex(args.out, "code/tab_h2.py", body, mac.footer())
write_metrics(args.metrics, {"n_rows": sum(1 for r in rows if r != ["addlinespace"]),
                             "n_macro_cells": len(mac.sources), "n_direct_cells": mac.direct,
                             "n_capped_listed": len(capped), "h2_holds_shown": v["h2_holds"]})
print(f"wrote {args.out}: {len(mac.sources)} macros, {mac.direct} direct, {len(capped)} capped stores checked")
