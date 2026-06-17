#!/bin/bash

set -e

echo "🚀 Generating full site system..."

./scripts/build-sitemap.sh
./scripts/build-rss.sh
./scripts/build-links.sh
./scripts/build-search-index.sh
./scripts/build-tags.sh

echo "🧠 OpenGraph assumed embedded in templates or build step"

echo "✅ All outputs updated"
