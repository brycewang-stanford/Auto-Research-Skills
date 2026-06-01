# Static Discovery Site

`site/` is a dependency-free, build-free browser for `catalog/search-index.json`
and `catalog/collisions.json`. It is plain HTML/CSS/JS — no framework, no bundler
— and renders entirely client-side from the generated catalog.

## Pages

- **`index.html`** — the skill catalog: search, rank, filter, sort, and inspect
  every bundled skill.
- **`collisions.html`** — the name-collision resolver: for skill names that mean
  different things across collections, see what each version actually does.

## Catalog browser features (`index.html`)

- **Ranked search** — multi-term search scored by where each term hits (exact
  name > name prefix > tag > collection > trigger > path), not just substring
  order.
- **Match highlighting** — search terms are highlighted in result names and
  triggers so you can see *why* a skill matched.
- **Filters** — by tag, by collection, and by quality flag (name collision,
  rebundled copy, missing frontmatter, template). Tag and collection dropdowns
  show how many skills each holds, and active filters appear as removable chips.
- **Sort** — best match, name (A–Z), or collection (A–Z).
- **Detail drawer** — click any skill (or press <kbd>Enter</kbd>) for its full
  trigger, tags, flags, license, path, a link to the **upstream source file**,
  and a jump to the rest of that collection.
- **Copy path** and **Source ↗** links on every card; the source link resolves
  against the collection's upstream repository (`repo_url` in the index), since
  files here live behind git submodules.
- **Shareable URLs** — the active query, sort, filters, and flags are mirrored to
  the URL, so any view can be linked or bookmarked.
- **Keyboard** — <kbd>/</kbd> focuses search, <kbd>Esc</kbd> clears it or closes
  the drawer.
- **Light / dark theme** — follows your OS by default; the toggle persists your
  choice. No-JS visitors get a `<noscript>` explanation.

The page degrades gracefully: with no matches it says so, and large result sets
page in 60 at a time via **Load more** rather than rendering thousands of cards
at once.

## Serve locally

Serve the repository root, then open `/site/`:

```bash
make serve-site
```

The default URL is <http://127.0.0.1:8765/site/>. The collision resolver is at
<http://127.0.0.1:8765/site/collisions.html>. Override the port when needed:

```bash
make serve-site SITE_PORT=8787
```

## Validate

```bash
make site-check      # data contract + required element ids + asset links
make site-js-check   # node --check on the page scripts
```

## Regenerate the backing data

After the bundled submodules change, refresh the catalog the site reads:

```bash
make catalog         # rebuilds catalog/skills.json + search-index.json + collisions.json
```

## Deploy

`.github/workflows/pages.yml` publishes this directory to GitHub Pages on every
push to `main` that touches `site/**` or the catalog JSON (or on manual
dispatch). It bundles only `site/*` and the two generated catalog JSON files —
no submodules, no large images — and serves the catalog at the Pages root via a
redirect to `/site/`. Enable it once under **Settings → Pages → Source: GitHub
Actions**.
