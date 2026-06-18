#!/bin/bash
set -e

echo "🧠 Building content model (v3.2)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-model.json"

echo "{" > "$OUTPUT"

FIRST=true

find . -type f -name "*.html" | while read -r file; do

  # ---------------------------------------
  # Convert file path → canonical URL
  # ---------------------------------------
  URL=$(echo "$file" \
    | sed 's|^\./||' \
    | sed 's|index.html||' \
    | sed 's|\.html$||')

  URL="https://unboundhealing.org/${URL}"

  # ---------------------------------------
  # REAL STRUCTURED EXTRACTION (v3.2 upgrade)
  # ---------------------------------------
  TITLE=$(python3 - <<EOF
from bs4 import BeautifulSoup

with open("$file", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

title = soup.title.string if soup.title else ""
print(title.strip() if title else "")
EOF
)

  DESCRIPTION=$(python3 - <<EOF
from bs4 import BeautifulSoup

with open("$file", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

meta = soup.find("meta", attrs={"name": "description"})
print(meta["content"].strip() if meta and meta.get("content") else "")
EOF
)

  # ---------------------------------------
  # TAG EXTRACTION (light heuristic for now)
  # ---------------------------------------
  TAGS=$(echo "$URL" | tr '/' '\n' | grep -v '^$' | tail -n +4 | paste -sd "," -)

  # ---------------------------------------
  # JSON SAFE OUTPUT
  # ---------------------------------------
  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$OUTPUT"
  fi

  cat <<EOF >> "$OUTPUT"
"$URL": {
  "file": "$file",
  "title": "$TITLE",
  "description": "$DESCRIPTION",
  "tags": "$TAGS",
  "url": "$URL"
}
EOF

done

echo "}" >> "$OUTPUT"

echo "✅ Content model built (v3.2)"
