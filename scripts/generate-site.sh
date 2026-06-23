#!/bin/bash
set -euo pipefail

echo "🚀 Generating UNIFIED semantic-salience system (v3 SINGLE SOURCE)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

echo "🧭 Building registry..."
./scripts/build-content-registry.sh

echo "🌌 Building semantic truth layer (PRIMARY ARTIFACT)..."
python3 scripts/build-semantic-salience.py

# -----------------------------------------
# HARD GUARANTEE: semantic-salience MUST exist
# -----------------------------------------
if [ ! -f "semantic-salience.json" ]; then
  echo "❌ semantic-salience.json missing — HARD STOP"
  exit 1
fi

echo "🏠 Homepage intelligence (derivative)"
python3 scripts/build-homepage-intelligence.py || true

echo "🔗 Internal links (optional)"
./scripts/apply-internal-links.sh || true

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

echo "🧭 FINAL STATE: semantic-salience is the ONLY truth layer"
