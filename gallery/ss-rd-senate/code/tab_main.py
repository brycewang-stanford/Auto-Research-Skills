"""Table: H1 replicated against the printed CCFT (2017, Sec. 7.2) default output.

Columns: printed (strings copied from sources/notes.md, the Scout's record of the
article), replicated under masspoints 'off' (primary) and 'adjust' (secondary).
Replicated cells are LaTeX macros from paper/numbers.tex (generated from claims.jsonl).
Each macro is checked here: its claim must name a run metric, and the claim value must
equal that metric in runs/h1-rdrobust/metrics.json (or the run named by the claim).

Output: paper/tables/tab_main.tex (tabular only; the Writer wraps it in table and
caption from paper/figures/CAPTIONS.md). Metrics: runs/tab-main/metrics.json.

Usage (crew.py run --kind analysis):
    .venv/bin/python code/tab_main.py runs/tab-main/metrics.json
"""
import argparse
import json
import os
import re

WS = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
H1 = os.path.join(WS, "runs", "h1-rdrobust", "metrics.json")
NOTES = os.path.join(WS, "sources", "notes.md")
NUMBERS = os.path.join(WS, "paper", "numbers.tex")
CLAIMS = os.path.join(WS, "claims.jsonl")
OUT = os.path.join(WS, "paper", "tables", "tab_main.tex")

def load_macros():
    """macro name -> claim id, from the generated numbers.tex."""
    out = {}
    pat = re.compile(r"\\newcommand\{\\(\w+)\}\{(.*?)\}\s*%\s*(\S+)")
    with open(NUMBERS) as f:
        for line in f:
            m = pat.search(line)
            if m:
                out[m.group(1)] = m.group(3)
    return out


def load_claims():
    with open(CLAIMS) as f:
        return [json.loads(l) for l in f if l.strip()]


def check_macro(name, macro_to_id, claims_by_id, metrics_cache):
    if name not in macro_to_id:
        raise SystemExit(f"macro {name} is not in numbers.tex")
    c = claims_by_id[macro_to_id[name]]
    sup = c["support"][0]
    run, metric = sup["run"], sup["metric"]
    if run not in metrics_cache:
        with open(os.path.join(WS, "runs", run, "metrics.json")) as f:
            metrics_cache[run] = json.load(f)
    val = metrics_cache[run][metric]
    diff = abs(float(val) - float(c["value"]))
    if diff > 1e-9 * max(1.0, abs(float(val))):
        raise SystemExit(f"claim {c['id']} value differs from run {run} metric {metric}")
    return diff


def printed_targets():
    """Printed CCFT (2017) values, copied as strings from the Scout's record."""
    with open(NOTES) as f:
        txt = f.read()
    est = re.search(r"Conventional estimate: ([\d.]+),", txt).group(1)
    lo, hi = re.search(r"Robust bias-corrected CI: \[([\d.]+), ([\d.]+)\]", txt).groups()
    n = re.search(r"N = ([\d,]+) with a non-missing outcome", txt).group(1)
    h, b = re.search(r"h = ([\d.]+) on both sides, b = ([\d.]+)", txt).groups()
    return {"est": est, "lo": lo, "hi": hi, "n": n, "h": h, "b": b}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("metrics")
    args = ap.parse_args()

    macro_to_id = load_macros()
    claims = load_claims()
    claims_by_id = {c["id"]: c for c in claims}
    cache = {}
    checked = {}
    for name in ["RdEffect", "RdCiLow", "RdCiHigh", "RdN", "RdBw", "RdB",
                 "RdAdjEffect", "RdAdjCiLow", "RdAdjCiHigh", "RdAdjBw", "RdSensAdjustN",
                 "RdSensAdjustB"]:
        checked[name] = check_macro(name, macro_to_id, claims_by_id, cache)

    with open(H1) as f:
        h1 = json.load(f)
    verdict_off = "pass" if h1["h1_pass_off"] == 1 else "fail"
    pr = printed_targets()

    rows = [
        ("Conventional estimate (pp)", pr["est"], r"\RdEffect", r"\RdAdjEffect"),
        ("Robust bias-corrected 95\\% CI, lower (pp)", pr["lo"], r"\RdCiLow", r"\RdAdjCiLow"),
        ("Robust bias-corrected 95\\% CI, upper (pp)", pr["hi"], r"\RdCiHigh", r"\RdAdjCiHigh"),
        ("$N$ (elections with an observed outcome)", pr["n"], r"\RdN", r"\RdSensAdjustN"),
        ("Bandwidth $h$ (pp, both sides)", pr["h"], r"\RdBw", r"\RdAdjBw"),
        ("Bias bandwidth $b$ (pp, left side)", pr["b"], r"\RdB", r"\RdSensAdjustB"),
    ]
    lines = [
        r"\begin{tabular}{lrrr}",
        r"\toprule",
        r"& Printed (CCFT 2017) & Replicated, \texttt{off} (primary) & Replicated, \texttt{adjust} (secondary) \\",
        r"\midrule",
    ]
    for label, printed, off, adj in rows:
        lines.append(f"{label} & {printed} & {off} & {adj} \\\\")
    lines += [
        r"\midrule",
        f"Tolerance check (estimate and CI within 0.01 pp; $N$ exact; $h$ within 0.0005) & -- & {verdict_off} & not judged \\\\",
        r"\bottomrule",
        r"\end{tabular}",
        "",
    ]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        f.write("\n".join(lines))

    m = {
        "n_macros_checked": len(checked),
        "max_macro_check_diff": max(checked.values()),
        "printed_est": float(pr["est"]),
        "printed_h": float(pr["h"]),
        "printed_b": float(pr["b"]),
        "verdict_off": h1["h1_pass_off"],
        "n_rows": len(rows),
    }
    os.makedirs(os.path.dirname(os.path.abspath(args.metrics)), exist_ok=True)
    with open(args.metrics, "w") as f:
        json.dump(m, f, indent=2)
        f.write("\n")
    print("\n".join(lines))
    print(json.dumps(m, indent=2))


if __name__ == "__main__":
    main()
