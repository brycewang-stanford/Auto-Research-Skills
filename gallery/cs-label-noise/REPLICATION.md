# Replication: cs-label-noise

**Outcome (2026-11-18, Replicator):** clean rerun **passed**. All 20 runs in the ledger
were re-executed from scratch in a fresh environment and every recorded metric reproduced
at `rtol = 1e-6` (`atol = 1e-9`). Report: `replication.json` (created 2026-11-18T17:11:29Z,
`reuse_data: false`).

## 1. Environment

Build a new virtual environment from `code/requirements.txt` alone (25 pinned packages,
including numpy 2.5.5, pandas 3.1.1, scikit-learn 1.9.1, scipy 1.18.1, matplotlib 3.11.2).

```bash
cd gallery/cs-label-noise
uv venv --python 3.12 .venv          # the rerun used CPython 3.12.11 (uv 0.7.15)
uv pip install --python .venv/bin/python -r code/requirements.txt
```

Every run calls `.venv/bin/python`, so the environment must sit at `.venv` in the workspace
root. For the rerun it was built outside the workspace and symlinked there (see section 5).
`uv pip freeze` of that environment matches `code/requirements.txt` exactly: nothing extra
was installed and nothing the runs needed was missing.

The rerun driver `crew.py` itself ran under the system `python3` (3.14.6, stdlib only).
Hardware: Apple Silicon (arm64) laptop, macOS 26.6.2. The experiment uses 8 joblib workers
with one BLAS/OpenMP thread each, and the results do not depend on the worker count or on
timing (fit times are kept out of the metrics, in `runs/<id>/timing.json`).

## 2. Data

No data is committed (`data/raw/` and `data/derived/` are git-ignored). The `fetch-data`
run downloads everything; you need internet access for it.

| Dataset | Source | Pin |
|---|---|---|
| breast_cancer | bundled with scikit-learn 1.9.1 | no download |
| credit-g | OpenML via `sklearn.datasets.fetch_openml` | data_id 31, version 1 |
| adult | OpenML via `sklearn.datasets.fetch_openml` | data_id 1590, version 2 |
| covtype | `sklearn.datasets.fetch_covtype` (figshare file 5976039) | sha256 checked by scikit-learn |

The download cache goes to `data/raw/sklearn_home/` (never `~/scikit_learn_data`).
`fetch_data.py` asserts the OpenML data_id, version and md5 it receives, and the sha256 of
each CSV it writes is a ledger metric, so a silently changed upstream file fails the rerun.
For this rerun the existing cache was moved out of the workspace first, so all three
downloads were made fresh from OpenML and figshare. `data/manifest.json` and
`data/CODEBOOK.md` describe each dataset and its licence.

## 3. Commands, in order

Either run everything at once and compare with the ledger:

```bash
python3 ../../crew/scripts/crew.py rerun .     # from the workspace root
```

or run the steps by hand from the workspace root, in this order (the ledger order):

| # | Run | Command | Time in the original run |
|---|---|---|---|
| 1 | timing-synthetic | `.venv/bin/python code/timing_synthetic.py` | 1.6 min |
| 2 | fetch-data | `.venv/bin/python code/fetch_data.py` | 1.5 min |
| 3 | prepare-data | `.venv/bin/python code/prepare_data.py` | 4 s |
| 4 | timing-covtype-stress | `.venv/bin/python code/timing_covtype_stress.py` | 35 s |
| 5 | smoke | `experiment.py --smoke` for variants `main`, `gbdt_noes`, `cleanval` (full command in `runs/smoke/run.json`) | 49 s |
| 6 | main-rho0 | `.venv/bin/python code/experiment.py --rhos 0 --variant main --out results/cells_rho0.csv --metrics runs/main-rho0/metrics.json --timing runs/main-rho0/timing.json` | 5.1 min |
| 7 | exclusion-check | `.venv/bin/python code/exclusion.py --metrics runs/exclusion-check/metrics.json` | <1 s |
| 8 | main-noisy | `.venv/bin/python code/experiment.py --rhos 0.1 0.2 0.3 0.4 --variant main --out results/cells_noisy.csv --metrics runs/main-noisy/metrics.json --timing runs/main-noisy/timing.json` | 11.7 min |
| 9 | h-tests | `.venv/bin/python code/analyze.py --test main --metrics runs/h-tests/metrics.json` | 1 s |
| 10 | descriptives | `.venv/bin/python code/analyze.py --describe --metrics runs/descriptives/metrics.json` | 1 s |
| 11 | abl-noes | `experiment.py --rhos 0 0.4 --variant gbdt_noes ...` then `analyze.py --test noes ...` | 2.7 min |
| 12 | abl-cleanval | `experiment.py --rhos 0.4 --variant cleanval ...` then `analyze.py --test cleanval ...` | 4.9 min |
| 13 | abl-budget | `.venv/bin/python code/analyze.py --test half --metrics runs/abl-budget/metrics.json` | 1 s |
| 14-16 | fig-accuracy, fig-contrasts, fig-ablations | `code/fig_*.py --out paper/figures/fig_*.pdf --metrics runs/fig-*/metrics.json` | 18 s together |
| 17-20 | tab-h1h2, tab-ablations, tab-exclusion, tab-accuracy | `code/tab_*.py --out paper/tables/tab_*.tex --metrics runs/tab-*/metrics.json` | 2 s together |

The exact argument lists are in `runs/<id>/run.json` (`command`). Then `crew.py numbers .`
regenerates `paper/numbers.tex` from `claims.jsonl`.

## 4. Expected time

About **30 minutes** of wall time on an otherwise idle Apple Silicon laptop (the original
runs add up to 29 min; `main-noisy` is 40% of it). This rerun took **61 min** (3,667 s,
16:10:22Z to 17:11:29Z) because other workspaces' reruns (at least ss-null-effect) ran on the same
machine at the same time and competed for the 8 cores. Speed changes no number.

## 5. What was done, and the killed first attempt

1. Checked the fresh environment at the scratch path `replicate-cs/.venv`: CPython 3.12.11,
   `include-system-site-packages = false`, and its live `uv pip freeze` equals
   `code/requirements.txt` line for line. It was reused, not rebuilt.
2. Moved the workspace's own `.venv` to `gallery/.cs-label-noise-venv-orig`, symlinked the
   fresh environment at `.venv`, and moved `data/raw/sklearn_home` to
   `gallery/.cs-label-noise-sklearn-home-orig` so `fetch-data` had to download again.
3. Ran `crew.py rerun` (no `--reuse-data`, default tolerances). A shell `trap` restored the
   original `.venv` and the cache on exit, success or not; both were back at 17:11:29Z.
   The symlink was never committed.

**Earlier attempts.** Two earlier rerun attempts on 2026-11-18 were killed by session
restarts before they finished: the first at 14:51-15:03Z (SIGTERM after 769 s), the second
at 15:04-15:18Z (SIGTERM after about 14 min, during the long experiment runs). Neither
wrote `replication.json`, and their wrapper script restored the workspace `.venv` both times.
The first attempt also overlapped with the figures-ra rerunning the table and figure runs
(15:02Z), so its workspace copy predated those records. This third attempt was launched
detached from the session (`nohup`) and ran to completion against the current ledger.

## 6. Mismatches and workarounds

- Mismatches: **none**. 20/20 runs `match`; no run failed.
- Workarounds: none needed in the analysis. The only operational steps were the
  `.venv` symlink swap and the detached launch described above.
