#!/bin/bash
set -euo pipefail

echo "🧠 Building content model (v6 hardened resolver + dependency-safe)..."

ROOT_DIR="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT_DIR"

REGISTRY="content-registry.json"
OUTPUT="content-model.json"
TMP="content-model.tmp.json"

if [ ! -f "$REGISTRY" ]; then
  echo "❌ registry missing"
  exit 1
fi

echo "🧭 loading registry..."

COUNT=$(python3 - <<EOF
import json
print(len(json.load(open("$REGISTRY")).get("pages", [])))
EOF
)

echo "📦 registry entries: $COUNT"

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
PROCESSED=0

python3 - <<EOF > /tmp/_pages.txt
import json
data=json.load(open("$REGISTRY"))
for p in data["pages"]:
    print(p["path"] + "||" + p["url"])
EOF

while IFS="||" read -r path url; do

  file="$ROOT_DIR/$path"

  echo "🔎 resolving: $path → $file"

  if [ ! -f "$file" ]; then
    echo "❌ missing file: $file"
    exit 1
  fi

  # ---------------------------------------------------
  # SAFE TITLE EXTRACTION (NO BS4 DEPENDENCY)
  # ---------------------------------------------------

  TITLE=$(python3 - "$file" <<'PY'
import sys
import re

path=sys.argv[1]

try:
    html=open(path,encoding="utf-8").read()
except:
    html=""

m=re.search(r"<title>(.*?)</title>", html, re.IGNORECASE|re.DOTALL)
print(m.group(1).strip() if m else "")
PY
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

  ((PROCESSED++))

done < /tmp/_pages.txt

echo "]" >> "$TMP"
echo "}" >> "$TMP"

python3 - <<EOF
import json
json.load(open("$TMP"))
print("✅ model valid")
EOF

mv "$TMP" "$OUTPUT"

echo "📦 pages processed: $PROCESSED"
echo "✅ content model built"
