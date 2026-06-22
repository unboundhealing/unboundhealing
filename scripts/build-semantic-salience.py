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


print("\n🧪 RAW INPUT INSPECTION")
print("SAMPLE GRAPH EDGE:", graph[:3])
print("SAMPLE CLUSTER:", list(clusters.items())[:2])


# =========================================================
# HYBRID NETWORK BUILD
# =========================================================

inflow_raw = defaultdict(float)
outflow_raw = defaultdict(float)

url_neighbors = defaultdict(dict)
concept_neighbors = defaultdict(lambda: defaultdict(float))

edge_total = len(graph)
edge_concept_coverage = 0


# damping reduces dominance of generic words ("this", "that")
def concept_damp(c):
    return 1.0 / (1.0 + math.log1p(len(c)))


for edge in graph:

    weight = float(edge.get("weight", 1))
    source = edge.get("from")
    target = edge.get("to")
    concepts = edge.get("shared_concepts", [])

    if concepts:
        edge_concept_coverage += 1

    if not source or not target:
        continue

    # URL FLOW (raw)
    outflow_raw[source] += weight
    inflow_raw[target] += weight

    url_neighbors[source][target] = url_neighbors[source].get(target, 0) + weight
    url_neighbors[target][source] = url_neighbors[target].get(source, 0) + weight

    # =========================================================
    # CONCEPT GRAPH + DIFFUSION + DAMPING
    # =========================================================

    # direct clique connections
    for a in concepts:
        for b in concepts:
            if a == b:
                continue

            w = weight * concept_damp(a) * concept_damp(b)
            concept_neighbors[a][b] += w


print("\n🧪 EDGE SIGNAL COVERAGE")
print(f"Edges with shared_concepts: {edge_concept_coverage}/{edge_total}")


# =========================================================
# HELPERS
# =========================================================

def log_norm(d):
    """log-scaled normalization (prevents collapse, preserves structure)"""
    if not d:
        return {}

    transformed = {k: math.log1p(v) for k, v in d.items()}
    max_v = max(transformed.values(), default=1)

    return {k: v / max_v for k, v in transformed.items()}


def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


# =========================================================
# FLOW SIGNALS (RAW + LOG NORMALIZED)
# =========================================================

inflow = log_norm(inflow_raw)
outflow = log_norm(outflow_raw)


# =========================================================
# CONNECTIVITY (with diffusion smoothing)
# =========================================================

connectivity_raw = {
    c: len(concept_neighbors.get(c, {}))
    for c in clusters.keys()
}

connectivity = log_norm(connectivity_raw)


# =========================================================
# STABILITY FUNCTION (FIXED)
# =========================================================

def stability_fn(i, o):
    # symmetric balance score
    if i + o == 0:
        return 0.0
    return 1.0 - abs(i - o) / (i + o)


# =========================================================
# CONCEPT DIFFUSION STEP (IMPORTANT FIX)
# =========================================================

# propagate influence once across concept graph
diffused = defaultdict(float)

for c, neighbors in concept_neighbors.items():
    for n, w in neighbors.items():
        diffused[c] += w * 0.25
        diffused[n] += w * 0.25


diffused = log_norm(diffused)


# =========================================================
# SEMANTIC GRAVITY MODEL (STABILIZED v4)
# =========================================================

output = {}

for concept, pages in clusters.items():

    i = inflow.get(concept, 0.0)
    o = outflow.get(concept, 0.0)

    conn = connectivity.get(concept, 0.0)
    diff = diffused.get(concept, 0.0)

    salience_raw = (i + o) / 2.0

    stability = stability_fn(i, o)

    # =========================================================
    # FINAL GRAVITY (balanced composite)
    # =========================================================

    gravity = (
        (salience_raw * 0.4)
        + (conn * 0.2)
        + (diff * 0.2)
        + (stability * 0.2)
    )

    gravity = clamp(gravity)

    # related concepts (top neighbors)
    related = sorted(
        concept_neighbors.get(concept, {}).items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    output[concept] = {
        "salience": round(salience_raw, 4),
        "gravity": round(gravity, 4),
        "inflow": round(i, 4),
        "outflow": round(o, 4),
        "stability": round(stability, 4),
        "connectivity": round(conn, 4),
        "diffusion": round(diff, 4),
        "page_count": len(pages),
        "pages": pages,
        "related_concepts": [
            {"concept": c, "weight": round(w, 4)}
            for c, w in related
        ]
    }


# =========================================================
# SAVE OUTPUT
# =========================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)


# =========================================================
# DEBUG REPORT
# =========================================================

print("\n🧠 Semantic gravity model built (v4.0)")
print("📦 Wrote:", OUTPUT_FILE)
print("📦 Concepts:", len(output))

top = sorted(output.items(), key=lambda x: x[1]["gravity"], reverse=True)[:10]

print("\n🌌 Top gravity concepts")

for concept, data in top:
    print(
        f"{concept}: "
        f"gravity={data['gravity']} "
        f"salience={data['salience']} "
        f"conn={data['connectivity']} "
        f"diff={data['diffusion']}"
    )
