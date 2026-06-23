#!/bin/bash
# ARCHIVED 2026-06
# Replaced by semantic-salience → inject-related-content.py
# Retained only for historical reference.

set -e

echo "🔗 Applying internal link suggestions (v3.2)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

INPUT="link-suggestions.json"

if [ ! -f "$INPUT" ]; then
  echo "❌ link-suggestions.json not found"
  exit 1
fi

# ---------------------------------------
# Extract all source pages
# ---------------------------------------
PAGES=$(grep -o '"https://unboundhealing.org[^"]*"' "$INPUT" \
  | sort | uniq)

for page in $PAGES; do

  FILE_PATH=$(echo "$page" \
    | sed 's|https://unboundhealing.org|.|' \
    | sed 's|/$|/index.html|' \
    | sed 's|^./|./|')

  if [ ! -f "$FILE_PATH" ]; then
    continue
  fi

  echo "→ processing $FILE_PATH"

  # ---------------------------------------
  # Extract target links
  # ---------------------------------------
  LINKS=$(grep -A20 "$page" "$INPUT" \
    | grep -o '"https://unboundhealing.org[^"]*"' \
    | sort | uniq)

  if [ -z "$LINKS" ]; then
    continue
  fi

  TMP_FILE="${FILE_PATH}.tmp"

  cp "$FILE_PATH" "$TMP_FILE"

  for link in $LINKS; do

    # ---------------------------------------
    # Convert URL → relative path
    # ---------------------------------------
    REL=$(echo "$link" \
      | sed 's|https://unboundhealing.org||')

    # Skip self-links
    if [[ "$REL" == "$(echo "$page" | sed 's|https://unboundhealing.org||')" ]]; then
      continue
    fi

    # ---------------------------------------
    # ONLY inject if not already present
    # ---------------------------------------
    if ! grep -q "$REL" "$TMP_FILE"; then

      echo "🔗 injecting $REL into $FILE_PATH"

      # Insert before closing </main> if exists
      if grep -q "</main>" "$TMP_FILE"; then
        sed -i '' "s|</main>|<p class=\"auto-link\">Related: <a href=\"$REL\">$REL</a></p></main>|" "$TMP_FILE"
      else
        # fallback: append at end
        echo "<p class=\"auto-link\">Related: <a href=\"$REL\">$REL</a></p>" >> "$TMP_FILE"
      fi
    fi

  done

  mv "$TMP_FILE" "$FILE_PATH"

done

echo "✅ Internal link injection complete (v3.2)"
