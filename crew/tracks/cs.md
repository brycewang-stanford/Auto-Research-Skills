# Computer-science track

An empirical machine-learning paper: a question about how methods behave, answered by
experiments that anyone can rerun.

## What a finished paper contains

1. A question and a hypothesis that an experiment could contradict.
2. Related work: what is known, and what this adds.
3. Setup: datasets, splits, methods, tuning, metric, seeds, compute.
4. Results with uncertainty across seeds, in tables and figures built from the run ledger.
5. Ablations or controls that test the explanation, not only the headline.
6. Limitations, scope, and every deviation from the approved design.

## Design rules

- At least five seeds per configuration; report mean and standard deviation, and say how
  many seeds. A difference inside the noise is no difference.
- Same splits, same tuning budget, same preprocessing for every method. Tune on
  validation data. Touch the test set once per configuration.
- Compare against the strong, simple baseline, tuned as carefully as the method of
  interest.
- Evaluate against the dataset's own labels with a standard metric implementation.
- State scope exactly. Three small datasets support a claim about those datasets.
- Fix the compute budget at the design gate. Seed tasks must run on a laptop CPU in under
  an hour in total.

## Tools

Python with pinned versions in `code/requirements.txt`: scikit-learn, NumPy, pandas,
PyTorch where needed, matplotlib for figures. Use a virtual environment inside the
workspace (`.venv/`, git-ignored). Prefer datasets that ship with a library or have a
stable download with a hash.

Patterns in this repository the roles can draw on:
[`systems/aideml`](../../systems/aideml) for experiment search,
[`benchmarks/mlagentbench`](../../benchmarks/mlagentbench) for task framing, and the
experiment and figures [starter kits](../../catalog/STARTER-KITS.md).

## Common ways these papers go wrong

Test-set tuning; leakage through preprocessing fitted on all data; a weak or untuned
baseline; one seed; a metric chosen after seeing results; "robust" and "consistent"
claimed from a handful of runs; an ablation that removes the method but also changes the
budget.
