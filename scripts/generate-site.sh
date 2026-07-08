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


echo "AFTER semantic-salience"
git status --short


# HARD GUARANTEE: semantic-salience MUST exist
if [ ! -f "assets/semantic-salience.json" ]; then
  echo "❌ assets/semantic-salience.json missing — HARD STOP"
  exit 1
fi

# ---------------------------------------------------------
# STEP 2 — DERIVATIVE LAYERS (TRUTH CONSUMERS ONLY)
# ---------------------------------------------------------

echo "🏠 Homepage intelligence (derivative)"
python3 scripts/build-homepage-intelligence.py || true


echo "AFTER homepage-intelligence"
git status --short


# ---------------------------------------------------------
# STEP 3 — TAGS / RENDER LAYER
# ---------------------------------------------------------

echo "🏷️ Building vocabulary..."
python3 scripts/build-vocabulary.py


echo "AFTER vocabulary"
git status --short


# ---------------------------------------------------------
# STEP 4 — PRESENTATION / RENDER LAYER
# ---------------------------------------------------------

echo "📡 Tracking injection (standalone consumer)..."
python3 scripts/build-tracking.py

echo "📡 RSS (optional)"
./scripts/generate-rss.sh || true


echo "AFTER rss"
git status --short


echo "🗺 Sitemap (optional)"
./scripts/build-sitemap.sh || true


echo "AFTER sitemap"
git status --short


echo "🔎 Search index (optional)"
./scripts/build-search-index.sh || true


echo "AFTER search-index"
git status --short


echo "💾 Committing generated assets..."

git config user.name "github-actions"
git config user.email "github-actions@github.com"

git add \
  assets/*.json \
  "**/*.html" \
  feed.xml \
  sitemap.xml
  
git commit -m "🔄 update generated site assets" || exit 0

git fetch origin main

git status --short

git push

# ---------------------------------------------------------
# FINAL STATE DECLARATION
# ---------------------------------------------------------

echo "🧭 FINAL STATE: semantic-salience is the ONLY truth layer"
echo "🧱 legacy semantic graph systems are archived / disabled"
