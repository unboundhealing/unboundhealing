#!/bin/bash
set -euo pipefail

echo "🔗 Building content graph (v3.7 hardened + URL normalization fix)..."

ROOT_DIR="${GITHUB_WORKSPACE:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

echo "📍 ROOT_DIR: $ROOT_DIR"
cd "$ROOT_DIR" || {
  echo "❌ Cannot enter ROOT_DIR"
  exit 1
}

INPUT="content-model.json"
OUTPUT="content-graph.json"

if [ ! -f "$INPUT" ]; then
  echo "❌ content-model.json not found."
  exit 1
fi

python3 << 'EOF'
import json
import re
from collections import Counter

INPUT = "content-model.json"
OUTPUT = "content-graph.json"

# ==========================================================
# LOAD
# ==========================================================

with open(INPUT, "r", encoding="utf-8") as f:
    raw = json.load(f)

print("\n🧪 CONTENT MODEL INSPECTION")
print("root type:", type(raw).__name__)

pages = []

if isinstance(raw, dict):
    pages = raw.get("pages", [])
elif isinstance(raw, list):
    pages = raw

if not pages:
    raise ValueError("No pages detected")

# ==========================================================
# CLEANING HELPERS (CRITICAL FIX LAYER)
# ==========================================================

def clean_url(u: str):
    if not u:
        return u
    u = u.strip()

    # remove leading pipe corruption
    if u.startswith("|"):
        u = u[1:]

    # fix malformed protocol
    u = u.replace("https:///","https://")
    u = u.replace("http:///","http://")

    return u

def normalize_tag(t: str):
    if not t:
        return None

    t = str(t).strip().lower()

    # kill URLs in tags (CRITICAL FIX)
    if "http" in t or "://" in t:
        return None

    # kill path fragments
    if "/" in t:
        return None

    # remove garbage artifacts
    if len(t) < 3:
        return None

    if t in {"this","that","and","or","the","a","an"}:
        return None

    return t

def normalize_tags(tags):
    if not tags:
        return []

    if isinstance(tags, str):
        tags = re.split(r"[,\s]+", tags)

    cleaned = []
    seen = set()

    for t in tags:
        t = normalize_tag(t)
        if t and t not in seen:
            cleaned.append(t)
            seen.add(t)

    return cleaned

# ==========================================================
# BUILD NODES
# ==========================================================

nodes = []

for p in pages:

    url = clean_url(p.get("url"))
    tags = normalize_tags(p.get("tags"))

    nodes.append({
        "url": url,
        "title": p.get("title",""),
        "tags": tags
    })

# ==========================================================
# BUILD EDGES (SAFE ONLY)
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

        # FINAL SAFETY FILTER (critical)
        shared = [c for c in shared if normalize_tag(c)]

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

print("\nTOP 30 TAGS")
for t,c in Counter(all_tags).most_common(30):
    print(t, c)

# ==========================================================
# FALLBACK SAFETY (ONLY IF NEEDED)
# ==========================================================

if not edges:
    print("⚠️ injecting fallback edge (safe mode)")
    edges = [{
        "from": "system://root",
        "to": "system://root",
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
print("✅ content-graph built (v3.8 hardened URL-safe)")
EOF

echo "✅ Content graph built"
