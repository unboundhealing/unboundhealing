#!/bin/bash
set -euo pipefail

echo "🧠 Building content model (v4.3 hardened JSON-safe pipeline)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-model.json"
TMP_OUTPUT="content-model.tmp.json"

echo "🧠 Scanning HTML files..."

# ---------------------------------------
# Collect files in stable order (CRITICAL for reproducibility)
# ---------------------------------------
mapfile -t FILES < <(find . -type f -name "*.html" | sort)

TOTAL=${#FILES[@]}
echo "📦 pages discovered: $TOTAL"

# ---------------------------------------
# Start JSON (atomic build)
# ---------------------------------------
echo "{" > "$TMP_OUTPUT"
echo '"pages": [' >> "$TMP_OUTPUT"

FIRST=true
PROCESSED=0

# ---------------------------------------
# Process each file
# ---------------------------------------
for file in "${FILES[@]}"; do
  ((PROCESSED++))

  # ---------------------------------------
  # Normalize URL
  # ---------------------------------------
  URL=$(echo "$file" \
    | sed 's|^\./||' \
    | sed 's|index.html$||' \
    | sed 's|\.html$||')

  URL="https://unboundhealing.org/${URL}"

  # ---------------------------------------
  # Extract title safely
  # ---------------------------------------
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

  # ---------------------------------------
  # Extract description safely
  # ---------------------------------------
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

  # ---------------------------------------
  # BODY SAMPLE (limited + safe)
  # ---------------------------------------
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

  # ---------------------------------------
  # TAG GENERATION (stable + bounded)
  # ---------------------------------------
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

    tags = [w for w,_ in counts.most_common(20)]

    print(",".join(tags))

except Exception:
    print("")
EOF
)

  # Convert tags string → JSON array
  TAG_JSON=$(python3 - <<EOF
import json, sys
tags = sys.stdin.read().strip()
if not tags:
    print("[]")
else:
    arr = [t.strip() for t in tags.split(",") if t.strip()]
    print(json.dumps(arr))
EOF
<<< "$TAGS")

  # ---------------------------------------
  # WRITE ENTRY
  # ---------------------------------------
  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$TMP_OUTPUT"
  fi

  cat <<EOF >> "$TMP_OUTPUT"
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

# ---------------------------------------
# CLOSE JSON
# ---------------------------------------
echo "]" >> "$TMP_OUTPUT"
echo "}" >> "$TMP_OUTPUT"

# ---------------------------------------
# VALIDATION STEP (prevents graph crash)
# ---------------------------------------
echo "🧪 validating JSON..."

python3 - <<EOF
import json
with open("$TMP_OUTPUT","r") as f:
    json.load(f)
print("✅ JSON valid")
EOF

# ---------------------------------------
# ATOMIC WRITE (CRITICAL FIX)
# ---------------------------------------
mv "$TMP_OUTPUT" "$OUTPUT"

echo "✅ Content model built (v4.3 hardened JSON-safe pipeline)"
echo "📁 output: $OUTPUT"
echo "📦 pages processed: $TOTAL"
