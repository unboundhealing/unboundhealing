#!/bin/bash

echo "🚀 Generating full site system..."

./scripts/build-sitemap.sh
./scripts/build-rss.sh
./scripts/build-links.sh
./scripts/build-search-index.sh
./scripts/build-tags.sh

echo "✅ All outputs updated"
