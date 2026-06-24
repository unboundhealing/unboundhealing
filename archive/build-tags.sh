#!/bin/bash
set -euo pipefail

echo "🏷 Building tags (v4.0 semantic-salience projection ONLY)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

INPUT="semantic-salience.json"
OUTPUT="tags.json"

if [ ! -f "$INPUT" ]; then
  echo "❌ semantic-salience.json not found — cannot build tags"
  exit 1
fi

echo "🧠 Loading semantic-salience truth layer..."

python3 << 'EOF'
import json

INPUT = "semantic-salience.json"
OUTPUT = "tags.json"

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

pages = data.get("pages", {})

# ---------------------------------------
# BUILD INVERTED INDEX (concept → pages)
# ---------------------------------------
tag_index = {}

for url, node in pages.items():
    concepts = node.get("concepts", [])

    if not isinstance(concepts, list):
        continue

    for c in concepts:
        if not isinstance(c, dict):
            continue

        tag = c.get("word")
        if not tag:
            continue

        if tag not in tag_index:
            tag_index[tag] = {
                "count": 0,
                "pages": []
            }

        tag_index[tag]["count"] += 1
        tag_index[tag]["pages"].append(url)

# ---------------------------------------
# DEDUPE + CLEAN OUTPUT
# ---------------------------------------
for tag, obj in tag_index.items():
    obj["pages"] = sorted(list(set(obj["pages"])))

# sort tags by importance
sorted_tags = dict(
    sorted(tag_index.items(), key=lambda x: -x[1]["count"])
)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(sorted_tags, f, indent=2)

print("🏷 Tags built (v4.0 SALIENCE-ONLY)")
print("📦 tags:", len(sorted_tags))
EOF
