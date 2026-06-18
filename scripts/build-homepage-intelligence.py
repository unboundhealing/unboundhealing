import json
import os
from collections import Counter

# ----------------------------------
# ALWAYS resolve repo root in CI
# ----------------------------------
ROOT = os.environ.get("GITHUB_WORKSPACE")

if not ROOT:
    # fallback for local runs
    ROOT = os.getcwd()

SEMANTIC_GRAPH = os.path.join(ROOT, "semantic-graph.json")
CLUSTERS = os.path.join(ROOT, "concept-clusters.json")
OUTPUT = os.path.join(ROOT, "homepage-intelligence.json")

# ----------------------------------
# Load inputs safely
# ----------------------------------
with open(SEMANTIC_GRAPH, "r", encoding="utf-8") as f:
    graph = json.load(f)

with open(CLUSTERS, "r", encoding="utf-8") as f:
    clusters = json.load(f)

# ----------------------------------
# Page importance scoring
# ----------------------------------
scores = Counter()

for edge in graph.get("edges", []):
    weight = edge.get("weight", 1)
    scores[edge["from"]] += weight
    scores[edge["to"]] += weight

top_pages = [
    {"url": url, "score": score}
    for url, score in scores.most_common(10)
]

# ----------------------------------
# Concept importance scoring
# ----------------------------------
concept_scores = [
    {
        "concept": concept,
        "pages": len(members)
    }
    for concept, members in clusters.items()
]

concept_scores.sort(key=lambda x: x["pages"], reverse=True)

# ----------------------------------
# Write output (CRITICAL FIX)
# ----------------------------------
output = {
    "featured_pages": top_pages[:5],
    "top_concepts": concept_scores[:10]
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("🏠 Homepage intelligence built (v3.3)")
print(f"📦 Wrote: {OUTPUT}")
