#!/bin/zsh

set -e

# =========================
# CONFIG
# =========================
PROJECT_ROOT="/Users/unboundhealing/Documents/Unbound Healing/Web Design"
SITEMAP="$PROJECT_ROOT/sitemap.xml"
OUTPUT="$PROJECT_ROOT/feed.xml"
BASE_URL="https://unboundhealing.org"

cd "$PROJECT_ROOT" || exit 1

echo "📡 Generating RSS feed from sitemap..."

# =========================
# FUNCTIONS
# =========================

sentence_case() {
  # lowercases everything, then capitalizes first word
  # preserves proper nouns crudely via whitelist pattern later if needed

  local input="$1"

  # lowercase whole string
  local lower=$(echo "$input" | tr '[:upper:]' '[:lower:]')

  # capitalize first character
  local first_char=$(echo "${lower:0:1}" | tr '[:lower:]' '[:upper:]')
  local rest="${lower:1}"

  echo "${first_char}${rest}"
}

extract_title() {
  local file="$1"
  grep -m 1 "<title>" "$file" | sed 's/<[^>]*>//g'
}

extract_description() {
  local file="$1"

  # meta description
  local desc=$(grep -m 1 'meta name="description"' "$file" \
    | sed 's/.*content="\([^"]*\)".*/\1/')

  echo "$desc"
}

# =========================
# BUILD RSS HEADER
# =========================

cat > "$OUTPUT" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>

<title>Unbound Healing Ministries</title>
<link>$BASE_URL/</link>
<description>Reflection, presence, and invitation into deeper awareness through writing, listening, and shared attention.</description>
<language>en-us</language>

<image>
  <url>$BASE_URL/og-image.png</url>
  <title>Unbound Healing Ministries</title>
  <link>$BASE_URL/</link>
</image>

<lastBuildDate>$(date -R)</lastBuildDate>
EOF

# =========================
# PROCESS SITEMAP URLS
# =========================

grep "<loc>" "$SITEMAP" | sed 's/<[^>]*>//g' | while read -r url; do

  # skip index page duplicates if needed later
  path=$(echo "$url" | sed "s|$BASE_URL||")
  file_path="$PROJECT_ROOT${path}index.html"

  # fallback for direct html pages
  if [[ ! -f "$file_path" ]]; then
    file_path="$PROJECT_ROOT${path}.html"
  fi

  # skip if file doesn't exist (folders like /opening/)
  if [[ ! -f "$file_path" ]]; then
    continue
  fi

  raw_title=$(extract_title "$file_path")
  title=$(sentence_case "$raw_title")

  description=$(extract_description "$file_path")

  cat >> "$OUTPUT" <<EOF

<item>
  <title>$title</title>
  <link>$url</link>
  <guid>$url</guid>
  <description><![CDATA[$description]]></description>
</item>
EOF

done

# =========================
# CLOSE RSS
# =========================

cat >> "$OUTPUT" <<EOF

</channel>
</rss>
EOF

echo "✅ RSS feed generated: feed.xml"
