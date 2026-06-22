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
print("SAMPLE GRAPH EDGE:", graph[:2])
print("SAMPLE CLUSTER:", list(clusters.items())[:2])

# =========================================================
# STRUCTURES
# =========================================================

url_inflow = defaultdict(float)
url_outflow = defaultdict(float)

concept_inflow = defaultdict(float)
concept_outflow = defaultdict(float)

concept_neighbors = defaultdict(lambda: defaultdict(float))

edge_total = len(graph)
edge_concept_coverage = 0

# =========================================================
# CONCEPT DAMPING (stopword-aware)
# =========================================================

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
# PHASE 1 — BUILD GRAPH + CONCEPT-PROJECTED FLOW
# =========================================================

for edge in graph:
    weight = float(edge.get("weight", 1))
    source = edge.get("from")
    target = edge.get("to")
    concepts = edge.get("shared_concepts", [])

    if not source or not target:
        continue

    # URL flow
    url_outflow[source] += weight
    url_inflow[target] += weight

    if concepts:
        edge_concept_coverage += 1

        # =====================================================
        # CONCEPT PROJECTION (CRITICAL FIX)
        # distribute edge signal into concept space
        # =====================================================

        per_concept = weight / len(concepts)

        for c in concepts:
            concept_inflow[c] += per_concept
            concept_outflow[c] += per_concept

    # concept neighborhood graph (semantic coupling)
    for a in concepts:
        for b in concepts:
            if a == b:
                continue

            w = weight * concept_damp(a) * concept_damp(b)

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
    t = {k: math.log1p(v) for k, v in d.items()}
    m = max(t.values(), default=1.0)
    return {k: v / m for k, v in t.items()}

def clamp(x):
    return max(0.0, min(1.0, x))

def stability_fn(i, o):
    denom = i + o
    if denom == 0:
        return 0.0
    return 1.0 - abs(i - o) / denom

# =========================================================
# NORMALIZE URL + CONCEPT FLOWS
# =========================================================

url_inflow_n = log_norm(url_inflow)
url_outflow_n = log_norm(url_outflow)

concept_inflow_n = log_norm(concept_inflow)
concept_outflow_n = log_norm(concept_outflow)

# =========================================================
# CONNECTIVITY
# =========================================================

connectivity_raw = {
    c: len(concept_neighbors.get(c, {}))
    for c in clusters.keys()
}

connectivity = log_norm(connectivity_raw)

# =========================================================
# PHASE 2 — DIFFUSION UPGRADE (PageRank-style random walk)
# =========================================================

nodes = list(concept_neighbors.keys())
diff = {n: 1.0 for n in nodes}

damping = 0.85
iterations = 8

for _ in range(iterations):
    new = defaultdict(float)

    for n, nbrs in concept_neighbors.items():
        total = sum(nbrs.values()) + 1e-9

        for m, w in nbrs.items():
            new[m] += (diff[n] * (w / total))

    # normalize + damping
    diff = {
        k: (damping * new[k] + (1 - damping) * 1.0)
        for k in new
    }

diff = log_norm(diff)

# =========================================================
# PHASE 3 — SEMANTIC GRAVITY MODEL (FIXED SALIENCE SPACE)
# =========================================================

output = {}

for concept, pages in clusters.items():

    i = concept_inflow_n.get(concept, 0.0)
    o = concept_outflow_n.get(concept, 0.0)

    conn = connectivity.get(concept, 0.0)
    d = diff.get(concept, 0.0)

    # NOW VALID (no longer zeroed)
    salience_raw = (i + o) / 2.0
    stability = stability_fn(i, o)

    # nonlinear fusion
    gravity = (
        (salience_raw ** 1.15) * 0.40 +
        (conn ** 1.05) * 0.20 +
        (d ** 1.10) * 0.25 +
        (stability ** 1.25) * 0.15
    )

    gravity = clamp(gravity)

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
        "diffusion": round(d, 4),
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

print("\n🧠 Semantic gravity model built (v5.0 concept-projected + diffusion)")
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
