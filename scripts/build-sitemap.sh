#!/bin/bash
set -e

echo "🗺 Building sitemap..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

OUTPUT="sitemap.xml"

cat > "$OUTPUT" <<EOF

<?xml version="1.0" encoding="UTF-8"?>

<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">

EOF

find . -name "*.html" 
! -path "./404.html" 
! -path "./assets/*" 
| sort | while read -r file
do

URL=$(echo "$file" 
| sed 's|^./||' 
| sed 's|index.html$||' 
| sed 's|.html$||')

if [ -z "$URL" ]; then
FULL_URL="https://unboundhealing.org/"
else
FULL_URL="https://unboundhealing.org/${URL}"
fi

cat >> "$OUTPUT" <<EOF <url> <loc>${FULL_URL}</loc> </url>

EOF

done

echo "</urlset>" >> "$OUTPUT"

echo "✅ sitemap.xml updated"
