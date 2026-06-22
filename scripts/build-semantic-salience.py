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
# NETWORK STRUCTURES
# =========================================================

inflow_raw = defaultdict(float)
outflow_raw = defaultdict(float)

concept_neighbors = defaultdict(lambda: defaultdict(float))

edge_total = len(graph)
edge_concept_coverage = 0


# =========================================================
# IMPROVED CONCEPT DAMPING (semantic frequency bias)
# =========================================================
# instead of string length (bad proxy), use mild lexical damping
# keeps "this/that" down but doesn't distort real short concepts

STOP_BIAS = {
    "this": 0.55,
    "that": 0.60,
    "here": 0.75,
    "just": 0.70,
    "about": 0.85
}

def concept_damp(c):
    return STOP_BIAS.get(c, 1.0)


# =========================================================
# BUILD GRAPH
# =========================================================

for edge in graph:

    weight = float(edge.get("weight", 1))
    source = edge.get("from")
    target = edge.get("to")
    concepts = edge.get("shared_concepts", [])

    if concepts:
        edge_concept_coverage += 1

    if not source or not target:
        continue

    # FLOW
    outflow_raw[source] += weight
    inflow_raw[target] += weight

    # =========================================================
    # CONCEPT GRAPH (ASYMMETRIC + WEIGHTED)
    # =========================================================
    # key fix: directional reinforcement instead of full clique explosion

    for a in concepts:
        for b in concepts:

            if a == b:
                continue

            w = weight * concept_damp(a) * concept_damp(b)

            # bidirectional but NOT identical (slight asymmetry)
            concept_neighbors[a][b] += w
            concept_neighbors[b][a] += w * 0.85


print("\n🧪 EDGE SIGNAL COVERAGE")
print(f"Edges with shared_concepts: {edge_concept_coverage}/{edge_total}")


# =========================================================
# HELPERS
# =========================================================

def log_norm(d):
    if not d:
        return {}

    transformed = {k: math.log1p(v) for k, v in d.items()}
    max_v = max(transformed.values(), default=1.0)

    return {k: v / max_v for k, v in transformed.items()}


def clamp(x):
    return max(0.0, min(1.0, x))


# =========================================================
# FLOW NORMALIZATION (POST-GRAPH BUILD ONLY)
# =========================================================

inflow = log_norm(inflow_raw)
outflow = log_norm(outflow_raw)


# =========================================================
# CONNECTIVITY
# =========================================================

connectivity_raw = {
    c: len(concept_neighbors.get(c, {}))
    for c in clusters.keys()
}

connectivity = log_norm(connectivity_raw)


# =========================================================
# STABILITY (IMPROVED NUMERICAL SAFETY)
# =========================================================

def stability_fn(i, o):
    denom = i + o
    if denom == 0:
        return 0.0
    return 1.0 - abs(i - o) / denom


# =========================================================
# CONCEPT DIFFUSION (FIXED: TWO-PASS NORMALIZED FLOW)
# =========================================================

# Step 1: accumulate influence
raw_diff = defaultdict(float)

for c, neighbors in concept_neighbors.items():
    total = sum(neighbors.values()) + 1e-9

    for n, w in neighbors.items():
        flow = (w / total)

        raw_diff[c] += flow
        raw_diff[n] += flow * 0.65  # decay for outward diffusion

# Step 2: normalize diffusion field
diffused = log_norm(raw_diff)


# =========================================================
# SEMANTIC GRAVITY MODEL (v4.1)
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
    # NONLINEAR FUSION (IMPORTANT FIX)
    # replaces linear blend with soft geometric coupling
    # =========================================================

    base = (
        (salience_raw ** 1.2) * 0.45 +
        (conn ** 1.1) * 0.20 +
        (diff ** 1.1) * 0.20 +
        (stability ** 1.3) * 0.15
    )

    gravity = clamp(base)

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

print("\n🧠 Semantic gravity model built (v4.1 stabilized)")
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
