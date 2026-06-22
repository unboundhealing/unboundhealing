import json
import os
import math
from collections import defaultdict

ROOT = os.environ.get("GITHUB_WORKSPACE", os.getcwd())

GRAPH_FILE = os.path.join(ROOT, "semantic-graph.json")
OUTPUT_FILE = os.path.join(ROOT, "semantic-salience.json")

# =========================================================
# LOAD
# =========================================================

with open(GRAPH_FILE, "r", encoding="utf-8") as f:
    graph_data = json.load(f)

graph = graph_data.get("edges", [])

# ---------------------------------------------------------
# HARD SAFETY GUARD (your requested rule)
# ---------------------------------------------------------

if not graph or graph == [
    {
        "from": "__system__",
        "to": "__system__",
        "weight": 1.0,
        "shared_concepts": ["system", "fallback"]
    }
]:
    raise ValueError("Semantic graph not yet valid gravity substrate")

print("\n🧪 RAW INPUT INSPECTION")
print("SAMPLE EDGE:", graph[:2])

# =========================================================
# STRUCTURES
# =========================================================

concept_in = defaultdict(float)
concept_out = defaultdict(float)
concept_links = defaultdict(lambda: defaultdict(float))

edge_count = len(graph)
covered_edges = 0

# =========================================================
# STOP DAMPING (gravity attenuation)
# =========================================================

STOP_BIAS = {
    "this": 0.50,
    "that": 0.55,
    "just": 0.65,
    "about": 0.80,
    "here": 0.75
}

def damp(c):
    return STOP_BIAS.get(c, 1.0)

# =========================================================
# FLOW PROJECTION (ONLY SOURCE OF TRUTH)
# =========================================================

for e in graph:
    w = float(e.get("weight", 1))
    src = e.get("from")
    tgt = e.get("to")
    concepts = e.get("shared_concepts", [])

    if not src or not tgt:
        continue

    if concepts:
        covered_edges += 1
        per = w / max(len(concepts), 1)

        for c in concepts:
            concept_in[c] += per
            concept_out[c] += per

        for a in concepts:
            for b in concepts:
                if a == b:
                    continue
                concept_links[a][b] += w * damp(a) * damp(b)

# =========================================================
# NORMALIZATION (FIXED + SAFE)
# =========================================================

def log_norm(d):
    if not d:
        return {}

    t = {k: math.log1p(v) for k, v in d.items()}
    values = list(t.values())

    if not values:
        return {}

    m = max(values)
    if m == 0:
        return {k: 0.0 for k in t}

    return {k: v / m for k, v in t.items()}

def clamp(x):
    return max(0.0, min(1.0, x))

def stability(i, o):
    denom = i + o
    if denom == 0:
        return 0.0
    return 1.0 - abs(i - o) / denom

# =========================================================
# NORMALIZE FLOWS
# =========================================================

in_n = log_norm(concept_in)
out_n = log_norm(concept_out)

connectivity_raw = {c: len(n) for c, n in concept_links.items()}
connectivity = log_norm(connectivity_raw)

# =========================================================
# DIFFUSION FIELD (gravity relaxation)
# =========================================================

nodes = list(concept_links.keys())
rank = {n: 1.0 for n in nodes}

damping = 0.85
iterations = 10

for _ in range(iterations):
    new = defaultdict(float)

    for n, nbrs in concept_links.items():
        total = sum(nbrs.values()) + 1e-9

        for m, w in nbrs.items():
            new[m] += rank[n] * (w / total)

    rank = {
        k: damping * new[k] + (1 - damping)
        for k in new
    }

rank = log_norm(rank)

# =========================================================
# GRAVITY FIELD (FINAL AUTHORITY LAYER)
# =========================================================

output = {}

all_concepts = (
    set(in_n.keys()) |
    set(out_n.keys()) |
    set(connectivity.keys()) |
    set(rank.keys())
)

for c in all_concepts:

    i = in_n.get(c, 0.0)
    o = out_n.get(c, 0.0)
    conn = connectivity.get(c, 0.0)
    r = rank.get(c, 0.0)

    s = stability(i, o)

    salience = (i + o) / 2.0

    gravity = (
        (salience ** 1.1) * 0.45 +
        (conn ** 1.05) * 0.25 +
        (r ** 1.1) * 0.20 +
        (s ** 1.2) * 0.10
    )

    output[c] = {
        "gravity": round(clamp(gravity), 5),
        "salience": round(salience, 5),
        "inflow": round(i, 5),
        "outflow": round(o, 5),
        "connectivity": round(conn, 5),
        "diffusion": round(r, 5),
        "stability": round(s, 5)
    }

# =========================================================
# SAVE (ONLY SOURCE OF TRUTH)
# =========================================================

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print("\n🧠 Semantic gravity model built (v5.2 salience-core)")
print("📦 concepts:", len(output))
