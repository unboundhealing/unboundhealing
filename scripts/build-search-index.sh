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
# SINGLE PYTHON PASS: CONCEPT MAP ONLY
# ---------------------------------------------------------

CONCEPT_MAP=$(python3 << 'EOF'
import json

with open("semantic-salience.json", "r", encoding="utf-8") as f:
    data = json.load(f)

if not isinstance(data, dict):
    raise SystemExit("semantic-salience must be a dict")

graph = data.get("page_graph", {})

result = {}

for url, node in graph.items():

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

    result[url] = clean[:10]

import json as j
print(j.dumps(result))
EOF
)

# ---------------------------------------------------------
# BEGIN INDEX
# ---------------------------------------------------------

echo "{" > "$OUTPUT"
FIRST=true

# ---------------------------------------------------------
# SAFE FILE DISCOVERY (FIXED LOOP - NO SUBSHELLS)
# ---------------------------------------------------------

find . -type f -name "*.html" ! -path "./assets/*" | sort | while IFS= read -r file
do

# -------------------------------------------------------
# URL NORMALIZATION
# -------------------------------------------------------

REL_PATH="${file#./}"

if [[ "$REL_PATH" == "index.html" ]]; then
    URL="https://unboundhealing.org/"
else
    URL="${REL_PATH%index.html}"
    URL="${URL%.html}"
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
# SAFE TAG EXTRACTION (NO JSON RE-PIPE, NO HEREDOC BRIDGING)
# -------------------------------------------------------

TAGS=$(printf "%s" "$CONCEPT_MAP" | python3 - "$URL" << 'EOF'
import json, sys

data = json.load(sys.stdin)
url = sys.argv[1]

node = data.get(url, [])

if not isinstance(node, list):
    node = []

clean = []
seen = set()

for c in node:
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

# -------------------------------------------------------
# ESCAPING
# -------------------------------------------------------

ESC_TITLE=$(printf '%s' "$TITLE" | sed 's/"/\\"/g')
ESC_DESC=$(printf '%s' "$DESC" | sed 's/"/\\"/g')
ESC_TAGS=$(printf '%s' "$TAGS" | sed 's/"/\\"/g')

# -------------------------------------------------------
# JSON OUTPUT
# -------------------------------------------------------

if [ "$FIRST" = true ]; then
    FIRST=false
else
      echo "," >> "$OUTPUT"
fi

cat <<EOF >> "$OUTPUT"
"$URL": {
"title": "$ESC_TITLE",
"url": "$URL",
"path": "$file",
"type": "page",
"tags": "$ESC_TAGS",
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
