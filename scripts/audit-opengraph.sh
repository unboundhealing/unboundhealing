#!/bin/bash
set -e

echo "🧭 Auditing OpenGraph tags..."

MISSING=0

while IFS= read -r file; do

  if ! grep -q "og:title" "$file"; then
    echo "⚠️ Missing og:title in $file"
    MISSING=1
  fi

  if ! grep -q "og:description" "$file"; then
    echo "⚠️ Missing og:description in $file"
    MISSING=1
  fi

  if ! grep -q "og:image" "$file"; then
    echo "⚠️ Missing og:image in $file"
    MISSING=1
  fi

done < <(find . -name "*.html")

if [ "$MISSING" -eq 1 ]; then
  echo "❌ OpenGraph audit failed"
  exit 1
fi

echo "✅ OpenGraph audit passed"
