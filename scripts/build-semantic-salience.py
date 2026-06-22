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
# STRUCTURES
# =========================================================

inflow_raw = defaultdict(float)
outflow_raw = defaultdict(float)

concept_graph = defaultdict(lambda: defaultdict(float))

edge_total = len(graph)
edge_concept_coverage = 0


# =========================================================
# ADAPTIVE CONCEPT DAMPING (IMPROVED)
# =========================================================

STOP_BIAS = {
    "this": 0.50,
    "that": 0.55,
    "here": 0.70,
    "just": 0.65,
    "about": 0.80,
    "what": 0.70,
    "like": 0.85
}

def concept_damp(c):
    # hybrid damping: stopword bias + mild length entropy proxy
    base = STOP_BIAS.get(c, 1.0)
    entropy_penalty = 1.0 / (1.0 + math.log1p(len(c)))
    return base * (0.7 + 0.3 * entropy_penalty)


# =========================================================
# EDGE PRUNING THRESHOLD (NOISE CONTROL)
# =========================================================

MIN_EDGE_WEIGHT = 0.1


# =========================================================
# BUILD STRUCTURAL + CONCEPT SPACE
# =========================================================

for edge in graph:

    weight = float(edge.get("weight", 1))
    source = edge.get("from")
    target = edge.get("to")
    concepts = edge.get("shared_concepts", [])

    if not source or not target:
        continue

    if concepts:
        edge_concept_coverage += 1

    # -------------------------
    # URL FLOW SPACE
    # -------------------------
    outflow_raw[source] += weight
    inflow_raw[target] += weight

    # -------------------------
    # CONCEPT MANIFOLD (PRUNED)
    # -------------------------
    for a in concepts:
        for b in concepts:

            if a == b:
                continue

            w = weight * concept_damp(a) * concept_damp(b)

            if w < MIN_EDGE_WEIGHT:
                continue

            concept_graph[a][b] += w


print("\n🧪 EDGE SIGNAL COVERAGE")
print(f"Edges with shared_concepts: {edge_concept_coverage}/{edge_total}")


# =========================================================
# NORMALIZATION (LOG-STABLE)
# =========================================================

def log_norm(d):
    if not d:
        return {}

    v = {k: math.log1p(x) for k, x in d.items()}
    m = max(v.values(), default=1.0)

    return {k: x / m for k, x in v.items()}


inflow = log_norm(inflow_raw)
outflow = log_norm(outflow_raw)


# =========================================================
# CONNECTIVITY
# =========================================================

connectivity_raw = {
    c: len(concept_graph.get(c, {}))
    for c in clusters.keys()
}

connectivity = log_norm(connectivity_raw)


# =========================================================
# STABILITY (ENERGY BALANCE MODEL)
# =========================================================

def stability_fn(i, o):
    denom = i + o
    if denom == 0:
        return 0.0

    imbalance = abs(i - o) / denom
    return 1.0 / (1.0 + imbalance)


# =========================================================
# OPTION A: CONCEPT-PROJECTED FLOW MODEL
# =========================================================
# converts URL flow → concept manifold influence

concept_flow = defaultdict(float)

for c in clusters.keys():
    concept_flow[c] = (inflow.get(c, 0.0) + outflow.get(c, 0.0)) / 2.0


# =========================================================
# DIFFUSION UPGRADE (RANDOM WALK NORMALIZED PROPAGATION)
# =========================================================

diffusion = defaultdict(float)

for node, neighbors in concept_graph.items():

    total = sum(neighbors.values())
    if total == 0:
        continue

    for n, w in neighbors.items():

        p = w / total  # transition probability

        diffusion[node] += p
        diffusion[n] += p * 0.6  # decay outward spread

diffusion = log_norm(diffusion)


# =========================================================
# SEMANTIC GRAVITY MODEL (FINAL v5)
# =========================================================

output = {}

for concept, pages in clusters.items():

    i = inflow.get(concept, 0.0)
    o = outflow.get(concept, 0.0)

    conn = connectivity.get(concept, 0.0)
    diff = diffusion.get(concept, 0.0)

    projected = concept_flow.get(concept, 0.0)
    stability = stability_fn(i, o)

    # -----------------------------------------------------
    # NONLINEAR MULTI-LAYER FUSION
    # -----------------------------------------------------

    salience = math.log1p(projected)

    gravity = (
        (salience ** 1.15) * 0.35 +
        (conn ** 1.10) * 0.20 +
        (diff ** 1.15) * 0.25 +
        (stability ** 1.25) * 0.20
    )

    gravity = max(0.0, min(1.0, gravity))

    related = sorted(
        concept_graph.get(concept, {}).items(),
        key=lambda x: x[1],
        reverse=True
    )[:10]

    output[concept] = {
        "salience": round(salience, 4),
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

print("\n🧠 Semantic gravity model built (v5 concept-projected)")
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
