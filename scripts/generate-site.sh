#!/bin/bash
set -euo pipefail

echo "🚀 Generating UNIFIED semantic-salience system (v3 SINGLE SOURCE)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

echo "🔄 Syncing with origin..."
git fetch origin main
git rebase origin/main

# ---------------------------------------------------------
# STEP 1 — TRUTH LAYER (ONLY AUTHORITATIVE SOURCE)
# ---------------------------------------------------------

echo "🌌 Building semantic truth layer (PRIMARY ARTIFACT)..."
python3 scripts/build-semantic-salience.py

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

# ---------------------------------------------------------
# STEP 3 — TAGS / RENDER LAYER
# ---------------------------------------------------------

echo "🏷️ Building vocabulary..."
python3 scripts/build-vocabulary.py

# ---------------------------------------------------------
# STEP 4 — PRESENTATION / RENDER LAYER
# ---------------------------------------------------------

echo "📡 Tracking injection..."
python3 scripts/build-tracking.py

echo "📡 Verifying tracker..."
python3 scripts/build-tracking.py

echo "📡 RSS (optional)"
./scripts/generate-rss.sh || true

echo "🗺 Sitemap (optional)"
./scripts/build-sitemap.sh || true

echo "🔎 Search index (optional)"
./scripts/build-search-index.sh || true

echo "===== HTML DIFF ====="
git diff -- opening/no-tea/index.html

echo "💾 Committing generated assets..."

git config user.name "github-actions"
git config user.email "github-actions@github.com"

git add \
  assets/*.json \
  *.html \
  **/*.html \
  feed.xml \
  sitemap.xml

echo "🔍 STAGED FILES:"
git diff --cached --name-only

if git diff --cached --quiet; then
  echo "✅ No generated changes detected"
  exit 0
fi

git commit -m "🔄 update generated site assets" || true

git push

# ---------------------------------------------------------
# FINAL STATE DECLARATION
# ---------------------------------------------------------

echo "🧭 FINAL STATE: semantic-salience is the ONLY truth layer"
echo "🧱 legacy semantic graph systems are archived / disabled"
