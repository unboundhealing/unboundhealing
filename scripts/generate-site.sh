#!/bin/bash
set -euo pipefail

echo "🚀 Generating UNIFIED semantic-salience system (v3 SINGLE SOURCE)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

# ---------------------------------------------------------
# STEP 1 — TRUTH LAYER (ONLY AUTHORITATIVE SOURCE)
# ---------------------------------------------------------

echo "🌌 Building semantic truth layer (PRIMARY ARTIFACT)..."
python3 scripts/build-semantic-salience.py

echo ""
echo "===== SALIENCE DEBUG ====="
python3 - <<'PY'
import json

with open("semantic-salience.json","r",encoding="utf-8") as f:
    data = json.load(f)

print()
print("===== SALIENCE STRUCTURE =====")
print(data.keys())

if "page_graph" in data:
    print()
    print("PAGE_GRAPH TYPE:")
    print(type(data["page_graph"]))

    if isinstance(data["page_graph"], dict):
        first_key = next(iter(data["page_graph"]))
        print()
        print("FIRST PAGE_GRAPH KEY:")
        print(first_key)

        print()
        print("FIRST PAGE_GRAPH VALUE:")
        print(data["page_graph"][first_key])

print("==============================")
print()

print("TOP LEVEL KEYS:")
print(list(data.keys()))

pages = data.get("pages")

if isinstance(pages, dict):
    print()
    print("PAGE COUNT:", len(pages))

    first_url = next(iter(pages))
    print()
    print("FIRST URL:")
    print(first_url)

    print()
    print("FIRST NODE:")
    print(json.dumps(pages[first_url], indent=2)[:3000])
else:
    print()
    print("NO 'pages' DICT FOUND")
PY
echo "=========================="
echo ""

# HARD GUARANTEE: semantic-salience MUST exist
if [ ! -f "semantic-salience.json" ]; then
  echo "❌ semantic-salience.json missing — HARD STOP"
  exit 1
fi

# ---------------------------------------------------------
# STEP 1.5 — SYSTEM INTROSPECTION (NON-BLOCKING)
# ---------------------------------------------------------
echo "🧭 Dependency collapse analysis (optional)"
python3 scripts/build-dependency-collapse-map.py || true

# ---------------------------------------------------------
# STEP 2 — DERIVATIVE LAYERS (TRUTH CONSUMERS ONLY)
# ---------------------------------------------------------

echo "🏠 Homepage intelligence (derivative)"
python3 scripts/build-homepage-intelligence.py || true

# ---------------------------------------------------------
# STEP 3 — PRESENTATION / RENDER LAYER
# ---------------------------------------------------------

echo "🧠 Enhancing pages (optional)"
python3 scripts/enhance-pages.py

echo "🔗 building related content..."
python3 scripts/build-related-content.py

echo "🧩 injecting content into pages..."
python3 scripts/inject-content.py

echo "📡 RSS (optional)"
./scripts/generate-rss.sh || true

echo "🗺 Sitemap (optional)"
./scripts/build-sitemap.sh || true

echo "🔎 Search index (optional)"
./scripts/build-search-index.sh || true

# ---------------------------------------------------------
# FINAL STATE DECLARATION
# ---------------------------------------------------------

echo "🧭 FINAL STATE: semantic-salience is the ONLY truth layer"
echo "🧱 legacy semantic graph systems are archived / disabled"
