#!/bin/bash
set -euo pipefail

echo "🔗 Building content graph (v3.9 canonical-id hardened + CI-safe)"

ROOT_DIR="${GITHUB_WORKSPACE:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$ROOT_DIR" || exit 1

INPUT="content-model.json"
OUTPUT="content-graph.json"

if [ ! -f "$INPUT" ]; then
  echo "❌ content-model.json not found"
  exit 1
fi

python3 << 'EOF'
import json
import re
from collections import defaultdict

INPUT = "content-model.json"
OUTPUT = "content-graph.json"

def canonical(path: str) -> str:
    if not path:
        return ""

    p = str(path).strip()
    p = p.lstrip("|")
    p = re.sub(r"^https?:\/\/[^\/]+", "", p)
    p = "/" + p.strip("/")
    p = re.sub(r"/+", "/", p)

    # enforce directory-style canonicalization
    if "." not in p.split("/")[-1]:
        if not p.endswith("/"):
            p += "/"

    return p.lower()

def normalize_tags(tags):
    if not tags:
        return []

    if isinstance(tags, str):
        tags = tags.split(",")

    out = []
    seen = set()

    for t in tags:
        t = str(t).strip().lower()
        t = re.sub(r"[^a-z0-9\-_]", "", t)

        if not t or t in seen:
            continue

        seen.add(t)
        out.append(t)

    return out

with open(INPUT, "r", encoding="utf-8") as f:
    raw = json.load(f)

pages = raw.get("pages", [])

nodes = []
for p in pages:
    url = canonical(p.get("url") or p.get("file"))
    if not url:
        continue

    nodes.append({
        "url": url,
        "title": p.get("title", ""),
        "tags": normalize_tags(p.get("tags"))
    })

edges = []

for i, a in enumerate(nodes):
    for j, b in enumerate(nodes):
        if i == j:
            continue

        shared = sorted(set(a["tags"]) & set(b["tags"]))

        if not shared:
            continue

        edges.append({
            "from": a["url"],
            "to": b["url"],
            "weight": float(len(shared)),
            "shared_concepts": shared
        })

if not edges:
    edges = [{
        "from": "/__system__/",
        "to": "/__system__/",
        "weight": 1.0,
        "shared_concepts": ["system"]
    }]

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({"nodes": nodes, "edges": edges}, f, indent=2, ensure_ascii=False)

print("📦 nodes:", len(nodes))
print("📦 edges:", len(edges))
print("✅ content-graph built (stable canonical layer)")
EOF

echo "✅ Content graph built"
