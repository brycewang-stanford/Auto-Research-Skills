# 📚 catalog/ — skill discovery layer

This hub bundles dozens of upstream collections as git submodules. Together
they ship **3,250 `SKILL.md` files (≈2,534 unique)** — but until now there was
no way to browse or search an *individual* skill without grepping every
submodule. This directory fixes that.

Everything except the two hand-written dossiers is **generated** by
[`../tools/build_catalog.py`](../tools/build_catalog.py) and reads only
`.gitmodules` + the working tree (fully offline).

## What's here

| File | Generated? | Purpose |
|---|---|---|
| [`CATALOG.md`](CATALOG.md) | ✅ | Human entry point: at-a-glance stats, per-collection index, and the most re-bundled skills. |
| [`collections/`](collections/) | ✅ | One page per collection — every skill with its trigger, flags, and a link to the source `SKILL.md`. |
| [`skills.json`](skills.json) | ✅ | Full machine-readable manifest (name, description, collection, repo URL, license, dedup info) for every skill. |
| [`skills.csv`](skills.csv) | ✅ | The same data, flat — grep it or open it in a spreadsheet. |
| [`QUALITY.md`](QUALITY.md) | ✍️ | Redundancy, name-collision, and frontmatter findings + suggestions for maintainers. |
| [`DISCOVERY.md`](DISCOVERY.md) | ✍️ | Vetted candidate skills **not yet bundled**, with live signals and ready-to-run vendoring commands. |

## Regenerate

Run after submodules are added, removed, or updated:

```bash
python tools/build_catalog.py          # writes skills.json, skills.csv, CATALOG.md, collections/*.md
python tools/build_catalog.py --check  # parse-and-count only, writes nothing (good for CI)
```

No third-party dependencies — standard-library Python 3.9+.

## Find a skill

```bash
# "Which collections have a Zotero / DiD / survey skill?"
grep -i zotero catalog/skills.csv
python3 -c "import json;[print(s['collection'],s['name']) for s in json.load(open('catalog/skills.json'))['skills'] if 'did' in s['name'].lower()]"
```

> The catalog is a **read** layer. It never modifies submodules, `.gitmodules`,
> the READMEs, or `STARS.md`. To add a new collection, follow
> [`../CURATION.md`](../CURATION.md); candidates worth vendoring are queued in
> [`DISCOVERY.md`](DISCOVERY.md).
