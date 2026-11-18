"""Figure: forest plot of the primary ATT and every robustness estimate, with +/-M marked.

Reads runs/main-aipw, rob-trim, rob-covsets, rob-learners, rob-estimators and rob-diff74
metrics.json only. Writes paper/figures/fig_forest.pdf. Every row is drawn in the same
style; rows whose estimand differs from the primary's use an open marker. select-re75 is
not a robustness estimate of the ATT (it is a descriptive measure of selection on re75)
and is reported in the table, not here.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import INK, LIGHT, MUTED, VERMILLION, load_metrics, money, mpl_setup, save_pdf, write_metrics  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_forest.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

main = load_metrics("main-aipw")
M = main["margin_M"]

# (row label, run, metric prefix, same estimand as the primary?) in the order of
# design.analysis_plan. The label says what changes relative to the primary.
ROWS = [
    ("Primary: cross-fitted AIPW\n(boosting outcome, L2-logit propensity)", "main-aipw", "", True),
    ("Trimmed overlap, $\\bar m \\in [0.1, 0.9]$\n(ATT among the trimmed sample)", "rob-trim", "", False),
    ("Covariate set (a): age, educ, married,\n1974-75 earnings", "rob-covsets", "covset_a_", True),
    ("Covariate set (b): all but\n1974 earnings", "rob-covsets", "covset_b_", True),
    ("Parametric nuisances\n(logit propensity, OLS outcome)", "rob-learners", "linear_", True),
    ("Random-forest nuisances", "rob-learners", "rf_", True),
    ("OLS coefficient on treat (HC2)", "rob-estimators", "ols_", True),
    ("Hajek IPW (bootstrap SE, 999 draws)", "rob-estimators", "ipw_", True),
    ("Conditional DiD on re78 $-$ re74\n(conditional parallel trends 1974-78)", "rob-diff74", "", False),
]

rows = []
for label, run, pre, same in ROWS:
    m = load_metrics(run)
    assert m["margin_M"] == M, f"{run} uses a different M"
    r = {"label": label, "run": run, "pre": pre, "same": same,
         "est": m[pre + "effect"], "lo95": m[pre + "ci_low"], "hi95": m[pre + "ci_high"],
         "lo90": m.get(pre + "ci90_low"), "hi90": m.get(pre + "ci90_high"),
         "n": m[pre + "n"]}
    rows.append(r)

plt = mpl_setup()
fig, ax = plt.subplots(figsize=(6.6, 4.3))
ys = list(range(len(rows)))[::-1]
lo_all = min([r["lo95"] for r in rows] + [-M])
hi_all = max([r["hi95"] for r in rows] + [M])
pad = 0.06 * (hi_all - lo_all)
xlim = (lo_all - pad, hi_all + pad)

ax.axvspan(-M, M, color=LIGHT, alpha=0.45, lw=0, zorder=0)
for x in (-M, M):
    ax.axvline(x, color=VERMILLION, lw=0.9, ls=(0, (5, 2)), zorder=1)
ax.axvline(0, color=MUTED, lw=0.7, zorder=1)
n_90 = 0
for y, r in zip(ys, rows):
    ax.plot([r["lo95"], r["hi95"]], [y, y], color=INK, lw=0.9, solid_capstyle="butt", zorder=2)
    if r["lo90"] is not None:
        ax.plot([r["lo90"], r["hi90"]], [y, y], color=INK, lw=3.0, solid_capstyle="butt", zorder=2)
        n_90 += 1
    ax.plot([r["est"]], [y], marker="o", ms=5.2, color=INK,
            mfc=INK if r["same"] else "white", mew=1.0, zorder=3)
    txt = f"{money(r['est'])} [{money(r['lo95'])}, {money(r['hi95'])}]"
    if r["n"] != main["n"]:
        txt += f"  n = {r['n']:,}"
    ax.text(1.01, y, txt, transform=ax.get_yaxis_transform(), ha="left", va="center", fontsize=7.2)
ax.text(1.01, len(rows) - 0.35, "Estimate [95% CI]", transform=ax.get_yaxis_transform(),
        ha="left", va="center", fontsize=7.2, style="italic")
ax.set_yticks(ys)
ax.set_yticklabels([r["label"] for r in rows], fontsize=7.2, linespacing=1.05)
ax.set_ylim(-0.7, len(rows) - 0.1)
ax.set_xlim(*xlim)
ax.tick_params(axis="y", length=0)
ax.spines["left"].set_visible(False)
ax.set_xlabel("Effect on 1978 earnings, nominal dollars (last row: on re78 $-$ re74)")
Mtxt = format(M, ",.2f")  # the format of the claim macro \EquivMargin
ax.text(M, -0.62, f" +M = {Mtxt}", color=VERMILLION, fontsize=7, ha="left", va="bottom")
ax.text(-M, -0.62, f"\u2212M = \u2212{Mtxt} ", color=VERMILLION, fontsize=7, ha="right", va="bottom")
ax.grid(axis="x", color="#e6e6e6", lw=0.5, zorder=0)

from matplotlib.lines import Line2D  # noqa: E402
handles = [
    Line2D([], [], color=INK, lw=3.0, label="90% CI (TOST for $|$ATT$|$ < M)"),
    Line2D([], [], color=INK, lw=0.9, label="95% CI"),
    Line2D([], [], color=INK, marker="o", ls="", mfc=INK, label="ATT on re78, full sample"),
    Line2D([], [], color=INK, marker="o", ls="", mfc="white", label="different estimand"),
]
ax.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=4,
          frameon=False, fontsize=7, handlelength=1.8, columnspacing=1.2)
fig.tight_layout()
save_pdf(fig, args.out)

write_metrics(args.metrics, {
    "n_rows": len(rows), "n_rows_with_90ci": n_90,
    "rows": ",".join(f"{r['run']}:{r['pre'] or 'main'}" for r in rows),
    "margin_M": M, "xlim_low": xlim[0], "xlim_high": xlim[1],
    "checksum_plotted": sum(r["est"] + r["lo95"] + r["hi95"] for r in rows),
})
