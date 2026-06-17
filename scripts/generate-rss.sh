#!/bin/zsh

set -e

PROJECT_ROOT="/Users/unboundhealing/Documents/Unbound Healing/Web Design"
SITEMAP="$PROJECT_ROOT/sitemap.xml"
OUTPUT="$PROJECT_ROOT/feed.xml"
BASE_URL="https://unboundhealing.org"

cd "$PROJECT_ROOT" || exit 1

echo "📡 Generating RSS feed v1.2..."

# =========================
# PROPER NOUNS (extend anytime)
# =========================
PROPER_NOUNS=(
  "Tom"
  "Liz"
  "Unbound Healing"
  "Substack"
  "GitHub"
  "Interconnected Content Initiative"
)

protect_proper_nouns() {
  local input="$1"
  local output="$input"

  for noun in "${PROPER_NOUNS[@]}"; do
    output=$(echo "$output" | sed "s/${noun,,}/__PROTECTED_${noun}__/gI")
  done

  echo "$output"
}

restore_proper_nouns() {
  local input="$1"
  local output="$input"

  for noun in "${PROPER_NOUNS[@]}"; do
    output=$(echo "$output" | sed "s/__PROTECTED_${noun}__/$noun/g")
  done

  echo "$output"
}

sentence_case() {
  local input="$1"

  # protect proper nouns first
  local protected=$(protect_proper_nouns "$input")

  # lowercase everything
  local lower=$(echo "$protected" | tr '[:upper:]' '[:lower:]')

  # capitalize first character only
  local first_char=$(echo "${lower:0:1}" | tr '[:lower:]' '[:upper:]')
  local rest="${lower:1}"

  local combined="${first_char}${rest}"

  # restore proper nouns
  restore_proper_nouns "$combined"
}

extract_title() {
  local file="$1"
  grep -m 1 "<title>" "$file" | sed 's/<[^>]*>//g'
}

extract_description() {
  local file="$1"
  grep -m 1 'meta name="description"' "$file" \
    | sed 's/.*content="\([^"]*\)".*/\1/'
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
# PROCESS SITEMAP
# =========================

grep "<loc>" "$SITEMAP" | sed 's/<[^>]*>//g' | while read -r url; do

  echo "→ processing $url"

  path=$(echo "$url" | sed "s|$BASE_URL||")
  file_path="$PROJECT_ROOT${path}index.html"

  if [[ ! -f "$file_path" ]]; then
    file_path="$PROJECT_ROOT${path}.html"
  fi

  if [[ ! -f "$file_path" ]]; then
    continue
  fi

  raw_title=$(extract_title "$file_path")

  if [[ -z "$raw_title" ]]; then
    raw_title="Untitled"
  fi

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

cat >> "$OUTPUT" <<EOF

</channel>
</rss>
EOF

echo "✅ RSS feed generated at $OUTPUT"
