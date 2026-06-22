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
# DEBUG: RAW INPUT INSPECTION
# =========================================================

print("\n🧪 RAW INPUT INSPECTION")
print("SAMPLE GRAPH EDGE:", graph[:5])
print("SAMPLE CLUSTER:", list(clusters.items())[:2])


# =========================================================
# 🧪 CONCEPT ALIGNMENT CHECK
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
# BUILD URL + CONCEPT HYBRID SIGNAL MODEL
# =========================================================

inflow = defaultdict(float)
outflow = defaultdict(float)

# URL neighbors (kept for page-level structure)
url_neighbors = defaultdict(dict)

# ✅ NEW: concept-level graph (THIS FIXES EVERYTHING)
concept_neighbors = defaultdict(dict)

edge_concept_coverage = 0
edge_total = len(graph)

for edge in graph:

    weight = float(edge.get("weight", 1))
    source = edge.get("from")
    target = edge.get("to")
    concepts = edge.get("shared_concepts", [])

    if concepts:
        edge_concept_coverage += 1

    if not source or not target:
        continue

    # -----------------------------
    # URL-level structure (unchanged)
    # -----------------------------
    outflow[source] += weight
    inflow[target] += weight

    url_neighbors[source][target] = url_neighbors[source].get(target, 0) + weight
    url_neighbors[target][source] = url_neighbors[target].get(source, 0) + weight

    # -----------------------------
    # ✅ CONCEPT-LEVEL GRAPH (FIX)
    # -----------------------------
    # connect all concepts in shared_concepts to each other
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

    return {
        k: round(v / max_value, 4)
        for k, v in values.items()
    }


inflow = normalize(inflow)
outflow = normalize(outflow)


# =========================================================
# CONNECTIVITY (NOW CORRECT)
# =========================================================

connectivity = {}

for concept in clusters.keys():
    connectivity[concept] = len(concept_neighbors.get(concept, {}))

connectivity = normalize(connectivity)


# =========================================================
# DEBUG: POST-NETWORK STATE
# =========================================================

print("\n🧪 NETWORK STATE INSPECTION")

sample_neighbors = dict(list(concept_neighbors.items())[:2])
print("CONCEPT NEIGHBOR SAMPLE:", sample_neighbors)

print("Inflow nodes:", len(inflow))
print("Outflow nodes:", len(outflow))
print("Connectivity nodes:", len(connectivity))

zero_conn = sum(1 for v in connectivity.values() if v == 0)

if zero_conn > 0:
    print(f"⚠️ {zero_conn} concepts have ZERO connectivity")


# =========================================================
# BUILD SEMANTIC GRAVITY MODEL
# =========================================================

output = {}

for concept, pages in clusters.items():

    incoming = inflow.get(concept, 0.0)
    outgoing = outflow.get(concept, 0.0)
    conn = connectivity.get(concept, 0.0)

    stability = round(1 - abs(incoming - outgoing), 4)
    salience = round((incoming + outgoing) / 2, 4)

    gravity = round(salience * stability * conn, 4)

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
        "salience": salience,
        "gravity": gravity,
        "inflow": incoming,
        "outflow": outgoing,
        "stability": stability,
        "connectivity": conn,
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

top = sorted(
    output.items(),
    key=lambda x: x[1]["gravity"],
    reverse=True
)[:10]

print("\n🌌 Top gravity concepts")

for concept, data in top:
    print(
        f"{concept}: "
        f"gravity={data['gravity']} "
        f"salience={data['salience']} "
        f"connectivity={data['connectivity']}"
    )
