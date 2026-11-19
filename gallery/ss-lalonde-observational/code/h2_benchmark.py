"""Run h2-benchmark (H2, descriptive): ONLY after the results gate is approved (design.method.h2_descriptive).

This is the only script in code/ that contains the experimental benchmark. It reads
runs/main-aipw/metrics.json and nothing else.
  diff     = theta - BENCH
  se_comb  = sqrt(SE^2 + BENCH_SE^2), BENCH_SE the SE published with the benchmark
             (Dehejia and Wahba 1999, Table 3, row NSW, column (1); the robust 670.82 is not used)
  95% band = diff +/- 1.959964 se_comb
The two estimates share the 185 treated men, so their covariance is positive and se_comb
overstates the uncertainty (stated with the number). Descriptive only: no test, no p-value,
no ranking or choice of estimators.

Run from the workspace root, after the results gate:  .venv/bin/python -I code/h2_benchmark.py
"""

import json
import math
import sys
from pathlib import Path

from scipy.stats import norm

MAIN_METRICS = Path("runs/main-aipw/metrics.json")
OUT = Path("runs/h2-benchmark/metrics.json")
BENCH = 1794.0
BENCH_SE = 633.0
Z95 = float(norm.ppf(0.975))


def h2(theta: float, se: float) -> dict:
    diff = theta - BENCH
    se_comb = math.sqrt(se ** 2 + BENCH_SE ** 2)
    return {"h2_diff": diff, "h2_se_combined": se_comb,
            "h2_ci_low": diff - Z95 * se_comb, "h2_ci_high": diff + Z95 * se_comb}


def main() -> int:
    m = json.loads(MAIN_METRICS.read_text())
    met = {"benchmark": BENCH, "benchmark_se": BENCH_SE,
           "main_effect": float(m["effect"]), "main_se": float(m["se"])}
    met.update(h2(float(m["effect"]), float(m["se"])))
    met["note"] = "descriptive; se_combined ignores the shared treated men and overstates the uncertainty"
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(met, indent=2) + "\n")
    print(met)
    return 0


if __name__ == "__main__":
    sys.exit(main())
