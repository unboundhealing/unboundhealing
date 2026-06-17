#!/bin/bash
set -e

echo "🔗 Building link-reference.md..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="link-reference.md"

echo "# UNBOUND HEALING LINK REFERENCE" > "$OUTPUT"
echo "" >> "$OUTPUT"

find . -name "*.html" 
! -path "./404.html" 
! -path "./assets/*" 
| sort | while read -r file
do

TITLE=$(grep -m1 "<title>" "$file" 
| sed 's/<[^>]*>//g' 
| sed 's/| Unbound Healing Ministries//')

URL=$(echo "$file" 
| sed 's|^./||' 
| sed 's|index.html$||' 
| sed 's|.html$||')

INTERNAL="/${URL}"

if [ "$INTERNAL" = "/" ]; then
INTERNAL="/"
fi

EXTERNAL="https://unboundhealing.org${INTERNAL}"

cat >> "$OUTPUT" <<EOF

## ${TITLE}

External: <a href="${EXTERNAL}">${TITLE}</a>

Internal: <a href="${INTERNAL}">${TITLE}</a>

EOF

done

echo "✅ link-reference.md updated"
