#!/bin/bash
set -euo pipefail

echo "🚀 Generating UNIFIED semantic-salience system (v1 SINGLE SOURCE)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

echo "🧭 Building registry..."
./scripts/build-content-registry.sh

echo "🌌 Building SEMANTIC TRUTH LAYER (ONLY AUTHORITY)..."
python3 scripts/build-semantic-salience.py

echo "🏠 Rendering homepage intelligence..."
python3 scripts/build-homepage-intelligence.py

echo "🔗 Applying link injections..."
./scripts/apply-internal-links.sh

echo "🗺 Building sitemap..."
./scripts/build-sitemap.sh

echo "📡 Generating RSS..."
./scripts/generate-rss.sh

echo "✨ Enhancing pages..."
python3 scripts/enhance-pages.py

echo "✅ BUILD COMPLETE — semantic-salience is single source of truth"
