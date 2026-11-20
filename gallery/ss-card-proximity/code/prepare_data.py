"""Build the analysis file for the Card (1993/1995) college-proximity replication.

Reads data/raw/proximity/nls.dat (3,613 rows) at the column positions printed in
code_bk.txt, checks the parse against a whitespace (SAS list-input) reading and against
every N, mean, standard deviation, minimum and maximum printed in code_bk.txt, constructs
the variables of Card's example program read1.sas, applies the sample rule and writes
the analysis file.

Sample rule (plan.json, task dr-prepare; sources/notes.md sec. 1): rows with a non-missing
lwage76 (Card's N = 3,010). The file's lwage76 is already trimmed by Card; it is not
re-trimmed here. Unweighted: the weight variable is carried along but not applied.

Constructed variables (read1.sas):
    exp76  = age76 - ed76 - 6          potential experience, years
    exp762 = exp76 * exp76             its square (Card's Table 2 prints exp762/100)
    f1..f8 = 1{famed = k}, k = 1..8    parental-education classes (famed = 9 omitted)
Added for the experience-endogenous (Panel B) specification, whose instruments for
experience and its square are age and age squared (Card, Table 3 note b):
    age762 = age76 * age76

Descriptive checks against Card's Table 1 (WP 4483, PDF p. 33), Table 2 note and Table 3
note are univariate means only. By design this script computes nothing that relates the
instrument (nearc4) to education or wages: no cross-tabulation, correlation or
regression.

Outputs
- data/derived/card_analysis.csv    one row per man in the sample; all 52 raw variables
                                    (codebook names, raw tokens; '.' -> empty) plus the
                                    constructed ones
- data/prepare_metrics.json         row counts, parse checks, comparison statistics

Run from the workspace root:  python3 code/prepare_data.py   (standard library only)
"""

import csv
import json
import math
import re
import sys
from pathlib import Path

RAW = Path("data/raw/proximity/nls.dat")
CODEBOOK = Path("data/raw/proximity/code_bk.txt")
OUT = Path("data/derived/card_analysis.csv")
METRICS = Path("data/prepare_metrics.json")

# (name, first column, last column), 1-based inclusive, from code_bk.txt.
LAYOUT = [
    ("id", 1, 5), ("nearc2", 7, 7), ("nearc4", 10, 10), ("nearc4a", 12, 13),
    ("nearc4b", 15, 16), ("ed76", 18, 19), ("ed66", 21, 22), ("age76", 24, 25),
    ("daded", 27, 31), ("nodaded", 33, 33), ("momed", 35, 39), ("nomomed", 41, 41),
    ("weight", 43, 54), ("momdad14", 56, 56), ("sinmom14", 58, 58), ("step14", 60, 60),
    ("reg661", 62, 62), ("reg662", 64, 64), ("reg663", 66, 66), ("reg664", 68, 68),
    ("reg665", 70, 70), ("reg666", 72, 72), ("reg667", 74, 74), ("reg668", 76, 76),
    ("reg669", 78, 78), ("south66", 80, 80), ("work76", 82, 82), ("work78", 84, 84),
    ("lwage76", 86, 97), ("lwage78", 99, 110), ("famed", 112, 112), ("black", 114, 114),
    ("smsa76r", 116, 116), ("smsa78r", 118, 118), ("reg76r", 120, 120),
    ("reg78r", 122, 122), ("reg80r", 124, 124), ("smsa66r", 126, 126),
    ("wage76", 128, 132), ("wage78", 134, 138), ("wage80", 140, 144),
    ("noint78", 146, 146), ("noint80", 148, 148), ("enroll76", 150, 150),
    ("enroll78", 152, 152), ("enroll80", 154, 154), ("kww", 156, 157), ("iq", 159, 161),
    ("marsta76", 163, 163), ("marsta78", 165, 165), ("marsta80", 167, 167),
    ("libcrd14", 169, 169),
]
NAMES = [n for n, _, _ in LAYOUT]
CONSTRUCTED = ["exp76", "exp762", "age762"] + [f"f{k}" for k in range(1, 9)]

# Card (1993, NBER WP 4483), Table 1 (PDF p. 33), columns 2 (interviewed in 1976, valid
# education, N = 3613) and 3 (valid wage and education, N = 3010). Percentages, except
# parental education, KWW and education (means). Read from the page image.
CARD_T1 = {
    "age66_14_15_pct": (25.3, 25.5), "age66_16_17_pct": (23.8, 24.1),
    "age66_18_20_pct": (24.1, 24.6), "age66_21_24_pct": (26.7, 25.8),
    "region66_northeast_pct": (20.0, 20.7), "region66_midwest_pct": (26.3, 26.0),
    "region66_south_pct": (41.3, 41.4), "region66_west_pct": (12.5, 11.9),
    "smsa66_pct": (64.3, 65.0), "nearc4_pct": (67.8, 68.2),
    "momdad14_pct": (79.2, 78.9), "sinmom14_pct": (10.0, 10.1),
    "momed_valid_mean": (10.4, 10.3), "daded_valid_mean": (10.0, 10.0),
    "black_pct": (23.0, 23.0), "kww_mean": (33.5, 33.5), "ed76_mean": (13.2, 13.3),
    "south76_pct": (40.0, 40.3),
}
# Table 2 note and Table 3 note (N = 3010): mean (s.d.) of log wage and of education.
CARD_NOTES = {"lwage76_mean": 6.262, "lwage76_sd": 0.444, "ed76_mean": 13.263,
              "ed76_sd": 2.677}


def num(tok):
    return None if tok == "." else float(tok)


def parse_fixed(line):
    return {n: line[a - 1:b].strip() for n, a, b in LAYOUT}


def parse_codebook_stats():
    stats = {}
    pat = re.compile(r"^\s+([A-Z0-9]+)\s+(\d+)\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)\s*$")
    for line in CODEBOOK.read_text().splitlines():
        m = pat.match(line)
        if m and m.group(1).lower() in NAMES:
            stats[m.group(1).lower()] = (int(m.group(2)),) + m.group(3, 4, 5, 6)
    return stats


def describe(vals):
    v = [x for x in vals if x is not None]
    n = len(v)
    mean = sum(v) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in v) / (n - 1))
    return n, mean, sd, min(v), max(v)


def main() -> int:
    lines = RAW.read_text().splitlines()
    m = {"rows_in_file": len(lines)}

    # Parse: fixed columns, then cross-check with whitespace tokens (read1.sas list input).
    rows, mismatches = [], 0
    for line in lines:
        fixed = parse_fixed(line)
        toks = line.split()
        if len(toks) != len(NAMES):
            print(f"line has {len(toks)} tokens: {line[:40]!r}", file=sys.stderr)
            return 1
        if any(num(fixed[n]) != num(t) for n, t in zip(NAMES, toks)):
            mismatches += 1
        rows.append(fixed)
    m["fixed_vs_list_parse_mismatched_rows"] = mismatches
    ids = [r["id"] for r in rows]
    m["id_unique"] = int(len(set(ids)) == len(ids))

    # Check against every statistic printed in code_bk.txt (3613 rows; SAS proc means, n-1).
    # A statistic matches if it rounds to the printed value at the printed precision
    # (|ours - printed| <= half a unit in the last printed decimal place).
    cb = parse_codebook_stats()
    m["codebook_vars_listed"] = len(cb)
    worst, failed = 0.0, []
    for name, (n_cb, *printed) in cb.items():
        n, *ours = describe([num(r[name]) for r in rows])
        ok = n == n_cb
        for got, tok in zip(ours, printed):
            dec = len(tok.split(".")[1]) if "." in tok else 0
            ratio = abs(got - float(tok)) / (0.5 * 10 ** -dec)
            worst = max(worst, ratio)
            ok = ok and ratio <= 1.0 + 1e-9
        if not ok:
            failed.append(name)
    m["codebook_vars_matching"] = len(cb) - len(failed)
    m["codebook_stats_checked"] = 5 * len(cb)
    m["codebook_max_diff_in_half_units"] = round(worst, 6)
    if failed:
        print("codebook mismatch: " + ", ".join(failed), file=sys.stderr)

    # Construct variables (read1.sas) on all rows.
    for r in rows:
        age, ed, famed = num(r["age76"]), num(r["ed76"]), num(r["famed"])
        exp = age - ed - 6
        r["exp76"], r["exp762"], r["age762"] = exp, exp * exp, age * age
        for k in range(1, 9):
            r[f"f{k}"] = int(famed == k)

    # Sample rule: non-missing lwage76.
    sample = [r for r in rows if r["lwage76"] != "."]
    dropped = [r for r in rows if r["lwage76"] == "."]
    m["rows_kept"] = len(sample)
    m["rows_dropped_missing_lwage76"] = len(dropped)
    m["dropped_with_wage76_present"] = sum(r["wage76"] != "." for r in dropped)
    m["dropped_wage76_present_below_100c"] = sum(
        r["wage76"] != "." and num(r["wage76"]) < 100 for r in dropped)
    m["dropped_wage76_present_above_3000c"] = sum(
        r["wage76"] != "." and num(r["wage76"]) > 3000 for r in dropped)
    m["kept_with_wage76_missing"] = sum(r["wage76"] == "." for r in sample)
    m["kept_lwage76_ne_log_wage76"] = sum(
        abs(num(r["lwage76"]) - math.log(num(r["wage76"]))) > 1e-6 for r in sample)
    m["wage76_nonmissing_all"] = sum(r["wage76"] != "." for r in rows)

    # Missing values among the variables of Card's specifications, in the sample.
    used = ["lwage76", "ed76", "nearc4", "age76", "black", "smsa76r", "reg76r", "smsa66r",
            "reg662", "reg663", "reg664", "reg665", "reg666", "reg667", "reg668", "reg669",
            "daded", "momed", "nodaded", "nomomed", "famed", "momdad14", "sinmom14"]
    m["sample_missing_in_spec_vars"] = sum(r[v] == "." for r in sample for v in used)
    m["sample_exp76_min"] = min(r["exp76"] for r in sample)
    m["sample_exp76_max"] = max(r["exp76"] for r in sample)
    m["sample_exp76_negative"] = sum(r["exp76"] < 0 for r in sample)
    m["sample_ed76_min"] = min(num(r["ed76"]) for r in sample)
    m["sample_ed76_max"] = max(num(r["ed76"]) for r in sample)
    m["sample_age76_min"] = min(num(r["age76"]) for r in sample)
    m["sample_age76_max"] = max(num(r["age76"]) for r in sample)
    m["sample_famed9"] = sum(num(r["famed"]) == 9 for r in sample)
    m["all_reg665_to_667_ne_south66"] = sum(
        sum(num(r[f"reg66{k}"]) for k in (5, 6, 7)) != num(r["south66"]) for r in rows)
    m["sample_reg_dummies_sum_not_1"] = sum(
        sum(num(r[f"reg66{k}"]) for k in range(1, 10)) != 1 for r in sample)

    # Univariate comparisons with Card's Table 1 (cols 2 and 3) and table notes.
    def pct(rs, f):
        return 100.0 * sum(f(r) for r in rs) / len(rs)

    def mean_of(rs, name, keep=lambda r: True):
        v = [num(r[name]) for r in rs if keep(r) and r[name] != "."]
        return sum(v) / len(v)

    regions = {"northeast": (1, 2), "midwest": (3, 4), "south": (5, 6, 7), "west": (8, 9)}
    for tag, rs, col in (("all3613", rows, 0), ("sample", sample, 1)):
        ours = {}
        age66 = [num(r["age76"]) - 10 for r in rs]
        for lab, lo, hi in (("14_15", 14, 15), ("16_17", 16, 17), ("18_20", 18, 20),
                            ("21_24", 21, 24)):
            ours[f"age66_{lab}_pct"] = 100.0 * sum(lo <= a <= hi for a in age66) / len(rs)
        for reg, divs in regions.items():
            ours[f"region66_{reg}_pct"] = pct(rs, lambda r, d=divs: any(num(r[f"reg66{k}"]) == 1 for k in d))
        ours["smsa66_pct"] = pct(rs, lambda r: num(r["smsa66r"]) == 1)
        ours["nearc4_pct"] = pct(rs, lambda r: num(r["nearc4"]) == 1)
        ours["momdad14_pct"] = pct(rs, lambda r: num(r["momdad14"]) == 1)
        ours["sinmom14_pct"] = pct(rs, lambda r: num(r["sinmom14"]) == 1)
        ours["momed_valid_mean"] = mean_of(rs, "momed", lambda r: r["nomomed"] == "0")
        ours["daded_valid_mean"] = mean_of(rs, "daded", lambda r: r["nodaded"] == "0")
        ours["black_pct"] = pct(rs, lambda r: num(r["black"]) == 1)
        ours["kww_mean"] = mean_of(rs, "kww")
        ours["ed76_mean"] = mean_of(rs, "ed76")
        ours["south76_pct"] = pct(rs, lambda r: num(r["reg76r"]) == 1)
        n_round_ok = 0
        for k, v in ours.items():
            pub = CARD_T1[k][col]
            m[f"t1_{tag}_{k}"] = round(v, 4)
            m[f"t1_{tag}_{k}_pub"] = pub
            n_round_ok += abs(v - pub) <= 0.05 + 1e-9
        m[f"t1_{tag}_rounds_to_published"] = n_round_ok
        m[f"t1_{tag}_items"] = len(ours)
        m[f"t1_{tag}_momed_all_mean"] = round(mean_of(rs, "momed"), 4)
        m[f"t1_{tag}_daded_all_mean"] = round(mean_of(rs, "daded"), 4)
        m[f"t1_{tag}_kww_n"] = sum(r["kww"] != "." for r in rs)

    n, mean, sd, _, _ = describe([num(r["lwage76"]) for r in sample])
    m["sample_lwage76_mean"], m["sample_lwage76_sd"] = round(mean, 4), round(sd, 4)
    n, mean, sd, _, _ = describe([num(r["ed76"]) for r in sample])
    m["sample_ed76_mean"], m["sample_ed76_sd"] = round(mean, 4), round(sd, 4)
    for k, v in CARD_NOTES.items():
        m[f"notes_{k}_pub"] = v
    m["notes_rounds_to_published"] = sum(
        abs(m[f"sample_{k}"] - v) <= 0.0005 + 1e-9 for k, v in CARD_NOTES.items())
    for name in ("exp76", "exp762", "age76"):
        n, mean, sd, _, _ = describe([float(r[name]) if not isinstance(r[name], str) else num(r[name]) for r in sample])
        m[f"sample_{name}_mean"], m[f"sample_{name}_sd"] = round(mean, 4), round(sd, 4)
    # Means of the controls in the sample (univariate), for the data section of the paper.
    for name in ("black", "smsa76r", "reg76r", "smsa66r", "momdad14", "sinmom14",
                 "nodaded", "nomomed", "daded", "momed") + tuple(f"reg66{k}" for k in range(1, 10)):
        m[f"sample_{name}_mean"] = round(mean_of(sample, name), 4)
    for k in range(1, 10):
        m[f"sample_famed{k}_share"] = round(sum(num(r["famed"]) == k for r in sample) / len(sample), 4)

    # Write the analysis file.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(NAMES + CONSTRUCTED)
        for r in sample:
            raw = ["" if r[n] == "." else r[n] for n in NAMES]
            con = [int(r[c]) for c in CONSTRUCTED]
            w.writerow(raw + con)
    m["derived_rows"] = len(sample)
    m["derived_columns"] = len(NAMES) + len(CONSTRUCTED)

    METRICS.write_text(json.dumps(m, indent=2) + "\n")
    print(f"wrote {OUT}: {len(sample)} rows; dropped {len(dropped)} with missing lwage76")
    return 0 if (not failed and mismatches == 0 and m["id_unique"]) else 1


if __name__ == "__main__":
    sys.exit(main())
