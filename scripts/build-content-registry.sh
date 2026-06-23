#!/bin/bash
set -euo pipefail

# =========================================================
# DIAGNOSTIC MODE (CRITICAL FIX)
# =========================================================
set -x
trap 'echo "❌ REGISTRY FAILED AT LINE $LINENO (exit code $?)"' ERR

echo "🧭 Building deterministic content registry (v8 DIAGNOSTIC + CI-TRACE MODE)..."

ROOT_DIR="${GITHUB_WORKSPACE:-$(pwd)}"
echo "📍 ROOT_DIR = $ROOT_DIR"

cd "$ROOT_DIR" || {
  echo "❌ FAILED TO ENTER ROOT_DIR"
  exit 1
}

OUTPUT="content-registry.json"
TMP="content-registry.tmp.json"
TMP_FILES="$(mktemp)"

# =========================================================
# STEP 1 — FILE DISCOVERY (NO PIPE CHAINS THAT CAN FAIL SILENTLY)
# =========================================================

echo "📂 scanning root: $(pwd)"

find . -type f -name "*.html" 2>&1 \
  | grep -v "^find:" \
  | grep -v "^grep:" \
  | grep -v "^Binary file" \
  | grep -v "./.git/" \
  | grep -v "./.github/" \
  | grep -v "./scripts/" \
  | sort > "$TMP_FILES"

echo "📦 file list written to temp buffer: $TMP_FILES"

COUNT=$(wc -l < "$TMP_FILES" | tr -d ' ')
echo "📦 html files discovered: $COUNT"

if [ "$COUNT" -eq 0 ]; then
  echo "❌ NO FILES FOUND — ABORT"
  exit 1
fi

echo "checkpoint A: file discovery complete"

# =========================================================
# STEP 2 — INIT JSON
# =========================================================

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
PROCESSED=0

echo "checkpoint B: JSON initialized"

# =========================================================
# STEP 3 — PROCESS FILES (SAFE STREAM LOOP)
# =========================================================

while IFS= read -r file; do

  echo "processing: $file"

  if [ -z "${file:-}" ]; then
    echo "⚠️ skipping empty file line"
    continue
  fi

  clean="${file#./}"

  if [ -z "$clean" ]; then
    echo "⚠️ skipping empty clean path"
    continue
  fi

  # -----------------------------------------------------
  # URL NORMALIZATION (SAFE STRING OPS ONLY)
  # -----------------------------------------------------

  url_path="${clean%index.html}"
  url_path="${url_path%.html}"

  url="https://unboundhealing.org/${url_path}"
  url=$(echo "$url" | sed 's|//|/|g' | sed 's|https:/|https://|')

  # -----------------------------------------------------
  # TYPE
  # -----------------------------------------------------

  type="page"
  case "$clean" in
    assets/*) type="asset" ;;
  esac

  # -----------------------------------------------------
  # PYTHON BLOCK (ISOLATED + LOGGED)
  # -----------------------------------------------------

  echo "🐍 extracting metadata for: $clean"

  PY_OUT=$(python3 - "$file" <<'PY'
import sys
import json
import re
from bs4 import BeautifulSoup
from collections import Counter

path = sys.argv[1]

try:
    html = open(path, encoding="utf-8").read()
except:
    html = ""

soup = BeautifulSoup(html, "html.parser")

title = ""
description = ""
body = ""
tags = []

try:
    if soup.title and soup.title.string:
        title = soup.title.string.strip()
except:
    pass

try:
    m = soup.find("meta", attrs={"name": "description"})
    if m and m.get("content"):
        description = m["content"].strip()
except:
    pass

try:
    body = soup.get_text(" ", strip=True)[:220]
except:
    pass

try:
    text = soup.get_text(" ", strip=True).lower()
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text)

    stop = {
        "the","and","for","with","that","this","from","you","are","was",
        "have","has","had","not","but","all","any","can","will","our",
        "into","over","under","between","about"
    }

    filtered = [w for w in words if w not in stop]
    tags = [w for w,_ in Counter(filtered).most_common(20)]
except:
    tags = []

print(json.dumps({
    "title": title,
    "description": description,
    "body": body,
    "tags": tags
}))
PY
) || {
    echo "❌ PYTHON FAILURE ON: $file"
    exit 1
}

TITLE=$(echo "$PY_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")
DESCRIPTION=$(echo "$PY_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['description'])")
BODY_SAMPLE=$(echo "$PY_OUT" | python3 -c "import sys,json; print(json.load(sys.stdin)['body'])")
TAG_JSON=$(echo "$PY_OUT" | python3 -c "import sys,json; print(json.dumps(json.load(sys.stdin)['tags']))")

# -----------------------------------------------------
# WRITE ENTRY
# -----------------------------------------------------

if [ "$FIRST" = true ]; then
  FIRST=false
else
  echo "," >> "$TMP"
fi

cat <<EOF >> "$TMP"
{
  "path": "$clean",
  "url": "$url",
  "type": "$type",
  "title": $(python3 -c "import json; print(json.dumps('''$TITLE'''))"),
  "description": $(python3 -c "import json; print(json.dumps('''$DESCRIPTION'''))"),
  "body_sample": $(python3 -c "import json; print(json.dumps('''$BODY_SAMPLE'''))"),
  "tags": $TAG_JSON
}
EOF

PROCESSED=$((PROCESSED+1))

done < "$TMP_FILES"

echo "checkpoint C: loop complete"

# =========================================================
# STEP 4 — FINALIZE JSON
# =========================================================

echo "]" >> "$TMP"
echo "}" >> "$TMP"

echo "checkpoint D: JSON closed"

# =========================================================
# STEP 5 — VALIDATION (STRICT + TRACEABLE)
# =========================================================

echo "🧪 validating registry..."

python3 - <<EOF
import json

path="$TMP"

with open(path) as f:
    data = json.load(f)

print("pages:", len(data.get("pages", [])))

assert "pages" in data
assert isinstance(data["pages"], list)
assert len(data["pages"]) > 0

for i,p in enumerate(data["pages"]):
    for k in ["path","url","type","title","description","body_sample","tags"]:
        if k not in p:
            raise Exception(f"Missing key {k} at index {i}")

print("✅ registry valid (v8 fully traced)")
EOF

echo "checkpoint E: validation passed"

# =========================================================
# STEP 6 — ATOMIC WRITE
# =========================================================

mv "$TMP" "$OUTPUT"
rm -f "$TMP_FILES"

echo "📦 registry entries: $PROCESSED"
echo "📁 wrote: $OUTPUT"
echo "✅ content registry built (v8 DIAGNOSTIC COMPLETE)"
