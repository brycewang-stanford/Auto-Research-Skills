"""Figure fig-select (analysis_plan 1 and 18): the 24 candidates' pre-period RMSEs.

Reads   runs/select/metrics.json     rmse_<id>, maxabs_<id>, selected, selected_rmse, tie_used,
                                     n_tied_at_4dp, n_candidates, n_pseudo_dates, pseudo_dates,
                                     input_last_quarter
        runs/select/pseudo_atts.csv  candidate, pseudo_date, tau (24 x 6 rows, design order)
Writes  paper/figures/fig_select.pdf, paper/figures/fig_select.caption.md, and the run's
        metrics (--metrics).

Nothing is estimated here. Panel (a) draws each candidate's RMSE as a bar from zero; panel (b)
draws the six pseudo-ATTs behind it, so the spread of the criterion is visible. The script checks
that the RMSEs and max |tau| in metrics.json equal those recomputed from pseudo_atts.csv, that
the selected candidate has the smallest RMSE at four decimals (the first step of the selection
rule), and that select read no quarter after 2019Q4.
"""
from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
# code/select.py shadows the standard-library module 'select' (reached by matplotlib through
# subprocess -> selectors); load the standard one before code/ is on the path.
sys.path[:] = [p for p in sys.path if str(Path(p or ".").resolve()) != _HERE]
import select  # noqa: E402,F401  (standard library)
sys.path.insert(0, _HERE)

import figlib as F  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--csv", default="runs/select/pseudo_atts.csv")
ap.add_argument("--run-metrics", default="runs/select/metrics.json")
ap.add_argument("--out", default="paper/figures/fig_select.pdf")
ap.add_argument("--caption", default="paper/figures/fig_select.caption.md")
ap.add_argument("--metrics", default="runs/fig-select/metrics.json")
args = ap.parse_args()

CSV, MJ = args.csv, args.run_metrics
M = F.load_json(MJ)
rows = F.load_csv(CSV)

# ----------------------------------------------------------------------------- read and check
order = []                      # candidates in the order select wrote them (the design's order)
taus: dict[str, list[tuple[int, float]]] = {}
for r in rows:
    cid = F.need(r, "candidate", CSV)
    if cid not in taus:
        order.append(cid)
        taus[cid] = []
    taus[cid].append((F.quarter_index(F.need(r, "pseudo_date", CSV)), F.fnum(r, "tau", CSV)))

n_cand = int(F.need(M, "n_candidates", MJ))
n_dates = int(F.need(M, "n_pseudo_dates", MJ))
dates = [F.quarter_index(d) for d in str(F.need(M, "pseudo_dates", MJ)).split(",")]
if len(order) != n_cand or len(dates) != n_dates:
    raise F.FigureInputError(f"{CSV}: {len(order)} candidates / {len(dates)} dates, metrics say "
                             f"{n_cand} / {n_dates}")
if sorted(dates) != list(range(min(dates), min(dates) + len(dates))):
    raise F.FigureInputError("the pseudo-dates are not consecutive quarters (the caption says they are)")
rmse_keys = sorted(k[len("rmse_"):] for k in M if k.startswith("rmse_"))
if rmse_keys != sorted(order):
    raise F.FigureInputError("the candidates in pseudo_atts.csv and the rmse_ metrics differ")
for cid in order:
    F.parse_candidate(cid)
    got = sorted(q for q, _ in taus[cid])
    if got != sorted(dates):
        raise F.FigureInputError(f"{CSV}: {cid} has pseudo-dates {got}, metrics list {dates}")
    t = [v for _, v in taus[cid]]
    rm = math.sqrt(sum(v * v for v in t) / len(t))
    if not F.close(rm, float(M[f"rmse_{cid}"]), 1e-8):
        raise F.FigureInputError(f"{cid}: RMSE from the csv {rm} != metrics {M[f'rmse_{cid}']}")
    if not F.close(max(abs(v) for v in t), float(F.need(M, f"maxabs_{cid}", MJ)), 1e-8):
        raise F.FigureInputError(f"{cid}: max |tau| from the csv != metrics")

last_q = str(F.need(M, "input_last_quarter", MJ))
if F.quarter_index(last_q) > F.quarter_index("2019Q4"):
    raise F.FigureInputError(f"select read data through {last_q}; the design stops at 2019Q4")
selected = F.need(M, "selected", MJ)
if selected not in order:
    raise F.FigureInputError(f"selected candidate {selected} is not among the candidates")
rmse = {cid: float(M[f"rmse_{cid}"]) for cid in order}
if not F.close(rmse[selected], float(F.need(M, "selected_rmse", MJ)), 1e-12):
    raise F.FigureInputError("selected_rmse is not the RMSE of the selected candidate")
if round(rmse[selected], 4) != min(round(v, 4) for v in rmse.values()):
    raise F.FigureInputError("the selected candidate does not have the smallest RMSE at 4 decimals")
tie_used = int(F.need(M, "tie_used", MJ))
n_tied = int(F.need(M, "n_tied_at_4dp", MJ))

# ----------------------------------------------------------------------------- figure
plt = F.mpl_setup()
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

n = len(order)
fig, (axa, axb) = plt.subplots(1, 2, figsize=(6.9, 0.17 * n + 1.3), sharey=True,
                               gridspec_kw={"width_ratios": [1.0, 1.25], "wspace": 0.08})
ys = list(range(n))[::-1]                                       # design order, top to bottom
ypos = dict(zip(order, ys))
fam = [F.parse_candidate(c)["est"] for c in order]
for i in range(1, n):                                           # rule between estimator families
    if fam[i] != fam[i - 1]:
        for ax in (axa, axb):
            ax.axhline(ys[i] + 0.5, color=F.LIGHT, lw=0.6, zorder=0)

for cid in order:
    y, sel = ypos[cid], cid == selected
    axa.barh(y, F.SCALE * rmse[cid], height=0.62, color=F.INK if sel else F.LIGHT,
             edgecolor=F.INK, lw=0.4, zorder=2)
    vals = [F.SCALE * v for _, v in sorted(taus[cid])]
    axb.plot([min(vals), max(vals)], [y, y], color=F.MUTED, lw=0.6, zorder=1)
    axb.plot(vals, [y] * len(vals), ls="", marker="o", ms=2.6, color=F.INK,
             mfc=F.INK if sel else "white", mew=0.6, zorder=2)
xmax = F.SCALE * max(rmse.values())
axa.text(F.SCALE * rmse[selected] + 0.02 * xmax, ypos[selected], "selected", ha="left", va="center",
         fontsize=7, weight="bold")
axa.set_xlim(0, 1.25 * xmax)
axa.set_yticks(ys)
axa.set_yticklabels(order, fontsize=7)
for lab in axa.get_yticklabels():
    if lab.get_text() == selected:
        lab.set_fontweight("bold")
axa.tick_params(axis="y", length=0)
axa.set_ylim(-0.7, n - 0.3)
axa.set_xlabel(f"RMSE of the {n_dates} pseudo-ATTs ({F.UNIT_LABEL})")
axa.set_title("(a) Selection criterion RMSE$_c$", loc="left")
axa.grid(axis="x", color="#e6e6e6", lw=0.5, zorder=0)
axb.axvline(0, color=F.MUTED, lw=0.7, zorder=0)
axb.set_xlabel(f"Pseudo-ATT at each pseudo-date ({F.UNIT_LABEL})")
axb.set_title(f"(b) The {n_dates} pseudo-ATTs behind each RMSE", loc="left")
axb.grid(axis="x", color="#e6e6e6", lw=0.5, zorder=0)
axb.tick_params(axis="y", length=0)
lim = max(abs(v) for c in order for _, v in taus[c]) * F.SCALE * 1.08
axb.set_xlim(-lim, lim)
handles = [Patch(facecolor=F.INK, edgecolor=F.INK, label="selected candidate"),
           Patch(facecolor=F.LIGHT, edgecolor=F.INK, lw=0.4, label="other candidates"),
           Line2D([], [], ls="", marker="o", ms=2.6, color=F.INK, mfc="white", mew=0.6,
                  label="pseudo-ATT (filled: selected)"),
           Line2D([], [], color=F.MUTED, lw=0.6, label=f"range of the {n_dates}")]
fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.04), ncol=4, frameon=False,
           fontsize=7, handlelength=1.6, columnspacing=1.2)
F.save_pdf(fig, args.out)

# ----------------------------------------------------------------------------- caption
date_txt = ", ".join(F.quarter_label(q) for q in sorted(dates))
tie_txt = (f"The RMSEs of {n_tied} candidates are equal at four decimals, so the tie-break "
           "(smaller max |pseudo-ATT|, then the earlier candidate in the design's order) chose "
           "among them." if tie_used else
           "No other candidate has the same RMSE at four decimals, so the tie-break was not used.")
caption = f"""\
# Figure `fig_select.pdf` (run `fig-select`, script `code/fig_select.py`)

Generated from `runs/select/metrics.json` and `runs/select/pseudo_atts.csv`; do not edit by
hand. Any number below that the text also quotes is written there as its claim macro.

**Caption.** Pre-period selection of the primary estimator. Each row is one of the {n}
candidates (estimator, donor weighting where it applies, employment outcome E or P, donor pool
D20 or R50), in the design's order. At each of the {n_dates} pseudo-dates ({date_txt}), California is
treated as if the law had started then, and the candidate's pseudo-ATT is its pooled estimate
over the eight quarters three to ten quarters after the pseudo-date. AB 1228 did not exist
then, so a pseudo-ATT measures how far the candidate's counterfactual misses California's path;
it also contains anything else specific to California in those quarters, such as the rises in
its general minimum wage (design threat T17). Panel (a): RMSE$_c$, the root mean square of the {n_dates} pseudo-ATTs, in
{F.UNIT_LABEL} of employment (P candidates read on the log-employment scale); the bars start at
zero. Panel (b): the {n_dates} pseudo-ATTs behind each RMSE and their range. The selection run read
data through {last_q} only. The selected candidate, `{selected}` ({F.describe_candidate(selected)}),
is the one with the smallest RMSE (black bar, filled markers). {tie_txt}

**What the figure does not show.** The RMSEs are a pre-period placebo criterion, not estimates
with a sampling interval, so no confidence interval is drawn; panel (b) shows their spread. The
{n_dates} pseudo-dates are consecutive quarters whose eight-quarter windows overlap, so the
{n_dates} pseudo-ATTs are not {n_dates} independent draws, and a small difference between two RMSEs is not
evidence that one estimator is better. The figure says nothing about any quarter after
{last_q} and nothing about the effect of the law.
"""
F.write_text(args.caption, caption)

F.write_metrics(args.metrics, {
    "selected": selected, "n_candidates": n, "n_pseudo_dates": n_dates, "tie_used": tie_used,
    "n_tied_at_4dp": n_tied, "input_last_quarter": last_q,
    "selected_rank": sorted(order, key=lambda c: (rmse[c], order.index(c))).index(selected) + 1,
    "checksum_rmse": sum(rmse.values()),
    "checksum_tau": sum(v for c in order for _, v in taus[c]),
    "xlim_rmse_high": axa.get_xlim()[1], "xlim_tau": lim,
})
print(f"fig-select: {n} candidates, selected {selected} -> {args.out}")
