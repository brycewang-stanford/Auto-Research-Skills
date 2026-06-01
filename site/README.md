# Static Discovery Site

`site/` is a dependency-free browser for `catalog/search-index.json` and
`catalog/collisions.json`.

Serve the repository root, then open `/site/`:

```bash
make serve-site
```

The default URL is <http://127.0.0.1:8765/site/>. The name-collision resolver is
available at <http://127.0.0.1:8765/site/collisions.html>.

Override the port when needed:

```bash
make serve-site SITE_PORT=8787
```

Validate the site contract with:

```bash
make site-check
make site-js-check
```

Regenerate the backing data after submodules change:

```bash
make catalog
```
