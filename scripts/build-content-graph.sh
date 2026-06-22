#!/bin/bash
set -e

echo "🔗 Building content graph (v3.4 schema-flex safe)..."

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

INPUT = "content-model.json"
OUTPUT = "content-graph.json"

with open(INPUT, "r", encoding="utf-8") as f:
    raw = json.load(f)

# -----------------------------
# NORMALIZE INPUT (CRITICAL FIX)
# -----------------------------
pages = []

if isinstance(raw, dict):

    # Case 1: standard schema
    if "pages" in raw and isinstance(raw["pages"], list):
        pages = raw["pages"]

    # Case 2: object-map schema (YOUR CURRENT BUG)
    else:
        for url, obj in raw.items():
            if not isinstance(obj, dict):
                continue

            pages.append({
                "url": url,
                "title": obj.get("title", ""),
                "tags": obj.get("tags", [])
            })

elif isinstance(raw, list):
    pages = raw

# -----------------------------
# HARD SAFETY CHECK
# -----------------------------
if not pages:
    print("❌ ERROR: No pages detected after normalization")
    print("🔍 raw type:", type(raw))
    exit(1)

nodes = []
edges = []

# -----------------------------
# build nodes
# -----------------------------
for p in pages:
    nodes.append({
        "url": p.get("url"),
        "title": p.get("title", ""),
        "tags": p.get("tags", [])
    })

# -----------------------------
# build edges (tag overlap)
# -----------------------------

def overlap(a, b):
    return len(set(a) & set(b))

for i, a in enumerate(pages):
    tags_a = set(a.get("tags", []))

    for j, b in enumerate(pages):
        if i == j:
            continue

        tags_b = set(b.get("tags", []))

        score = overlap(tags_a, tags_b)

        if score > 0:
            edges.append({
                "from": a.get("url"),
                "to": b.get("url"),
                "weight": float(score),
                "shared_concepts": list(tags_a & tags_b)
            })

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({
        "nodes": nodes,
        "edges": edges
    }, f, indent=2, ensure_ascii=False)

print("📦 nodes:", len(nodes))
print("📦 edges:", len(edges))
EOF

echo "✅ Content graph built (v3.4 schema-flex safe)"
