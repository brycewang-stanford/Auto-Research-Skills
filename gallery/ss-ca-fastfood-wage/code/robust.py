"""Robustness runs (analysis_plan 9-13): python3 code/robust.py <variant>.

Inputs  data/derived/state_panel.csv, runs/select/metrics.json, runs/level-mde/metrics.json
Output  runs/<run id>/metrics.json

variant     run id               what changes (everything else as the selected candidate)
base2023q4  rob-base-2023q4      B = 2023Q4 (Dube's base): fit to 2023Q4, DDT trend 2022Q1-2023Q4,
                                 2024Q1 dropped, post 2024Q2-2026Q1
preab257    rob-pre-ab257        B = 2022Q2: fit 2014Q1-2019Q4 + 2022Q1-2022Q2, 2022Q3-2024Q1 out of
                                 base, fit and post; DDT trend over the last 9 non-COVID quarters
                                 (2018Q2-2019Q4, 2022Q1-2022Q2; design-r2 D10); post 2024Q2-2026Q1
pool        rob-pool             the other pool (D20 <-> R50); level-mde statistic 'op'
naics7225   rob-7225             outcome NAICS 7225 employment. Main: donors with a suppressed 7225
                                 row dropped and listed (t at nu over its own donors, capped at its
                                 own J). Second: all donors, 2024Q4 dropped from every unit's post
                                 window (7-quarter mean)
final7      rob-final-quarters   post 2024Q2-2025Q4 (no preliminary 2026Q1)

Critical values: level-mde statistic h2 (the selected candidate's H2 value: L quantile, and t at
the run's own nu = min(own J, nu_hat over its own donors)), except rob-pool ('op'). Each run
reports the label the H2 rule would give, marked 'not the headline'. SDID's zeta uses T_post =
the length of the run's post window (7 for final7 and the second 7225 number).
"""
import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
# code/select.py shadows the standard-library module 'select'; load the standard one first.
sys.path[:] = [p for p in sys.path if str(Path(p or ".").resolve()) != _HERE]
import select  # noqa: E402,F401  (standard library)
sys.path.insert(0, _HERE)

import numpy as np  # noqa: E402

import sclib as S  # noqa: E402

RUN_IDS = {"base2023q4": "rob-base-2023q4", "preab257": "rob-pre-ab257", "pool": "rob-pool",
           "naics7225": "rob-7225", "final7": "rob-final-quarters"}
POST = list(range(S.qidx(2024, 2), S.qidx(2026, 1) + 1))


def one(panel, m_lvl, spec, donors, win, stat, tag, m):
    r = S.placebo_inference(S.make_stat_fn(panel, spec, win, keys=["pooled"]), S.CA, donors,
                            S.pop_at_base(panel, win))["pooled"]
    c, nu_hat, nu = S.crit_for(m_lvl, stat, donors)
    m.update(S.flatten_inference(tag, r, c, nu))
    m[f"{tag}_nu_hat"] = nu_hat
    m[f"{tag}_nu"] = nu
    m[f"{tag}_pct"] = S.pct(r["tau"])
    sign, size, label = S.h2_label(S.intervals(r["tau"], r["se"], c))
    m.update({f"{tag}_sign": sign, f"{tag}_size": size, f"{tag}_label": label,
              f"{tag}_headline": "not the headline"})


def main(variant):
    if variant not in RUN_IDS:
        raise SystemExit(f"variant must be one of {sorted(RUN_IDS)}")
    panel, selected, spec, pool, m_lvl = S.load_run_context()
    donors = S.POOLS[pool]
    m = {"selected": selected, "variant": variant}
    if variant == "base2023q4":
        win = S.custom_windows(S.qidx(2023, 4), POST, fit_start=spec.fit_start, trend="b8")
        one(panel, m_lvl, spec, donors, win, "h2", "rob", m)
    elif variant == "preab257":
        win = S.custom_windows(S.qidx(2022, 2), POST, fit_start=spec.fit_start, trend="last9")
        m["trend_quarters"] = ",".join(S.qlabel(q) for q in win.trend)
        one(panel, m_lvl, spec, donors, win, "h2", "rob", m)
    elif variant == "pool":
        op = S.other_pool(pool)
        m["pool"] = op
        win = S.standard_windows(S.REAL_B, fit_start=spec.fit_start, years=False, anticip=False)
        one(panel, m_lvl, spec, S.POOLS[op], win, "op", "rob", m)
    elif variant == "final7":
        win = S.custom_windows(S.REAL_B, range(S.qidx(2024, 2), S.qidx(2025, 4) + 1),
                               fit_start=spec.fit_start)
        one(panel, m_lvl, spec, donors, win, "h2", "rob", m)
    elif variant == "naics7225":
        sp = spec.with_(industry="7225")
        sup = [u for u in panel.units if np.nansum(panel.sup7225[panel.row[u]]) > 0]
        if S.CA in sup:
            raise ValueError("California's 7225 series has a suppressed row")
        sup_q = sorted({S.qlabel(int(panel.qi[p])) for u in sup
                        for p in np.flatnonzero(panel.sup7225[panel.row[u]] > 0)})
        kept = [u for u in donors if u not in sup]
        m.update({"suppressed_states": ",".join(panel.abbr.get(u, u) for u in sup),
                  "suppressed_quarters": ",".join(sup_q),
                  "dropped_donors": ",".join(panel.abbr.get(u, u) for u in donors if u in sup),
                  "J_main": len(kept)})
        win = S.standard_windows(S.REAL_B, fit_start=spec.fit_start, years=False, anticip=False)
        one(panel, m_lvl, sp, kept, win, "h2", "rob", m)
        post7 = [q for q in POST if S.qlabel(q) not in sup_q]
        win2 = S.custom_windows(S.REAL_B, post7, fit_start=spec.fit_start)
        m["post_quarters_second"] = len(post7)
        one(panel, m_lvl, sp, donors, win2, "h2", "rob_alldonors", m)
    m.update(S.solver_metrics())
    S.write_json(Path("runs") / RUN_IDS[variant] / "metrics.json", m)
    print(f"{RUN_IDS[variant]}: {m['rob_att']:.4f} -> {m['rob_label']}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "")
