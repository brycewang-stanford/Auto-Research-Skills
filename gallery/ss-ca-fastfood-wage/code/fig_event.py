"""Figure fig-event (analysis_plan 16 and 18): the event path of the selected candidate.

Reads   runs/event-path/event_path.csv   one row per outcome (emp, wage) and quarter: gap, se,
                                         se_s, se_n, lo95, hi95 and the flags covid, in_fit,
                                         post, ab257, ab1228
        runs/event-path/metrics.json     selected, figure_case, figure_note, nu_hat, nu, c_*
Writes  paper/figures/fig_event.pdf, paper/figures/fig_event.caption.md, and the run's
        metrics (--metrics).

Nothing is estimated here. The script redraws the run's gaps and pointwise bands, checks that
the bands equal gap - c x SE with the run's own critical values, and prints the caption from the
run's outputs (candidate, outcome, estimator case and the note design-r2 D11 requires). The
in-fit marker is drawn only when the estimator is SC or SDID: for those, every in_fit quarter
is in-sample fit. For DD the counterfactual uses the base quarter only, and for DDT the trend
window; event_path.csv records neither, so DD and DDT get no in-fit marker and the caption
carries the run's figure_note instead.
"""
from __future__ import annotations

import argparse
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
ap.add_argument("--csv", default="runs/event-path/event_path.csv")
ap.add_argument("--run-metrics", default="runs/event-path/metrics.json")
ap.add_argument("--out", default="paper/figures/fig_event.pdf")
ap.add_argument("--caption", default="paper/figures/fig_event.caption.md")
ap.add_argument("--metrics", default="runs/fig-event/metrics.json")
args = ap.parse_args()

W = args.csv
M = F.load_json(args.run_metrics)
rows = F.load_csv(W)

# ----------------------------------------------------------------------------- read and check
selected = F.need(M, "selected", args.run_metrics)
cand = F.parse_candidate(selected)
case = F.need(M, "figure_case", args.run_metrics)
if case != cand["est"]:
    raise F.FigureInputError(f"figure_case {case} is not the estimator of {selected}")
note = F.need(M, "figure_note", args.run_metrics)
nu = float(F.need(M, "nu", args.run_metrics))
c = {k: float(F.need(M, f"c_{k}", args.run_metrics)) for k in ("hi95", "hi975", "lo05", "lo025")}
if int(F.need(M, "n_rows", args.run_metrics)) != len(rows):
    raise F.FigureInputError(f"{W}: {len(rows)} rows, metrics say {M['n_rows']}")

OUTCOMES = ("emp", "wage")
series = {}
for o in OUTCOMES:
    rs = [r for r in rows if F.need(r, "outcome", W) == o]
    if not rs:
        raise F.FigureInputError(f"{W}: no rows for outcome '{o}'")
    pts = []
    for r in rs:
        q = F.quarter_index(F.need(r, "quarter", W))
        g, se = F.fnum(r, "gap", W), F.fnum(r, "se", W)
        se_s, se_n = F.fnum(r, "se_s", W), F.fnum(r, "se_n", W)
        lo, hi = F.fnum(r, "lo95", W), F.fnum(r, "hi95", W)
        where = f"{W} {o} {r['quarter']}"
        if not F.close(se, max(se_s, se_n), 1e-7):
            raise F.FigureInputError(f"{where}: se is not max(se_s, se_n)")
        # %.10g in the csv: compare on the scale of the gap, not relative to a near-zero bound
        tol = 1e-8 * max(1.0, abs(g) + abs(c["hi975"] * se))
        if abs(lo - (g - c["hi975"] * se)) > tol or abs(hi - (g - c["lo025"] * se)) > tol:
            raise F.FigureInputError(f"{where}: band is not gap - c x SE with the run's c")
        flags = {k: int(F.need(r, k, W)) for k in ("covid", "in_fit", "post", "ab257", "ab1228")}
        pts.append({"q": q, "gap": g, "se": se, "lo": lo, "hi": hi, **flags})
    pts.sort(key=lambda p: p["q"])
    qs = [p["q"] for p in pts]
    if qs != list(range(qs[0], qs[0] + len(qs))):
        raise F.FigureInputError(f"{W}: quarters of '{o}' are not consecutive and unique")
    for k in ("ab257", "ab1228"):
        if sum(p[k] for p in pts) != 1:
            raise F.FigureInputError(f"{W}: '{o}' has {sum(p[k] for p in pts)} rows flagged {k}")
    if any(p["covid"] and (p["in_fit"] or p["post"]) for p in pts):
        raise F.FigureInputError(f"{W}: a COVID quarter is flagged in_fit or post")
    series[o] = pts

if [p["q"] for p in series["emp"]] != [p["q"] for p in series["wage"]]:
    raise F.FigureInputError(f"{W}: the two outcomes have different quarters")
flag_cols = ("covid", "in_fit", "post", "ab257", "ab1228")
if any(tuple(a[k] for k in flag_cols) != tuple(b[k] for k in flag_cols)
       for a, b in zip(series["emp"], series["wage"])):
    raise F.FigureInputError(f"{W}: the two outcomes have different quarter flags")

ref = series["emp"]
qs = [p["q"] for p in ref]
q_first, q_last = qs[0], qs[-1]
covid_q = [p["q"] for p in ref if p["covid"]]
post_q = [p["q"] for p in ref if p["post"]]
fit_q = [p["q"] for p in ref if p["in_fit"]]
q_ab257 = next(p["q"] for p in ref if p["ab257"])
q_ab1228 = next(p["q"] for p in ref if p["ab1228"])
mark_fit = case in ("SC", "SDID")
if not fit_q or not post_q:
    raise F.FigureInputError(f"{W}: no fit-window or no post-window quarter is flagged")
q_base = max(fit_q)                      # B: the last quarter of every real fit window
between = [q for q in qs if q_base < q < min(post_q)]
if any(q in covid_q for q in between):
    raise F.FigureInputError(f"{W}: unexpected quarters between the fit and post windows")
REFIT = {"DD": "", "DDT": ", its trend fitted on the wage", "SC": ", its weights fitted on the wage",
         "SDID": ", its unit and time weights fitted on the wage"}


def runs_of(quarters):
    """Contiguous blocks of quarter indices, as (first, last)."""
    out = []
    for q in sorted(quarters):
        if out and q == out[-1][1] + 1:
            out[-1][1] = q
        else:
            out.append([q, q])
    return [tuple(b) for b in out]


# ----------------------------------------------------------------------------- figure
plt = F.mpl_setup()
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

fig, axes = plt.subplots(2, 1, figsize=(6.9, 5.2), sharex=True, gridspec_kw={"hspace": 0.28})
titles = {"emp": f"(a) Employment: {F.OUTCOME_NAME[cand['norm']]}",
          "wage": f"(b) Wage: {F.OUTCOME_NAME['W']}"}
for ax, o in zip(axes, OUTCOMES):
    pts = series[o]
    x = [p["q"] for p in pts]
    y = [F.SCALE * p["gap"] for p in pts]
    lo = [F.SCALE * p["lo"] for p in pts]
    hi = [F.SCALE * p["hi"] for p in pts]
    for a, b in runs_of(covid_q):
        ax.axvspan(a - 0.5, b + 0.5, facecolor="white", edgecolor=F.MUTED,
                   hatch="////", lw=0, zorder=0)
    for a, b in runs_of(post_q):
        ax.axvspan(a - 0.5, b + 0.5, color=F.LIGHT, alpha=0.55, lw=0, zorder=0)
    ax.axhline(0, color=F.MUTED, lw=0.7, zorder=1)
    ax.fill_between(x, lo, hi, color=F.BAND, alpha=0.75, lw=0, step=None, zorder=2)
    ax.plot(x, y, color=F.INK, lw=0.9, zorder=3)
    filled = [i for i, p in enumerate(pts) if not mark_fit or p["in_fit"]]
    hollow = [i for i, p in enumerate(pts) if mark_fit and not p["in_fit"]]
    ax.plot([x[i] for i in filled], [y[i] for i in filled], ls="", marker="o", ms=2.8, color=F.INK,
            mew=0.7, zorder=4)
    ax.plot([x[i] for i in hollow], [y[i] for i in hollow], ls="", marker="o", ms=2.8, color=F.INK,
            mfc="white", mew=0.7, zorder=4)
    ax.axvline(q_ab257, color=F.BLUE, lw=0.9, ls=(0, (5, 2)), zorder=1)
    ax.axvline(q_ab1228, color=F.VERMILLION, lw=0.9, ls=(0, (1, 1.2)), zorder=1)
    ax.set_title(titles[o], loc="left")
    ax.set_ylabel(f"California minus\ncounterfactual ({F.UNIT_LABEL})")
    ax.grid(axis="y", color="#e6e6e6", lw=0.5, zorder=0)
    ax.set_xlim(q_first - 0.8, q_last + 0.8)

ymax = axes[0].get_ylim()[1]
for qv, txt, col in ((q_ab257, "AB 257", F.BLUE), (q_ab1228, "AB 1228", F.VERMILLION)):
    axes[0].text(qv + 0.25, ymax, txt, ha="left", va="top", fontsize=7, color=col,
                 bbox={"facecolor": "white", "edgecolor": "none", "pad": 0.6, "alpha": 0.85}, zorder=6)
years = sorted({q // 4 for q in qs})
axes[-1].set_xticks([4 * yv for yv in years if q_first <= 4 * yv <= q_last])
axes[-1].set_xticklabels([str(yv) for yv in years if q_first <= 4 * yv <= q_last])
axes[-1].set_xlabel("Quarter (tick = first quarter of the year)")

handles = [Line2D([], [], color=F.INK, lw=0.9, marker="o", ms=2.8, label="gap"),
           Patch(facecolor=F.BAND, alpha=0.75, label="pointwise 95% band"),
           Patch(facecolor="white", edgecolor=F.MUTED, hatch="////", lw=0, label="COVID quarters"),
           Patch(facecolor=F.LIGHT, alpha=0.55, label="post window"),
           Line2D([], [], color=F.BLUE, lw=0.9, ls=(0, (5, 2)), label=f"AB 257 enacted ({F.quarter_label(q_ab257)})"),
           Line2D([], [], color=F.VERMILLION, lw=0.9, ls=(0, (1, 1.2)), label=f"first quarter after AB 1228 was signed ({F.quarter_label(q_ab1228)})")]
if mark_fit:
    handles.insert(1, Line2D([], [], color=F.INK, ls="", marker="o", ms=2.8, mfc="white", mew=0.7,
                             label="outside the weight-fit window"))
fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.045), ncol=3,
           frameon=False, fontsize=7, handlelength=1.8, columnspacing=1.1)
F.save_pdf(fig, args.out)

# ----------------------------------------------------------------------------- caption
cov = runs_of(covid_q)
gap_txt = ", ".join(F.quarter_label(q) for q in between) or "none"
pst = runs_of(post_q)
span = lambda blocks: ", ".join(f"{F.quarter_label(a)}–{F.quarter_label(b)}" for a, b in blocks)  # noqa: E731
fit_txt = (f" Filled markers are quarters in the weight-fit window ({len(fit_q)} quarters), where the "
           "gap is in-sample fit; open markers are outside it." if mark_fit else "")
caption = f"""\
# Figure `fig_event.pdf` (run `fig-event`, script `code/fig_event.py`)

Generated from `runs/event-path/event_path.csv` and `runs/event-path/metrics.json`; do not edit
by hand. Any number below that the text also quotes is written there as its claim macro.

**Caption.** Quarterly gap between California and its estimated counterfactual,
{F.quarter_label(q_first)}–{F.quarter_label(q_last)}, for the primary candidate `{selected}`:
{F.describe_candidate(selected)}. Panel (a) is the candidate's employment outcome
({F.OUTCOME_NAME[cand['norm']]}); panel (b) is the {F.OUTCOME_NAME['W']}, with the same estimator,
weighting and pool{REFIT[case]}. Each point is California's outcome minus
the counterfactual the estimator builds from the donors, fitted with the base quarter {F.quarter_label(q_base)}, in {F.UNIT_LABEL} (close to percent for small values).{fit_txt} The shaded band
is a pointwise 95% interval, gap − c_hi(0.975) SE to gap − c_lo(0.025) SE, where SE =
max(SE_s, SE_n) comes from the donors' placebo gaps at that quarter and the critical values are
those of the selected candidate's H2 statistic from run level-mde (t at ν = {F.fmt(nu, '.1f')}
with the decision-set quantile as a floor; c_hi(0.975) = {F.fmt(c['hi975'])}, c_lo(0.025) =
{F.fmt(c['lo025'])}); both panels use these critical values, as the run does. Hatched: COVID
quarters ({span(cov)}), excluded from every fit window. Light shading: the post window
({span(pst)}). Dashed line: {F.quarter_label(q_ab257)}, the quarter AB 257 was enacted
(September 2022). Dotted line: {F.quarter_label(q_ab1228)}, the first quarter after AB 1228 was
signed (28 September 2023). The quarters after the last fit-window quarter ({F.quarter_label(q_base)})
and before the post window ({gap_txt}) are in neither window.

**Reading (estimator case {case}).** {note[0].upper() + note[1:]}.

**What the figure does not show.** The bands are pointwise, not simultaneous, so a quarter
whose band excludes zero is not a test that the path is zero{', and no pre-period part of the figure is a pre-trend test' if case != 'DD' else ''}. The figure is report-only: no hypothesis label is read from
it. The pooled post-window estimates, their intervals and the hypothesis labels come
from runs h2-emp (employment) and h1-wage (wage); the per-quarter bands here use per-quarter
standard errors and are not those intervals.
"""
F.write_text(args.caption, caption)

F.write_metrics(args.metrics, {
    "selected": selected, "figure_case": case, "in_fit_marked": int(mark_fit),
    "n_quarters": len(qs), "first_quarter": F.quarter_label(q_first),
    "last_quarter": F.quarter_label(q_last), "n_covid": len(covid_q), "n_post": len(post_q),
    "n_in_fit": len(fit_q), "nu": nu,
    "checksum_emp": sum(p["gap"] + p["lo"] + p["hi"] for p in series["emp"]),
    "checksum_wage": sum(p["gap"] + p["lo"] + p["hi"] for p in series["wage"]),
    "ylim_emp_low": axes[0].get_ylim()[0], "ylim_emp_high": axes[0].get_ylim()[1],
    "ylim_wage_low": axes[1].get_ylim()[0], "ylim_wage_high": axes[1].get_ylim()[1],
})
print(f"fig-event: {selected} ({case}), {len(qs)} quarters -> {args.out}")
