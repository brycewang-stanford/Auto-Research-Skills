"""Run pub-values: the published Table 3 (rows 1-5) and Table 4 column (i) values, parsed
from the Scout's verified transcription in sources/notes.md (section 1, read from the page
images of Card and Krueger 1994, p. 780). No number is typed here.

Every H1 target parsed here must equal the published value that the verdict run used
(runs/verdict/metrics.json, *_pub); the run fails otherwise. The other values (rows 1, 2
and 5; Table 4's SE of regression and the mean and SD of the dependent variable) are
report-only and judged nowhere.

Writes runs/pub-values/metrics.json: pub_r<row>_<pa|nj|did>[_se], pub_t4_*, and for each
value the number of decimals it is printed with (*_dp), so a table can print it as
published.

Usage, from the workspace root (through crew.py run):
    .venv/bin/python -I code/pub_values.py --metrics runs/pub-values/metrics.json
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from figlib import load_metrics, write_metrics  # noqa: E402

NOTES = "sources/notes.md"
NUM = r"(-?\d+(?:\.\d+)?)"
PAIR = re.compile(r"^\**\s*" + NUM + r"\s*\(" + NUM + r"\)\s*\**$")

ap = argparse.ArgumentParser()
ap.add_argument("--metrics", required=True)
args = ap.parse_args()

text = Path(NOTES).read_text(encoding="utf-8")


def section(start: str, stop: str) -> str:
    i = text.index(start)
    j = text.index(stop, i + len(start))
    return text[i:j]


def decimals(s: str) -> int:
    return len(s.split(".")[1]) if "." in s else 0


m: dict = {}


def put(key: str, s: str) -> None:
    m[key] = float(s) if "." in s else int(s)
    m[key + "_dp"] = decimals(s)


# Table 3: one markdown row per table row, columns PA (i), NJ (ii), NJ-PA (iii)
t3 = section("### Published headline: Table 3", "### Published regressions: Table 4")
rows = {}
for line in t3.splitlines():
    hit = re.match(r"^\|\s*([1-5])\.\s[^|]*\|(.*)\|\s*$", line)
    if hit:
        cells = [c.strip() for c in hit.group(2).split("|")]
        if len(cells) != 3:
            raise ValueError(f"Table 3 row {hit.group(1)}: expected 3 cells, got {cells}")
        rows[int(hit.group(1))] = cells
if sorted(rows) != [1, 2, 3, 4, 5]:
    raise ValueError(f"Table 3 rows found: {sorted(rows)}")
for r, cells in rows.items():
    for col, cell in zip(("pa", "nj", "did"), cells):
        pair = PAIR.match(cell)
        if not pair:
            raise ValueError(f"Table 3 row {r} {col}: cannot parse {cell!r}")
        put(f"pub_r{r}_{col}", pair.group(1))
        put(f"pub_r{r}_{col}_se", pair.group(2))

# Table 4, column (i): the first cell of the NJ-dummy and SE-of-regression rows,
# the sample size and the mean and SD of the dependent variable
t4 = section("### Published regressions: Table 4", "### The authors' own robustness checks")
hit = re.search(r"^\| NJ dummy \|([^|]*)\|", t4, re.M)
pair = PAIR.match(hit.group(1).strip()) if hit else None
if not pair:
    raise ValueError("Table 4: NJ dummy, column (i) not found")
put("pub_t4_b_nj", pair.group(1))
put("pub_t4_se_nj", pair.group(2))
hit = re.search(r"^\| SE of regression \|\s*" + NUM + r"\s*\|", t4, re.M)
if not hit:
    raise ValueError("Table 4: SE of regression, column (i) not found")
put("pub_t4_root_mse", hit.group(1))
hit = re.search(r"Sample: \*\*(\d+) stores\*\*", t4)
if not hit:
    raise ValueError("Table 4: sample size not found")
put("pub_t4_n", hit.group(1))
hit = re.search(r"Its mean is " + NUM + r" and its SD is " + NUM + r"\.", t4.replace("\n", " "))
if not hit:
    raise ValueError("Table 4: mean and SD of the dependent variable not found")
put("pub_t4_dep_mean", hit.group(1))
put("pub_t4_dep_sd", hit.group(2))

# Cross-check against the published values the verdict judged with
v = load_metrics("verdict")
check = {"h1a_did_pub": "pub_r3_did", "h1a_did_se_pub": "pub_r3_did_se",
         "h1a_pa_pub": "pub_r3_pa", "h1a_pa_se_pub": "pub_r3_pa_se",
         "h1a_nj_pub": "pub_r3_nj", "h1a_nj_se_pub": "pub_r3_nj_se",
         "h1b_did_pub": "pub_r4_did", "h1b_did_se_pub": "pub_r4_did_se",
         "h1b_pa_pub": "pub_r4_pa", "h1b_pa_se_pub": "pub_r4_pa_se",
         "h1b_nj_pub": "pub_r4_nj", "h1b_nj_se_pub": "pub_r4_nj_se",
         "h1c_b_nj_pub": "pub_t4_b_nj", "h1c_se_nj_pub": "pub_t4_se_nj",
         "h1c_n_pub": "pub_t4_n"}
for vk, pk in check.items():
    if v[vk] != m[pk]:
        raise AssertionError(f"{NOTES} gives {pk} = {m[pk]}, the verdict used {vk} = {v[vk]}")
m["n_checked_against_verdict"] = len(check)

write_metrics(args.metrics, m)
print(f"pub-values: {len([k for k in m if k.startswith('pub_') and not k.endswith('_dp')])} "
      f"published values; {len(check)} equal the verdict's")
