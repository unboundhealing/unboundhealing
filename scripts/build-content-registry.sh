#!/bin/bash
set -euo pipefail

echo "🧭 Building deterministic content registry..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-registry.json"
TMP="content-registry.tmp.json"

# -----------------------------
# deterministic file scan rules
# -----------------------------
mapfile -t FILES < <(find . -type f -name "*.html" | sort)

echo "📦 files discovered: ${#FILES[@]}"

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
COUNT=0

for file in "${FILES[@]}"; do

  # normalize exclusions (IMPORTANT: NOT restrictive on content)
  if [[ "$file" == ./.git/* ]] || [[ "$file" == ./.github/* ]]; then
    continue
  fi

  # strip leading ./
  clean="${file#./}"

  # URL normalization
  url=$(echo "$clean" | sed 's|index.html$||' | sed 's|\.html$||')
  url="https://unboundhealing.org/${url}"

  # basic page classification (non-restrictive)
  type="page"
  if [[ "$clean" == assets/* ]]; then
    type="asset"
  fi

  if [ "$FIRST" = true ]; then
    FIRST=false
  else
    echo "," >> "$TMP"
  fi

  cat <<EOF >> "$TMP"
{
  "path": "$clean",
  "url": "$url",
  "type": "$type"
}
EOF

  ((COUNT++))

done

echo "]" >> "$TMP"
echo "}" >> "$TMP"

echo "🧪 validating registry..."

python3 - <<EOF
import json
json.load(open("$TMP"))
print("✅ registry valid")
EOF

mv "$TMP" "$OUTPUT"

echo "📦 registry entries: $COUNT"
echo "📁 wrote: $OUTPUT"
echo "✅ content registry built"
