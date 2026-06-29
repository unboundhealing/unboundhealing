#!/bin/bash
set -euo pipefail

echo "🔎 Building search index (v5 unified python builder)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

SAL_FILE="assets/semantic-salience.json"
OUTPUT="assets/search-index.json"

if [ ! -f "$SAL_FILE" ]; then
  echo "❌ asset/semantic-salience.json missing — HARD STOP"
  exit 1
fi

if [ ! -s "$SAL_FILE" ]; then
  echo "❌ assets/semantic-salience.json is empty — HARD STOP (CI race detected)"
  exit 1
fi

echo "🧠 Running unified index builder..."

python3 << 'EOF'

import os
import json
from pathlib import Path

ROOT = Path(os.getcwd())
SAL_FILE = ROOT / "assets/semantic-salience.json"
OUTPUT_FILE = ROOT / "assets/search-index.json"

# -------------------------------------------------------
# SAFE LOAD
# -------------------------------------------------------

try:
    raw = SAL_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError("assets/semantic-salience.json is empty")

    salience = json.loads(raw)

except Exception as e:
    raise SystemExit(f"❌ Failed to load semantic-salience.json: {e}")

nodes = salience.get("nodes", {})
page_graph = salience.get("page_graph", {})

if not isinstance(page_graph, dict):
    raise SystemExit("❌ page_graph must be dict")
    
# -------------------------------------------------------
# INDEX BUILD
# -------------------------------------------------------

index = {}

for url, node in nodes.items():

    if not isinstance(node, dict):
        continue

    file_path = node.get("path", "")
    path = ROOT / file_path if file_path else None

    # -------------------------------------------------------
    # Additional search metadata
    # -------------------------------------------------------

    title = node.get("title", "")
    section = node.get("section", "")
    kind = node.get("kind", "")
    desc = node.get("description", "")
    excerpt = node.get("excerpt", "")
    tags = node.get("concepts", [])
    concepts = tags
    aliases = []
    word_count = node.get("word_count", 0)

    search_text = node.get("search_text", "")

    index[url] = {
        "title": title,
        "url": url,
        "path": file_path,

        "type": "page",
        "section": section,
        "kind": kind,

        "description": desc,
        "excerpt": excerpt,
        "search_text": search_text,

        "tags": tags,
        "concepts": concepts,
        "aliases": [],

        "word_count": word_count,
        "reading_time": max(1, round(word_count / 200)),

        "priority": 1.0,

        "image": "",
        "last_modified": ""
    }

# -------------------------------------------------------
# WRITE (atomic)
# -------------------------------------------------------

tmp_path = OUTPUT_FILE.with_suffix(".tmp")

tmp_path.write_text(
    json.dumps(index, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

os.replace(tmp_path, OUTPUT_FILE)

print("✅ Search index built (v5 unified python builder)")
print(f"📦 pages indexed: {len(index)}")
print("🧠 semantic-salience is the single truth source")
EOF

echo "🎉 Done."
