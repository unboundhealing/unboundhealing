#!/bin/bash
set -euo pipefail

echo "🧭 Building deterministic content registry (v8 stable + CI-safe)..."

ROOT_DIR="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT_DIR"

OUTPUT="content-registry.json"
TMP="content-registry.tmp.json"
TMP_FILES="$(mktemp)"

echo "📂 scanning root: $(pwd)"

find . -type f -name "*.html" 2>/dev/null \
  | grep -v "./.git/" \
  | grep -v "./.github/" \
  | grep -v "./scripts/" \
  | sort > "$TMP_FILES"

COUNT=$(wc -l < "$TMP_FILES" | tr -d ' ')

echo "📦 html files discovered: $COUNT"

if [ "$COUNT" -eq 0 ]; then
  echo "❌ NO FILES FOUND"
  exit 1
fi

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
PROCESSED=0

while IFS= read -r file; do

  clean="${file#./}"

  url_path="${clean%index.html}"
  url_path="${url_path%.html}"

  url="https://unboundhealing.org/${url_path}"
  url=$(echo "$url" | sed 's|//|/|g' | sed 's|https:/|https://|')

  type="page"
  [[ "$clean" == assets/* ]] && type="asset"

  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$TMP"
  fi

  cat <<EOF >> "$TMP"
{
  "path": "$clean",
  "url": "$url",
  "type": "$type"
}
EOF

  ((PROCESSED++))

done < "$TMP_FILES"

echo "]" >> "$TMP"
echo "}" >> "$TMP"

python3 - <<EOF
import json
json.load(open("$TMP"))
print("✅ registry valid")
EOF

mv "$TMP" "$OUTPUT"
rm -f "$TMP_FILES"

echo "📦 registry entries: $PROCESSED"
echo "✅ registry built"
