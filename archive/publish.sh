#!/bin/bash

set -e  # stop on error

echo "🚀 Unbound Healing Publisher v1.3 (Step 1)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

echo "📡 Generating RSS feed..."
./scripts/generate-rss.sh

echo "📄 (placeholder) sitemap sync..."
# future: ./scripts/generate-sitemap.sh

echo "🔗 (placeholder) link-reference sync..."
# future: ./scripts/generate-link-reference.sh

echo "🔎 (placeholder) search index..."
# future: ./scripts/generate-search-index.sh

echo "📦 Staging changes..."
git add \
  sitemap.xml \
  feed.xml \
  link-reference.md \
  search-index.json \
  tags.json

echo "📝 Committing changes..."

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

git commit -m "site publish: $TIMESTAMP" || echo "⚠️ No changes to commit"

echo "⬆️ Pushing to origin/main..."
git push

echo "✅ Publish complete."
