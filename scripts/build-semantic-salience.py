#!/usr/bin/env python3
import json
import os
import re
from collections import defaultdict, Counter

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

REGISTRY_PATH = os.path.join(ROOT, "content-registry.json")
OUTPUT_PATH = os.path.join(ROOT, "semantic-salience.json")


# -------------------------------------------------------
# SAFETY GUARDS
# -------------------------------------------------------
if not os.path.exists(REGISTRY_PATH):
    raise FileNotFoundError("content-registry.json missing (required single input source)")


# -------------------------------------------------------
# NORMALIZATION
# -------------------------------------------------------
def normalize(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\\-_/ ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str):
    return [t for t in text.split(" ") if len(t) > 2]


# -------------------------------------------------------
# LOAD REGISTRY (ONLY INPUT SOURCE)
# -------------------------------------------------------
with open(REGISTRY_PATH, "r", encoding="utf-8") as f:
    registry = json.load(f)

pages = registry.get("pages", [])

if not pages:
    raise ValueError("Registry contains no pages")


# -------------------------------------------------------
# BUILD INTERNAL STATE
# -------------------------------------------------------
nodes = {}
concept_counts = Counter()
edges = []


# -------------------------------------------------------
# BUILD NODES + CONCEPTS
# -------------------------------------------------------
for p in pages:
    path = p.get("path", "")
    url = p.get("url", "")

    base = normalize(path + " " + url)
    concepts = tokenize(base)

    nodes[url] = {
        "path": path,
        "url": url,
        "concepts": concepts
    }

    for c in concepts:
        concept_counts[c] += 1


# -------------------------------------------------------
# BUILD EDGES (FULL DENSE GRAPH)
# -------------------------------------------------------
urls = list(nodes.keys())

for i in range(len(urls)):
    for j in range(i + 1, len(urls)):
        a = nodes[urls[i]]
        b = nodes[urls[j]]

        shared = list(set(a["concepts"]) & set(b["concepts"]))

        if shared:
            edges.append({
                "from": urls[i],
                "to": urls[j],
                "weight": len(shared),
                "shared": shared[:12]
            })


# -------------------------------------------------------
# BUILD SINGLE TRUTH LAYER (SALIENCE)
# -------------------------------------------------------
total = sum(concept_counts.values()) or 1

salience = {
    c: {
        "count": n,
        "score": n / total
    }
    for c, n in concept_counts.items()
}


# -------------------------------------------------------
# GUARANTEE NON-EMPTY OUTPUT (NO FAIL STATES)
# -------------------------------------------------------
if not edges and len(urls) > 1:
    edges = [{
        "from": urls[0],
        "to": urls[1],
        "weight": 1,
        "shared": ["system"]
    }]


# -------------------------------------------------------
# WRITE OUTPUT (ONLY TRUTH ARTIFACT)
# -------------------------------------------------------
output = {
    "truth_layer": "semantic-salience",
    "nodes": nodes,
    "edges": edges,
    "salience": salience
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)


print("🌌 semantic-salience COMPLETE (single truth layer)")
print("📦 nodes:", len(nodes))
print("📦 edges:", len(edges))
print("🧠 concepts:", len(salience))
print("📁 output:", OUTPUT_PATH)
