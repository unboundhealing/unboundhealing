import json
import os
import math
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
# DEBUG: RAW INPUT INSPECTION
# =========================================================

print("\n🧪 RAW INPUT INSPECTION")
print("SAMPLE GRAPH EDGE:", graph[:5])
print("SAMPLE CLUSTER:", list(clusters.items())[:2])


# =========================================================
# CONCEPT ALIGNMENT CHECK
# =========================================================

graph_concepts_sample = set()
for e in graph[:20]:
    graph_concepts_sample.update(e.get("shared_concepts", []))

cluster_keys_sample = set(list(clusters.keys())[:50])

overlap = graph_concepts_sample & cluster_keys_sample

print("\n🧪 CONCEPT ALIGNMENT CHECK")
print("Graph concept sample:", list(graph_concepts_sample)[:20])
print("Cluster keys sample:", list(cluster_keys_sample)[:20])
print("Overlap count:", len(overlap))
print("Overlap sample:", list(overlap)[:10])


# =========================================================
# BUILD HYBRID NETWORK
# =========================================================

inflow = defaultdict(float)
outflow = defaultdict(float)

url_neighbors = defaultdict(dict)
concept_neighbors = defaultdict(dict)

edge_total = len(graph)
edge_concept_coverage = 0

for edge in graph:

    weight = float(edge.get("weight", 1))
    source = edge.get("from")
    target = edge.get("to")
    concepts = edge.get("shared_concepts", [])

    if concepts:
        edge_concept_coverage += 1

    if not source or not target:
        continue

    # URL FLOW
    outflow[source] += weight
    inflow[target] += weight

    url_neighbors[source][target] = url_neighbors[source].get(target, 0) + weight
    url_neighbors[target][source] = url_neighbors[target].get(source, 0) + weight

    # CONCEPT GRAPH (fully connected clique per edge)
    for a in concepts:
        for b in concepts:
            if a == b:
                continue
            concept_neighbors[a][b] = concept_neighbors[a].get(b, 0) + weight


print("\n🧪 EDGE SIGNAL COVERAGE")
print(f"Edges with shared_concepts: {edge_concept_coverage}/{edge_total}")


# =========================================================
# SAFE NORMALIZATION
# =========================================================

def normalize(values):
    if not values:
        return {}

    max_value = max(values.values(), default=0)

    if max_value <= 0:
        return {k: 0.0 for k in values}

    return {k: round(v / max_value, 4) for k, v in values.items()}


# =========================================================
# CONNECTIVITY (IMPROVED: LOG SCALE)
# =========================================================

connectivity_raw = {
    concept: len(concept_neighbors.get(concept, {}))
    for concept in clusters.keys()
}

max_conn = max(connectivity_raw.values(), default=1)

connectivity = {
    k: math.log1p(v) / math.log1p(max_conn) if max_conn > 0 else 0.0
    for k, v in connectivity_raw.items()
}


# =========================================================
# NORMALIZE FLOW
# =========================================================

inflow = normalize(inflow)
outflow = normalize(outflow)


# =========================================================
# DEBUG STATE
# =========================================================

print("\n🧪 NETWORK STATE INSPECTION")
print("Concept neighbor sample:", dict(list(concept_neighbors.items())[:2]))
print("Inflow nodes:", len(inflow))
print("Outflow nodes:", len(outflow))
print("Connectivity nodes:", len(connectivity_raw))

zero_conn = sum(1 for v in connectivity.values() if v == 0)
if zero_conn:
    print(f"⚠️ {zero_conn} concepts have ZERO connectivity")


# =========================================================
# SEMANTIC GRAVITY MODEL (STABILIZED)
# =========================================================

output = {}

for concept, pages in clusters.items():

    incoming = inflow.get(concept, 0.0)
    outgoing = outflow.get(concept, 0.0)
    conn = connectivity.get(concept, 0.0)

    # STABILITY (bounded ratio form)
    stability = 1 / (1 + abs(incoming - outgoing))

    # SALIENCE
    salience = (incoming + outgoing) / 2

    # NORMALIZED COMPOSITE GRAVITY (GEOMETRIC MEAN)
    gravity = (salience * stability * conn) ** (1/3) if (salience * stability * conn) > 0 else 0.0

    related_concepts = []

    for related, weight in sorted(
        concept_neighbors.get(concept, {}).items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]:

        related_concepts.append({
            "concept": related,
            "weight": round(weight, 4)
        })

    output[concept] = {
        "salience": round(salience, 4),
        "gravity": round(gravity, 4),
        "inflow": round(incoming, 4),
        "outflow": round(outgoing, 4),
        "stability": round(stability, 4),
        "connectivity": round(conn, 4),
        "page_count": len(pages),
        "pages": pages,
        "related_concepts": related_concepts
    }


# =========================================================
# SAVE OUTPUT
# =========================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)


# =========================================================
# DEBUG REPORT
# =========================================================

print("\n🧠 Semantic gravity model built")
print("📦 Wrote:", OUTPUT_FILE)
print("📦 Concepts:", len(output))

print("\n🔎 SYSTEM SANITY CHECK")
print("Graph edges:", len(graph))
print("Concept clusters:", len(clusters))
print("Inflow nodes:", len(inflow))
print("Outflow nodes:", len(outflow))
print("Connectivity nodes:", len(connectivity))

top = sorted(output.items(), key=lambda x: x[1]["gravity"], reverse=True)[:10]

print("\n🌌 Top gravity concepts")

for concept, data in top:
    print(
        f"{concept}: "
        f"gravity={data['gravity']} "
        f"salience={data['salience']} "
        f"connectivity={data['connectivity']}"
    )
