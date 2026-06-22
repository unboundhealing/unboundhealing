import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-graph.json")
CLUSTERS_FILE = os.path.join(ROOT, "concept-clusters.json")

OUTPUT_FILE = os.path.join(ROOT, "semantic-salience.json")


# =========================================================
# LOAD DATA
# =========================================================

with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    graph = json.load(f).get("edges", [])

with open(CLUSTERS_FILE, "r", encoding="utf-8") as f:
    clusters = json.load(f)


# =========================================================
# BUILD CONCEPT CENTRALITY SCORES
# =========================================================

concept_scores = defaultdict(float)

for edge in graph:
    weight = edge.get("weight", 1)

    concept_scores[edge.get("from")] += weight
    concept_scores[edge.get("to")] += weight


# =========================================================
# NORMALIZE SCORES (0 → 1)
# =========================================================

max_score = max(concept_scores.values(), default=1)

normalized_scores = {
    concept: round(score / max_score, 4)
    for concept, score in concept_scores.items()
}


# =========================================================
# BUILD SALIENCE STRUCTURE (SINGLE SOURCE OF TRUTH)
# =========================================================

salience = {}

for concept, pages in clusters.items():

    salience[concept] = {
        "salience": normalized_scores.get(concept, 0),
        "page_count": len(pages),
        "pages": pages
    }


# =========================================================
# WRITE OUTPUT
# =========================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(salience, f, indent=2, ensure_ascii=False)


# =========================================================
# DEBUG (safe, structured, not breaking pipeline)
# =========================================================

print("🧠 Semantic salience built")
print(f"📦 Wrote: {OUTPUT_FILE}")
print(f"🔢 Concepts: {len(salience)}")

print("\n📊 Sample (first 3 concepts):")
for i, (k, v) in enumerate(salience.items()):
    print(k)
    print(v)
    print("---")
    if i == 2:
        break
