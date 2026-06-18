#!/bin/bash
set -e

echo "🔎 Building search index (v3.1 connected intelligence)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="search-index.json"

echo "{" > "$OUTPUT"

FIRST=true

find . -type f -name "*.html" | while IFS= read -r file; do

  # -----------------------------
  # Normalize URL
  # -----------------------------
  URL=$(echo "$file" \
    | sed 's|^\./||' \
    | sed 's|index.html||' \
    | sed 's|\.html$||')

  URL="https://unboundhealing.org/${URL}"

  # -----------------------------
  # Extract metadata
  # -----------------------------
  TITLE=$(grep -m1 "<title>" "$file" | sed 's/<[^>]*>//g' || true)

  DESC=$(grep -m1 'name="description"' "$file" \
    | sed -E 's/.*content="([^"]*)".*/\1/' || true)

  # -----------------------------
  # v3.1: structured tag system (path-based for now, semantic later)
  # -----------------------------
  TAGS=$(echo "$file" \
    | sed 's|^\./||' \
    | awk -F'/' '
      {
        for (i=2; i<NF; i++) printf $i (i<NF-1?",":"")
      }
    ')

  # -----------------------------
  # fallback safety
  # -----------------------------
  [ -z "$TITLE" ] && TITLE="Untitled"
  [ -z "$DESC" ] && DESC=""

  # -----------------------------
  # JSON comma handling
  # -----------------------------
  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$OUTPUT"
  fi

  # -----------------------------
  # OUTPUT STRUCTURED OBJECT (v3.1 schema aligned)
  # -----------------------------
  cat <<EOF >> "$OUTPUT"
"$URL": {
  "title": "$TITLE",
  "url": "$URL",
  "path": "$file",
  "type": "page",
  "tags": "$TAGS",
  "description": "$DESC",
  "image": "",
  "last_modified": ""
}
EOF

done

echo "}" >> "$OUTPUT"

echo "✅ Search index built (v3.1)"
