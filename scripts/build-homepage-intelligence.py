import json
from collections import defaultdict, Counter
import os

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-graph.json")
CLUSTERS_FILE = os.path.join(ROOT, "concept-clusters.json")
OUTPUT = os.path.join(ROOT, "homepage-intelligence.json")

# -----------------------------
# Load data
# -----------------------------
with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    graph = json.load(f)["edges"]

with open(CLUSTERS_FILE, "r", encoding="utf-8") as f:
    clusters = json.load(f)

# -----------------------------
# Node importance (centrality-lite)
# -----------------------------
scores = Counter()

for edge in graph:
    weight = edge.get("weight", 1)
    scores[edge["from"]] += weight
    scores[edge["to"]] += weight

featured_pages = [
    {"url": url, "score": score}
    for url, score in scores.most_common(10)
]

# -----------------------------
# Cluster importance
# -----------------------------
cluster_scores = []

for concept, pages in clusters.items():
    cluster_scores.append({
        "concept": concept,
        "size": len(pages)
    })

cluster_scores.sort(key=lambda x: x["size"], reverse=True)

clean_clusters = {}

for concept, pages in clusters.items():
    concept_clean = concept.strip().lower()

    if concept_clean in STOP_CONCEPTS:
        continue

    if len(concept_clean) < 3:
        continue

    clean_clusters[concept] = pages

STOP_CONCEPTS = {
    "that", "these", "those",
    "and", "or", "but",
    "the", "a", "an",
    "to", "of", "in", "on", "for",
    "unbound",  # optional: only if it's not semantically meaningful in your model
}

# -----------------------------
# Build “gravity layer”
# -----------------------------
top_concepts = cluster_scores[:8]

output = {
    "featured_pages": featured_pages[:3],
    "concept_clusters": top_concepts[:3]
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("🏠 Homepage intelligence built (v3.3 Phase 4)")
