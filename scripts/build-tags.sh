#!/bin/bash
set -e

echo "🏷 Building tags..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="tags.json"

echo "{" > "$OUTPUT"

FIRST=true

find . -type f -name "*.html" | while read -r file; do

  URL=$(echo "$file" \
    | sed 's|^\./||' \
    | sed 's|index.html||' \
    | sed 's|\.html$||')

  URL="https://unboundhealing.org/${URL}"

  TAG1=$(echo "$URL" | cut -d'/' -f4)
  TAG2=$(echo "$URL" | cut -d'/' -f5)

  if [ -z "$TAG2" ]; then
    TAGS="$TAG1"
  else
    TAGS="$TAG1,$TAG2"
  fi

  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$OUTPUT"
  fi

  cat <<EOF >> "$OUTPUT"
"$URL": "$TAGS"
EOF

done

echo "}" >> "$OUTPUT"

echo "✅ Tags built"
