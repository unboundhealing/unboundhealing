#!/bin/zsh

SITE="https://unboundhealing.org"
SITEMAP="./sitemap.xml"
OUTPUT="./feed.xml"

echo "📡 Generating RSS feed..."

# start feed
cat > "$OUTPUT" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
<title>Unbound Healing Ministries</title>
<link>$SITE</link>
<description>Reflection, presence, and invitation into deeper awareness through writing, listening, and shared attention.</description>
<language>en-us</language>
<image>
  <url>$SITE/og-image.png</url>
  <title>Unbound Healing Ministries</title>
  <link>$SITE</link>
</image>
EOF

# extract URLs from sitemap
grep -o "<loc>[^<]*</loc>" "$SITEMAP" | sed 's/<loc>//g;s/<\/loc>//g' | while read url
do

  # skip homepage if you want (optional)
  # [[ "$url" == "$SITE/" ]] && continue

  echo "→ processing $url"

  html=$(curl -s "$url")

  title=$(echo "$html" | grep -o '<title>[^<]*</title>' | sed 's/<title>//g;s/<\/title>//g')
  desc=$(echo "$html" | grep -o 'name="description" content="[^"]*"' | sed 's/.*content="//g;s/"//g')

  # XML escape safety (basic)
  title=$(echo "$title" | sed 's/&/\&amp;/g')
  desc=$(echo "$desc" | sed 's/&/\&amp;/g')

  cat >> "$OUTPUT" <<EOF

<item>
  <title>$title</title>
  <link>$url</link>
  <guid>$url</guid>
  <description>$desc</description>
</item>
EOF

done

# close feed
cat >> "$OUTPUT" <<EOF
</channel>
</rss>
EOF

echo "✅ RSS feed generated at $OUTPUT"
