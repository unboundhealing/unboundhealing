#!/bin/bash
set -euo pipefail

echo "🧭 Building deterministic content registry (v7 streaming + CI-safe + zero array model)..."

ROOT_DIR="${GITHUB_WORKSPACE:-$(pwd)}"
cd "$ROOT_DIR"

OUTPUT="content-registry.json"
TMP="content-registry.tmp.json"
TMP_FILES="$(mktemp)"

# ---------------------------------------------------
# STEP 1 — FILE DISCOVERY (STREAMING ONLY, NO ARRAYS)
# ---------------------------------------------------

echo "📂 scanning root: $(pwd)"

# deterministic file list (no arrays, no pipefail traps)
find . -type f -name "*.html" \
  ! -path "./.git/*" \
  ! -path "./.github/*" \
  ! -path "./scripts/*" \
  2>/dev/null \
  | sort > "$TMP_FILES" || true

COUNT=$(wc -l < "$TMP_FILES" | tr -d ' ')

echo "📦 html files discovered: $COUNT"

if [ "$COUNT" -eq 0 ]; then
  echo "❌ No HTML files found — aborting registry build"
  exit 1
fi

# ---------------------------------------------------
# STEP 2 — INIT JSON OUTPUT
# ---------------------------------------------------

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
PROCESSED=0

# ---------------------------------------------------
# STEP 3 — STREAM PROCESSING LOOP
# ---------------------------------------------------

while IFS= read -r file; do

  # safety guard
  if [ -z "${file:-}" ]; then
    continue
  fi

  clean="${file#./}"

  # skip empty after normalization
  if [ -z "$clean" ]; then
    continue
  fi

  # ---------------------------------------------------
  # URL NORMALIZATION
  # ---------------------------------------------------

  url_path="${clean%index.html}"
  url_path="${url_path%.html}"

  url="https://unboundhealing.org/${url_path}"
  url=$(echo "$url" | sed 's|//|/|g' | sed 's|https:/|https://|')

  # ---------------------------------------------------
  # TYPE CLASSIFICATION
  # ---------------------------------------------------

  type="page"
  if [[ "$clean" == assets/* ]]; then
    type="asset"
  fi

  # ---------------------------------------------------
  # PYTHON ENRICHMENT (SINGLE PASS, SAFE OUTPUT)
  # ---------------------------------------------------

  read -r TITLE DESCRIPTION BODY_SAMPLE TAG_JSON <<EOF
$(python3 - "$file" <<'PY'
import sys
import json
import re
from bs4 import BeautifulSoup
from collections import Counter

path = sys.argv[1]

def safe_read():
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

html = safe_read()
soup = BeautifulSoup(html, "html.parser")

# title
try:
    title = (soup.title.string or "").strip()
except:
    title = ""

# description
try:
    m = soup.find("meta", attrs={"name": "description"})
    description = m["content"].strip() if m and m.get("content") else ""
except:
    description = ""

# body sample
try:
    text = soup.get_text(" ", strip=True)
    body_sample = text[:220]
except:
    body_sample = ""

# tags (stable deterministic)
try:
    text = soup.get_text(" ", strip=True).lower()
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text)

    stop = {
        "the","and","for","with","that","this","from","you","are","was",
        "have","has","had","not","but","all","any","can","will","our",
        "into","over","under","between","about"
    }

    filtered = [w for w in words if w not in stop]
    counts = Counter(filtered)
    tags = [w for w,_ in counts.most_common(20)]
except:
    tags = []

print(
    title.replace("\n"," ") + "\t" +
    description.replace("\n"," ") + "\t" +
    body_sample.replace("\n"," ") + "\t" +
    json.dumps(tags)
)
PY
)
EOF

  IFS=$'\t' read -r TITLE DESCRIPTION BODY_SAMPLE TAG_JSON <<< "$TITLE"

  # ---------------------------------------------------
  # FINAL SAFETY NORMALIZATION
  # ---------------------------------------------------

  TITLE="${TITLE:-}"
  DESCRIPTION="${DESCRIPTION:-}"
  BODY_SAMPLE="${BODY_SAMPLE:-}"
  TAG_JSON="${TAG_JSON:-[]}"

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
  "path": "$clean",
  "url": "$url",
  "type": "$type",
  "title": $(python3 -c "import json; print(json.dumps('''$TITLE'''))"),
  "description": $(python3 -c "import json; print(json.dumps('''$DESCRIPTION'''))"),
  "body_sample": $(python3 -c "import json; print(json.dumps('''$BODY_SAMPLE'''))"),
  "tags": $TAG_JSON
}
EOF

  ((PROCESSED++))

done < "$TMP_FILES"

# ---------------------------------------------------
# STEP 4 — FINALIZE JSON
# ---------------------------------------------------

echo "]" >> "$TMP"
echo "}" >> "$TMP"

# ---------------------------------------------------
# STEP 5 — VALIDATION (STRICT)
# ---------------------------------------------------

echo "🧪 validating registry..."

python3 - <<EOF
import json

with open("$TMP","r") as f:
    data = json.load(f)

assert "pages" in data
assert isinstance(data["pages"], list)
assert len(data["pages"]) > 0

for p in data["pages"]:
    for k in ["path","url","type","title","description","body_sample","tags"]:
        if k not in p:
            raise Exception(f"Missing key: {k}")

print("✅ registry valid (v7 streaming + CI-safe + deterministic)")
EOF

# ---------------------------------------------------
# STEP 6 — ATOMIC WRITE
# ---------------------------------------------------

mv "$TMP" "$OUTPUT"

rm -f "$TMP_FILES"

# ---------------------------------------------------
# STEP 7 — SUMMARY
# ---------------------------------------------------

echo "📦 registry entries: $PROCESSED"
echo "📁 wrote: $OUTPUT"
echo "✅ content registry built (v7 streaming, zero arrays, CI-stable)"
