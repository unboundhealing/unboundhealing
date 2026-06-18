#!/bin/bash
set -e

echo "🔗 Building content graph (v3.2)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

INPUT="content-model.json"
OUTPUT="content-graph.json"

if [ ! -f "$INPUT" ]; then
  echo "❌ content-model.json not found. Run build-content-model.sh first."
  exit 1
fi

# ---------------------------------------
# Initialize graph structure
# ---------------------------------------
echo "{" > "$OUTPUT"
echo '"nodes": [' >> "$OUTPUT"

# Extract URLs as nodes
URLS=$(grep -o '"url": *"[^"]*"' "$INPUT" \
  | sed 's/"url": "//' \
  | sed 's/"//g' \
  | sort \
  | uniq)

FIRST=true

for url in $URLS; do

  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$OUTPUT"
  fi

  # Extract metadata
  TITLE=$(grep -A3 "$url" "$INPUT" | grep '"title"' | head -n1 | sed 's/.*": "//' | sed 's/".*//')
  TAGS=$(grep -A5 "$url" "$INPUT" | grep '"tags"' | head -n1 | sed 's/.*": "//' | sed 's/".*//')

  cat <<EOF >> "$OUTPUT"
{
  "url": "$url",
  "title": "$TITLE",
  "tags": "$TAGS"
}
EOF

done

echo "]," >> "$OUTPUT"
echo '"edges": [' >> "$OUTPUT"

# ---------------------------------------
# Build edges (tag-based relationships)
# ---------------------------------------

EDGE_FIRST=true

for url_a in $URLS; do
  TAGS_A=$(grep -A5 "$url_a" "$INPUT" | grep '"tags"' | head -n1 | sed 's/.*": "//' | sed 's/".*//')

  for url_b in $URLS; do
    if [ "$url_a" = "$url_b" ]; then
      continue
    fi

    TAGS_B=$(grep -A5 "$url_b" "$INPUT" | grep '"tags"' | head -n1 | sed 's/.*": "//' | sed 's/".*//')

    # ---------------------------------------
    # SIMPLE OVERLAP SCORE
    # ---------------------------------------
    SCORE=0

    for tag in $(echo "$TAGS_A" | tr ',' ' '); do
      echo "$TAGS_B" | grep -q "$tag" && SCORE=$((SCORE+1)) || true
    done

    if [ "$SCORE" -gt 0 ]; then

      if [ "$EDGE_FIRST" = true ]; then
        EDGE_FIRST=false
      else
        echo "," >> "$OUTPUT"
      fi

      cat <<EOF >> "$OUTPUT"
{
  "from": "$url_a",
  "to": "$url_b",
  "weight": $SCORE
}
EOF

    fi

  done
done

echo "]" >> "$OUTPUT"
echo "}" >> "$OUTPUT"

echo "✅ Content graph built (v3.2)"
