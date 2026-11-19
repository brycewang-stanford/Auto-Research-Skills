"""Figure: forest plot of the primary contrast, every robustness estimate and the H3 placebo.

Reads runs/main-aipw, rob-trim, rob-learners, rob-covsets, rob-estimators, rob-diff74,
placebo-re75 and h2-benchmark metrics.json only. Writes paper/figures/fig_forest.pdf.
Nothing is re-estimated.

Panel (a): outcome re78. One row per estimate, in the order of the analysis plan, each with
its 95% CI. The right-hand columns say whether the row can trigger the design's
disagreement rule (design.threats, DEV-11) and whether it did; "did" is the run's own
logged flag (*triggers_abstract_statement). Which rows can trigger is a design rule, not a
result, so it is written here as a constant and checked against the runs (a row that cannot
trigger must not carry a true flag). The experimental benchmark is drawn as a separate
reference line from runs/h2-benchmark (H2, descriptive; after the results gate); no row is
compared with it or ranked by it.

Panel (b): outcome re75, the H3 placebo, with zero and the pass band [-bound, +bound] of
the H3 rule (bound from the placebo run). The verdict is the run's logged verdict.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import BLUE, INK, LIGHT, MUTED, VERMILLION, load_metrics, mpl_setup, num, save_pdf, write_metrics  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_forest.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

main = load_metrics("main-aipw")
H2 = load_metrics("h2-benchmark")
P = load_metrics("placebo-re75")
assert H2["main_effect"] == main["effect"], "h2-benchmark did not read this main-aipw"

# (label, run, metric prefix, can trigger, trigger flag key or None, open marker?)
# "can trigger": design.threats (DEV-11). rob-estimators (b) triggers only if its point
# estimate lies outside main-aipw's 95% CI ("yes*"). Open markers: rows that never trigger
# (they change the estimand or the assumption).
ROWS = [
    ("Primary: cross-fitted AIPW, all 10 covariates", "main-aipw", "", None, None, False),
    ("Control-only trimming (rob-trim)", "rob-trim", "", "yes", "triggers_abstract_statement", False),
    ("(a) Parametric nuisances (rob-learners)", "rob-learners", "linear_", "yes",
     "linear_triggers_abstract_statement", False),
    ("(b) Random-forest nuisances (rob-learners)", "rob-learners", "rf_", "yes",
     "rf_triggers_abstract_statement", False),
    ("(a) Earnings-history core: drops black,\nhisp, nodegree (rob-covsets)", "rob-covsets", "covset_a_", "yes",
     "covset_a_triggers_abstract_statement", False),
    ("(b) Single lag: drops re74, u74 (rob-covsets)", "rob-covsets", "covset_b_", "no", None, True),
    ("OLS coefficient on treat, HC2 (rob-estimators)", "rob-estimators", "ols_", "no", None, True),
    ("Hajek IPW, bootstrap SE (rob-estimators)", "rob-estimators", "ipw_", "yes*",
     "ipw_triggers_abstract_statement", False),
    ("Conditional DiD on re78 $-$ re74,\ntime-invariant covariates (rob-diff74)", "rob-diff74", "", "no",
     "triggers_abstract_statement", True),
]
# Display format of each interval's lower bound: the claims' macro formats (primary-ci-low
# is ",.1f", so the figure prints 9.6 as \PrimaryCiLow does; every other bound is ",.0f").
LOW_FMT = {("main-aipw", ""): ",.1f"}

rows = []
for label, run, pre, can, flag, open_marker in ROWS:
    m = load_metrics(run)
    if can is None:
        did = None
    elif can == "no":
        assert flag is None or m[flag] is False, f"{run}:{pre} cannot trigger but its flag is true"
        did = None
    else:
        did = bool(m[flag])
    rows.append({"label": label, "run": run, "pre": pre, "can": can, "did": did, "open": open_marker,
                 "est": m[pre + "effect"], "lo": m[pre + "ci_low"], "hi": m[pre + "ci_high"],
                 "lofmt": LOW_FMT.get((run, pre), ",.0f")})

plt = mpl_setup()
from matplotlib.lines import Line2D  # noqa: E402

fig, (ax, axp) = plt.subplots(2, 1, figsize=(6.9, 4.9), sharex=True,
                              gridspec_kw={"height_ratios": [len(rows) + 1.3, 1.9], "hspace": 0.32})
bound = P["bound"]
lo_all = min([r["lo"] for r in rows] + [P["ci_low"], -bound])
hi_all = max([r["hi"] for r in rows] + [P["ci_high"], bound, H2["benchmark"]])
pad = 0.05 * (hi_all - lo_all)
xlim = (lo_all - pad, hi_all + pad)

ys = list(range(len(rows)))[::-1]
ax.axvline(0, color=MUTED, lw=0.8, zorder=1)
ax.axvline(H2["benchmark"], color=BLUE, lw=1.0, ls=(0, (5, 2)), zorder=1)
ax.axhline(ys[0] - 0.5, color=LIGHT, lw=0.6, zorder=0)
for y, r in zip(ys, rows):
    primary = r["can"] is None
    ax.plot([r["lo"], r["hi"]], [y, y], color=INK, lw=1.4 if primary else 0.9, solid_capstyle="butt", zorder=2)
    ax.plot([r["est"]], [y], marker="s" if primary else "o", ms=5.6 if primary else 4.8, color=INK,
            mfc="white" if r["open"] else INK, mew=1.0, zorder=3)
    ax.text(1.02, y, f"{num(r['est'])} [{num(r['lo'], r['lofmt'])}, {num(r['hi'])}]",
            transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=7.2)
    can = "reference" if primary else r["can"]
    did = "" if primary else ("\u2013" if r["did"] is None else ("YES" if r["did"] else "no"))
    ax.text(1.30, y, can, transform=ax.get_yaxis_transform(), ha="center", va="center", fontsize=7.2)
    ax.text(1.43, y, did, transform=ax.get_yaxis_transform(), ha="center", va="center", fontsize=7.2,
            weight="bold" if r["did"] else "normal", color=VERMILLION if r["did"] else INK)
hy = len(rows) - 0.25
for x, t in ((1.02, "Estimate [95% CI]"), (1.30, "Can trigger\nthe rule?"), (1.43, "Did it?")):
    ax.text(x, hy, t, transform=ax.get_yaxis_transform(), ha="left" if x < 1.1 else "center", va="bottom",
            fontsize=7.2, style="italic")
ax.text(H2["benchmark"] + 0.012 * (xlim[1] - xlim[0]), hy + 0.1,
        f"experimental benchmark {num(H2['benchmark'])}\n(DW 1999; H2, descriptive only)",
        ha="left", va="bottom", fontsize=6.8, color=BLUE)
ax.set_yticks(ys)
ax.set_yticklabels([r["label"] for r in rows], fontsize=7.2, linespacing=1.0)
ax.set_ylim(-0.6, len(rows) + 0.75)
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
ax.set_title("(a) Outcome re78: primary contrast and robustness estimates", loc="left", fontsize=8)
ax.grid(axis="x", color="#e6e6e6", lw=0.5, zorder=0)

# (b) the H3 placebo
axp.axvspan(-bound, bound, color=LIGHT, alpha=0.45, lw=0, zorder=0)
for x in (-bound, bound):
    axp.axvline(x, color=INK, lw=0.7, ls=(0, (1, 1.5)), zorder=1)
axp.axvline(0, color=MUTED, lw=0.8, zorder=1)
axp.plot([P["ci_low"], P["ci_high"]], [0, 0], color=INK, lw=0.9, solid_capstyle="butt", zorder=2)
axp.plot([P["effect"]], [0], marker="o", ms=4.8, color=INK, mew=1.0, zorder=3)
axp.text(1.02, 0, f"{num(P['effect'])} [{num(P['ci_low'])}, {num(P['ci_high'])}]",
         transform=axp.get_yaxis_transform(), ha="left", va="center", fontsize=7.2)
axp.text(1.365, 0, f"H3: {P['verdict'].upper()}\n(CI excludes 0)" if P["ci_excludes_zero"] else f"H3: {P['verdict'].upper()}",
         transform=axp.get_yaxis_transform(), ha="center", va="center", fontsize=7.2, weight="bold",
         color=VERMILLION if P["verdict"] == "fail" else INK)
axp.text(bound, 0.62, f" pass band ±{num(bound)}", ha="left", va="center", fontsize=6.8)
axp.set_yticks([0])
axp.set_yticklabels(["Placebo: outcome re75, covariates\nwithout re75 and u75 (placebo-re75)"], fontsize=7.2,
                    linespacing=1.0)
axp.set_ylim(-0.75, 0.95)
axp.tick_params(axis="y", length=0)
axp.spines["left"].set_visible(False)
axp.set_title("(b) H3 placebo: outcome re75 (the program cannot have affected it)", loc="left", fontsize=8)
axp.grid(axis="x", color="#e6e6e6", lw=0.5, zorder=0)
axp.set_xlim(*xlim)
from matplotlib.ticker import FuncFormatter  # noqa: E402
axp.xaxis.set_major_formatter(FuncFormatter(lambda v, _: num(v)))
axp.set_xlabel("Contrast in earnings, 1982 dollars (treated men minus comparable CPS men)")

handles = [
    Line2D([], [], color=INK, lw=0.9, label="95% CI"),
    Line2D([], [], color=INK, marker="s", ls="", mfc=INK, label="primary"),
    Line2D([], [], color=INK, marker="o", ls="", mfc=INK, label="can trigger the rule"),
    Line2D([], [], color=INK, marker="o", ls="", mfc="white", label="never triggers (changes assumption or estimand)"),
    Line2D([], [], color=BLUE, lw=1.0, ls=(0, (5, 2)), label="experimental benchmark (H2)"),
]
fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.45, -0.045), ncol=5, frameon=False,
           fontsize=7, handlelength=1.8, columnspacing=1.2)
save_pdf(fig, args.out)

write_metrics(args.metrics, {
    "n_rows_re78": len(rows), "n_rows_placebo": 1,
    "rows": ",".join(f"{r['run']}:{r['pre'] or 'main'}" for r in rows),
    "n_rows_can_trigger": sum(1 for r in rows if r["can"] in ("yes", "yes*")),
    "n_rows_triggered": sum(1 for r in rows if r["did"]),
    "triggered_rows": ",".join(f"{r['run']}:{r['pre'] or 'main'}" for r in rows if r["did"]),
    "benchmark_line": H2["benchmark"], "placebo_bound": bound, "placebo_verdict": P["verdict"],
    "xlim_low": xlim[0], "xlim_high": xlim[1],
    "checksum_plotted": sum(r["est"] + r["lo"] + r["hi"] for r in rows) + P["effect"] + P["ci_low"] + P["ci_high"],
})
