#!/bin/bash
set -e

echo "🔎 Building search index..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="search-index.json"

echo "[" > "$OUTPUT"

first=true

# Pull URLs from sitemap
grep "<loc>" sitemap.xml | sed 's/<[^>]*>//g' | while read -r url; do

  echo "→ indexing $url"

  # fetch HTML
  html=$(curl -s "$url")

  # extract title
  title=$(echo "$html" | grep -o '<title>[^<]*' | sed 's/<title>//')

  # extract meta description
  desc=$(echo "$html" | grep -o 'meta name="description" content="[^"]*"' | sed 's/.*content="//;s/"$//')

  # basic tag inference (folder-based)
  tags=$(echo "$url" | awk -F/ '{for(i=4;i<NF;i++) printf $i","}' | sed 's/,$//')

  if [ "$first" = true ]; then
    first=false
  else
    echo "," >> "$OUTPUT"
  fi

  cat <<EOF >> "$OUTPUT"
{
  "title": "$title",
  "url": "$url",
  "description": "$desc",
  "tags": "$tags"
}
EOF

done

echo "]" >> "$OUTPUT"

echo "✅ search-index.json built"
