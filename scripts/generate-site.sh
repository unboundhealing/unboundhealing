#!/bin/bash
set -e

echo "🚀 Generating full site system v1.3"

./scripts/build-sitemap.sh
./scripts/build-rss.sh
./scripts/build-links.sh
./scripts/build-search-index.sh
./scripts/build-tags.sh
./scripts/audit-opengraph.sh

echo "✅ All systems updated"
