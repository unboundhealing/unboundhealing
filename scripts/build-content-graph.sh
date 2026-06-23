#!/bin/bash
set -euo pipefail

echo "🔗 Building content graph (v3.9 canonical-id hardened + CI-safe)"

ROOT_DIR="${GITHUB_WORKSPACE:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cd "$ROOT_DIR"

INPUT="content-model.json"
OUTPUT="content-graph.json"

if [ ! -f "$INPUT" ]; then
  echo "❌ content-model.json not found"
  exit 1
fi

python3 << 'EOF'
import json
from collections import Counter
import re
import os

INPUT = "content-model.json"
OUTPUT = "content-graph.json"

# =========================================================
# CANONICAL ID NORMALIZER (SINGLE SOURCE OF TRUTH)
# =========================================================

def canonical(path: str) -> str:
    if not path:
        return ""

    p = str(path).strip()

    # remove pipe artifacts
    p = p.lstrip("|")

    # strip domain if accidentally present
    p = re.sub(r"^https?:\/\/[^\/]+", "", p)

    # normalize slashes
    p = "/" + p.strip("/")

    # collapse duplicates
    p = re.sub(r"/+", "/", p)

    # enforce trailing slash for "directory-like" nodes
    if "." not in p.split("/")[-1]:
        if not p.endswith("/"):
            p += "/"

    return p.lower()

# ==========================================================
# LOAD
# ==========================================================

with open(INPUT, "r", encoding="utf-8") as f:
    raw = json.load(f)

pages = raw.get("pages", [])

if not pages:
    raise ValueError("No pages found in content-model.json")

# ==========================================================
# NORMALIZE TAGS
# ==========================================================

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

        if not t:
            continue

        if t in seen:
            continue

        seen.add(t)
        out.append(t)

    return out

# ==========================================================
# BUILD NODES (CANONICALIZED URLS)
# ==========================================================

nodes = []

for p in pages:
    nodes.append({
        "url": canonical(p.get("url") or p.get("file")),
        "title": p.get("title", ""),
        "tags": normalize_tags(p.get("tags"))
    })

# remove empty nodes
nodes = [n for n in nodes if n["url"]]

# ==========================================================
# BUILD EDGES (STRICT MATCH ONLY)
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
# DEBUG
# ==========================================================

print("\n🧪 CONTENT GRAPH DEBUG")
print("pages:", len(nodes))
print("edges:", len(edges))

all_tags = []
for n in nodes:
    all_tags.extend(n["tags"])

print("total tags:", len(all_tags))
print("unique tags:", len(set(all_tags)))

# ==========================================================
# FALLBACK (NEVER ZERO GRAPH)
# ==========================================================

if not edges:
    print("⚠️ WARNING: no edges detected → injecting safe self-edge graph")

    edges = [{
        "from": "/__system__/",
        "to": "/__system__/",
        "weight": 1.0,
        "shared_concepts": ["system"]
    }]

# ==========================================================
# SAVE
# ==========================================================

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump({
        "nodes": nodes,
        "edges": edges
    }, f, indent=2, ensure_ascii=False)

print("\n📦 nodes:", len(nodes))
print("📦 edges:", len(edges))
print("✅ content-graph built (v3.9 canonical-id stable)")
EOF

echo "✅ Content graph built"
