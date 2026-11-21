"""Figure fig-placebo (analysis_plan 4 and 18): California's H2 estimate against the placebos.

Reads   runs/h2-emp/placebos.csv    state_fips, abbr, pop_base, tau, tau_scaled (one row per donor)
        runs/h2-emp/metrics.json    selected, outcome, base, post, nu, J, h2_att, h2_se, h2_se_s,
                                    h2_se_n, h2_J, h2_lo95, h2_hi95, h2_lo90, h2_hi90, h2_c_*
        runs/level-mde/metrics.json selected, sdid_floor_h2, pool_h2, qcal_<pool>_* (whether the
                                    SDID Monte Carlo floor applies, and its values)
Writes  paper/figures/fig_placebo.pdf, paper/figures/fig_placebo.caption.md, and the run's
        metrics (--metrics).

Nothing is estimated here. Each donor's placebo estimate is drawn unscaled (open marker; SE_n
is their root mean square) and scaled by sqrt(pop_j / pop_CA) (filled marker; SE_s is their
root mean square), next to California's pooled estimate with its 90% and 95% intervals. The
script checks that SE_s, SE_n, SE and the intervals in metrics.json follow from placebos.csv and
the run's critical values, and that every donor was scaled by the same California population.
"""
from __future__ import annotations

import argparse
import math

import figlib as F

ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
ap.add_argument("--csv", default="runs/h2-emp/placebos.csv")
ap.add_argument("--run-metrics", default="runs/h2-emp/metrics.json")
ap.add_argument("--level-metrics", default="runs/level-mde/metrics.json")
ap.add_argument("--out", default="paper/figures/fig_placebo.pdf")
ap.add_argument("--caption", default="paper/figures/fig_placebo.caption.md")
ap.add_argument("--metrics", default="runs/fig-placebo/metrics.json")
args = ap.parse_args()

CSV, MJ = args.csv, args.run_metrics
M = F.load_json(MJ)
rows = F.load_csv(CSV)

# ----------------------------------------------------------------------------- read and check
selected = F.need(M, "selected", MJ)
cand = F.parse_candidate(selected)
g = lambda k: float(F.need(M, k, MJ))  # noqa: E731
att, se, se_s, se_n = g("h2_att"), g("h2_se"), g("h2_se_s"), g("h2_se_n")
ci = {k: g(f"h2_{k}") for k in ("lo95", "hi95", "lo90", "hi90")}
c = {k: g(f"h2_c_{k}") for k in ("hi95", "hi975", "lo05", "lo025")}
FLOOR = F.sdid_floor(F.load_json(args.level_metrics), args.level_metrics, selected, c,
                     ("hi95", "hi975", "lo05", "lo025"))
nu = g("nu")
J = int(F.need(M, "J", MJ))
if int(F.need(M, "h2_J", MJ)) != J or len(rows) != J:
    raise F.FigureInputError(f"{CSV}: {len(rows)} donors; metrics J = {J}, h2_J = {M['h2_J']}")

don = []
for r in rows:
    d = {"fips": F.need(r, "state_fips", CSV), "abbr": F.need(r, "abbr", CSV),
         "pop": F.fnum(r, "pop_base", CSV), "tau": F.fnum(r, "tau", CSV),
         "tau_s": F.fnum(r, "tau_scaled", CSV)}
    if d["pop"] <= 0:
        raise F.FigureInputError(f"{CSV}: {d['fips']} has a non-positive population")
    don.append(d)
if len({d["fips"] for d in don}) != J:
    raise F.FigureInputError(f"{CSV}: duplicate donors")

rms = lambda v: math.sqrt(sum(x * x for x in v) / len(v))  # noqa: E731
if not F.close(rms([d["tau_s"] for d in don]), se_s, 1e-7):
    raise F.FigureInputError("SE_s in metrics is not the RMS of the scaled placebos")
if not F.close(rms([d["tau"] for d in don]), se_n, 1e-7):
    raise F.FigureInputError("SE_n in metrics is not the RMS of the unscaled placebos")
if not F.close(se, max(se_s, se_n), 1e-12):
    raise F.FigureInputError("SE in metrics is not max(SE_s, SE_n)")
# tau_scaled = tau sqrt(pop_j / pop_CA): the implied pop_CA must be the same for every donor
implied = [d["pop"] * (d["tau"] / d["tau_s"]) ** 2 for d in don if d["tau"] != 0 and d["tau_s"] != 0]
if implied and (max(implied) - min(implied)) > 1e-6 * max(implied):
    raise F.FigureInputError(f"{CSV}: the placebos were not scaled by one California population")
tol = 1e-10 * max(1.0, abs(att) + abs(c["hi975"] * se))
for k, want in (("lo95", att - c["hi975"] * se), ("hi95", att - c["lo025"] * se),
                ("lo90", att - c["hi95"] * se), ("hi90", att - c["lo05"] * se)):
    if abs(ci[k] - want) > tol:
        raise F.FigureInputError(f"h2_{k} is not att - c x SE with the run's critical values")
pop_ca = sum(implied) / len(implied) if implied else float("nan")

# ----------------------------------------------------------------------------- figure
plt = F.mpl_setup()
from matplotlib.lines import Line2D  # noqa: E402

don.sort(key=lambda d: (d["tau_s"], d["fips"]))
n = J + 1
fig, ax = plt.subplots(figsize=(4.6, 0.125 * n + 1.35))
y_ca = n - 1 + 0.6                                              # California on top, set apart
ys = list(range(J))
S = F.SCALE
ax.axvline(0, color=F.MUTED, lw=0.7, zorder=1)
for x in (-se, se):
    ax.axvline(S * x, color=F.INK, lw=0.6, ls=(0, (4, 2)), zorder=1)
for y, d in zip(ys, don):
    ax.plot([S * d["tau"], S * d["tau_s"]], [y, y], color=F.LIGHT, lw=0.8, zorder=2)
    ax.plot([S * d["tau"]], [y], ls="", marker="o", ms=3.0, color=F.INK, mfc="white", mew=0.6, zorder=3)
    ax.plot([S * d["tau_s"]], [y], ls="", marker="o", ms=3.0, color=F.INK, mew=0.6, zorder=4)
ax.axhline(J - 0.5 + 0.3, color=F.LIGHT, lw=0.6, zorder=0)
ax.plot([S * ci["lo95"], S * ci["hi95"]], [y_ca, y_ca], color=F.VERMILLION, lw=0.9,
        solid_capstyle="butt", zorder=3)
ax.plot([S * ci["lo90"], S * ci["hi90"]], [y_ca, y_ca], color=F.VERMILLION, lw=2.6,
        solid_capstyle="butt", zorder=3)
ax.plot([S * att], [y_ca], ls="", marker="s", ms=4.6, color=F.INK, mec="white", mew=0.5, zorder=5)
ax.set_yticks([y_ca] + ys)
ax.set_yticklabels(["California"] + [d["abbr"] for d in don], fontsize=6.5)
ax.get_yticklabels()[0].set_fontweight("bold")
ax.tick_params(axis="y", length=0)
ax.set_ylim(-0.8, y_ca + 0.9)
xs = [S * v for d in don for v in (d["tau"], d["tau_s"])] + [S * ci["lo95"], S * ci["hi95"], S * se, -S * se]
pad = 0.06 * (max(xs) - min(xs))
ax.set_xlim(min(xs) - pad, max(xs) + pad)
ax.set_xlabel(f"Pooled post-window estimate ({F.UNIT_LABEL} of employment)")
ax.grid(axis="x", color="#e6e6e6", lw=0.5, zorder=0)
handles = [Line2D([], [], ls="", marker="s", ms=4.6, color=F.INK, label="California"),
           Line2D([], [], color=F.VERMILLION, lw=2.6, label="90% CI"),
           Line2D([], [], color=F.VERMILLION, lw=0.9, label="95% CI"),
           Line2D([], [], ls="", marker="o", ms=3.0, color=F.INK, label="placebo, scaled"),
           Line2D([], [], ls="", marker="o", ms=3.0, color=F.INK, mfc="white", mew=0.6,
                  label="placebo, unscaled"),
           Line2D([], [], color=F.INK, lw=0.6, ls=(0, (4, 2)), label="± SE")]
fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, -0.06 if J > 30 else -0.11),
           ncol=3, frameon=False, fontsize=7, handlelength=1.6, columnspacing=1.0)
F.save_pdf(fig, args.out)

# ----------------------------------------------------------------------------- caption
which = "SE_s (scaled)" if se_s >= se_n else "SE_n (unscaled)"
caption = f"""\
# Figure `fig_placebo.pdf` (run `fig-placebo`, script `code/fig_placebo.py`)

Generated from {F.file_list([CSV, MJ, args.level_metrics])}; do not edit by hand.
Any number below that the text also quotes is written there as its claim macro.

**Caption.** California's pooled estimate for H2 against the placebo estimates of its {J}
donors. Outcome: {F.OUTCOME_NAME[cand['norm']]}; estimator `{selected}`
({F.describe_candidate(selected)}); base quarter {F.need(M, 'base', MJ)}, post window {F.need(M, 'post', MJ)};
values in {F.UNIT_LABEL}. Each donor's placebo is the same estimate with that donor treated and
the other {J - 1} donors as its pool. Open markers: the placebo estimate; filled markers: the
same estimate times sqrt(pop_j / pop_CA), with populations at the base quarter. SE_n is the
root mean square of the unscaled placebos and SE_s that of the scaled ones; the inference uses
SE = max(SE_s, SE_n), here {which}, and the dashed lines mark ± SE. California's 90% interval
(thick) and 95% interval (thin) are estimate − c × SE with the critical values of run
level-mde's H2 statistic (t at ν = {F.fmt(nu, '.1f')} with {FLOOR['phrase']}),
as in run h2-emp.{FLOOR['sentence']} Donors are sorted by their scaled placebo.

**What the figure does not show.** The donors' placebo estimates are not effects of any
policy; they show how large an estimate this procedure gives where no fast-food law applies.
The figure is not a permutation test: California's rank among the placebos is not the
inference the design uses, and no p-value is read from it. The H2 label comes from the 95% and
90% intervals by the rule of hypotheses[1] (run h2-emp), not from this figure.
"""
F.write_text(args.caption, caption)

F.write_metrics(args.metrics, {
    "selected": selected, "J": J, "se_is_scaled": int(se_s >= se_n), "nu": nu,
    "sdid_floor": FLOOR["applies"], "sdid_floor_binding": ",".join(FLOOR["binding"]),
    "implied_pop_ca": pop_ca,
    "checksum_placebos": sum(d["tau"] + d["tau_s"] for d in don),
    "checksum_ca": att + sum(ci.values()),
    "xlim_low": ax.get_xlim()[0], "xlim_high": ax.get_xlim()[1],
})
print(f"fig-placebo: {J} donors, {selected} -> {args.out}")
