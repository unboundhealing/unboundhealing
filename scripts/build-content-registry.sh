#!/bin/bash
set -euo pipefail

echo "🧭 Building deterministic content registry (v5 full-enriched + CI-safe + schema-locked)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-registry.json"
TMP="content-registry.tmp.json"

# ---------------------------------------------------
# STEP 1 — DISCOVER FILES (HARD DETERMINISTIC ORDER)
# ---------------------------------------------------

echo "📂 scanning root: $(pwd)"

mapfile -t FILES < <(
  find . -type f -name "*.html" \
    ! -path "./.git/*" \
    ! -path "./.github/*" \
    | sort
)

echo "📦 html files discovered: ${#FILES[@]}"

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "❌ No HTML files found — aborting registry build"
  exit 1
fi

# ---------------------------------------------------
# STEP 2 — START JSON
# ---------------------------------------------------

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
COUNT=0

# ---------------------------------------------------
# STEP 3 — PROCESS FILES
# ---------------------------------------------------

for file in "${FILES[@]}"; do

  clean="${file#./}"

  # -----------------------------
  # URL NORMALIZATION
  # -----------------------------

  url_path=$(echo "$clean" \
    | sed 's|index.html$||' \
    | sed 's|\.html$||')

  url_path="${url_path#./}"
  url="https://unboundhealing.org/${url_path}"
  url=$(echo "$url" | sed 's|//|/|g' | sed 's|https:/|https://|')

  # -----------------------------
  # PYTHON ENRICHMENT (SINGLE PASS)
  # -----------------------------

  read -r TITLE DESCRIPTION BODY_SAMPLE TAGS <<EOF
$(python3 - "$file" <<'PY'
import sys
from bs4 import BeautifulSoup
import re
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

# TITLE
try:
    title = (soup.title.string or "").strip()
except:
    title = ""

# DESCRIPTION
try:
    m = soup.find("meta", attrs={"name": "description"})
    description = m["content"].strip() if m and m.get("content") else ""
except:
    description = ""

# BODY SAMPLE
try:
    text = soup.get_text(" ", strip=True)
    body_sample = text[:220]
except:
    body_sample = ""

# TAGS (stable + bounded)
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

import json

print(title.replace("\n"," ") + "\t" +
      description.replace("\n"," ") + "\t" +
      body_sample.replace("\n"," ") + "\t" +
      json.dumps(tags))
PY
)
EOF

  IFS=$'\t' read -r TITLE DESCRIPTION BODY_SAMPLE TAG_JSON <<< "$TITLE"

  # fallback safety
  TITLE="${TITLE:-}"
  DESCRIPTION="${DESCRIPTION:-}"
  BODY_SAMPLE="${BODY_SAMPLE:-}"
  TAG_JSON="${TAG_JSON:-[]}"

  # ---------------------------------------------------
  # WRITE ENTRY (STRICT SCHEMA)
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
  "type": "page",

  "title": $(python3 -c "import json; print(json.dumps('''$TITLE'''))"),
  "description": $(python3 -c "import json; print(json.dumps('''$DESCRIPTION'''))"),
  "body_sample": $(python3 -c "import json; print(json.dumps('''$BODY_SAMPLE'''))"),

  "tags": $TAG_JSON
}
EOF

  ((COUNT++))

done

# ---------------------------------------------------
# STEP 4 — CLOSE JSON
# ---------------------------------------------------

echo "]" >> "$TMP"
echo "}" >> "$TMP"

# ---------------------------------------------------
# STEP 5 — VALIDATION (HARD CONTRACT CHECK)
# ---------------------------------------------------

echo "🧪 validating registry..."

python3 - <<EOF
import json

with open("$TMP","r") as f:
    data = json.load(f)

assert "pages" in data
assert isinstance(data["pages"], list)

for p in data["pages"]:
    required = ["path","url","type","title","description","body_sample","tags"]
    for r in required:
        if r not in p:
            raise Exception("Missing key: " + r)

print("✅ registry valid (v5 schema-locked + fully enriched)")
EOF

# ---------------------------------------------------
# STEP 6 — ATOMIC WRITE
# ---------------------------------------------------

mv "$TMP" "$OUTPUT"

echo "📦 registry entries: $COUNT"
echo "📁 wrote: $OUTPUT"
echo "✅ content registry built (v5 schema-locked + deterministic + fully enriched)"
