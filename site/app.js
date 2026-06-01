/*
 * Discovery browser for the Auto-Research-Skills hub.
 *
 * Loads catalog/search-index.json (produced by tools/build_index.py) and lets
 * you search, rank, filter, sort, and inspect every bundled skill — entirely
 * client-side, no build step. Filter state is mirrored to the URL so any view
 * is shareable, and each skill links back to its upstream source repository.
 *
 * Self-contained on search-index.json; reuses site/styles.css for visuals. All
 * third-party text is rendered with textContent, never innerHTML.
 *
 * Serve from the repo root so ../catalog/... resolves, then open /site/.
 */
(() => {
  "use strict";

  const DATA_URL = "../catalog/search-index.json";
  const PAGE_SIZE = 60;
  const THEME_KEY = "ars-theme";
  const FLAG_KEYS = ["collision", "dup", "no-fm", "template"];
  const FLAG_LABELS = {
    collision: "name collision",
    dup: "rebundled copy",
    "no-fm": "no frontmatter",
    template: "template",
  };
  const numberFmt = new Intl.NumberFormat("en-US");

  const els = {
    summary: document.getElementById("summary"),
    query: document.getElementById("query"),
    sort: document.getElementById("sort"),
    tagFilter: document.getElementById("tagFilter"),
    collectionFilter: document.getElementById("collectionFilter"),
    flagCollision: document.getElementById("flagCollision"),
    flagDup: document.getElementById("flagDup"),
    flagNoFrontmatter: document.getElementById("flagNoFrontmatter"),
    flagTemplate: document.getElementById("flagTemplate"),
    reset: document.getElementById("reset"),
    themeToggle: document.getElementById("themeToggle"),
    collectionCount: document.getElementById("collectionCount"),
    collectionBars: document.getElementById("collectionBars"),
    resultCount: document.getElementById("resultCount"),
    results: document.getElementById("results"),
    status: document.getElementById("status"),
    activeFilters: document.getElementById("activeFilters"),
    loadMore: document.getElementById("loadMore"),
    drawer: document.getElementById("drawer"),
    drawerTitle: document.getElementById("drawerTitle"),
    drawerBody: document.getElementById("drawerBody"),
    drawerClose: document.getElementById("drawerClose"),
  };
  const flagInputs = {
    collision: els.flagCollision,
    dup: els.flagDup,
    "no-fm": els.flagNoFrontmatter,
    template: els.flagTemplate,
  };

  const state = {
    data: null,
    collectionsByName: new Map(),
    query: "",
    sort: "relevance",
    tag: "",
    collection: "",
    flags: { collision: false, dup: false, "no-fm": false, template: false },
    results: [],
    terms: [],
    shown: PAGE_SIZE,
    lastFocus: null,
  };

  const SORT_LABELS = { relevance: "best match", name: "name", collection: "collection" };

  // ---------- helpers ----------

  function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text != null) node.textContent = text;
    return node;
  }

  function externalLink(href, text, className) {
    const a = el("a", className, text);
    a.href = href;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    return a;
  }

  function escapeRegex(value) {
    return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  }

  // Append text to a parent node, wrapping any matched search terms in <mark>.
  // Builds real text nodes / elements — never innerHTML — so it stays XSS-safe.
  function appendHighlighted(parent, text, terms) {
    const value = String(text || "");
    const pattern = terms.map(escapeRegex).filter(Boolean).join("|");
    if (!pattern) {
      parent.appendChild(document.createTextNode(value));
      return;
    }
    const re = new RegExp(`(${pattern})`, "ig");
    let last = 0;
    let match;
    while ((match = re.exec(value)) !== null) {
      if (match.index > last) parent.appendChild(document.createTextNode(value.slice(last, match.index)));
      parent.appendChild(el("mark", null, match[0]));
      last = match.index + match[0].length;
      if (match.index === re.lastIndex) re.lastIndex += 1; // guard against zero-width matches
    }
    if (last < value.length) parent.appendChild(document.createTextNode(value.slice(last)));
  }

  function repoUrlFor(collectionName) {
    const meta = state.collectionsByName.get(collectionName);
    return meta && meta.repo_url ? String(meta.repo_url) : "";
  }

  // Best-effort deep link to the skill's file in its upstream repo. The
  // aggregator stores files behind submodules, so we resolve against the
  // upstream repo_url rather than this repo's blob view.
  function sourceUrlFor(skill) {
    const repo = repoUrlFor(skill.collection).replace(/\.git$/, "").replace(/\/+$/, "");
    if (!repo) return "";
    const prefix = `skills/${skill.collection}/`;
    let sub = skill.path || "";
    if (sub.startsWith(prefix)) sub = sub.slice(prefix.length);
    if (!sub) return repo;
    const encoded = sub.split("/").map(encodeURIComponent).join("/");
    return `${repo}/blob/HEAD/${encoded}`;
  }

  function debounce(fn, ms) {
    let t = null;
    return (...args) => {
      clearTimeout(t);
      t = setTimeout(() => fn(...args), ms);
    };
  }

  // ---------- ranking & filtering ----------

  function termScore(skill, term) {
    const name = skill.name.toLowerCase();
    let best = 0;
    if (name === term) best = 100;
    else if (name.startsWith(term)) best = 70;
    else if (name.includes(term)) best = 50;
    if ((skill.tags || []).some((tag) => tag.toLowerCase().includes(term))) best = Math.max(best, 40);
    if (skill.collection.toLowerCase().includes(term)) best = Math.max(best, 25);
    if ((skill.trigger || "").toLowerCase().includes(term)) best = Math.max(best, 20);
    if ((skill.path || "").toLowerCase().includes(term)) best = Math.max(best, 10);
    return best;
  }

  function passesFilters(skill) {
    if (state.tag && !(skill.tags || []).includes(state.tag)) return false;
    if (state.collection && skill.collection !== state.collection) return false;
    for (const key of FLAG_KEYS) {
      if (state.flags[key] && !(skill.flags || []).includes(key)) return false;
    }
    return true;
  }

  function compareName(a, b) {
    return a.skill.name.localeCompare(b.skill.name) || a.skill.collection.localeCompare(b.skill.collection);
  }

  function computeResults() {
    const terms = state.query.trim().toLowerCase().split(/\s+/).filter(Boolean);
    state.terms = terms;
    const scored = [];
    for (const skill of state.data.skills) {
      if (!passesFilters(skill)) continue;
      let score = 0;
      let matchedAll = true;
      for (const term of terms) {
        const s = termScore(skill, term);
        if (s === 0) {
          matchedAll = false;
          break;
        }
        score += s;
      }
      if (!matchedAll) continue;
      scored.push({ skill, score });
    }

    const sort = state.sort;
    scored.sort((a, b) => {
      if (sort === "name") return compareName(a, b);
      if (sort === "collection") {
        return a.skill.collection.localeCompare(b.skill.collection) || compareName(a, b);
      }
      if (terms.length) {
        const diff = b.score - a.score;
        if (diff) return diff;
      }
      return compareName(a, b);
    });
    return scored.map((entry) => entry.skill);
  }

  // ---------- rendering ----------

  function renderSummary(totals) {
    const metrics = [
      ["skill files", totals.skill_files],
      ["unique", totals.unique_skills],
      ["collections", totals.collections],
      ["rebundled", totals.rebundled],
      ["collisions", totals.name_collisions],
    ];
    els.summary.replaceChildren(
      ...metrics.map(([label, value]) => {
        const cell = el("div");
        cell.append(el("span", "metric", numberFmt.format(value || 0)), el("span", "label", label));
        return cell;
      }),
    );
  }

  function populateSelect(select, values, allLabel, counts) {
    select.replaceChildren();
    select.append(new Option(allLabel, ""));
    for (const value of values) {
      const count = counts ? counts.get(value) : null;
      const label = count != null ? `${value} (${numberFmt.format(count)})` : value;
      select.append(new Option(label, value));
    }
  }

  function renderBars(collections) {
    const sorted = [...collections].sort((a, b) => b.skill_files - a.skill_files).slice(0, 12);
    const max = sorted[0] ? sorted[0].skill_files : 1;
    els.collectionCount.textContent = `${collections.length} collections`;
    const frag = document.createDocumentFragment();
    for (const collection of sorted) {
      const width = Math.max(3, (collection.skill_files / max) * 100);
      const row = el("div", "bar-row");
      const name = el("button", "bar-name", collection.name);
      name.type = "button";
      name.title = `Filter to ${collection.name}`;
      name.addEventListener("click", () => {
        state.collection = collection.name;
        els.collectionFilter.value = collection.name;
        onFiltersChanged();
      });
      const track = el("span", "bar-track");
      const fill = el("span", "bar-fill");
      fill.style.width = `${width}%`;
      track.appendChild(fill);
      row.append(name, track, el("span", "bar-value", numberFmt.format(collection.skill_files)));
      frag.appendChild(row);
    }
    els.collectionBars.replaceChildren(frag);
  }

  function chip(text, className) {
    return el("span", className ? `chip ${className}` : "chip", text);
  }

  function skillCard(skill) {
    const card = el("article", "skill-card");
    card.tabIndex = 0;
    card.setAttribute("role", "button");
    card.setAttribute("aria-label", `Open details for ${skill.name}`);

    const topline = el("div", "skill-topline");
    const nameEl = el("h3", "skill-name");
    appendHighlighted(nameEl, skill.name, state.terms);
    topline.append(nameEl);
    const collectionBtn = el("button", "collection collection-btn", skill.collection);
    collectionBtn.type = "button";
    collectionBtn.title = `Filter to ${skill.collection}`;
    collectionBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      state.collection = skill.collection;
      els.collectionFilter.value = skill.collection;
      onFiltersChanged();
    });
    topline.append(collectionBtn);
    card.append(topline);

    const triggerEl = el("p", "trigger");
    appendHighlighted(triggerEl, skill.trigger || "—", state.terms);
    card.append(triggerEl);

    const chips = el("div", "chips");
    for (const flag of skill.flags || []) chips.append(chip(FLAG_LABELS[flag] || flag, "flag"));
    for (const tag of skill.tags || []) chips.append(chip(tag));
    if (skill.license) chips.append(chip(skill.license, "license"));
    if (chips.childNodes.length) card.append(chips);

    card.append(el("code", "path", skill.path));

    const actions = el("div", "card-actions");
    const source = sourceUrlFor(skill);
    if (source) {
      const link = externalLink(source, "Source ↗", "action");
      link.addEventListener("click", (event) => event.stopPropagation());
      actions.append(link);
    }
    const copyBtn = el("button", "action", "Copy path");
    copyBtn.type = "button";
    copyBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      copyText(skill.path, copyBtn, "Copy path");
    });
    actions.append(copyBtn);
    const detailsBtn = el("button", "action ghost", "Details");
    detailsBtn.type = "button";
    detailsBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      openDrawer(skill);
    });
    actions.append(detailsBtn);
    card.append(actions);

    const open = () => openDrawer(skill);
    card.addEventListener("click", open);
    card.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        open();
      }
    });
    return card;
  }

  function renderResults() {
    const total = state.results.length;
    els.resultCount.textContent = total
      ? `${numberFmt.format(total)} match${total === 1 ? "" : "es"}`
      : "0 matches";

    if (!total) {
      els.status.classList.remove("hidden");
      els.status.textContent = "No skills match the current filters.";
      els.results.replaceChildren();
      els.loadMore.classList.add("hidden");
      return;
    }

    els.status.classList.add("hidden");
    const visible = state.results.slice(0, state.shown);
    const frag = document.createDocumentFragment();
    for (const skill of visible) frag.appendChild(skillCard(skill));
    els.results.replaceChildren(frag);

    if (state.shown < total) {
      els.loadMore.classList.remove("hidden");
      els.loadMore.textContent = `Load more (${numberFmt.format(total - state.shown)} hidden)`;
    } else {
      els.loadMore.classList.add("hidden");
    }
  }

  // ---------- detail drawer ----------

  function metaRow(label, valueNode) {
    const row = el("div", "meta-row");
    row.append(el("span", "meta-label", label));
    const value = el("div", "meta-value");
    value.append(valueNode);
    row.append(value);
    return row;
  }

  function openDrawer(skill) {
    state.lastFocus = document.activeElement;
    els.drawerTitle.textContent = skill.name;

    const body = document.createDocumentFragment();

    const repo = repoUrlFor(skill.collection);
    const collectionNode = repo
      ? externalLink(repo, `${skill.collection} ↗`)
      : el("span", null, skill.collection);
    body.append(metaRow("Collection", collectionNode));

    body.append(metaRow("Trigger", el("p", "drawer-trigger", skill.trigger || "—")));

    if ((skill.tags || []).length) {
      const tags = el("div", "chips");
      for (const tag of skill.tags) tags.append(chip(tag));
      body.append(metaRow("Tags", tags));
    }

    if ((skill.flags || []).length) {
      const flags = el("div", "chips");
      for (const flag of skill.flags) flags.append(chip(FLAG_LABELS[flag] || flag, "flag"));
      body.append(metaRow("Flags", flags));
    }

    if (skill.license) body.append(metaRow("License", el("span", null, skill.license)));

    const pathWrap = el("div", "path-wrap");
    pathWrap.append(el("code", "path", skill.path));
    const copyBtn = el("button", "action", "Copy");
    copyBtn.type = "button";
    copyBtn.addEventListener("click", () => copyText(skill.path, copyBtn, "Copy"));
    pathWrap.append(copyBtn);
    body.append(metaRow("Path", pathWrap));

    const links = el("div", "drawer-links");
    const source = sourceUrlFor(skill);
    if (source) links.append(externalLink(source, "View source file ↗", "action"));
    const sameCollection = state.data.skills.filter((s) => s.collection === skill.collection).length;
    if (sameCollection > 1) {
      const btn = el("button", "action ghost", `${numberFmt.format(sameCollection)} skills in this collection`);
      btn.type = "button";
      btn.addEventListener("click", () => {
        state.collection = skill.collection;
        els.collectionFilter.value = skill.collection;
        closeDrawer();
        onFiltersChanged();
      });
      links.append(btn);
    }
    if ((skill.flags || []).includes("collision")) {
      links.append(externalLink(`collisions.html?q=${encodeURIComponent(skill.name)}`, "Compare colliding versions →", "action"));
    }
    body.append(links);

    els.drawerBody.replaceChildren(body);
    els.drawer.classList.add("open");
    els.drawer.setAttribute("aria-hidden", "false");
    document.body.classList.add("drawer-open");
    els.drawerClose.focus();
  }

  function closeDrawer() {
    if (!els.drawer.classList.contains("open")) return;
    els.drawer.classList.remove("open");
    els.drawer.setAttribute("aria-hidden", "true");
    document.body.classList.remove("drawer-open");
    if (state.lastFocus && typeof state.lastFocus.focus === "function") state.lastFocus.focus();
  }

  async function copyText(text, button, original) {
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = "Copied!";
      button.classList.add("copied");
    } catch {
      button.textContent = "Copy failed";
    }
    setTimeout(() => {
      button.textContent = original;
      button.classList.remove("copied");
    }, 1400);
  }

  // ---------- URL state ----------

  function readStateFromUrl() {
    const params = new URLSearchParams(window.location.search);
    state.query = params.get("q") || "";
    const sort = params.get("sort");
    if (sort === "name" || sort === "collection" || sort === "relevance") state.sort = sort;
    state.tag = params.get("tag") || "";
    state.collection = params.get("collection") || "";
    const flags = new Set((params.get("flags") || "").split(",").filter(Boolean));
    for (const key of FLAG_KEYS) state.flags[key] = flags.has(key);
  }

  function writeStateToUrl() {
    const params = new URLSearchParams();
    if (state.query.trim()) params.set("q", state.query.trim());
    if (state.sort !== "relevance") params.set("sort", state.sort);
    if (state.tag) params.set("tag", state.tag);
    if (state.collection) params.set("collection", state.collection);
    const flags = FLAG_KEYS.filter((key) => state.flags[key]);
    if (flags.length) params.set("flags", flags.join(","));
    const query = params.toString();
    const url = query ? `${window.location.pathname}?${query}` : window.location.pathname;
    window.history.replaceState(null, "", url);
  }

  function syncControlsFromState() {
    els.query.value = state.query;
    els.sort.value = state.sort;
    els.tagFilter.value = state.tag;
    els.collectionFilter.value = state.collection;
    for (const key of FLAG_KEYS) flagInputs[key].checked = state.flags[key];
  }

  // ---------- orchestration ----------

  function sortLabel(value) {
    return SORT_LABELS[value] || value;
  }

  function resetFilters() {
    state.query = "";
    state.sort = "relevance";
    state.tag = "";
    state.collection = "";
    for (const key of FLAG_KEYS) state.flags[key] = false;
    syncControlsFromState();
    onFiltersChanged();
  }

  // A removable chip per active filter, plus a clear-all when several apply.
  function renderActiveFilters() {
    const chips = [];
    if (state.query.trim()) chips.push([`search: ${state.query.trim()}`, () => { state.query = ""; els.query.value = ""; }]);
    if (state.tag) chips.push([`tag: ${state.tag}`, () => { state.tag = ""; els.tagFilter.value = ""; }]);
    if (state.collection) chips.push([`collection: ${state.collection}`, () => { state.collection = ""; els.collectionFilter.value = ""; }]);
    for (const key of FLAG_KEYS) {
      if (state.flags[key]) chips.push([`flag: ${FLAG_LABELS[key]}`, () => { state.flags[key] = false; flagInputs[key].checked = false; }]);
    }
    if (state.sort !== "relevance") chips.push([`sort: ${sortLabel(state.sort)}`, () => { state.sort = "relevance"; els.sort.value = "relevance"; }]);

    els.activeFilters.replaceChildren();
    if (!chips.length) {
      els.activeFilters.classList.add("hidden");
      return;
    }
    els.activeFilters.classList.remove("hidden");
    for (const [label, clear] of chips) {
      const chip = el("button", "filter-chip");
      chip.type = "button";
      chip.title = "Remove this filter";
      chip.append(el("span", null, label), el("span", "filter-chip-x", "✕"));
      chip.addEventListener("click", () => {
        clear();
        onFiltersChanged();
      });
      els.activeFilters.appendChild(chip);
    }
    if (chips.length > 1) {
      const clearAll = el("button", "filter-chip clear-all", "Clear all");
      clearAll.type = "button";
      clearAll.addEventListener("click", resetFilters);
      els.activeFilters.appendChild(clearAll);
    }
  }

  function apply() {
    state.results = computeResults();
    renderResults();
    renderActiveFilters();
    writeStateToUrl();
  }

  function onFiltersChanged() {
    state.shown = PAGE_SIZE;
    apply();
  }

  const onQueryInput = debounce(() => {
    state.query = els.query.value;
    onFiltersChanged();
  }, 110);

  function attachEvents() {
    els.query.addEventListener("input", onQueryInput);
    els.sort.addEventListener("change", () => {
      state.sort = els.sort.value;
      onFiltersChanged();
    });
    els.tagFilter.addEventListener("change", () => {
      state.tag = els.tagFilter.value;
      onFiltersChanged();
    });
    els.collectionFilter.addEventListener("change", () => {
      state.collection = els.collectionFilter.value;
      onFiltersChanged();
    });
    for (const key of FLAG_KEYS) {
      flagInputs[key].addEventListener("change", () => {
        state.flags[key] = flagInputs[key].checked;
        onFiltersChanged();
      });
    }
    els.reset.addEventListener("click", resetFilters);
    els.loadMore.addEventListener("click", () => {
      state.shown += PAGE_SIZE;
      renderResults();
    });
    els.themeToggle.addEventListener("click", toggleTheme);

    for (const node of els.drawer.querySelectorAll("[data-drawer-close]")) {
      node.addEventListener("click", closeDrawer);
    }
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape") {
        if (els.drawer.classList.contains("open")) {
          closeDrawer();
        } else if (document.activeElement === els.query && els.query.value) {
          els.query.value = "";
          state.query = "";
          onFiltersChanged();
        }
        return;
      }
      if (event.key === "Tab" && els.drawer.classList.contains("open")) {
        const focusables = Array.from(els.drawer.querySelectorAll('a[href], button:not([disabled])'));
        if (focusables.length) {
          const first = focusables[0];
          const last = focusables[focusables.length - 1];
          if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
          } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
          }
        }
        return;
      }
      if (event.key === "/" && !isTypingTarget(event.target)) {
        event.preventDefault();
        els.query.focus();
        els.query.select();
      }
    });
  }

  function isTypingTarget(target) {
    if (!target) return false;
    const tag = (target.tagName || "").toLowerCase();
    return tag === "input" || tag === "textarea" || tag === "select" || target.isContentEditable;
  }

  // ---------- theme ----------

  function storedTheme() {
    try {
      return localStorage.getItem(THEME_KEY);
    } catch {
      return null;
    }
  }

  function systemPrefersDark() {
    return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  }

  function applyTheme() {
    const stored = storedTheme();
    if (stored === "dark" || stored === "light") {
      document.documentElement.setAttribute("data-theme", stored);
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
    const dark = stored ? stored === "dark" : systemPrefersDark();
    els.themeToggle.setAttribute("aria-pressed", String(dark));
    const label = els.themeToggle.querySelector(".theme-label");
    if (label) label.textContent = dark ? "Light" : "Dark";
  }

  function toggleTheme() {
    const dark = (storedTheme() ? storedTheme() === "dark" : systemPrefersDark());
    try {
      localStorage.setItem(THEME_KEY, dark ? "light" : "dark");
    } catch {
      /* ignore storage failures (private mode) */
    }
    applyTheme();
  }

  // ---------- init ----------

  async function init() {
    applyTheme();
    readStateFromUrl();
    attachEvents();
    try {
      const response = await fetch(DATA_URL, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      state.data = await response.json();
      state.collectionsByName = new Map((state.data.collections || []).map((c) => [c.name, c]));
      const tagCounts = new Map();
      const collectionCounts = new Map();
      for (const skill of state.data.skills || []) {
        for (const tag of skill.tags || []) tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
        collectionCounts.set(skill.collection, (collectionCounts.get(skill.collection) || 0) + 1);
      }
      renderSummary(state.data.totals || {});
      populateSelect(els.tagFilter, state.data.tags || [], "All tags", tagCounts);
      populateSelect(
        els.collectionFilter,
        (state.data.collections || []).map((c) => c.name).sort(),
        "All collections",
        collectionCounts,
      );
      renderBars(state.data.collections || []);
      syncControlsFromState();
      apply();
    } catch (error) {
      els.status.classList.remove("hidden");
      els.status.textContent = `Could not load ${DATA_URL}. Run \`make serve-site\` from the repository root, then open /site/. (${error.message})`;
      els.resultCount.textContent = "Not loaded";
    }
  }

  init();
})();
