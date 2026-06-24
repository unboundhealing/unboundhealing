#!/bin/bash
set -euo pipefail

echo "🚀 Generating UNIFIED semantic-salience system (v3 SINGLE SOURCE)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

# ---------------------------------------------------------
# STEP 1 — REGISTRY (STRUCTURAL INPUT LAYER)
# ---------------------------------------------------------

echo "🧭 Building registry..."
./scripts/build-content-registry.sh

# ---------------------------------------------------------
# STEP 2 — TRUTH LAYER (ONLY AUTHORITATIVE SOURCE)
# ---------------------------------------------------------

echo "🌌 Building semantic truth layer (PRIMARY ARTIFACT)..."
python3 scripts/build-semantic-salience.py

# HARD GUARANTEE: semantic-salience MUST exist
if [ ! -f "semantic-salience.json" ]; then
  echo "❌ semantic-salience.json missing — HARD STOP"
  exit 1
fi

# ---------------------------------------------------------
# STEP 2.5 — SYSTEM INTROSPECTION (NON-BLOCKING)
# ---------------------------------------------------------
echo "🧭 Dependency collapse analysis (optional)"
python3 scripts/build-dependency-collapse-map.py || true

# ---------------------------------------------------------
# STEP 3 — DERIVATIVE LAYERS (TRUTH CONSUMERS ONLY)
# ---------------------------------------------------------

echo "🏠 Homepage intelligence (derivative)"
python3 scripts/build-homepage-intelligence.py || true

# ---------------------------------------------------------
# STEP 4 — PRESENTATION / RENDER LAYER
# ---------------------------------------------------------

echo "🧠 Enhancing pages (optional)"
python3 scripts/enhance-pages.py || true

echo "📡 RSS (optional)"
./scripts/generate-rss.sh || true

echo "🗺 Sitemap (optional)"
./scripts/build-sitemap.sh || true

echo "🏷 Tags (optional)"
./scripts/build-tags.sh || true

echo "🔎 Search index (optional)"
./scripts/build-search-index.sh || true

# ---------------------------------------------------------
# FINAL STATE DECLARATION
# ---------------------------------------------------------

echo "🧭 FINAL STATE: semantic-salience is the ONLY truth layer"
