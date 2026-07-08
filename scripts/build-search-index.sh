#!/bin/bash
set -euo pipefail

echo "🔎 Building search index (v5 unified python builder)"

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

SAL_FILE="assets/semantic-salience.json"
VOCAB_FILE="assets/vocabulary.json"
OUTPUT="assets/search-index.json"

if [ ! -f "$SAL_FILE" ]; then
  echo "❌ asset/semantic-salience.json missing — HARD STOP"
  exit 1
fi

if [ ! -s "$SAL_FILE" ]; then
  echo "❌ assets/semantic-salience.json is empty — HARD STOP (CI race detected)"
  exit 1
fi

if [ ! -f "$VOCAB_FILE" ]; then
  echo "❌ assets/vocabulary.json missing — HARD STOP"
  exit 1
fi

if [ ! -s "$VOCAB_FILE" ]; then
  echo "❌ assets/vocabulary.json is empty — HARD STOP"
  exit 1
fi

echo "🧠 Running unified index builder..."

python3 << 'EOF'

import os
import json
from pathlib import Path

ROOT = Path(os.getcwd())
SAL_FILE = ROOT / "assets/semantic-salience.json"
VOCAB_FILE = ROOT / "assets/vocabulary.json"
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
    raise SystemExit(f"❌ Failed to load assets/semantic-salience.json: {e}")

nodes = salience.get("nodes", {})
page_graph = salience.get("page_graph", {})

if not isinstance(page_graph, dict):
    raise SystemExit("❌ page_graph must be dict")

# -------------------------------------------------------
# LOAD VOCABULARY
# -------------------------------------------------------

try:
    raw = VOCAB_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        raise ValueError("assets/vocabulary.json is empty")

    vocabulary = json.loads(raw)
    
except Exception as e:
    raise SystemExit(f"❌ Failed to load assets/vocabulary.json: {e}")

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

    path = path.as_posix() if path else ""
    title = node.get("title", "")
    description = node.get("description", "")
    section = node.get("section", "")
    kind = node.get("kind", "")
    excerpt = node.get("excerpt", "")
    concepts = node.get("concepts", [])

    vocab = vocabulary.get(url, {})
    
    tags = vocab.get("tags", [])
    aliases = vocab.get("aliases", [])    
    search_text = " ".join([
        node.get("search_text", ""),
        " ".join(tags),
        " ".join(aliases)
    ]).strip()
    
    word_count = node.get("word_count", 0)

    index[url] = {
        "url": url,
        "path": path,
        "title": title,
        "description": description,

        "type": "page",
        "section": section,
        "kind": kind,

        "excerpt": excerpt,
        "search_text": search_text,

        "concepts": concepts,
        "tags": tags,
        "aliases": aliases,

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

from pathlib import Path

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
