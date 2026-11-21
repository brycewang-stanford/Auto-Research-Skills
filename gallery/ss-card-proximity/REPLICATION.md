# Replication: ss-card-proximity

How to reproduce every number in `paper/main.pdf` from this workspace, and what happened
when the Replicator did so. Result of the clean rerun of 2026-11-21: **passed, 18 of 18
runs reproduced, all 911 recorded metrics matched** (`replication.json`, created
2026-11-21T04:33:26Z). Written by the Replicator; the outcome section reports
`replication.json`.

## 1. What was rerun

Every run in the ledger (`runs/<id>/run.json`), 18 in all: the two data runs
(fetch-data, prepare-data), the synthetic check of `code/ivlib.py` (check-synthetic),
the analysis runs for H1-H5 and the report-only checks, the verdict, the post hoc
diagnostic diag-panelb (D4), the SAS-listing check, describe-sample (D7) and the figure
run fig-chr (including its D8 relabelling, recorded 2026-11-21T04:01:41Z, the latest run
in the ledger). Nothing was skipped and `--reuse-data` was not used: the archive was
downloaded again from David Card's page.

## 2. Environment

- **Python 3.14.6** (Homebrew CPython, macOS 26.6.2 arm64, Apple M3, 8 cores), the same
  interpreter version recorded in every analysis run's `run.json`.
- **A fresh virtual environment built from `code/requirements.txt` alone.** `crew.py
  rerun --setup` created it inside the temporary copy of the workspace; the authors'
  `.venv` was not copied. The install (pip 26.1.2) exited 0 and installed exactly the 35
  pinned packages of `code/requirements.txt` (numpy 2.5.3, pandas 3.0.5, scipy 1.18.1,
  statsmodels 0.15.0, linearmodels 7.1, ivmodels 0.10.0, glum 3.5.0, numba 0.68.1,
  matplotlib 3.11.2, ...), nothing more and nothing missing. Nothing beyond the
  requirements file was needed.
- The runs call `.venv/bin/python <script>` (15 runs) or `python3 <script>` (fetch-data,
  prepare-data, describe-sample, which use the standard library only) from the workspace
  root. In the rerun the fresh `.venv/bin` was first on `PATH`, so `python3` was that
  environment's 3.14.6 too.
- **Seeds.** The only randomness is the start draws of the Panel B robust projection
  (`ivlib.PanelB`, `numpy.random.default_rng(4483)`) and the synthetic data of
  check-synthetic (same seed). Both are fixed in the code.
- No R, Stata or LaTeX is needed for the runs; LaTeX is needed only to compile the paper.

```bash
cd gallery/ss-card-proximity
python3.14 -m venv .venv
.venv/bin/pip install -r code/requirements.txt
```

## 3. Data

One public archive (`data/manifest.json`): `proximity.zip` from David Card's data page,
`https://davidcard.berkeley.edu/data_sets/proximity.zip` (134,563 bytes, SHA-256
`0e9b2ad4...82691f`). fetch-data downloads it (network access needed), fails unless the
size, the SHA-256 and the member list equal the pinned values, and extracts `nls.dat`,
`code_bk.txt`, `read1.sas` and `readme` to `data/raw/proximity/`; `read1.lst` stays in
the zip. prepare-data parses `nls.dat` into `data/derived/card_analysis.csv` (3,010
rows). Raw and derived files are git-ignored; nothing is redistributed.

In the rerun fetch-data's metrics, which include the SHA-256 of the archive and of
every extracted member, matched the ledger, so the bytes served on 2026-11-21 at about
04:04Z were identical to those of the first retrieval.

## 4. Commands

Automatic (what the Replicator ran, from the repository root):

```bash
python3 crew/scripts/crew.py rerun gallery/ss-card-proximity \
  --setup "python3.14 -m venv .venv && .venv/bin/pip install -r code/requirements.txt"
python3 crew/scripts/crew.py validate gallery/ss-card-proximity
```

By hand, from the workspace root after building `.venv` (section 2), in the order
`crew.py rerun` used (a run comes after every run that produced one of its inputs,
otherwise the order the runs were first recorded). Each command writes the metrics file
named in `runs/<id>/run.json`.

| # | Run | Command | Writes besides metrics |
|---|---|---|---|
| 1 | fetch-data | `python3 code/fetch_data.py` | `data/raw/proximity.zip`, `data/raw/proximity/*`, `data/fetch_metrics.json` |
| 2 | prepare-data | `python3 code/prepare_data.py` | `data/derived/card_analysis.csv`, `data/prepare_metrics.json` |
| 3 | check-synthetic | `.venv/bin/python code/test_ivlib.py` | `runs/check-synthetic/synthetic_card.csv`, `runs/check-synthetic/entry/...` |
| 4 | h1-b6 | `.venv/bin/python code/h1_b6.py` | |
| 5 | h1-a6 | `.venv/bin/python code/h1_a6.py` | |
| 6 | h1-a5 | `.venv/bin/python code/h1_a5.py` | |
| 7 | h2h3-weakiv | `.venv/bin/python code/h2h3_weakiv.py` | |
| 8 | h3b-subvector | `.venv/bin/python code/h3b_subvector.py` | `runs/h3b-subvector/profile.csv` |
| 9 | h4-chr | `.venv/bin/python code/h4_chr.py` | `runs/h4-chr/chr_grid.csv` |
| 10 | h5-cf | `.venv/bin/python code/h5_cf.py` | |
| 11 | r-age1419 | `.venv/bin/python code/r_age1419.py` | |
| 12 | r-balance | `.venv/bin/python code/r_balance.py` | |
| 13 | r-cluster | `.venv/bin/python code/r_cluster.py` | |
| 14 | verdict | `.venv/bin/python code/verdict.py` | |
| 15 | diag-panelb | `.venv/bin/python code/diag_panelb.py` | |
| 16 | check-sas-listing | `.venv/bin/python code/check_sas_listing.py` | (reads `read1.lst` inside the zip) |
| 17 | describe-sample | `python3 code/describe_sample.py` | |
| 18 | fig-chr | `.venv/bin/python code/fig_chr.py --metrics runs/fig-chr/metrics.json` | `paper/figures/chr.pdf` |

Then `crew.py numbers gallery/ss-card-proximity` regenerates `paper/numbers.tex` from
`claims.jsonl`, and the paper compiles from `paper/main.tex` (pdflatex, bibtex with
`refs.bib`, pdflatex twice).

## 5. Expected time

**About 30 minutes on a laptop; budget 15-30.** The whole rerun took **1,806 s (30 min
6 s) wall clock**, 04:03:20Z to 04:33:26Z, including the environment build and the
download. The machine was heavily shared at the time (1-minute load average 9.2 at the start,
5-minute 27.6, after a peak near 95 twenty minutes earlier, from other sessions), so this is an upper
figure. Two runs dominate: check-synthetic (435 s when first recorded) and h3b-subvector
(333 s, the grid inversions of the subvector sets); every other run takes a few seconds.
The environment build takes about a minute with a warm pip cache.

## 6. Outcome of the rerun

**`replication.json`: PASSED, 18 of 18 runs reproduced** (created 2026-11-21T04:33:26Z;
rtol 1e-6, atol 1e-9, the protocol defaults; `reuse_data: false`; setup exit code 0).

| Runs (in rerun order) | Status |
|---|---|
| fetch-data, prepare-data, check-synthetic | match |
| h1-b6, h1-a6, h1-a5, h2h3-weakiv, h3b-subvector, h4-chr, h5-cf | match |
| r-age1419, r-balance, r-cluster, verdict | match |
| diag-panelb, check-sas-listing, describe-sample, fig-chr | match |

Every run exited 0 and every one of the 911 recorded metrics matched within tolerance, so
**no metric failed to match** and there is no mismatch to explain. Notes:

- The headline numbers therefore reproduce from a fresh environment, for example the
  B6 2SLS return to schooling 0.13244 (conventional SE 0.04934, HC1 0.04878) on N =
  3,010, first stage on `nearc4` 0.3639 (SE 0.1024).
- The rerun compares metrics, not output bytes. The regenerated `chr.pdf`, `profile.csv`
  and `chr_grid.csv` in the temporary copy were not byte-compared with the workspace's
  copies; fig-chr's metrics (piece counts, window, critical values) matched.
- `replication.json` is newer than every run record (latest: fig-chr,
  2026-11-21T04:01:41Z). After the rerun the SHA-256 of every `runs/<id>/run.json` still
  equals its `record_sha256` in `replication.json`, so no run was re-recorded while the
  rerun was going on. No file under `code/`, `data/` (other than outputs), `sources/` or
  `runs/` changed between the copy (04:03:20Z) and the end of the rerun. The Writer
  revised `paper/` during the rerun; no run reads `paper/`, so that does not affect the
  result.

## 7. Attempts and workarounds

1. First attempt, started 2026-11-21 about 03:43Z: interrupted with the session before it
   finished. It wrote no `replication.json` and no line in `replication-history.jsonl`
   (the tool writes both only at the end); its temporary copy was removed by hand.
2. Second attempt, 04:03:20Z-04:33:26Z, run detached (`nohup`) so that it would survive
   another interruption: passed, recorded in `replication-history.jsonl`.

Workarounds: none. No code, data, metric or tolerance was changed, nothing was installed
beyond `code/requirements.txt`, and `--reuse-data` was not used.
