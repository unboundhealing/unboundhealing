#!/bin/bash
set -euo pipefail

echo "🧠 Building content model (v6 registry-driven deterministic pipeline - fixed resolver)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

REGISTRY="content-registry.json"
OUTPUT="content-model.json"
TMP="content-model.tmp.json"

# ---------------------------------------------------
# STEP 1 — VALIDATE REGISTRY EXISTS
# ---------------------------------------------------

if [ ! -f "$REGISTRY" ]; then
  echo "❌ registry missing: $REGISTRY"
  echo "💡 run build-content-registry.sh first"
  exit 1
fi

echo "🧭 loading registry..."

# ---------------------------------------------------
# STEP 2 — EXTRACT ENTRIES
# ---------------------------------------------------

COUNT=$(python3 - <<EOF
import json
data = json.load(open("$REGISTRY"))
print(len(data.get("pages", [])))
EOF
)

echo "📦 registry entries: $COUNT"

if [ "$COUNT" -eq 0 ]; then
  echo "❌ registry empty"
  exit 1
fi

# ---------------------------------------------------
# STEP 3 — BUILD MODEL
# ---------------------------------------------------

echo "🧠 building content model from registry..."

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
PROCESSED=0

python3 - <<EOF > /tmp/_pages.txt
import json
data = json.load(open("$REGISTRY"))
for p in data["pages"]:
    print(p["path"] + "||" + p["url"])
EOF

while IFS="||" read -r path url; do

  # ---------------------------------------------------
  # FIXED PATH RESOLUTION (CRITICAL FIX)
  # ---------------------------------------------------
  file="$ROOT_DIR/$path"
  file=$(echo "$file" | sed 's|//|/|g')

  echo "🔎 resolving: $path → $file"

  if [ ! -f "$file" ]; then
    echo "❌ missing registry file: $file"
    exit 1
  fi

  # ---------------------------------------------------
  # SAFE TITLE EXTRACTION
  # ---------------------------------------------------
  TITLE=$(python3 - <<EOF
from bs4 import BeautifulSoup

try:
    with open("$file", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    print((soup.title.string or "").strip())
except:
    print("")
EOF
)

  # ---------------------------------------------------
  # WRITE ENTRY
  # ---------------------------------------------------

  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$TMP"
  fi

  cat <<EOF >> "$TMP"
{
  "url": "$url",
  "file": "$path",
  "title": $(python3 -c "import json; print(json.dumps('''$TITLE'''))")
}
EOF

  ((PROCESSED++))

done < /tmp/_pages.txt

# ---------------------------------------------------
# STEP 4 — CLOSE JSON
# ---------------------------------------------------

echo "]" >> "$TMP"
echo "}" >> "$TMP"

# ---------------------------------------------------
# STEP 5 — VALIDATION
# ---------------------------------------------------

echo "🧪 validating JSON..."

python3 - <<EOF
import json
json.load(open("$TMP"))
print("✅ JSON valid (v6 pipeline)")
EOF

# ---------------------------------------------------
# STEP 6 — WRITE OUTPUT
# ---------------------------------------------------

mv "$TMP" "$OUTPUT"

echo "✅ Content model built (v6 registry-driven fixed)"
echo "📁 output: $OUTPUT"
echo "📦 pages processed: $PROCESSED"
