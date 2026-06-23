#!/bin/bash
set -euo pipefail

echo "🧭 Building deterministic content registry (v2 hardened + CI-safe)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-registry.json"
TMP="content-registry.tmp.json"

# ---------------------------------------------------
# STEP 1 — DETECT FILES (SAFE + ROOT-STABLE)
# ---------------------------------------------------

echo "📂 scanning root: $(pwd)"

mapfile -t RAW_FILES < <(
  find . -type f -name "*.html" \
    ! -path "./.git/*" \
    ! -path "./.github/*" \
    ! -path "./scripts/*" \
    | sort
)

echo "📦 html files discovered: ${#RAW_FILES[@]}"

# ---------------------------------------------------
# SAFETY CHECK (CRITICAL)
# ---------------------------------------------------

if [ "${#RAW_FILES[@]}" -eq 0 ]; then
  echo "❌ registry scan returned ZERO HTML files"
  echo "💡 check CI checkout path or working directory"
  exit 1
fi

# ---------------------------------------------------
# STEP 2 — BUILD REGISTRY
# ---------------------------------------------------

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
COUNT=0

for file in "${RAW_FILES[@]}"; do

  # normalize path (single consistent format)
  clean="${file#./}"

  # skip accidental empty
  if [ -z "$clean" ]; then
    continue
  fi

  # ---------------------------------------------------
  # URL NORMALIZATION (CANONICAL ROUTING)
  # ---------------------------------------------------

  url_path=$(echo "$clean" \
    | sed 's|index.html$||' \
    | sed 's|\.html$||')

  # ensure leading slash safety normalization
  url_path="${url_path#./}"
  url="https://unboundhealing.org/${url_path}"

  # remove accidental double slashes
  url=$(echo "$url" | sed 's|//|/|g' | sed 's|https:/|https://|')

  # ---------------------------------------------------
  # TYPE CLASSIFICATION (NON-RESTRICTIVE)
  # ---------------------------------------------------

  type="page"

  if [[ "$clean" == assets/* ]]; then
    type="asset"
  fi

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
  "type": "$type"
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
# VALIDATION (HARD FAIL SAFE)
# ---------------------------------------------------

echo "🧪 validating registry..."

python3 - <<EOF
import json
with open("$TMP","r") as f:
    json.load(f)
print("✅ registry valid")
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
echo "✅ content registry built (v2 deterministic + CI-safe)"
