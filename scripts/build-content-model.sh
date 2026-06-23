#!/bin/bash
set -e

echo "🧠 Building content model (v4.1 normalized + diagnostic pipeline)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-model.json"

# ==========================================================
# INIT OUTPUT
# ==========================================================

echo "{" > "$OUTPUT"
echo '  "pages": [' >> "$OUTPUT"

FIRST=true
PAGE_COUNT=0

# ==========================================================
# HTML DISCOVERY (SAFE ITERATION)
# ==========================================================

while IFS= read -r file; do

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
  # BODY SAMPLE (diagnostic-safe)
  # ---------------------------------------

  BODY_SAMPLE=$(python3 - <<EOF
from bs4 import BeautifulSoup

with open("$file", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

text = soup.get_text(" ", strip=True)
print(text[:300].replace("\n", " "))
EOF
)

  # ---------------------------------------
  # TAG EXTRACTION (ROBUST)
  # ---------------------------------------

  TAGS=$(python3 - <<EOF
from bs4 import BeautifulSoup

with open("$file", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f.read(), "html.parser")

# heuristic tag sources
raw = []

# 1. meta keywords
m = soup.find("meta", attrs={"name": "keywords"})
if m and m.get("content"):
    raw.extend(m["content"].split(","))

# 2. headings (light weight)
for h in soup.find_all(["h1", "h2"]):
    raw.append(h.get_text())

# normalize
clean = []
for t in raw:
    if not t:
        continue
    t = str(t).strip().lower()
    t = t.replace(" ", "-")
    if len(t) < 2:
        continue
    clean.append(t)

# dedupe preserve order
seen = set()
out = []
for t in clean:
    if t not in seen:
        seen.add(t)
        out.append(t)

print(out)
EOF
)

  # ---------------------------------------
  # WRITE PAGE OBJECT
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
    "body_sample": "$BODY_SAMPLE",
    "tags": $TAGS
  }
EOF

  PAGE_COUNT=$((PAGE_COUNT + 1))

done < <(find . -type f -name "*.html")

# ==========================================================
# CLOSE JSON
# ==========================================================

echo "" >> "$OUTPUT"
echo "  ]" >> "$OUTPUT"
echo "}" >> "$OUTPUT"

# ==========================================================
# SUMMARY REPORT
# ==========================================================

echo ""
echo "🧪 CONTENT MODEL DIAGNOSTICS"
echo "📦 pages processed: $PAGE_COUNT"
echo "📁 output: $OUTPUT"
echo "✅ content model built (v4.1 normalized + diagnostic pipeline)"
