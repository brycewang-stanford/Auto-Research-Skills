"""Figure fig-chr: H4 Conley-Hansen-Rossi (CHR) union bounds for the Panel A coefficient on
schooling, and the H3(b) profile robust Anderson-Rubin statistic for Panel B col 6.

Planned in plan.json design.analysis_plan step 12 (task f-fig-chr). No new statistic: every
number drawn is read from files that the logged runs h4-chr and h3b-subvector wrote, and the
only computation is comparing logged statistics with their planned critical values.

INPUT CONTRACT (the column and key names below are what this script reads; design.method
fixes the content, these names fix the spelling):

1. runs/h4-chr/chr_grid.csv  (--grid) one row per (spec, delta); extra columns are ignored.
     spec     "A6" or "A5" (case-insensitive)
     delta    bound on the direct effect of nearc4 on lwage76; must include the planned
              values 0, 0.005, 0.010, 0.015, 0.020 for both specs (more values are drawn too)
     ar_lo, ar_hi      bounds of the union over gamma0 in [0, delta] of the robust (HC1) 95%
                       AR sets for the Panel A coefficient on schooling
     wald_lo, wald_hi  bounds of the Wald-based union (secondary, not robust to weak IV)
   An unbounded side is written as -inf / inf.

2. runs/h4-chr/metrics.json  (--chr-metrics) the AR-based breakdown delta* for each spec:
     a6_pacoef_chr_breakdown, a5_pacoef_chr_breakdown
   (the claim ids of design.claims_plan with '-' or '_'; both spellings are accepted).

3. runs/h3b-subvector/profile.csv  (--profile) one row per point of the H3(b) point list
   (fine grid b0 in [-1, 1], step 5e-4, plus the 2 x 400 log-spaced outer points out to
   |b0| = 1e5), in any order; extra columns are ignored.
     b0       hypothesised coefficient on ed76
     m        profile robust projection statistic m(b0) = min_g HAR(b0, g)
     kappa_p  smallest root (GKMC / GKM19 statistic)
     kappa_1  largest root
     c_gkm19  GKM19 critical value at kappa_1(b0), Table 3 interpolation (3T), reported set
     c_gkm19q GKM19 critical value at kappa_1(b0), eq. (2.12) quantile from ivmodels (3Q)

4. runs/h3b-subvector/metrics.json  (--h3b-metrics) the reported set bounds:
     b6_ar_rob_lo, b6_ar_rob_hi, b6_ar_gkmc_lo, b6_ar_gkmc_hi, b6_ar_gkm19_lo,
     b6_ar_gkm19_hi, b6_ar_gkm19q_lo, b6_ar_gkm19q_hi  (an unbounded side: null or +-Infinity)
     b6_ar_rob_npieces (optional; checked when present)
   (claim ids with '-' or '_').

CHECKS (the script fails rather than draw a picture that disagrees with the ledger):
- chr_grid: lo <= hi; for each spec the union only widens as delta grows; the AR union
  excludes 0 at every delta below delta* - 1e-4 and contains 0 at every delta above
  delta* + 1e-4 (1e-4 = the gamma0 grid step of the run).
- profile: on the logged point list, the accepted pieces of each test (robust: m <= chi2(3)
  95%; GKMC: kappa_p <= chi2(1) 95%; GKM19: kappa_p <= c_gkm19 or c_gkm19q) have their outer
  ends bracketing the logged bisected bounds (the bound lies between the last rejected and
  the first accepted point); a side the metrics call unbounded is accepted at the last outer
  point; the robust piece count equals b6_ar_rob_npieces when that key exists.

PICTURE
(a) For A6 and A5: AR-based union bounds against delta (solid, markers at the logged deltas;
    the lines only connect them), Wald-based union (dashed), delta* (dotted vertical line).
(b) m(b0) on the plotted window with the chi2(3) 95% line; beneath it, the accepted pieces
    of the four H3(b) sets on the logged point list. A piece that leaves the window ends in an
    arrow labelled with its logged bound (or infinity); a piece wholly outside the window is
    listed at the window edge. The window is [-1, 1] if any set reaches beyond it, otherwise
    the span of the sets and 0, padded by 10% (override with --xlim).

Output: paper/figures/chr.pdf (vector) and a flat metrics JSON (--metrics) describing what
was drawn. Usage (crew.py run --kind analysis, after h4-chr and h3b-subvector):
    .venv/bin/python code/fig_chr.py --metrics runs/fig-chr/metrics.json
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import numpy as np
from scipy.stats import chi2

ap = argparse.ArgumentParser()
ap.add_argument("--grid", default="runs/h4-chr/chr_grid.csv")
ap.add_argument("--chr-metrics", default="runs/h4-chr/metrics.json")
ap.add_argument("--profile", default="runs/h3b-subvector/profile.csv")
ap.add_argument("--h3b-metrics", default="runs/h3b-subvector/metrics.json")
ap.add_argument("--out", default="paper/figures/chr.pdf")
ap.add_argument("--metrics", required=True)
ap.add_argument("--xlim", nargs=2, type=float, default=None, help="panel (b) window")
args = ap.parse_args()

PLANNED_DELTAS = (0.0, 0.005, 0.010, 0.015, 0.020)   # design.method H4
GAMMA0_STEP = 1e-4                                   # design.method H4 union grid step
FINE_HALF = 1.0                                      # design.method H3(b) fine grid [-1, 1]
CRIT_ROB = float(chi2.ppf(0.95, 3))                  # robust projection, chi2(3) 95%
CRIT_GKMC = float(chi2.ppf(0.95, 1))                 # GKMC, chi2(k_Z - m_W = 1) 95%
assert abs(CRIT_ROB - 7.814728) < 1e-6 and abs(CRIT_GKMC - 3.841459) < 1e-6
SPECS = (("A6", "Panel A col. 6 (with family background)"),
         ("A5", "Panel A col. 5"))
SETS = (("rob", "Robust projection (primary)"),
        ("gkmc", "GKMC (homoskedastic)"),
        ("gkm19", "GKM19, Table 3 c.v. (reported)"),
        ("gkm19q", "GKM19, eq. (2.12) c.v."))

# One palette for the paper (Okabe-Ito); every encoding also has a grayscale cue.
INK, MUTED, LIGHT = "#222222", "#8a8a8a", "#d9d9d9"
BLUE, VERMILLION = "#0072B2", "#D55E00"
SPEC_STYLE = {"A6": dict(color=BLUE, marker="o"), "A5": dict(color=VERMILLION, marker="s")}


# ---------------------------------------------------------------- reading
def read_csv(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise SystemExit(f"{path}: no rows")
    return rows


def need_columns(path: str, rows: list[dict], cols: tuple) -> None:
    missing = [c for c in cols if c not in rows[0]]
    if missing:
        raise SystemExit(f"{path}: missing column(s) {missing}; found {list(rows[0])}. "
                         "See the input contract in code/fig_chr.py.")


def fnum(x, where: str) -> float:
    """A logged number; inf / -inf allowed (unbounded side), empty or NaN not."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise SystemExit(f"{where}: not a number: {x!r}") from None
    if math.isnan(v):
        raise SystemExit(f"{where}: NaN")
    return v


def metric(m: dict, claim_id: str, where: str, *, side: int = 0, optional: bool = False):
    """Metric named after a claim id, with '-' or '_'. side = -1/+1: None or +-inf = unbounded."""
    keys = [k for k in {claim_id, claim_id.replace("-", "_")} if k in m]
    if not keys:
        if optional:
            return None
        raise SystemExit(f"{where}: no key {claim_id.replace('-', '_')!r} (or {claim_id!r}); "
                         f"keys present: {sorted(m)}")
    vals = {json.dumps(m[k]) for k in keys}
    if len(vals) > 1:
        raise SystemExit(f"{where}: {keys} disagree")
    v = m[keys[0]]
    if v is None and side:
        return side * math.inf
    v = fnum(v, f"{where}:{keys[0]}")
    if math.isinf(v) and (not side or v * side < 0):
        raise SystemExit(f"{where}:{keys[0]} = {v} is not allowed here")
    return v


def load_json(path: str) -> dict:
    # json accepts Infinity / -Infinity / NaN, which Python's json.dump writes
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------- panel (a) data and checks
grid_rows = read_csv(args.grid)
need_columns(args.grid, grid_rows, ("spec", "delta", "ar_lo", "ar_hi", "wald_lo", "wald_hi"))
chr_m = load_json(args.chr_metrics)
union: dict[str, dict] = {}
for s, _ in SPECS:
    rows = [r for r in grid_rows if r["spec"].strip().upper() == s]
    if not rows:
        raise SystemExit(f"{args.grid}: no rows for spec {s}")
    rows.sort(key=lambda r: fnum(r["delta"], args.grid))
    d = np.array([fnum(r["delta"], f"{args.grid} {s} delta") for r in rows])
    cols = {c: np.array([fnum(r[c], f"{args.grid} {s} delta={r['delta']} {c}") for r in rows])
            for c in ("ar_lo", "ar_hi", "wald_lo", "wald_hi")}
    assert np.all(np.diff(d) > 0), f"{s}: repeated delta in {args.grid}"
    for pd_ in PLANNED_DELTAS:
        assert np.any(np.abs(d - pd_) < 1e-12), f"{s}: planned delta {pd_} missing from {args.grid}"
    assert d.min() >= 0
    for kind in ("ar", "wald"):
        lo, hi = cols[f"{kind}_lo"], cols[f"{kind}_hi"]
        assert np.all(lo <= hi), f"{s} {kind}: lo > hi"
        # unions over nested gamma0 ranges can only widen
        assert np.all(lo[1:] <= lo[:-1] + 1e-12) and np.all(hi[1:] >= hi[:-1] - 1e-12), \
            f"{s} {kind}: union does not widen with delta"
    dstar = metric(chr_m, f"{s.lower()}-pacoef-chr-breakdown", args.chr_metrics)
    assert dstar >= 0 and math.isfinite(dstar)
    contains0 = (cols["ar_lo"] <= 0) & (cols["ar_hi"] >= 0)
    below, above = d < dstar - GAMMA0_STEP, d > dstar + GAMMA0_STEP
    assert not np.any(contains0 & below), f"{s}: AR union contains 0 below delta* = {dstar}"
    assert np.all(contains0[above]), f"{s}: AR union excludes 0 above delta* = {dstar}"
    union[s] = dict(delta=d, dstar=dstar, **cols)

# ---------------------------------------------------------------- panel (b) data and checks
prof_rows = read_csv(args.profile)
need_columns(args.profile, prof_rows, ("b0", "m", "kappa_p", "kappa_1", "c_gkm19", "c_gkm19q"))
P = {c: np.array([fnum(r[c], f"{args.profile} {c}") for r in prof_rows])
     for c in ("b0", "m", "kappa_p", "kappa_1", "c_gkm19", "c_gkm19q")}
order = np.argsort(P["b0"], kind="stable")
P = {c: v[order] for c, v in P.items()}
b0 = P["b0"]
assert np.all(np.isfinite(b0)) and np.all(np.diff(b0) > 0), "profile: b0 not distinct and finite"
for c in ("m", "kappa_p", "kappa_1", "c_gkm19", "c_gkm19q"):
    assert np.all(np.isfinite(P[c])) and np.all(P[c] >= -1e-9), f"profile: {c} not finite, >= 0"
assert np.all(P["kappa_p"] <= P["kappa_1"] + 1e-9), "profile: kappa_p > kappa_1"
fine = np.abs(b0) <= FINE_HALF + 1e-12
assert fine.sum() >= 1000, "profile: fewer than 1000 points on the fine grid [-1, 1]"

ACCEPT = {"rob": P["m"] <= CRIT_ROB,
          "gkmc": P["kappa_p"] <= CRIT_GKMC,
          "gkm19": P["kappa_p"] <= P["c_gkm19"],
          "gkm19q": P["kappa_p"] <= P["c_gkm19q"]}
h3b_m = load_json(args.h3b_metrics)


def pieces(acc: np.ndarray) -> list[tuple[int, int]]:
    """Index ranges [i, j] of maximal runs of accepted points."""
    out, i, n = [], 0, len(acc)
    while i < n:
        if acc[i]:
            j = i
            while j + 1 < n and acc[j + 1]:
                j += 1
            out.append((i, j))
            i = j + 1
        else:
            i += 1
    return out


def brackets(bound: float, inner: int, outer: int | None, name: str) -> None:
    """The logged bound lies between the first accepted point and its rejected neighbour."""
    if outer is None:   # the accepted run reaches the end of the point list
        assert math.isinf(bound), f"{name}: accepted at the last point but logged bound {bound} is finite"
        return
    assert math.isfinite(bound), f"{name}: logged bound unbounded but point {b0[outer]} rejected"
    a, b = sorted((b0[inner], b0[outer]))
    tol = 1e-6 * max(1.0, abs(bound))
    assert a - tol <= bound <= b + tol, f"{name}: logged bound {bound} outside [{a}, {b}]"


SETINFO: dict[str, dict] = {}
for key, _ in SETS:
    lo = metric(h3b_m, f"b6-ar-{key}-lo", args.h3b_metrics, side=-1)
    hi = metric(h3b_m, f"b6-ar-{key}-hi", args.h3b_metrics, side=+1)
    pc = pieces(ACCEPT[key])
    assert pc, f"{key}: no accepted point on the profile grid; the set is empty?"
    (i0, _), (_, j1) = pc[0], pc[-1]
    brackets(lo, i0, i0 - 1 if i0 > 0 else None, f"{key} lower")
    brackets(hi, j1, j1 + 1 if j1 < len(b0) - 1 else None, f"{key} upper")
    SETINFO[key] = dict(lo=lo, hi=hi, pieces=pc)
npieces = metric(h3b_m, "b6-ar-rob-npieces", args.h3b_metrics, optional=True)
if npieces is not None:
    assert int(npieces) == len(SETINFO["rob"]["pieces"]), \
        f"robust set: {len(SETINFO['rob']['pieces'])} pieces on the grid, metrics say {npieces}"


def piece_ends(key: str, k: int) -> tuple[float, float]:
    """Ends of piece k: logged bisected bounds at the two extremes, grid points inside."""
    info, (i, j) = SETINFO[key], SETINFO[key]["pieces"][k]
    lo = info["lo"] if k == 0 else float(b0[i])
    hi = info["hi"] if k == len(info["pieces"]) - 1 else float(b0[j])
    return lo, hi


# window for panel (b)
if args.xlim:
    XL = tuple(args.xlim)
else:
    ends = [e for key, _ in SETS for k in range(len(SETINFO[key]["pieces"]))
            for e in piece_ends(key, k)]
    if any(abs(e) > FINE_HALF for e in ends):
        XL = (-FINE_HALF, FINE_HALF)
    else:
        lo_, hi_ = min(ends + [0.0]), max(ends + [0.0])
        pad = 0.1 * (hi_ - lo_)
        XL = (max(-FINE_HALF, lo_ - pad), min(FINE_HALF, hi_ + pad))
assert XL[0] < XL[1]


def fmt(v: float) -> str:
    if math.isinf(v):
        return r"$-\infty$" if v < 0 else r"$+\infty$"
    s = f"{v:.3g}" if abs(v) < 1e4 else f"{v:.2e}"
    return s.replace("-", "\N{MINUS SIGN}")


# ---------------------------------------------------------------- figure
import matplotlib  # noqa: E402

matplotlib.use("pdf")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

plt.rcParams.update({
    "font.family": "STIXGeneral", "mathtext.fontset": "stix", "font.size": 8,
    "axes.titlesize": 8.5, "axes.labelsize": 8, "xtick.labelsize": 7.5, "ytick.labelsize": 7.5,
    "legend.fontsize": 7, "axes.linewidth": 0.6, "axes.edgecolor": INK, "axes.labelcolor": INK,
    "text.color": INK, "xtick.color": INK, "ytick.color": INK, "xtick.major.width": 0.6,
    "ytick.major.width": 0.6, "axes.spines.top": False, "axes.spines.right": False,
    "pdf.fonttype": 42,
})
fig = plt.figure(figsize=(6.5, 3.3))
gs = fig.add_gridspec(2, 2, width_ratios=[1, 1.15], height_ratios=[2.0, 1.45],
                      wspace=0.30, hspace=0.10)
axA = fig.add_subplot(gs[:, 0])
axB = fig.add_subplot(gs[0, 1])
axS = fig.add_subplot(gs[1, 1], sharex=axB)

# (a) CHR unions
finite_vals = np.concatenate([np.concatenate([u[c][np.isfinite(u[c])] for c in
                              ("ar_lo", "ar_hi", "wald_lo", "wald_hi")]) for u in union.values()])
ylo, yhi = min(finite_vals.min(), 0.0), max(finite_vals.max(), 0.0)
YA = (ylo - 0.06 * (yhi - ylo), yhi + 0.14 * (yhi - ylo))   # head room for the delta* labels
dmax = max(u["delta"].max() for u in union.values())
off = 0.012 * dmax
axA.axhline(0, color=MUTED, lw=0.6, zorder=1)
n_clipped_a = 0
for idx, (s, _) in enumerate(SPECS):
    u, st = union[s], SPEC_STYLE[s]
    x = u["delta"] + (idx - 0.5) * off           # small offset so the two specs do not overlap
    for kind, ls, lw, mk in (("ar", "-", 1.1, True), ("wald", (0, (4, 2)), 0.8, False)):
        for c, sgn in ((f"{kind}_lo", -1), (f"{kind}_hi", 1)):
            y = u[c].copy()
            inf = ~np.isfinite(y)
            n_clipped_a += int(inf.sum())
            y[inf] = np.nan                       # an unbounded side is not joined to the line
            axA.plot(x, y, color=st["color"], ls=ls, lw=lw, zorder=3,
                     marker=st["marker"] if mk else None, ms=3.0, mfc="white", mew=0.8)
            if inf.any():                         # arrowhead at the axis edge
                axA.plot(x[inf], np.full(inf.sum(), YA[0] if sgn < 0 else YA[1]), ls="none",
                         color=st["color"], marker="v" if sgn < 0 else "^", ms=4, zorder=4,
                         clip_on=False)
    if u["dstar"] <= dmax * 1.05:
        axA.axvline(u["dstar"], color=st["color"], ls=(0, (1, 1.5)), lw=0.9, zorder=2)
        axA.annotate(rf"$\delta^*_{{{s}}}$", (u["dstar"], YA[1]), xytext=(2, -2),
                     textcoords="offset points", ha="left", va="top", fontsize=7,
                     color=st["color"])
    else:
        axA.annotate(rf"$\delta^*_{{{s}}}$ = {fmt(u['dstar'])} $\rightarrow$", (dmax, YA[1]),
                     ha="right", va="top", fontsize=7, color=st["color"])
axA.set_xlim(-0.04 * dmax, dmax * 1.06)
axA.set_ylim(*YA)
axA.set_xlabel(r"Bound on the direct effect of nearc4, $\delta$ (log points)")
axA.set_ylabel("Coefficient on schooling (log points per year)")
axA.set_title(r"(a) Panel A: union of 95% sets, $\gamma_0 \in [0, \delta]$", loc="left")
handles = [Line2D([], [], color=SPEC_STYLE[s]["color"], marker=SPEC_STYLE[s]["marker"], ms=3,
                  mfc="white", lw=1.1, label=lab) for s, lab in SPECS]
handles += [Line2D([], [], color=INK, lw=1.1, label="Robust AR-based union"),
            Line2D([], [], color=INK, lw=0.8, ls=(0, (4, 2)), label="Wald-based union"),
            Line2D([], [], color=INK, lw=0.9, ls=(0, (1, 1.5)), label=r"Breakdown $\delta^*$ (AR)")]
fig.legend(handles=handles, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3,
           frameon=False, handlelength=2.2, columnspacing=1.4)
if n_clipped_a:
    axA.text(0.99, 0.01, r"$\blacktriangle$/$\blacktriangledown$: side unbounded",
             transform=axA.transAxes, ha="right", va="bottom", fontsize=6.5)

# (b) profile statistic
win = (b0 >= XL[0]) & (b0 <= XL[1])
YB = (0.0, float(np.clip(1.08 * P["m"][win].max(), 1.6 * CRIT_ROB, 3.0 * CRIT_ROB)))
mplot = np.minimum(P["m"][win], YB[1] * 1.02)
axB.plot(b0[win], mplot, color=BLUE, lw=1.0, zorder=3)
axB.axhline(CRIT_ROB, color=INK, ls=(0, (4, 2)), lw=0.8, zorder=2)
axB.text(float(b0[win][np.argmin(P["m"][win])]), CRIT_ROB, r"$\chi^2_3$ 95% critical value",
         ha="center", va="bottom", fontsize=7)        # above the curve's minimum, clear of it
axB.axvline(0, color=MUTED, lw=0.6, zorder=1)
axB.set_ylim(*YB)
axB.set_ylabel(r"$m(b_0)$")
axB.set_title(r"(b) Panel B col. 6: profile robust AR statistic", loc="left")
plt.setp(axB.get_xticklabels(), visible=False)

# set strip
n_rows = len(SETS)
axS.axvline(0, color=MUTED, lw=0.6, zorder=1)
drawn = {}
for r, (key, label) in enumerate(SETS):
    y = n_rows - 1 - r
    col = BLUE if key == "rob" else INK
    lw = 3.2 if key == "rob" else 2.0
    drawn[key] = 0
    outside = []
    for k in range(len(SETINFO[key]["pieces"])):
        lo, hi = piece_ends(key, k)
        if hi < XL[0] or lo > XL[1]:
            outside.append((lo, hi))
            continue
        a, b = max(lo, XL[0]), min(hi, XL[1])
        if a == b:                                   # a single accepted point
            axS.plot([a], [y], marker="|", color=col, ms=6, mew=1.2)
        else:
            axS.plot([a, b], [y, y], color=col, lw=lw, solid_capstyle="butt", zorder=3)
        drawn[key] += 1
        for end, edge, sgn in ((lo, XL[0], -1), (hi, XL[1], 1)):
            if (sgn < 0 and end < edge) or (sgn > 0 and end > edge):
                axS.plot([edge], [y], marker="<" if sgn < 0 else ">", color=col, ms=4, zorder=4)
                axS.annotate(fmt(end), (edge, y), xytext=(-sgn * 6, -2.5), textcoords="offset points",
                             ha="right" if sgn > 0 else "left", va="top", fontsize=6.5, color=col)
    if outside:
        txt = "also " + ", ".join(f"[{fmt(a)}, {fmt(b)}]" for a, b in outside)
        right = all(a > XL[1] for a, _ in outside)
        axS.text(XL[1] if right else XL[0], y + 0.14 if right else y - 0.14, txt, fontsize=6,
                 color=col, ha="right" if right else "left", va="bottom" if right else "top")
    axS.text(XL[0] + 0.01 * (XL[1] - XL[0]), y + 0.14, label, fontsize=6.5, ha="left",
             va="bottom", color=col)
axS.set_yticks([])
axS.set_ylim(-0.35, n_rows - 0.15)
axS.spines["left"].set_visible(False)
axS.set_ylabel("95% sets", labelpad=4)
axS.set_xlim(*XL)
axS.set_xlabel(r"Hypothesised return to schooling, $b_0$")

Path(args.out).parent.mkdir(parents=True, exist_ok=True)
fig.savefig(args.out, format="pdf", bbox_inches="tight", pad_inches=0.02,
            metadata={"CreationDate": None, "ModDate": None})

out = {"n_grid_rows": len(grid_rows), "n_profile_rows": len(prof_rows),
       "n_profile_fine": int(fine.sum()), "window_lo": XL[0], "window_hi": XL[1],
       "n_inf_clipped_panel_a": n_clipped_a, "crit_rob": CRIT_ROB, "crit_gkmc": CRIT_GKMC}
for s, _ in SPECS:
    out[f"n_delta_{s.lower()}"] = int(len(union[s]["delta"]))
    out[f"dstar_{s.lower()}"] = union[s]["dstar"]
for key, _ in SETS:
    out[f"pieces_{key}"] = len(SETINFO[key]["pieces"])
    out[f"pieces_drawn_{key}"] = drawn[key]
Path(args.metrics).parent.mkdir(parents=True, exist_ok=True)
Path(args.metrics).write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {args.out}; window [{XL[0]:.4g}, {XL[1]:.4g}]; pieces "
      + ", ".join(f"{k}={len(SETINFO[k]['pieces'])}" for k, _ in SETS))
