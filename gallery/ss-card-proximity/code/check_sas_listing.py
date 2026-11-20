"""Run check-sas-listing (plan.json analysis_plan step 13; design.data; task e-sas-code):
report-only comparison of Card's SAS listing read1.lst with our OLS runs.

read1.lst is the listing of Card's example program read1.sas, whose `proc reg s` fits four
models: ed76 on f1-f8, ed76 on parental education, and two log-wage models,
  lwage76 = ed76 exp76 exp762 black smsa76r reg76r smsa66r reg662-reg669   (16 parameters
            with the intercept; our Table 2 column 2, run h1-a5)
  the same + daded momed nodaded nomomed f1-f8 momdad14 sinmom14          (30 parameters;
            our Table 2 column 5, run h1-b6).
This script reads read1.lst from data/raw/proximity.zip in memory (it is never extracted
or written to disk and its text is not printed), parses the PROC REG model blocks, keeps
the two whose dependent variable is LWAGE76, identifies them by their number of
parameters (16 and 30; anything else fails the run), and compares for each:
  - N: "Number of Observations Used" when the listing prints it; otherwise the corrected
    total degrees of freedom + 1 (SAS 6 PROC REG prints no N; the model has an
    intercept). Must equal our N exactly.
  - the ED76 parameter estimate and its standard error, at the listing's printed
    precision: a printed value with d decimals matches iff |ours - printed| < 0.5 x 10^-d
    (the H1 rounding rule), our values unrounded.
Parsing handles both the SAS 6 layout ("Model: MODEL3", "Dependent Variable: LWAGE76",
"C Total", "Prob > |T|") and the SAS 8/9 layout ("Corrected Total", "Number of
Observations Used", "Pr > |t|", "<.0001"), page headers and form feeds inside a block, a
parameter table split across pages, and the descriptive-statistics block printed by the
`s` option (rows are read only after a "Parameter Estimates" heading within a model block),
and a model header repeated on a continuation page (it continues the current block).

A match confirms the data reading and variable construction to more digits than Card's
tables; it settles nothing about the 2SLS standard-error formula. Report-only: nothing
here changes a specification, sample rule, SE formula or claim.

Inputs: data/raw/proximity.zip, runs/h1-a5/metrics.json, runs/h1-b6/metrics.json.
Output: runs/check-sas-listing/metrics.json.
Usage (workspace root): .venv/bin/python code/check_sas_listing.py
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import ivlib  # noqa: E402

RUN = "check-sas-listing"
ZIP = Path("data/raw/proximity.zip")
MEMBER = "read1.lst"

NUM = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[Ee][-+]?\d+)?"
RE_MODEL = re.compile(r"^\s*Model:\s*(\S+)", re.I)
RE_DEP = re.compile(r"^\s*Dependent\s+Variable:\s*(\S+)", re.I)
RE_PARAM_HDR = re.compile(r"Parameter\s+Estimates", re.I)
RE_ROW = re.compile(rf"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+(\d+)\s+({NUM})\s+({NUM})\s+({NUM})\s+(<?\s*{NUM})")
RE_CTOTAL = re.compile(r"^\s*(?:C\s+Total|Corrected\s+Total)\s+(\d+)\s", re.I)
RE_NUSED = re.compile(r"Number\s+of\s+Observations\s+Used\s+(\d+)", re.I)
RE_ERRDF = re.compile(rf"^\s*Error\s+(\d+)\s+{NUM}", re.I)


def decimals(token: str) -> int:
    t = token.lower()
    if "e" in t:
        mant, exp = t.split("e")
        d = len(mant.split(".")[1]) if "." in mant else 0
        return d - int(exp)
    return len(t.split(".")[1]) if "." in t else 0


def parse_listing(text: str) -> list[dict]:
    """Every PROC REG model block: name, dependent variable, N, error df, parameter rows."""
    models: list[dict] = []
    cur = None
    in_params = False
    for raw in text.replace("\f", "\n").splitlines():
        line = raw.rstrip()
        mm = RE_MODEL.match(line)
        if mm and cur is not None and cur["model"] == mm.group(1).upper():
            continue          # the same model's header repeated on a continuation page
        if mm:
            cur = {"model": mm.group(1).upper(), "dep": None, "n_used": None, "ctotal_df": None,
                   "error_df": None, "params": {}}
            models.append(cur)
            in_params = False
            continue
        if cur is None:
            continue
        md = RE_DEP.match(line)
        if md:
            cur["dep"] = md.group(1).upper()
            continue
        mn = RE_NUSED.search(line)
        if mn:
            cur["n_used"] = int(mn.group(1))
            continue
        mc = RE_CTOTAL.match(line)
        if mc:
            cur["ctotal_df"] = int(mc.group(1))
            continue
        me = RE_ERRDF.match(line)
        if me and not in_params:
            cur["error_df"] = int(me.group(1))
            continue
        if RE_PARAM_HDR.search(line):
            in_params = True
            continue
        if in_params:
            mr = RE_ROW.match(line)
            if mr:
                name = mr.group(1).upper()
                if name not in cur["params"]:
                    cur["params"][name] = {"df": int(mr.group(2)), "est": mr.group(3),
                                           "se": mr.group(4)}
    return models


def model_n(m: dict) -> tuple[int | None, str]:
    if m["n_used"] is not None:
        return m["n_used"], "observations-used"
    if m["ctotal_df"] is not None:
        return m["ctotal_df"] + 1, "total-df-plus-1"
    return None, "none"


def matches(ours: float, printed: str) -> tuple[int, float, int]:
    d = decimals(printed)
    diff = float(ours) - float(printed)
    return int(abs(diff) < 0.5 * 10 ** -d), diff, d


def compare(models: list[dict], h1a5: dict, h1b6: dict) -> dict:
    wage = [m for m in models if m["dep"] == "LWAGE76"]
    ivlib.require(len(wage) == 2, f"expected 2 LWAGE76 models in the listing, found {len(wage)}")
    by_k = {len(m["params"]): m for m in wage}
    ivlib.require(sorted(by_k) == [16, 30],
                  f"LWAGE76 models have {sorted(len(m['params']) for m in wage)} parameters, "
                  "expected 16 and 30")
    ours = {"t2c2": (h1a5["a5_n"], h1a5["a5_ols"], h1a5["a5_ols_se"]),
            "t2c5": (h1b6["n_sample"], h1b6["ols_beta"], h1b6["ols_se"])}
    out: dict = {"sas_models_found": len(models), "sas_lwage_models": len(wage)}
    flags = []
    for tag, k in (("t2c2", 16), ("t2c5", 30)):
        m = by_k[k]
        ivlib.require("ED76" in m["params"], f"{m['model']}: no ED76 row")
        n_sas, n_src = model_n(m)
        ivlib.require(n_sas is not None, f"{m['model']}: no N or total df found")
        if m["error_df"] is not None:
            ivlib.require(m["error_df"] == n_sas - k, f"{m['model']}: error df != N - k")
        n_ours, b_ours, se_ours = ours[tag]
        row = m["params"]["ED76"]
        b_ok, b_diff, b_dec = matches(b_ours, row["est"])
        s_ok, s_diff, s_dec = matches(se_ours, row["se"])
        n_ok = int(int(n_ours) == n_sas)
        out.update({f"sas_{tag}_model": m["model"], f"sas_{tag}_k": k,
                    f"sas_{tag}_n": n_sas, f"sas_{tag}_n_source": n_src,
                    f"sas_{tag}_n_ours": int(n_ours), f"sas_{tag}_n_match": n_ok,
                    f"sas_{tag}_ed76": float(row["est"]), f"sas_{tag}_ed76_decimals": b_dec,
                    f"sas_{tag}_ed76_ours": float(b_ours), f"sas_{tag}_ed76_diff": b_diff,
                    f"sas_{tag}_ed76_match": b_ok,
                    f"sas_{tag}_ed76_se": float(row["se"]), f"sas_{tag}_ed76_se_decimals": s_dec,
                    f"sas_{tag}_ed76_se_ours": float(se_ours), f"sas_{tag}_ed76_se_diff": s_diff,
                    f"sas_{tag}_ed76_se_match": s_ok})
        flags += [n_ok, b_ok, s_ok]
    out["sas_items_matched"] = sum(flags)
    out["sas_items"] = len(flags)
    out["sas_ols_match"] = int(all(flags))
    return out


def main() -> int:
    with zipfile.ZipFile(ZIP) as z:
        ivlib.require(MEMBER in z.namelist(), f"{MEMBER} not in {ZIP}")
        text = z.read(MEMBER).decode("latin-1")          # in memory only
    h1a5 = json.loads(Path("runs/h1-a5/metrics.json").read_text())
    h1b6 = json.loads(Path("runs/h1-b6/metrics.json").read_text())
    m = compare(parse_listing(text), h1a5, h1b6)
    ivlib.write_metrics(ivlib.run_dir(RUN) / "metrics.json", m)
    print(f"{RUN}: {m['sas_items_matched']}/{m['sas_items']} items match "
          f"(N, ED76 estimate and SE of the two LWAGE76 models)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
