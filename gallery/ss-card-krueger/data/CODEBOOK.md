# Data codebook: ss-card-krueger

Prepared by the Data RA on 2026-11-19. Before the design gate: data preparation only. No
statistic relating state (treatment) to employment (outcome) has been computed.

## Source

| Item | Value |
|---|---|
| Archive | `https://davidcard.berkeley.edu/data_sets/njmin.zip`, 23,017 bytes, SHA-256 `41a29aec6b489658b20030d044a2b20a5f5a04b871cde41df057afd6013ba587` (server Last-Modified 27 Jul 2007) |
| Retrieved | 2026-11-19 by `code/fetch_data.py` (run `fetch-data`); the size and hash are pinned, so a rerun gets the same bytes or fails |
| Members | `public.dat` (410 obs, 46 variables), `codebook`, `check.sas` (the authors' SAS program), `read.me`, `survey1.nj`, `survey2.nj` (the text of the two questionnaires) |
| Terms | None stated (see `data/manifest.json`). Raw and derived files are git-ignored and rebuilt by the runs |
| Provenance note | `read.me` says the files "pertain to the New Jersey - Pennsylvania surveys used in *Myth and Measurement*, chapter 2". This is the authors' public release, which may differ from the file behind the 1994 AER tables (see `plan.json` H1) |
| Derived file | `data/derived/stores.csv`, 410 rows x 52 columns, made by `code/prepare_data.py` (run `prepare-data`). SHA-256 in `data/manifest.json` |

## Parsing

`public.dat` is read at the column positions printed in `codebook`. The authors' `check.sas`
instead reads it with SAS list input (whitespace-separated, `.` = missing). Both readings
were applied, and they give identical values on all 410 rows: every row has exactly 46
tokens, and no characters lie beyond column 196. Missing values (`.`) become empty cells in
the CSV. No rows are dropped and no values are recoded. Every count below comes from
`data/prepare_metrics.json`.

## Variables (codebook names; one row per store)

Units are as in `codebook`. Employment counts are numbers of persons and can be fractional
in the raw file (e.g. 14.50).

| Variable | Definition (from `codebook`) | Missing |
|---|---|---|
| `ROW_ID` | **Added.** Line number in `public.dat`, 1-410. Use this as the key (see SHEET) | 0 |
| `SHEET` | Sheet number, documented as "unique store id" | 0 (but 409 distinct values for 410 rows) |
| `CHAIN` | 1 = Burger King, 2 = KFC, 3 = Roy Rogers, 4 = Wendy's | 0 |
| `CO_OWNED` | 1 if company-owned | 0 |
| `STATE` | 1 = New Jersey, 0 = Pennsylvania | 0 |
| `SOUTHJ`, `CENTRALJ`, `NORTHJ` | 1 if in southern / central / northern NJ | 0 |
| `PA1`, `PA2` | 1 if in PA: northeast suburbs of Philadelphia / Easton etc. | 0 |
| `SHORE` | 1 if on the NJ shore | 0 |
| **Wave 1 (Feb-Mar 1992)** | | |
| `NCALLS` | Number of call-backs (0 = reached on first call) | see file |
| `EMPFT` | Full-time employees, **excluding** managers (survey1 Q1) | 6 |
| `EMPPT` | Part-time employees, **excluding** managers (survey1 Q1) | 4 |
| `NMGRS` | Managers and assistant managers (survey1 Q2) | 6 |
| `WAGE_ST` | Starting wage, $/hour | 20 |
| `INCTIME` | Months to usual first raise | |
| `FIRSTINC` | Usual amount of first raise, $/hour | |
| `BONUS` | 1 if cash bounty for new workers | |
| `PCTAFF` | % of employees affected by the new minimum | |
| `MEALS` | Free/reduced-price meals: 0 none, 1 free, 2 reduced, 3 both (`check.sas` calls it `MEAL`) | |
| `OPEN` | Hour of opening | |
| `HRSOPEN` | Hours open per day | |
| `PSODA`, `PFRY`, `PENTREE` | Prices of a medium soda, small fries and an entree, incl. tax, $ | |
| `NREGS`, `NREGS11` | Cash registers in the store / open at 11:00 am | |
| **Wave 2 (Nov-Dec 1992)** | | |
| `TYPE2` | Type of 2nd interview: 1 phone, 2 personal | |
| `STATUS2` | 0 refused, 1 answered, 2 closed for renovations, 3 closed "permanently", 4 closed for highway construction, 5 closed due to mall fire | 0 |
| `DATE2` | Date of 2nd interview, MMDDYY integer (e.g. 111792 = 17 Nov 1992) | 0 |
| `NCALLS2` | Number of call-backs | |
| `EMPFT2`, `EMPPT2`, `NMGRS2` | As in wave 1, at wave 2 | 12, 10, 6 |
| `WAGE_ST2` | Starting wage, $/hour | 21 |
| `INCTIME2`, `FIRSTIN2` | As in wave 1 | |
| `SPECIAL2` | 1 if special program for new workers | |
| `MEALS2`, `OPEN2R`, `HRSOPEN2`, `PSODA2`, `PFRY2`, `PENTREE2`, `NREGS2`, `NREGS112` | As in wave 1, at wave 2 | |
| **Constructed** | | |
| `FTE` | Wave-1 full-time-equivalent employment = `EMPFT + NMGRS + 0.5*EMPPT`. This is CK (1994, p. 775) "full-time workers [including managers] plus 0.5 times the number of part-time workers", and `EMPTOT` in `check.sas`. Missing if any part is missing | 12 |
| `FTE2` | The same at wave 2 (`EMPTOT2` in `check.sas`). Closure coding comes from the file and is not imposed here: the 6 permanently closed stores have EMPFT2 = EMPPT2 = NMGRS2 = 0, so FTE2 = 0. The 4 temporarily closed stores and the refusal have FTE2 missing. This matches CK Table 3 rows 1-4 | 14 |
| `CLOSED_PERM` | 1 if `STATUS2 == 3` (`CLOSED` in `check.sas`) | 0 |
| `CLOSED_TEMP` | 1 if `STATUS2` in {2, 4, 5}: the paper's "four temporarily closed stores" | 0 |
| `REFUSED2` | 1 if `STATUS2 == 0` | 0 |

The questionnaire wording (`survey1.nj` Q1-Q2) confirms that `EMPFT` and `EMPPT` exclude
managers and assistant managers, who are counted only in `NMGRS`. So `EMPFT + NMGRS` is the
paper's "full-time including managers". The 0.4 and 0.6 weights in Table 5 change only the
weight on `EMPPT`.

No per-store change in FTE, and no NJ-vs-PA level, change or regression, has been computed.

## Checks against the source

| Check | Source value | Observed | Match |
|---|---|---|---|
| Stores (rows) | 410 (CK Table 1; codebook; read.me) | 410 | yes |
| NJ / PA | 331 / 79 (CK Table 1) | 331 / 79 | yes |
| Wave-2 interviewed (`STATUS2 = 1`) | 399: 321 NJ, 78 PA (CK Table 1; codebook) | 399: 321 NJ, 78 PA | yes |
| Closed permanently (`STATUS2 = 3`) | 6: 5 NJ, 1 PA | 6: 5 NJ, 1 PA | yes |
| Under renovation (`STATUS2 = 2`) | 2, NJ | 2, NJ | yes |
| Temporarily closed (`STATUS2` 4 and 5) | 2, NJ | 2, NJ (1 highway construction, 1 mall fire) | yes |
| "Four temporarily closed" (2, 4, 5) | 4, NJ | 4, NJ | yes |
| Refused wave 2 (`STATUS2 = 0`) | 1, NJ | 1, NJ | yes |
| Permanently closed stores: wave-2 FTE | 0 (CK Table 3 notes) | 0 for all 6 (all three parts 0) | yes |
| Temporarily closed stores: wave-2 FTE | missing (CK Table 3 notes) | missing for all 4, and for the refusal | yes |
| NJ stores by wave-1 starting wage: 4.25 / 4.26-4.99 / >= 5.00 | N = 101 / 140 / 73 (CK Table 3 cols iv-vi) | 101 / 140 / 73 (17 NJ stores have no wave-1 wage) | yes |
| `check.sas` Table 4 subset (FTE both waves, and closed or wage both waves): count only | 357 (CK Table 4) | 357 | yes |
| Fixed-width vs list input | identical | 0 rows differ | yes |
| Region dummies | exactly one of the 5 per store, consistent with STATE | 0 violations | yes |

Store counts with non-missing FTE (sample availability, not employment statistics). CK give
no per-wave counts; the comparators are secondary sources:

| | Wave 1 | Wave 2 | Both waves (balanced) |
|---|---|---|---|
| NJ | 321 | 319 | 309 |
| PA | 77 | 77 | 75 |
| All | 398 | 396 | 384 |
| Secondary reference | Mamula (2021): NJ 321, PA 77 | Mamula: NJ 319, PA 77 | Ropponen (2010, fn 8): 309 NJ + 75 PA |

All three match.

Missing wave-1 FTE: 12 stores (2 PA, 10 NJ), all of them interviewed in wave 2. Each is
missing at least one of EMPFT, EMPPT, NMGRS. Missing wave-2 FTE: 14 stores, namely the 4
temporarily closed, the 1 refusal and 9 stores interviewed in wave 2 with an
item missing (2 PA, 7 NJ).

## Discrepancies and things to know

1. **SHEET is not unique.** The codebook calls it a "unique store id", but SHEET = 407
   appears twice (ROW_ID 42: PA, KFC; ROW_ID 168: NJ, Wendy's). These are different stores.
   Use `ROW_ID` as the key. Nothing in the analysis needs a cross-file merge, so this has no
   effect on the estimates. It does contradict the statement in `sources/notes.md` (from NW
   1995 fn 6) that the public file has "no store identifier": SHEET identifies stores within
   this file, apart from the duplicate.
2. **Names in `check.sas` differ from the codebook** for three variables: `CHAINr`, `STATEr`
   and `MEAL` (the codebook has CHAIN, STATE, MEALS). The CSV uses the codebook names. The
   values are the same, because `check.sas` reads positionally.
3. **Codebook vs paper wording of closures.** The codebook has two "temporarily closed"
   codes, 4 (highway construction) and 5 (mall fire), where CK Table 1 says "temporarily
   closed". CK's "four temporarily closed stores" are codes 2, 4 and 5.
4. **The renovation store SHEET 65 (ROW_ID 198, NJ) reports some wave-2 items:** NMGRS2 = 3
   and WAGE_ST2 = 5.05, but EMPFT2 and EMPPT2 are missing. So its FTE2 is missing, as CK
   treat it. A design that sets temporarily closed stores to 0 (CK Table 3 row 5, Table 5)
   must do so explicitly from `CLOSED_TEMP`.
5. **`check.sas` does not set the Table 3 samples itself.** It computes EMPTOT, EMPTOT2 and
   DEMP with missing-value propagation, and defines the Table 4 subset as `DEMP` non-missing
   and (`CLOSED = 1` or (`CLOSED = 0` and `DWAGE` non-missing)). Its `GAP` is 0 for PA, 0 for
   NJ with `WAGE_ST >= 5.05`, `(5.05 - WAGE_ST)/WAGE_ST` for NJ with a positive wage, and
   missing otherwise. These rules are for the Econometrician; they are not applied in
   `stores.csv`.
6. **No wave-1 interview date.** Only `DATE2` exists (consistent with NW 1995 fn 6).
7. `codebook` contains one non-ASCII separator line (IBM code-page box characters), and
   `read.me` misspells the SAS file's name as "chS ck.sas". Neither affects the data.
