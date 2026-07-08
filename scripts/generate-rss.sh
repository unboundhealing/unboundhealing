#!/bin/bash
set -e

echo "📡 Generating RSS feed v1.3 (CI-safe)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

SITEMAP="sitemap.xml"
OUTPUT="feed.xml"
BASE_URL="https://unboundhealing.org"

# =========================
# PROPER NOUNS
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

  local protected=$(protect_proper_nouns "$input")
  local lower=$(echo "$protected" | tr '[:upper:]' '[:lower:]')

  local first_char=$(echo "${lower:0:1}" | tr '[:lower:]' '[:upper:]')
  local rest="${lower:1}"

  restore_proper_nouns "${first_char}${rest}"
}

extract_title() {
  local file="$1"
  grep -m1 "<title>" "$file" | sed 's/<[^>]*>//g'
}

extract_description() {
  local file="$1"
  grep -m1 'meta name="description"' "$file" \
    | sed 's/.*content="\([^"]*\)".*/\1/'
}

# =========================
# RSS HEADER
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

EOF

# =========================
# PROCESS SITEMAP
# =========================

grep "<loc>" "$SITEMAP" | sed 's/<[^>]*>//g' | sort | while read -r url; do

  echo "→ processing $url"

  path=$(echo "$url" | sed "s|$BASE_URL||")

  file_path="$ROOT_DIR${path}index.html"
  if [[ ! -f "$file_path" ]]; then
    file_path="$ROOT_DIR${path}.html"
  fi

  if [[ ! -f "$file_path" ]]; then
    continue
  fi

  raw_title=$(extract_title "$file_path")
  [ -z "$raw_title" ] && raw_title="Untitled"

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
