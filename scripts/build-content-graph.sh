#!/bin/bash
set -e

echo "🔗 Building content graph (v3.4 schema-flex safe → gravity projection feed)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

INPUT="content-model.json"
OUTPUT="content-graph.json"

if [ ! -f "$INPUT" ]; then
  echo "❌ content-model.json not found."
  exit 1
fi

python3 - << 'EOF'
import json
import os

INPUT = "content-model.json"
OUTPUT = "content-graph.json"

with open(INPUT, "r", encoding="utf-8") as f:
    raw = json.load(f)

# --------------------------------------------------
# NORMALIZE INPUT (supports both schemas safely)
# --------------------------------------------------
pages = []

if isinstance(raw, dict):
    if "pages" in raw and isinstance(raw["pages"], list):
        pages = raw["pages"]
    else:
        for url, obj in raw.items():
            if isinstance(obj, dict):
                pages.append({
                    "url": url,
                    "title": obj.get("title", ""),
                    "tags": obj.get("tags", [])
                })

elif isinstance(raw, list):
    pages = raw

if not pages:
    raise ValueError("No pages found in content-model.json")

# --------------------------------------------------
# BUILD NODES + EDGES (tag overlap projection only)
# --------------------------------------------------
nodes = []
edges = []

def overlap(a, b):
    return len(set(a) & set(b))

for i, a in enumerate(pages):
    a_tags = a.get("tags", []) or []

    nodes.append({
        "url": a.get("url"),
        "title": a.get("title", ""),
        "tags": a_tags
    })

    for j, b in enumerate(pages):
        if i == j:
            continue

        b_tags = b.get("tags", []) or []

        score = overlap(a_tags, b_tags)

        if score > 0:
            edges.append({
                "from": a.get("url"),
                "to": b.get("url"),
                "weight": float(score),
                "shared_concepts": list(set(a_tags) & set(b_tags))
            })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({
        "nodes": nodes,
        "edges": edges
    }, f, indent=2, ensure_ascii=False)

print("📦 nodes:", len(nodes))
print("📦 edges:", len(edges))
print("✅ content-graph built (v3.4 gravity projection feed)")
EOF

echo "✅ Content graph built"
