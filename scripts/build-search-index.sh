#!/bin/bash
set -euo pipefail

echo "🔎 Building search index (v5 unified python builder)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

SAL_FILE="semantic-salience.json"
OUTPUT="search-index.json"

if [ ! -f "$SAL_FILE" ]; then
  echo "❌ semantic-salience.json missing — HARD STOP"
  exit 1
fi

if [ ! -s "$SAL_FILE" ]; then
  echo "❌ semantic-salience.json is empty — HARD STOP (CI race detected)"
  exit 1
fi

echo "🧠 Running unified index builder..."

python3 << 'EOF'

import os
import json
from pathlib import Path

ROOT = Path(os.getcwd())
SAL_FILE = ROOT / "semantic-salience.json"
OUTPUT_FILE = ROOT / "search-index.json"

# -------------------------------------------------------
# SAFE LOAD
# -------------------------------------------------------

try:
    raw = SAL_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError("semantic-salience.json is empty")

    salience = json.loads(raw)

except Exception as e:
    raise SystemExit(f"❌ Failed to load semantic-salience.json: {e}")

nodes = salience.get("nodes", {})
page_graph = salience.get("page_graph", {})

if not isinstance(page_graph, dict):
    raise SystemExit("❌ page_graph must be dict")

# -------------------------------------------------------
# DISPLAY TITLE
# -------------------------------------------------------

def get_display_title(node):
    if not node:
        return ""

    title = node.get("title")

    if isinstance(title, str) and title.strip():
        return title.strip()

    url = node.get("url", "")
    return url.rstrip("/").split("/")[-1]
    
# -------------------------------------------------------
# BUILD CONCEPT MAP
# -------------------------------------------------------

concept_map = {}

for url, node in page_graph.items():

    concepts = []

    if isinstance(node, dict):
        raw = node.get("concepts", [])
        if isinstance(raw, list):
            for c in raw:
                if isinstance(c, str):
                    concepts.append(c)

    clean = []
    seen = set()

    for c in concepts:
        c = c.strip().lower()
        if not c or c in seen:
            continue
        seen.add(c)
        clean.append(c)

    concept_map[url] = clean[:10]

# -------------------------------------------------------
# INDEX BUILD
# -------------------------------------------------------

index = {}

for url, node in nodes.items():

    if not isinstance(node, dict):
        continue

    file_path = node.get("path", "")
    path = ROOT / file_path if file_path else None

    # title resolution (TRUTH LAYER ONLY)
    title = get_display_title(node)

    # description (optional passthrough from node if exists)
    desc = node.get("description", "") if isinstance(node, dict) else ""

    tags = concept_map.get(url, [])

    index[url] = {
        "title": title,
        "url": url,
        "path": file_path,

        "type": "page",
        "kind": "page",
        "section": "",

        "tags": tags[:10],
        "concepts": tags[:10],
        "aliases": [],

        "description": desc,
        "excerpt": "",
        "search_text": "",

        "word_count": 0,
        "reading_time": 0,

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
