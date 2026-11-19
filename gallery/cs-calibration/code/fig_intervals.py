"""Figure: forest plot of the pre-registered per-dataset intervals for H1, H2a and H2b
(run `fig-intervals`).

Reads runs/h-tests/metrics.json only. The metrics, contrasts, predicted signs, margins, category
words and the k-of-4 rule are imported from code/analyze.py, the code run `h-tests` executed.
One panel per hypothesis, one row per dataset: the mean paired difference (10 seeds) with its 95%
plain paired t(9) interval, the +/- margin as dashed reference lines over a light band, zero as a
solid line, and the category per row. Electricity's category label carries a dagger where the overall verdict would
change if its category were any other category (the same computation as tab_decision.py).

Writes paper/figures/fig_intervals.pdf.
"""
from __future__ import annotations

import argparse

from analyze import CATEGORY, HYPOTHESES, OVERALL, overall
from figlib import (BLUE, DATASETS, INK, LIGHT, MUTED, NAME, VERMILLION, ds_key, load_metrics,
                    mpl_setup, save_pdf, write_metrics)

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="paper/figures/fig_intervals.pdf")
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

R = "h-tests"
M = load_metrics(R)
assert M["n_seeds"] == 10
HYPS = (("h1", "H1"), ("h2a", "H2a"), ("h2b", "H2b"))
CAT_SHORT = {0: "no difference", 1: "holds", 2: "contradicted", 3: "inconclusive"}
assert set(CAT_SHORT) == set(CATEGORY)
# Category encoding: marker shape and fill (grayscale-safe) plus colour.
CAT_STYLE = {1: dict(marker="o", mfc=BLUE, color=BLUE),
             2: dict(marker="X", mfc=VERMILLION, color=VERMILLION),
             0: dict(marker="D", mfc="white", color=INK),
             3: dict(marker="o", mfc="white", color=MUTED)}
METRIC_LABEL = {"ece": "difference in plug-in ECE", "brier": "difference in Brier score"}


def elec_pivotal(hid: str) -> bool:
    """Would the overall verdict change if electricity's category were any other category?"""
    cats = {d: int(M[f"{hid}_{ds_key(d)}_cat"]) for d in DATASETS}
    base = overall(list(cats.values()))
    return any(overall([alt if d == "electricity" else c for d, c in cats.items()]) != base
               for alt in CATEGORY if alt != cats["electricity"])


plt = mpl_setup()
fig, axes = plt.subplots(1, len(HYPS), figsize=(6.6, 2.55))
out: dict = {"n_panels": len(HYPS)}
checksum, n_rows = 0.0, 0
for ax, (hid, label) in zip(axes, HYPS):
    metric, treat, comp, sign, margin, role = HYPOTHESES[hid]
    assert role == "confirmatory"
    piv = elec_pivotal(hid)
    out[f"{hid}_elec_pivotal"] = int(piv)
    ax.axvspan(-margin, margin, color=LIGHT, alpha=0.6, lw=0, zorder=0)
    for x in (-margin, margin):
        ax.axvline(x, color=MUTED, lw=0.7, ls=(0, (3, 2)), zorder=1)
    ax.axvline(0, color=INK, lw=0.7, zorder=1)
    xs = [-margin, margin, 0.0]
    ylabels = []
    for r, d in enumerate(DATASETS):
        y = len(DATASETS) - 1 - r
        k = f"{hid}_{ds_key(d)}"
        mean, lo, hi, cat = M[k + "_mean"], M[k + "_lo"], M[k + "_hi"], int(M[k + "_cat"])
        assert lo <= mean <= hi
        st = CAT_STYLE[cat]
        ax.plot([lo, hi], [y, y], color=st["color"], lw=1.4, solid_capstyle="butt", zorder=3)
        ax.plot([mean], [y], marker=st["marker"], ms=5, mfc=st["mfc"], mec=st["color"], mew=0.9,
                ls="none", zorder=4)
        dag = r"$^{\dagger}$" if d == "electricity" and piv else ""
        ax.text(mean, y + 0.2, CAT_SHORT[cat] + dag, ha="center", va="bottom", fontsize=6.3,
                color=st["color"] if cat != 3 else INK)
        xs += [lo, hi]
        checksum += mean + lo + hi + cat
        n_rows += 1
        ylabels.append((y, NAME[d]))
    lo_x, hi_x = min(xs), max(xs)
    pad = 0.12 * (hi_x - lo_x)
    ax.set_xlim(lo_x - pad, hi_x + pad)
    ax.set_ylim(-0.6, len(DATASETS) - 0.35)
    ax.set_yticks([y for y, _ in ylabels])
    ax.set_yticklabels([t for _, t in ylabels] if ax is axes[0] else [])
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.ticklabel_format(axis="x", style="sci", scilimits=(-2, 2), useMathText=True)
    ax.xaxis.get_offset_text().set_fontsize(6.5)
    ax.set_xlabel(METRIC_LABEL[metric], fontsize=7.5)
    v = int(M[f"{hid}_overall_code"])
    assert OVERALL[v] == M[f"{hid}_overall"]
    checksum += v
    tm = {"lr": "LR", "rf": "RF", "hgb": "HGB"}
    cm = {"none": "none", "isotonic": "iso"}
    ax.set_title(f"{label}: {tm[treat[0]]} {cm[treat[1]]} $-$ {tm[comp[0]]} {cm[comp[1]]}\n"
                 f"predicted {'> 0' if sign > 0 else '< 0'}; overall: {OVERALL[v]}",
                 fontsize=7.5, linespacing=1.3)
fig.tight_layout(w_pad=0.6)
save_pdf(fig, args.out)

out.update({"n_rows": n_rows, "checksum_plotted": checksum})
write_metrics(args.metrics, out)
print(f"rows {n_rows}, pivotal {[out[f'{h}_elec_pivotal'] for h, _ in HYPS]}")
