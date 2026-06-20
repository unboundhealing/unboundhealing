import json
import os
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-graph.json")
CLUSTERS_FILE = os.path.join(ROOT, "concept-clusters.json")

OUTPUT = os.path.join(
    ROOT,
    "semantic-salience.json"
)

# -----------------------------
# Load data
# -----------------------------

with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    graph = json.load(f)["edges"]

with open(CLUSTERS_FILE, "r", encoding="utf-8") as f:
    clusters = json.load(f)

# -----------------------------
# Concept centrality
# -----------------------------

concept_scores = defaultdict(float)

for edge in graph:

    weight = edge.get("weight", 1)

    concept_scores[edge["from"]] += weight
    concept_scores[edge["to"]] += weight

# -----------------------------
# Normalize
# -----------------------------

max_score = max(concept_scores.values(), default=1)

for concept in concept_scores:

    concept_scores[concept] = round(
        concept_scores[concept] / max_score,
        4
    )

# -----------------------------
# Build output
# -----------------------------

output = {}

for concept, pages in clusters.items():

    score = concept_scores.get(concept, 0)

    output[concept] = {
        "salience": score,
        "page_count": len(pages),
        "pages": pages
    }

# -----------------------------
# Save
# -----------------------------

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(
        output,
        f,
        indent=2,
        ensure_ascii=False
    )

print("🧠 Semantic salience built")
print("📦 Wrote:", OUTPUT)