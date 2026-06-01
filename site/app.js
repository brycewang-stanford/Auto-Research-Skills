(function () {
  const state = {
    data: null,
    query: "",
    tag: "",
    collection: "",
    flags: {
      collision: false,
      "no-fm": false,
      template: false,
    },
  };

  const els = {
    summary: document.getElementById("summary"),
    query: document.getElementById("query"),
    tagFilter: document.getElementById("tagFilter"),
    collectionFilter: document.getElementById("collectionFilter"),
    flagCollision: document.getElementById("flagCollision"),
    flagNoFrontmatter: document.getElementById("flagNoFrontmatter"),
    flagTemplate: document.getElementById("flagTemplate"),
    reset: document.getElementById("reset"),
    collectionCount: document.getElementById("collectionCount"),
    collectionBars: document.getElementById("collectionBars"),
    resultCount: document.getElementById("resultCount"),
    results: document.getElementById("results"),
    status: document.getElementById("status"),
  };

  const numberFmt = new Intl.NumberFormat("en-US");

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function renderSummary(totals) {
    els.summary.innerHTML = [
      ["skill files", totals.skill_files],
      ["unique", totals.unique_skills],
      ["collections", totals.collections],
      ["collisions", totals.name_collisions],
    ]
      .map(
        ([label, value]) => `
          <div>
            <span class="metric">${numberFmt.format(value || 0)}</span>
            <span class="label">${label}</span>
          </div>
        `,
      )
      .join("");
  }

  function populateSelect(select, values, allLabel) {
    select.innerHTML = `<option value="">${allLabel}</option>`;
    for (const value of values) {
      const option = document.createElement("option");
      option.value = value;
      option.textContent = value;
      select.appendChild(option);
    }
  }

  function renderBars(collections) {
    const sorted = [...collections].sort((a, b) => b.skill_files - a.skill_files).slice(0, 12);
    const max = sorted[0] ? sorted[0].skill_files : 1;
    els.collectionCount.textContent = `${collections.length} collections`;
    els.collectionBars.innerHTML = sorted
      .map((collection) => {
        const width = Math.max(3, (collection.skill_files / max) * 100);
        return `
          <div class="bar-row" title="${escapeHtml(collection.name)}">
            <span class="bar-name">${escapeHtml(collection.name)}</span>
            <span class="bar-track"><span class="bar-fill" style="width:${width}%"></span></span>
            <span class="bar-value">${numberFmt.format(collection.skill_files)}</span>
          </div>
        `;
      })
      .join("");
  }

  function matchesQuery(skill, query) {
    if (!query) {
      return true;
    }
    const haystack = [
      skill.name,
      skill.collection,
      skill.trigger,
      skill.path,
      ...(skill.tags || []),
      ...(skill.flags || []),
    ]
      .join(" ")
      .toLowerCase();
    return query
      .split(/\s+/)
      .filter(Boolean)
      .every((term) => haystack.includes(term));
  }

  function filteredSkills() {
    const query = state.query.trim().toLowerCase();
    return state.data.skills.filter((skill) => {
      if (!matchesQuery(skill, query)) {
        return false;
      }
      if (state.tag && !(skill.tags || []).includes(state.tag)) {
        return false;
      }
      if (state.collection && skill.collection !== state.collection) {
        return false;
      }
      return Object.entries(state.flags).every(
        ([flag, enabled]) => !enabled || (skill.flags || []).includes(flag),
      );
    });
  }

  function renderResults() {
    const skills = filteredSkills();
    els.resultCount.textContent = `${numberFmt.format(skills.length)} matches`;
    if (!skills.length) {
      els.status.classList.remove("hidden");
      els.status.textContent = "No skills match the current filters.";
      els.results.innerHTML = "";
      return;
    }

    els.status.classList.add("hidden");
    els.results.innerHTML = skills.slice(0, 80).map(renderSkill).join("");
    if (skills.length > 80) {
      els.status.classList.remove("hidden");
      els.status.textContent = `Showing the first 80 of ${numberFmt.format(skills.length)} matches. Refine the filters to narrow the set.`;
    }
  }

  function renderSkill(skill) {
    const flags = (skill.flags || [])
      .map((flag) => `<span class="chip flag">${escapeHtml(flag)}</span>`)
      .join("");
    const tags = (skill.tags || [])
      .map((tag) => `<span class="chip">${escapeHtml(tag)}</span>`)
      .join("");
    const license = skill.license ? `<span class="chip">${escapeHtml(skill.license)}</span>` : "";

    return `
      <article class="skill-card">
        <div class="skill-topline">
          <h3 class="skill-name">${escapeHtml(skill.name)}</h3>
          <span class="collection">${escapeHtml(skill.collection)}</span>
        </div>
        <p class="trigger">${escapeHtml(skill.trigger)}</p>
        <div class="chips">${flags}${tags}${license}</div>
        <code class="path">${escapeHtml(skill.path)}</code>
      </article>
    `;
  }

  function attachEvents() {
    els.query.addEventListener("input", () => {
      state.query = els.query.value;
      renderResults();
    });
    els.tagFilter.addEventListener("change", () => {
      state.tag = els.tagFilter.value;
      renderResults();
    });
    els.collectionFilter.addEventListener("change", () => {
      state.collection = els.collectionFilter.value;
      renderResults();
    });
    els.flagCollision.addEventListener("change", () => {
      state.flags.collision = els.flagCollision.checked;
      renderResults();
    });
    els.flagNoFrontmatter.addEventListener("change", () => {
      state.flags["no-fm"] = els.flagNoFrontmatter.checked;
      renderResults();
    });
    els.flagTemplate.addEventListener("change", () => {
      state.flags.template = els.flagTemplate.checked;
      renderResults();
    });
    els.reset.addEventListener("click", () => {
      state.query = "";
      state.tag = "";
      state.collection = "";
      state.flags.collision = false;
      state.flags["no-fm"] = false;
      state.flags.template = false;
      els.query.value = "";
      els.tagFilter.value = "";
      els.collectionFilter.value = "";
      els.flagCollision.checked = false;
      els.flagNoFrontmatter.checked = false;
      els.flagTemplate.checked = false;
      renderResults();
    });
  }

  async function init() {
    attachEvents();
    try {
      const response = await fetch("../catalog/search-index.json", { cache: "no-store" });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      state.data = await response.json();
      renderSummary(state.data.totals || {});
      populateSelect(els.tagFilter, state.data.tags || [], "All tags");
      populateSelect(
        els.collectionFilter,
        (state.data.collections || []).map((collection) => collection.name).sort(),
        "All collections",
      );
      renderBars(state.data.collections || []);
      renderResults();
    } catch (error) {
      els.status.textContent = `Could not load ../catalog/search-index.json. Run make serve-site from the repository root, then open /site/. ${error.message}`;
      els.resultCount.textContent = "Not loaded";
    }
  }

  init();
})();
