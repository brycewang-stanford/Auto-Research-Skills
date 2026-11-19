# Design evidence (design-r1 F4)

Proof that no rule, deviation or threat in `plan.json` changed after the `diag-overlap`
run. `lalonde_write_design.py` is the Designer's deterministic writer; `reconstruct.py`
re-runs it on `plan.json` at commit 716b6c3 (`base_716b6c3.json`) to rebuild the
pre-diagnostics design, `reconstructed_320cc2.json`, whose SHA-256 matches the hash the
Designer logged before `diag-overlap` ran (320cc2...). Copied from the Designer's scratch
space by the PI on 2026-11-19 so that the proof is kept with the workspace.
