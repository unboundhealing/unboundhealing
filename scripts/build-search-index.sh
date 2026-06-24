#!/bin/bash
set -euo pipefail

echo "🔎 Building search index (v4.2 truth-layer consumer)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="search-index.json"
SAL_FILE="semantic-salience.json"

# ---------------------------------------------------------
# HARD REQUIREMENT: TRUTH LAYER MUST EXIST
# ---------------------------------------------------------

if [ ! -f "$SAL_FILE" ]; then
  echo "❌ semantic-salience.json missing — HARD STOP"
  exit 1
fi

echo "🧠 Loading semantic-salience (truth layer)..."

# ---------------------------------------------------------
# PROJECT CONCEPTS FROM TRUTH LAYER
# ---------------------------------------------------------

CONCEPT_MAP=$(python3 << 'EOF'
import json

with open("semantic-salience.json", "r", encoding="utf-8") as f:
    data = json.load(f)

result = {}

if not isinstance(data, dict):
    raise SystemExit("semantic-salience must be a dict")

for url, node in data.items():

    concepts = []

    if isinstance(node, dict):

        raw = node.get("concepts", [])

        if isinstance(raw, list):

            for c in raw:

                if isinstance(c, str):
                    concepts.append(c)

                elif isinstance(c, dict):
                    word = c.get("word")
                    if word:
                        concepts.append(word)

    result[url] = concepts[:10]

print(json.dumps(result))
EOF
)

# ---------------------------------------------------------
# BEGIN INDEX
# ---------------------------------------------------------

echo "{" > "$OUTPUT"

FIRST=true

# ---------------------------------------------------------
# DISCOVER HTML FILES
# ---------------------------------------------------------

find . -type f -name "*.html" ! -path "./assets/*" | sort | while IFS= read -r file
do

  # -------------------------------------------------------
  # CANONICAL URL NORMALIZATION
  # -------------------------------------------------------

  REL_PATH=$(echo "$file" | sed 's|^\./||')

  if [[ "$REL_PATH" == "index.html" ]]; then
      URL="https://unboundhealing.org/"
  else
      URL=$(echo "$REL_PATH" \
        | sed 's|index.html$||' \
        | sed 's|\.html$||')

      URL="https://unboundhealing.org/${URL}"

      case "$URL" in
          */) ;;
          *) URL="${URL}/" ;;
      esac
  fi

  # -------------------------------------------------------
  # TITLE
  # -------------------------------------------------------

  TITLE=$(grep -m1 "<title>" "$file" \
    | sed 's/<[^>]*>//g' \
    || true)

  [ -z "$TITLE" ] && TITLE="Untitled"

  # -------------------------------------------------------
  # DESCRIPTION
  # -------------------------------------------------------

  DESC=$(grep -m1 'name="description"' "$file" \
    | sed -E 's/.*content="([^"]*)".*/\1/' \
    || true)

  [ -z "$DESC" ] && DESC=""

  # -------------------------------------------------------
  # SALIENCE PROJECTION
  # -------------------------------------------------------

  TAGS=$(python3 << EOF
import json

data = json.loads("""$CONCEPT_MAP""")

url = "$URL"

concepts = data.get(url, [])

clean = []
seen = set()

for c in concepts:

    if not isinstance(c, str):
        continue

    c = c.strip().lower()

    if not c:
        continue

    if c in seen:
        continue

    seen.add(c)
    clean.append(c)

print(",".join(clean[:10]))
EOF
)

  # -------------------------------------------------------
  # JSON COMMA MANAGEMENT
  # -------------------------------------------------------

  if [ "$FIRST" = true ]; then
      FIRST=false
  else
      echo "," >> "$OUTPUT"
  fi

  # -------------------------------------------------------
  # ESCAPE STRINGS
  # -------------------------------------------------------

  ESC_TITLE=$(printf '%s' "$TITLE" | sed 's/"/\\"/g')
  ESC_DESC=$(printf '%s' "$DESC" | sed 's/"/\\"/g')

  # -------------------------------------------------------
  # WRITE ENTRY
  # -------------------------------------------------------

  cat <<EOF >> "$OUTPUT"
"$URL": {
  "title": "$ESC_TITLE",
  "url": "$URL",
  "path": "$file",
  "type": "page",
  "tags": "$TAGS",
  "description": "$ESC_DESC",
  "image": "",
  "last_modified": ""
}
EOF

done

echo "" >> "$OUTPUT"
echo "}" >> "$OUTPUT"

echo "✅ Search index built (v4.2 truth-layer consumer)"
echo "🧠 semantic-salience is the source of all semantic metadata"
