/* =========================================================
   SITE SEARCH (v1)
   Lightweight live search over search-index.json
   ========================================================= */

let SEARCH_INDEX = {};

/* -----------------------------------------
   LOAD INDEX
----------------------------------------- */

async function loadSearchIndex() {
  try {
    const res = await fetch('/assets/search-index.json');
    SEARCH_INDEX = await res.json();
    console.log("🔎 search index loaded:", Object.keys(SEARCH_INDEX).length);
  } catch (err) {
    console.error("❌ failed to load search index", err);
  }
}

/* -----------------------------------------
   NORMALIZE QUERY
----------------------------------------- */

function normalize(str) {
  return (str || "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s]/g, " ");
}

/* -----------------------------------------
   SCORE FUNCTION (v1 simple lexical)
----------------------------------------- */

function scoreEntry(query, entry) {
  const q = normalize(query);

  const haystack = normalize([
    entry.title,
    entry.description,
    entry.tags
  ].join(" "));

  if (!q || !haystack) return 0;

  let score = 0;

  const qTokens = q.split(/\s+/);

  for (const token of qTokens) {
    if (!token) continue;

    if (haystack.includes(token)) {
      score += 2;
    }
  }

  // bonus: title match
  if (normalize(entry.title).includes(q)) {
    score += 5;
  }

  return score;
}

/* -----------------------------------------
   SEARCH ENGINE
----------------------------------------- */

function searchSite(query) {
  const results = [];

  for (const url in SEARCH_INDEX) {
    const entry = SEARCH_INDEX[url];

    const score = scoreEntry(query, entry);

    if (score > 0) {
      results.push({
        ...entry,
        score
      });
    }
  }

  return results
    .sort((a, b) => b.score - a.score)
    .slice(0, 10);
}

/* -----------------------------------------
   RENDER RESULTS
----------------------------------------- */

function renderResults(results) {
  const container = document.getElementById("search-results");

  if (!container) return;

  if (!results.length) {
    container.innerHTML = "";
    return;
  }

  container.innerHTML = results.map(r => `
    <div class="search-result">
      <a href="${r.url}">
        <strong>${r.title || "(untitled)"}</strong>
      </a>
      <div style="font-size: 0.8rem; opacity: 0.7;">
        ${r.description || ""}
      </div>
    </div>
  `).join("");
}

/* -----------------------------------------
   INPUT HANDLER
----------------------------------------- */

function attachSearchInput() {
  const input = document.getElementById("site-search");

  if (!input) return;

  input.addEventListener("input", (e) => {
    const query = e.target.value;

    const results = searchSite(query);

    renderResults(results);
  });
}

/* -----------------------------------------
   INIT
----------------------------------------- */

document.addEventListener("DOMContentLoaded", async () => {
  await loadSearchIndex();
  attachSearchInput();
});
