#!/bin/bash
set -e

echo "🔗 Building content graph (v3.4 schema-safe)..."

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
import sys

INPUT = "content-model.json"
OUTPUT = "content-graph.json"

with open(INPUT, "r", encoding="utf-8") as f:
    data = json.load(f)

# ---------------------------------------
# SCHEMA RESOLUTION (FIXES YOUR ISSUE)
# ---------------------------------------
pages = None

if isinstance(data, dict):
    if "pages" in data:
        pages = data["pages"]
    elif "nodes" in data:
        pages = data["nodes"]
    elif "content" in data:
        pages = data["content"]

if not pages:
    print("❌ ERROR: No pages/nodes/content found in content-model.json")
    print("🔍 Available keys:", list(data.keys()) if isinstance(data, dict) else type(data))
    sys.exit(1)

# ---------------------------------------
# NORMALIZE PAGE STRUCTURE
# ---------------------------------------
normalized = []

for p in pages:
    if not isinstance(p, dict):
        continue

    url = p.get("url")
    if not url:
        continue

    tags = p.get("tags") or []
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    normalized.append({
        "url": url,
        "title": p.get("title", ""),
        "tags": tags
    })

# ---------------------------------------
# BUILD GRAPH
# ---------------------------------------
nodes = []
edges = []

for p in normalized:
    nodes.append({
        "url": p["url"],
        "title": p["title"],
        "tags": p["tags"]
    })

def overlap(a, b):
    return len(set(a) & set(b))

for i, a in enumerate(normalized):
    tags_a = set(a["tags"])

    for j, b in enumerate(normalized):
        if i == j:
            continue

        tags_b = set(b["tags"])
        score = overlap(tags_a, tags_b)

        if score > 0:
            edges.append({
                "from": a["url"],
                "to": b["url"],
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

echo "✅ Content graph built (v3.4 schema-safe)"
