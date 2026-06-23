#!/bin/bash
set -euo pipefail

echo "🚀 Generating v3.3 full system..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

echo "🧭 Building deterministic content registry..."
./scripts/build-content-registry.sh

if [ ! -f "content-registry.json" ]; then
  echo "❌ registry missing after build"
  exit 1
fi

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

echo "🌿 Building semantic salience..."
python3 scripts/build-semantic-salience.py

echo "🌱 Building semantic concepts..."
python3 scripts/build-semantic-concepts.py

echo "📖 Building page titles..."
python3 scripts/build-page-titles.py

echo "🏠 Building homepage intelligence..."
python3 scripts/build-homepage-intelligence.py

echo "🔗 Applying internal link injections..."
./scripts/apply-internal-links.sh

echo "🧠 Building semantic words..."
python3 scripts/build-semantic-words.py

echo "🧭 Building word graph..."
python3 scripts/build-word-graph.py

echo "✨ Enhancing pages..."
python3 scripts/enhance-pages.py

echo "🧠 Rendering homepage intelligence HTML..."
python3 scripts/render-homepage-html.py

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

echo "✅ All outputs updated"
