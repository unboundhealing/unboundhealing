#!/bin/bash
set -euo pipefail

echo "🧠 Building content model (v9 canonical-ID aligned + CI-safe)"

ROOT_DIR="${GITHUB_WORKSPACE:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

echo "📍 ROOT_DIR: $ROOT_DIR"
cd "$ROOT_DIR" || exit 1

REGISTRY="content-registry.json"
OUTPUT="content-model.json"
TMP="content-model.tmp.json"
BROKEN_LOG="broken-paths.log"

: > "$BROKEN_LOG"

if [ ! -f "$REGISTRY" ]; then
  echo "❌ registry missing"
  exit 1
fi

echo "🧭 loading registry..."

python3 - <<EOF > /tmp/_pages.txt
import json
data=json.load(open("$REGISTRY"))
for p in data.get("pages", []):
    print(p.get("path","") + "||" + p.get("url",""))
EOF

echo "🧠 building content model..."

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
COUNT=0

canonicalize () {
  python3 - <<PY
import re,sys
p=sys.argv[1].strip()

p=p.lstrip("|")
p=re.sub(r"^https?:\/\/[^\/]+","",p)
p="/" + p.strip("/")
p=re.sub(r"/+","/",p)
if "." not in p.split("/")[-1]:
    if not p.endswith("/"):
        p+="/"
print(p.lower())
PY
}

while IFS="||" read -r path url; do

  clean_path="$(canonicalize "$path")"
  clean_url="$(canonicalize "$url")"

  file="$ROOT_DIR/$clean_path"
  file="$(echo "$file" | sed 's#//*/#/#g')"

  echo "🔎 resolving: $clean_path"

  if [ ! -f "$file" ]; then
    echo "❌ missing file: $file"
    echo "$clean_path" >> "$BROKEN_LOG"
    continue
  fi

  TITLE=$(python3 - "$file" <<'PY'
import sys,re
html=open(sys.argv[1],encoding="utf-8").read()
m=re.search(r"<title>(.*?)</title>",html,re.I|re.S)
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
  "url": "$clean_url",
  "file": "$clean_path",
  "title": $(python3 -c "import json; print(json.dumps('''$TITLE'''))")
}
EOF

  COUNT=$((COUNT+1))

done < /tmp/_pages.txt

echo "]" >> "$TMP"
echo "}" >> "$TMP"

python3 - <<EOF
import json
json.load(open("$TMP"))
print("✅ model JSON valid")
EOF

mv "$TMP" "$OUTPUT"

echo "📦 pages processed: $COUNT"
echo "⚠️ broken paths: $(wc -l < $BROKEN_LOG || true)"
echo "✅ content model built (v9 canonical-id aligned)"
