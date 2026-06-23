#!/bin/bash
set -euo pipefail

echo "🧭 Building deterministic content registry (v9 STREAM SAFE + CI bulletproof)..."

ROOT_DIR="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT_DIR" || exit 1

OUTPUT="content-registry.json"
TMP="content-registry.tmp.json"

echo "📂 scanning root: $(pwd)"

# ---------------------------------------------------
# STEP 1 — STREAM FILE COUNT (NO ARRAYS, NO PIPEFAIL TRAPS)
# ---------------------------------------------------

COUNT=0

TMP_LIST="$(mktemp)"

find . -type f -name "*.html" 2>/dev/null \
  | grep -v "./.git/" \
  | grep -v "./.github/" \
  | grep -v "./scripts/" \
  | sort > "$TMP_LIST"

COUNT=$(wc -l < "$TMP_LIST" | tr -d ' ')

echo "📦 html files discovered: $COUNT"

if [ "$COUNT" -eq 0 ]; then
  echo "❌ no HTML files found"
  exit 1
fi

# ---------------------------------------------------
# STEP 2 — INIT JSON
# ---------------------------------------------------

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=1
PROCESSED=0

# ---------------------------------------------------
# STEP 3 — STREAM LOOP (NO ARRAYS EVER)
# ---------------------------------------------------

while IFS= read -r file; do

  clean="${file#./}"

  url_path="${clean%index.html}"
  url_path="${url_path%.html}"

  url="https://unboundhealing.org/${url_path}"
  url=$(echo "$url" | sed 's#//+#/#g' | sed 's#https:/#https://#')

  type="page"
  [[ "$clean" == assets/* ]] && type="asset"

  if [ "$FIRST" -eq 0 ]; then
    echo "," >> "$TMP"
  fi
  FIRST=0

  cat <<EOF >> "$TMP"
{
  "path": "$clean",
  "url": "$url",
  "type": "$type"
}
EOF

  PROCESSED=$((PROCESSED+1))

done < "$TMP_LIST"

# ---------------------------------------------------
# STEP 4 — CLOSE JSON
# ---------------------------------------------------

echo "]" >> "$TMP"
echo "}" >> "$TMP"

# ---------------------------------------------------
# STEP 5 — VALIDATE
# ---------------------------------------------------

python3 - <<EOF
import json
json.load(open("$TMP"))
print("✅ registry valid (v9 stream-safe)")
EOF

# ---------------------------------------------------
# STEP 6 — FINALIZE
# ---------------------------------------------------

mv "$TMP" "$OUTPUT"
rm -f "$TMP_LIST"

echo "📦 registry entries: $PROCESSED"
echo "✅ content registry built (v9 STREAM SAFE + CI HARDENED)"
