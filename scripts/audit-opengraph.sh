#!/bin/bash
set -e

echo "🧭 Auditing OpenGraph tags..."

MISSING=0

# ---------------------------------------
# ONLY audit public-facing pages
# ---------------------------------------
find . -name "*.html" \
  ! -path "./assets/*" \
  ! -path "./assets/images/_html/*" \
  ! -path "./assets/page-template/*" \
  ! -path "./assets/entry-template/*" \
  ! -path "./assets/updates-temp/*" \
  | while IFS= read -r file; do

    # -----------------------------------
    # Check required OG tags
    # -----------------------------------
    if ! grep -q "og:title" "$file"; then
      echo "⚠️ Missing og:title in $file"
      MISSING=1
    fi

    if ! grep -q "og:description" "$file"; then
      echo "⚠️ Missing og:description in $file"
      MISSING=1
    fi

    # og:image is OPTIONAL for some pages, but still flagged
    if ! grep -q "og:image" "$file"; then
      echo "⚠️ Missing og:image in $file"
      MISSING=1
    fi

  done

# ---------------------------------------
# Final result
# ---------------------------------------
if [ "$MISSING" -eq 1 ]; then
  echo "❌ OpenGraph audit failed"
  exit 1
fi

echo "✅ OpenGraph audit passed"
