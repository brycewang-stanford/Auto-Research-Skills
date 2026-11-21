# Seed acquisition and preparation notes

Source: `crew/bench/seeds/ss-null-effect/task.json` and the immutable repository CSV at commit `40fac308b3c6ed5a9832e9d687519b12c9487b76`. The full origin URL, CC0-1.0 terms, retrieval date and verified SHA256 are in `manifest.json`. This is synthetic data; no historical administrative dataset identity or real currency is established.

`code/fetch_seed.py` downloads that pinned source, checks the published seed hash before parsing, and copies identical bytes to `data/raw/seed.csv`. The logged `fetch-seed` data-prep run records code/output hashes and schema/missingness metrics. It uses only Python's standard library. A clean rerun downloads identical bytes from the pinned URL. No derived sample or cleaned data is necessary: analysis should read the unchanged raw copy. No rows were deleted, imputed, trimmed, winsorized or selected.

## Variables authorized for use

Definitions come from seed task metadata and plan.json design.data; details absent from these sources remain undocumented.

| Variable | Definition | Units/coding |
|---|---|---|
| id | Person identifier; one row per supplied cohort member | Identifier, unique and nonmissing |
| treat | Voluntary program participation during 1976–77 | Binary 0/1; 1 participant |
| age | Preprogram age | Years (age reference date undocumented) |
| educ | Preprogram education | Supplied numeric education measure; exact coding/unit undocumented |
| married | Preprogram marital indicator | Binary 0/1 |
| urban | Preprogram urban-residence indicator | Binary 0/1 |
| region | Preprogram region | Categorical label; observed midwest, northeast, south, west |
| children | Preprogram children measure | Supplied numeric measure; exact definition undocumented |
| health_limit | Preprogram health-limitation indicator | Binary 0/1 |
| re74 | Preprogram 1974 earnings | Supplied earnings units; currency and price base undocumented |
| re75 | Preprogram 1975 earnings; prespecified sole placebo outcome | Supplied earnings units; currency and price base undocumented |
| unemp74 | Preprogram unemployment indicator, 1974 | Binary 0/1; duration/reference-period definition undocumented |
| unemp75 | Preprogram unemployment indicator, 1975 | Binary 0/1; duration/reference-period definition undocumented |
| re78 | Primary postprogram 1978 earnings | Supplied earnings units; currency and price base undocumented |

Remaining header names appear in `schema.json` solely to document schema: re79, employed78, hours78, benefits78, wellbeing78 and survey_q01–survey_q20 are excluded by design. Their values were copied and hashed as source bytes but not parsed, validated, summarized or searched. Neither postprogram earnings summaries nor baseline earnings summaries were calculated. No treatment-group counts or relationships were calculated.

## Source comparisons and authorized validation

- Source task reports 4000 adults: observed row count exactly 4000, all retained; zero dropped.
- Required names match the first fourteen header fields exactly. Full header has 39 columns, consistent with id, treatment, eleven preprogram characteristics, six postprogram outcomes and twenty survey items described by the seed.
- All 4000 ids are unique/nonmissing; duplicates: zero.
- Missing values in every required field: zero. Nonfinite numerical values in every required numeric field (including re75/re78): zero. These are validity counts, not outcome summaries.
- Nonbinary values in treat, married, urban, health_limit, unemp74 and unemp75: zero.
- Region is nonmissing throughout and has four observed labels listed above. **Limitation:** neither source task nor design supplies an external allowed region vocabulary. Nonmissingness and observed label schema are verified; independent validation that these are the intended “known” categories cannot be performed from available metadata. This should be resolved by design review rather than silently defining validity from observed data.
- Expected SHA256 `f09fba8695df8d2cfe44abe770860772f07a562ad88c19789f6feab946048ca9` matches acquired bytes exactly (483855 bytes).
- Source description says about 40% participate. This was not checked, because this assignment permits schema/missingness only and does not authorize treatment summaries. No source outcome summary exists in the supplied metadata; none was sought or calculated.

The run's `validation_pass=1` refers to executable schema/missingness checks only; it does not resolve the unavailable external region vocabulary, validate identification, or authorize analysis. Any failed required check raises an error; the code performs no sample restriction or automatic repair. Gate approvals and task status changes remain with the PI.
