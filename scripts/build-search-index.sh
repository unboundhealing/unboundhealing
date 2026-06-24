#!/bin/bash
set -euo pipefail

echo "🔎 Building search index (v4.1 resilient salience-consumer)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="search-index.json"
SAL_FILE="semantic-salience.json"

echo "{" > "$OUTPUT"
FIRST=true

# ---------------------------------------
# SAFE SALIENCE LOAD (NON-FATAL)
# ---------------------------------------
CONCEPT_MAP="{}"

if [ -f "$SAL_FILE" ]; then
  echo "🧠 Loading semantic-salience (optional enhancer)..."

  CONCEPT_MAP=$(python3 - << 'EOF'
import json

try:
    with open("semantic-salience.json", "r", encoding="utf-8") as f:
        data = json.load(f)
except Exception:
    print("{}")
    raise SystemExit(0)

pages = data.get("pages", {}) if isinstance(data, dict) else {}

result = {}

for url, node in pages.items():
    concepts = []

    if isinstance(node, dict):
        raw = node.get("concepts", [])

        if isinstance(raw, list):
            for c in raw:
                if isinstance(c, dict):
                    w = c.get("word")
                    if w:
                        concepts.append(w)

    result[url] = concepts[:10]

print(json.dumps(result))
EOF
  ) || CONCEPT_MAP="{}"
else
  echo "⚠️ semantic-salience not found — continuing with empty tags"
fi

# ---------------------------------------
# BUILD STRUCTURAL INDEX (NO SEMANTIC DEPENDENCY)
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
  # OPTIONAL SALIENCE TAGS (SAFE FALLBACK)
  # ---------------------------------------
  TAGS=$(echo "$CONCEPT_MAP" | python3 - << EOF
import json, sys

try:
    data = json.load(sys.stdin)
except Exception:
    data = {}

url = "$URL"

concepts = data.get(url, []) if isinstance(data, dict) else []

if not isinstance(concepts, list):
    concepts = []

# normalize + dedupe
clean = []
seen = set()

for c in concepts:
    if not isinstance(c, str):
        continue
    c = c.strip().lower()
    if not c or c in seen:
        continue
    seen.add(c)
    clean.append(c)

print(",".join(clean[:10]))
EOF
)

  # ---------------------------------------
  # WRITE ENTRY
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

echo "✅ Search index built (v4.1 resilient)"
echo "🧠 semantic-salience is optional, not required"
