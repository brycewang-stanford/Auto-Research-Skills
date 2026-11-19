"""Parse the Card-Krueger public data (public.dat) into a store-level CSV.

Reads data/raw/njmin/public.dat (written by code/fetch_data.py) by the column positions in
the bundled `codebook`, and checks that this gives the same values as the whitespace
(list) input used by the authors' own program check.sas. It keeps every row and every
codebook variable, under the codebook's names, and adds:

- ROW_ID       1..410, the line number in public.dat. SHEET is documented as a "unique
               store id" but is not unique (two different stores have SHEET 407), so
               ROW_ID is the key.
- FTE, FTE2    full-time-equivalent employment in waves 1 and 2, as defined in Card and
               Krueger (1994, p. 775) and computed in check.sas (EMPTOT, EMPTOT2):
               EMPFT + NMGRS + 0.5 * EMPPT (full-time incl. managers and assistant
               managers, plus half the part-timers). Missing if any part is missing.
- CLOSED_PERM  1 if STATUS2 == 3 (closed "permanently"); check.sas calls this CLOSED.
- CLOSED_TEMP  1 if STATUS2 in {2, 4, 5} (renovation, highway construction, mall fire):
               the paper's "four temporarily closed stores".
- REFUSED2     1 if STATUS2 == 0 (refused the second interview).

The closure coding of FTE2 is the one in the file, not imposed here: permanently closed
stores carry 0 in EMPFT2, EMPPT2 and NMGRS2 (so FTE2 = 0, as in CK Table 3), and the
temporarily closed and refusing stores have FTE2 missing. The script asserts both.

Checks against Card and Krueger (1994) Table 1 (via sources/notes.md) and the codebook:
410 stores, 331 NJ and 79 PA; wave 2 interviewed 399 (321 NJ, 78 PA); 6 closed
permanently (5 NJ, 1 PA); 2 under renovation and 2 temporarily closed (all NJ); 1 refusal
(NJ). A failed check makes the run exit non-zero.

Nothing here relates the state (treatment) to employment (outcome): the metrics are
counts of rows and of missing values, plus the published counts they are checked against.

Outputs
- data/derived/stores.csv        410 rows: ROW_ID, the 46 codebook variables, FTE, FTE2,
                                 CLOSED_PERM, CLOSED_TEMP, REFUSED2
- data/prepare_metrics.json      flat counts and check results

Run from the workspace root:
    .venv/bin/python -I code/prepare_data.py
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAW = Path("data/raw/njmin/public.dat")
OUT = Path("data/derived/stores.csv")
METRICS = Path("data/prepare_metrics.json")

# (name, start column, end column), 1-based and inclusive, copied from `codebook`.
CODEBOOK = [
    ("SHEET", 1, 3), ("CHAIN", 5, 5), ("CO_OWNED", 7, 7), ("STATE", 9, 9),
    ("SOUTHJ", 11, 11), ("CENTRALJ", 13, 13), ("NORTHJ", 15, 15), ("PA1", 17, 17),
    ("PA2", 19, 19), ("SHORE", 21, 21),
    ("NCALLS", 23, 24), ("EMPFT", 26, 30), ("EMPPT", 32, 36), ("NMGRS", 38, 42),
    ("WAGE_ST", 44, 48), ("INCTIME", 50, 54), ("FIRSTINC", 56, 60), ("BONUS", 62, 62),
    ("PCTAFF", 64, 68), ("MEALS", 70, 70), ("OPEN", 72, 76), ("HRSOPEN", 78, 82),
    ("PSODA", 84, 88), ("PFRY", 90, 94), ("PENTREE", 96, 100), ("NREGS", 102, 103),
    ("NREGS11", 105, 106),
    ("TYPE2", 108, 108), ("STATUS2", 110, 110), ("DATE2", 112, 117), ("NCALLS2", 119, 120),
    ("EMPFT2", 122, 126), ("EMPPT2", 128, 132), ("NMGRS2", 134, 138), ("WAGE_ST2", 140, 144),
    ("INCTIME2", 146, 150), ("FIRSTIN2", 152, 156), ("SPECIAL2", 158, 158),
    ("MEALS2", 160, 160), ("OPEN2R", 162, 166), ("HRSOPEN2", 168, 172),
    ("PSODA2", 174, 178), ("PFRY2", 180, 184), ("PENTREE2", 186, 190),
    ("NREGS2", 192, 193), ("NREGS112", 195, 196),
]
NAMES = [name for name, _, _ in CODEBOOK]
INTEGER_VARS = ["SHEET", "CHAIN", "CO_OWNED", "STATE", "SOUTHJ", "CENTRALJ", "NORTHJ", "PA1",
                "PA2", "SHORE", "NCALLS", "BONUS", "MEALS", "NREGS", "NREGS11", "TYPE2",
                "STATUS2", "DATE2", "NCALLS2", "SPECIAL2", "MEALS2", "NREGS2", "NREGS112"]

# Card and Krueger (1994) Table 1, as recorded in sources/notes.md section 1; the STATUS2
# totals are also printed in the codebook.
EXPECTED = {
    "rows": 410, "nj": 331, "pa": 79,
    "wave2_interviewed": 399, "wave2_interviewed_nj": 321, "wave2_interviewed_pa": 78,
    "closed_perm": 6, "closed_perm_nj": 5, "closed_perm_pa": 1,
    "renovation": 2, "renovation_nj": 2,
    "closed_temp_other": 2, "closed_temp_other_nj": 2,  # highway construction + mall fire
    "closed_temp": 4, "closed_temp_nj": 4,
    "refused": 1, "refused_nj": 1,
}


def parse_token(text: str) -> float:
    text = text.strip()
    return np.nan if text in ("", ".") else float(text)


def main() -> int:
    lines = RAW.read_text(encoding="ascii").splitlines()
    m: dict = {"rows_raw": len(lines)}

    # 1. fixed-width read by the codebook, and list read as in check.sas
    fixed = [[line[a - 1:b] for _, a, b in CODEBOOK] for line in lines]
    listed = [line.split() for line in lines]
    m["rows_with_46_tokens"] = sum(len(t) == len(NAMES) for t in listed)
    m["rows_fixed_vs_list_mismatch"] = sum(
        [c.strip() for c in f] != t for f, t in zip(fixed, listed))
    m["max_line_length"] = max(len(line) for line in lines)
    m["nonblank_chars_beyond_col_196"] = sum(bool(line[196:].strip()) for line in lines)

    df = pd.DataFrame([[parse_token(c) for c in row] for row in fixed], columns=NAMES)
    for col in INTEGER_VARS:
        df[col] = df[col].astype("Int64")
    df.insert(0, "ROW_ID", np.arange(1, len(df) + 1))

    # 2. per-store FTE, wave 1 and wave 2 (sum is missing if any part is missing)
    df["FTE"] = df["EMPFT"] + df["NMGRS"] + 0.5 * df["EMPPT"]
    df["FTE2"] = df["EMPFT2"] + df["NMGRS2"] + 0.5 * df["EMPPT2"]
    df["CLOSED_PERM"] = (df["STATUS2"] == 3).astype("Int64")
    df["CLOSED_TEMP"] = df["STATUS2"].isin([2, 4, 5]).astype("Int64")
    df["REFUSED2"] = (df["STATUS2"] == 0).astype("Int64")

    # 3. counts
    nj, pa = df["STATE"] == 1, df["STATE"] == 0
    st = df["STATUS2"]
    obs = {
        "rows": len(df), "nj": int(nj.sum()), "pa": int(pa.sum()),
        "wave2_interviewed": int((st == 1).sum()),
        "wave2_interviewed_nj": int(((st == 1) & nj).sum()),
        "wave2_interviewed_pa": int(((st == 1) & pa).sum()),
        "closed_perm": int((st == 3).sum()),
        "closed_perm_nj": int(((st == 3) & nj).sum()),
        "closed_perm_pa": int(((st == 3) & pa).sum()),
        "renovation": int((st == 2).sum()), "renovation_nj": int(((st == 2) & nj).sum()),
        "closed_temp_other": int(st.isin([4, 5]).sum()),
        "closed_temp_other_nj": int((st.isin([4, 5]) & nj).sum()),
        "closed_temp": int(st.isin([2, 4, 5]).sum()),
        "closed_temp_nj": int((st.isin([2, 4, 5]) & nj).sum()),
        "refused": int((st == 0).sum()), "refused_nj": int(((st == 0) & nj).sum()),
    }
    for code in range(6):
        m[f"status2_eq_{code}"] = int((st == code).sum())
    m["status2_missing"] = int(st.isna().sum())
    m["state_missing"] = int(df["STATE"].isna().sum())
    failures = []
    for key, want in EXPECTED.items():
        m[f"obs_{key}"] = obs[key]
        m[f"exp_{key}"] = want
        if obs[key] != want:
            failures.append(f"{key}: observed {obs[key]}, expected {want}")

    # closure coding of wave-2 employment, as it is in the file
    perm = st == 3
    temp_or_refused = st.isin([0, 2, 4, 5])
    m["closed_perm_fte2_all_zero"] = bool((df.loc[perm, "FTE2"] == 0).all())
    m["closed_perm_components2_all_zero"] = bool(
        (df.loc[perm, ["EMPFT2", "EMPPT2", "NMGRS2"]] == 0).all().all())
    m["temp_closed_or_refused_fte2_all_missing"] = bool(df.loc[temp_or_refused, "FTE2"].isna().all())
    m["temp_closed_or_refused_with_some_component2"] = int(
        df.loc[temp_or_refused, ["EMPFT2", "EMPPT2", "NMGRS2"]].notna().any(axis=1).sum())
    if not (m["closed_perm_fte2_all_zero"] and m["temp_closed_or_refused_fte2_all_missing"]):
        failures.append("closure coding of FTE2 is not 0 for permanent / missing for temporary")

    # missing-value counts: employment components and FTE by wave (pooled and by state;
    # these are sample-availability counts, not employment statistics)
    for col in ["EMPFT", "EMPPT", "NMGRS", "WAGE_ST", "EMPFT2", "EMPPT2", "NMGRS2", "WAGE_ST2"]:
        m[f"missing_{col}"] = int(df[col].isna().sum())
    for wave, col in (("w1", "FTE"), ("w2", "FTE2")):
        avail = df[col].notna()
        m[f"fte_{wave}_nonmissing"] = int(avail.sum())
        m[f"fte_{wave}_nonmissing_nj"] = int((avail & nj).sum())
        m[f"fte_{wave}_nonmissing_pa"] = int((avail & pa).sum())
    both = df["FTE"].notna() & df["FTE2"].notna()
    m["fte_both_waves_nonmissing"] = int(both.sum())
    m["fte_both_waves_nonmissing_nj"] = int((both & nj).sum())
    m["fte_both_waves_nonmissing_pa"] = int((both & pa).sum())
    m["fte_w1_missing_interviewed_w2"] = int((df["FTE"].isna() & (st == 1)).sum())
    m["fte_w2_missing_interviewed_w2"] = int((df["FTE2"].isna() & (st == 1)).sum())
    # secondary references (not CK numbers): Mamula 2021 non-missing FTE PA 77/77, NJ 321/319;
    # Ropponen 2010 fn 8 balanced sample 309 NJ + 75 PA
    m["ref_mamula_fte_w1_nj"], m["ref_mamula_fte_w1_pa"] = 321, 77
    m["ref_mamula_fte_w2_nj"], m["ref_mamula_fte_w2_pa"] = 319, 77
    m["ref_ropponen_balanced_nj"], m["ref_ropponen_balanced_pa"] = 309, 75

    # check.sas's Table 4 subset, as a count only: DEMP non-missing and
    # (CLOSED=1 or (CLOSED=0 and DWAGE non-missing)); CK Table 4 reports 357 stores
    t4 = both & (perm | (~perm & df["WAGE_ST"].notna() & df["WAGE_ST2"].notna()))
    m["checksas_table4_subset_n"] = int(t4.sum())
    m["exp_table4_n"] = 357

    # NJ stores by wave-1 starting wage group (CK Table 3 cols iv-vi report N = 101, 140, 73)
    w = df["WAGE_ST"]
    groups = {"425": w == 4.25, "426_499": (w > 4.25) & (w < 5.00), "500plus": w >= 5.00}
    for g, mask in groups.items():
        m[f"nj_wage_{g}_n"] = int((mask & nj).sum())
        m[f"nj_wage_{g}_n_fte_w1"] = int((mask & nj & df["FTE"].notna()).sum())
    m["nj_wage_missing_n"] = int((nj & w.isna()).sum())
    m["exp_nj_wage_425_n"], m["exp_nj_wage_426_499_n"], m["exp_nj_wage_500plus_n"] = 101, 140, 73

    # identifiers and value domains
    m["sheet_unique_values"] = int(df["SHEET"].nunique())
    m["sheet_duplicated_rows"] = int(df["SHEET"].duplicated(keep=False).sum())
    m["chain_outside_1_4"] = int((~df["CHAIN"].isin([1, 2, 3, 4])).sum())
    region = df[["SOUTHJ", "CENTRALJ", "NORTHJ", "PA1", "PA2"]].sum(axis=1)
    m["region_dummies_not_summing_to_1"] = int((region != 1).sum())
    m["nj_region_inconsistent"] = int(
        (nj & (df[["SOUTHJ", "CENTRALJ", "NORTHJ"]].sum(axis=1) != 1)).sum()
        + (pa & (df[["PA1", "PA2"]].sum(axis=1) != 1)).sum())
    m["negative_employment_values"] = int(
        (df[["EMPFT", "EMPPT", "NMGRS", "EMPFT2", "EMPPT2", "NMGRS2"]] < 0).sum().sum())
    m["columns_out"] = df.shape[1]
    m["rows_out"] = len(df)
    m["rows_dropped"] = 0

    for check, ok in (("rows_with_46_tokens", m["rows_with_46_tokens"] == len(lines)),
                      ("fixed_vs_list", m["rows_fixed_vs_list_mismatch"] == 0),
                      ("region", m["region_dummies_not_summing_to_1"] == 0),
                      ("chain", m["chain_outside_1_4"] == 0),
                      ("negative", m["negative_employment_values"] == 0)):
        if not ok:
            failures.append(check)
    m["n_check_failures"] = len(failures)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False)
    METRICS.parent.mkdir(parents=True, exist_ok=True)
    METRICS.write_text(json.dumps(m, indent=2) + "\n")
    print(f"wrote {OUT}: {len(df)} rows, {df.shape[1]} columns")
    for f in failures:
        print(f"CHECK FAILED: {f}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
