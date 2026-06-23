#!/bin/bash
set -euo pipefail

echo "🧠 Building content model (v7 hardened CI-resilient resolver)..."

ROOT_DIR="${GITHUB_WORKSPACE:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

echo "📍 ROOT_DIR: $ROOT_DIR"
cd "$ROOT_DIR" || {
  echo "❌ Cannot enter ROOT_DIR"
  exit 1
}

REGISTRY="content-registry.json"
OUTPUT="content-model.json"
TMP="content-model.tmp.json"
BROKEN_LOG="broken-paths.log"

: > "$BROKEN_LOG"

# ---------------------------------------------------
# STEP 1 — VALIDATE REGISTRY
# ---------------------------------------------------

if [ ! -f "$REGISTRY" ]; then
  echo "❌ registry missing: $REGISTRY"
  exit 1
fi

echo "🧭 loading registry..."

COUNT=$(python3 - <<EOF
import json
print(len(json.load(open("$REGISTRY")).get("pages", [])))
EOF
)

echo "📦 registry entries: $COUNT"

if [ "$COUNT" -eq 0 ]; then
  echo "❌ registry empty"
  exit 1
fi

# ---------------------------------------------------
# STEP 2 — LOAD REGISTRY STREAM
# ---------------------------------------------------

python3 - <<EOF > /tmp/_pages.txt
import json
data=json.load(open("$REGISTRY"))
for p in data["pages"]:
    print(p["path"] + "||" + p["url"])
EOF

# ---------------------------------------------------
# STEP 3 — BUILD MODEL
# ---------------------------------------------------

echo "🧠 building content model from registry..."

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
PROCESSED=0
BROKEN=0

while IFS="||" read -r path url; do

  # ---------------------------------------------------
  # SAFE NORMALIZATION
  # ---------------------------------------------------

  clean="${path#./}"

  # resolve safely
  file="$ROOT_DIR/$clean"
  file="$(echo "$file" | sed 's#//*/#/#g')"

  echo "🔎 resolving: $clean"

  # ---------------------------------------------------
  # FILE GUARD (NO EXIT — JUST LOG)
  # ---------------------------------------------------

  if [ ! -f "$file" ]; then
    echo "❌ missing file: $file"
    echo "$clean" >> "$BROKEN_LOG"
    BROKEN=$((BROKEN+1))
    continue
  fi

  # ---------------------------------------------------
  # SAFE TITLE EXTRACTION (NO BS4 DEPENDENCY)
  # ---------------------------------------------------

  TITLE=$(python3 - "$file" <<'PY'
import sys,re
path=sys.argv[1]

try:
    html=open(path,encoding="utf-8").read()
except:
    html=""

m=re.search(r"<title>(.*?)</title>", html, re.IGNORECASE|re.DOTALL)
print(m.group(1).strip() if m else "")
PY
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
  "file": "$clean",
  "title": $(python3 -c "import json; print(json.dumps('''$TITLE'''))")
}
EOF

  PROCESSED=$((PROCESSED+1))

done < /tmp/_pages.txt

# ---------------------------------------------------
# STEP 4 — CLOSE JSON
# ---------------------------------------------------

echo "]" >> "$TMP"
echo "}" >> "$TMP"

# ---------------------------------------------------
# STEP 5 — VALIDATE OUTPUT (NON-FATAL SAFE)
# ---------------------------------------------------

python3 - <<EOF
import json
json.load(open("$TMP"))
print("✅ model JSON valid")
EOF

# ---------------------------------------------------
# STEP 6 — WRITE OUTPUT
# ---------------------------------------------------

mv "$TMP" "$OUTPUT"

# ---------------------------------------------------
# SUMMARY
# ---------------------------------------------------

echo "📦 pages processed: $PROCESSED"
echo "⚠️ broken paths: $BROKEN"
echo "📁 broken log: $BROKEN_LOG"
echo "✅ content model built (v7 resilient, non-fatal FS mode)"
