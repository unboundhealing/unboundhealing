import json
import os
import re
from collections import Counter, defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

REGISTRY_FILE = os.path.join(ROOT, "content-registry.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-salience.json")

STOP = {
    "the","a","an","and","or","to","of","in","on","for","with","is","it",
    "this","that","just","here","thing","things"
}

def normalize(text):
    if not text:
        return None
    text = str(text).lower().strip()
    text = re.sub(r"[^a-z\\- ]", "", text)
    if text in STOP:
        return None
    if len(text) < 3:
        return None
    return text

# ----------------------------
# LOAD REGISTRY
# ----------------------------

with open(REGISTRY_FILE, "r", encoding="utf-8") as f:
    registry = json.load(f)

pages = registry.get("pages", [])

nodes = []
concept_counts = Counter()
edges = []

# ----------------------------
# BUILD NODES + CONCEPTS
# ----------------------------

for p in pages:
    path = p.get("path","")
    url = p.get("url","")

    # derive lightweight concepts from URL path
    parts = re.split(r"[\\/\\-]", path)

    concepts = []
    for part in parts:
        n = normalize(part)
        if n:
            concepts.append(n)

    concepts = list(dict.fromkeys(concepts))

    for c in concepts:
        concept_counts[c] += 1

    nodes.append({
        "url": url,
        "path": path,
        "concepts": concepts
    })

# ----------------------------
# BUILD EDGES (ONLY FROM SAME LAYER)
# ----------------------------

for i, a in enumerate(nodes):
    for j, b in enumerate(nodes):
        if i >= j:
            continue

        shared = list(set(a["concepts"]) & set(b["concepts"]))
        if not shared:
            continue

        edges.append({
            "from": a["url"],
            "to": b["url"],
            "weight": len(shared),
            "concepts": shared
        })

# ----------------------------
# BUILD SALIENCE
# ----------------------------

total = sum(concept_counts.values()) or 1

salience = {
    c: {
        "count": n,
        "salience": n / total
    }
    for c, n in concept_counts.items()
}

# ----------------------------
# OUTPUT (SINGLE SOURCE OF TRUTH)
# ----------------------------

output = {
    "nodes": nodes,
    "edges": edges,
    "salience": salience
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("🌌 semantic-salience built (SINGLE SOURCE OF TRUTH)")
print("📦 nodes:", len(nodes))
print("📦 edges:", len(edges))
print("🧠 concepts:", len(salience))
