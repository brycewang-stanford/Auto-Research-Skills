/*
 * Name-collision resolver for the Auto-Research-Skills hub.
 *
 * Loads catalog/collisions.json (produced by tools/build_index.py) and renders,
 * for every skill name that means different things across collections, what
 * each collection's version actually does — so a user can choose deliberately
 * instead of letting an undefined by-name resolution pick for them.
 *
 * Self-contained on collisions.json; reuses site/styles.css for visuals. All
 * third-party text is rendered with textContent, never innerHTML.
 *
 * Serve from the repo root so ../catalog/... resolves, then open /site/collisions.html.
 */
(() => {
  "use strict";

  const DATA_URL = "../catalog/collisions.json";
  const RENDER_CAP = 120;

  const els = {
    summary: document.getElementById("summary"),
    query: document.getElementById("query"),
    resultCount: document.getElementById("resultCount"),
    status: document.getElementById("status"),
    results: document.getElementById("results"),
  };
  const fmt = new Intl.NumberFormat("en-US");

  let groups = [];

  fetch(DATA_URL)
    .then((res) => {
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
    .then(init)
    .catch((err) => {
      els.status.classList.remove("hidden");
      els.status.textContent =
        `Could not load ${DATA_URL} — ${err.message}. Serve the repo root ` +
        "(e.g. python3 -m http.server) and open /site/collisions.html. " +
        "Run `python3 tools/build_index.py` if the file is missing.";
      els.resultCount.textContent = "—";
    });

  function init(data) {
    // Already sorted by build_index.py: most ambiguous (most collections) first.
    groups = Array.isArray(data.collisions) ? data.collisions : [];
    renderSummary(data);
    els.status.classList.add("hidden");
    els.query.addEventListener("input", debounce(apply, 110));
    apply();
  }

  function renderSummary(data) {
    const collectionsInvolved = new Set();
    let totalVariants = 0;
    let mostAmbiguous = 0;
    for (const g of groups) {
      totalVariants += g.variants.length;
      if (g.collections > mostAmbiguous) mostAmbiguous = g.collections;
      for (const v of g.variants) collectionsInvolved.add(v.collection);
    }
    const metrics = els.summary.querySelectorAll(".metric");
    const values = [
      data.count != null ? data.count : groups.length,
      collectionsInvolved.size,
      mostAmbiguous,
      totalVariants,
    ];
    metrics.forEach((m, i) => (m.textContent = fmt.format(values[i])));
  }

  function apply() {
    const q = els.query.value.trim().toLowerCase();
    const matched = q ? groups.filter((g) => g.name.toLowerCase().includes(q)) : groups;

    els.resultCount.textContent =
      matched.length > RENDER_CAP
        ? `showing ${RENDER_CAP} of ${fmt.format(matched.length)} — refine to narrow`
        : `${fmt.format(matched.length)} name${matched.length === 1 ? "" : "s"}`;

    const frag = document.createDocumentFragment();
    for (const g of matched.slice(0, RENDER_CAP)) frag.appendChild(card(g));
    els.results.replaceChildren(frag);

    if (matched.length === 0) {
      els.status.classList.remove("hidden");
      els.status.textContent = "No colliding names match that filter.";
    } else {
      els.status.classList.add("hidden");
    }
  }

  function card(g) {
    const wrap = document.createElement("article");
    wrap.className = "collision-card";

    const head = document.createElement("div");
    head.className = "collision-head";
    const name = document.createElement("h3");
    name.className = "collision-name";
    name.textContent = g.name;
    const badge = document.createElement("span");
    badge.className = "badge";
    const meanings = g.distinct_bodies != null ? g.distinct_bodies : g.variants.length;
    badge.textContent = `${g.collections} collections · ${meanings} distinct meanings`;
    head.append(name, badge);
    wrap.appendChild(head);

    for (const v of g.variants) wrap.appendChild(variant(v));
    return wrap;
  }

  function variant(v) {
    const row = document.createElement("div");
    row.className = "variant";

    const headCol = document.createElement("div");
    headCol.className = "variant-head";
    const collection = document.createElement(v.repo_url ? "a" : "span");
    collection.className = "collection";
    collection.textContent = v.collection;
    if (v.repo_url) {
      collection.href = v.repo_url;
      collection.target = "_blank";
      collection.rel = "noopener noreferrer";
      collection.title = `Source: ${v.repo_url}`;
    }
    headCol.appendChild(collection);
    if (v.bodies_in_collection > 1) {
      const note = document.createElement("span");
      note.className = "muted";
      note.textContent = `${v.bodies_in_collection} variants here`;
      headCol.appendChild(note);
    }

    const body = document.createElement("div");
    const trigger = document.createElement("div");
    trigger.className = "variant-trigger";
    trigger.textContent = v.trigger || "—";
    const path = document.createElement("code");
    path.className = "path";
    path.textContent = v.path;
    body.append(trigger, path);

    row.append(headCol, body);
    return row;
  }

  function debounce(fn, ms) {
    let t = null;
    return (...a) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...a), ms);
    };
  }
})();
