#!/bin/bash
set -e

echo "🚀 Generating full site system..."

./scripts/build-sitemap.sh
./scripts/build-links.sh
./scripts/generate-rss.sh
./scripts/build-search-index.sh
./scripts/build-tags.sh
./scripts/audit-opengraph.sh

echo "✅ All outputs updated"
