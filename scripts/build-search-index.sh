#!/bin/bash
set -euo pipefail

echo "🔎 Building search index (v4.0 salience-consumer architecture)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="search-index.json"

if [ ! -f "semantic-salience.json" ]; then
  echo "❌ semantic-salience.json missing — cannot build search index"
  exit 1
fi

echo "{" > "$OUTPUT"

FIRST=true

# ---------------------------------------
# Load semantic-salience for tag projection
# ---------------------------------------
SAL_FILE="semantic-salience.json"

echo "🧠 Loading semantic-salience (truth layer consumer mode)..."

# We extract concept map using python for safety + correctness
CONCEPT_MAP=$(python3 - << 'EOF'
import json

with open("semantic-salience.json", "r", encoding="utf-8") as f:
    data = json.load(f)

pages = data.get("pages", {})

result = {}

for url, node in pages.items():
    concepts = node.get("concepts", [])
    if isinstance(concepts, list):
        result[url] = [
            c.get("word") for c in concepts
            if isinstance(c, dict) and c.get("word")
        ]

print(json.dumps(result))
EOF
)

# ---------------------------------------
# Process HTML files (STRUCTURE ONLY)
# ---------------------------------------
find . -type f -name "*.html" | while IFS= read -r file; do

  URL=$(echo "$file" \
    | sed 's|^\./||' \
    | sed 's|index.html||' \
    | sed 's|\.html$||')

  URL="https://unboundhealing.org/${URL}"

  TITLE=$(grep -m1 "<title>" "$file" | sed 's/<[^>]*>//g' || true)
  DESC=$(grep -m1 'name="description"' "$file" \
    | sed -E 's/.*content="([^"]*)".*/\1/' || true)

  [ -z "$TITLE" ] && TITLE="Untitled"
  [ -z "$DESC" ] && DESC=""

  # ---------------------------------------
  # SALIENCE-DRIVEN TAGS (NOT FILESYSTEM)
  # ---------------------------------------
  TAGS=$(echo "$CONCEPT_MAP" | python3 - << EOF
import json, sys

data = json.load(sys.stdin)

url = "$URL"
concepts = data.get(url, [])

# ensure stable, small tag set
concepts = [c for c in concepts if c]

print(",".join(concepts[:10]))
EOF
)

  # ---------------------------------------
  # JSON formatting
  # ---------------------------------------
  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$OUTPUT"
  fi

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

echo "✅ Search index built (v4.0 SALIENCE-ALIGNED)"
echo "🧠 tags now derived from semantic-salience (NOT filesystem)"
