"""describe-sample: Card (WP 4483) Table 1 column 3 items for the 3,010-man sample (D7).

Deviation D7 (plan.json design): result claims must come from analysis runs, so this
descriptive analysis run recomputes, from the analysis file, the Table 1 column 3 items
that the data-prep run prepare-data already recorded, asserts that each equals the value
prepare-data wrote, and writes them under the same key names so the data section can cite
them as macros. It changes no estimate, decision or count.

Shares and means only, each of one variable at a time. Nothing here relates nearc4 to
schooling or wages: nearc4 enters only as its own share of the sample.

Definitions are those of code/prepare_data.py (Table 1 column 3, Card 1993 NBER WP 4483,
PDF p. 33):
- percentages: 100 x (number of men with the indicator = 1) / 3,010;
- age in 1966 = age76 - 10, grouped 14-15, 16-17, 18-20, 21-24;
- region in 1966: Northeast = reg661 or reg662, Midwest = reg663 or reg664,
  South = reg665-reg667, West = reg668 or reg669;
- South in 1976 = reg76r; SMSA in 1966 = smsa66r;
- mother's (father's) education: mean of momed (daded) over men with nomomed = 0
  (nodaded = 0), i.e. not mean-imputed;
- KWW: mean over men with a non-missing kww; education: mean of ed76.
A value matches Card if |value - published| <= 0.05 (one printed decimal).

Inputs:  data/derived/card_analysis.csv (hash checked against data/manifest.json),
         data/prepare_metrics.json (the prepare-data run's metrics).
Output:  runs/describe-sample/metrics.json (flat JSON).
Standard library only.
"""

import csv
import hashlib
import json
import sys
from pathlib import Path

DATA = Path("data/derived/card_analysis.csv")
MANIFEST = Path("data/manifest.json")
PREP = Path("data/prepare_metrics.json")
OUT = Path("runs/describe-sample/metrics.json")
TOL = 1e-9

# Card (1993, NBER WP 4483), Table 1 column 3 (valid wage and education, N = 3010).
PUBLISHED = {
    "age66_14_15_pct": 25.5, "age66_16_17_pct": 24.1, "age66_18_20_pct": 24.6,
    "age66_21_24_pct": 25.8, "region66_northeast_pct": 20.7, "region66_midwest_pct": 26.0,
    "region66_south_pct": 41.4, "region66_west_pct": 11.9, "smsa66_pct": 65.0,
    "nearc4_pct": 68.2, "momdad14_pct": 78.9, "sinmom14_pct": 10.1,
    "momed_valid_mean": 10.3, "daded_valid_mean": 10.0, "black_pct": 23.0,
    "kww_mean": 33.5, "ed76_mean": 13.3, "south76_pct": 40.3,
}
REGIONS = {"northeast": (1, 2), "midwest": (3, 4), "south": (5, 6, 7), "west": (8, 9)}


def check(cond, msg):
    if not cond:
        print(f"ASSERTION FAILED: {msg}", file=sys.stderr)
        sys.exit(1)


def main() -> int:
    digest = hashlib.sha256(DATA.read_bytes()).hexdigest()
    manifest = json.loads(MANIFEST.read_text())
    want = [d["sha256"] for d in manifest["datasets"] if d["path"] == str(DATA)]
    check(want == [digest], f"{DATA} sha256 {digest} does not match data/manifest.json")

    with DATA.open(newline="") as fh:
        rows = list(csv.DictReader(fh))
    n = len(rows)
    check(n == 3010, f"expected 3010 rows, found {n}")

    def flag(name):
        return [r[name] == "1" for r in rows]

    def pct(bools):
        return 100.0 * sum(bools) / n

    def mean(name, keep=lambda r: True):
        v = [float(r[name]) for r in rows if keep(r) and r[name] != ""]
        return sum(v) / len(v)

    ours = {}
    age66 = [float(r["age76"]) - 10 for r in rows]
    for lab, lo, hi in (("14_15", 14, 15), ("16_17", 16, 17), ("18_20", 18, 20),
                        ("21_24", 21, 24)):
        ours[f"age66_{lab}_pct"] = pct(lo <= a <= hi for a in age66)
    for reg, divs in REGIONS.items():
        ours[f"region66_{reg}_pct"] = pct(any(r[f"reg66{k}"] == "1" for k in divs) for r in rows)
    ours["smsa66_pct"] = pct(flag("smsa66r"))
    ours["nearc4_pct"] = pct(flag("nearc4"))
    ours["momdad14_pct"] = pct(flag("momdad14"))
    ours["sinmom14_pct"] = pct(flag("sinmom14"))
    ours["momed_valid_mean"] = mean("momed", lambda r: r["nomomed"] == "0")
    ours["daded_valid_mean"] = mean("daded", lambda r: r["nodaded"] == "0")
    ours["black_pct"] = pct(flag("black"))
    ours["kww_mean"] = mean("kww")
    ours["ed76_mean"] = mean("ed76")
    ours["south76_pct"] = pct(flag("reg76r"))
    check(set(ours) == set(PUBLISHED), "item list differs from the published list")

    prep = json.loads(PREP.read_text())
    m = {"n_sample": n}
    rounds_ok, misses = 0, []
    for k, v in ours.items():
        key = f"t1_sample_{k}"
        value = round(v, 4)  # prepare-data recorded four decimals
        check(abs(value - prep[key]) <= TOL, f"{key}: {value} != prepare-data {prep[key]}")
        check(abs(PUBLISHED[k] - prep[f"{key}_pub"]) <= TOL, f"{key}_pub differs from prepare-data")
        m[key] = value
        m[f"{key}_pub"] = PUBLISHED[k]
        ok = abs(v - PUBLISHED[k]) <= 0.05 + 1e-9
        m[f"{key}_rounds_to_published"] = int(ok)
        rounds_ok += ok
        if not ok:
            misses.append(k)
    m["t1_sample_rounds_to_published"] = rounds_ok
    m["t1_sample_items"] = len(ours)
    m["t1_sample_misses"] = len(misses)
    check(rounds_ok == prep["t1_sample_rounds_to_published"], "rounds-to-published count differs")
    check(len(ours) == prep["t1_sample_items"], "item count differs")
    m["t1_sample_kww_n"] = sum(r["kww"] != "" for r in rows)
    check(m["t1_sample_kww_n"] == prep["t1_sample_kww_n"], "KWW count differs")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(m, indent=2) + "\n")
    print(f"wrote {OUT}: {len(ours)} items, {rounds_ok} round to Card's Table 1 col. 3; "
          f"misses: {', '.join(misses)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
