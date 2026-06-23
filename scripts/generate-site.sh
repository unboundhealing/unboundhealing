#!/bin/bash
set -euo pipefail

echo "🚀 Generating UNIFIED semantic-salience system (v2 SINGLE SOURCE)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

echo "🧭 Building registry..."
./scripts/build-content-registry.sh

echo "🌌 Building semantic truth layer..."
python3 scripts/build-semantic-salience.py

echo "🏠 Homepage intelligence..."
python3 scripts/build-homepage-intelligence.py || true

echo "🔗 Internal links..."
./scripts/apply-internal-links.sh || true

echo "🗺 Sitemap..."
./scripts/build-sitemap.sh || true

echo "📡 RSS..."
./scripts/generate-rss.sh || true

echo "✨ Page enhancement..."
python3 scripts/enhance-pages.py || true

echo "✅ BUILD COMPLETE — semantic-salience is the ONLY truth layer"
