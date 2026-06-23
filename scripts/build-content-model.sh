#!/bin/bash
set -euo pipefail

echo "🧠 Building content model (v6 registry-driven deterministic pipeline)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

REGISTRY="content-registry.json"
OUTPUT="content-model.json"
TMP="content-model.tmp.json"

# -----------------------------
# VALIDATE REGISTRY EXISTS
# -----------------------------
if [ ! -f "$REGISTRY" ]; then
  echo "❌ registry missing: $REGISTRY"
  echo "💡 run build-content-registry.sh first"
  exit 1
fi

echo "🧭 loading registry..."

# -----------------------------
# extract page list safely
# -----------------------------
PAGES=$(python3 - <<EOF
import json
data = json.load(open("$REGISTRY"))
pages = data.get("pages", [])
print(len(pages))
EOF
)

echo "📦 registry entries: $PAGES"

if [ "$PAGES" -eq 0 ]; then
  echo "❌ registry empty"
  echo "💡 build-content-registry.sh produced no pages"
  exit 1
fi

# -----------------------------
# START MODEL BUILD
# -----------------------------
echo "🧠 building content model from registry..."

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
COUNT=0

python3 - <<EOF > /tmp/_registry_pages.txt
import json
data = json.load(open("$REGISTRY"))
for p in data["pages"]:
    print(p["path"] + "||" + p["url"])
EOF

while IFS="||" read -r path url; do

  file="$ROOT_DIR/$path"

  if [ ! -f "$file" ]; then
    echo "⚠️ missing file: $file"
    continue
  fi

  TITLE=$(python3 - <<EOF
from bs4 import BeautifulSoup
path="$file"
try:
    soup = BeautifulSoup(open(path, encoding="utf-8").read(), "html.parser")
    print((soup.title.string or "").strip())
except:
    print("")
EOF
)

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

  ((COUNT++))

done < /tmp/_registry_pages.txt

echo "]" >> "$TMP"
echo "}" >> "$TMP"

# -----------------------------
# validate
# -----------------------------
echo "🧪 validating JSON..."

python3 - <<EOF
import json
json.load(open("$TMP"))
print("✅ JSON valid")
EOF

mv "$TMP" "$OUTPUT"

echo "✅ Content model built (v6 registry-driven)"
echo "📁 output: $OUTPUT"
echo "📦 pages processed: $COUNT"
