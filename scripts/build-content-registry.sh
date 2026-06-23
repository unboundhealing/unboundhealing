#!/bin/bash
set -euo pipefail

echo "🧭 Building deterministic content registry (v6 contract-safe + path-normalized)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-registry.json"
TMP="content-registry.tmp.json"

# ---------------------------------------------------
# STEP 1 — DISCOVER FILES (DETERMINISTIC + SAFE)
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
  echo "❌ No HTML files found — aborting registry build"
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
# STEP 3 — BUILD ENTRIES
# ---------------------------------------------------

for file in "${FILES[@]}"; do

  # -----------------------------
  # CANONICAL PATH NORMALIZATION
  # -----------------------------
  clean="${file#./}"
  clean="${clean#./}"

  # force absolute safety (no leading ./ or /)
  clean=$(echo "$clean" | sed 's|^\./||' | sed 's|^/||')

  # skip empty safety
  if [ -z "$clean" ]; then
    continue
  fi

  # -----------------------------
  # URL NORMALIZATION
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

  # -----------------------------
  # WRITE ENTRY
  # -----------------------------
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
# STEP 4 — CLOSE JSON
# ---------------------------------------------------

echo "]" >> "$TMP"
echo "}" >> "$TMP"

# ---------------------------------------------------
# STEP 5 — VALIDATION (STRICT)
# ---------------------------------------------------

echo "🧪 validating registry..."

python3 - <<EOF
import json

with open("$TMP","r") as f:
    data = json.load(f)

assert "pages" in data
assert isinstance(data["pages"], list)

for p in data["pages"]:
    for k in ["path","url","type"]:
        if k not in p:
            raise Exception("Missing key: " + k)

print("✅ registry valid (v6 contract-safe)")
EOF

# ---------------------------------------------------
# STEP 6 — ATOMIC WRITE
# ---------------------------------------------------

mv "$TMP" "$OUTPUT"

echo "📦 registry entries: $COUNT"
echo "📁 wrote: $OUTPUT"
echo "✅ registry built (v6 contract-safe + normalized paths)"
