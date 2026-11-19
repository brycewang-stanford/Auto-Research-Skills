"""Verdict run (plan.json analysis_plan step 8): the only place a hypothesis is judged.

Reads the metrics of main-t3, main-t4 and h2-winsor and writes, for every H1 target, the
published value, the absolute difference and a 0/1 met flag, plus the H2 flags.

Decision rules (design.method DECISION RULES, fixed at the design gate):
- H1 target met iff round(|replicated (unrounded) - published|, 6) <= 0.05 (inclusive);
  N = 357 must match exactly.
- A part is reproduced (h1x_met) only if all its targets are met; point and SE targets
  are also flagged separately (h1x_point_met, h1x_se_met; H1(c)'s N target is h1c_n_met,
  a data check because N = 357 was already observed at data prep).
- H2 holds iff sign(did_w) = sign(did_u) and |did_w| >= 0.5 * |did_u|, on unrounded
  point estimates.

Published values: Card and Krueger (1994) Table 3 rows 3-4 and Table 4 column (i), as in
plan.json hypotheses H1 and sources/notes.md.

Usage, from the workspace root (through crew.py run; see runs/NOTES.md):
    .venv/bin/python -I code/verdict.py [--t3 runs/main-t3/metrics.json]
        [--t4 runs/main-t4/metrics.json] [--h2 runs/h2-winsor/metrics.json]
        [--out runs/verdict/metrics.json]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOLERANCE = 0.05
CONSISTENCY_TOL = 1e-9

# (target key, source run, metric, published value, kind)
TARGETS = {
    "h1a": [
        ("did", "t3", "did_r3", 2.76, "point"), ("did_se", "t3", "did_r3_se", 1.36, "se"),
        ("pa", "t3", "chg_r3_pa", -2.16, "point"), ("pa_se", "t3", "chg_r3_pa_se", 1.25, "se"),
        ("nj", "t3", "chg_r3_nj", 0.59, "point"), ("nj_se", "t3", "chg_r3_nj_se", 0.54, "se"),
    ],
    "h1b": [
        ("did", "t3", "did_r4", 2.75, "point"), ("did_se", "t3", "did_r4_se", 1.34, "se"),
        ("pa", "t3", "chg_r4_pa", -2.28, "point"), ("pa_se", "t3", "chg_r4_pa_se", 1.25, "se"),
        ("nj", "t3", "chg_r4_nj", 0.47, "point"), ("nj_se", "t3", "chg_r4_nj_se", 0.48, "se"),
    ],
    "h1c": [
        ("b_nj", "t4", "b_nj", 2.33, "point"), ("se_nj", "t4", "se_nj", 1.19, "se"),
    ],
}
H1C_N_PUBLISHED = 357


def sign(x: float) -> int:
    return (x > 0) - (x < 0)


def target_met(replicated: float, published: float) -> tuple[float, int]:
    diff = abs(float(replicated) - float(published))
    return diff, int(round(diff, 6) <= TOLERANCE)


def judge(t3: dict, t4: dict, h2: dict) -> dict:
    src = {"t3": t3, "t4": t4}
    m: dict = {}
    for part, targets in TARGETS.items():
        flags = {"point": [], "se": []}
        for key, run, metric, pub, kind in targets:
            rep = src[run][metric]
            diff, met = target_met(rep, pub)
            m[f"{part}_{key}_rep"] = float(rep)
            m[f"{part}_{key}_pub"] = pub
            m[f"{part}_{key}_absdiff"] = diff
            m[f"{part}_{key}_met"] = met
            flags[kind].append(met)
        if part == "h1c":
            n_met = int(int(t4["n"]) == H1C_N_PUBLISHED)
            m["h1c_n_rep"], m["h1c_n_pub"], m["h1c_n_met"] = int(t4["n"]), H1C_N_PUBLISHED, n_met
        m[f"{part}_point_met"] = int(all(flags["point"]))
        m[f"{part}_se_met"] = int(all(flags["se"]))
        m[f"{part}_met"] = int(m[f"{part}_point_met"] and m[f"{part}_se_met"]
                               and m.get(f"{part}_n_met", 1))

    # consistency: H2's unwinsorized comparator is the replicated row-4 estimate
    if abs(float(h2["did_u"]) - float(t3["did_r4"])) > CONSISTENCY_TOL:
        raise AssertionError("h2-winsor did_u differs from main-t3 did_r4")
    did_u, did_w = float(h2["did_u"]), float(h2["did_w"])
    m["h2_did_u"], m["h2_did_w"] = did_u, did_w
    m["h2_sign_same"] = int(sign(did_w) == sign(did_u))
    m["h2_half_kept"] = int(abs(did_w) >= 0.5 * abs(did_u))
    m["h2_holds"] = int(m["h2_sign_same"] and m["h2_half_kept"])
    return m


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--t3", default="runs/main-t3/metrics.json")
    p.add_argument("--t4", default="runs/main-t4/metrics.json")
    p.add_argument("--h2", default="runs/h2-winsor/metrics.json")
    p.add_argument("--out", default="runs/verdict/metrics.json")
    a = p.parse_args(argv)
    load = lambda path: json.loads(Path(path).read_text())  # noqa: E731
    m = judge(load(a.t3), load(a.t4), load(a.h2))
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(m, indent=2, allow_nan=False) + "\n")
    print(f"verdict: h1a_met={m['h1a_met']} h1b_met={m['h1b_met']} "
          f"h1c_met={m['h1c_met']} h2_holds={m['h2_holds']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
