#!/bin/bash
set -e

echo "🔗 Building content graph (v3.4 schema-flex)..."

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
    data = json.load(f)

# ---------------------------------------
# 🔍 SCHEMA DETECTION LAYER (NEW)
# ---------------------------------------

if "pages" in data and isinstance(data["pages"], list):
    pages = data["pages"]

elif "nodes" in data and isinstance(data["nodes"], list):
    pages = data["nodes"]

else:
    # fallback: treat dict-of-urls as pages
    pages = []

    for k, v in data.items():
        if isinstance(v, dict):
            pages.append({
                "url": k,
                "title": v.get("title", ""),
                "tags": v.get("tags", [])
            })

print("🔍 Detected pages:", len(pages))

# ---------------------------------------
# BUILD NODES
# ---------------------------------------

nodes = []
edges = []

for p in pages:
    if not isinstance(p, dict):
        continue

    nodes.append({
        "url": p.get("url"),
        "title": p.get("title"),
        "tags": p.get("tags", [])
    })

# ---------------------------------------
# BUILD EDGES (tag overlap)
# ---------------------------------------

def overlap(a, b):
    return len(set(a) & set(b))

for i, a in enumerate(pages):
    tags_a = set(a.get("tags", []) if isinstance(a, dict) else [])

    for j, b in enumerate(pages):
        if i == j:
            continue

        tags_b = set(b.get("tags", []) if isinstance(b, dict) else [])

        score = overlap(tags_a, tags_b)

        if score > 0:
            edges.append({
                "from": a.get("url"),
                "to": b.get("url"),
                "weight": float(score),
                "shared_concepts": list(tags_a & tags_b)
            })

output = {
    "nodes": nodes,
    "edges": edges
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("📦 nodes:", len(nodes))
print("📦 edges:", len(edges))
EOF

echo "✅ Content graph built (v3.4 schema-flex)"
