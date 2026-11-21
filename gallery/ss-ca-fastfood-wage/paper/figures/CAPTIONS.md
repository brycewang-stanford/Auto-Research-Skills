# Figure captions (ss-ca-fastfood-wage)

Each figure is built by a script under `code/` that runs through `crew.py run --kind analysis`
with the role `figures-ra`, after the runs it reads. The scripts read only files that logged
runs wrote, each declared with `--input`; they read no claim file and nothing under `data/`, and
they estimate nothing. No number is typed by hand.

Which estimator, pool and outcome the paper uses is fixed by run `select` after the design gate,
and the figure note the design requires (design-r2 D11) depends on it. So each script writes its
own caption, printed from the same run outputs it plots, next to the PDF:
`paper/figures/<figure>.caption.md`. That file is the caption; this one only lists the figures.
Where the text quotes a number that also appears in a caption, the Writer uses the claim's macro.

| Figure | Run | Script | Reads | Writes |
|---|---|---|---|---|
| `fig_event.pdf` | `fig-event` | `code/fig_event.py` | `runs/event-path/event_path.csv`, `runs/event-path/metrics.json`, `runs/level-mde/metrics.json`, `runs/h1-wage/metrics.json` | `paper/figures/fig_event.pdf`, `paper/figures/fig_event.caption.md`, `runs/fig-event/metrics.json` |
| `fig_select.pdf` | `fig-select` | `code/fig_select.py` | `runs/select/pseudo_atts.csv`, `runs/select/metrics.json` | `paper/figures/fig_select.pdf`, `paper/figures/fig_select.caption.md`, `runs/fig-select/metrics.json` |
| `fig_placebo.pdf` | `fig-placebo` | `code/fig_placebo.py` | `runs/h2-emp/placebos.csv`, `runs/h2-emp/metrics.json`, `runs/level-mde/metrics.json` | `paper/figures/fig_placebo.pdf`, `paper/figures/fig_placebo.caption.md`, `runs/fig-placebo/metrics.json` |

All three scripts import `code/figlib.py` (palette, style, caption wording of candidate ids);
each run names it with `--code` as well. fig-event and fig-placebo read `runs/level-mde/metrics.json`
only for `sdid_floor_h2`, `pool_h2` and `qcal_<pool>_*`: when the selected candidate is SDID their
captions state the Monte Carlo floor on the critical values (design.method C1), its values, and
which critical values it sets. fig-event also reads `runs/h1-wage/metrics.json` (`selected`, `nu`,
`h1_c_hi95`, `h1_c_hi975`): its caption states H1's one-sided critical values for panel (b), says
that the wage bands use the H2 critical values and whether they are narrower than the H1 test,
and that a wage band excluding zero is not evidence against the H1 verdict (code-r2 C4). Each
generated caption's "Generated from" line lists every file its script read.

What each figure shows, and what it cannot:

- **fig_event**: the quarterly California-minus-counterfactual gap of the selected candidate
  (employment outcome and wage), with pointwise 95% bands, COVID quarters, the post window, AB 257
  and the first quarter after AB 1228 was signed. It is report-only; the bands are pointwise; it
  is a check of falsification (ii) only if DD is selected, and never a pre-trend test for DDT, SC
  or SDID (the caption prints the run's `figure_note`).
- **fig_select**: the 24 candidates' pre-period RMSEs (bars from zero) and the six pseudo-ATTs
  behind each. Pre-2020 data only; a placebo criterion with no sampling interval; says nothing
  about the effect of the law.
- **fig_placebo**: California's pooled H2 estimate with its 90% and 95% intervals against the
  donors' placebo estimates, unscaled and population-scaled, and ± SE. Not a permutation test;
  the H2 label comes from the intervals in run h2-emp.

Style: one palette (Okabe-Ito) and one style for every figure; every distinction also has a
grayscale cue (marker fill or shape, hatching, line style, position). Vector PDFs with embedded
STIX fonts at 6.5 to 8.5 pt, written without a creation date so the same inputs give the same
bytes. Estimates are shown in 100 × log points; bars start at zero; no axis is cropped.

Example commands (after the design gate, the code review and the runs they read):

```bash
python3 crew/scripts/crew.py run <ws> --id fig-select --role figures-ra --kind analysis \
  --code code/fig_select.py --code code/figlib.py \
  --input runs/select/pseudo_atts.csv --input runs/select/metrics.json \
  --output paper/figures/fig_select.pdf --output paper/figures/fig_select.caption.md \
  --metrics runs/fig-select/metrics.json -- python3 code/fig_select.py
```

and likewise for `fig-event` and `fig-placebo` with the inputs in the table above.
