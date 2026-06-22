import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-graph.json")
OUTPUT_FILE = os.path.join(ROOT, "concept-clusters.json")

STOP = {"this","that","just","about","here","like"}

with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    graph = json.load(f).get("edges", [])

clusters = defaultdict(list)

for e in graph:
    url = e["to"]

    for c in e.get("shared_concepts", []):
        c = c.lower().strip()

        if c in STOP:
            continue

        clusters[c].append({
            "url": url,
            "weight": float(e.get("weight", 1))
        })

# prune junk clusters
clusters = {
    k: v for k, v in clusters.items()
    if len(v) >= 2 and k not in STOP
}

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(clusters, f, indent=2)

print("🧩 Concept clusters built (v4.0 clean)")
print("📦 clusters:", len(clusters))
