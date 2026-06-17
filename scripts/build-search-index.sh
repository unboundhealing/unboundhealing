#!/bin/bash
set -e

echo "🔎 Building search index..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="search-index.json"

echo "{" > "$OUTPUT"

FIRST=true

find . -type f -name "*.html" | while read -r file; do

  URL=$(echo "$file" \
    | sed 's|^\./||' \
    | sed 's|index.html||' \
    | sed 's|\.html$||')

  URL="https://unboundhealing.org/${URL}"

  TITLE=$(grep -m1 "<title>" "$file" | sed 's/<[^>]*>//g' || true)
  DESC=$(grep -m1 'name="description"' "$file" | sed -E 's/.*content="([^"]*)".*/\1/' || true)

  TAGS=$(echo "$URL" | tr '/' '\n' | grep -v '^$' | tail -n +4 | paste -sd "," -)

  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$OUTPUT"
  fi

  cat <<EOF >> "$OUTPUT"
"$URL": {
  "title": "$TITLE",
  "description": "$DESC",
  "tags": "$TAGS",
  "url": "$URL"
}
EOF

done

echo "}" >> "$OUTPUT"

echo "✅ Search index built"
