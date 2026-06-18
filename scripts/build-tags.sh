#!/bin/bash
set -e

echo "🏷 Building tags (v3.1 derived intelligence)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

INPUT="search-index.json"
OUTPUT="tags.json"

if [ ! -f "$INPUT" ]; then
  echo "❌ search-index.json not found"
  exit 1
fi

echo "{" > "$OUTPUT"

# ---------------------------------------
# Extract all tag strings from search index
# ---------------------------------------

ALL_TAGS=$(grep -o '"tags": *"[^"]*"' "$INPUT" \
  | sed 's/"tags": "//' \
  | sed 's/"//g' \
  | tr ',' '\n' \
  | sed '/^$/d' \
  | sort \
  | uniq)

FIRST=true

for tag in $ALL_TAGS; do

  # ---------------------------------------
  # Find pages containing this tag
  # ---------------------------------------
  PAGES=$(grep -B3 -A2 "\"tags\":.*$tag" "$INPUT" \
    | grep '"url"' \
    | sed -E 's/.*"(https[^"]+)".*/\1/' \
    | sort \
    | uniq)

  PAGE_LIST=$(printf '%s\n' "$PAGES" | sed 's/^/    "/; s/$/"/' | paste -sd "," -)

  COUNT=$(echo "$PAGES" | grep -c .)

  # ---------------------------------------
  # JSON formatting safety
  # ---------------------------------------
  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$OUTPUT"
  fi

  cat <<EOF >> "$OUTPUT"
"$tag": {
  "count": $COUNT,
  "pages": [
$PAGE_LIST
  ]
}
EOF

done

echo "}" >> "$OUTPUT"

echo "✅ Tags built (v3.1)"
