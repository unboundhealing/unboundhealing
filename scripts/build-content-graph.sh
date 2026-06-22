#!/bin/bash
set -e

echo "🔗 Building content graph (v3.3 stable)..."

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

pages = data.get("pages", [])

nodes = []
edges = []

# -----------------------------
# build nodes
# -----------------------------
for p in pages:
    nodes.append({
        "url": p.get("url"),
        "title": p.get("title"),
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

output = {
    "nodes": nodes,
    "edges": edges
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("nodes:", len(nodes))
print("edges:", len(edges))
EOF

echo "✅ Content graph built (v3.3 stable)"
