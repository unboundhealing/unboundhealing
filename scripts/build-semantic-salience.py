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
# BUILD DIRECTIONAL CONCEPT NETWORK
# =========================================================

inflow = defaultdict(float)
outflow = defaultdict(float)
neighbors = defaultdict(dict)

for edge in graph:

    weight = float(edge.get("weight", 1))

    source = edge.get("from")
    target = edge.get("to")

    if not source or not target:
        continue

    outflow[source] += weight
    inflow[target] += weight

    neighbors[source][target] = neighbors[source].get(target, 0) + weight
    neighbors[target][source] = neighbors[target].get(source, 0) + weight


# =========================================================
# SAFE NORMALIZATION (NO DIVISION ERRORS EVER)
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
# CONNECTIVITY (SAFE + GUARDED)
# =========================================================

connectivity = {}

for concept in clusters.keys():
    connectivity[concept] = len(neighbors.get(concept, {}))

connectivity = normalize(connectivity)


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
# DEBUG REPORT (THIS IS WHAT YOU WERE MISSING)
# =========================================================

print("🧠 Semantic gravity model built")
print("📦 Wrote:", OUTPUT_FILE)
print("📦 Concepts:", len(output))

print("\n🔎 SYSTEM SANITY CHECK")

print("Graph edges:", len(graph))
print("Concept clusters:", len(clusters))
print("Inflow nodes:", len(inflow))
print("Outflow nodes:", len(outflow))
print("Connectivity nodes:", len(connectivity))

# detect silent failure mode
zero_conn = sum(1 for v in connectivity.values() if v == 0)
if zero_conn > 0:
    print(f"⚠️ {zero_conn} concepts have ZERO connectivity")

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
