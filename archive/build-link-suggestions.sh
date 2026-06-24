#!/bin/bash
set -e

echo "🔗 Building internal link suggestions (v3.2)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

INPUT="content-graph.json"
OUTPUT="link-suggestions.json"

if [ ! -f "$INPUT" ]; then
  echo "❌ content-graph.json not found. Run build-content-graph.sh first."
  exit 1
fi

echo "{" > "$OUTPUT"

# ---------------------------------------
# Extract nodes
# ---------------------------------------
URLS=$(grep -o '"url": *"[^"]*"' "$INPUT" \
  | sed 's/"url": "//' \
  | sed 's/"//g' \
  | sort | uniq)

FIRST=true

for url in $URLS; do

  # ---------------------------------------
  # Find strongest edges for this node
  # ---------------------------------------
  MATCHES=$(grep -A5 "\"from\": \"$url\"" "$INPUT" \
    | grep -B5 '"weight":' \
    | grep '"to"' \
    | sed 's/.*": "//' \
    | sed 's/".*//' \
    | sort | uniq)

  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$OUTPUT"
  fi

  echo "\"$url\": [" >> "$OUTPUT"

  INNER_FIRST=true

  for match in $MATCHES; do
    if [ "$INNER_FIRST" = true ]; then
      INNER_FIRST=false
    else
      echo "," >> "$OUTPUT"
    fi

    echo "  \"$match\"" >> "$OUTPUT"
  done

  echo "]" >> "$OUTPUT"

done

echo "}" >> "$OUTPUT"

echo "✅ Link suggestions generated (v3.2)"
