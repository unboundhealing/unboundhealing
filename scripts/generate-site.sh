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

echo "🧠 Building semantic model..."
python3 scripts/extract-semantic-model.py

echo "🧭 Building semantic graph..."
python3 scripts/build-semantic-graph.py

echo "🧩 Building concept clusters..."
python3 scripts/build-concept-clusters.py

echo "🏠 Building homepage intelligence..."
python3 scripts/build-homepage-intelligence.py

# =========================
# EXECUTION LAYER
# =========================

echo "🔗 Applying internal link injections..."
./scripts/apply-internal-links.sh

# =========================
# OUTPUT LAYERS (existing system)
# =========================

echo "🏷 Building tags..."
./scripts/build-tags.sh

echo "🔎 Building search index..."
./scripts/build-search-index.sh

echo "🧠 Building semantic words (v3.3 Phase 1)..."
python3 scripts/build-semantic-words.py
echo "✅ Semantic words built (v3.3)"

echo "🧭 Building word graph (v3.3 Phase 2)..."
python3 scripts/build-word-graph.py
echo "✅ Word graph built (v3.3)"

echo "🔗 Injecting related content (v3.3 Phase 3)..."
python3 scripts/inject-related-content.py
echo "✅ Related content injected (v3.3)"

echo "🗺 Building sitemap..."
./scripts/build-sitemap.sh

echo "📡 Generating RSS..."
./scripts/generate-rss.sh

echo "🧭 Auditing OpenGraph..."
./scripts/audit-opengraph.sh

echo "✅ All outputs updated (v3.2 pipeline complete)"
