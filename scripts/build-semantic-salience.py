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
    graph = json.load(f)["edges"]

with open(CLUSTERS_FILE, "r", encoding="utf-8") as f:
    clusters = json.load(f)


# =========================================================
# BUILD DIRECTIONAL CONCEPT NETWORK
# =========================================================

inflow = defaultdict(float)
outflow = defaultdict(float)

neighbors = defaultdict(dict)

for edge in graph:

    weight = float(edge.get("weight", 1))

    source = edge["from"]
    target = edge["to"]

    outflow[source] += weight
    inflow[target] += weight

    neighbors[source][target] = (
        neighbors[source].get(target, 0)
        + weight
    )

    neighbors[target][source] = (
        neighbors[target].get(source, 0)
        + weight
    )


# =========================================================
# NORMALIZATION
# =========================================================

def normalize(values):

    max_value = max(values.values(), default=1)

    output = {}

    for key, value in values.items():

        output[key] = round(
            value / max_value,
            4
        )

    return output


inflow = normalize(inflow)
outflow = normalize(outflow)


# =========================================================
# BUILD SALIENCE MODEL
# =========================================================

output = {}

for concept, pages in clusters.items():

    incoming = inflow.get(concept, 0.0)
    outgoing = outflow.get(concept, 0.0)

    stability = round(
        1 - abs(incoming - outgoing),
        4
    )

    salience = round(
        (incoming + outgoing) / 2,
        4
    )

    related_concepts = []

    for related, weight in sorted(
        neighbors.get(concept, {}).items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]:

        related_concepts.append({
            "concept": related,
            "weight": round(weight, 4)
        })

    output[concept] = {
        "salience": salience,
        "inflow": incoming,
        "outflow": outgoing,
        "stability": stability,
        "page_count": len(pages),
        "pages": pages,
        "related_concepts": related_concepts
    }


# =========================================================
# SAVE
# =========================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        output,
        f,
        indent=2,
        ensure_ascii=False
    )

print("🧠 Semantic gravity model built")
print("📦 Wrote:", OUTPUT_FILE)
print("📦 Concepts:", len(output))
