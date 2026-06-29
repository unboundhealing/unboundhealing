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
# SECTION
# -------------------------------------------------------

def get_section(url):

    path = url.replace("https://unboundhealing.org/", "").strip("/")

    if path == "":
        return "home"

    return path.split("/")[0]

# -------------------------------------------------------
# KIND
# -------------------------------------------------------

def get_kind(section):

    mapping = {
        "home": "home",
        "opening": "journal",
        "concept": "concept",
        "about": "about",
        "gathering": "gathering",
        "supporting": "supporting",
        "listen": "listen",
        "welcome": "welcome"
    }

    return mapping.get(section, "page")
    
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

def build_search_text(
    title,
    description,
    excerpt,
    tags,
    concepts,
    aliases,
):

    fields = [
        title,
        description,
        excerpt,
        " ".join(tags),
        " ".join(concepts),
        " ".join(aliases),
    ]

    return " ".join(
        str(x).strip().lower()
        for x in fields
        if x
    )
    
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
    section = get_section(url)
    kind = get_kind(section)
  
    # -------------------------------------------------------
    # Additional search metadata
    # -------------------------------------------------------

    excerpt = node.get("excerpt", "")
    kind = node.get("kind", "page")

    word_count = node.get("word_count", 0)
    concept_count = len(tags)

    related_count = len(page_graph.get(url, {}).get("related", []))

    search_text = build_search_text(
        title,
        desc,
        excerpt,
        tags,
        tags,
        []
    )
    
    index[url] = {
        "title": title,
        "url": url,
        "path": file_path,

        "type": "page",
        "section": section,
        "kind": kind,

        "tags": tags,
        "concepts": tags,
        "aliases": [],

        "description": desc,
        "excerpt": excerpt,
        "search_text": search_text,

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
