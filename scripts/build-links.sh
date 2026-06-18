#!/bin/bash
set -e

echo "🔗 Building link intelligence layer (v3.1)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

INPUT="search-index.json"
OUTPUT="link-reference.md"

if [ ! -f "$INPUT" ]; then
  echo "❌ search-index.json not found"
  exit 1
fi

echo "# 🔗 UNBOUND HEALING LINK INTELLIGENCE" > "$OUTPUT"
echo "" >> "$OUTPUT"

# ---------------------------------------
# Extract all URLs (nodes)
# ---------------------------------------
URLS=$(grep -o '"url": *"[^"]*"' "$INPUT" \
  | sed 's/"url": "//' \
  | sed 's/"//g' \
  | sort \
  | uniq)

for url in $URLS; do

  echo "→ processing $url"

  # ---------------------------------------
  # Extract slug for matching relationships
  # ---------------------------------------
  SLUG=$(echo "$url" | sed 's|https://unboundhealing.org||')

  # ---------------------------------------
  # Find pages that mention this URL
  # (basic heuristic: occurrence in index)
  # ---------------------------------------
  INCOMING=$(grep -B5 -A5 "$url" "$INPUT" \
    | grep '"url"' \
    | sed -E 's/.*"(https[^"]+)".*/\1/' \
    | sort | uniq)

  # ---------------------------------------
  # Write section
  # ---------------------------------------
  echo "## $url" >> "$OUTPUT"
  echo "" >> "$OUTPUT"

  echo "### Incoming Links" >> "$OUTPUT"

  if [ -z "$INCOMING" ]; then
    echo "- None detected" >> "$OUTPUT"
  else
    for link in $INCOMING; do
      echo "- $link" >> "$OUTPUT"
    done
  fi

  echo "" >> "$OUTPUT"

  echo "### Outgoing Links (placeholder for future parser)" >> "$OUTPUT"
  echo "- (to be derived from HTML body parsing in v3.2)" >> "$OUTPUT"

  echo "" >> "$OUTPUT"

done

echo "✅ Link intelligence layer built (v3.1)"
