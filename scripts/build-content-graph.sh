#!/bin/bash
set -e

echo "🔗 Building content graph (v3.5 gravity projection feed)..."

ROOT_DIR="$(git rev-parse --show-toplevel)"
cd "$ROOT_DIR"

INPUT="content-model.json"
OUTPUT="content-graph.json"

if [ ! -f "$INPUT" ]; then
  echo "❌ content-model.json not found."
  exit 1
fi

python3 << 'EOF'
import json

INPUT = "content-model.json"
OUTPUT = "content-graph.json"

# ==========================================================
# LOAD
# ==========================================================

with open(INPUT, "r", encoding="utf-8") as f:
    raw = json.load(f)

# ==========================================================
# NORMALIZE INPUT SCHEMAS
# ==========================================================

pages = []

if isinstance(raw, dict):

    if "pages" in raw and isinstance(raw["pages"], list):

        pages = raw["pages"]

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

if not pages:
    raise ValueError("No pages detected in content-model.json")

# ==========================================================
# TAG NORMALIZATION
# ==========================================================

def normalize_tags(tags):

    if not tags:
        return []

    if isinstance(tags, str):

        tags = [
            t.strip().lower()
            for t in tags.split(",")
            if t.strip()
        ]

    elif isinstance(tags, list):

        tags = [
            str(t).strip().lower()
            for t in tags
            if str(t).strip()
        ]

    else:
        return []

    return list(dict.fromkeys(tags))

# ==========================================================
# BUILD NODES
# ==========================================================

nodes = []

for page in pages:

    tags = normalize_tags(page.get("tags"))

    nodes.append({
        "url": page.get("url"),
        "title": page.get("title", ""),
        "tags": tags
    })

# ==========================================================
# BUILD EDGES
# ==========================================================

edges = []

for i, a in enumerate(nodes):

    a_tags = set(a["tags"])

    if not a_tags:
        continue

    for j, b in enumerate(nodes):

        if i == j:
            continue

        b_tags = set(b["tags"])

        shared = sorted(a_tags & b_tags)

        if not shared:
            continue

        edges.append({
            "from": a["url"],
            "to": b["url"],
            "weight": float(len(shared)),
            "shared_concepts": shared
        })

# ==========================================================
# DEBUGGING
# ==========================================================

print("\n🧪 CONTENT GRAPH DEBUG")

print("pages:", len(nodes))
print("edges:", len(edges))

if nodes:
    print("\nSAMPLE NODE:")
    print(json.dumps(nodes[0], indent=2))

if edges:
    print("\nSAMPLE EDGE:")
    print(json.dumps(edges[0], indent=2))

print("\nFIRST FIVE EDGE CONCEPT LISTS:")

for edge in edges[:5]:
    print(edge.get("shared_concepts"))

# ==========================================================
# SAVE
# ==========================================================

with open(OUTPUT, "w", encoding="utf-8") as f:

    json.dump(
        {
            "nodes": nodes,
            "edges": edges
        },
        f,
        indent=2,
        ensure_ascii=False
    )

print("\n📦 nodes:", len(nodes))
print("📦 edges:", len(edges))
print("✅ content-graph built (v3.5 gravity projection feed)")
EOF

echo "✅ Content graph built"
