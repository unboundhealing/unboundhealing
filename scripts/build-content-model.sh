#!/bin/bash
set -euo pipefail

echo "🧠 Building content model (v6 declarative registry + deterministic pipeline)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

REGISTRY="content-registry.json"
MODEL="content-model.json"
TMP_MODEL="content-model.tmp.json"

# -------------------------------------------------------
# STEP 0 — DETERMINE CONTENT SURFACE (NON-RESTRICTIVE)
# -------------------------------------------------------
# We are NOT blocking access. We are simply defining what
# belongs to "content surface" vs "system/internal surface".

echo "🧭 Building deterministic content registry..."

mapfile -t RAW_FILES < <(find . -type f -name "*.html" | sort)

INCLUDE_PATTERNS=(
  "./assets/"
  "./concept/"
  "./about/"
  "./opening/"
  "./noticing/"
  "./listening/"
  "./gathering/"
  "./supporting/"
  "./inviting/"
  "./index.html"
  "./welcome/"
  "./feed.xml"
  "./sitemap.xml"
)

is_included() {
  local file="$1"
  for pattern in "${INCLUDE_PATTERNS[@]}"; do
    if [[ "$file" == *"$pattern"* ]]; then
      return 0
    fi
  done
  return 1
}

# -------------------------------------------------------
# BUILD REGISTRY (DETERMINISTIC SOURCE OF TRUTH)
# -------------------------------------------------------

echo "{" > "$REGISTRY"
echo '"included_files": [' >> "$REGISTRY"

FIRST=true
INCLUDED_COUNT=0

for file in "${RAW_FILES[@]}"; do
  # normalize
  CLEAN_FILE="${file#./}"

  if is_included "$CLEAN_FILE"; then
    if [ "$FIRST" = true ]; then
      FIRST=false
    else
      echo "," >> "$REGISTRY"
    fi

    HASH=$(echo -n "$CLEAN_FILE" | shasum -a 256 | awk '{print $1}')

    cat <<EOF >> "$REGISTRY"
{
  "file": "$CLEAN_FILE",
  "hash": "$HASH"
}
EOF

    ((INCLUDED_COUNT++))
  fi
done

echo "]" >> "$REGISTRY"
echo "}" >> "$REGISTRY"

echo "📦 registry entries: $INCLUDED_COUNT"

# -------------------------------------------------------
# VALIDATE REGISTRY
# -------------------------------------------------------
echo "🧪 validating registry..."

python3 - <<EOF
import json
with open("$REGISTRY") as f:
    json.load(f)
print("✅ registry valid")
EOF

# -------------------------------------------------------
# STEP 1 — LOAD REGISTERED FILES ONLY
# -------------------------------------------------------
echo "🧠 Building content model from registry..."

mapfile -t FILES < <(python3 - <<EOF
import json

with open("$REGISTRY") as f:
    data = json.load(f)

files = [x["file"] for x in data["included_files"]]
files.sort()
print("\n".join(files))
EOF
)

TOTAL=${#FILES[@]}
echo "📦 pages discovered (registry-controlled): $TOTAL"

# -------------------------------------------------------
# STEP 2 — BUILD MODEL
# -------------------------------------------------------
echo "{" > "$TMP_MODEL"
echo '"pages": [' >> "$TMP_MODEL"

FIRST=true
PROCESSED=0

for file in "${FILES[@]}"; do
  ((PROCESSED++))

  URL=$(echo "$file" \
    | sed 's|^\./||' \
    | sed 's|index.html$||' \
    | sed 's|\.html$||')

  URL="https://unboundhealing.org/${URL}"

  # -------------------------
  # TITLE
  # -------------------------
  TITLE=$(python3 - "$file" <<'EOF'
import sys
from bs4 import BeautifulSoup

path = sys.argv[1]

try:
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")
    print((soup.title.string or "").strip())
except Exception:
    print("")
EOF
)

  # -------------------------
  # DESCRIPTION
  # -------------------------
  DESCRIPTION=$(python3 - "$file" <<'EOF'
import sys
from bs4 import BeautifulSoup

path = sys.argv[1]

try:
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    m = soup.find("meta", attrs={"name": "description"})
    if m and m.get("content"):
        print(m["content"].strip())
    else:
        print("")
except Exception:
    print("")
EOF
)

  # -------------------------
  # BODY SAMPLE
  # -------------------------
  BODY_SAMPLE=$(python3 - "$file" <<'EOF'
import sys
from bs4 import BeautifulSoup

path = sys.argv[1]

try:
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    text = soup.get_text(" ", strip=True)
    print(text[:200].replace("\n", " "))
except Exception:
    print("")
EOF
)

  # -------------------------
  # TAGS (deterministic)
  # -------------------------
  TAGS=$(python3 - "$file" <<'EOF'
import sys
from bs4 import BeautifulSoup
import re
from collections import Counter

path = sys.argv[1]

try:
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    text = soup.get_text(" ", strip=True).lower()
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text)

    stop = {
        "the","and","for","with","that","this","from","you","are","was",
        "have","has","had","not","but","all","any","can","will","our"
    }

    filtered = [w for w in words if w not in stop]
    counts = Counter(filtered)

    tags = sorted([w for w,_ in counts.most_common(20)])
    print(",".join(tags))

except Exception:
    print("")
EOF
)

  TAG_JSON=$(python3 - <<EOF
import json, sys
tags = sys.stdin.read().strip()
if not tags:
    print("[]")
else:
    print(json.dumps([t.strip() for t in tags.split(",") if t.strip()]))
EOF
<<< "$TAGS")

  # -------------------------
  # WRITE ENTRY
  # -------------------------
  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$TMP_MODEL"
  fi

  cat <<EOF >> "$TMP_MODEL"
{
  "url": "$URL",
  "file": "$file",
  "title": $(python3 -c "import json; print(json.dumps('''$TITLE'''))"),
  "description": $(python3 -c "import json; print(json.dumps('''$DESCRIPTION'''))"),
  "body_sample": $(python3 -c "import json; print(json.dumps('''$BODY_SAMPLE'''))"),
  "tags": $TAG_JSON
}
EOF

  echo "✨ processed ($PROCESSED/$TOTAL): $URL"

done

# -------------------------------------------------------
# FINALIZE MODEL
# -------------------------------------------------------
echo "]" >> "$TMP_MODEL"
echo "}" >> "$TMP_MODEL"

echo "🧪 validating JSON..."

python3 - <<EOF
import json
with open("$TMP_MODEL") as f:
    json.load(f)
print("✅ JSON valid")
EOF

mv "$TMP_MODEL" "$MODEL"

# -------------------------------------------------------
# SUMMARY OUTPUT
# -------------------------------------------------------
echo "✅ Content model built (v6 deterministic registry system)"
echo "📁 model: $MODEL"
echo "📁 registry: $REGISTRY"
echo "📦 pages processed: $TOTAL"
