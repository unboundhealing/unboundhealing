#!/bin/zsh

set -e

BASE="/Users/unboundhealing/Documents/Unbound Healing/Web Design"
DICT="$BASE/scripts/image_dictionary.txt"

NAME="$1"

if [ -z "$NAME" ]; then
  echo "No filename provided"
  exit 1
fi

OUTPUT="$BASE/assets/images/_html/${NAME}.html"
mkdir -p "$BASE/assets/images/_html"

# ----------------------------------------
# DEFAULT FALLBACK VALUES (your old system)
# ----------------------------------------
clean_name=$(echo "$NAME" | tr '_' ' ')
fallback_artist=$(echo "$clean_name" | awk '{print $1}')
fallback_title=$(echo "$clean_name" | cut -d' ' -f2-)
fallback_caption="Expert+ run of \"$fallback_title\". Gameplay captured in motion."

artist="$fallback_artist"
title="$fallback_title"
caption="$fallback_caption"

# ----------------------------------------
# DICTIONARY OVERRIDE (NEW LAYER)
# ----------------------------------------
if [ -f "$DICT" ]; then
  entry=$(grep "^$NAME|" "$DICT")

  if [ ! -z "$entry" ]; then
    artist=$(echo "$entry" | cut -d'|' -f2)
    title=$(echo "$entry" | cut -d'|' -f3)
    caption=$(echo "$entry" | cut -d'|' -f4)
  fi
fi

# ----------------------------------------
# FINAL FORMATTING
# ----------------------------------------
full_title="$artist – $title"
alt_text="$full_title (Beat Saber)"

# ----------------------------------------
# OUTPUT FILE
# ----------------------------------------
cat > "$OUTPUT" <<EOF
<figure class="article-image">
  <a href="/assets/images/${NAME}.webp"
     target="_blank"
     rel="noopener noreferrer">

    <picture>
      <source
        media="(max-width: 768px)"
        srcset="/assets/images/${NAME}_mobile.webp">

      <img
        src="/assets/images/${NAME}.webp"
        alt="$alt_text"
        loading="lazy">
    </picture>

  </a>

  <figcaption>
    $caption
  </figcaption>
</figure>
EOF

echo "Created: $OUTPUT"
