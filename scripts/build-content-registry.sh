#!/bin/bash
set -euo pipefail

echo "🧭 Building deterministic content registry (v6 CI-hardened + fully deterministic)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="content-registry.json"
TMP="content-registry.tmp.json"

# ---------------------------------------------------
# STEP 1 — DISCOVER FILES (CI-SAFE, NO MAPFILE)
# ---------------------------------------------------

echo "📂 scanning root: $(pwd)"

FILES=()

while IFS= read -r f; do
  # defensive guard
  [[ -z "${f:-}" ]] && continue

  FILES+=("$f")
done < <(
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
# STEP 2 — INIT JSON
# ---------------------------------------------------

echo "{" > "$TMP"
echo '"pages": [' >> "$TMP"

FIRST=true
COUNT=0

# ---------------------------------------------------
# STEP 3 — BUILD ENTRIES
# ---------------------------------------------------

for file in "${FILES[@]}"; do

  # safety guard (CRITICAL under set -u)
  if [[ -z "${file:-}" ]]; then
    continue
  fi

  # normalize path
  clean="${file#./}"
  clean="${clean#./}"

  if [[ -z "$clean" ]]; then
    continue
  fi

  # ---------------------------------------------------
  # URL NORMALIZATION (CANONICAL)
  # ---------------------------------------------------

  url_path=$(echo "$clean" \
    | sed 's|index.html$||' \
    | sed 's|\.html$||')

  url="https://unboundhealing.org/${url_path}"

  # collapse accidental slashes
  url=$(echo "$url" | sed 's|//|/|g' | sed 's|https:/|https://|')

  # ---------------------------------------------------
  # TYPE CLASSIFICATION (NON-RESTRICTIVE)
  # ---------------------------------------------------

  type="page"
  if [[ "$clean" == assets/* ]]; then
    type="asset"
  fi

  # ---------------------------------------------------
  # WRITE JSON ENTRY (SAFE + DETERMINISTIC)
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
# STEP 4 — CLOSE JSON
# ---------------------------------------------------

echo "]" >> "$TMP"
echo "}" >> "$TMP"

# ---------------------------------------------------
# STEP 5 — VALIDATION (HARD GUARANTEE)
# ---------------------------------------------------

echo "🧪 validating registry..."

python3 - <<EOF
import json

with open("$TMP","r") as f:
    data = json.load(f)

if "pages" not in data:
    raise Exception("Missing 'pages' key")

if not isinstance(data["pages"], list):
    raise Exception("'pages' must be a list")

if len(data["pages"]) == 0:
    raise Exception("Registry is empty")

for p in data["pages"]:
    for k in ["path", "url", "type"]:
        if k not in p:
            raise Exception(f"Missing key: {k}")

print("✅ registry valid (v6 CI-hardened + deterministic)")
EOF

# ---------------------------------------------------
# STEP 6 — ATOMIC WRITE
# ---------------------------------------------------

mv "$TMP" "$OUTPUT"

# ---------------------------------------------------
# STEP 7 — SUMMARY
# ---------------------------------------------------

echo "📦 registry entries: $COUNT"
echo "📁 wrote: $OUTPUT"
echo "✅ content registry built (v6 CI-hardened + fully deterministic + zero mapfile + zero subshell risk)"
