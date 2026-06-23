#!/bin/bash
set -euo pipefail

echo "🧭 Building deterministic content registry (v4 semantic-first + CI-safe + fully enriched)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-registry.json"
TMP="content-registry.tmp.json"

# ---------------------------------------------------
# STEP 1 — DISCOVER FILES (DETERMINISTIC)
# ---------------------------------------------------

echo "📂 scanning root: $(pwd)"

mapfile -t FILES < <(
  find . -type f -name "*.html" \
    ! -path "./.git/*" \
    ! -path "./.github/*" \
    ! -path "./scripts/*" \
    | sort
)

echo "📦 html files discovered: ${#FILES[@]}"

if [ "${#FILES[@]}" -eq 0 ]; then
  echo "❌ no HTML files found — aborting registry build"
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
# STEP 3 — PROCESS FILES (SEMANTIC EXTRACTION)
# ---------------------------------------------------

for file in "${FILES[@]}"; do

  clean="${file#./}"

  # -----------------------------
  # URL normalization
  # -----------------------------
  url_path=$(echo "$clean" \
    | sed 's|index.html$||' \
    | sed 's|\.html$||')

  url="https://unboundhealing.org/${url_path}"
  url=$(echo "$url" | sed 's|//|/|g' | sed 's|https:/|https://|')

  # -----------------------------
  # TYPE
  # -----------------------------
  type="page"
  if [[ "$clean" == assets/* ]]; then
    type="asset"
  fi

  # ---------------------------------------------------
  # SEMANTIC EXTRACTION (TITLE / DESCRIPTION / BODY / TAGS)
  # ---------------------------------------------------

  read -r TITLE DESCRIPTION BODY_SAMPLE TAGS_JSON < <(
    python3 - "$file" <<'EOF'
import sys, json, re
from bs4 import BeautifulSoup
from collections import Counter

path = sys.argv[1]

try:
    with open(path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    # ---------------- title ----------------
    title = (soup.title.string if soup.title else "") or ""
    title = title.strip()

    # ---------------- description ----------------
    desc = ""
    m = soup.find("meta", attrs={"name": "description"})
    if m and m.get("content"):
        desc = m["content"].strip()

    # ---------------- body sample ----------------
    text = soup.get_text(" ", strip=True)
    body = text[:240].replace("\n", " ")

    # ---------------- tags ----------------
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]{2,}", text.lower())

    stop = {
        "the","and","for","with","that","this","from","you","are","was",
        "have","has","had","not","but","all","any","can","will","our",
        "into","over","under","than","then","them","they","there"
    }

    filtered = [w for w in words if w not in stop]
    counts = Counter(filtered)

    tags = [w for w,_ in counts.most_common(20)]

    print(title)
    print(desc)
    print(body)
    print(json.dumps(tags))

except Exception:
    print("")
    print("")
    print("")
    print("[]")
EOF
  )

  # ---------------------------------------------------
  # JSON SAFE FIELDS
  # ---------------------------------------------------

  TITLE=$(python3 -c "import json; print(json.dumps('''$TITLE'''))")
  DESCRIPTION=$(python3 -c "import json; print(json.dumps('''$DESCRIPTION'''))")
  BODY_SAMPLE=$(python3 -c "import json; print(json.dumps('''$BODY_SAMPLE'''))")

  # TAGS already JSON-safe
  TAGS_JSON=${TAGS_JSON:-"[]"}

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
  "title": $TITLE,
  "description": $DESCRIPTION,
  "body_sample": $BODY_SAMPLE,
  "tags": $TAGS_JSON
}
EOF

  ((COUNT++))

done

# ---------------------------------------------------
# CLOSE JSON
# ---------------------------------------------------

echo "]" >> "$TMP"
echo "}" >> "$TMP"

# ---------------------------------------------------
# VALIDATION (STRICT)
# ---------------------------------------------------

echo "🧪 validating registry..."

python3 - <<EOF
import json

with open("$TMP","r") as f:
    data = json.load(f)

assert "pages" in data
assert isinstance(data["pages"], list)

for p in data["pages"]:
    assert "url" in p
    assert "title" in p
    assert "tags" in p

print("✅ registry valid (v4 semantic-first)")
EOF

# ---------------------------------------------------
# ATOMIC WRITE
# ---------------------------------------------------

mv "$TMP" "$OUTPUT"

# ---------------------------------------------------
# SUMMARY
# ---------------------------------------------------

echo "📦 registry entries: $COUNT"
echo "📁 wrote: $OUTPUT"
echo "✅ content registry built (v4 semantic-first deterministic + CI-safe + model-ready)"
