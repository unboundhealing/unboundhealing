#!/bin/bash
set -e

echo "🚀 Generating v3.2 full system..."

# =========================
# v3.2 INTELLIGENCE LAYER
# =========================

echo "🧠 Building content model..."
./scripts/build-content-model.sh

echo "🔗 Building content graph..."
./scripts/build-content-graph.sh

echo "💡 Building link suggestions..."
./scripts/build-link-suggestions.sh

# =========================
# OUTPUT LAYERS (existing system)
# =========================

echo "🏷 Building tags..."
./scripts/build-tags.sh

echo "🔎 Building search index..."
./scripts/build-search-index.sh

echo "🗺 Building sitemap..."
./scripts/build-sitemap.sh

echo "📡 Generating RSS..."
./scripts/generate-rss.sh

echo "🧭 Auditing OpenGraph..."
./scripts/audit-opengraph.sh

echo "✅ All outputs updated (v3.2 pipeline complete)"
