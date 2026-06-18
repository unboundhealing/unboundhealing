import json
from collections import Counter

SEMANTIC_GRAPH = "semantic-graph.json"
CLUSTERS = "concept-clusters.json"
OUTPUT = "homepage-intelligence.json"

with open(SEMANTIC_GRAPH, "r", encoding="utf-8") as f:
    graph = json.load(f)

with open(CLUSTERS, "r", encoding="utf-8") as f:
    clusters = json.load(f)

# ----------------------------
# Page importance scoring
# ----------------------------

scores = Counter()

for edge in graph.get("edges", []):

    weight = edge.get("weight", 1)

    scores[edge["from"]] += weight
    scores[edge["to"]] += weight

top_pages = []

for url, score in scores.most_common(10):
    top_pages.append({
        "url": url,
        "score": score
    })

# ----------------------------
# Concept importance scoring
# ----------------------------

concept_scores = []

for concept, members in clusters.items():

    concept_scores.append({
        "concept": concept,
        "pages": len(members)
    })

concept_scores.sort(
    key=lambda x: x["pages"],
    reverse=True
)

# ----------------------------
# Build homepage intelligence
# ----------------------------

output = {
    "featured_pages": top_pages[:5],
    "top_concepts": concept_scores[:10]
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)

print("🏠 Homepage intelligence built (v3.3)")
