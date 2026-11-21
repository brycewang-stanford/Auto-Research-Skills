"""Run select (analysis_plan 1; design.method CANDIDATE SET and SELECTION RULE).

Input   data/derived/state_panel_pre.csv only (2014Q1-2019Q4; the script refuses any later quarter)
Output  runs/select/pseudo_atts.csv   24 candidates x 6 pseudo-dates of California's pseudo-ATTs
        runs/select/metrics.json      rmse_<id>, maxabs_<id> for every candidate, selected,
                                      selected_rmse, tie_used, and the best DD/DDT/SC/SDID

At each pseudo-date B' in 2016Q1..2017Q2, California is treated with the candidate's pool as
donors and the windows F(B'), A(B'), P(B') of design.method NOTATION; the pseudo-ATT is the
pooled estimate over P(B') = B'+3..B'+10 (for P candidates read on the log-employment scale,
which is the same number: F16). RMSE_c = sqrt(mean over the six B' of tau_c(B')^2).
Primary = argmin RMSE_c; tie-break: RMSEs equal after rounding to 4 decimals, then smaller
max |tau_c(B')|, then the earlier candidate in the design's order. Run once.
"""
import sys
from pathlib import Path

_HERE = str(Path(__file__).resolve().parent)
# This file shares its name with the standard-library module 'select'. Load the standard module
# before code/ is on the import path, so that subprocess/selectors (imported by scipy) find it.
sys.path[:] = [p for p in sys.path if str(Path(p or ".").resolve()) != _HERE]
import select  # noqa: E402,F401  (standard library)
sys.path.insert(0, _HERE)

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import sclib as S  # noqa: E402

INPUT = Path("data/derived/state_panel_pre.csv")
OUT_DIR = Path("runs/select")
METRICS = OUT_DIR / "metrics.json"
PSEUDO_CSV = OUT_DIR / "pseudo_atts.csv"


def load_input(src=INPUT):
    """Read the truncated panel; raise if it holds any quarter after 2019Q4 (0f (v))."""
    df = S.read_panel_csv(src, pre_only=True)
    return S.Panel(df)


def pseudo_atts(panel):
    rows = []
    for cid in S.CANDIDATES:
        spec, pool = S.parse_candidate(cid)
        for B in S.PSEUDO_DATES:
            win = S.standard_windows(B, fit_start=spec.fit_start, years=False, anticip=False)
            taus, _ = S.estimate(panel, spec, win, S.CA, S.POOLS[pool])
            rows.append({"candidate": cid, "pseudo_date": S.qlabel(B), "tau": taus["pooled"]})
    return pd.DataFrame(rows)


def select_candidate(tab):
    """Apply the selection rule to the long table of pseudo-ATTs."""
    rmse, maxabs = {}, {}
    for cid in S.CANDIDATES:
        t = tab.loc[tab.candidate == cid, "tau"].to_numpy()
        if len(t) != len(S.PSEUDO_DATES):
            raise ValueError(f"{cid}: {len(t)} pseudo-ATTs")
        rmse[cid] = float(np.sqrt(np.mean(t ** 2)))
        maxabs[cid] = float(np.max(np.abs(t)))
    best = min(round(rmse[c], 4) for c in S.CANDIDATES)
    tied = [c for c in S.CANDIDATES if round(rmse[c], 4) == best]   # kept in the design's order
    if len(tied) == 1:
        return tied[0], 0, len(tied), rmse, maxabs
    m = min(maxabs[c] for c in tied)
    winner = [c for c in tied if maxabs[c] == m][0]                 # then the earlier candidate
    return winner, 1, len(tied), rmse, maxabs


def main():
    panel = load_input()
    tab = pseudo_atts(panel)
    selected, tie_used, n_tied, rmse, maxabs = select_candidate(tab)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tab.to_csv(PSEUDO_CSV, index=False, float_format="%.10g")
    m = {"input_last_quarter": S.qlabel(int(panel.qi[-1])), "n_candidates": len(S.CANDIDATES),
         "n_pseudo_dates": len(S.PSEUDO_DATES),
         "pseudo_dates": ",".join(S.qlabel(b) for b in S.PSEUDO_DATES)}
    for cid in S.CANDIDATES:
        m[f"rmse_{cid}"] = rmse[cid]
    for cid in S.CANDIDATES:
        m[f"maxabs_{cid}"] = maxabs[cid]
    m.update({"selected": selected, "selected_rmse": rmse[selected],
              "selected_maxabs": maxabs[selected], "tie_used": tie_used, "n_tied_at_4dp": n_tied})
    for est in ["DD", "DDT", "SC", "SDID"]:
        ids = [c for c in S.CANDIDATES if c.split("-")[0] == est]
        b = min(ids, key=lambda c: (rmse[c], S.CANDIDATES.index(c)))
        m[f"best_{est}_id"] = b
        m[f"best_{est}_rmse"] = rmse[b]
    m["solver_solves"] = S.SOLVER_LOG["solves"]
    m["solver_kkt_max"] = S.SOLVER_LOG["kkt_max"]
    m["solver_not_converged"] = S.SOLVER_LOG["not_converged"]
    S.write_json(METRICS, m)
    print(f"selected {selected} (RMSE {rmse[selected]:.4f}; tie_used {tie_used})")


if __name__ == "__main__":
    main()
