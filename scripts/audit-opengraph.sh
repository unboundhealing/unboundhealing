#!/bin/bash
set -euo pipefail

echo "🧭 Auditing OpenGraph tags..."

MISSING=0

# ---------------------------------------------------------
# AUDIT PUBLIC-FACING HTML ONLY
# ---------------------------------------------------------

while IFS= read -r file; do

  # -------------------------------------------------------
  # REQUIRED TAGS
  # -------------------------------------------------------

  if ! grep -q "og:title" "$file"; then
    echo "⚠️ Missing og:title in $file"
    ((MISSING+=1))
  fi

  if ! grep -q "og:description" "$file"; then
    echo "⚠️ Missing og:description in $file"
    ((MISSING+=1))
  fi

  # -------------------------------------------------------
  # OPTIONAL BUT RECOMMENDED
  # -------------------------------------------------------

  if ! grep -q "og:image" "$file"; then
    echo "⚠️ Missing og:image in $file"
  fi

done < <(
  find . -name "*.html" \
    ! -path "./assets/*" \
    ! -path "./assets/images/_html/*" \
    ! -path "./assets/page-template/*" \
    ! -path "./assets/entry-template/*" \
    ! -path "./assets/updates-temp/*"
)

# ---------------------------------------------------------
# FINAL RESULT
# ---------------------------------------------------------

if [ "$MISSING" -gt 0 ]; then
  echo ""
  echo "❌ OpenGraph audit failed"
  echo "📊 Required tag violations: $MISSING"
  exit 1
fi

echo "✅ OpenGraph audit passed"
