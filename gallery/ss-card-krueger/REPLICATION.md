# Replication: ss-card-krueger

How to reproduce every number in `paper/main.pdf` from this workspace, and what happened
when the Replicator did so. Result of the clean rerun of 2026-11-19: **passed, 15 of 15
runs reproduced** (`replication.json`, created 2026-11-19T12:29:25Z). Written by the
Replicator; the outcome section reports `replication.json`.

## 1. Environment

- **Python 3.12.** The rerun used CPython 3.12.11 for every run (macOS 26.6.2 arm64), the
  same interpreter version recorded in each `runs/<id>/run.json`. `replication.json`
  records `python 3.14.6`: that is the interpreter that ran `crew.py` itself, not the
  runs' `.venv`.
- **Python packages:** `code/requirements.txt` only (25 pinned packages: numpy 2.5.5,
  pandas 3.1.1, scipy 1.18.1, statsmodels 0.15.0, matplotlib 3.11.2, ...). No R, Stata or
  LaTeX is needed for the runs (LaTeX only to compile the paper, section 3).
- **No seeds matter for the results.** Every estimator is deterministic. The only seed
  (20261119) is in `code/test_ck.py`, which generates the synthetic file for
  check-synthetic.
- The runs call `.venv/bin/python -I ...` from the workspace root, so the environment
  must live at `.venv` inside the workspace (a real directory or a symlink).

```bash
cd gallery/ss-card-krueger
uv venv --python 3.12 .venv
uv pip install --python .venv/bin/python -r code/requirements.txt
uv pip freeze --python .venv/bin/python | diff - <(grep -v '^#' code/requirements.txt | sort)   # expect no output
```

The Replicator built the environment outside the workspace with uv 0.7.15, confirmed
that `uv pip freeze` equals `code/requirements.txt` exactly (25 packages, nothing extra),
and symlinked it at `.venv` for the rerun. Nothing beyond the requirements file was
needed.

## 2. Data

One public archive (`data/manifest.json`): `njmin.zip` from David Card's data page,
`https://davidcard.berkeley.edu/data_sets/njmin.zip` (23,017 bytes; SHA-256
`41a29aec...ba587`; members `public.dat`, `codebook`, `check.sas`, `read.me`,
`survey1.nj`, `survey2.nj`). Run fetch-data downloads it (network access needed),
fails unless the size and SHA-256 equal the pinned values, and unzips it to
`data/raw/njmin/`. Run prepare-data parses `public.dat` (410 stores) into
`data/derived/stores.csv` and `data/prepare_metrics.json`. Raw and derived files are
git-ignored; nothing is redistributed.

The rerun re-downloaded and re-derived both (`reuse_data: false`). fetch-data's metrics
include the SHA-256 of the archive and of every member, and they matched, so the bytes
served on 2026-11-19T12:28Z were identical to those of the first retrieval.

## 3. Commands

Automatic (what the Replicator ran):

```bash
python3 <repo>/crew/scripts/crew.py rerun gallery/ss-card-krueger
python3 <repo>/crew/scripts/crew.py validate gallery/ss-card-krueger --strict
```

By hand, from the workspace root, in the order `crew.py rerun` used (a run comes after
every run that produced one of its inputs, otherwise the order the runs were recorded).
Every command is `.venv/bin/python -I <script> ...`; each writes the metrics file
recorded in `runs/<id>/run.json`.

| # | Run | Script and arguments | Writes besides metrics |
|---|---|---|---|
| 1 | fetch-data | `code/fetch_data.py` | `data/raw/njmin.zip`, `data/raw/njmin/*`, `data/fetch_metrics.json` |
| 2 | prepare-data | `code/prepare_data.py` | `data/derived/stores.csv`, `data/prepare_metrics.json` |
| 3 | check-synthetic | `code/test_ck.py` | `runs/check-synthetic/synthetic_stores.csv` |
| 4 | main-t3 | `code/ck_analysis.py main-t3` | |
| 5 | main-t4 | `code/ck_analysis.py main-t4` | |
| 6 | se-alt | `code/ck_analysis.py se-alt` | |
| 7 | placebo-hiwage | `code/ck_analysis.py placebo-hiwage` | |
| 8 | h2-winsor | `code/ck_analysis.py h2-winsor` | `runs/h2-winsor/capped.csv` |
| 9 | h2-closures-excl | `code/ck_analysis.py h2-closures-excl` | |
| 10 | h2-nw-rule | `code/ck_analysis.py h2-nw-rule` | |
| 11 | verdict | `code/verdict.py` | |
| 12 | pub-values | `code/pub_values.py --metrics runs/pub-values/metrics.json` | (reads `sources/notes.md`) |
| 13 | tab-h2 | `code/tab_h2.py --metrics runs/tab-h2/metrics.json` | `paper/tables/tab_h2.tex` |
| 14 | tab-replication | `code/tab_replication.py --metrics runs/tab-replication/metrics.json` | `paper/tables/tab_replication.tex` |
| 15 | fig-dfte-dist | `code/fig_dfte_dist.py --metrics runs/fig-dfte-dist/metrics.json` | `paper/figures/fig_dfte_dist.pdf` |

The scripts create their output directories themselves. Then `crew.py numbers gallery/ss-card-krueger` regenerates
`paper/numbers.tex` from `claims.jsonl`, and the paper compiles from `paper/main.tex`
(pdflatex, bibtex with `refs.bib`, pdflatex twice).

## 4. Expected time

**Under a minute on a laptop.** The whole rerun took 46 s wall clock (12:28:39Z to
12:29:25Z), including the download, with a load average of about 5 on the machine at
the start. Building the environment with uv took well under a minute more (packages were
in uv's cache; a cold install downloads about 25 wheels).

## 5. Outcome of the rerun

**`replication.json`: PASSED, 15 of 15 runs reproduced** (created 2026-11-19T12:29:25Z;
rtol 1e-6, atol 1e-9, the protocol defaults; `reuse_data: false`).

| Run (in rerun order) | Status |
|---|---|
| fetch-data, prepare-data, check-synthetic | match |
| main-t3, main-t4, se-alt, placebo-hiwage | match |
| h2-winsor, h2-closures-excl, h2-nw-rule | match |
| verdict | match |
| pub-values, tab-h2, tab-replication, fig-dfte-dist | match |

Every run exited 0 and every recorded metric matched, so there is no mismatch to
explain. Notes:

- The headline numbers therefore reproduce from a fresh environment: Table 3 row 3
  DiD 2.7536 (SE 1.3100), row 4 2.7500 (1.3423); Table 4 column (i) N = 357,
  coefficient 2.3258 (SE 1.1916); H2 winsorized 2.3395, ratio 0.851.
- One judged target sits close to its tolerance: the row-3 DiD SE misses the published
  1.36 by 0.04997, against a threshold of 0.05 (`verdict` metric
  `h1a_did_se_absdiff`). The rerun reproduced that SE to within rtol 1e-6 (about
  1.3e-6 absolute, against a margin of 2.6e-5), so its met flag did not change in the
  fresh environment.
- The rerun compares metrics, not output bytes. The table and figure runs' metrics
  matched; the regenerated `.tex` and `.pdf` files in the temporary copy were not
  byte-compared with the committed ones.
- The rerun is newer than every run record (latest: fig-dfte-dist,
  2026-11-19T08:10:17Z). After the rerun the SHA-256 of every `runs/<id>/run.json`
  still equals the `record_sha256` in `replication.json`, so no run was re-recorded
  while the rerun was going on.
- `crew.py rerun` copied the workspace at 12:28:39Z. The Scout edited `refs.bib` and
  `sources/sources.json` around the same time (log entry `bib-fixed`, 12:28:26Z). Those
  files are not an input of any run (pub-values reads `sources/notes.md`, which was
  not edited), so the edit does not affect this result.

## 6. Procedure and workarounds

1. Fresh environment built outside the workspace (scratch directory, uv 0.7.15,
   CPython 3.12.11) from `code/requirements.txt` alone; `uv pip freeze` identical to the
   requirements file.
2. The authors' `.venv` was parked at `gallery/.ss-card-krueger-venv-orig`, the fresh
   environment was symlinked at `.venv`, and an exit trap restored the original
   (restored 12:29:25Z; `.venv` is a real directory again and the parked copy is gone).
   The symlink was never committed (`.venv` is gitignored).
3. `crew.py rerun` was run detached with `nohup`. One attempt, no restarts.

Workarounds: none beyond the environment symlink. No code, data, metric or tolerance was
changed, and `--reuse-data` was not used.
