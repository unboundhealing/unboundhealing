#!/bin/bash
set -e

echo "🧠 Building content model (v3.3 normalized)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-model.json"

echo "{" > "$OUTPUT"
echo '"pages": [' >> "$OUTPUT"

FIRST=true

find . -type f -name "*.html" | while read -r file; do

  # ---------------------------------------
  # URL normalization
  # ---------------------------------------
  URL=$(echo "$file" \
    | sed 's|^\./||' \
    | sed 's|index.html||' \
    | sed 's|\.html$||')

  URL="https://unboundhealing.org/${URL}"

  # ---------------------------------------
  # TITLE
  # ---------------------------------------
  TITLE=$(python3 - <<EOF
from bs4 import BeautifulSoup

with open("$file", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

t = soup.title.string if soup.title else ""
print(t.strip() if t else "")
EOF
)

  # ---------------------------------------
  # DESCRIPTION
  # ---------------------------------------
  DESCRIPTION=$(python3 - <<EOF
from bs4 import BeautifulSoup

with open("$file", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

m = soup.find("meta", attrs={"name": "description"})
print(m["content"].strip() if m and m.get("content") else "")
EOF
)

  # ---------------------------------------
  # TAGS (stable + safe fallback)
  # ---------------------------------------
  TAGS=$(echo "$URL" | tr '/' '\n' | grep -v '^$' | tail -n +4 | paste -sd "," -)

  # ---------------------------------------
  # WRITE JSON ITEM
  # ---------------------------------------
  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$OUTPUT"
  fi

  cat <<EOF >> "$OUTPUT"
{
  "url": "$URL",
  "file": "$file",
  "title": "$TITLE",
  "description": "$DESCRIPTION",
  "tags": "$TAGS"
}
EOF

done

echo "]" >> "$OUTPUT"
echo "}" >> "$OUTPUT"

echo "✅ Content model built (v3.3 normalized)"
